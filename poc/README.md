# The POC

Simplified for the exercise, so it's written to be read, not run. `llm`, `vectordb` and `logs`
stand in for a vendor SDK, a vector DB client and a logging helper.

```
 operator ──> API Gateway ──> Lambda: handler.py ──> LLM (tool use)
                                   │
          ┌───────────────┬────────┴─────────┬──────────────────┐
     RDS Postgres     carrier tracking    vector DB          answer_cache
     shipments,       API (live)          one index over     (a table in
     events, users    tools.py            documents in S3    the same RDS)
          ▲
   ingest job, every 4 hours: carrier bulk feed → shipments, events
```

| | |
|---|---|
| `handler.py` | cache lookup, the agent loop, cache write |
| `tools.py` | the four tools the model can call |
| `prompt.md` | the system prompt |
| `schema.sql` | the Postgres tables |

The user's id comes from the API Gateway authorizer. The web client doesn't block: a user can send
another question while one is still running. Every question and tool call is logged; the
exports are in `data/`, and `data/README.md` says what each column means.
