# Freight Operations Assistant project reference

## Scope

Apply this reference only to `fifty-tenants-portcast-senior-mle-assignment`.
This includes its saved checkout and worktrees.
The saved checkout is:
`C:/Users/nithi/Downloads/Compressed/fifty-tenants-portcast-senior-mle-assignment/fifty-tenants-portcast-senior-mle-assignment`.

Use this hierarchy for the Freight Operations Assistant architecture.
Check components and relationships against the current repository source.
Adapt names and lanes to the diagram scope. Do not invent components.
Keep proposed and implemented architecture distinct.
Resolve the visual paths below from the current repository root.

## Freight lanes and visual hierarchy

- Put the Operator/User on the far left. Arrange the primary request path
  left to right inside the system boundary:
  **Web Client → API Gateway → Operations Assistant / Lambda**.
- Put synchronous external dependencies, **LLM Vendor** and **Carrier Tracking
  API**, in a vertical column on the right, outside the system boundary.
- Separate the persistent **Data layer** along the bottom: **RDS/Postgres,
  S3 Document Storage, Vector DB**.
- Put **Carrier Bulk Feed → Shipment Ingest Job** in a separate lower
  background-processing lane, with the external feed outside the boundary.
- Put **CloudWatch Logs** in a separate observability area at the bottom-right.
- The eye must first follow **Operator → Web Client → API Gateway → Operations
  Assistant**, then notice dependencies, data, ingestion, retrieval, and logs.

## Freight annotations

- Put values such as the **29-second gateway timeout**, **90-second Lambda
  timeout**, **60 requests/minute**, **24-hour cache TTL**, and **every 4 hours**
  into small, readable secondary annotations where relevant. Verify values
  against the current source before including them.

## Freight system boundary

- Make the **Freight Operations Assistant — Single Customer** boundary clearly
  visible but visually secondary. Do not use an extremely faint dashed border.

## Existing visual reference

- Use `docs/architecture/architecture-review.svg` and `docs/architecture/architecture-review.png` as the
  existing visual reference, not as evidence that architectural facts are current.
