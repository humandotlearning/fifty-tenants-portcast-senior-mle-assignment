"""Tools the assistant can call. POC: one customer, one database, one index."""
import os
import time

import psycopg2
import requests

from logs import log_tool_call
from vectordb import index  # vendor client

CARRIER_API = "https://api.tracking-vendor.example/v2/track"

TOOLS = [
    {"name": "get_shipment",
     "description": "Get one shipment by container number or booking reference: status, last event, "
                    "vessel, ports, planned and estimated arrival, customs hold.",
     "input_schema": {"type": "object", "properties": {"ref": {"type": "string"}}, "required": ["ref"]}},
    {"name": "list_shipments",
     "description": "List the container numbers of the user's shipments. Optional status filter: at_origin, "
                    "in_transit, arrived.",
     "input_schema": {"type": "object", "properties": {"status": {"type": "string"}}}},
    {"name": "carrier_track",
     "description": "Get the live status of a container straight from the carrier.",
     "input_schema": {"type": "object", "properties": {"container_no": {"type": "string"}},
                      "required": ["container_no"]}},
    {"name": "search_docs",
     "description": "Search the customer's documents (BLs, invoices, packing lists). Returns the three "
                    "most relevant passages.",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
]


def _conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def get_shipment(ref, user_id):
    cur = _conn().cursor()
    cur.execute("SELECT * FROM shipments WHERE container_no = %s OR booking_ref = %s", (ref, ref))
    row = cur.fetchone()
    if not row:
        return {"error": f"no shipment {ref}"}
    return dict(zip([c.name for c in cur.description], row))


def list_shipments(user_id, status=None):
    cur = _conn().cursor()
    cur.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
    role = cur.fetchone()[0]
    sql, args = "SELECT container_no FROM shipments WHERE true", []
    if role != "team_lead":  # team leads see the whole desk
        sql, args = sql + " AND owner_id = %s", args + [user_id]
    if status:
        sql, args = sql + " AND status = %s", args + [status]
    cur.execute(sql, args)
    return [r[0] for r in cur.fetchall()]


def carrier_track(container_no, user_id):
    for attempt in range(3):
        r = requests.get(CARRIER_API, params={"container": container_no},
                         headers={"X-Api-Key": os.environ["CARRIER_API_KEY"]}, timeout=10)
        if r.status_code == 429:
            time.sleep(0.3)
            continue
        return r.json()
    return {"error": "rate limited"}


def search_docs(query, user_id):
    return [hit.text for hit in index.query(text=query, top_k=3)]


def run_tool(call, user_id, step):
    fn = {"get_shipment": get_shipment, "list_shipments": list_shipments,
          "carrier_track": carrier_track, "search_docs": search_docs}[call.name]
    started = time.time()
    result = fn(**call.input, user_id=user_id)
    log_tool_call(call, result, step=step, started=started)
    return {"type": "tool_result", "tool_use_id": call.id, "content": result}
