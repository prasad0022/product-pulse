# Product Pulse

**Official project:** Product Risk Detection Platform  
**Application:** Product Pulse

Product Pulse is a portfolio-level product-risk demo that uses synthetic commerce data to rank products by risk, analyze product trends, retrieve product-specific knowledge, and return cited root-cause candidates and recommended next actions.

## MVP capabilities
- ETL and data quality checks over synthetic product/order/return/review/support data
- Pandas/NumPy EDA and business KPI notebook
- Scikit-learn next-month risk model with chronological train/validation/test splits
- Product risk scoring and risk ranking API
- Product-scoped RAG using Sentence Transformers + FAISS when available, with a keyword fallback
- Optional Gemini structured synthesis; default local fallback requires no API key
- React + Recharts dashboard, FastAPI backend, Docker Compose, tests, and GitHub Actions CI

## Data note
All customer, order, return, review, ticket, product knowledge and RCA records are synthetic demonstration data. The model metrics are only an assessment of this synthetic dataset and must not be presented as expected real-world performance.

## Quick start
See [`LOCAL_SETUP.md`](LOCAL_SETUP.md). In short:

```bash
python -m venv .venv
# Activate the environment, then:
pip install -r requirements.txt
python scripts/generate_data.py
python scripts/train_model.py
pytest -q
uvicorn api.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`; API docs are at `http://localhost:8000/docs`.

## Key documentation
- `docs/DATA_GENERATION.md` — synthetic-data provenance
- `docs/ML_MODEL_REPORT.md` — chronological model evaluation
- `docs/RAG_EVALUATION_V0.md` — RAG retrieval evaluation
- `docs/ENGINEERING_WORKFLOW.md` — engineering workflow
