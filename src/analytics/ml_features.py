"""Shared feature engineering for Product Pulse's risk model."""
from __future__ import annotations

import pandas as pd

FEATURE_COLUMNS = [
    "orders",
    "units_sold",
    "returned_units",
    "return_rate",
    "avg_rating",
    "review_count",
    "negative_review_rate",
    "support_ticket_count",
    "return_rate_3m_avg",
    "rating_3m_avg",
    "negative_review_rate_3m_avg",
    "ticket_count_3m_avg",
    "return_rate_change_1m",
    "avg_rating_change_1m",
    "negative_review_rate_change_1m",
    "support_ticket_count_change_1m",
    "category",
    "brand",
]

ROLLING_FEATURES = [
    ("return_rate", "return_rate_3m_avg"),
    ("avg_rating", "rating_3m_avg"),
    ("negative_review_rate", "negative_review_rate_3m_avg"),
    ("support_ticket_count", "ticket_count_3m_avg"),
]


def build_model_features(
    monthly: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    """Build model inputs in chronological order for each product."""
    required_monthly = {
        "product_id", "month", "orders", "units_sold",
        "returned_units", "return_rate", "avg_rating",
        "review_count", "negative_review_rate",
        "support_ticket_count",
    }
    missing = required_monthly.difference(monthly.columns)
    if missing:
        raise ValueError(
            f"Monthly metrics missing columns: {sorted(missing)}"
        )

    required_products = {"product_id", "category", "brand"}
    missing = required_products.difference(products.columns)
    if missing:
        raise ValueError(
            f"Product metadata missing columns: {sorted(missing)}"
        )

    df = monthly.sort_values(["product_id", "month"]).copy()
    grouped = df.groupby("product_id", sort=False)

    for source, target in ROLLING_FEATURES:
        df[target] = grouped[source].transform(
            lambda values: values.rolling(3, min_periods=1).mean()
        )
        df[f"{source}_change_1m"] = (
            grouped[source].diff().fillna(0)
        )

    df = df.merge(
        products[["product_id", "category", "brand"]],
        on="product_id",
        how="left",
    )

    if df[["category", "brand"]].isna().any().any():
        raise ValueError(
            "Some product metrics have no matching category/brand metadata"
        )

    return df