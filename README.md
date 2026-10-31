# Product Pulse

**Project:** Product Risk Detection Platform  
**Release:** v1.0.0  
**Application:** Product Pulse

Product Pulse is an AI-assisted product-risk detection and investigation platform built as a DSAI capstone project. It combines product-level commerce analytics, a machine-learning model that estimates next-month high-risk probability, product-scoped knowledge retrieval, and an optional Gemini-based investigation response. A React dashboard presents portfolio and product insights through a FastAPI backend.

> **Data and evaluation notice:** All project data is synthetic demonstration data. Model metrics and investigation examples demonstrate the implementation on the generated dataset; they are not evidence of expected performance on real customer or commerce data.

## Key capabilities

- Generate reproducible synthetic commerce data and validate data relationships and ranges.
- Explore portfolio KPIs and product-level monthly trends.
- Calculate and rank product risk using return, rating, review, and support signals.
- Train and serve a next-month high-risk classification model.
- Retrieve product-specific knowledge using Sentence Transformers embeddings and FAISS, with a keyword-based fallback.
- Generate structured investigation responses with an optional Gemini provider; use deterministic fallback responses when Gemini is disabled or unavailable.
- Display portfolio and product insights through a React dashboard.
- Run the API and frontend with Docker Compose or as separate local development processes.

## Technology stack

| Area | Technologies |
|---|---|
| Frontend | React 18, Vite 6, Recharts |
| Backend/API | Python 3.11, FastAPI, Pydantic, Uvicorn |
| Data processing | Pandas, NumPy |
| Machine learning | scikit-learn, joblib |
| Semantic retrieval | Sentence Transformers (`all-MiniLM-L6-v2`), FAISS CPU |
| LLM integration | Google Gen AI SDK, Gemini (optional) |
| Packaging and runtime | Docker, Docker Compose |
| Quality and automation | pytest, GitHub Actions |

## Architecture at a glance

1. Synthetic source tables are generated under `data/processed/`; knowledge chunks and evaluation queries are generated under `data/rag/`.
2. Data validation and EDA help inspect completeness, relationships, distributions, and business KPIs.
3. The ML training script engineers monthly features, evaluates Logistic Regression and Random Forest with chronological splits, and saves the selected pipeline as `models/risk_model.joblib`.
4. FastAPI exposes portfolio, product, trend, ticket, health, and investigation endpoints.
5. The investigation flow combines product analytics, live ML risk inference, product-scoped retrieval, and either Gemini synthesis or deterministic fallback synthesis.
6. The React dashboard consumes the API. Docker Compose runs the API and frontend as separate services.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the component and request flows.

## Quick start with Docker Compose

**Prerequisites:** Git and Docker Desktop with Docker Compose support.

From the repository root:

```bash
docker compose up --build -d
```

Open the application:

- Frontend: <http://localhost:4173>
- API: <http://localhost:8000>
- Interactive API documentation: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

Stop the services:

```bash
docker compose down
```

Rebuild after code or dependency changes:

```bash
docker compose up --build -d
```

The default configuration does not require a Gemini API key. To enable Gemini, create a local `.env` file using `.env.example` as a guide and set:

```dotenv
PRODUCT_PULSE_LLM=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

Never commit `.env` or API keys. Keep `PRODUCT_PULSE_LLM=none` to use the deterministic response path without an external LLM.

## Local development

For a non-Docker setup, see [`LOCAL_SETUP.md`](LOCAL_SETUP.md). Typical backend setup:

```bash
python -m venv .venv
# Windows CMD: .venv\Scripts\activate.bat
# PowerShell:  .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/generate_data.py
python scripts/validate_data.py
python scripts/train_model.py
python scripts/evaluate_rag.py
pytest -q
uvicorn api.main:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server normally runs at <http://localhost:5173>. The Docker frontend is served at <http://localhost:4173>.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | API health and runtime configuration summary |
| `GET` | `/products?limit=40` | Product list ordered by risk signal |
| `GET` | `/portfolio/summary` | Portfolio-level KPIs |
| `GET` | `/products/{product_id}/risk` | Product risk summary and model prediction |
| `GET` | `/products/{product_id}/trend` | Monthly product metrics |
| `GET` | `/products/{product_id}/tickets` | Product support-ticket summary |
| `POST` | `/investigate` | Evidence-backed product investigation |

Interactive request and response schemas are available at `/docs`. Detailed examples are in [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md).

## Repository documentation

- [`docs/PROJECT_OVERVIEW.md`](docs/PROJECT_OVERVIEW.md) — problem, objectives, scope, and outcomes
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — components and data/request flows
- [`docs/DATA_SCIENCE_ML.md`](docs/DATA_SCIENCE_ML.md) — data generation, EDA, features, training, and metrics
- [`docs/RAG_GENAI.md`](docs/RAG_GENAI.md) — retrieval, Gemini integration, and fallback behavior
- [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) — endpoints and example requests
- [`docs/TESTING.md`](docs/TESTING.md) — verification results, test coverage, and limitations
- [`LOCAL_SETUP.md`](LOCAL_SETUP.md) — detailed local setup

## Limitations

- The generated dataset is synthetic and deliberately includes seeded patterns for repeatable demonstrations.
- Model metrics are specific to the generated data and chronological evaluation window; external validation on real data is not available.
- The curated RAG retrieval benchmark is small. It is not a comprehensive semantic retrieval or LLM faithfulness evaluation.
- Gemini is an optional external dependency and is subject to API availability, quotas, and model access.
- Investigation output is decision support. Root-cause candidates must be checked against real operational evidence before action.

## Release

This repository documents the **Product Pulse v1.0.0** capstone release. See the Git tag `v1.0.0` and the GitHub Releases page for the published release notes once the tag has been pushed and the release has been created.
