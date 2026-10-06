"""Plot the fixed-model cost scenarios. Do not change the earlier reports.

Run from the project folder in PowerShell:
    $env:PYTHONPATH = "$PWD\\.plot_deps"
    python plot_redesign_costs.py

The token and carrier reductions are untested assumptions.
All comparison bars exclude infrastructure and indexing costs.
"""
import csv
import json
from decimal import Decimal
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter

root = Path(__file__).resolve().parent
output = root / "redesign_cost_outputs"
baseline = json.loads((root / "poc/architecture-50-costs.json").read_text(encoding="utf-8"))
prices = (root / "costs-and-limits.md").read_text(encoding="utf-8")
model_price_row = next(line for line in prices.splitlines() if line.startswith("| `m-large`"))
assert "| $2.00 / 1M tokens | $8.00 / 1M tokens |" in model_price_row
assert "$0.004 per successful call." in prices
assert "next tier is $300 for 10M" in prices
assert baseline["customers"] == 50 and baseline["seats"] == 5267

model = Decimal(str(baseline["projected_model_month_usd"]))
carrier = Decimal(str(baseline["projected_carrier_month_usd"]))
assert abs(model + carrier - Decimal(str(baseline["projected_model_carrier_month_usd"]))) < Decimal("0.00000001")
scenarios = [
    ("Original role-based projection", Decimal("1"), Decimal("1")),
    ("60% fewer tokens; carrier calls unchanged", Decimal("0.4"), Decimal("1")),
    ("60% fewer tokens; 70% fewer paid carrier calls", Decimal("0.4"), Decimal("0.3")),
]
rows = []
for name, token_factor, carrier_factor in scenarios:
    model_cost, carrier_cost = model * token_factor, carrier * carrier_factor
    rows.append({"scenario": name, "model": "m-large", "input_token_factor": token_factor,
                 "output_token_factor": token_factor, "carrier_call_factor": carrier_factor,
                 "model_usd_month": model_cost, "carrier_usd_month": carrier_cost,
                 "total_usd_month": model_cost + carrier_cost,
                 "cost_usd_seat_month": (model_cost + carrier_cost) / baseline["seats"],
                 "scope": "Model + carrier only; infrastructure excluded"})

# Check the displayed totals. Keep full precision until presentation.
assert [r["total_usd_month"].quantize(Decimal("0.01")) for r in rows] == [
    Decimal("12523.41"), Decimal("6057.07"), Decimal("4834.75")]
vector_subtotal = rows[-1]["total_usd_month"] + Decimal("300")
assert vector_subtotal.quantize(Decimal("0.01")) == Decimal("5134.75")

output.mkdir(exist_ok=True)
with (output / "fixed_model_cost_projection.csv").open("w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 16,
                     "svg.fonttype": "none", "text.parse_math": False, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.spines.left": False})
fig, ax = plt.subplots(figsize=(16, 9), facecolor="white")
model_costs = [float(r["model_usd_month"]) for r in rows]
carrier_costs = [float(r["carrier_usd_month"]) for r in rows]
ax.bar(range(3), model_costs, .56, color="#2563a6", label="Model — m-large")
ax.bar(range(3), carrier_costs, .56, bottom=model_costs, color="#d95f02", label="Carrier calls")
for i, row in enumerate(rows):
    ax.text(i, float(row["total_usd_month"]) + 280, f'${row["total_usd_month"]:,.2f}',
            ha="center", va="bottom", fontsize=22, fontweight="bold", color="#172337")
    ax.text(i, model_costs[i]/2, f'${row["model_usd_month"]:,.2f}',
            ha="center", va="center", fontsize=18, fontweight="bold", color="white")
    height = model_costs[i] + carrier_costs[i]/2
    ax.annotate(f'${row["carrier_usd_month"]:,.2f}', (i+.28, height), (i+.38, height),
                ha="left", va="center", fontsize=16, color="#172337",
                arrowprops={"arrowstyle": "-", "color": "#465469", "lw": 1.2})

ax.set_xticks(range(3), ["Original projection\nPilot usage by role",
                       "60% fewer tokens\nCarrier calls unchanged",
                       "60% fewer tokens\n70% fewer paid carrier calls"])
ax.tick_params(axis="x", length=0, pad=15, labelsize=16)
ax.tick_params(axis="y", length=0, labelsize=14)
ax.set_xlim(-.65, 2.85)
ax.set_ylim(0, 14500)
ax.set_yticks(range(0, 12501, 2500))
ax.yaxis.set_major_formatter(StrMethodFormatter("${x:,.0f}"))
ax.set_ylabel("Monthly model + carrier cost (USD)", fontsize=16, labelpad=15)
ax.grid(axis="y", color="#e3e8ef", linewidth=1)
ax.set_axisbelow(True)
fig.suptitle("Monthly cost for 50 customers — same m-large model", x=.08, y=.965,
             ha="left", fontsize=25, fontweight="bold", color="#172337")
fig.text(.08, .900, "30-day month · 5,267 seats · Model + carrier only · Infrastructure excluded",
         fontsize=16, color="#465469")
fig.legend(loc="upper right", bbox_to_anchor=(.95, .884), ncol=2, frameon=False, fontsize=16)
fig.text(.08, .185, "SCENARIO ASSUMPTIONS — reductions are untested; all bars use the same prices.",
         fontsize=15, fontweight="bold", color="#172337")
fig.text(.08, .147, "m-large: $2 / 1M input tokens, $8 / 1M output tokens. Carrier: $0.004 / successful call.", fontsize=14)
fig.text(.08, .109, f"Proposed 10M-vector tier: +$300/month. Last case: ${vector_subtotal:,.2f} + other infrastructure and indexing costs.", fontsize=14)
fig.text(.08, .071, "Carrier savings require agreed data freshness. A queue alone saves no model or carrier cost.", fontsize=14)
fig.text(.08, .033, "Safe caching and complete reports can change usage. Source: poc/architecture-50-costs.json.", fontsize=14, color="#465469")
fig.subplots_adjust(left=.10, right=.95, top=.82, bottom=.30)
fig.savefig(output / "fixed_model_cost_projection.png", dpi=180, facecolor="white")
fig.savefig(output / "fixed_model_cost_projection.svg", facecolor="white")
plt.close(fig)
for row in rows:
    print(f'{row["scenario"]}: model ${row["model_usd_month"]:,.2f} + carrier ${row["carrier_usd_month"]:,.2f} = ${row["total_usd_month"]:,.2f}')
print(f"Last case plus vector tier: ${vector_subtotal:,.2f}; other infrastructure and indexing costs excluded.")
print("Arithmetic and source-price checks passed.")
