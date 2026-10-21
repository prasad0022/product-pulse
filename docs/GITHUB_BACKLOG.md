# Product Pulse — GitHub Backlog

The following items should be created as GitHub Issues and grouped into milestones.

## M1 — Foundation
- [ ] Create GitHub repository and initial project structure
- [ ] Add README and project definition
- [ ] Add synthetic data generation pipeline
- [ ] Validate data quality and referential integrity
- [ ] Create EDA notebook and baseline business KPIs

## M2 — ML Risk Engine
- [ ] Finalize ML target and leakage-safe time split
- [ ] Build baseline risk model
- [ ] Evaluate precision/recall/F1/ROC-AUC
- [ ] Create product risk scoring output
- [ ] Document model limitations and assumptions

## M3 — RAG Knowledge Layer
- [ ] Finalize knowledge document schema
- [ ] Implement chunking
- [ ] Implement embeddings and FAISS retrieval
- [ ] Create RAG evaluation queries
- [ ] Add citation-ready evidence format

## M4 — Agent + API
- [ ] Define investigation tool contracts
- [ ] Integrate SQL/risk/trend tools
- [ ] Integrate RAG tool
- [ ] Integrate LLM provider abstraction
- [ ] Expose investigation through FastAPI

## M5 — Product Pulse UI
- [ ] Build overview dashboard
- [ ] Connect frontend to API
- [ ] Build AI investigation experience
- [ ] Add product trend visualizations

## M6 — Production Readiness
- [ ] Add tests and CI
- [ ] Add logging and configuration
- [ ] Finalize Docker Compose
- [ ] Improve README and architecture docs
- [ ] End-to-end test and demo preparation
