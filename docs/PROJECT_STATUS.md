# Product Pulse — Project Status

## Locked decisions
- Official project: Product Risk Detection Platform
- Application: Product Pulse
- Target submission: November 3, 2026
- Data strategy: controlled, reproducible synthetic data
- History: January–December 2025
- Products: 40 across 6 categories
- ML objective: predict next-month high-risk status from current product signals
- AI flow: structured product analytics + ML risk prediction + product-scoped RAG + structured investigation response
- Cost constraint: free/open-source tools and optional free-tier LLM API

## Implemented
- Reproducible synthetic data generator (`scripts/generate_data.py`)
- Data integrity validator (`scripts/validate_data.py`)
- ML training/evaluation script (`scripts/train_model.py`)
- Deterministic RAG evaluation (`scripts/evaluate_rag.py`)
- FastAPI endpoints for portfolio, product risk/trend/tickets, and investigation
- Sentence Transformers + FAISS retrieval with a keyword fallback
- Optional Gemini structured-output provider
- React dashboard connected to the API
- Docker Compose, local setup instructions, test suite, and GitHub Actions CI

## Verification status
- 24/24 data integrity checks pass
- Data regeneration is reproducible with the fixed seed
- 15 Python tests pass
- API smoke test passes, including `/investigate`, structured output, source retrieval, and CORS
- Frontend JSX syntax was checked with the TypeScript parser
- Full npm production build was not verified in this workspace because package installation timed out
- Docker Compose was not executed because Docker is not installed in this workspace; verify it locally

## Data and evaluation caveats
All project data is synthetic. The high model metrics indicate that the intended patterns can be learned from this generated dataset; they are not evidence of expected accuracy on a real commerce dataset. The RAG hit@5 metric is a small, curated keyword-retrieval smoke test, not a semantic-RAG or answer-quality benchmark.
