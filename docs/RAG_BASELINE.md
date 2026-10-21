# Product Pulse — RAG Baseline

{
  "documents": 48,
  "chunks": 48,
  "chunking": {
    "method": "fixed_word_window",
    "chunk_size_words": 120,
    "overlap_words": 20
  },
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "vector_index": "FAISS IndexFlatIP with normalized embeddings (cosine-equivalent)",
  "evaluation_queries": 8,
  "notes": [
    "This is the first local RAG baseline.",
    "Product metadata is retained for filtering and citations.",
    "Reranking and advanced hybrid retrieval are intentionally deferred."
  ]
}
