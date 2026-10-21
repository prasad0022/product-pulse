"""Run a lightweight deterministic retrieval evaluation (no LLM/API required)."""
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.rag.service import KeywordRAGRetriever

RAG_DIR = ROOT / "data" / "rag"
DOCS = ROOT / "docs"


def main():
    retriever = KeywordRAGRetriever(RAG_DIR / "document_chunks.csv")
    queries = pd.read_csv(RAG_DIR / "rag_eval_queries.csv")
    results = []
    for row in queries.to_dict(orient="records"):
        hits = retriever.retrieve(row["query"], top_k=5, product_id=row["product_id"])
        expected = [term.strip().lower() for term in str(row["expected_terms"]).split("|") if term.strip()]
        hit = any(any(term in hitrow["text"].lower() for term in expected) for hitrow in hits)
        results.append({"query_id": row["query_id"], "product_id": row["product_id"], "top_k": 5,
                        "retrieval_hit": int(hit), "top_document_ids": "|".join(dict.fromkeys(x["document_id"] for x in hits))})
    result_df = pd.DataFrame(results)
    result_df.to_csv(RAG_DIR / "rag_eval_results.csv", index=False)
    hit_rate = float(result_df["retrieval_hit"].mean()) if len(result_df) else 0.0
    (DOCS / "RAG_EVALUATION_REPORT.md").write_text(
        "# Product Pulse RAG Evaluation\n\n"
        "This is a deterministic keyword-retrieval smoke benchmark over a small, manually curated synthetic query set. "
        "It does not measure semantic retrieval quality, answer faithfulness, or real-world performance.\n\n"
        f"- Queries: {len(result_df)}\n- Retrieval hit@5: {hit_rate:.1%}\n"
        "- Run with: `python scripts/evaluate_rag.py`\n",
        encoding="utf-8",
    )
    print(f"RAG hit@5: {hit_rate:.1%} ({len(result_df)} queries)")


if __name__ == "__main__":
    main()
