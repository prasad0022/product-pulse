"""Generate all reproducible Product Pulse synthetic data and derived data artifacts.

Run from the repository root:
    python scripts/generate_data.py

All records are synthetic; no real customer or company data is used.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
RAG_DATA = ROOT / "data" / "rag"
DOCS = ROOT / "docs"
for directory in (DATA, RAG_DATA, DOCS):
    directory.mkdir(parents=True, exist_ok=True)

CATEGORIES = {
    "Electronics": ["Smartphone", "Wireless Earbuds", "Smartwatch", "Bluetooth Speaker", "Tablet", "Power Bank", "Webcam", "Router"],
    "Home Appliances": ["Air Fryer", "Mixer Grinder", "Vacuum Cleaner", "Electric Kettle", "Room Heater", "Air Purifier", "Coffee Maker"],
    "Fitness & Wearables": ["Fitness Band", "Smart Scale", "Massage Gun", "Yoga Mat", "Exercise Bike", "Treadmill"],
    "Personal Care": ["Hair Dryer", "Electric Shaver", "Trimmer", "Face Cleansing Brush", "Water Flosser", "Hair Styler"],
    "Home & Kitchen": ["Non-stick Cookware Set", "Food Storage Set", "Water Bottle", "Desk Lamp", "Kitchen Scale", "Knife Set", "Bedsheet Set"],
    "Accessories": ["Laptop Sleeve", "USB-C Hub", "Phone Case", "Charging Cable", "Wireless Charger", "Car Phone Mount"],
}
BRANDS = ["Nova", "Pulse", "Vertex", "Aster", "Orbit", "Zenith", "Nexora", "Lumio"]
REGIONS = ["North", "South", "East", "West", "Central"]
SEGMENTS = ["Value", "Standard", "Premium"]
CHANNELS = ["Web", "Mobile App", "Marketplace"]
PAYMENTS = ["UPI", "Card", "NetBanking", "COD"]
RISK_PROFILES = {
    "P1005": "battery", "P1013": "motor", "P1018": "charging", "P1024": "durability",
    "P1029": "size_fit", "P1034": "packaging", "P1037": "connectivity", "P1040": "compatibility",
}
ISSUES = {
    "battery": ("Battery / charging", ["Battery drains much faster than expected.", "Charging has become unreliable after a few weeks.", "Battery backup is poor compared with expectations."], ["Battery issue", "Poor battery life", "Charging problem"], "battery cell degradation or charging-module instability", "verify the affected batch, inspect the charging module, review supplier quality"),
    "motor": ("Performance / motor", ["The motor started making unusual noise.", "Performance dropped after a few weeks.", "The device stopped working during normal use."], ["Stopped working", "Motor noise", "Performance issue"], "motor assembly or component quality issue", "inspect motor assembly and review supplier batch quality"),
    "charging": ("Charging", ["Charging is intermittent.", "The device does not always recognize the charger.", "Power connection is unreliable."], ["Charging problem", "Does not charge", "Intermittent power"], "charging-port or power-controller instability", "inspect the charging interface and test the power controller"),
    "durability": ("Product durability", ["The product broke sooner than expected.", "Build quality does not feel durable.", "A component became loose after limited use."], ["Damaged/defective", "Poor durability", "Product broke"], "material/component durability issue", "inspect failed components and review material specifications"),
    "size_fit": ("Size / fit", ["The size did not match the description.", "Fit is uncomfortable.", "Sizing information was misleading."], ["Wrong size", "Poor fit", "Size mismatch"], "sizing specification or product-dimension issue", "review dimensions, update listing measurements, validate the size chart"),
    "packaging": ("Packaging / damage", ["The item arrived with damaged packaging.", "The product box was crushed during delivery.", "The item arrived with visible damage."], ["Damaged package", "Damaged product", "Packaging issue"], "insufficient packaging protection or handling damage", "review packaging design and carrier handling"),
    "connectivity": ("Connectivity", ["Connection drops frequently.", "Pairing is unreliable.", "The device disconnects unexpectedly."], ["Connection drops", "Connectivity issue", "Pairing problem"], "firmware/connectivity-module instability", "review firmware version and test the connectivity module"),
    "compatibility": ("Compatibility", ["It does not work with my device.", "Compatibility information is unclear.", "The accessory is incompatible with my setup."], ["Compatibility issue", "Does not work with device", "Compatibility mismatch"], "compatibility limitation or unclear product specification", "validate supported devices and improve product documentation"),
    "none": ("General product issue", ["Good quality and works as expected.", "Happy with the purchase.", "Value for money.", "Performance is acceptable."], ["Changed mind", "Not as expected", "Damaged in transit", "Other"], "no consistent product-level failure pattern identified", "continue monitoring and review issue trends"),
}


def save(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)
    print(f"{path.relative_to(ROOT)}: {len(df):,} rows")


def make_products(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    number = 1001
    for category, names in CATEGORIES.items():
        for name in names:
            if len(rows) >= 40:
                break
            rows.append({
                "product_id": f"P{number}",
                "product_name": f"{BRANDS[(number - 1001) % len(BRANDS)]} {name}",
                "category": category,
                "brand": BRANDS[(number - 999) % len(BRANDS)],
                "base_price": round(float(rng.uniform(35, 650)), 2),
                "launch_date": "2024-10-01",
                "risk_profile": RISK_PROFILES.get(f"P{number}", "none"),
            })
            # Set reproducible launch date from a timestamp rather than a constant.
            rows[-1]["launch_date"] = (pd.Timestamp("2024-10-01") + pd.Timedelta(days=int(rng.integers(0, 273)))).date().isoformat()
            number += 1
        if len(rows) >= 40:
            break
    return pd.DataFrame(rows)


def main() -> None:
    rng = np.random.default_rng(SEED)
    random.seed(SEED)

    products = make_products(rng)
    customers = pd.DataFrame([{
        "customer_id": f"C{i:04d}",
        "customer_segment": rng.choice(SEGMENTS, p=[0.30, 0.50, 0.20]),
        "region": rng.choice(REGIONS),
        "signup_date": (pd.Timestamp("2024-01-01") + pd.Timedelta(days=int(rng.integers(0, 365)))).date().isoformat(),
    } for i in range(1, 501)])

    product_weights = rng.uniform(0.7, 1.4, len(products))
    product_weights /= product_weights.sum()
    orders, items = [], []
    order_no = item_no = 1
    monthly_order_counts = [360, 370, 390, 400, 410, 420, 420, 430, 440, 450, 450, 470]
    for month_start, count in zip(pd.date_range("2025-01-01", "2025-12-01", freq="MS"), monthly_order_counts):
        month_end = month_start + pd.offsets.MonthEnd(1)
        for _ in range(count):
            order_id = f"O{order_no:05d}"; order_no += 1
            customer_id = str(rng.choice(customers.customer_id.values))
            order_date = month_start + pd.Timedelta(days=int(rng.integers(0, month_start.days_in_month)))
            order_status = str(rng.choice(["Delivered", "Cancelled"], p=[0.94, 0.06]))
            orders.append({
                "order_id": order_id, "customer_id": customer_id,
                "order_date": order_date.date().isoformat(),
                "order_status": order_status,
                "payment_method": rng.choice(PAYMENTS, p=[0.38, 0.34, 0.13, 0.15]),
                "channel": rng.choice(CHANNELS, p=[0.42, 0.38, 0.20]),
            })
            if order_status != "Delivered":
                continue
            n_items = int(rng.choice([1, 1, 1, 1, 2, 2, 3], p=[0.28, 0.16, 0.16, 0.12, 0.14, 0.09, 0.05]))
            chosen = rng.choice(products.product_id.values, size=n_items, replace=False, p=product_weights)
            for product_id in chosen:
                product = products.loc[products.product_id == product_id].iloc[0]
                quantity = int(rng.choice([1, 1, 1, 2], p=[0.60, 0.20, 0.15, 0.05]))
                items.append({"order_item_id": f"OI{item_no:06d}", "order_id": order_id, "product_id": product_id,
                              "quantity": quantity, "unit_price": round(max(10, float(product.base_price * rng.normal(1, 0.05))), 2)})
                item_no += 1
    orders = pd.DataFrame(orders); items = pd.DataFrame(items)
    order_dates = orders.set_index("order_id").order_date.to_dict()
    item_to_order = items.set_index("order_item_id").order_id.to_dict()
    item_to_product = items.set_index("order_item_id").product_id.to_dict()
    item_to_qty = items.set_index("order_item_id").quantity.to_dict()
    product_profiles = products.set_index("product_id").risk_profile.to_dict()

    returns = []
    return_no = 1
    for _, item in items.iterrows():
        order_date = pd.Timestamp(order_dates[item.order_id]); month = order_date.month
        profile = product_profiles[item.product_id]
        if profile == "none":
            probability = 0.052
        else:
            ramp = max(0, month - 2) / 10
            probability = 0.045 + 0.235 * ramp
        if month in (10, 11, 12): probability *= 1.06
        if rng.random() < min(probability, 0.38):
            info = ISSUES[profile]
            return_date = min(order_date + pd.Timedelta(days=int(rng.integers(2, 15))), pd.Timestamp("2025-12-31"))
            returns.append({"return_id": f"R{return_no:06d}", "order_item_id": item.order_item_id,
                            "return_date": return_date.date().isoformat(), "return_reason": rng.choice(info[2]),
                            "return_status": rng.choice(["Approved", "Refunded"], p=[0.25, 0.75]),
                            "returned_quantity": int(item.quantity)})
            return_no += 1
    returns = pd.DataFrame(returns, columns=["return_id", "order_item_id", "return_date", "return_reason", "return_status", "returned_quantity"])

    # Reviews are linked to real generated order items and occur within the order's month.
    selected_items = items.sample(n=min(2200, len(items)), random_state=SEED)
    reviews = []
    for n, (_, item) in enumerate(selected_items.iterrows(), 1):
        order_date = pd.Timestamp(order_dates[item.order_id]); product_id = item.product_id
        profile = product_profiles[product_id]; month = order_date.month
        neg_prob = min(0.15 + 0.48 * max(0, month - 2) / 10, 0.72) if profile != "none" else 0.16
        negative = rng.random() < neg_prob
        if negative:
            rating = int(rng.choice([1, 2, 3], p=[0.30, 0.45, 0.25]))
            review_text = rng.choice(ISSUES[profile][1] if profile != "none" else ["Delivery was late.", "Expected better quality.", "The product is okay but not great."])
        else:
            rating = int(rng.choice([4, 5], p=[0.35, 0.65])); review_text = rng.choice(ISSUES["none"][1])
        days_left = (order_date + pd.offsets.MonthEnd(0) - order_date).days
        review_date = order_date + pd.Timedelta(days=int(rng.integers(0, max(1, min(20, days_left) + 1))))
        reviews.append({"review_id": f"RV{n:06d}", "product_id": product_id,
                        "customer_id": str(rng.choice(customers.customer_id.values)),
                        "review_date": review_date.date().isoformat(), "rating": rating, "review_text": review_text})
    reviews = pd.DataFrame(reviews)

    # Ticket volume is deliberately higher for at-risk products and grows later in the year.
    tickets = []
    for n in range(1, 1001):
        product_id = str(rng.choice(products.product_id.values, p=product_weights))
        profile = product_profiles[product_id]
        month = int(rng.integers(1, 13)); day = int(rng.integers(1, 28))
        date = pd.Timestamp(year=2025, month=month, day=day)
        issue, symptoms, _, _, _ = ISSUES[profile]
        priority_probs = [0.30, 0.48, 0.18, 0.04] if profile == "none" else [0.18, 0.44, 0.30, 0.08]
        priority = str(rng.choice(["Low", "Medium", "High", "Critical"], p=priority_probs))
        resolution_hours = max(1.0, float(rng.gamma(2.1, 5.0) * (1.25 if priority in ("High", "Critical") else 1.0)))
        tickets.append({"ticket_id": f"T{n:06d}", "product_id": product_id,
                        "customer_id": str(rng.choice(customers.customer_id.values)), "created_at": date.isoformat(),
                        "issue_type": issue, "priority": priority, "resolution_time_hours": round(resolution_hours, 2),
                        "resolution_status": rng.choice(["Resolved", "Pending", "Escalated"], p=[0.84, 0.11, 0.05]),
                        "ticket_text": rng.choice(symptoms)})
    tickets = pd.DataFrame(tickets)

    # Monthly product metrics: product/order cohorts ensure returns attach to the order month.
    order_month = orders.assign(month=pd.to_datetime(orders.order_date).dt.to_period("M").astype(str))[ ["order_id", "month"] ]
    item_month = items.merge(order_month, on="order_id", how="left")
    monthly = item_month.groupby(["product_id", "month"], as_index=False).agg(orders=("order_id", "nunique"), units_sold=("quantity", "sum"))
    monthly = monthly.rename(columns={"product_id": "product_id"})

    if not returns.empty:
        return_rows = returns[["return_id", "order_item_id", "returned_quantity"]].merge(items[["order_item_id", "product_id", "order_id"]], on="order_item_id", how="left")
        return_rows = return_rows.merge(order_month, on="order_id", how="left")
        returned = return_rows.groupby(["product_id", "month"], as_index=False).agg(returned_units=("returned_quantity", "sum"))
        monthly = monthly.merge(returned, on=["product_id", "month"], how="left")
    else:
        monthly["returned_units"] = 0
    monthly["returned_units"] = monthly["returned_units"].fillna(0).astype(int)

    reviews_m = reviews.assign(month=pd.to_datetime(reviews.review_date).dt.to_period("M").astype(str))
    review_metrics = reviews_m.assign(negative=reviews_m.rating <= 3).groupby(["product_id", "month"], as_index=False).agg(
        avg_rating=("rating", "mean"), review_count=("review_id", "count"), negative_review_rate=("negative", "mean"))
    monthly = monthly.merge(review_metrics, on=["product_id", "month"], how="left")
    tickets_m = tickets.assign(month=pd.to_datetime(tickets.created_at).dt.to_period("M").astype(str))
    ticket_metrics = tickets_m.groupby(["product_id", "month"], as_index=False).agg(support_ticket_count=("ticket_id", "count"))
    monthly = monthly.merge(ticket_metrics, on=["product_id", "month"], how="left")

    all_months = [x.strftime("%Y-%m") for x in pd.date_range("2025-01-01", "2025-12-01", freq="MS")]
    grid = pd.MultiIndex.from_product([products.product_id.tolist(), all_months], names=["product_id", "month"]).to_frame(index=False)
    monthly = grid.merge(monthly, on=["product_id", "month"], how="left")
    for col, default in {"orders": 0, "units_sold": 0, "returned_units": 0, "avg_rating": 4.0, "review_count": 0, "negative_review_rate": 0.0, "support_ticket_count": 0}.items():
        monthly[col] = monthly[col].fillna(default)
    for col in ["orders", "units_sold", "returned_units", "review_count", "support_ticket_count"]:
        monthly[col] = monthly[col].astype(int)
    monthly["return_rate"] = (monthly.returned_units / monthly.units_sold.replace(0, np.nan)).fillna(0).clip(0, 1).round(4)
    monthly["avg_rating"] = monthly.avg_rating.round(3)
    monthly["negative_review_rate"] = monthly.negative_review_rate.round(4)
    monthly = monthly.sort_values(["product_id", "month"]).reset_index(drop=True)

    # Risk labels: current month predicts next month's composite risk signal.
    m = monthly.copy()
    for col, name in [("return_rate", "return_rate_3m"), ("avg_rating", "rating_3m"), ("negative_review_rate", "negative_rate_3m"), ("support_ticket_count", "tickets_3m")]:
        m[name] = m.groupby("product_id")[col].transform(lambda s: s.rolling(3, min_periods=1).mean())
    m["signal_score"] = (
        0.45 * np.clip(m.return_rate_3m / 0.16, 0, 1)
        + 0.25 * np.clip((5 - m.rating_3m) / 2.2, 0, 1)
        + 0.20 * np.clip(m.negative_rate_3m / 0.55, 0, 1)
        + 0.10 * np.clip(m.tickets_3m / 15, 0, 1)
    )
    m["future_signal_score"] = m.groupby("product_id").signal_score.shift(-1)
    m["future_high_risk"] = (m.future_signal_score >= 0.55).astype(int)
    m["risk_score"] = (m.signal_score * 100).round(2)
    m["risk_level"] = pd.cut(m.risk_score, [-np.inf, 30, 60, np.inf], labels=["Low", "Medium", "High"]).astype(str)
    labels = m.loc[m.month != "2025-12", ["product_id", "month", "risk_score", "risk_level", "future_high_risk"]].copy()
    monthly_metrics = monthly[["product_id", "month", "orders", "units_sold", "returned_units", "return_rate", "avg_rating", "review_count", "negative_review_rate", "support_ticket_count"]].copy()

    # Current portfolio risk summary uses the latest three-month product signals.
    summary = m[m.month == "2025-12"].merge(products[["product_id", "product_name", "category", "brand"]], on="product_id", how="left")
    # Display smoothed trailing-three-month signals so a low-volume single month
    # does not dominate the portfolio prioritization.
    summary["return_rate"] = summary["return_rate_3m"]
    summary["avg_rating"] = summary["rating_3m"]
    summary["negative_review_rate"] = summary["negative_rate_3m"]
    summary["support_ticket_count"] = summary["tickets_3m"].round(1)
    summary["risk_signal_score"] = summary.risk_score
    summary = summary[["product_id", "product_name", "category", "brand", "return_rate", "avg_rating", "negative_review_rate", "support_ticket_count", "risk_signal_score", "risk_level"]].sort_values("risk_signal_score", ascending=False)

    # Product knowledge documents and chunks.
    knowledge = []
    doc_no = 1
    for _, p in products.iterrows():
        profile = p.risk_profile; issue, symptoms, _, cause, actions = ISSUES[profile]
        content = (f"Product: {p.product_name}\nProduct ID: {p.product_id}\nCategory: {p.category}\nBrand: {p.brand}\n\n"
                   f"Purpose: Product usage, warranty, troubleshooting and quality investigation guidance.\n"
                   f"Known symptoms: {'; '.join(symptoms)}\nPotential root cause: {cause}.\n"
                   f"Recommended operational actions: {actions}.\n"
                   "Warranty guidance: Inspect the unit and available usage evidence before replacement. Record recurring defects by product or batch.\n"
                   "Escalation: Repeated or clustered failures should be reviewed by the quality team.")
        knowledge.append({"document_id": f"D{doc_no:04d}", "product_id": p.product_id, "document_type": "product_knowledge", "title": f"{p.product_name} — Product & Warranty Guide", "content": content})
        doc_no += 1
    for product_id, profile in RISK_PROFILES.items():
        p = products.loc[products.product_id == product_id].iloc[0]
        issue, symptoms, _, cause, actions = ISSUES[profile]
        knowledge.append({"document_id": f"D{doc_no:04d}", "product_id": product_id, "document_type": "historical_rca", "title": f"Historical RCA — {p.product_name}",
                          "content": f"Historical incident review for {p.product_name} ({product_id}). Observed symptoms: {'; '.join(symptoms)}. A previous investigation identified {cause} as a likely cause. Recommended actions: {actions}. This record is supporting evidence only and does not prove the cause of a current problem."})
        doc_no += 1
    knowledge = pd.DataFrame(knowledge)

    chunk_rows = []
    chunk_no = 1
    for _, doc in knowledge.iterrows():
        words = str(doc.content).split(); start = 0; chunk_idx = 0
        while start < len(words):
            end = min(start + 120, len(words))
            chunk_rows.append({"chunk_id": f"CH{chunk_no:05d}", "document_id": doc.document_id, "product_id": doc.product_id,
                               "document_type": doc.document_type, "title": doc.title, "chunk_index": chunk_idx, "text": " ".join(words[start:end])})
            chunk_no += 1; chunk_idx += 1
            if end == len(words): break
            start = end - 20
    chunks = pd.DataFrame(chunk_rows)

    eval_queries = pd.DataFrame([
        ("Q001", "P1005", "battery drains quickly and product does not charge reliably", "battery|charging"),
        ("Q002", "P1013", "product makes unusual motor noise and loses performance", "motor|performance"),
        ("Q003", "P1018", "intermittent charging and power connection failures", "charging|power"),
        ("Q004", "P1024", "product breaks early and has poor durability", "durability|component"),
        ("Q005", "P1029", "customers report wrong size and poor fit", "size|fit"),
        ("Q006", "P1034", "customers receive products with damaged packaging", "packaging|damage"),
        ("Q007", "P1037", "device disconnects and has pairing problems", "connectivity|pairing"),
        ("Q008", "P1040", "accessory is not compatible with the customer's device", "compatibility|compatible"),
    ], columns=["query_id", "product_id", "query", "expected_terms"])

    # Save artifacts.
    outputs = {
        "products.csv": products, "customers.csv": customers, "orders.csv": orders,
        "order_items.csv": items, "returns.csv": returns, "reviews.csv": reviews,
        "support_tickets.csv": tickets, "product_metrics_monthly.csv": monthly_metrics,
        "product_risk_labels.csv": labels, "knowledge_documents.csv": knowledge,
        "product_risk_summary.csv": summary,
    }
    for filename, frame in outputs.items(): save(frame, DATA / filename)
    save(chunks, RAG_DATA / "document_chunks.csv")
    save(eval_queries, RAG_DATA / "rag_eval_queries.csv")

    meta = {
        "seed": SEED, "data_period": {"orders_start": "2025-01-01", "orders_end": "2025-12-31"},
        "synthetic_data": True, "counts": {name.removesuffix(".csv"): len(frame) for name, frame in outputs.items()},
        "rag_chunks": len(chunks), "evaluation_queries": len(eval_queries),
        "seeded_risk_products": sorted(RISK_PROFILES),
    }
    (DOCS / "DATA_GENERATION_METADATA.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (DOCS / "DATA_GENERATION.md").write_text(
        "# Product Pulse Synthetic Data\n\n"
        "All data in this capstone is synthetic and generated programmatically; it does not represent real customer/company records.\n\n"
        "- Period: January–December 2025 order history\n- Fixed random seed: 42\n- Products: 40 across 6 categories\n- Customers: 500\n- Orders: 5,010\n- Review/ticket text is generated from controlled issue profiles.\n"
        "- Eight products have deliberately seeded risk patterns so evaluation and demos are reproducible.\n\n"
        "Rebuild all core data with `python scripts/generate_data.py`.\n", encoding="utf-8")

    # Remove stale model outputs so regenerated data cannot be mixed with an older trained model.
    for stale in [DATA / "ml_test_predictions.csv", DATA / "ml_test_predictions_v1.csv", DATA / "risk_model_predictions.csv", DATA / "product_ml_features_v0.csv"]:
        if stale.exists(): stale.unlink()
    model_dir = ROOT / "models"
    if model_dir.exists():
        for p in model_dir.glob("risk_model*.*"): p.unlink()
    print("\nGeneration complete. All data is synthetic and reproducible with seed 42.")
    print(f"Products: {len(products)} | Orders: {len(orders)} | Reviews: {len(reviews)} | Returns: {len(returns)} | Tickets: {len(tickets)}")

if __name__ == "__main__":
    main()
