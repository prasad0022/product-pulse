"""Read-only product analytics tools used by the API and AI investigation."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from src.analytics.ml_inference import predict_latest_month

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


def _read(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        raise RuntimeError(f"Required data file is missing: {path.name}. Run scripts/generate_data.py first.")
    return pd.read_csv(path)

def _risk_frame() -> pd.DataFrame:
    """Combine business risk signals with live ML predictions."""
    frame = _read("product_risk_summary.csv")
    monthly = _read("product_metrics_monthly.csv")
    products = _read("products.csv")

    predictions = predict_latest_month(monthly, products)

    return frame.merge(
        predictions,
        on="product_id",
        how="left",
        validate="one_to_one",
    )

def get_products(limit: int = 40) -> list[dict]:
    df = _risk_frame().sort_values("risk_signal_score", ascending=False).head(max(1, min(limit, 100)))
    return df.where(pd.notna(df), None).to_dict(orient="records")


def get_product_risk(product_id: str) -> dict:
    df = _risk_frame()
    row = df.loc[df["product_id"] == product_id]
    if row.empty:
        raise ValueError(f"Unknown product_id: {product_id}")
    return row.iloc[0].where(pd.notna(row.iloc[0]), None).to_dict()


def get_product_trend(product_id: str) -> list[dict]:
    df = _read("product_metrics_monthly.csv")
    rows = df.loc[df["product_id"] == product_id].sort_values("month")
    if rows.empty:
        raise ValueError(f"Unknown product_id: {product_id}")
    return rows[["month", "orders", "units_sold", "returned_units", "return_rate", "avg_rating", "negative_review_rate", "support_ticket_count"]].to_dict(orient="records")


def get_ticket_summary(product_id: str) -> dict:
    df = _read("support_tickets.csv")
    rows = df.loc[df["product_id"] == product_id]
    if rows.empty:
        return {"ticket_count": 0, "top_issue_types": {}, "avg_resolution_hours": 0.0}
    return {
        "ticket_count": int(len(rows)),
        "top_issue_types": rows["issue_type"].value_counts().head(5).to_dict(),
        "avg_resolution_hours": round(float(rows["resolution_time_hours"].mean()), 2),
    }


def get_portfolio_summary() -> dict:
    products = _risk_frame()
    orders = _read("orders.csv")
    items = _read("order_items.csv")
    returns = _read("returns.csv")
    reviews = _read("reviews.csv")
    units = float(items["quantity"].sum()) if not items.empty else 0.0
    returned = float(returns["returned_quantity"].sum()) if not returns.empty and "returned_quantity" in returns else float(len(returns))
    revenue = float((items["quantity"] * items["unit_price"]).sum()) if not items.empty else 0.0
    return {
        "product_count": int(products["product_id"].nunique()),
        "high_risk_count": int((products["risk_level"] == "High").sum()),
        "medium_risk_count": int((products["risk_level"] == "Medium").sum()),
        "low_risk_count": int((products["risk_level"] == "Low").sum()),
        "order_count": int(orders["order_id"].nunique()),
        "units_sold": int(units),
        "overall_return_rate": round(returned / units, 4) if units else 0.0,
        "average_rating": round(float(reviews["rating"].mean()), 2) if not reviews.empty else None,
        "review_count": int(len(reviews)),
        "support_ticket_count": int(len(_read("support_tickets.csv"))),
        "gross_revenue": round(revenue, 2),
        "data_period": "2025-01 to 2025-12",
        "data_type": "synthetic demo data",
    }
