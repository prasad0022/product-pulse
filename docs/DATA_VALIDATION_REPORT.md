# Product Pulse Data Validation Report

Overall result: **PASS**

## Checks
- [x] exactly 40 products
- [x] unique product ids
- [x] unique customer ids
- [x] unique order ids
- [x] unique order item ids
- [x] unique return ids
- [x] unique review ids
- [x] unique ticket ids
- [x] orders reference customers
- [x] items reference orders
- [x] items reference products
- [x] returns reference order items
- [x] reviews reference products
- [x] reviews reference customers
- [x] tickets reference products
- [x] tickets reference customers
- [x] monthly metrics have 480 rows
- [x] monthly metric product month unique
- [x] labels exclude december
- [x] labels reference products
- [x] knowledge docs reference products
- [x] chunks reference documents
- [x] return rates in range
- [x] ratings in range

## Table statistics

| File | Rows | Columns | Missing cells | Duplicate rows |
|---|---:|---:|---:|---:|
| `products.csv` | 40 | 7 | 0 | 0 |
| `customers.csv` | 500 | 4 | 0 | 0 |
| `orders.csv` | 5,010 | 6 | 0 | 0 |
| `order_items.csv` | 6,202 | 5 | 0 | 0 |
| `returns.csv` | 444 | 6 | 0 | 0 |
| `reviews.csv` | 2,200 | 6 | 0 | 0 |
| `support_tickets.csv` | 1,000 | 9 | 0 | 0 |
| `product_metrics_monthly.csv` | 480 | 10 | 0 | 0 |
| `product_risk_labels.csv` | 440 | 5 | 0 | 0 |
| `knowledge_documents.csv` | 48 | 5 | 0 | 0 |
| `product_risk_summary.csv` | 40 | 10 | 0 | 0 |

RAG chunks: 48

All input records are synthetic demo data.
