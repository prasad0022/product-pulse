"""Product Pulse investigation service.

The current version is deterministic so the end-to-end workflow can be tested
without an external LLM. The LLM response layer can be plugged in later.
"""

from pathlib import Path
from typing import Any
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
RAG_DIR = Path(__file__).resolve().parents[2] / "data" / "rag"

def _risk(product_id: str) -> dict:
    df = pd.read_csv(DATA_DIR / "product_risk_summary.csv")
    row = df.loc[df["product_id"] == product_id]
    if row.empty:
        raise ValueError(f"Unknown product_id: {product_id}")
    return row.iloc[0].to_dict()

def _trend(product_id: str) -> list[dict]:
    df = pd.read_csv(DATA_DIR / "product_metrics_monthly.csv")
    rows = df.loc[df["product_id"] == product_id].sort_values("month")
    return rows.to_dict(orient="records")

def _tickets(product_id: str) -> dict:
    df = pd.read_csv(DATA_DIR / "support_tickets.csv")
    rows = df.loc[df["product_id"] == product_id]
    if rows.empty:
        return {"count": 0, "issues": {}, "avg_resolution_hours": 0.0}
    return {
        "count": int(len(rows)),
        "issues": rows["issue_type"].value_counts().head(5).to_dict(),
        "avg_resolution_hours": round(float(rows["resolution_time_hours"].mean()), 2),
    }

def _knowledge(product_id: str, limit: int = 3) -> list[dict]:
    df = pd.read_csv(DATA_DIR / "knowledge_documents.csv")
    rows = df.loc[df["product_id"] == product_id].head(limit)
    return rows[["document_id","document_type","title","content"]].to_dict(orient="records")

def investigate_product(product_id: str) -> dict[str, Any]:
    """Return risk, evidence, likely causes and next actions for one product."""
    risk = _risk(product_id)
    trend = _trend(product_id)
    tickets = _tickets(product_id)
    knowledge = _knowledge(product_id)

    latest = trend[-1]
    previous = trend[-2] if len(trend) > 1 else trend[-1]

    drivers = []
    if float(latest["return_rate"]) > float(previous["return_rate"]) + 0.03:
        drivers.append("return rate is increasing")
    if float(latest["avg_rating"]) < float(previous["avg_rating"]) - 0.20:
        drivers.append("customer rating is declining")
    if float(latest["negative_review_rate"]) > 0.45:
        drivers.append("negative-review rate is elevated")
    if int(latest["support_ticket_count"]) >= 18:
        drivers.append("support-ticket volume is elevated")

    root_cause_candidates = []
    issue_text = " ".join(str(x).lower() for x in tickets["issues"].keys())
    for candidate in ["Battery / charging","Charging","Performance / motor","Product durability",
                      "Size / fit","Packaging / damage","Connectivity","Compatibility","General product issue"]:
        if candidate.lower() in issue_text:
            root_cause_candidates.append(candidate)

    if not root_cause_candidates:
        root_cause_candidates = [knowledge[0]["title"]] if knowledge else ["No consistent cause identified"]

    actions = []
    for doc in knowledge:
        text = str(doc["content"])
        marker = "Recommended operational actions:"
        if marker in text:
            actions.append(text.split(marker,1)[1].split("Warranty guidance:",1)[0].strip())

    return {
        "product": {
            "product_id": risk["product_id"],
            "product_name": risk["product_name"],
            "category": risk["category"],
            "brand": risk["brand"],
        },
        "risk": {
            "score": round(float(risk["risk_signal_score"]), 2),
            "level": risk["risk_level"],
            "latest_return_rate": round(float(risk["return_rate"]), 4),
            "latest_rating": round(float(risk["avg_rating"]), 2),
        },
        "risk_drivers": drivers,
        "support_evidence": tickets,
        "knowledge_evidence": [
            {k: doc[k] for k in ["document_id","document_type","title","content"]}
            for doc in knowledge
        ],
        "likely_root_causes": root_cause_candidates[:3],
        "recommended_actions": actions[:3],
        "note": "This is decision-support output. It should not be treated as proof of causality.",
    }
