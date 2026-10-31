# Product Pulse — Local Setup

This guide describes how to run Product Pulse locally with Docker Compose or separate Python and Node.js processes.

## Prerequisites

- Git
- Docker Desktop with Docker Compose support for the containerized option
- Python 3.11 and Node.js 20 for local development

## Option A — Docker Compose (recommended for the demo)

From the repository root:

```cmd
docker compose up --build -d
```

Check the services:

```cmd
docker compose ps
```

Open:

- Frontend: http://localhost:4173
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health

View API logs:

```cmd
docker compose logs -f api
```

View frontend logs:

```cmd
docker compose logs -f frontend
```

Stop the containers:

```cmd
docker compose down
```

Rebuild after application code or dependency changes:

```cmd
docker compose up --build -d
```

When only environment variables change, recreate the API service so the new values are applied:

```cmd
docker compose up -d --force-recreate api
```

## Optional Gemini configuration

The application can run without Gemini. The default provider setting is `PRODUCT_PULSE_LLM=none`, which uses deterministic synthesis.

To enable Gemini, create a `.env` file in the repository root based on `.env.example` and configure:

```dotenv
PRODUCT_PULSE_LLM=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

Do not commit `.env` or share the API key. Keep the key in your local environment only. Gemini availability and quotas depend on the provider account and model access.

## Option B — Local Python and Node.js

### 1. Create and activate a Python environment

Windows CMD:

```cmd
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
```

PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 2. Install backend dependencies and prepare data

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/generate_data.py
python scripts/validate_data.py
python scripts/train_model.py
python scripts/evaluate_rag.py
pytest -q
```

### 3. Start the API

```bash
uvicorn api.main:app --reload --port 8000
```

Open <http://localhost:8000/docs> for the API documentation.

### 4. Install and start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

## Smoke-test the application

1. Call `GET http://localhost:8000/health` and confirm the API returns `status: ok`.
2. Open the frontend and confirm the product portfolio loads.
3. Call `GET /products?limit=40` and confirm product records are returned.
4. Call a product risk endpoint, for example `GET /products/P1029/risk`.
5. Call `POST /investigate` with a known product ID and an investigation question.
6. Confirm the response reports its generation and retrieval modes and includes retrieved source metadata.
7. When Gemini is configured, confirm the live request reports `generation_mode: llm`; when it is not configured, confirm the deterministic fallback path is available.

## Troubleshooting notes

- If `python` is not found on Windows, try the Python launcher `py` or `py -m json.tool` when formatting a `curl` response.
- If a container is already running with old environment values, recreate the service using `docker compose up -d --force-recreate api`.
- If source code or dependencies changed, rebuild with `docker compose up --build -d`.
- If Gemini generation fails, check the `PRODUCT_PULSE_LLM`, `GEMINI_API_KEY`, `GEMINI_MODEL` configuration and inspect `docker compose logs -f api`. The deterministic fallback is designed to keep the core investigation workflow available.
- All project data is synthetic. Do not interpret sample risk scores or model predictions as real-world operational conclusions.
