# Product Pulse — Data Science and Machine Learning

## 1. Objective

The data science component explores product performance and predicts whether a product is likely to be classified as high risk in the following month. The workflow covers data generation, validation, exploratory analysis, feature engineering, model comparison, evaluation, and live inference.

## 2. Data source and reproducibility

All records are programmatically generated synthetic demonstration data. The generator uses a fixed random seed of `42` and creates a January–December 2025 history. Eight products include seeded risk patterns so that risk scenarios can be reproduced during development and demonstration.

| Table | Rows | Purpose |
|---|---:|---|
| `products.csv` | 40 | Product attributes, category, and brand |
| `customers.csv` | 500 | Synthetic customer dimension |
| `orders.csv` | 5,010 | Order headers and order dates |
| `order_items.csv` | 6,202 | Product-level items, quantities, and prices |
| `returns.csv` | 444 | Returned item records |
| `reviews.csv` | 2,200 | Product feedback and ratings |
| `support_tickets.csv` | 1,000 | Support issue and resolution records |
| `product_metrics_monthly.csv` | 480 | Monthly metrics for 40 products across 12 months |
| `product_risk_labels.csv` | 440 | Next-month labels; December is excluded because a following month is not available in the dataset |
| `knowledge_documents.csv` | 48 | Product knowledge and historical guidance used by RAG |
| `product_risk_summary.csv` | 40 | Product-level latest-period risk summary |

The detailed generation metadata is recorded in `docs/DATA_GENERATION_METADATA.json`. Regenerate the source data with:

```bash
python scripts/generate_data.py
```

## 3. Data validation

The validation script checks table existence, row-level identifiers, relationships between customers/orders/items/products/returns/reviews/tickets, monthly record uniqueness, valid references, and ranges for rates and ratings.

The recorded validation report shows **24 of 24 checks passed**. It also reports no missing cells or duplicate rows in the listed core tables. Run validation with:

```bash
python scripts/validate_data.py
```

See `docs/DATA_VALIDATION_REPORT.md` for the recorded table statistics and checklist.

## 4. Exploratory data analysis

The notebook `notebooks/01_eda_business_kpis.ipynb` is the EDA entry point. The analysis is designed to explore product and portfolio behavior using Pandas, NumPy, and visualizations.

Relevant business and quality measures include:

- Order and unit volume.
- Gross sales value derived from item quantity and unit price.
- Return volume and return rate.
- Average product rating and negative-review rate.
- Support ticket volume and issue categories.
- Monthly changes in product metrics.
- Product risk score and Low/Medium/High risk distribution.

The EDA provides descriptive context for the supervised learning task. Observed metric relationships in this synthetic dataset should not be interpreted as causal effects.

## 5. Prediction target

The model objective is to estimate next-month high-risk status using the current month's product signals.

The target field is `future_high_risk`. It represents whether the next month's rolling composite product risk score reaches the defined high-risk threshold (`>= 0.55`). December records are excluded from supervised training because their next-month target would fall outside the generated history.

## 6. Feature engineering

The training script creates the following feature groups:

| Feature group | Examples |
|---|---|
| Current-month activity | `orders`, `units_sold`, `returned_units`, `review_count` |
| Product quality and feedback | `return_rate`, `avg_rating`, `negative_review_rate` |
| Support activity | `support_ticket_count` |
| Three-month rolling signals | `return_rate_3m_avg`, `rating_3m_avg`, `negative_review_rate_3m_avg`, `ticket_count_3m_avg` |
| One-month changes | `return_rate_change_1m`, `avg_rating_change_1m`, `negative_review_rate_change_1m`, `support_ticket_count_change_1m` |
| Product descriptors | `category`, `brand` |

Numeric fields are median-imputed and standardized. Categorical fields are imputed using the most frequent value and one-hot encoded. The preprocessing steps are included in the scikit-learn pipeline so the same transformations are applied at inference time.

## 7. Models and evaluation design

Two candidate classifiers are compared:

- **Logistic Regression:** balanced class weights, increased iteration limit, and fixed random state.
- **Random Forest:** 300 trees, depth limit of 6, minimum leaf size of 2, balanced class weights, and fixed random state.

A chronological split is used to reduce the risk of training on future months:

| Split | Period |
|---|---|
| Training | January–August 2025 (through `2025-08`) |
| Validation | September 2025 (`2025-09`) |
| Test | October–November 2025 (`2025-10` and `2025-11`) |

The candidate model is selected using validation F1, with validation ROC-AUC as a tie-breaker. Reported metrics include accuracy, precision, recall, F1, and ROC-AUC.

### Recorded evaluation results

The checked-in model report records the following results:

| Model | Validation F1 | Validation ROC-AUC | Test F1 | Test ROC-AUC |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.824 | 0.996 | 0.826 | 0.991 |
| Random Forest | 0.800 | 0.987 | 0.895 | 0.979 |

The validation-based selection rule selects Logistic Regression in the recorded report because its validation F1 is higher. Random Forest has a higher test F1 in this particular split; this does not change the pre-defined validation-based selection rule.

The training report is generated at `docs/ML_MODEL_REPORT.json` and `docs/ML_MODEL_REPORT.md` by:

```bash
python scripts/train_model.py
```

## 8. Model artifact and live inference

The selected preprocessing/classification pipeline is serialized to:

```text
models/risk_model.joblib
```

The product risk API returns the product's current risk signals and, when a trained prediction artifact/model is available in the running application, next-month prediction fields such as:

- `predicted_next_month_high_risk_probability`
- `predicted_next_month_high_risk`
- `ml_prediction_month`
- `ml_prediction_target_month`
- `ml_model_name`
- `ml_prediction_source`

A local API smoke test on October 31, 2026 confirmed `ml_prediction_source: live_model_inference` for a product-risk request. This confirms the current integration path; the value itself remains a prediction based on synthetic training data.

## 9. Interpretation and limitations

- The records are synthetic and include designed risk patterns. Strong scores can reflect those patterns and should not be generalized to live retail operations.
- The validation window contains one month and the test window contains two months; wider temporal and external validation would be required for a production model.
- A predicted probability is a model estimate, not a guarantee that a product will become high risk.
- A risk score is a prioritization signal. Operational decisions require additional context and human review.

## 10. Reproduction commands

```bash
python scripts/generate_data.py
python scripts/validate_data.py
python scripts/train_model.py
pytest -q
```
