"""Evidence aggregation and structured response generation for Product Pulse."""
from __future__ import annotations
import logging
from typing import Any
from pydantic import ValidationError
from .response_schema import InvestigationResponse
from .synthesis import build_synthesis_prompt, fallback_response

logger = logging.getLogger("product_pulse.investigation")


class InvestigationEngine:
    def __init__(self, tools: Any, rag_service: Any, llm_provider: Any = None):
        self.tools = tools
        self.rag_service = rag_service
        self.llm = llm_provider

    def run(self, product_id: str, question: str) -> dict[str, Any]:
        risk = self.tools.get_product_risk(product_id)
        trends = self.tools.get_product_trend(product_id)
        tickets = self.tools.get_ticket_summary(product_id)
        rag = self.rag_service.answer(question=question, product_id=product_id, top_k=5)
        sources = rag.get("sources", [])
        business_evidence = {"risk": risk, "recent_trend": trends[-6:], "support": tickets}
        generation_mode = "deterministic_fallback"

        if self.llm is not None:
            try:
                prompt = build_synthesis_prompt(question, product_id, business_evidence, sources)
                data = self.llm.generate_json(prompt)
                response = InvestigationResponse.model_validate(data)
                generation_mode = "llm"
            except (RuntimeError, ValueError, ValidationError, TypeError) as exc:
                # Provider quota/network/output issues should not make the demo unusable.
                logger.warning("llm_generation_failed product_id=%s error_type=%s; using fallback", product_id, type(exc).__name__)
                response = InvestigationResponse.model_validate(
                    fallback_response(product_id, risk, trends, tickets, sources)
                )
        else:
            response = InvestigationResponse.model_validate(
                fallback_response(product_id, risk, trends, tickets, sources)
            )

        # Do not return source references that were not actually retrieved.
        allowed = {str(s.get("document_id")): str(s.get("title", "")) for s in sources}
        response_payload = response.model_dump()
        valid_citations = [s for s in response_payload.get("sources", []) if s.get("source_id") in allowed]
        if not valid_citations and sources:
            valid_citations = [{"source_id": s["document_id"], "title": s["title"]} for s in sources]
        response_payload["sources"] = valid_citations

        return {
            "product_id": product_id,
            "question": question,
            "generation_mode": generation_mode,
            "retrieval_mode": rag.get("retrieval_mode", "unknown"),
            "response": response_payload,
            "raw_evidence": business_evidence,
            "retrieved_sources": sources,
        }
