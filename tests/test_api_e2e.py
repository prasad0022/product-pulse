from fastapi.testclient import TestClient
import api.main as main


class FakeRAGService:
    def answer(self, question: str, product_id: str, top_k: int = 5):
        return {
            "question": question,
            "retrieval_mode": "test_fake",
            "sources": [{
                "chunk_id": "CH00001",
                "document_id": "D0001",
                "product_id": product_id,
                "title": "Test product guide",
                "document_type": "product_knowledge",
                "text": "Potential root cause: sizing specification issue. Recommended operational actions: validate the size chart. Warranty guidance: inspect evidence.",
                "score": 0.99,
                "retrieval_mode": "test_fake",
            }],
        }


def test_portfolio_endpoints():
    client = TestClient(main.app)
    products_response = client.get("/products?limit=40")
    summary_response = client.get("/portfolio/summary")
    assert products_response.status_code == 200
    assert len(products_response.json()) == 40
    assert summary_response.status_code == 200
    assert summary_response.json()["product_count"] == 40


def test_investigation_end_to_end_with_stubbed_rag(monkeypatch):
    monkeypatch.setattr(main, "get_rag_service", lambda: FakeRAGService())
    monkeypatch.setattr(main, "make_llm_provider", lambda: None)
    client = TestClient(main.app)
    response = client.post("/investigate", json={
        "product_id": "P1029",
        "question": "Why is this product high risk and what should we investigate?",
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["product_id"] == "P1029"
    assert payload["response"]["findings"]
    assert payload["response"]["root_cause_candidates"]
    assert payload["response"]["sources"][0]["source_id"] == "D0001"
    assert payload["retrieved_sources"][0]["retrieval_mode"] == "test_fake"


def test_unknown_product_returns_404():
    client = TestClient(main.app)
    response = client.get("/products/P9999/risk")
    assert response.status_code == 404
