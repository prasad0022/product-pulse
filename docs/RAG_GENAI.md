# Product Pulse — RAG and Generative AI

## 1. Purpose

The RAG and GenAI component supports product-level investigation. Given a product identifier and a natural-language question, Product Pulse gathers structured product evidence, retrieves relevant product-scoped knowledge, and generates a concise investigation response.

The response is intended for decision support. It must distinguish observed evidence from inferred root-cause candidates and must not present an inference as a confirmed cause.

## 2. Knowledge corpus

The synthetic knowledge corpus contains **48 product knowledge documents**, represented as **48 retrieval chunks** in `data/rag/document_chunks.csv`. The source records are associated with product identifiers and include product guidance, known symptoms, potential root causes, warranty guidance, operational recommendations, and/or historical RCA context.

The product identifier is used to scope retrieval so the investigation does not intentionally search across unrelated products.

## 3. Semantic retrieval

The semantic retrieval path uses:

- Sentence Transformers model: `sentence-transformers/all-MiniLM-L6-v2`
- Vector index: FAISS CPU
- Similarity approach: normalized embeddings with FAISS inner-product search
- Retrieval limit: up to five chunks per investigation request

The retriever loads the chunk table, creates embeddings for the selected product's chunks, builds/caches a product-specific FAISS index, embeds the user question, and returns the top-ranked chunks with document identifiers, titles, text, similarity score, and retrieval mode.

Successful live investigation output on October 31, 2026 reported `retrieval_mode: semantic_faiss` and returned product-specific source content.

## 4. Keyword fallback

If semantic retrieval dependencies or model initialization are unavailable, the RAG service falls back to a local keyword retriever. The fallback tokenizes the question and source text, ranks chunks by token overlap, and returns the top matches for the selected product.

The API exposes the active retrieval path through `retrieval_mode` (`semantic_faiss` or `keyword_fallback`).

## 5. Retrieval evaluation

The existing evaluation script, `scripts/evaluate_rag.py`, runs a small curated keyword-retrieval smoke benchmark. The recorded report contains:

- 8 manually curated queries.
- Retrieval hit@5: 8/8 (100%) on that query set.

**Interpretation:** this result measures the keyword fallback against a small expected-term query set. It is not a benchmark of FAISS semantic retrieval quality, Gemini response quality, answer faithfulness, or real-world knowledge coverage.

Run it with:

```bash
python scripts/evaluate_rag.py
```

## 6. Investigation workflow

The `/investigate` endpoint receives:

```json
{
  "product_id": "P1023",
  "question": "Why is this product high risk? Identify the top three root cause candidates, supporting evidence, and recommended actions."
}
```

The investigation engine:

1. Retrieves the product risk summary.
2. Retrieves the product's recent monthly trend records.
3. Retrieves a support-ticket summary.
4. Runs product-scoped RAG retrieval for the question.
5. Sends structured evidence and retrieved source text to Gemini when enabled.
6. Validates the generated JSON against the investigation response schema.
7. Filters returned source references to sources actually retrieved by the RAG step.
8. Uses deterministic synthesis if Gemini is disabled or generation/validation fails.

The API response includes `generation_mode`, `retrieval_mode`, `response`, `raw_evidence`, and `retrieved_sources`.

## 7. Gemini integration

Gemini is an optional provider implemented using the Google Gen AI SDK. It is not required to run the core application.

Configure locally using environment variables:

```dotenv
PRODUCT_PULSE_LLM=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

The default setting is:

```dotenv
PRODUCT_PULSE_LLM=none
```

When Gemini mode is active, the provider requests JSON output and the investigation engine validates the response using Pydantic. A live `/investigate` request on October 31, 2026 returned `generation_mode: llm`, `retrieval_mode: semantic_faiss`, and a successful API response, confirming that the configured Gemini and semantic retrieval path was exercised in the local environment.

Provider availability and quotas depend on the configured Google AI account, API key, and model access. Never commit the API key or a populated `.env` file.

## 8. Deterministic fallback

When Gemini is disabled or a generation/validation error occurs, Product Pulse returns a deterministic response based on the available structured metrics and retrieved sources. This fallback helps keep the investigation workflow usable without an external LLM call.

The fallback is not generative AI. The response's `generation_mode` distinguishes it from Gemini output (`deterministic_fallback` versus `llm`).

## 9. Response structure

The investigation response contains:

| Field | Description |
|---|---|
| `findings` | Concise statements describing the observed product situation |
| `evidence` | Relevant metrics, trends, and retrieved knowledge |
| `root_cause_candidates` | Potential explanations that require further validation |
| `recommended_actions` | Suggested follow-up checks or operational actions |
| `sources` | Retrieved document identifiers and titles |
| `disclaimer` | Decision-support and causal uncertainty notice |

`retrieved_sources` is also returned separately with the chunk text and retrieval metadata, allowing the response to be inspected against its source material.

## 10. Limitations and responsible interpretation

- The knowledge corpus is synthetic and limited to the generated product scenarios.
- Product-scoped retrieval can only find information present in the selected product's documents.
- The current retrieval benchmark is small and does not provide a comprehensive semantic retrieval evaluation.
- There is no large-scale human-rated evaluation of Gemini answer quality or factual faithfulness in this project.
- LLM output can still be incomplete or malformed; schema validation and deterministic fallback reduce, but do not eliminate, that risk.
- Root-cause candidates are hypotheses. Validate them with real product, batch, supplier, fulfillment, and customer evidence before taking operational action.
