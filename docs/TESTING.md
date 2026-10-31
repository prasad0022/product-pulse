# Product Pulse — Testing and Verification

## 1. Purpose

This document summarizes the available checks for data integrity, the Python backend, API contracts, ML pipeline, retrieval, frontend, and local Docker deployment. Test outcomes are tied to the recorded local runs; they should not be interpreted as a formal production certification.

## 2. Automated test suite

Run from the repository root:

```bash
pytest -q
```

The latest local test run reported by the project author on October 31, 2026 completed with:

**17 passed, 1 warning.**

The warning was a dependency deprecation warning and did not fail the suite.

The repository test modules cover:

- API health and product-risk response contracts.
- Product analytics and workflow behavior.
- Data table presence and key referential constraints.
- Investigation response schema and source handling.
- API end-to-end request behavior using test doubles/stubs for external dependencies.
- Unknown-product behavior.

Some tests intentionally stub RAG or provider integrations. The test suite therefore does not, by itself, prove the behavior of every live external service. Live integration was smoke-tested separately as recorded below.

## 3. Data validation and reproducibility

Recorded validation result:

- **24/24 data validation checks passed.**
- The checks cover identifiers, foreign-key relationships, monthly metric uniqueness, label/document references, and valid rate/rating ranges.
- The recorded core tables contain no missing cells or duplicate rows in the validation report.
- The synthetic data generator uses fixed seed `42`; a prior reproducibility check found identical hashes for selected generated tables across consecutive runs.

Run:

```bash
python scripts/generate_data.py
python scripts/validate_data.py
```

Review `docs/DATA_VALIDATION_REPORT.md` and `docs/DATA_GENERATION_METADATA.json` for the recorded details.

## 4. Machine-learning verification

Run:

```bash
python scripts/train_model.py
```

The training script compares Logistic Regression and Random Forest using chronological train/validation/test periods, writes `models/risk_model.joblib`, and produces the ML model report and prediction file.

The recorded model report is in `docs/ML_MODEL_REPORT.md` and `docs/ML_MODEL_REPORT.json`. Model scores are from synthetic data only and must not be represented as expected production accuracy.

A local product-risk API request on October 31, 2026 returned `ml_prediction_source: live_model_inference`, confirming that the deployed API path used the model for that request.

## 5. RAG and Gemini smoke verification

The RAG evaluation script:

```bash
python scripts/evaluate_rag.py
```

Recorded result: 8/8 (100%) keyword retrieval hit@5 on the small curated evaluation set. This is a keyword-retrieval smoke benchmark, not a formal semantic retrieval or answer-faithfulness evaluation.

A live `/investigate` request on October 31, 2026 was also exercised with Gemini configured. The observed response reported:

- `generation_mode: llm`
- `retrieval_mode: semantic_faiss`
- Gemini generation success in the service logs
- HTTP 200 from the API
- Product-specific retrieved source content and structured investigation output

This confirms that the local Gemini + semantic retrieval integration path was exercised successfully. It does not constitute a broad evaluation of generated-answer quality.

## 6. API and Docker verification

The project author reported that the Docker Compose application was built and run locally, with the API and frontend available for manual verification. API smoke checks include:

- `GET /health`
- `GET /products?limit=40`
- `GET /portfolio/summary`
- Product risk, trend, and ticket endpoints
- `POST /investigate`

The live investigation and product-risk requests noted above returned HTTP 200.

Useful local commands:

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f api
docker compose logs -f frontend
docker compose down
```

The services are expected at `http://localhost:8000` (API) and `http://localhost:4173` (frontend). The Swagger UI is available at `http://localhost:8000/docs`.

## 7. Frontend verification

The React dashboard was run locally through the Docker Compose setup and manually checked by the project author. The codebase also contains a GitHub Actions workflow that installs frontend dependencies and runs `npm run build` using Node.js 20.

A separate end-to-end browser automation suite is not included in the current test scope. Do not claim automated UI testing unless a corresponding CI run or browser test report is available.

## 8. Continuous integration

The GitHub Actions workflow `.github/workflows/ci.yml` defines two jobs:

1. **Python tests:** install test dependencies, generate data, validate data, train the model, run pytest, and evaluate retrieval.
2. **Frontend build:** install Node.js dependencies and run the Vite production build.

Check the GitHub Actions run associated with the release commit before publishing the v1.0.0 release. Documentation in this file describes the configured workflow; it does not claim that a particular remote CI run has passed unless the GitHub run confirms it.

## 9. Known testing limitations

- All data is synthetic; external validation against real commerce data is not available.
- The ML validation split is one month and the test split is two months in the generated history.
- The RAG evaluation query set is small and evaluates keyword retrieval only.
- Live Gemini integration was smoke-tested, not evaluated against a large human-rated question set.
- No full browser automation or load/performance test is included in the current verification record.
- A successful local Docker run does not imply a cloud-hosted production deployment or security audit.

## 10. Release verification checklist

Before creating the GitHub release, verify the following on the intended release branch:

- [ ] `VERSION` contains `1.0.0`.
- [ ] FastAPI metadata in `api/main.py` reports `1.0.0`.
- [ ] `.env`, API keys, and local secrets are not staged or committed.
- [ ] `python scripts/validate_data.py` passes.
- [ ] `python scripts/train_model.py` completes and the model artifact is present.
- [ ] `pytest -q` passes.
- [ ] `python scripts/evaluate_rag.py` completes.
- [ ] `docker compose up --build -d` starts both services successfully.
- [ ] `/health`, product-risk, and `/investigate` smoke checks succeed.
- [ ] Gemini mode is tested if it is enabled for the demo; the default fallback path is also checked.
- [ ] GitHub Actions passes on the release commit.
- [ ] Git tag `v1.0.0` is pushed and the GitHub Release is created from that tag.
