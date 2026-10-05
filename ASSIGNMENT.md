# Senior MLE take-home: from one customer to fifty

**4 hours. Please don't go over.** There's more here than fits in four hours, on purpose. Pick what
you think matters most, work on that, and when the time's up send what you have, with a line on
what you left out. We'd rather see what you prioritise in four hours than what you produce in
twelve. AI tools are fine; use whatever you normally use.

## The scenario

*This is a made-up scenario. The company, customers, code and data are invented for this exercise.*

A freight-tech company has built an AI assistant for the operations teams at freight forwarders.
Operators type questions like "where is ZNTU9304748?", "which of my shipments are late?" or "what
does the BL for BK232180 say about the consignee?", and an LLM answers using four tools over the
customer's data.

It was built in three weeks as a proof of concept, for one customer: 40 users (39 operators and a
team lead) and about 300 active shipments. The stack is simple:
- API Gateway in front of one Lambda
- Postgres on RDS with the customer's shipments, refreshed from the carrier feed every four hours
- documents in S3, searchable through a vector DB
- a live carrier-tracking API
- an answer cache in Postgres

Everything is single-tenant.

After a six-week pilot:
- The customer likes it, and the team lead uses it for everything.
- There were nearly 2,000 questions, at under 3 cents each on average.
- Users say it's sometimes slow and some questions time out, "but if you ask again it's instant".
  The team thinks a faster model would fix that.

It's now the end of September 2026. Sales expects **fifty customers within a year**, and the first
new ones go live in the next few months. The team's estimate is that fifty customers is fifty times
the pilot: about $2,000 a month in model and carrier spend, against about $45,000 a month in
revenue. So nobody is worried about cost, and nobody has thought about scale.

**You've just joined, and this is now yours. What does it take to get to fifty?**

## What's in the folder

| | |
|---|---|
| `poc/` | the POC code: handler, tools, prompt, schema. Simplified for the exercise, so it's for reading, not running |
| `data/pilot_questions.csv` | every question in the pilot: who asked, when, what it cost, how long it took, how it ended |
| `data/pilot_tool_calls.csv` | every tool call those questions made |
| `data/pilot_users.csv` | the pilot's users |
| `data/tenants.csv` | the fifty customers sales expects, including the pilot, with go-live dates |
| `data/pilot_feedback.md` | what pilot users said in week five |
| `data/README.md` | what each column means |
| `costs-and-limits.md` | the prices and limits to assume |

## What to send back

Send whatever you have at the four-hour mark. Unfinished is fine; tell us what you'd do next.

**1. Your thinking (max 3 pages).** Cover what matters most; a bullet can be one line, or left out.
- What the system looks like at fifty customers: what you'd change from the POC, and what you'd keep.
- What breaks first, and roughly when. Back it with the pilot data.
- What decides what: what the model does, what code does, and what the assistant may do on its own.
- What it costs per customer and per seat, against the price. Show your arithmetic, and correct the
  team's estimate if it's wrong.
- The order you'd do it in: what has to be true before the next customer goes live, and what can wait.

**2. Something running (about a quarter of your time).** Build whatever settles a question you
couldn't settle by reasoning: for example a cost or capacity model from the logs, a replay of the
pilot at fifty customers, or one piece of the POC rewritten with tests. Tell us why you picked it.

**3. A short note (max 1 page).**
- The decision you were least sure about, and what would change your mind.
- One place an AI tool was confidently wrong while you worked, and how you caught it. Skip this if
  you didn't use one.

## Ground rules
- The scenario is incomplete on purpose. Where you need a fact we haven't given you, write down your
  assumption and keep going.
- Use any format that opens easily.
- We're assessing judgment, not volume or polish: what you noticed, what you decided, and whether
  your numbers come from the evidence.
- Afterwards we'll have a ~45-minute call to go through it together. Have your work open; we may
  ask you to change an assumption and re-run something. Please keep AI tools closed during the
  call. Expect pushback.
