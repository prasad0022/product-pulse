
"""Train and evaluate Product Pulse's next-month risk model.

Run from the project root:
    python scripts/train_model.py

Outputs:
    models/risk_model.joblib
    data/processed/risk_model_predictions.csv
    docs/ML_MODEL_REPORT.json
    docs/ML_MODEL_REPORT.md

The dataset is synthetic. Metrics demonstrate pipeline behavior and do
not estimate real-world production performance.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# Resolve the repository root so the script works when launched from
# the project root or by an absolute path.
ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics.ml_features import (  # noqa: E402
    FEATURE_COLUMNS,
    build_model_features,
)


DATA = ROOT / "data" / "processed"
DOCS = ROOT / "docs"
MODELS = ROOT / "models"

# Ensure output directories exist.
DATA.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)
MODELS.mkdir(parents=True, exist_ok=True)


RANDOM_STATE = 42
POSITIVE_CLASS = 1

TRAIN_END_MONTH = "2025-08"
VALIDATION_MONTH = "2025-09"
TEST_MONTHS = ["2025-10", "2025-11"]


def positive_class_probabilities(
    model: Pipeline,
    features: pd.DataFrame,
) -> np.ndarray:
    """Return probabilities for the high-risk class, regardless of class order."""
    classes = list(model.classes_)

    if POSITIVE_CLASS not in classes:
        raise RuntimeError(
            f"Trained model does not contain positive class {POSITIVE_CLASS}."
        )

    positive_index = classes.index(POSITIVE_CLASS)
    probabilities = model.predict_proba(features)

    return probabilities[:, positive_index]


def metrics_for(
    model: Pipeline,
    features: pd.DataFrame,
    target: pd.Series,
) -> dict:
    """Calculate classification metrics for one dataset split."""
    target = pd.Series(target).astype(int).reset_index(drop=True)

    if len(target) == 0:
        raise ValueError("Cannot calculate metrics for an empty dataset.")

    probabilities = positive_class_probabilities(model, features)
    predictions = (probabilities >= 0.5).astype(int)

    roc_auc = (
        float(roc_auc_score(target, probabilities))
        if target.nunique() > 1
        else None
    )

    return {
        "rows": int(len(target)),
        "positive_rate": float(target.mean()),
        "accuracy": float(accuracy_score(target, predictions)),
        "precision": float(
            precision_score(target, predictions, zero_division=0)
        ),
        "recall": float(
            recall_score(target, predictions, zero_division=0)
        ),
        "f1": float(f1_score(target, predictions, zero_division=0)),
        "roc_auc": roc_auc,
    }


def build_pipeline() -> Pipeline:
    """Create a complete preprocessing and classification pipeline."""
    categorical_columns = ["category", "brand"]
    numeric_columns = [
        column
        for column in FEATURE_COLUMNS
        if column not in categorical_columns
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                numeric_columns,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        (
                            "imputer",
                            SimpleImputer(strategy="most_frequent"),
                        ),
                        (
                            "onehot",
                            OneHotEncoder(handle_unknown="ignore"),
                        ),
                    ]
                ),
                categorical_columns,
            ),
        ],
        remainder="drop",
    )

    # The classifier is replaced by each candidate below.
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            (
                "model",
                LogisticRegression(
                    max_iter=2500,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def load_training_data() -> pd.DataFrame:
    """Load inputs, build shared features, and attach training labels."""
    monthly_path = DATA / "product_metrics_monthly.csv"
    products_path = DATA / "products.csv"
    labels_path = DATA / "product_risk_labels.csv"

    for path in (monthly_path, products_path, labels_path):
        if not path.is_file():
            raise FileNotFoundError(
                f"Required input file is missing: {path}"
            )

    monthly = pd.read_csv(monthly_path)
    products = pd.read_csv(products_path)
    labels = pd.read_csv(labels_path)

    required_label_columns = {
        "product_id",
        "month",
        "future_high_risk",
    }
    missing = required_label_columns.difference(labels.columns)

    if missing:
        raise ValueError(
            f"Risk labels are missing required columns: {sorted(missing)}"
        )

    # Use the same feature engineering as API-time inference.
    features = build_model_features(monthly, products)

    df = features.merge(
        labels[["product_id", "month", "future_high_risk"]],
        on=["product_id", "month"],
        how="inner",
        validate="one_to_one",
    )

    if df.empty:
        raise RuntimeError(
            "No training rows remain after joining metrics and risk labels."
        )

    df["future_high_risk"] = pd.to_numeric(
        df["future_high_risk"], errors="raise"
    ).astype(int)

    if not df["future_high_risk"].isin([0, 1]).all():
        raise ValueError("future_high_risk must contain only 0 and 1.")

    # The labels available in the current dataset cover months through
    # November 2025; December features remain available for live inference.
    df = df[df["month"] < "2025-12"].copy()
    df = df.sort_values(["product_id", "month"]).reset_index(drop=True)

    missing_features = set(FEATURE_COLUMNS).difference(df.columns)
    if missing_features:
        raise ValueError(
            f"Model features are missing: {sorted(missing_features)}"
        )

    return df


def create_model_candidates() -> dict[str, Pipeline]:
    """Create independent pipelines for model comparison."""
    return {
        "logistic_regression": build_pipeline(),
        "random_forest": Pipeline(
            steps=[
                ("preprocess", build_pipeline().named_steps["preprocess"]),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=300,
                        max_depth=6,
                        min_samples_leaf=2,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def validate_splits(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
) -> None:
    """Fail early when a split cannot support binary evaluation."""
    for name, split in (
        ("training", train),
        ("validation", validation),
        ("test", test),
    ):
        if split.empty:
            raise RuntimeError(f"The {name} split is empty.")

        if split["future_high_risk"].nunique() < 2:
            raise RuntimeError(
                f"The {name} split must contain both target classes. "
                "Review the synthetic data or split dates."
            )


def select_model(results: dict) -> str:
    """Select the candidate with the best validation F1, then ROC-AUC."""
    def selection_key(name: str) -> tuple[float, float]:
        validation_metrics = results[name]["validation"]

        roc_auc = validation_metrics["roc_auc"]
        return (
            validation_metrics["f1"],
            float(roc_auc) if roc_auc is not None else -1.0,
        )

    return max(results, key=selection_key)


def write_reports(
    selected_model: str,
    results: dict,
    feature_columns: list[str],
) -> None:
    """Write machine-readable and Markdown model reports."""
    report = {
        "objective": (
            "Predict next-month high risk from current-month product signals."
        ),
        "target": (
            "future_high_risk: next month's rolling composite risk "
            "score is at least 0.55."
        ),
        "time_split": {
            "train": f"through {TRAIN_END_MONTH}",
            "validation": VALIDATION_MONTH,
            "test": TEST_MONTHS,
        },
        "model_selection": (
            "Highest validation F1, with validation ROC-AUC as tie-breaker."
        ),
        "selected_model": selected_model,
        "deployment_training_window": (
            f"Through {VALIDATION_MONTH}; the selected pipeline is "
            "refitted on training plus validation data."
        ),
        "features": feature_columns,
        "results": results,
        "caveat": (
            "The dataset is synthetic and contains seeded patterns. "
            "Metrics demonstrate pipeline behavior; they do not estimate "
            "real-world production performance."
        ),
    }

    report_json_path = DOCS / "ML_MODEL_REPORT.json"
    report_json_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Product Pulse ML Model Report",
        "",
        f"Selected model: **{selected_model}**",
        "",
        "Chronological evaluation; the target is next-month product risk.",
        "",
        "| Model | Val F1 | Val ROC-AUC | Test F1 | Test ROC-AUC |",
        "|---|---:|---:|---:|---:|",
    ]

    for name, model_results in results.items():
        validation = model_results["validation"]
        test = model_results["test"]

        val_auc = validation["roc_auc"]
        test_auc = test["roc_auc"]

        val_auc_text = f"{val_auc:.3f}" if val_auc is not None else "N/A"
        test_auc_text = f"{test_auc:.3f}" if test_auc is not None else "N/A"

        lines.append(
            f"| {name} "
            f"| {validation['f1']:.3f} "
            f"| {val_auc_text} "
            f"| {test['f1']:.3f} "
            f"| {test_auc_text} |"
        )

    lines.extend(
        [
            "",
            (
                "**Important:** Evaluation metrics are calculated before "
                "the final refit. The test period is held out during both "
                "model selection and final training."
            ),
            "",
            (
                "**Data limitation:** This is a synthetic-data demonstration, "
                "not evidence of real-world model accuracy."
            ),
        ]
    )

    (DOCS / "ML_MODEL_REPORT.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    """Train candidates, evaluate them, save the winner, and export predictions."""
    df = load_training_data()

    train = df[df["month"] <= TRAIN_END_MONTH].copy()
    validation = df[df["month"] == VALIDATION_MONTH].copy()
    test = df[df["month"].isin(TEST_MONTHS)].copy()

    validate_splits(train, validation, test)

    model_candidates = create_model_candidates()
    results = {}

    X_train = train[FEATURE_COLUMNS]
    y_train = train["future_high_risk"]

    X_validation = validation[FEATURE_COLUMNS]
    y_validation = validation["future_high_risk"]

    X_test = test[FEATURE_COLUMNS]
    y_test = test["future_high_risk"]

    # Train on the training period and evaluate on later periods.
    for name, model in model_candidates.items():
        print(f"Training candidate: {name}")

        model.fit(X_train, y_train)

        results[name] = {
            "validation": metrics_for(
                model,
                X_validation,
                y_validation,
            ),
            "test": metrics_for(
                model,
                X_test,
                y_test,
            ),
        }

    selected_name = select_model(results)
    best_model = model_candidates[selected_name]

    # Refit the selected pipeline on training plus validation data.
    # The held-out October/November test labels are not used for fitting.
    training_and_validation = pd.concat(
        [train, validation],
        ignore_index=True,
    )

    best_model.fit(
        training_and_validation[FEATURE_COLUMNS],
        training_and_validation["future_high_risk"],
    )

    model_path = MODELS / "risk_model.joblib"
    joblib.dump(best_model, model_path)

    # Export probabilities for the labelled monthly rows. The saved model
    # supports live inference on the newest monthly features as well.
    all_probabilities = positive_class_probabilities(
        best_model,
        df[FEATURE_COLUMNS],
    )

    predictions = df[
        ["product_id", "month", "future_high_risk"]
    ].copy()

    predictions[
        "predicted_next_month_high_risk_probability"
    ] = all_probabilities.round(5)

    predictions["split"] = np.select(
        [
            predictions["month"] <= TRAIN_END_MONTH,
            predictions["month"] == VALIDATION_MONTH,
            predictions["month"].isin(TEST_MONTHS),
        ],
        ["train", "validation", "test"],
        default="not_evaluated",
    )

    predictions_path = DATA / "risk_model_predictions.csv"
    predictions.to_csv(predictions_path, index=False)

    write_reports(
        selected_model=selected_name,
        results=results,
        feature_columns=FEATURE_COLUMNS,
    )

    output = {
        "selected_model": selected_name,
        "model_path": str(model_path.relative_to(ROOT)),
        "predictions_path": str(predictions_path.relative_to(ROOT)),
        "report_path": str(
            (DOCS / "ML_MODEL_REPORT.json").relative_to(ROOT)
        ),
        "deployment_training_window": (
            f"through {VALIDATION_MONTH}"
        ),
        "results": results,
        "prediction_rows": int(len(predictions)),
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
