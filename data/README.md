# The data

These are exports from the pilot's logs, covering six weeks from Monday 10 Aug 2026. Timestamps are
UTC; the pilot customer is in Singapore (UTC+8). User ids are pseudonymised.

## pilot_questions.csv: one row per question
| Column | Meaning |
|---|---|
| `asked_at_utc` | when the question reached the Lambda |
| `cache_key` | the first 12 characters of the handler's cache key |
| `cache_hit` | 1 if the answer came from `answer_cache` |
| `http_status`, `latency_ms` | what the user saw, from the API Gateway access log. `latency_ms` stops at 29,000 when the gateway gives up |
| `run_ms` | how long the Lambda ran, including after the gateway gave up |
| `stop_reason` | `answered`, `step_cap` (the loop reached `MAX_STEPS`) or `cache` |
| `llm_calls`, `tool_calls` | model calls and tool calls in the run; a retried tool call counts once |
| `carrier_calls` | billed carrier calls; rejected ones aren't billed |
| `tokens_in`, `tokens_out` | summed over the run's model calls |
| `cost_usd` | model plus carrier spend for the question; AWS isn't included |

## pilot_tool_calls.csv: one row per tool call attempt
| Column | Meaning |
|---|---|
| `step` | the loop step the call was made in |
| `attempt` | `carrier_track` retries are logged as separate attempts |
| `target` | the tool's main input |
| `status` | `ok`, or `429` when the carrier API rejected the call |
| `result_count` | rows returned by `list_shipments` |
| `data_age_min` | minutes since that shipment's row was last refreshed from the bulk feed |
| `differs_from_db` | carrier calls only: 1 if the live status differed from our row. Added for the pilot review by comparing each live call with the row at that moment |
| `cost_usd` | the carrier charge for the call |

## pilot_users.csv
`role` is `operator` or `team_lead`. `shipments_in_scope` is the number of the pilot's active
shipments that are theirs; the team lead's scope is the whole desk.

## tenants.csv: the pilot plus the 49 customers on the sales list
| Column | Meaning |
|---|---|
| `status` | `pilot`, `signed` or `pipeline` |
| `target_go_live` | the month the customer goes live (`live` for the pilot) |
| `seats` | users, team leads included |
| `teams` | teams, each with one team lead |
| `active_shipments` | shipments in flight at any one time |
| `utc_offset_hours` | standard time; ignore daylight saving |
| `price_per_seat_usd` | the price for all of that customer's seats |
