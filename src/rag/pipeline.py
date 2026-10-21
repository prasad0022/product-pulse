"""Product Pulse RAG orchestration.

LLM-agnostic: retrieval is separate from generation so the application can use
any free-tier/local provider later.
"""
from typing import Any, Callable, Sequence


class RAGPipeline:
    def __init__(self, retriever: Any, llm: Callable[[str], str] | None = None):
        self.retriever = retriever
        self.llm = llm

    @staticmethod
    def build_context(results: Sequence[dict]) -> str:
        blocks = []
        for r in results:
            blocks.append(
                f"[SOURCE {r['document_id']}] {r['title']}\n"
                f"Product: {r['product_id']}\n"
                f"{r['text']}"
            )
        return "\n\n".join(blocks)

    @staticmethod
    def build_prompt(question: str, context: str) -> str:
        return f"""You are Product Pulse, a product-risk investigation assistant.

Answer the business question using ONLY the evidence in the supplied context.
Do not invent causes, metrics, or actions.
Clearly distinguish evidence from inference.
Cite sources using their SOURCE identifiers.

Question:
{question}

Context:
{context}

Return:
1. Findings
2. Evidence
3. Likely root-cause candidates
4. Recommended next actions
5. Sources
"""

    def retrieve(self, question: str, product_id: str | None = None, top_k: int = 5):
        return self.retriever.retrieve(question, top_k=top_k, product_id=product_id)

    def answer(self, question: str, product_id: str | None = None, top_k: int = 5) -> dict:
        results = self.retrieve(question, product_id=product_id, top_k=top_k)
        context = self.build_context(results)
        prompt = self.build_prompt(question, context)

        if self.llm is None:
            return {
                "question": question,
                "answer": "LLM provider not configured. Retrieved evidence is available.",
                "sources": results,
                "prompt": prompt,
            }

        return {
            "question": question,
            "answer": self.llm(prompt),
            "sources": results,
        }
