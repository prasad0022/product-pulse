import json
from typing import Any

def build_synthesis_prompt(question: str, product_id: str, business_evidence: dict, rag_sources: list[dict]) -> str:
    evidence_text = json.dumps(business_evidence, indent=2, default=str)
    source_text = "\n\n".join(
        f"[SOURCE {s['document_id']}] {s['title']}\n{s['text']}"
        for s in rag_sources
    )
    return f"""You are Product Pulse, an AI product-risk investigation assistant.

Product: {product_id}
Business question: {question}

Structured business evidence:
{evidence_text}

Retrieved knowledge sources:
{source_text}

Rules:
- Do not invent metrics, causes, documents, or actions.
- Separate observed evidence from inferred root-cause candidates.
- Do not claim causal certainty from observational data.
- Cite retrieved knowledge using SOURCE IDs.
- Keep the answer concise and business-oriented.
- Return valid JSON only.

Keys:
findings, evidence, root_cause_candidates, recommended_actions, sources, disclaimer
"""

def fallback_response(product_id: str, risk: dict, trends: list[dict], tickets: dict, sources: list[dict]) -> dict[str, Any]:
    """Build a useful cited response without requiring an external LLM API."""
    import re

    latest = trends[-1] if trends else {}
    findings = [
        f"{risk['product_name']} is currently {risk['risk_level']} risk with a score of {float(risk['risk_signal_score']):.1f}/100.",
        f"Trailing risk-summary return rate is {float(risk.get('return_rate', latest.get('return_rate', 0)))*100:.1f}%.",
        f"Average rating in the latest monthly record is {float(latest.get('avg_rating', risk.get('avg_rating', 0))):.2f}/5.",
    ]
    top_issues = tickets.get("top_issue_types", tickets.get("issues", {}))
    evidence = [
        f"Support tickets observed in the dataset: {tickets.get('ticket_count', tickets.get('count', 0))}.",
        f"Most common support issue types: {', '.join(top_issues.keys()) or 'none identified'}.",
    ]

    root_candidates = []
    actions = []
    for source in sources:
        text = str(source.get("text", ""))
        source_id = str(source.get("document_id", "unknown"))
        cause = re.search(r"Potential root cause:\s*(.*?)(?:\. Recommended operational actions:|\. Warranty guidance:|$)", text, flags=re.IGNORECASE)
        if not cause:
            cause = re.search(r"identified\s+(.*?)\s+as a likely cause", text, flags=re.IGNORECASE)
        if cause:
            candidate = cause.group(1).strip().rstrip(".")
            if candidate and candidate not in root_candidates:
                root_candidates.append(f"Investigate {candidate} (source {source_id}); this is a candidate, not a confirmed cause.")
        action = re.search(r"Recommended operational actions:\s*(.*?)(?:\. Warranty guidance:|\. Escalation:|$)", text, flags=re.IGNORECASE)
        if not action:
            action = re.search(r"Recommended actions:\s*(.*?)(?:\. This historical record|$)", text, flags=re.IGNORECASE)
        if action:
            candidate_action = action.group(1).strip().rstrip(".")
            if candidate_action and candidate_action not in actions:
                actions.append(candidate_action)

    if not root_candidates:
        root_candidates = ["Review support signals and product documentation before assigning a root cause."]
    if not actions:
        actions = [
            "Investigate the highest-volume issue type.",
            "Validate the product documentation and warranty guidance.",
            "Monitor the risk trend after corrective action.",
        ]

    return {
        "findings": findings,
        "evidence": evidence,
        "root_cause_candidates": root_candidates[:3],
        "recommended_actions": actions[:3],
        "sources": [{"source_id": s["document_id"], "title": s["title"]} for s in sources],
        "disclaimer": "Decision-support output. Retrieved historical guidance is supporting evidence, not proof of current causality.",
    }
