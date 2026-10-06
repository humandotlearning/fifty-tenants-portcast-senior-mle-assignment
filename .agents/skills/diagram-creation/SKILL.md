---
name: diagram-creation
description: Create or update system architecture diagrams for a senior software architecture review. Use C4 Container diagrams by default. Keep Mermaid source editable, use precise SVG and high-resolution PNG when needed, and verify the rendered layout. Freight-specific rules apply only to the named project reference.
---

# Diagram Creation

Apply these rules when creating or updating a system architecture diagram.
Produce a polished diagram for a senior software architecture review.
Prioritize readability and visual hierarchy over a compact canvas.

## Project scope

For the `fifty-tenants-portcast-senior-mle-assignment` repository, read
[the freight project reference](references/freight-operations-assistant.md).
Apply that reference in its saved checkout and worktrees.
The reference defines the freight lanes, boundary, annotations, and visual paths.
Do not add those components or use those paths for unrelated projects.
For other projects, use their current code, documentation, and stated scope.

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

Put the primary request path left to right. Put people on the far left.
Place synchronous external calls on the right and persistent data below.
Keep background work and logs in separate areas when present.

- Use a **16:9 landscape canvas**, centered vertically and horizontally, with
  no large empty header region.
- Use a consistent grid. Keep at least **60 px horizontal spacing** between
  containers, **70 px vertical spacing** between rows, and **40 px padding**
  inside the system boundary. Measurements refer to the final diagram canvas.
- Give containers in the same logical layer equal heights where practical.
- Adapt component names and lanes to the architecture being diagrammed while
  preserving this hierarchy. Do not add components solely to fill the layout.
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

Put verified limits and schedules in small, readable secondary annotations.
Check each value against the current source before adding it.

## Colour and system boundary

Make the system boundary clearly visible but visually secondary.
Do not use an extremely faint dashed border.
Use a boundary name that matches the current diagram scope.

- Use a light or very dark neutral background with WCAG-like high contrast.
  On dark backgrounds, use near-white text rather than grey-on-grey.
- Use no more than **four semantic colour families**: one consistent blue
  family for internal applications; a second subtle family for datastores;
  neutral grey for external systems/people; and a muted third family for
  background processing and observability.
- Pair colour with shapes, stereotypes, labels, or line styles so meaning does
  not depend on colour alone.
- Do not use transparency for important text, borders, or relationship labels.
- Put its title in the upper-left with enough padding that no connector crosses
  it. Update the boundary name when the diagram's scope changes.

## Deliver and verify

- Use Mermaid `C4Container` for editable Mermaid source. When its automatic
  layout cannot meet these rules, provide a precisely laid-out SVG plus a
  high-resolution PNG preview; retain Mermaid source for the C4 structure.
  Clearly state which artifact preserves the exact review layout.
- Render and visually inspect the final diagram at full-canvas and normal
  screen size. Fix crossings, clipped text, insufficient contrast, label
  collisions, and spacing problems before delivering it.
- Deliver a clean architecture-review diagram, not a dense autogenerated
  dependency graph. Avoid unnecessary dependencies or unrelated code changes.
