"""Validate Product Pulse dataset integrity and write a report."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
DOCS = ROOT / "docs"
TABLES = ["products.csv", "customers.csv", "orders.csv", "order_items.csv", "returns.csv", "reviews.csv", "support_tickets.csv", "product_metrics_monthly.csv", "product_risk_labels.csv", "knowledge_documents.csv", "product_risk_summary.csv"]


def main():
    frames = {name: pd.read_csv(DATA / name) for name in TABLES}
    products, customers, orders, items, returns = (frames[x] for x in ["products.csv", "customers.csv", "orders.csv", "order_items.csv", "returns.csv"])
    reviews, tickets, metrics, labels = (frames[x] for x in ["reviews.csv", "support_tickets.csv", "product_metrics_monthly.csv", "product_risk_labels.csv"])
    docs = frames["knowledge_documents.csv"]
    chunks = pd.read_csv(ROOT / "data" / "rag" / "document_chunks.csv")
    checks = {
        "exactly_40_products": len(products) == 40,
        "unique_product_ids": products.product_id.is_unique,
        "unique_customer_ids": customers.customer_id.is_unique,
        "unique_order_ids": orders.order_id.is_unique,
        "unique_order_item_ids": items.order_item_id.is_unique,
        "unique_return_ids": returns.return_id.is_unique,
        "unique_review_ids": reviews.review_id.is_unique,
        "unique_ticket_ids": tickets.ticket_id.is_unique,
        "orders_reference_customers": set(orders.customer_id).issubset(set(customers.customer_id)),
        "items_reference_orders": set(items.order_id).issubset(set(orders.order_id)),
        "items_reference_products": set(items.product_id).issubset(set(products.product_id)),
        "returns_reference_order_items": set(returns.order_item_id).issubset(set(items.order_item_id)),
        "reviews_reference_products": set(reviews.product_id).issubset(set(products.product_id)),
        "reviews_reference_customers": set(reviews.customer_id).issubset(set(customers.customer_id)),
        "tickets_reference_products": set(tickets.product_id).issubset(set(products.product_id)),
        "tickets_reference_customers": set(tickets.customer_id).issubset(set(customers.customer_id)),
        "monthly_metrics_have_480_rows": len(metrics) == 40 * 12,
        "monthly_metric_product_month_unique": not metrics.duplicated(["product_id", "month"]).any(),
        "labels_exclude_december": not labels.month.astype(str).str.endswith("12").any(),
        "labels_reference_products": set(labels.product_id).issubset(set(products.product_id)),
        "knowledge_docs_reference_products": set(docs.product_id).issubset(set(products.product_id)),
        "chunks_reference_documents": set(chunks.document_id).issubset(set(docs.document_id)),
        "return_rates_in_range": metrics.return_rate.between(0, 1).all(),
        "ratings_in_range": metrics.avg_rating.between(1, 5).all(),
    }
    checks = {key: bool(value) for key, value in checks.items()}
    table_stats = []
    for name, df in frames.items():
        table_stats.append({"file": name, "rows": len(df), "columns": len(df.columns), "missing_cells": int(df.isna().sum().sum()), "duplicate_rows": int(df.duplicated().sum())})
    result = {"all_checks_passed": all(checks.values()), "checks": checks, "tables": table_stats, "rag_chunks": len(chunks)}
    report_lines = ["# Product Pulse Data Validation Report", "", f"Overall result: **{'PASS' if result['all_checks_passed'] else 'FAIL'}**", "", "## Checks"]
    report_lines.extend([f"- [{'x' if ok else ' '}] {key.replace('_', ' ')}" for key, ok in checks.items()])
    report_lines += ["", "## Table statistics", "", "| File | Rows | Columns | Missing cells | Duplicate rows |", "|---|---:|---:|---:|---:|"]
    report_lines.extend([f"| `{x['file']}` | {x['rows']:,} | {x['columns']} | {x['missing_cells']} | {x['duplicate_rows']} |" for x in table_stats])
    report_lines += ["", f"RAG chunks: {len(chunks):,}", "", "All input records are synthetic demo data."]
    (DOCS / "DATA_VALIDATION_REPORT.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    (DOCS / "DATA_VALIDATION_REPORT.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"all_checks_passed": result["all_checks_passed"], "checks_passed": sum(checks.values()), "checks_total": len(checks)}, indent=2))
    if not result["all_checks_passed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
