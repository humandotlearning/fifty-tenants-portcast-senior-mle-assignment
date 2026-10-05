# Costs and limits

Assume these for the exercise.

## Model
| | Input | Output | Notes |
|---|---|---|---|
| `m-large` (what the POC uses) | $2.00 / 1M tokens | $8.00 / 1M tokens | good at multi-step tool use |
| `m-fast` | $0.40 / 1M tokens | $1.60 / 1M tokens | about twice as fast; noticeably worse at multi-step tool use |

Both have a 200k-token context window. Assume no discount for prompt caching, and that the model
vendor's rate limits aren't a constraint.

## Carrier tracking API (live status)
- $0.004 per successful call.
- **60 successful requests per calendar minute per account.** Rejected requests (HTTP 429) aren't
  counted or billed. There is one account, shared by every customer.
- Latency: p50 ~2 s, p95 ~4 s.
- A higher tier gives 600 successful requests per calendar minute for $1,500 a month plus $0.003 per call.

## Carrier bulk feed
- Free to use. An ingest job pulls it every **4 hours** into the `shipments` and `events` tables.

## AWS (monthly, at pilot scale)
| | Cost | Limit that matters |
|---|---|---|
| API Gateway + Lambda | ~$12 | API Gateway waits **29 s** for the Lambda, then returns 504. Lambda timeout is 90 s. Account concurrency 1,000 |
| RDS Postgres, db.t4g.medium | ~$62 | ~400 connections |
| S3 | ~$3 | — |
| Vector DB, starter tier | $70 | up to 1M vectors; the next tier is $300 for 10M. The pilot's index holds about 9,000 |
| CloudWatch | ~$8 | — |

## Price
- $10 per seat per month; $7 for customers with 151-300 seats; $6 above 300. The price applies to
  all of a customer's seats.
- Each customer's seats and price are in `data/tenants.csv`.
