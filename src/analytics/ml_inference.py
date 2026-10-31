"""Live next-month risk inference."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from src.analytics.ml_features import (
    FEATURE_COLUMNS,
    build_model_features,
)

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "risk_model.joblib"


@lru_cache(maxsize=1)
def load_risk_model():
    """Load the trained model once per process."""
    if not MODEL_PATH.is_file():
        raise RuntimeError(
            "Trained model missing at models/risk_model.joblib. "
            "Run `python scripts/train_model.py` or rebuild Docker."
        )

    try:
        return joblib.load(MODEL_PATH)
    except Exception as exc:
        raise RuntimeError(
            "Could not load models/risk_model.joblib"
        ) from exc


def predict_latest_month(
    monthly: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    """Predict next-month high risk using each product's latest row."""
    features = build_model_features(monthly, products)

    if features.empty:
        raise RuntimeError("No product features available for inference")

    latest = (
        features.sort_values(["product_id", "month"])
        .groupby("product_id", sort=False, as_index=False)
        .tail(1)
        .copy()
    )

    model = load_risk_model()
    probabilities = model.predict_proba(latest[FEATURE_COLUMNS])

    classes = list(model.classes_)
    if 1 not in classes:
        raise RuntimeError("Model does not contain positive class 1")

    positive_index = classes.index(1)
    latest["predicted_next_month_high_risk_probability"] = (
        probabilities[:, positive_index].astype(float)
    )
    latest["predicted_next_month_high_risk"] = (
        latest["predicted_next_month_high_risk_probability"] >= 0.5
    )

    latest["ml_prediction_month"] = latest["month"].astype(str)
    latest["ml_prediction_target_month"] = latest["month"].map(
        lambda month: str(pd.Period(str(month), freq="M") + 1)
    )

    model_step = getattr(model, "named_steps", {}).get("model")
    latest["ml_model_name"] = type(
        model_step if model_step is not None else model
    ).__name__
    latest["ml_prediction_source"] = "live_model_inference"

    return latest[
        [
            "product_id",
            "predicted_next_month_high_risk_probability",
            "predicted_next_month_high_risk",
            "ml_prediction_month",
            "ml_prediction_target_month",
            "ml_model_name",
            "ml_prediction_source",
        ]
    ].reset_index(drop=True)