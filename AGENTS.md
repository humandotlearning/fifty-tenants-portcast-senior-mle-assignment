# Repository instructions

## Explanations and documentation

- Whenever explaining something or writing or updating documentation, use
  **ASD-STE100 (Simplified Technical English) style**. This applies to chat
  explanations, comments, README files, architecture notes, and diagram text.
- Use short, clear sentences and simple words. Use active voice where possible.
- Give each sentence one main idea. Keep each paragraph on one topic.
- Use consistent terms. Use the same word for the same concept throughout.
- Give instructions as direct commands. Separate steps and state conditions
  clearly before the actions that depend on them.
- Avoid idioms, unnecessary jargon, ambiguous pronouns, and long noun groups.
- Preserve technical accuracy, necessary technical names, code identifiers,
  commands, and quoted source text. Explain unfamiliar technical terms briefly.
- Treat this as a writing-style requirement. Do not claim formal ASD-STE100
  compliance unless the text has been checked against the standard.

## System architecture diagrams

These instructions apply whenever creating or updating a system architecture
diagram in this repository. Produce a polished diagram suitable for a senior
software architecture review. Prioritize readability and visual hierarchy over
fitting every detail into one compact canvas.

## Use C4

- Use C4 notation. Default to a **C4 Container diagram** unless another C4 level
  is explicitly requested.
- Distinguish people, internal application containers, datastores, and external
  systems. Keep stereotypes such as `Person`, `Container`, `Database`,
  `Datastore`, and `External System` subtle but readable.
- Make component names the strongest text in each box. Technology names are
  secondary; descriptions explain the component's responsibility.
- Show independently running/deployed components at container level. Keep
  functions, tools, prompts, and agent-loop steps inside their owning container
  rather than drawing them as separate containers.
- Ground current-state diagrams in the repository's code and documentation.
  Distinguish proposed architecture from implemented architecture, and label
  unspecified pipelines or assumptions instead of inventing implementation.

## Layout and visual hierarchy

- Use a **16:9 landscape canvas**, centered vertically and horizontally, with
  no large empty header region.
- Use a consistent grid. Keep at least **60 px horizontal spacing** between
  containers, **70 px vertical spacing** between rows, and **40 px padding**
  inside the system boundary. Measurements refer to the final diagram canvas.
- Give containers in the same logical layer equal heights where practical.
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
- Adapt component names and lanes to the architecture being diagrammed while
  preserving this hierarchy. Do not add components solely to fill the layout.
- The eye must first follow **Operator → Web Client → API Gateway → Operations
  Assistant**, then notice dependencies, data, ingestion, retrieval, and logs.
- Make the diagram understandable in **5–10 seconds** at first glance, with
  secondary details discoverable on closer inspection.

## Connections

- **Minimizing edge crossings is the highest-priority layout rule.** Reposition
  nodes and reroute connections before accepting a crossing.
- Prefer orthogonal **90° connectors** over long diagonal lines.
- Use **prominent solid arrows** for the primary request path and synchronous
  calls, **normal solid arrows** for data/service dependencies, and **dashed
  arrows** for logging, indexing, ingestion, and background flows.
- Make the primary request path visually stronger than secondary relationships.
- Keep each relationship label close to its corresponding line. Give labels
  a **solid, opaque background** so connectors never pass visually through text.
- Do not allow nodes, arrows, labels, or boundary titles to overlap. Do not
  route connectors through unrelated nodes, labels, or the boundary title.
- Include a concise legend for relationship styles when needed.

## Typography and information density

- Keep all labels readable at normal screen size. Use these canvas-equivalent
  font sizes: diagram title **28–32 px**; system boundary title **20–22 px**;
  container names **18–20 px, bold**; technology/type labels **14–16 px**;
  descriptions and relationship labels **at least 14 px**.
- **Never shrink text to make the diagram fit.** Shorten descriptions, wrap
  names, or give the layout more room instead.
- Limit each container description to **1–2 short lines**.
- Keep only architecture-significant details in the main diagram. Keep
  implementation details out of component titles.
- Put values such as the **29-second gateway timeout**, **90-second Lambda
  timeout**, **60 requests/minute**, **24-hour cache TTL**, and **every 4 hours**
  into small, readable secondary annotations where relevant. Verify values
  against the current source before including them.

## Colour and system boundary

- Use a light or very dark neutral background with WCAG-like high contrast.
  On dark backgrounds, use near-white text rather than grey-on-grey.
- Use no more than **four semantic colour families**: one consistent blue
  family for internal applications; a second subtle family for datastores;
  neutral grey for external systems/people; and a muted third family for
  background processing and observability.
- Pair colour with shapes, stereotypes, labels, or line styles so meaning does
  not depend on colour alone.
- Do not use transparency for important text, borders, or relationship labels.
- Make the **Freight Operations Assistant — Single Customer** boundary clearly
  visible but visually secondary. Do not use an extremely faint dashed border.
- Put its title in the upper-left with enough padding that no connector crosses
  it. Update the boundary name when the diagram's scope changes.

## Deliver and verify

- Use Mermaid `C4Container` for editable Mermaid source. When its automatic
  layout cannot meet these rules, provide a precisely laid-out SVG plus a
  high-resolution PNG preview; retain Mermaid source for the C4 structure.
  Clearly state which artifact preserves the exact review layout.
- Use `poc/architecture-review.svg` and `poc/architecture-review.png` as the
  existing visual reference, not as evidence that architectural facts are current.
- Render and visually inspect the final diagram at full-canvas and normal
  screen size. Fix crossings, clipped text, insufficient contrast, label
  collisions, and spacing problems before delivering it.
- Deliver a clean architecture-review diagram, not a dense autogenerated
  dependency graph. Avoid unnecessary dependencies or unrelated code changes.
