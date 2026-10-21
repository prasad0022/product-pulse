"""Train and evaluate Product Pulse's next-month risk model.

Run after `python scripts/generate_data.py`:
    python scripts/train_model.py
"""
from __future__ import annotations
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
DOCS = ROOT / "docs"
MODELS = ROOT / "models"
MODELS.mkdir(exist_ok=True)


def metrics_for(model, X, y):
    probs = model.predict_proba(X)[:, 1]
    pred = (probs >= 0.5).astype(int)
    return {
        "rows": int(len(y)),
        "positive_rate": float(y.mean()) if len(y) else 0.0,
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, probs)) if y.nunique() > 1 else None,
    }


def main():
    monthly = pd.read_csv(DATA / "product_metrics_monthly.csv")
    products = pd.read_csv(DATA / "products.csv")
    labels = pd.read_csv(DATA / "product_risk_labels.csv")
    df = monthly.sort_values(["product_id", "month"]).copy()
    grouped = df.groupby("product_id", sort=False)

    for source, target in [
        ("return_rate", "return_rate_3m_avg"),
        ("avg_rating", "rating_3m_avg"),
        ("negative_review_rate", "negative_review_rate_3m_avg"),
        ("support_ticket_count", "ticket_count_3m_avg"),
    ]:
        df[target] = grouped[source].transform(lambda s: s.rolling(3, min_periods=1).mean())
        df[f"{source}_change_1m"] = grouped[source].diff().fillna(0)

    df = df.merge(labels[["product_id", "month", "future_high_risk"]], on=["product_id", "month"], how="inner")
    df = df.merge(products[["product_id", "category", "brand"]], on="product_id", how="left")
    df = df[df["month"] < "2025-12"].copy()

    feature_cols = [
        "orders", "units_sold", "returned_units", "return_rate", "avg_rating", "review_count",
        "negative_review_rate", "support_ticket_count", "return_rate_3m_avg", "rating_3m_avg",
        "negative_review_rate_3m_avg", "ticket_count_3m_avg", "return_rate_change_1m",
        "avg_rating_change_1m", "negative_review_rate_change_1m", "support_ticket_count_change_1m",
        "category", "brand",
    ]
    train = df[df.month <= "2025-08"]
    val = df[df.month == "2025-09"]
    test = df[df.month.isin(["2025-10", "2025-11"])]
    if train.future_high_risk.nunique() < 2 or val.future_high_risk.nunique() < 2 or test.future_high_risk.nunique() < 2:
        raise RuntimeError("Target needs both classes in train, validation, and test splits; review the synthetic data definition.")

    numeric_cols = [c for c in feature_cols if c not in ("category", "brand")]
    categorical_cols = ["category", "brand"]
    preprocessor = ColumnTransformer([
        ("num", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric_cols),
        ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical_cols),
    ])
    candidates = {
        "logistic_regression": Pipeline([("preprocess", preprocessor), ("model", LogisticRegression(max_iter=2500, class_weight="balanced", random_state=42))]),
        "random_forest": Pipeline([("preprocess", preprocessor), ("model", RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=2, class_weight="balanced", random_state=42, n_jobs=-1))]),
    }
    results = {}
    for name, model in candidates.items():
        model.fit(train[feature_cols], train.future_high_risk)
        results[name] = {"validation": metrics_for(model, val[feature_cols], val.future_high_risk), "test": metrics_for(model, test[feature_cols], test.future_high_risk)}

    selected = max(candidates, key=lambda name: (results[name]["validation"]["f1"], results[name]["validation"]["roc_auc"] or -1))
    best_model = candidates[selected]
    best_model.fit(train[feature_cols], train.future_high_risk)
    joblib.dump(best_model, MODELS / "risk_model.joblib")

    all_probs = best_model.predict_proba(df[feature_cols])[:, 1]
    predictions = df[["product_id", "month", "future_high_risk"]].copy()
    predictions["predicted_next_month_high_risk_probability"] = all_probs.round(5)
    predictions["split"] = np.select([predictions.month <= "2025-08", predictions.month == "2025-09", predictions.month.isin(["2025-10", "2025-11"])], ["train", "validation", "test"], default="not_evaluated")
    predictions.to_csv(DATA / "risk_model_predictions.csv", index=False)

    report = {
        "objective": "Predict next-month high risk from current-month product signals.",
        "target": "future_high_risk: next month's rolling composite risk score >= 0.55.",
        "time_split": {"train": "through 2025-08", "validation": "2025-09", "test": ["2025-10", "2025-11"]},
        "selected_model": selected,
        "features": feature_cols,
        "results": results,
        "caveat": "The dataset is synthetic and contains seeded patterns. Metrics demonstrate pipeline behavior; they do not estimate real-world production performance.",
    }
    (DOCS / "ML_MODEL_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = ["# Product Pulse ML Model Report", "", f"Selected model: **{selected}**", "", "Chronological evaluation; the target is next-month product risk.", "", "| Model | Val F1 | Val ROC-AUC | Test F1 | Test ROC-AUC |", "|---|---:|---:|---:|---:|"]
    for name, res in results.items():
        v, t = res["validation"], res["test"]
        lines.append(f"| {name} | {v['f1']:.3f} | {v['roc_auc']:.3f} | {t['f1']:.3f} | {t['roc_auc']:.3f} |")
    lines += ["", "**Important:** this is a synthetic-data demonstration, not evidence of real-world model accuracy."]
    (DOCS / "ML_MODEL_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"selected_model": selected, "results": results, "predictions": str(DATA / 'risk_model_predictions.csv')}, indent=2))

if __name__ == "__main__":
    main()
