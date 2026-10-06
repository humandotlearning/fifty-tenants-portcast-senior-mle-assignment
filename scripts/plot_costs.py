"""Plot the pilot fit and monthly cost arithmetic. Requires matplotlib."""
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter
from cost_model import read, fit

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--data", type=Path, default=Path(__file__).resolve().parent.parent / "data")
p.add_argument("--output", type=Path, default=Path(__file__).resolve().parent.parent / "model_outputs")
a = p.parse_args()
q, users, tenants = read(a.data / "pilot_questions.csv"), read(a.data / "pilot_users.csv"), read(a.data / "tenants.csv")
roles = {u["user_id"]: u["role"] for u in users}
for r in q:
    r["role"], r["portfolio"] = roles[r["user_id"]], "my shipments" in r["question_text"].lower()
    r["at"] = datetime.fromisoformat(r["asked_at_utc"].replace("Z", "+00:00"))
start = min(r["at"] for r in q).replace(hour=0, minute=0, second=0, microsecond=0)
train, test = [r for r in q if r["at"] < start + timedelta(days=28)], [r for r in q if r["at"] >= start + timedelta(days=28)]
model, baseline = fit(train), fit(train, False)
keys = [("operator", False), ("operator", True), ("team_lead", False), ("team_lead", True)]
plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})
a.output.mkdir(parents=True, exist_ok=True)
fig, ax = plt.subplots(figsize=(12, 7))
for i, key in enumerate(keys):
    rows = [r for r in test if (r["role"], r["portfolio"]) == key]
    # Spread dots sideways only so repeated/zero costs remain visible.
    ax.scatter([i + ((j*17 % 31)/30 - .5)*.42 for j in range(len(rows))], [100*float(r["cost_usd"]) for r in rows],
               s=20, alpha=.35, color="#2c7fb8", label="Actual held-out questions" if i == 0 else None)
    ax.hlines(100*model[key], i-.29, i+.29, color="#d95f02", linewidth=3, label="Four-group prediction (trained on first 28 days)" if i == 0 else None)
    ax.scatter(i, 100*mean(float(r["cost_usd"]) for r in rows), marker="D", s=70, color="#1b9e77", edgecolors="white",
               zorder=4, label="Actual held-out group average" if i == 0 else None)
    ax.text(i, -.06, f"n = {len(rows)}", transform=ax.get_xaxis_transform(), ha="center", color="#555555")
ax.set_xticks(range(4), ["Operator\nOther questions", "Operator\n'My shipments'", "Team lead\nOther questions", "Team lead\n'My shipments'"])
ax.tick_params(axis="x", pad=30)
ax.set_ylabel("Model + carrier cost per question (US cents)")
ax.set_ylim(bottom=-1)
ax.grid(axis="y", alpha=.18)
ax.legend(loc="upper left", fontsize=10, frameon=False)
fig.suptitle("The fit distinguishes question types; individual costs still vary", fontsize=17, fontweight="bold", y=.96)
ax.set_title(f"Final 14 days: {len(test)} held-out questions; four fixed category predictions", fontsize=12, pad=16)
errors = [[float(r["cost_usd"])-(model[(r["role"], r["portfolio"])] if detailed else baseline[r["role"]]) for r in test] for detailed in [True, False]]
metrics = [(100*mean(abs(e) for e in es), 100*mean(e*e for e in es)**.5) for es in errors]
fig.text(.08, .055, f"Average gap between prediction and actual cost: fit {metrics[0][0]:.2f} cents vs role-only {metrics[1][0]:.2f} cents.", fontsize=11)
fig.text(.08, .02, "This tests later pilot questions, not a fitted relationship between tenant size and spending.", fontsize=11, color="#555555")
fig.subplots_adjust(bottom=.23, top=.83, left=.08, right=.98)
fig.savefig(a.output / "fit_heldout.png", dpi=180)
plt.close(fig)

rates = {role: sum(float(r["cost_usd"]) for r in q if r["role"] == role)/sum(u["role"] == role for u in users)*30/42 for role in ["operator", "team_lead"]}
leads = sum(int(t["teams"]) for t in tenants)
operators = sum(int(t["seats"])-int(t["teams"]) for t in tenants)
ops = [50*39*rates["operator"], operators*rates["operator"], operators*rates["operator"]]
lead = [50*rates["team_lead"], leads*rates["team_lead"], .5*leads*rates["team_lead"]]
totals = [o+l for o, l in zip(ops, lead)]
fig, ax = plt.subplots(figsize=(12, 7))
ax.bar(range(3), ops, .58, color="#2c7fb8", label="Operators")
ax.bar(range(3), lead, .58, bottom=ops, color="#d95f02", label="Team leads")
for i, total in enumerate(totals):
    ax.text(i, total+280, f"$"+"{total:,.2f}".format(total=total), ha="center", fontsize=15, fontweight="bold")
    ax.text(i, ops[i]+lead[i]/2, f"$"+"{part:,.2f}".format(part=lead[i]), ha="center", va="center", color="white", fontsize=12)
    ax.text(i, -950, f"Operator portion: $"+f"{ops[i]:,.2f}", ha="center", fontsize=11, color="#2c7fb8")
ax.set_xticks(range(3), ["50 identical pilots\n1,950 operators + 50 leads", "Actual 50 tenants\n4,893 operators + 374 leads", "Actual 50, half lead frequency\nOperator usage unchanged"])
ax.tick_params(axis="x", pad=40)
ax.set_ylim(0, max(totals)*1.18)
ax.yaxis.set_major_formatter(StrMethodFormatter("${x:,.0f}"))
ax.set_ylabel("Monthly model + carrier spending (USD)")
ax.grid(axis="y", alpha=.18)
ax.set_axisbelow(True)
ax.legend(loc="upper left", frameon=False)
fig.suptitle("More team leads drive spending above fifty pilot workloads", fontsize=17, fontweight="bold", y=.96)
ax.set_title(f"30-day months; full lead frequency = {totals[1]/totals[0]:.2f}x baseline; half frequency = {totals[2]/totals[0]:.2f}x", fontsize=12, pad=16)
fig.text(.08, .09, f"Actual-tenant formula (USD): {operators:,} x {rates['operator']:.8f} + {leads} x {rates['team_lead']:.8f} x lead frequency", fontsize=11)
fig.text(.08, .055, "Per-user monthly rates come from the 42-day pilot, including all timed-out billed work. Infrastructure excluded.", fontsize=11)
fig.text(.08, .02, "Assumes ONE pilot lead represents future leads; role usage, question mix and cache savings stay the same.", fontsize=11, color="#555555")
fig.subplots_adjust(bottom=.29, top=.83, left=.09, right=.98)
fig.savefig(a.output / "monthly_spending.png", dpi=180)
plt.close(fig)
print(f"Verified arithmetic: baseline ${totals[0]:.2f}; full ${totals[1]:.2f} ({totals[1]/totals[0]:.4f}x); half ${totals[2]:.2f} ({totals[2]/totals[0]:.4f}x)")
print(f"Plots: {(a.output / 'fit_heldout.png').resolve()} and {(a.output / 'monthly_spending.png').resolve()}")
