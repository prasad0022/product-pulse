"""Download/cache the local embedding model used by Product Pulse RAG."""
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

if __name__ == "__main__":
    SentenceTransformer(MODEL_NAME)
    print(f"Cached embedding model: {MODEL_NAME}")
