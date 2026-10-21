"""RAG service with semantic retrieval and a dependency-light lexical fallback."""
from __future__ import annotations
import logging
import re
from pathlib import Path
from typing import Any
import pandas as pd
from .retriever import LocalRAGRetriever

logger = logging.getLogger("product_pulse.rag")
ROOT = Path(__file__).resolve().parents[2]
CHUNKS = ROOT / "data" / "rag" / "document_chunks.csv"


class KeywordRAGRetriever:
    """Small deterministic fallback used when semantic dependencies/model are unavailable."""
    def __init__(self, chunks_csv: str | Path):
        self.chunks = pd.read_csv(chunks_csv)

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", str(value).lower()))

    def retrieve(self, query: str, top_k: int = 5, product_id: str | None = None) -> list[dict]:
        rows = self.chunks.copy()
        if product_id:
            rows = rows[rows["product_id"] == product_id]
        if rows.empty:
            raise ValueError(f"No RAG documents found for product_id={product_id}")
        q = self._tokens(query)
        scored = []
        for _, row in rows.iterrows():
            tokens = self._tokens(row["text"])
            score = len(q & tokens) / max(len(q), 1)
            scored.append((score, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [{
            "chunk_id": row["chunk_id"], "document_id": row["document_id"],
            "product_id": row["product_id"], "title": row["title"],
            "document_type": row["document_type"], "text": row["text"],
            "score": float(score), "retrieval_mode": "keyword_fallback",
        } for score, row in scored[:max(1, top_k)]]


class ProductPulseRAG:
    def __init__(self, llm_provider: Any = None):
        if not CHUNKS.exists():
            raise RuntimeError("RAG chunks are missing. Run scripts/generate_data.py first.")
        try:
            self.retriever = LocalRAGRetriever(CHUNKS)
            self.retrieval_mode = "semantic_faiss"
        except Exception as exc:
            logger.warning("Semantic RAG unavailable; using keyword fallback: %s", exc)
            self.retriever = KeywordRAGRetriever(CHUNKS)
            self.retrieval_mode = "keyword_fallback"
        self.llm_provider = llm_provider

    def retrieve_evidence(self, question: str, product_id: str, top_k: int = 5) -> list[dict]:
        return self.retriever.retrieve(question, top_k=top_k, product_id=product_id)

    def answer(self, question: str, product_id: str, top_k: int = 5) -> dict:
        sources = self.retrieve_evidence(question, product_id, top_k)
        return {"question": question, "sources": sources, "retrieval_mode": self.retrieval_mode}
