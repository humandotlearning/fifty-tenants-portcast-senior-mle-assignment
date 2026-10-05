# A small cost fit: fifty customers are not fifty pilot workloads

The 84-line standard-library script fits four mean costs: operator/team lead × whether the question contains “my shipments.” This is least-squares regression with two binary predictors and their interaction. Predictors are available before execution; billed tokens and carrier calls are used only to reconcile spend.

First 28 days train (1,437 questions), last 14 days test (515): fitted MAE **3.1832 cents**, RMSE **6.3880 cents**, versus role-only baseline **3.9474 / 7.2557 cents**. Refit averages for projection are $0.011287/operator ordinary question, $0.013457/operator portfolio question, $0.011564/lead ordinary question and $0.097489/lead portfolio question. The time split tests later pilot traffic, with recurring users/questions, not unseen customers.

The six-week pilot spent **$54.188814**: $46.240814 in tokens + 1,987 successful carrier calls × $0.004 = $7.948000. Question and tool totals reconcile without double-counting. All 132 timed-out runs are included ($36.108102); 323 questions were cache hits. The sole lead asked 993/1,952 questions and generated 79.7% of spend.

| 30-day monthly comparison | Model + carrier |
|---|---:|
| Pilot | $38.71 |
| Fifty identical pilots | $1,935.31 |
| Listed fifty customers, pilot role behavior retained | **$12,523.41** |
| Same customers, half the lead question frequency | $6,754.57 |

The fifty customers have **5,267 seats, 374 leads and 175,750 shipments**. Revenue is **$45,340/month**, applying each customer's tier to all its seats. Projection arithmetic is **4,893 operators × $0.201459/month + 374 leads × $30.849380/month**. Thus spend is 323.55 pilot equivalents, or **6.47× the fifty-times estimate**; $2.38/seat and 72.38% margin before infrastructure and other costs. Per-tenant costs, revenue and margins are in tenant_costs.csv.

The fit helps distinguish expensive pilot questions. Summing its refitted predictions reproduces pilot role totals: aggregate scaling is role-count arithmetic, not an independently learned law about larger customers.

Assumptions and limits:

- One lead per team; other seats are operators. Each retains the pilot role's per-user question frequency, query mix, cache behavior and average billed work. Only one lead/customer was observed; representative lead behavior is the largest unverified assumption. The knob multiplies lead question frequency, with mix/cost fixed.
- A month is 30 days; the pilot denominator is 42 complete calendar days, including quiet days. All fifty are live simultaneously, including pipeline customers, without probability adjustment. Rollout timing and timezone-related burst capacity are outside this small cost model.
- Larger shipment counts do not increase per-question cost here. This preserves the observed capped POC behavior, not complete portfolio answers: its 25-step limit can omit work. Scope and lead role are confounded in this pilot; shipment fan-out is not fitted. Team allocation, context growth and completed-work cost require new data.
- Preserving observed cache hit rates assumes tenant/user scoping is fixed without losing savings. The current question-only key is unsafe across scopes; correcting it may increase spend. This projection must not rely on cross-tenant cache reuse.
- Exercise model/carrier tariffs and tool policy stay fixed. Rejected carrier calls are unbilled; observed billed costs include retry effects and timed-out work. Costs are observed executed work, not unconstrained demand under the shared 60-successes/minute quota.
- AWS/vector infrastructure is excluded from projected model/carrier spend. The stipulated pilot infrastructure is $155/month; its scaling is not established, and model/carrier margin is not business profit.

Run from the assignment workspace (Python only, no installation):
```powershell
python cost_model.py
python cost_model.py --lead-frequency 0.5 --output model_outputs_half_lead
```

To run the saved copy from any directory:
```powershell
python 'C:\Users\nithi\Documents\Codex\2026-10-04\realtime-voice-chat\outputs\portcast-cost-model\cost_model.py' --data 'C:\Users\nithi\Downloads\Compressed\fifty-tenants-portcast-senior-mle-assignment\fifty-tenants-portcast-senior-mle-assignment\data' --output 'C:\Users\nithi\Documents\Codex\2026-10-04\realtime-voice-chat\outputs\portcast-cost-model'
```

Validation: both default and half-lead runs passed inline checks for calendar coverage, tariff reconstruction, tool/question carrier agreement, pilot-total reproduction and tenant seat tiers. Capacity simulation and a shipment-size regression were deliberately omitted.
