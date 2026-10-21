# Product Pulse — Local Setup

## Option A: Docker Compose

Prerequisites: Docker Desktop and Git.

From the project root:

```bash
docker compose up --build
```

Open:
- Frontend: http://localhost:4173
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

The Docker build installs the dependencies. Semantic retrieval downloads/loads its embedding model when available; the application falls back to keyword retrieval if it cannot be loaded. Docker itself has not been verified in this authoring environment, so validate this path on your machine.

## Option B: Local Python + Node

### 1. Backend environment

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Regenerate synthetic data and train the risk model

```bash
python scripts/generate_data.py
python scripts/validate_data.py
python scripts/train_model.py
python scripts/evaluate_rag.py
pytest -q
```

All generated data is synthetic and uses a fixed random seed. Run both scripts after changing the generator.

### 3. Start the API

```bash
uvicorn api.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 4. Start the frontend in a second terminal

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

## Optional semantic model cache

The application uses Sentence Transformers + FAISS for semantic retrieval when dependencies and the model are available. To pre-download/cache the embedding model:

```bash
python scripts/download_models.py
```

If the model cannot load, Product Pulse uses the local keyword retrieval fallback. The default path does not require an LLM API key.

## Optional Gemini LLM

The default is `PRODUCT_PULSE_LLM=none`. To enable the optional Gemini provider, configure these environment variables locally (never commit secrets):

```text
PRODUCT_PULSE_LLM=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

Gemini availability and quotas depend on the provider's current plan/model access. The application can run without it.

## End-to-end smoke test

1. Confirm `/health` returns `status: ok`.
2. Open the dashboard and verify all 40 products load.
3. Select product `P1029` or another product marked High risk.
4. Ask: `Why is this product high risk and what should we investigate?`
5. Check that the API returns findings, evidence, root-cause candidates, recommended actions, and source references.
6. Confirm the displayed sources match `data/processed/knowledge_documents.csv`.
