# Docker Readiness

Docker Compose defines an API and frontend service. The API healthcheck is configured and CORS allows the default local frontend origins.

The image installs the full Python dependency set. Semantic retrieval loads the Sentence Transformers model when possible; if semantic dependencies or model loading fail, the service falls back to local keyword retrieval.

**Verification status:** Docker was not available in the authoring workspace, so the Compose build/run has not been executed here. Verify with `docker compose up --build` on the target machine. This documentation does not claim a Docker E2E pass.
