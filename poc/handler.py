"""Lambda entry point for the ops assistant. POC: one customer."""
import hashlib
import json
import os
import re
import time

import psycopg2

from llm import client  # thin wrapper around the vendor SDK
from logs import log_question
from tools import TOOLS, run_tool

MODEL = os.environ.get("MODEL", "m-large")
MAX_STEPS = 25
CACHE_TTL_HOURS = 24

with open(os.path.join(os.path.dirname(__file__), "prompt.md")) as f:
    SYSTEM_PROMPT = f.read()


def _db():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def cache_key(question):
    q = re.sub(r"[^a-z0-9 ]", "", question.lower())
    return hashlib.sha1(re.sub(r"\s+", " ", q).strip().encode()).hexdigest()


def cache_get(key):
    with _db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT answer FROM answer_cache WHERE key = %s AND created_at > now() - make_interval(hours => %s)",
            (key, CACHE_TTL_HOURS),
        )
        row = cur.fetchone()
        return row[0] if row else None


def cache_put(key, answer):
    with _db() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO answer_cache (key, answer, created_at) VALUES (%s, %s, now()) "
            "ON CONFLICT (key) DO UPDATE SET answer = EXCLUDED.answer, created_at = now()",
            (key, answer),
        )


def handler(event, context):
    started = time.time()
    question = json.loads(event["body"])["question"]
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]

    key = cache_key(question)
    cached = cache_get(key)
    if cached:
        log_question(user_id, question, key, cache_hit=True, started=started)
        return {"statusCode": 200, "body": json.dumps({"answer": cached})}

    system = SYSTEM_PROMPT.format(user_id=user_id, today=time.strftime("%Y-%m-%d"))
    messages = [{"role": "user", "content": question}]
    stop_reason = "answered"
    for step in range(MAX_STEPS):
        reply = client.messages(model=MODEL, system=system, tools=TOOLS, messages=messages)
        messages.append({"role": "assistant", "content": reply.content})
        if reply.stop_reason != "tool_use":
            break
        results = [run_tool(call, user_id=user_id, step=step + 1) for call in reply.tool_calls]
        messages.append({"role": "user", "content": results})
    else:
        stop_reason = "step_cap"
        messages.append({"role": "user", "content": "Answer now with what you have."})
        reply = client.messages(model=MODEL, system=system, messages=messages)

    answer = reply.text
    cache_put(key, answer)
    log_question(user_id, question, key, cache_hit=False, started=started, stop_reason=stop_reason,
                 usage=client.usage_since(started))
    return {"statusCode": 200, "body": json.dumps({"answer": answer})}
