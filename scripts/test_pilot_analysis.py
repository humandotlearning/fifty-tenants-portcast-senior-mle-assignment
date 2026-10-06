"""Check cache ordering, expiry, and retry accounting without a test framework."""
from analyze_pilot import build_evidence, cache_sources


def question(qid, at, user="U1", hit=0, run=1000):
    return dict(question_id=qid, asked_at_utc=f"2026-08-{at}", user_id=user,
                question_text="Which of my shipments are late?", cache_key="key",
                cache_hit=str(hit), run_ms=str(run), latency_ms=str(min(run, 29000)),
                http_status="504" if run > 29000 else "200", stop_reason="cache" if hit else "answered",
                tokens_in="0", tokens_out="0", carrier_calls="0", tool_calls="0", cost_usd="0")


def main():
    # The first run starts earlier but writes after the second run.
    rows = [question("Q1", "10T00:00:00Z", run=40000),
            question("Q2", "10T00:00:05Z", user="U2"),
            question("Q3", "10T00:00:10Z", user="U3", hit=1),
            question("Q4", "10T00:00:45Z", user="U1", hit=1),
            question("Q5", "11T00:00:40Z", hit=1),
            question("Q6", "10T00:00:01Z", hit=1)]
    sources = cache_sources(rows)
    assert sources["Q3"]["source_question_id"] == "Q2"
    assert sources["Q3"]["cache_source"] == "different_user"
    assert sources["Q4"]["source_question_id"] == "Q1"
    assert sources["Q4"]["cache_source"] == "same_user"
    assert sources["Q5"]["cache_source"] == "unmatched", "TTL excludes exactly 24 hours"
    assert sources["Q6"]["cache_source"] == "unmatched", "Do not match future writes"
    q = question("Q7", "10T01:00:00Z")
    q.update(carrier_calls="1", tool_calls="1", cost_usd="0.004")
    tools = [dict(question_id="Q7", tool="carrier_track", target="C1", step="1", attempt=str(i),
                  called_at_utc=f"2026-08-10T01:00:0{i}Z", status=status,
                  cost_usd="0.004" if status == "ok" else "0")
             for i, status in enumerate(["429", "429", "ok"], 1)]
    evidence, minutes = build_evidence([q], tools, [dict(user_id="U1", role="team_lead")])
    assert evidence[0]["unique_live_targets"] == 1 and evidence[0]["carrier_429_attempts"] == 2
    assert minutes[0]["total_attempts"] == 3 and minutes[0]["successful"] == 1
    # Another successful check of the same target adds spend but not coverage.
    tools.append(dict(tools[-1], step="2", attempt="1", called_at_utc="2026-08-10T01:01:00Z"))
    q.update(carrier_calls="2", tool_calls="2", cost_usd="0.008")
    evidence, minutes = build_evidence([q], tools, [dict(user_id="U1", role="team_lead")])
    assert evidence[0]["unique_live_targets"] == 1
    assert len(minutes) == 2 and sum(r["successful"] for r in minutes) == 2
    print("Checks passed: cache completion order, scope, expiry, future writes, and carrier retries.")


if __name__ == "__main__":
    main()
