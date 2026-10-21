"""Tool contracts for Product Pulse agent."""
from typing import Any, Callable

class ProductPulseTools:
    def __init__(
        self,
        risk_tool: Callable[[str], dict],
        trend_tool: Callable[[str], list[dict]],
        ticket_tool: Callable[[str], dict],
        rag_tool: Callable[[str, str | None, int], dict],
    ):
        self.risk_tool = risk_tool
        self.trend_tool = trend_tool
        self.ticket_tool = ticket_tool
        self.rag_tool = rag_tool

    def get_product_risk(self, product_id: str) -> dict:
        return self.risk_tool(product_id)

    def get_product_trend(self, product_id: str) -> list[dict]:
        return self.trend_tool(product_id)

    def get_ticket_summary(self, product_id: str) -> dict:
        return self.ticket_tool(product_id)

    def search_product_knowledge(self, question: str, product_id: str | None = None, top_k: int = 5) -> dict:
        return self.rag_tool(question, product_id, top_k)
