"""Product Pulse agent workflow."""

from typing import Any


class ProductPulseWorkflow:
    def __init__(self, tools: Any, rag_service: Any | None = None, synthesizer=None):
        self.tools = tools
        self.rag_service = rag_service
        self.synthesizer = synthesizer

    def run(self, product_id: str, question: str) -> dict:
        risk = self.tools.get_product_risk(product_id)
        trend = self.tools.get_product_trend(product_id)
        tickets = self.tools.get_ticket_summary(product_id)

        rag = None
        if self.rag_service is not None:
            rag = self.rag_service.answer(
                question=question,
                product_id=product_id,
                top_k=5,
            )

        evidence = {
            "risk": risk,
            "trend": trend[-6:],
            "tickets": tickets,
            "rag": rag,
        }

        if self.synthesizer:
            answer = self.synthesizer(question, evidence)
        elif rag and rag.get("answer"):
            answer = rag["answer"]
        else:
            answer = self._fallback_summary(evidence)

        return {
            "product_id": product_id,
            "question": question,
            "evidence": evidence,
            "answer": answer,
        }

    @staticmethod
    def _fallback_summary(evidence: dict) -> dict:
        risk = evidence["risk"]
        latest = evidence["trend"][-1] if evidence["trend"] else {}
        return {
            "summary": (
                f"{risk['product_name']} is currently {risk['risk_level']} risk "
                f"with a risk score of {float(risk['risk_signal_score']):.1f}."
            ),
            "signals": {
                "return_rate": latest.get("return_rate"),
                "avg_rating": latest.get("avg_rating"),
                "negative_review_rate": latest.get("negative_review_rate"),
                "support_ticket_count": latest.get("support_ticket_count"),
            },
            "note": "Decision-support output; root-cause candidates require evidence review."
        }
