"""RAG evaluation helpers for Product Pulse."""

from typing import Iterable
import pandas as pd


def retrieval_hit_at_k(
    chunks: pd.DataFrame,
    query: str,
    expected_terms: Iterable[str],
    product_id: str,
    k: int = 5,
) -> int:
    """Return 1 when top-k product-scoped chunks contain an expected term."""
    q_terms = set(str(query).lower().split())
    rows = chunks[chunks["product_id"] == product_id].copy()

    def score(text: str) -> float:
        terms = set(str(text).lower().split())
        return len(q_terms & terms) / max(len(q_terms), 1)

    rows["score"] = rows["text"].apply(score)
    top = rows.sort_values("score", ascending=False).head(k)

    expected = [str(x).lower().strip() for x in expected_terms]
    return int(any(
        any(term in str(text).lower() for term in expected)
        for text in top["text"].tolist()
    ))
