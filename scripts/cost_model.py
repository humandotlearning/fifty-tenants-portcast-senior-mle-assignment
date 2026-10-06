"""Four-group least-squares cost fit and fifty-tenant projection; standard library only."""
import argparse
import csv
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean


def read(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def fit(rows, detailed=True):
    groups = defaultdict(list)
    for q in rows:
        groups[(q["role"], q["portfolio"]) if detailed else q["role"]].append(float(q["cost_usd"]))
    return {key: mean(values) for key, values in groups.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent.parent / "model_outputs")
    parser.add_argument("--lead-frequency", type=float, default=1, help="Relative to the single pilot lead")
    args = parser.parse_args()
    if args.lead_frequency < 0:
        parser.error("Lead frequency must be nonnegative")
    questions = read(args.data / "pilot_questions.csv")
    tools = read(args.data / "pilot_tool_calls.csv")
    users = {u["user_id"]: u for u in read(args.data / "pilot_users.csv")}
    tenants = read(args.data / "tenants.csv")
    for q in questions:
        q["role"] = users[q["user_id"]]["role"]
        q["portfolio"] = "my shipments" in q["question_text"].lower()
        q["at"] = datetime.fromisoformat(q["asked_at_utc"].replace("Z", "+00:00"))
    start = min(q["at"] for q in questions).replace(hour=0, minute=0, second=0, microsecond=0)
    assert all(start <= q["at"] < start + timedelta(days=42) for q in questions)
    train = [q for q in questions if q["at"] < start + timedelta(days=28)]
    test = [q for q in questions if q["at"] >= start + timedelta(days=28)]
    fitted, baseline = fit(train), fit(train, detailed=False)
    for name, model, detailed in [("Four-group fit", fitted, True), ("Role-only baseline", baseline, False)]:
        errors = [model[(q["role"], q["portfolio"]) if detailed else q["role"]] - float(q["cost_usd"]) for q in test]
        print(f"{name}: held-out MAE ${mean(abs(e) for e in errors):.6f}; RMSE ${mean(e*e for e in errors)**.5:.6f}")
    full_fit = fit(questions)
    pilot = sum(float(q["cost_usd"]) for q in questions)
    token_cost = sum(int(q["tokens_in"])*2e-6 + int(q["tokens_out"])*8e-6 for q in questions)
    carrier = sum(int(q["carrier_calls"]) for q in questions)
    assert carrier == sum(t["tool"] == "carrier_track" and t["status"] == "ok" for t in tools)
    assert abs(pilot - token_cost - carrier*.004) < 1e-8
    assert abs(sum(float(t["cost_usd"]) for t in tools) - carrier*.004) < 1e-8
    role_cost = {role: sum(full_fit[(q["role"], q["portfolio"])] for q in questions if q["role"] == role)
                 / sum(u["role"] == role for u in users.values()) * 30/42 for role in ["operator", "team_lead"]}
    assert abs(sum(role_cost[u["role"]] for u in users.values()) - pilot*30/42) < 1e-8
    projected = []
    for t in tenants:
        seats, leads, rate = int(t["seats"]), int(t["teams"]), float(t["price_per_seat_usd"])
        assert 0 < leads < seats
        assert rate == (6 if seats > 300 else 7 if seats > 150 else 10)
        cost = (seats-leads)*role_cost["operator"] + leads*args.lead_frequency*role_cost["team_lead"]
        projected.append({"tenant_id": t["tenant_id"], "seats": seats, "leads": leads, "cost_usd_month": cost,
                          "revenue_usd_month": seats*rate, "cost_usd_seat": cost/seats,
                          "model_carrier_margin_pct": 100*(seats*rate-cost)/(seats*rate)})
    spend = sum(t["cost_usd_month"] for t in projected)
    revenue = sum(t["revenue_usd_month"] for t in projected)
    print(f"Pilot: {len(questions)} questions; {len(train)}/{len(test)} train/test; ${pilot:.6f} = tokens ${token_cost:.6f} + carrier ${carrier*.004:.6f}")
    print(f"Cache hits {sum(int(q['cache_hit']) for q in questions)}; 504s {sum(q['http_status']=='504' for q in questions)}; timed-out spend ${sum(float(q['cost_usd']) for q in questions if q['http_status']=='504'):.6f}")
    print(f"Monthly cost/operator ${role_cost['operator']:.6f}; cost/lead ${role_cost['team_lead']:.6f}; lead frequency {args.lead_frequency:g}")
    for key, cost in sorted(full_fit.items()):
        print(f"Fitted role={key[0]}, portfolio={key[1]}: ${cost:.6f}/question")
    print(f"All-live tenants {len(tenants)}; seats {sum(t['seats'] for t in projected)}; leads {sum(t['leads'] for t in projected)}")
    print(f"Pilot/month ${pilot*30/42:.2f}; 50x ${50*pilot*30/42:.2f}; projected ${spend:.2f}; ratio {spend/(50*pilot*30/42):.4f}x")
    print(f"Revenue ${revenue:.2f}; model/carrier margin {100*(revenue-spend)/revenue:.2f}%")
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "tenant_costs.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(projected[0]))
        writer.writeheader()
        writer.writerows(projected)
    print(f"Checks passed; tenant breakdown: {(args.output / 'tenant_costs.csv').resolve()}")


if __name__ == "__main__":
    main()
