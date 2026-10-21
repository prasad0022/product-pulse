# Product Pulse — Verification Report

Date: 2026-10-21

## Passed checks

- Python syntax compilation for generator, model script, validation script, evaluation script, API and core RAG modules: PASS
- Data generator rerun with seed `42`: selected core CSV files produced identical SHA-256 hashes across two runs
- Data validation: **24/24 checks passed**
- Automated Python tests: **15 passed**
- FastAPI smoke checks: `/health`, `/products?limit=40`, `/portfolio/summary`, product risk, product trend, and `/investigate`: PASS
- CORS response for `http://localhost:5173`: PASS
- Investigation payload contains findings, evidence, root-cause candidates, recommendations, sources, and disclaimer: PASS
- Local keyword RAG fallback returned source documents for the sample Product P1029 investigation: PASS
- Frontend JSX syntax parse/transpile: PASS
- RAG keyword hit@5: **8/8 queries (100%)** on the intentionally small curated evaluation set

## ML baseline

See `ML_MODEL_REPORT.md`. The model was trained on the generated dataset with a chronological split. Model scores are only synthetic-data validation results and must not be presented as expected real-world performance.

## Not verified in this workspace

- `npm install` / `npm run build`: the install attempt timed out in this environment, so a complete Vite production build remains unverified.
- Docker Compose build/run: Docker is not installed in this environment. Run `docker compose up --build` on the local machine to validate container behavior.
- Gemini API live call: requires a locally configured API key and is intentionally not required for the default workflow.

## Overall status

**Ready for local integration testing, but not fully verified across Docker and the production frontend build.** Follow `LOCAL_SETUP.md` and report any local error output verbatim so it can be debugged.
