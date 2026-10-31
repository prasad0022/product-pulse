
"""Evidence aggregation and structured response generation for Product Pulse."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from .response_schema import InvestigationResponse
from .synthesis import build_synthesis_prompt, fallback_response

logger = logging.getLogger("product_pulse.investigation")


class InvestigationEngine:
    """Combines structured business evidence, RAG and optional LLM synthesis."""

    def __init__(
        self,
        tools: Any,
        rag_service: Any,
        llm_provider: Any = None,
    ):
        self.tools = tools
        self.rag_service = rag_service
        self.llm = llm_provider

    @staticmethod
    def _normalize_llm_response(
        data: Any,
        retrieved_sources: list[dict],
        fallback: dict,
    ) -> dict:
        """
        Normalize Gemini output before Pydantic validation.

        Source references are always constructed from documents actually
        retrieved by the RAG service, not from model-generated citations.
        """

        if not isinstance(data, dict):
            raise ValueError(
                "Gemini response must be a JSON object."
            )

        normalized = {}

        # These fields must be lists of strings.
        list_fields = [
            "findings",
            "evidence",
            "root_cause_candidates",
            "recommended_actions",
        ]

        for field in list_fields:
            value = data.get(field, fallback.get(field, []))

            if value is None:
                value = []

            elif isinstance(value, str):
                value = [value]

            elif isinstance(value, (list, tuple)):
                value = [
                    str(item).strip()
                    for item in value
                    if item is not None and str(item).strip()
                ]

            else:
                value = [str(value)]

            normalized[field] = value

        # Never trust source IDs invented by the LLM.
        # Use the exact documents returned by the retriever.
        normalized["sources"] = [
            {
                "source_id": str(source["document_id"]),
                "title": str(source["title"]),
            }
            for source in retrieved_sources
            if source.get("document_id") and source.get("title")
        ]

        disclaimer = data.get(
            "disclaimer",
            fallback.get("disclaimer"),
        )

        if not isinstance(disclaimer, str) or not disclaimer.strip():
            disclaimer = fallback.get(
                "disclaimer",
                "Decision-support output. Root-cause candidates require validation.",
            )

        normalized["disclaimer"] = disclaimer.strip()

        return normalized

    def _build_fallback(
        self,
        product_id: str,
        risk: dict,
        trends: list[dict],
        tickets: dict,
        sources: list[dict],
    ) -> dict:
        """Build and validate the deterministic fallback response."""

        fallback = fallback_response(
            product_id,
            risk,
            trends,
            tickets,
            sources,
        )

        return InvestigationResponse.model_validate(
            fallback
        ).model_dump()

    def run(
        self,
        product_id: str,
        question: str,
    ) -> dict[str, Any]:

        # ---------------------------------------------------------
        # 1. Gather structured business evidence
        # ---------------------------------------------------------

        risk = self.tools.get_product_risk(product_id)

        trends = self.tools.get_product_trend(product_id)

        tickets = self.tools.get_ticket_summary(product_id)

        # ---------------------------------------------------------
        # 2. Retrieve relevant documents using RAG
        # ---------------------------------------------------------

        rag = self.rag_service.answer(
            question=question,
            product_id=product_id,
            top_k=5,
        )

        sources = rag.get("sources", [])

        if not isinstance(sources, list):
            sources = []

        retrieval_mode = rag.get(
            "retrieval_mode",
            "unknown",
        )

        # ---------------------------------------------------------
        # 3. Combine evidence
        # ---------------------------------------------------------

        business_evidence = {
            "risk": risk,
            "recent_trend": trends[-6:],
            "support": tickets,
        }

        generation_mode = "deterministic_fallback"

        # ---------------------------------------------------------
        # 4. Generate response using Gemini when configured
        # ---------------------------------------------------------

        if self.llm is not None:

            try:
                prompt = build_synthesis_prompt(
                    question=question,
                    product_id=product_id,
                    business_evidence=business_evidence,
                    rag_sources=sources,
                )

                # Call Gemini.
                llm_data = self.llm.generate_json(prompt)

                # Build fallback data as a safety net for missing fields.
                fallback_data = fallback_response(
                    product_id,
                    risk,
                    trends,
                    tickets,
                    sources,
                )

                # Normalize Gemini output.
                normalized_data = self._normalize_llm_response(
                    data=llm_data,
                    retrieved_sources=sources,
                    fallback=fallback_data,
                )

                # Validate the final response.
                validated_response = InvestigationResponse.model_validate(
                    normalized_data
                )

                response_payload = validated_response.model_dump()

                generation_mode = "llm"

                logger.info(
                    "llm_generation_success product_id=%s model=%s",
                    product_id,
                    getattr(self.llm, "model", "configured_provider"),
                )

            except Exception as exc:

                # Log detailed validation errors without exposing secrets.
                if isinstance(exc, ValidationError):
                    error_details = exc.errors(
                        include_input=False
                    )
                else:
                    error_details = str(exc)

                logger.exception(
                    "llm_generation_failed "
                    "product_id=%s "
                    "error_type=%s "
                    "details=%s; using deterministic fallback",
                    product_id,
                    type(exc).__name__,
                    error_details,
                )

                response_payload = self._build_fallback(
                    product_id=product_id,
                    risk=risk,
                    trends=trends,
                    tickets=tickets,
                    sources=sources,
                )

        else:

            # -----------------------------------------------------
            # 5. Deterministic fallback when Gemini is disabled
            # -----------------------------------------------------

            response_payload = self._build_fallback(
                product_id=product_id,
                risk=risk,
                trends=trends,
                tickets=tickets,
                sources=sources,
            )

        # ---------------------------------------------------------
        # 6. Return the investigation result
        # ---------------------------------------------------------

        return {
            "product_id": product_id,
            "question": question,
            "generation_mode": generation_mode,
            "retrieval_mode": retrieval_mode,
            "response": response_payload,
            "raw_evidence": business_evidence,
            "retrieved_sources": sources,
        }
