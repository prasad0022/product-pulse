"""Product Pulse FastAPI application."""
from __future__ import annotations
import logging
import os
import sys
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analytics import product_tools
from src.logging_config import configure_logging
from src.rag.service import ProductPulseRAG
from src.rag.investigation import InvestigationEngine
from src.rag.llm_provider import GeminiProvider

configure_logging()
logger = logging.getLogger("product_pulse.api")

class QueryRequest(BaseModel):
    product_id: str = Field(..., min_length=2, max_length=32)
    question: str = Field(..., min_length=5, max_length=1000)

app = FastAPI(
    title="Product Pulse API",
    version="0.4.0",
    description="Product Risk Detection and AI-assisted product investigation API.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:4173,http://localhost:5173").split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def make_llm_provider():
    provider = os.getenv("PRODUCT_PULSE_LLM", "none").lower()
    if provider == "gemini":
        return GeminiProvider()
    return None


@lru_cache(maxsize=1)
def get_rag_service():
    return ProductPulseRAG()


def make_tools():
    class Tools:
        get_product_risk = staticmethod(product_tools.get_product_risk)
        get_product_trend = staticmethod(product_tools.get_product_trend)
        get_ticket_summary = staticmethod(product_tools.get_ticket_summary)
    return Tools()


@app.get("/health")
def health():
    logger.info("health_check")
    return {"status": "ok", "service": "product-pulse-api", "version": app.version,
            "llm_provider": os.getenv("PRODUCT_PULSE_LLM", "none"),
            "data_type": "synthetic demo data"}


@app.get("/products")
def products(limit: int = Query(default=40, ge=1, le=100)):
    return product_tools.get_products(limit=limit)


@app.get("/portfolio/summary")
def portfolio_summary():
    return product_tools.get_portfolio_summary()


@app.get("/products/{product_id}/risk")
def product_risk(product_id: str):
    try:
        return product_tools.get_product_risk(product_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/products/{product_id}/trend")
def product_trend(product_id: str):
    try:
        return product_tools.get_product_trend(product_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/products/{product_id}/tickets")
def product_tickets(product_id: str):
    try:
        return product_tools.get_ticket_summary(product_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/investigate")
def investigate(request: QueryRequest):
    logger.info("investigation_request product_id=%s", request.product_id)
    try:
        engine = InvestigationEngine(tools=make_tools(), rag_service=get_rag_service(), llm_provider=make_llm_provider())
        return engine.run(request.product_id, request.question)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("investigation_runtime_error product_id=%s", request.product_id)
        raise HTTPException(status_code=503, detail="Investigation service unavailable. Check logs and configuration.") from exc
