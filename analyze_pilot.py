"""Create pilot issue charts and export their evidence. Requires matplotlib."""
import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from textwrap import fill

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, StrMethodFormatter
from cost_model import read

BLUE, RED, GREEN, GREY = "#2463a6", "#b84527", "#287a65", "#798493"
SGT = timezone(timedelta(hours=8))
GATEWAY_SECONDS, CARRIER_LIMIT, CACHE_HOURS = 29, 60, 24


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def cache_sources(questions):
    """Infer the last cache write before each hit from Lambda completion time."""
    events, writes, matches = [], {}, {}
    for q in questions:
        at = timestamp(q["asked_at_utc"])
        events.append((at, 1, q["question_id"], q))
        if not int(q["cache_hit"]):
            events.append((at + timedelta(milliseconds=int(q["run_ms"])), 0, q["question_id"], q))
    for at, kind, _, q in sorted(events):
        if kind == 0:
            writes[q["cache_key"]] = (at, q)
        elif int(q["cache_hit"]):
            source = writes.get(q["cache_key"])
            if source and at - source[0] < timedelta(hours=CACHE_HOURS):
                previous = source[1]
                matches[q["question_id"]] = dict(
                    cache_source="different_user" if previous["user_id"] != q["user_id"] else "same_user",
                    source_question_id=previous["question_id"], source_user_id=previous["user_id"],
                    source_stop_reason=previous["stop_reason"])
            else:
                matches[q["question_id"]] = {"cache_source": "unmatched"}
    return matches


def build_evidence(questions, tools, users):
    """Join logs once. Keep attempts separate from distinct live targets."""
    by_question, minutes = defaultdict(list), defaultdict(Counter)
    roles = {u["user_id"]: u["role"] for u in users}
    ids = {q["question_id"] for q in questions}
    assert len(roles) == len(users) and len(ids) == len(questions), "Duplicate IDs"
    for t in tools:
        assert t["question_id"] in ids, "Tool call has no question"
        by_question[t["question_id"]].append(t)
        if t["tool"] == "carrier_track":
            minute = timestamp(t["called_at_utc"]).replace(second=0, microsecond=0)
            minutes[minute][t["status"]] += 1
    sources, rows = cache_sources(questions), []
    for q in questions:
        calls = by_question[q["question_id"]]
        lists = [t for t in calls if t["tool"] == "list_shipments" and t["status"] == "ok"]
        live = [t for t in calls if t["tool"] == "carrier_track" and t["status"] == "ok"]
        row = dict(q)
        row.update(role=roles[q["user_id"]], portfolio="my shipments" in q["question_text"].lower(),
                   timeout=q["http_status"] == "504", run_seconds=int(q["run_ms"])/1000,
                   visible_seconds=int(q["latency_ms"])/1000, list_calls=len(lists),
                   listed_shipments=int(lists[0]["result_count"]) if len(lists) == 1 else "",
                   unique_db_targets=len({t["target"] for t in calls if t["tool"] == "get_shipment" and t["status"] == "ok"}),
                   unique_live_targets=len({t["target"] for t in live}),
                   carrier_429_attempts=sum(t["status"] == "429" for t in calls),
                   cache_source="not_hit", source_question_id="", source_user_id="", source_stop_reason="")
        row.update(sources.get(q["question_id"], {}))
        assert len(live) == int(q["carrier_calls"]), "Carrier billing mismatch"
        assert int(q["tool_calls"]) == len({(t["step"], t["tool"], t["target"]) for t in calls}), "Tool count mismatch"
        expected = int(q["tokens_in"])*2e-6 + int(q["tokens_out"])*8e-6 + len(live)*.004
        assert abs(float(q["cost_usd"]) - expected) < 1e-8, "Question tariff mismatch"
        assert row["visible_seconds"] <= GATEWAY_SECONDS, "Gateway limit mismatch"
        if row["timeout"]:
            assert row["visible_seconds"] == GATEWAY_SECONDS and row["run_seconds"] >= GATEWAY_SECONDS
        rows.append(row)
    minute_rows = [dict(minute_utc=at.isoformat(), minute_sgt=at.astimezone(SGT).isoformat(),
                        successful=c["ok"], rejected_attempts=c["429"], total_attempts=sum(c.values()))
                   for at, c in sorted(minutes.items())]
    assert all(r["successful"] <= CARRIER_LIMIT for r in minute_rows), "Carrier quota mismatch"
    assert abs(sum(float(t["cost_usd"]) for t in tools) - sum(int(q["carrier_calls"]) for q in questions)*.004) < 1e-8
    return rows, minute_rows


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def finish(fig, output, name, title, note):
    fig.suptitle(title, fontsize=20, fontweight="bold", x=.06, ha="left", y=.97)
    fig.text(.06, .025, note, fontsize=10, color="#374151", va="bottom")
    fig.subplots_adjust(top=.83, bottom=.20, left=.15 if name == "01_timeouts" else .09,
                        right=.96, wspace=.40, hspace=.60)
    for ax in fig.axes:
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#e2e6eb", linewidth=.8)
    fig.savefig(output / f"{name}.png", dpi=180, facecolor="white")
    fig.savefig(output / f"{name}.svg", facecolor="white")
    plt.close(fig)


def plot_latency(rows, output):
    lead = [q for q in rows if q["role"] == "team_lead" and q["portfolio"]]
    cold_lead = [q for q in lead if not int(q["cache_hit"])]
    groups = [("All questions", rows), ("Operators | new run", [q for q in rows if q["role"] == "operator" and not int(q["cache_hit"])]),
              ("Lead: other | new run", [q for q in rows if q["role"] == "team_lead" and not q["portfolio"] and not int(q["cache_hit"])]),
              ("Lead: my shipments | new run", cold_lead), ("Lead: my shipments | cache", [q for q in lead if int(q["cache_hit"])])]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(16, 8))
    for i, (_, group) in enumerate(groups):
        n, failures = len(group), sum(q["timeout"] for q in group)
        rate = 100*failures/n if n else 0
        ax.barh(i, rate, color=RED if i == 3 else BLUE, height=.55)
        ax.text(rate+2, i, f"{failures}/{n} = {rate:.1f}%", va="center", fontsize=11)
    ax.set_yticks(range(len(groups)), [name.replace(" | ", "\n") for name, _ in groups])
    ax.invert_yaxis()
    ax.set_xlim(0, 132)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.xaxis.set_major_formatter(PercentFormatter())
    ax.set_xlabel("Questions with HTTP 504")
    ax.set_title("Cache hits hide new-run failures", pad=14)
    for label, group, color, style in [("Lead: my shipments, new run", cold_lead, RED, "-"),
                                      ("Other new runs", [q for q in rows if not int(q["cache_hit"]) and not (q["role"] == "team_lead" and q["portfolio"])], BLUE, "-"),
                                      ("All cache hits", [q for q in rows if int(q["cache_hit"])], GREEN, "--")]:
        values = sorted(q["run_seconds"] for q in group)
        bx.step(values, [100*(i+1)/len(values) for i in range(len(values))], where="post", color=color, linestyle=style, linewidth=2.5, label=f"{label} (n={len(values)})")
    bx.axvline(GATEWAY_SECONDS, color=GREY, linestyle=":", linewidth=2)
    bx.text(30, 35, "Gateway stops\nat 29 seconds", color="#374151")
    bx.set(xlabel="Lambda run time (seconds)", ylabel="Runs completed (%)", ylim=(0, 104))
    bx.yaxis.set_major_formatter(PercentFormatter())
    bx.set_title("Work continues after the user times out", pad=14)
    bx.legend(loc="lower right", fontsize=9)
    finish(fig, output, "01_timeouts", "The overall timeout rate hides portfolio failures",
           "Portfolio = text contains 'my shipments'. New run = cache_hit 0. Groups overlap with 'All questions'.\n"
           "Run time comes from Lambda. Visible latency stops at 29 seconds. HTTP 200 and cache hits do not prove a correct answer.")


def plot_coverage(rows, output):
    eligible = [q for q in rows if q["list_calls"] == 1 and q["listed_shipments"] > 0]
    capped = [q for q in eligible if q["stop_reason"] == "step_cap"]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(15, 8))
    for label, group, color, marker in [("Reached step cap", capped, RED, "x"),
                                        ("Ended before step cap", [q for q in eligible if q["stop_reason"] != "step_cap"], BLUE, "o")]:
        ax.scatter([q["listed_shipments"] for q in group], [q["unique_live_targets"] for q in group], color=color, marker=marker, s=40, alpha=.65, label=f"{label} (n={len(group)})")
    maximum = max(q["listed_shipments"] for q in eligible)
    ax.plot([0, maximum], [0, maximum], linestyle="--", color=GREY, label="One live target per listed shipment")
    ax.set(xlabel="Shipments returned by list_shipments", ylabel="Distinct successful live targets", ylim=(-2, maximum*1.05))
    ax.set_title("Live checks cover few targets", pad=14)
    ax.legend(loc="upper left", fontsize=10)
    values = [median(q[key] for q in capped) for key in ["listed_shipments", "unique_db_targets", "unique_live_targets"]]
    bx.bar(range(3), values, color=[GREY, BLUE, RED], width=.6)
    for i, value in enumerate(values):
        bx.text(i, value+3, f"{value:g}", ha="center", fontweight="bold", fontsize=16)
    bx.set_xticks(range(3), ["Listed\nshipments", "Distinct DB\ntargets", "Distinct live\ntargets"])
    bx.set(ylabel="Median count per capped run", ylim=(0, max(values)*1.2))
    bx.set_title(f"Work stops at 25 steps (n={len(capped)})", pad=14)
    finish(fig, output, "02_shipment_checks", "The step cap prevents full portfolio checks",
           "Use runs with one successful, non-empty list call. Count distinct targets; retries do not add coverage.\n"
           "List members and answer text are absent. These counts show a coverage proxy, not measured answer accuracy.")


def plot_bursts(minutes, output):
    lookup = {timestamp(r["minute_sgt"]): r for r in minutes}
    mondays = sorted({at.date() for at in lookup if at.weekday() == 0})
    fig, axes = plt.subplots(2, 3, figsize=(16, 9), sharey=True)
    for ax, day in zip(axes.flat, mondays):
        times = [datetime.combine(day, datetime.min.time(), SGT) + timedelta(hours=8, minutes=58+i) for i in range(12)]
        ok = [lookup.get(at, {}).get("successful", 0) for at in times]
        rejected = [lookup.get(at, {}).get("rejected_attempts", 0) for at in times]
        ax.bar(range(12), ok, color=BLUE, label="Successful calls")
        ax.bar(range(12), rejected, bottom=ok, color=RED, hatch="//", label="429 attempts")
        ax.axhline(CARRIER_LIMIT, color=GREY, linestyle="--", label="60 successes/minute limit")
        ax.set_xticks([0, 3, 6, 9], [times[i].strftime("%H:%M") for i in [0, 3, 6, 9]])
        ax.set_title(f"{day:%d %b} | {sum(rejected)} rejected attempts", fontsize=12)
        ax.set_ylim(0, max(r["total_attempts"] for r in minutes)*1.15)
        ax.set_ylabel("Carrier attempts / minute")
    axes[0, 0].legend(loc="upper left", fontsize=9)
    finish(fig, output, "03_carrier_bursts", "Monday bursts exhaust the shared carrier quota",
           "Fixed window: 08:58-09:09 Singapore time (UTC+8), on all six pilot Mondays. Empty minutes have zero calls.\n"
           "429 bars count rejected attempts, including retries. They do not measure distinct requests or unconstrained demand.")


def plot_spend(rows, users, output):
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(15, 8))
    roles = ["operator", "team_lead"]
    normal = [sum(float(q["cost_usd"]) for q in rows if q["role"] == role and not q["timeout"]) for role in roles]
    failed = [sum(float(q["cost_usd"]) for q in rows if q["role"] == role and q["timeout"]) for role in roles]
    ax.bar(range(2), normal, color=BLUE, label="No HTTP 504")
    ax.bar(range(2), failed, bottom=normal, color=RED, hatch="//", label="HTTP 504")
    for i in range(2):
        ax.text(i, normal[i]+failed[i]+1.3, f"${normal[i]+failed[i]:.2f}", ha="center", fontsize=15, fontweight="bold")
    counts = Counter(u["role"] for u in users)
    ax.set_xticks(range(2), [f"Operators\n{counts['operator']} users", f"Team lead\n{counts['team_lead']} user"])
    ax.set(ylabel="Six-week model + carrier spend (USD)", ylim=(0, max(n+f for n, f in zip(normal, failed))*1.23))
    ax.yaxis.set_major_formatter(StrMethodFormatter("${x:,.0f}"))
    ax.set_title("One lead accounts for most spend", pad=14)
    ax.legend(loc="upper left")
    total = sum(float(q["cost_usd"]) for q in rows)
    shares = [100*sum(q["timeout"] for q in rows)/len(rows), 100*sum(failed)/total]
    bx.bar(range(2), shares, color=[GREY, RED], width=.55)
    for i, share in enumerate(shares):
        bx.text(i, share+2, f"{share:.1f}%", ha="center", fontsize=16, fontweight="bold")
    bx.set_xticks(range(2), ["Share of\nquestions", "Share of\nspend"])
    bx.set(ylabel="Share attributed to HTTP 504", ylim=(0, 100))
    bx.yaxis.set_major_formatter(PercentFormatter())
    bx.set_title("Timeouts consume most of the budget", pad=14)
    finish(fig, output, "04_spend", "A low mean cost hides expensive failed requests",
           f"Total: ${total:.6f}. Timed-out spend: ${sum(failed):.6f}. Includes work after the gateway returns 504.\n"
           "Model + carrier only. Rejected calls are unbilled. Role and scope overlap; one lead cannot establish a size effect.")


def plot_cache(rows, output):
    hits = [q for q in rows if int(q["cache_hit"])]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(15, 8))
    bottom = [0, 0]
    for source, label, color in [("same_user", "Same user as last inferred write", BLUE),
                                 ("different_user", "Different user from last inferred write", RED),
                                 ("unmatched", "No write matched in export", GREY)]:
        counts = [sum(q["portfolio"] == portfolio and q["cache_source"] == source for q in hits) for portfolio in [True, False]]
        ax.bar(range(2), counts, bottom=bottom, color=color, label=label, hatch="//" if source == "different_user" else None)
        for i, count in enumerate(counts):
            if count:
                ax.text(i, bottom[i]+count/2, str(count), color="white", va="center", ha="center", fontweight="bold")
        bottom = [a+b for a, b in zip(bottom, counts)]
    ax.set_xticks(range(2), ["My shipments", "Other questions"])
    ax.set(ylabel="Cache-hit questions", ylim=(0, max(bottom)*1.3))
    ax.set_title(f"Inferred source for {len(hits)} cache hits", pad=14)
    ax.legend(loc="upper right", fontsize=9)
    different = [q for q in hits if q["cache_source"] == "different_user" and q["portfolio"] and q["source_stop_reason"] == "step_cap"]
    example = min(different, key=lambda q: q["asked_at_utc"])
    source = next(q for q in rows if q["question_id"] == example["source_question_id"])
    bx.axis("off")
    bx.set_title("Example: one key, two user scopes", pad=14)
    bx.text(.02, .88, fill(example["question_text"], 42), fontsize=12, transform=bx.transAxes)
    bx.text(.02, .62, f"{source['question_id']} | {source['user_id']} ({source['role']})\nNew run reaches step cap\nWrite inferred at Lambda completion", fontsize=13, linespacing=1.7, transform=bx.transAxes,
            bbox=dict(boxstyle="round,pad=.8", facecolor="#eef3f9", edgecolor=BLUE))
    bx.annotate("Same cache key", xy=(.45, .39), xytext=(.45, .49), ha="center", xycoords="axes fraction", arrowprops=dict(arrowstyle="->", color=GREY), fontsize=11)
    bx.text(.02, .16, f"{example['question_id']} | {example['user_id']} ({example['role']})\nCache hit in {example['visible_seconds']:.3f} seconds", fontsize=13, linespacing=1.7, transform=bx.transAxes,
            bbox=dict(boxstyle="round,pad=.8", facecolor="#fbefe9", edgecolor=RED))
    finish(fig, output, "05_cache_scope", "Fast cache hits can reuse another user's result",
           "Inference: order writes by Lambda completion; match the last write within 24 hours. Exported keys have 12 characters.\n"
           "Exact write times and answer text are absent. Matches flag scope risk; they do not prove which answer a user received.")


def plot_freshness(tools, output):
    live = [t for t in tools if t["tool"] == "carrier_track" and t["status"] == "ok" and t["data_age_min"] and t["differs_from_db"] in ("0", "1")]
    bins = [(0, 60), (60, 120), (120, 180), (180, float("inf"))]
    grouped = [[t for t in live if low <= float(t["data_age_min"]) < high] for low, high in bins]
    counts = [len(group) for group in grouped]
    differences = [sum(t["differs_from_db"] == "1" for t in group) for group in grouped]
    rates = [100*d/n if n else 0 for d, n in zip(differences, counts)]
    write_csv(output / "freshness_bins.csv", [dict(age_min_inclusive=low, age_max_exclusive=high,
              live_checks=n, differs_from_db=d, difference_percent=rate)
              for (low, high), n, d, rate in zip(bins, counts, differences, rates)])
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(15, 8))
    ax.bar(range(4), rates, color=RED, width=.6)
    for i, (rate, d, n) in enumerate(zip(rates, differences, counts)):
        ax.text(i, rate+.4, f"{d}/{n}\n{rate:.1f}%", ha="center", fontsize=11)
    labels = ["0-59", "60-119", "120-179", "180+"]
    ax.set_xticks(range(4), labels)
    ax.set(xlabel="DB row age (minutes)", ylabel="Live checks that differ from DB", ylim=(0, max(rates)+3))
    ax.yaxis.set_major_formatter(PercentFormatter())
    ax.set_title("Older rows have more observed differences", pad=14)
    bx.bar(range(4), counts, color=BLUE, width=.6)
    bx.set_xticks(range(4), labels)
    bx.set(xlabel="DB row age (minutes)", ylabel="Successful live checks", ylim=(0, max(counts)*1.2))
    bx.set_title("Age groups have unequal sample sizes", pad=14)
    for i, n in enumerate(counts):
        bx.text(i, n+15, str(n), ha="center", fontsize=12)
    finish(fig, output, "06_freshness", "The four-hour feed leaves stale shipment status",
           f"Observed differences: {sum(differences)}/{sum(counts)} successful live checks ({100*sum(differences)/sum(counts):.1f}%).\n"
           "Checks are selected by the assistant and can repeat shipments. This is not a random sample or a population error rate.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path(__file__).parent / "data")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "pilot_outputs")
    args = parser.parse_args()
    questions, tools, users = [read(args.data / name) for name in ["pilot_questions.csv", "pilot_tool_calls.csv", "pilot_users.csv"]]
    rows, minutes = build_evidence(questions, tools, users)
    args.output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 12, "font.family": "DejaVu Sans", "text.parse_math": False,
                         "axes.spines.top": False, "axes.spines.right": False})
    write_csv(args.output / "question_evidence.csv", rows)
    write_csv(args.output / "carrier_minutes.csv", minutes)
    write_csv(args.output / "cache_hits.csv", [q for q in rows if int(q["cache_hit"])])
    plot_latency(rows, args.output)
    plot_coverage(rows, args.output)
    plot_bursts(minutes, args.output)
    plot_spend(rows, users, args.output)
    plot_cache(rows, args.output)
    plot_freshness(tools, args.output)
    total = round(sum(float(q["cost_usd"]) for q in rows), 6)
    cold_lead = [q for q in rows if q["role"] == "team_lead" and q["portfolio"] and not int(q["cache_hit"])]
    metrics = dict(questions=len(rows), timeouts=sum(q["timeout"] for q in rows),
                   cold_lead_portfolio_questions=len(cold_lead), cold_lead_portfolio_timeouts=sum(q["timeout"] for q in cold_lead),
                   cold_lead_portfolio_median_run_seconds=median(q["run_seconds"] for q in cold_lead),
                   step_cap_runs=sum(q["stop_reason"] == "step_cap" for q in rows), spend_usd=total,
                   timeout_spend_usd=round(sum(float(q["cost_usd"]) for q in rows if q["timeout"]), 6),
                   carrier_429_attempts=sum(r["rejected_attempts"] for r in minutes),
                   minutes_at_carrier_limit=sum(r["successful"] == CARRIER_LIMIT for r in minutes),
                   inferred_cross_user_hits=sum(q["cache_source"] == "different_user" for q in rows),
                   inferred_cross_user_portfolio_hits=sum(q["cache_source"] == "different_user" and q["portfolio"] for q in rows))
    capped = [q for q in rows if q["stop_reason"] == "step_cap" and q["list_calls"] == 1 and q["listed_shipments"] > 0]
    live = [t for t in tools if t["tool"] == "carrier_track" and t["status"] == "ok"]
    metrics.update(capped_median_listed=median(q["listed_shipments"] for q in capped),
                   capped_median_live_targets=median(q["unique_live_targets"] for q in capped),
                   live_checks=len(live), live_checks_different_from_db=sum(t["differs_from_db"] == "1" for t in live))
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2)+"\n", encoding="utf-8")
    report = f"""# Pilot issue analysis

The six-week pilot contains {len(rows):,} questions. It has one team lead and 39 operators.
The overall timeout rate is {100*metrics['timeouts']/len(rows):.1f}%. The mean question cost is ${total/len(rows):.4f}.
These means hide the failures below. These charts show observed pilot work. They do not project capacity at fifty customers.

| Issue | Evidence | Interpretation |
|---|---|---|
| Timeouts | {metrics['cold_lead_portfolio_timeouts']}/{len(cold_lead)} new lead portfolio runs time out ({100*metrics['cold_lead_portfolio_timeouts']/len(cold_lead):.1f}%). Median run time: {metrics['cold_lead_portfolio_median_run_seconds']:.1f} seconds. | The 29-second gateway deadline is shorter than most of these runs. Cache hits hide this failure. |
| Shipment checks | {metrics['step_cap_runs']} runs reach the step cap. These runs list a median of {metrics['capped_median_listed']:g} shipments and check {metrics['capped_median_live_targets']:g} distinct live targets. | The loop stops before it checks the full list. Counts are a coverage proxy. |
| Carrier quota | {metrics['carrier_429_attempts']} rejected attempts. {metrics['minutes_at_carrier_limit']} calendar minutes reach 60 successes. | Monday bursts already exhaust the shared quota. |
| Spend | Timeouts cost ${metrics['timeout_spend_usd']:.2f} of ${total:.2f} ({100*metrics['timeout_spend_usd']/total:.1f}%). | Failed requests consume most spend. Lambda work continues after the user times out. |
| Cache scope | {metrics['inferred_cross_user_hits']} hits follow an inferred write by another user. {metrics['inferred_cross_user_portfolio_hits']} concern 'my shipments'. | The question-only key can reuse an answer across user scopes. This is an inference, not proven disclosure. |
| Freshness | {metrics['live_checks_different_from_db']}/{len(live)} successful live checks differ from the DB ({100*metrics['live_checks_different_from_db']/len(live):.1f}%). | Some DB status is stale. These checks are selected and can repeat shipments. |

"""
    report += "\n\n".join(f"![{name.replace('_', ' ')}]({name}.png)" for name in ["01_timeouts", "02_shipment_checks", "03_carrier_bursts", "04_spend", "05_cache_scope", "06_freshness"])
    report += """

## Method and limits

- Join users by `user_id`. Join tool calls by `question_id`.
- Define portfolio questions by the phrase `my shipments`. This rule can miss other portfolio questions.
- Use `run_ms` for Lambda work. Visible latency stops at 29 seconds. Keep work after HTTP 504 in spend totals.
- Count distinct successful live targets for coverage. List members and answer text are absent. Coverage is a proxy. Answer accuracy is not measured.
- Count all carrier attempts by UTC calendar minute. Rejected attempts include retries. They are unbilled. The minute CSV contains occupied minutes. The Monday charts add zeros for empty minutes in the fixed window.
- Infer writes at Lambda completion. Assume completed new runs write their result, as the handler shows. Match the last write within 24 hours. Exact write times and full keys are absent. Matches flag scope risk, not proven answer disclosure.
- Live checks can repeat shipments. The assistant selects these checks. Do not apply the observed difference rate to all shipments.
- The pilot has one lead. Role and scope overlap. These observations do not prove a cause or predict all future leads.
- Check tool counts, token tariffs, carrier billing, and timeout limits on every run. Run `uv run --locked test_pilot_analysis.py` for small input checks.

Run `uv run --locked analyze_pilot.py` to reproduce the outputs. Use `--data` and `--output` to select folders. Each run replaces the named output files. PNG files provide previews. SVG files preserve text and lines for export. CSV files contain chart evidence. `metrics.json` contains the main totals.
"""
    (args.output / "results.md").write_text(report, encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"Checks passed. Six charts and evidence saved to {args.output.resolve()}")


if __name__ == "__main__":
    main()
