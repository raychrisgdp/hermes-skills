---
name: gdp-labs-diagram
description: Generate architecture and process diagrams using the GDP Labs visual style guide. Supports both HTML/SVG (presentation-grade) and Mermaid (source-editable) formats. Based on the GDP Labs Diagram Color Guide.
version: 1.1
author: GDP Labs
license: proprietary
dependencies: []
metadata:
  tags: [architecture, diagrams, SVG, HTML, mermaid, visualization, gdp-labs]
---

# GDP Labs Diagram Skill

Generate diagrams in the GDP Labs visual style. Two output formats:

- **HTML/SVG** — for presentation-grade diagrams that need precise layout, straight arrows, and PNG export for docs
- **Mermaid** — for source-editable diagrams in markdown (sequences, ERDs, simple flowcharts)

Both formats use the same color system, connector rules, and typography from the GDP Labs Diagram Color Guide.

## Templates

- `templates/sample-agent-workflow.html` — Full SVG sample from the PDF, demonstrating all color overrides
- `templates/sample-agent-workflow.md` — Same sample as Mermaid with classDef mappings

---

# Color System

Based on the GDP Labs Diagram Color Guide.

## Process/Flowchart Nodes — Solid Fills

Use Sky Blue `#00A0DF` as the default fill for ALL nodes. Text is White `#FFFFFF`.

Override only when one of these applies:

| Question | Fill | Text Color | Why |
| :--- | :--- | :--- | :--- |
| START or END terminal? | Navy Dark `#1A3F6F` | White | Entry/exit — use oval shape |
| Human review or gate? | Charcoal `#1A202C` | White | Must never look automated |
| Error or rejection path? | Pink `#CA54B0` | White | Immediate "something wrong" signal |
| Key CTA (max 1–2 per diagram)? | Navy `#306FB7` | White | Eye-drawing emphasis |
| Inactive / future / disabled? | Light Gray `#E8EEF4` | Charcoal `#1A202C` | Recedes visually |

**Default rule:** If none of the overrides apply, use Sky Blue. No further thinking required.

## Architecture Diagrams — 5-Group System

For architecture/block diagrams where semantic grouping matters:

| Group | Fill | Border | Meaning |
| :--- | :--- | :--- | :--- |
| Blue | `#E8F5FB` | `#00A0DF` | Primary active components |
| Green | `#EAF2EA` | `#4CAF7D` | Product boundaries (container fill) |
| Amber | `#FFF3E0` | `#F5A623` | Surface / helper steps |
| Purple | `#F0EBF9` | `#7C4DCC` | Supporting / integration |
| Rose | `#FFE9EE` | `#E05C7A` | Runnable / workload layers |
| Gray | `#E8EEF4` | `#8FA3B1` | Stores / neutral support |

For architecture diagrams: containers get the tinted fill, inner nodes get Sky Blue solid fill.

## Dashed Box Semantics

| Style | Border | Meaning |
| :--- | :--- | :--- |
| Planned / Future | Mid Gray `#8FA3B1` dashed (`7 6`) | Not yet built |
| Expandable / sub-diagram | Navy Dark `#1A3F6F` dashed | See detail diagram |
| Out of Scope | Mid Gray `#8FA3B1` dot-dash | Exists but outside scope |
| Error / Failure Zone | Pink `#CA54B0` dashed | Error handling region |

---

# Connector Lines

| Line Type | Color | Width | Style |
| :--- | :--- | :--- | :--- |
| Primary forward flow | `#00A0DF` | 2.4px | Solid |
| Secondary / branch | `#00A0DF` | 1.5px | Solid |
| Feedback / retry loop | `#1A3F6F` | 1.5px | Dashed (`6 4`) |
| Optional / informational | `#8FA3B1` | 1.2pt | Dashed (`4 4`) |
| Async / event-triggered | `#00A0DF` | 1.2pt | Dot-dash |
| Error / rejection | `#CA54B0` | 2px | Solid |

Rule: solid = forward/active. Dashed = backward/optional/async. Default to one arrow color family unless a second color carries a clear meaning such as error or retry.

## Arrow Routing Rules

### No crossing lines
- Avoid arrows crossing over boxes or other arrows whenever possible
- Re-layout first (move boxes), reroute second (change arrow paths)
- If crossing is unavoidable, the crossing arrow should be dashed (visually subordinate)
- No connector may pass through a node, decision diamond, or label area. Route through empty gutters or around the outside of the cluster.

### Straight and orthogonal arrows only
- Prefer straight horizontal or vertical arrows (direct, single-segment)
- If a straight path is blocked, use orthogonal paths (horizontal + vertical only, no diagonals)
- Never use curved or rounded arrows — they look imprecise and break visual rhythm
- Multi-segment orthogonal paths should have clean 90-degree corners
- For HTML/SVG diagrams, treat diagonal connectors as invalid unless the user explicitly requests them.

### Edge routing
- Route long return/event arrows around the outside of component clusters, not through them
- Enter the target near its boundary edge, not through the middle of a dense cluster
- Keep arrow lengths proportional — a 10-segment detour arrow looks broken
- When several sources feed one destination, prefer a shared fan-in bus over multiple nearly-parallel lines.
- When one source feeds sibling capabilities, show sibling branches rather than a stacked serial chain unless the runtime is actually sequential.

### Arrow anchoring
- Arrows must terminate at box edges, never mid-canvas or inside box content
- Arrows must start from a box edge or boundary edge too. Do not begin or end a connector in open whitespace.
- Center arrows on source/target box centers
- If arrows "look off" visually, check numeric center alignment first
- If a label can only fit by sitting on top of a connector, move the connector or move the label. Do not let text rest on the stroke.

---

# Typography

- **Font:** Inter (Google Fonts `Inter:wght@400;600;700`)
- **Diagram title:** 38px minimum, bold, Navy `#1A3F6F`, centered. For Docs/slides diagrams, increase when needed so the title remains clearly readable at fit.
- **Container label:** 19-20px, bold, `#1A202C` or `#1A3F6F`
- **Node title:** 20px, bold, White on blue fills / Charcoal on gray fills. Titles should be one of the most prominent text elements inside any node.
- **Node subtitle:** Avoid by default. Add only when it materially improves clarity, and remove it before shrinking the title.
- **Legend text:** 11px, `#1A202C`
- **Caption / helper:** Mid Gray `#8FA3B1`

Doc-readability defaults learned from review:

- For diagrams intended for Google Docs, markdown screenshots, or slides, increase the header title when needed so it remains readable after page-fit scaling.
- The title should be at least as visually dominant as any node title, and often larger.
- Default to no subtitle. Add a subtitle only when it materially improves clarity.
- Do not increase header size without checking the gap to the diagram. Keep the title block close enough to feel attached, with a clear but modest margin.
- Assume Google Docs and landscape slides are the default presentation targets unless the user specifies another insertion context.
- If a pre-title eyebrow or taxonomy label is used, treat it like optional support text: only include it when it adds real orientation and still passes fit readability.
- If a title becomes too long for one line, wrap it cleanly or widen the canvas. Do not let titles clip or crowd the top edge.

---

# HTML/SVG Diagrams

Use for presentation-grade diagrams where layout precision matters.

## HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>[Diagram Title]</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { background: #FFFFFF; width: max-content; height: max-content; overflow: hidden; }
    body { font-family: Inter, sans-serif; padding: 0; color: #1A202C; display: inline-block; }
    .container { display: inline-block; margin: 0; background: #FFFFFF; }
    .header { margin-bottom: 8px; padding: 10px 10px 0 10px; }
    h1 { font-size: 38px; color: #1A3F6F; font-weight: 700; text-align: center; }
    .diagram-wrap { background: #FFFFFF; border: 1px solid #D9E2EC; border-radius: 10px; padding: 10px; }
    svg { display: block; }
    line, path { stroke-linecap: round; stroke-linejoin: round; }
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Diagram Title</h1>
  </div>
  <div class="diagram-wrap">
    <svg width="2800" height="1200" viewBox="0 0 1400 600">
      <defs>
        <marker id="ah-blue" markerWidth="7" markerHeight="5" refX="6.2" refY="2.5" orient="auto">
          <polygon points="0 0, 7 2.5, 0 5" fill="#00A0DF" />
        </marker>
      </defs>
      <rect width="100%" height="100%" fill="#FFFFFF" />
      <!-- Nodes and connectors here -->
    </svg>
  </div>
</div>
</body>
</html>
```

Key rules:
- `html, body`: `width: max-content; height: max-content; overflow: hidden` — no responsive layout
- `body { display: inline-block }` — prevents extra whitespace in screenshots
- SVG viewBox is half the `width`/`height` (2x export resolution)
- White background, no grid
- Node radius: `rx="12"` for nodes, `rx="0"` for containers

Export-readability rules:

- Prefer `svg width` close to the logical `viewBox` width when exporting via Playwright with `device_scale_factor=2`. Do not blindly double the SVG CSS width; it makes all text physically smaller when the PNG is inserted into docs.
- Size text for the final inserted dimension, not just the browser preview. If the diagram is meant for a 680pt landscape insert, make sure title, node labels, and legends remain legible after downscaling.
- If readable typography makes the layout too dense, split the content into multiple diagrams instead of shrinking the text.

## Rendering (HTML → PNG)

```bash
python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1400, 'height': 600})
    page.goto('file:///absolute/path/to/diagram.html')
    page.wait_for_timeout(1000)
    page.screenshot(path='diagram.png', full_page=True)
    browser.close()
"
```

Viewport should match SVG `width`/`height`.

Source vs review artifact:

- **HTML/SVG is the editable source of truth** for making changes.
- **PNG is the visual review artifact** and the final validation target for presentation quality.
- Inspect raw HTML/SVG for diagnosis, not as the final visual judgment.

### Validation Setup

Required for the standard HTML/SVG validation workflow:

- `python3`
- Playwright Python package with Chromium available
- ability to inspect rendered PNGs visually

Quick setup check:

```bash
python3 -c "from playwright.sync_api import sync_playwright; print('playwright-ok')"
```

If this check fails, do not guess diagram quality from raw HTML. Either install the missing dependency or ask the user before proceeding.

### Validation Procedure

For every HTML/SVG diagram, validate in this order:

1. Inspect the HTML/SVG source only if needed for diagnosis.
2. Render the HTML to PNG using the command above.
3. Generate a Docs/slides fit-check PNG:

```bash
python3 scripts/docs_fit_check.py /absolute/path/to/diagram.png
```

4. Validate `G1` from the fit-check PNG or an inserted Docs/Slides screenshot when available.
5. Run helper reports when useful:

```bash
python3 scripts/png_margin_report.py /absolute/path/to/diagram.png
python3 scripts/svg_heuristics_report.py /absolute/path/to/diagram.html
```

6. Validate `G2`-`G9` from the original rendered PNG at normal and zoomed inspection, using helper output as supporting evidence rather than as the final verdict.
7. Mark rules using only directly visible evidence from the artifact.
8. Auto-fix red mechanical issues; ask the user only when the fix requires a real design tradeoff.

Automation preference:

- Prefer script-backed validation for deterministic or semi-deterministic checks.
- If a repeatable validation step does not yet have a helper script, add a small one under `scripts/` when it clearly reduces ambiguity or manual drift.
- Adapt helper scripts to the local environment when needed, but keep the human-review surface on the rendered artifact.

Current script coverage:

- `scripts/docs_fit_check.py` supports `G1` by producing a standardized Docs/slides fit preview.
- `scripts/png_margin_report.py` supports `G1` by reporting blank-margin usage on the rendered PNG.
- `scripts/svg_heuristics_report.py` supports parts of `G3`, `G4`, `G7`, and `G8` by flagging diagonal segments, rounded-rect overlaps, title-zone crossings, and likely text-overflow cases.
- `G2`, `G5`, `G6`, and `G9` still rely primarily on visual inspection of the rendered PNG, because they are composition and semantics-clarity rules.
- Helper output is supporting evidence. The final verdict still comes from the rendered artifact.

## Layout Rules

- **Container width:** Standardize per layer
- **Node height:** 80px standard; 52px for small wrappers
- **Node radius:** `rx="12"` for nodes, `rx="0"` for containers
- **Vertical gap:** Min 26px between container boundaries
- **Horizontal gap:** Min 40px between sibling nodes
- Separate decision branches enough that sibling result nodes cannot overlap.
- If a persistence, recall, or always-on runtime path is core behavior, draw it with a solid active connector. Reserve gray dashed lines for optional or indirect paths only.
- If a capability is described in the prose as part of the runtime, give it at least one explicit connection. Do not leave important boxes visually orphaned.
- If a legend is needed, prefer a compact horizontal legend bar or footer legend over a large detached legend card.
- Legends must remain readable at fit, must not be clipped, and must explain only visible boxes, boundaries, and line styles.
- Footer metadata such as `Last update` should be omitted unless explicitly requested; it competes with fit readability.
- For split diagrams, use descriptive titles such as `Gateway Routing Ingress` rather than generic `I` / `II` labels.
- If an edge label is needed, keep it short, lower-emphasis than node titles, and place it in dedicated whitespace near the connector. Do not let edge labels create route imbalance or sit on top of strokes.
- When multiple arrows branch from one source, branch from one clean tee/junction instead of several nearly-overlapping starts.
- Align repeated actors, roles, or stages to shared horizontal or vertical rails when the diagram has parallel columns or repeated rows. Reserve rotated labels for tall narrow side rails only; otherwise keep labels horizontal.
- If a node contains literal code, commands, paths, scopes, or token strings, use monospace for the literal fragment when it must stay in-node; otherwise move it to a nearby helper label. Do not squeeze long literal text into a narrow box.
- Keep decorative backgrounds subtle; they must not reduce text contrast or create confusion about diagram boundaries.
- Preserve a safe title band inside every boundary/container; routes should not cross or skim the title zone.
- In lane-based or multi-column diagrams, box placement should support one clear narrative lane rather than forcing the reader to zig-zag visually.

## Visual QA Checklist

Use this checklist for diagram review. It is intentionally visual-only. Do not mix architecture correctness or code-truth concerns into it.

| Rule | Meaning | Validation Mechanism | Auto-fix vs Ask User |
| :--- | :--- | :--- | :--- |
| `G1` | Fit readability, canvas efficiency, and non-interfering background treatment. At Google Docs / slide `Fit`, the smallest visible text is readable and the canvas does not waste large blank margins that shrink useful content. Decorative background should not reduce contrast or usable area. | Validate from the rendered PNG. If the diagram is intended for Docs/slides, use the inserted-doc or slide-fit view as the source of truth, not only browser preview. Check smallest visible text, blank margins, and whether decorative background reduces usable content area. | Auto-fix by cropping, resizing, removing low-value text, toning down background, or splitting the diagram. Ask the user if the fix requires a format tradeoff such as split vs single diagram or portrait vs landscape. |
| `G2` | Header discipline and text economy. Default is title-only header. No subtitle unless necessary. Optional eyebrow/pre-title only when it materially improves orientation. | Check whether the title is visually dominant, whether any subtitle or eyebrow is actually needed, and whether the gap between header and diagram feels intentional. | Auto-fix by removing subtitles, shrinking support text, wrapping long titles, or widening the canvas. Ask only if the user has explicitly requested a subtitle-heavy or editorial style. |
| `G3` | Connector geometry. All connectors are straight or orthogonal only. No diagonals or curves. | Trace every connector segment in the rendered PNG. Any diagonal or curved segment fails. | Auto-fix by rerouting orthogonally. Ask only if the user explicitly wants a non-standard visual style. |
| `G4` | Connector anchoring and clearance. Connectors must start and end on box or boundary edges, never in whitespace, and must not cut through boxes, titles, labels, legends, or box content. Container title zones are protected space. | Visually inspect every start point, endpoint, and route corridor. Confirm no connector terminates mid-air, passes through content areas, or crosses/skims a boundary title zone. | Auto-fix by moving boxes and rerouting lines. Ask the user only if repeated layout attempts still cannot avoid the conflict. |
| `G5` | Arrow alignment and balance. Branches should feel visually balanced, routes should avoid unnecessary bends, bulges, or awkward tee points, and edge labels must not distort branch geometry. If one branch is much cleaner than the other, re-layout first. | Compare sibling branches, tee points, edge-label positions, and route lengths. If one side looks forced or much messier than the other, it fails or is yellow. | Auto-fix by rebalancing boxes, adjusting tee points, or removing low-value edge labels. Ask if the cleaner layout would materially change the storytelling split of the diagram. |
| `G6` | Color semantics and legend necessity. A diagram should be understandable without a legend when possible. If different colors, dashed paths, or boundary styles are not self-evident, add a compact legend. | Perform a cold-reader check on the rendered PNG: could someone unfamiliar infer the meaning of colors and line styles from labels and structure alone? If not, a legend is needed and must still pass `G1`. | Auto-fix by simplifying colors or adding a compact footer/horizontal legend. Ask if the choice is between preserving richer semantic color meaning vs simplifying the palette. |
| `G7` | Boundary containment, internal padding, and literal-text treatment. Titles, nodes, and inner content must stay fully inside intended boxes with comfortable padding. Literal code/path/token text must either fit cleanly or move out of the node. | Check for clipping, crowding, edge pressure, and overloaded literal text. Container titles must have safe space and nothing should spill outside boundaries. | Auto-fix by widening nodes, moving boxes, shortening text, or using monospace for literal fragments. Ask only if shortening would lose meaning the user may care about. |
| `G8` | Box alignment, rail/grid placement, and narrative-lane clarity. Sibling boxes should align and space consistently. Repeated actors, roles, or stages should sit on stable horizontal/vertical rails so routing stays clean and the story reads in one clear lane. | Inspect rows, columns, repeated actors, and lane alignment. If misalignment forces detours, weakens one clear reading order, or makes relationships feel accidental, it fails or is yellow. | Auto-fix by aligning boxes and standardizing row/column spacing. Ask only if alignment would conflict with a user-requested narrative emphasis. |
| `G9` | Flow direction consistency. If arrows indicate flow/sequence, they must do so consistently within the diagram. Missing arrowheads or mixed directional conventions are not allowed. | Verify that all important forward flows use clear arrowheads, and that dashed feedback or retry paths also show direction when direction matters. Ignore editor/browser chrome. | Auto-fix by adding or normalizing arrowheads and line styles. Ask only if the user explicitly wants a non-directional conceptual diagram. |

Review discipline:

- When a user points out a defect, verify it visually from the rendered PNG or inserted doc view before marking the rule status.
- Mark a rule red only when the issue is directly visible in the artifact.
- Mark a rule yellow only when it is visible but arguable or still acceptable for draft review.
- Do not mark non-visual architecture concerns in this matrix; review those separately.
- Ignore browser/editor UI chrome such as selection handles, toolbar overlays, or temporary highlights when scoring the diagram.

---

# Mermaid Diagrams

Use for source-editable diagrams in markdown — sequences, ERDs, state diagrams, simple flowcharts.

## classDef Mappings

Use these `classDef` lines at the top of your Mermaid diagram. Do NOT wrap them in `%%{init:...}%%` — GitHub does not support init blocks.

```
classDef default fill:#00A0DF,stroke:#00A0DF,color:#FFFFFF,stroke-width:2px
classDef terminal fill:#1A3F6F,stroke:#1A3F6F,color:#FFFFFF,stroke-width:2px
classDef human fill:#1A202C,stroke:#1A202C,color:#FFFFFF,stroke-width:2px
classDef error fill:#CA54B0,stroke:#CA54B0,color:#FFFFFF,stroke-width:2px
classDef emphasis fill:#306FB7,stroke:#306FB7,color:#FFFFFF,stroke-width:2px
classDef inactive fill:#E8EEF4,stroke:#8FA3B1,color:#1A202C,stroke-width:2px
classDef store fill:#E8EEF4,stroke:#8FA3B1,color:#1A202C,stroke-width:2px
classDef boundary fill:#EAF2EA,stroke:#4CAF7D,color:#1A3F6F,stroke-width:2px
classDef support fill:#F0EBF9,stroke:#7C4DCC,color:#1A202C,stroke-width:2px
classDef workload fill:#FFE9EE,stroke:#E05C7A,color:#1A202C,stroke-width:2px
```

## Shape Conventions

| Shape | Mermaid Syntax | Use For |
| :--- | :--- | :--- |
| Rounded rect | `[Label]` | Process steps, components |
| Stadium | `([Label])` | START / END terminals |
| Diamond | `{Label}` | Decisions, gates |
| Cylinder | `[(Label)]` | Databases, storage |
| Subgraph | `subgraph` | Containers, boundaries |

## Per-Diagram Rules

### Flowcharts
- `flowchart TB` for layer stacks, `flowchart LR` for progression
- Put owned boundaries in `subgraph`
- Avoid bidirectional arrows unless both directions matter
- Label only important edges

### Sequence Diagrams
- 5-8 participants max
- Client/caller first, owned services next, external last
- Verb-first messages: `Create run`, `Submit flow`, not sentence-length
- Use `Note over` for important rules

### ER Diagrams
- Show only tables in scope
- Include PK, major FKs, 2-4 key fields
- Lead with primary entities

## GitHub / GitLab Compatibility

These cause `< Invalid Mermaid Codes >` or blank renders:

1. **No `%%{init:{...}}%%` blocks** — use `classDef` only
2. **No `direction LR/TB` inside subgraphs** — silently fails
3. **No `\\n` in labels** — use separate reference nodes
4. **No `<br/>` or `<small>` HTML** — plain text only
5. **No Unicode box-drawing or em-dash** (`—`, `–`, `━`) — use ASCII `-`
6. **No `stroke-dasharray` in classDef** — not valid in older versions
7. **No transparent fill** — use explicit light colors instead
8. **Max 2 levels deep subgraphs** — deeper breaks layout
9. **Keep edge labels short** — long labels cause overlap

If a diagram fails to render, strip `%%{init...}` and `direction` first.

## When Mermaid Is Wrong

Switch to HTML/SVG when:
- 10+ nodes with nested subgraphs (layout fights renderers)
- Strict stacked composition needed
- Straight arrows and exact spacing matter
- Presentation quality is critical

Rule: if you keep fighting the renderer, the tool choice is wrong.

---

# Format Decision

| Diagram Intent | Format | Why |
| :--- | :--- | :--- |
| Polished architecture/block topology | HTML → SVG → PNG | Layout precision, presentation quality |
| Temporal / runtime / process flow | Mermaid sequence | Time-ordered, source-editable |
| Schema / state semantics | Mermaid ERD / state | Structured, compact |
| Simple conceptual support | Mermaid flowchart | Text maintainability > polish |

---

# Google Docs Insertion

- Portrait primary figures: 480pt width
- Landscape primary: 680pt width
- Medium support: 420–460pt portrait / 560–620pt landscape
- Always insert with explicit width — never rely on auto-sizing
- Render Mermaid to PNG locally first via `mermaid-cli`
- Heading remap after Drive import: `#` → Title, `##` → Heading 1

---

# Anti-Patterns

1. Do not use pastel-tinted fills for process nodes — use solid Sky Blue
2. Do not use dark backgrounds — GDP Labs uses white
3. Do not put 3 parallel arrows where 1 representative suffices
4. Do not route arrows through box content
5. Do not use `min-height: 100vh` — creates blank space in screenshots
6. Do not mix node fills and container tints — containers are pale, nodes are saturated
7. Do not leave stale diagrams after replacing them
8. Do not reference `.html` paths in markdown — use `.png` only
9. Do not use curved or rounded arrows — straight and orthogonal only
10. Do not let arrows cross over boxes — re-layout or reroute
11. Do not use `%%{init:...}%%` blocks in Mermaid — GitHub rejects them
