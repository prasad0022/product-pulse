# Docker dependency-resolution fix (v0.2.1)

## Why this change

The prior Docker build failed while pip resolved broad, unpinned dependency ranges and could not find a compatible `pydantic-core` distribution for its selected environment. The failure happened during dependency installation, before application code or the frontend could build.

## Changes

- Pin the runtime and test dependency versions.
- Pin `pydantic==2.11.7` with its matching `pydantic-core==2.33.2`.
- Use `python:3.11-slim` for the API image to target a widely supported CPython wheel set.
- Avoid upgrading pip during the image build, which had added network/resolver work before dependency installation.
- Align GitHub Actions with Python 3.11.

## Rebuild

From the project root:

```bash
docker compose down
docker compose build --no-cache api
docker compose up --build
```

If the same `No matching distribution found for pydantic-core` error persists, check whether pip is configured to use a restricted package mirror, and whether Docker has access to `https://pypi.org/simple`. The fix has not been verified by a Docker build in this authoring environment.
