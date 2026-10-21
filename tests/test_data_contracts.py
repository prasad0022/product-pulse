from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"

def test_core_tables_exist_and_nonempty():
    required = [
        "products.csv","customers.csv","orders.csv","order_items.csv",
        "returns.csv","reviews.csv","support_tickets.csv",
        "product_metrics_monthly.csv","product_risk_labels.csv"
    ]
    for name in required:
        df = pd.read_csv(DATA / name)
        assert not df.empty, name

def test_product_ids_are_unique():
    df = pd.read_csv(DATA / "products.csv")
    assert df["product_id"].is_unique

def test_orders_reference_valid_customers():
    customers = pd.read_csv(DATA / "customers.csv")
    orders = pd.read_csv(DATA / "orders.csv")
    assert set(orders["customer_id"]).issubset(set(customers["customer_id"]))

def test_order_items_reference_products_and_orders():
    products = pd.read_csv(DATA / "products.csv")
    orders = pd.read_csv(DATA / "orders.csv")
    items = pd.read_csv(DATA / "order_items.csv")
    assert set(items["product_id"]).issubset(set(products["product_id"]))
    assert set(items["order_id"]).issubset(set(orders["order_id"]))
