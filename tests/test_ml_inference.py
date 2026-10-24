import math

from src.analytics.product_tools import (
    get_product_risk,
    get_products,
)


def test_risk_contains_live_model_prediction():
    result = get_product_risk("P1029")

    probability = result[
        "predicted_next_month_high_risk_probability"
    ]

    assert isinstance(probability, (float, int))
    assert math.isfinite(probability)
    assert 0.0 <= probability <= 1.0

    assert isinstance(
        result["predicted_next_month_high_risk"], bool
    )
    assert result["ml_prediction_source"] == "live_model_inference"
    assert result["ml_prediction_month"] == "2025-12"
    assert result["ml_prediction_target_month"] == "2026-01"
    assert result["ml_model_name"] in {
        "LogisticRegression",
        "RandomForestClassifier",
    }


def test_all_products_have_live_predictions():
    results = get_products(limit=100)

    assert len(results) == 40
    assert all(
        row["ml_prediction_source"] == "live_model_inference"
        for row in results
    )
    assert all(
        0.0 <= row["predicted_next_month_high_risk_probability"] <= 1.0
        for row in results
    )