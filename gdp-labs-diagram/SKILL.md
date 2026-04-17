---
name: gdp-labs-diagram
description: Generate architecture diagrams using the GDP Labs visual style guide. Solid-filled nodes, pastel container tints, Inter font, white background. Based on the GDP Labs Diagram Color Guide PDF.
version: 1.0.0
author: GDP Labs
license: proprietary
dependencies: []
metadata:
  tags: [architecture, diagrams, SVG, HTML, visualization, gdp-labs]
  related_skills: [architecture-diagram, mermaid-diagram]
---

# GDP Labs Diagram Skill

Generate architecture and design diagrams using the GDP Labs visual style. White background, solid-colored nodes, pastel-tinted containers, Inter font. Self-contained HTML with inline SVG.

This is distinct from the generic `architecture-diagram` skill (Cocoon AI dark theme). Use this skill when the diagram is for GDP Labs projects or when the GDP Labs Diagram Color Guide applies.

## Reference Diagrams

Real production diagrams are in `templates/`:
- `reference-architecture.html` — GL Runner internal architecture (control plane + execution plane)
- `reference-design-stack.html` — GL Runner design stack view (plugged implementations)
- `reference-ecosystem.html` — GL Runner ecosystem (GDP Labs platform context)
- `sample-agent-workflow.html` — PDF sample flowchart demonstrating all color overrides (HTML/SVG)
- `sample-agent-workflow.md` — Same sample as Mermaid with classDef mappings

The sample agent workflow demonstrates every color override from the PDF:
- Sky Blue default for all process steps
- Navy Dark oval for START/END terminals
- Charcoal for human Review Gates
- Pink for error/rejection path
- Navy for the key CTA (Merge Results)
- Dashed Navy Dark for retry loops

## Color System

Based on the GDP Labs Diagram Color Guide (PDF).

### Node Fills — Default

Use Sky Blue `#00A0DF` as the default fill for ALL nodes unless an override applies. Text on these nodes is White `#FFFFFF`.

```
<rect ... fill="#00A0DF" stroke="#00A0DF" rx="12" />
<text ... fill="#FFFFFF">Node Name</text>
```

### Node Fills — Override Decision Tree

| Question | Fill | Text | Why |
| :--- | :--- | :--- | :--- |
| Start or end terminal? | Navy Dark `#1A3F6F` | White | Entry/exit — use oval shape |
| Human review or gate? | Charcoal `#1A202C` | White | Must never look automated |
| Error or rejection path? | Pink `#CA54B0` | White | "Something wrong" signal |
| Most important CTA (max 1–2)? | Navy `#306FB7` | White | Eye-drawing emphasis |
| Inactive / future / disabled? | Light Gray `#E8EEF4` | Charcoal `#1A202C` | Recedes visually |
| Storage / neutral support? | Light Gray `#E8EEF4` | Charcoal `#1A202C` | Stores, queues, neutral boxes |

If none of the overrides apply, use Sky Blue. No further thinking required.

### Container / Boundary Tints

Containers group components by plane or ownership. Use the tinted fill + colored border:

| Container | Fill | Border | Label Text |
| :--- | :--- | :--- | :--- |
| Client / Surface | `#E8EEF4` | `#8FA3B1` | Charcoal `#1A202C` |
| Control Plane / Server | `#EAF2EA` | `#4CAF7D` | Navy `#1A3F6F` |
| Execution Plane / Worker | `#FFE9EE` | `#E05C7A` | Navy `#1A3F6F` |
| External / Integration | `#F0EBF9` | `#7C4DCC` | Charcoal `#1A202C` |

### Dashed Box Semantics

| Style | Border | Meaning |
| :--- | :--- | :--- |
| Planned / Future | Mid Gray `#8FA3B1` dashed (`7 6`) | Not yet built |
| Expandable / sub-diagram | Navy Dark `#1A3F6F` dashed | See detail diagram |
| Out of Scope | Mid Gray `#8FA3B1` dot-dash | Exists but outside scope |
| Error / Failure Zone | Pink `#CA54B0` dashed | Error handling region |

### Connector Lines

| Line Type | Color | Width | Style |
| :--- | :--- | :--- | :--- |
| Primary forward flow | `#00A0DF` | 2.4px | Solid |
| Secondary / branch | `#00A0DF` | 1.5px | Solid |
| Feedback / retry loop | `#1A3F6F` | 1.5px | Dashed (`6 4`) |
| Optional / informational | `#8FA3B1` | 1.2px | Dashed (`4 4`) |
| Async / event-triggered | `#00A0DF` | 1.2px | Dot-dash |
| Error / rejection | `#CA54B0` | 2px | Solid |

Rule: solid = forward/active. Dashed = backward/optional/async. Color matches the originating node.

## Typography

- **Font:** Inter (Google Fonts `Inter:wght@400;600;700`)
- **Diagram title:** 38px, bold, Navy `#1A3F6F`, centered
- **Subtitle:** 17px, `#4A5568`, centered
- **Container label:** 19px, bold, `#1A202C` or `#1A3F6F`
- **Node title:** 18px, bold, White `#FFFFFF` on blue fills / Charcoal `#1A202C` on gray fills
- **Node subtitle:** 14px (large nodes) or 13px (small nodes), White on blue / Charcoal on gray
- **Future/sub label:** 11px, `#4A5568`

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
    .diagram-wrap { background: #FFFFFF; border: 1px solid #D9E2EC; border-radius: 10px; padding: 10px 10px 4px 10px; }
    svg { display: block; }
    line, path { stroke-linecap: round; stroke-linejoin: round; }
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Diagram Title</h1>
    <p class="subtitle">One-line description</p>
  </div>
  <div class="diagram-wrap">
    <svg width="2640" height="1984" viewBox="0 0 1320 992">
      <defs>
        <marker id="arrBlue" markerWidth="7" markerHeight="5" refX="6.2" refY="2.5" orient="auto">
          <polygon points="0 0, 7 2.5, 0 5" fill="#00A0DF" />
        </marker>
      </defs>
      <rect width="100%" height="100%" fill="#FFFFFF" />
      <!-- Containers and nodes go here -->
    </svg>
  </div>
</div>
</body>
</html>
```

Key rules:
- `html, body` use `width: max-content; height: max-content; overflow: hidden` — no responsive layout
- `body { display: inline-block }` — prevents extra whitespace in screenshots
- SVG viewBox is half the `width`/`height` attributes (2x export resolution)
- Export at 2x for crisp PNG downscaling in Google Docs

## Rendering (HTML → PNG)

Use Playwright to screenshot:

```bash
python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1320, 'height': 992})
    page.goto('file:///absolute/path/to/diagram.html')
    page.wait_for_timeout(1000)
    page.screenshot(path='diagram.png', full_page=True)
    browser.close()
"
```

Viewport should match SVG `width`/`height`. `full_page=True` captures the entire diagram.

## Google Docs Insertion

- Portrait primary figures: 480pt width
- Landscape primary figures: 680pt width
- Medium support: 420–460pt portrait / 560–620pt landscape
- Always insert with explicit width — never rely on GDocs auto-sizing

## Layout Rules

- **Container width:** Standardize per layer (e.g., all server containers same width)
- **Node height:** 80px standard for main components; 52px for small wrappers (SDK, CLI)
- **Node radius:** `rx="12"` for nodes, `rx="0"` for containers (sharp corners on boundaries)
- **Vertical gap:** Minimum 26px between container bottom and next container top
- **Horizontal gap:** Minimum 40px between sibling nodes inside a container
- **Arrow anchoring:** Arrows terminate at box edges. Use center-point math to align.
- **Legend:** Optional. Use only when the diagram has 3+ color families or mixed line styles.

## Anti-Patterns

1. Do not use pastel-tinted fills for individual nodes — nodes are solid Sky Blue
2. Do not use JetBrains Mono — GDP Labs uses Inter
3. Do not use dark backgrounds — GDP Labs uses white
4. Do not put 3 parallel arrows where 1 representative suffices
5. Do not route arrows through box content — use center gutters
6. Do not use `min-height: 100vh` — it creates blank space in screenshots
7. Do not mix node fills and container tints — containers are pale, nodes are saturated
