# Product Pulse — UI MVP

## Screens
1. Overview dashboard: portfolio KPIs, risk distribution, return trend, prioritized products.
2. AI Investigation: selected product risk score, question box, evidence, likely cause, recommended actions, trend.

## Production direction
- Current frontend is a Vite/React MVP using deterministic demo data.
- The next integration is to replace the in-browser data with the FastAPI endpoints.
- AI Investigation will call `POST /investigate`.
- Chart data will call product risk/trend endpoints.
