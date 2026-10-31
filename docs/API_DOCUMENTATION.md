# Product Pulse — API Documentation

## 1. Overview

The Product Pulse backend is a FastAPI application. It returns JSON and provides interactive request/response documentation through Swagger UI.

- Local API base URL: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

## 2. Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health status, service name, application version, LLM provider setting, and data type |
| `GET` | `/products` | Product list ordered by risk signal; accepts `limit` (default 40, range 1–100) |
| `GET` | `/portfolio/summary` | Portfolio-level KPIs |
| `GET` | `/products/{product_id}/risk` | Risk summary and next-month model prediction fields for a product |
| `GET` | `/products/{product_id}/trend` | Monthly activity, quality, and support metrics for a product |
| `GET` | `/products/{product_id}/tickets` | All-period support ticket count, issue categories, and average resolution time for a product |
| `POST` | `/investigate` | Evidence retrieval and structured product investigation |

## 3. Endpoint examples

### 3.1 Health check

```http
GET /health
```

Example response shape:

```json
{
  "status": "ok",
  "service": "product-pulse-api",
  "version": "1.0.0",
  "llm_provider": "none",
  "data_type": "synthetic demo data"
}
```

The `version` value should be aligned with the release version in `api/main.py` before publishing v1.0.0.

### 3.2 List products

```http
GET /products?limit=40
```

Returns up to 100 product risk summaries, ordered by `risk_signal_score` descending. The response includes product identifiers, names, categories, brands, risk metrics, and prediction probability when available.

### 3.3 Portfolio summary

```http
GET /portfolio/summary
```

Returns portfolio measures including product and risk-level counts, order count, units sold, overall return rate, average rating, review count, support-ticket count, gross revenue, data period, and data type.

### 3.4 Product risk

```http
GET /products/P1029/risk
```

Representative fields include:

- `product_id`, `product_name`, `category`, and `brand`
- `return_rate`, `avg_rating`, `negative_review_rate`, and `support_ticket_count`
- `risk_signal_score` and `risk_level`
- `predicted_next_month_high_risk_probability`
- `predicted_next_month_high_risk`
- `ml_prediction_month`, `ml_prediction_target_month`, `ml_model_name`, and `ml_prediction_source`

Prediction fields depend on the trained model/prediction artifact available in the running environment.

### 3.5 Product trend

```http
GET /products/P1029/trend
```

Returns monthly records containing `month`, `orders`, `units_sold`, `returned_units`, `return_rate`, `avg_rating`, `negative_review_rate`, and `support_ticket_count`.

### 3.6 Product support tickets

```http
GET /products/P1029/tickets
```

Returns `ticket_count`, `top_issue_types`, and `avg_resolution_hours`. This summary is based on all support-ticket records for the product in the generated dataset. The `support_ticket_count` in a monthly product risk record is a monthly metric, so the two counts can legitimately differ.

### 3.7 Product investigation

Request:

```http
POST /investigate
Content-Type: application/json
```

Body:

```json
{
  "product_id": "P1023",
  "question": "Why is this product high risk? Identify the top three root cause candidates, supporting evidence, and recommended actions."
}
```

Windows CMD example with formatted JSON output (requires the Python launcher `py`):

```cmd
curl -s -X POST "http://localhost:8000/investigate" -H "Content-Type: application/json" -d "{\"product_id\":\"P1023\",\"question\":\"Why is this product high risk? Identify the top three root cause candidates, supporting evidence, and recommended actions.\"}" | py -m json.tool
```

Without Python formatting:

```cmd
curl -X POST "http://localhost:8000/investigate" -H "Content-Type: application/json" -d "{\"product_id\":\"P1023\",\"question\":\"Why is this product high risk? Identify the top three root cause candidates, supporting evidence, and recommended actions.\"}"
```

The investigation response contains:

| Field | Description |
|---|---|
| `product_id` | Product being investigated |
| `question` | User's investigation question |
| `generation_mode` | `llm` or `deterministic_fallback` |
| `retrieval_mode` | `semantic_faiss` or `keyword_fallback` |
| `response` | Findings, evidence, root-cause candidates, actions, sources, and disclaimer |
| `raw_evidence` | Product risk, recent trend, and support summary supplied to synthesis |
| `retrieved_sources` | Retrieved chunk details, scores, and retrieval mode |

## 4. Validation and error responses

- Invalid request fields are rejected by Pydantic/FastAPI request validation (HTTP 422).
- An unknown product identifier returns HTTP 404 for product-specific routes.
- A runtime investigation service failure can return HTTP 503 with a generic service-unavailable detail; inspect backend logs for the underlying diagnostic.
- A successful health or data request returns HTTP 200.

## 5. Environment configuration

| Variable | Description |
|---|---|
| `PRODUCT_PULSE_LLM` | `none` for deterministic fallback or `gemini` to enable Gemini |
| `GEMINI_API_KEY` | Secret key required for Gemini mode |
| `GEMINI_MODEL` | Gemini model identifier; default in the application is `gemini-3.5-flash-lite` |
| `CORS_ALLOW_ORIGINS` | Comma-separated list of permitted frontend origins |
| `LOG_LEVEL` | Logging level |

Use a local `.env` file for secrets and configuration. Do not add secrets to source control.

## 6. Interactive documentation

The running FastAPI instance publishes request and response schemas through Swagger UI at:

<http://localhost:8000/docs>
