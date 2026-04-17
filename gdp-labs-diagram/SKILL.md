---
name: gdp-labs-diagram
description: Generate architecture and process diagrams using the GDP Labs visual style guide. Supports both HTML/SVG (presentation-grade) and Mermaid (source-editable) formats. Based on the GDP Labs Diagram Color Guide.
version: 1.0.0
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

Rule: solid = forward/active. Dashed = backward/optional/async. Color matches the originating node.

---

# Typography

- **Font:** Inter (Google Fonts `Inter:wght@400;600;700`)
- **Diagram title:** 38px, bold, Navy `#1A3F6F`, centered
- **Subtitle:** 17px, `#4A5568`, centered
- **Container label:** 19px, bold, `#1A202C` or `#1A3F6F`
- **Node title:** 18px, bold, White on blue fills / Charcoal on gray fills
- **Node subtitle:** 14px (large) or 13px (small), White on blue / Charcoal on gray
- **Legend text:** 11px, `#1A202C`
- **Caption / helper:** Mid Gray `#8FA3B1`

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
    .subtitle { color: #4A5568; font-size: 17px; text-align: center; margin-top: 8px; }
    .diagram-wrap { background: #FFFFFF; border: 1px solid #D9E2EC; border-radius: 10px; padding: 10px; }
    svg { display: block; }
    line, path { stroke-linecap: round; stroke-linejoin: round; }
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Diagram Title</h1>
    <p class="subtitle">Description</p>
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

## Layout Rules

- **Container width:** Standardize per layer
- **Node height:** 80px standard; 52px for small wrappers
- **Node radius:** `rx="12"` for nodes, `rx="0"` for containers
- **Vertical gap:** Min 26px between container boundaries
- **Horizontal gap:** Min 40px between sibling nodes
- **Arrow anchoring:** Arrows terminate at box edges, center-aligned
- **Legend:** Only when 3+ color families or mixed line styles

---

# Mermaid Diagrams

Use for source-editable diagrams in markdown — sequences, ERDs, state diagrams, simple flowcharts.

## classDef Mappings

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Inter, ui-sans-serif, system-ui, sans-serif", "fontSize": "14px"}}}%%

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
