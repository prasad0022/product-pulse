# Product Pulse — Project Overview

**Official project title:** Product Risk Detection Platform  
**Application name:** Product Pulse  
**Release target:** v1.0.0  
**Project type:** DSAI capstone demonstration

## 1. Background

E-commerce product quality and customer experience are reflected across multiple operational data sources. Orders, returns, reviews, monthly product metrics, and support tickets each describe part of the product lifecycle. Reviewing these sources independently can make it difficult to identify products that may be developing quality or experience problems and to assemble the evidence needed for investigation.

Product Pulse demonstrates an integrated approach: consolidate product-level signals, estimate future risk, retrieve relevant product knowledge, and present a structured investigation that a human reviewer can validate.

## 2. Problem statement

The project addresses the following problem:

> How can product-level commerce and customer-feedback signals be combined to identify products with elevated future risk and support an evidence-led investigation of possible contributing factors?

The platform is a decision-support prototype. It does not establish causality or replace quality, operations, or customer-support review.

## 3. Objectives

1. Create a reproducible synthetic commerce dataset representing a product portfolio and its related transactions and feedback.
2. Validate the generated data for completeness, uniqueness, referential consistency, and valid metric ranges.
3. Explore business and product-quality KPIs using Python, Pandas, NumPy, and visual analysis.
4. Build and evaluate a supervised model to estimate whether a product will be high risk in the following month.
5. Provide API access to portfolio summaries, product risk, monthly trends, and support-ticket summaries.
6. Retrieve product-specific guidance and historical knowledge relevant to an investigation question.
7. Use an optional LLM to generate structured findings, evidence, root-cause candidates, recommendations, and source references.
8. Present the insights through a web dashboard and provide a reproducible containerized setup.

## 4. Scope

### Included

- Synthetic product, customer, order, order-item, return, review, and support-ticket data.
- Monthly product metrics and next-month risk labels.
- Data validation and EDA/business KPI analysis.
- Classification model training, chronological validation, model artifact generation, and live API inference.
- Product-scoped RAG using Sentence Transformers and FAISS, with keyword retrieval fallback.
- Optional Gemini-based structured response generation and deterministic fallback behavior.
- FastAPI backend, React dashboard, Docker Compose setup, tests, and GitHub Actions CI configuration.

### Not included

- Production integration with a real retailer, OMS, CRM, ERP, returns platform, or support-ticket platform.
- Use of real personal, customer, payment, or confidential business data.
- Automated corrective actions, refunds, replacements, or operational decisions.
- A production-grade causal inference system or a guarantee that an identified candidate is the true root cause.
- A formally validated production ML model or a comprehensive LLM evaluation benchmark.

## 5. Dataset summary

The project uses programmatically generated data with a fixed seed (`42`) for repeatability. The synthetic history covers January–December 2025 and contains:

| Dataset | Records |
|---|---:|
| Products | 40 |
| Customers | 500 |
| Orders | 5,010 |
| Order items | 6,202 |
| Returns | 444 |
| Reviews | 2,200 |
| Support tickets | 1,000 |
| Monthly product metrics | 480 |
| Monthly next-month risk labels | 440 |
| Product knowledge documents / RAG chunks | 48 |

Eight products have seeded risk patterns to make scenarios reproducible. These records are artificial and should not be interpreted as actual market observations.

## 6. Solution summary

Product Pulse brings together four main analytical stages:

1. **Descriptive analytics:** calculate portfolio and product-level metrics from the generated tables.
2. **Predictive analytics:** use historical monthly signals to estimate next-month high-risk probability.
3. **Knowledge retrieval:** retrieve relevant product-scoped documents for an investigation question.
4. **AI-assisted synthesis:** combine product metrics and retrieved knowledge into a structured response, with citations to retrieved source documents.

The frontend provides the user-facing dashboard, while FastAPI exposes the data and investigation workflows.

## 7. Expected outputs

- A reproducible synthetic dataset and data-quality validation report.
- An EDA notebook and a model evaluation report.
- A saved ML model artifact and live prediction fields from the product risk API.
- Product and portfolio API endpoints.
- Retrieved knowledge sources and structured product investigation responses.
- A browser-based dashboard and Docker Compose runtime.

## 8. Evaluation and limitations

The project demonstrates an end-to-end data science and AI application on a controlled synthetic dataset. The reported classification metrics are useful for comparing the candidate models on this generated dataset, but they do not estimate performance on real commerce data. The RAG hit@5 result is based on a small curated keyword-retrieval query set and does not measure semantic retrieval quality or answer faithfulness. Root-cause candidates remain hypotheses that require validation.

## 9. Conclusion

Product Pulse demonstrates how data engineering, exploratory analysis, supervised machine learning, semantic retrieval, optional LLM synthesis, API development, and frontend visualization can be connected into one product-risk investigation workflow. The v1.0.0 release represents the completed capstone prototype and its supporting technical documentation.
