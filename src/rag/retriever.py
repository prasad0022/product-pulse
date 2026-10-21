"""Local semantic retriever using Sentence Transformers and FAISS."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List
import pandas as pd


class LocalRAGRetriever:
    """Product-scoped semantic search. Per-product indexes are cached after first use."""
    def __init__(self, chunks_csv: str | Path, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            import faiss  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("Install sentence-transformers and faiss-cpu to use semantic RAG.") from exc
        self.chunks = pd.read_csv(chunks_csv)
        if self.chunks.empty:
            raise ValueError("The RAG chunk file is empty. Run scripts/generate_data.py first.")
        self.model = SentenceTransformer(model_name)
        self._indices: dict[str, tuple[object, pd.DataFrame]] = {}

    def _index_for(self, product_id: str | None):
        import faiss
        key = product_id or "__all__"
        if key in self._indices:
            return self._indices[key]
        rows = self.chunks if product_id is None else self.chunks[self.chunks.product_id == product_id]
        if rows.empty:
            raise ValueError(f"No RAG documents found for product_id={product_id}")
        rows = rows.reset_index(drop=True)
        vectors = self.model.encode(rows.text.tolist(), normalize_embeddings=True, show_progress_bar=False).astype("float32")
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        self._indices[key] = (index, rows)
        return index, rows

    def retrieve(self, query: str, top_k: int = 5, product_id: str | None = None) -> List[Dict]:
        index, rows = self._index_for(product_id)
        query_vector = self.model.encode([query], normalize_embeddings=True, show_progress_bar=False).astype("float32")
        k = min(max(1, int(top_k)), len(rows))
        scores, indices = index.search(query_vector, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            row = rows.iloc[int(idx)]
            results.append({
                "chunk_id": row.chunk_id,
                "document_id": row.document_id,
                "product_id": row.product_id,
                "title": row.title,
                "document_type": row.document_type,
                "text": row.text,
                "score": float(score),
                "retrieval_mode": "semantic_faiss",
            })
        return results
