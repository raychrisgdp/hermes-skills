---
name: architecture-diagram
description: Generate professional dark-themed system architecture diagrams as standalone HTML/SVG files. Self-contained output with no external dependencies. Based on Cocoon AI's architecture-diagram-generator (MIT).
version: 1.1.0
author: Cocoon AI (hello@cocoon-ai.com), ported by Hermes Agent
license: MIT
dependencies: []
metadata:
  hermes:
    tags: [architecture, diagrams, SVG, HTML, visualization, infrastructure, cloud]
    related_skills: [excalidraw]
---

# Architecture Diagram Skill

Generate professional, dark-themed technical architecture diagrams as standalone HTML files with inline SVG graphics. No external tools, no API keys, no rendering libraries — just write the HTML file and open it in a browser.

Based on [Cocoon AI's architecture-diagram-generator](https://github.com/Cocoon-AI/architecture-diagram-generator) (MIT).

## Workflow

1. User describes their system architecture (components, connections, technologies)
2. Generate the HTML file following the design system below
3. Save with `write_file` to a `.html` file (e.g. `~/architecture-diagram.html`)
4. Convert to PNG for markdown/doc attachment (see HTML→PNG below)
4. User opens in any browser — works offline, no dependencies

### Iterative refinement notes
- If a connector should stay straight, move the source/target anchor point instead of introducing a diagonal or routed detour.
- Preserve special routed paths only when the diagram semantics really require them.
- After each layout change, inspect the rendered PNG in a browser or vision pass; text snapshots miss spacing, overlap, and crop issues.
- When moving lower rows downward, re-check legend placement so it stays outside every boundary box.
- Keep paired diagrams (for example architecture and design views) aligned to the same spacing logic so they don’t drift visually.

### Output Location

Save diagrams to a user-specified path, or default to the current working directory:
```
./[project-name]-architecture.html
```

### Preview

After saving, suggest the user open it:
```bash
# macOS
open ./my-architecture.html
# Linux
xdg-open ./my-architecture.html
```

## HTML → PNG Conversion (for Markdown/Docs)

**This is the primary method for producing doc-attachable diagrams.** HTML/SVG with hand-positioned coordinates produces 9/10 quality; Graphviz .dot → .png produces 3/10 for complex diagrams (text truncation, overlap, cramped layout). Always prefer HTML→PNG over Graphviz for anything beyond trivial diagrams.

Use Playwright (or headless Chrome) to screenshot the HTML:

```bash
# Playwright (Python) — preferred
python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1200, 'height': 900})
    page.goto('file:///absolute/path/to/diagram.html')
    page.wait_for_timeout(1000)
    page.screenshot(path='diagram.png', full_page=True)
    browser.close()
"

# Chrome headless fallback
google-chrome --headless --screenshot=diagram.png --window-size=1200,900 \
  --no-sandbox file:///absolute/path/to/diagram.html
```

**Viewport sizing:** Match the SVG viewBox width. Height should be slightly taller than the viewBox to avoid scrollbars. `full_page=True` captures the entire page including overflow.

**File naming:** Save source as `[name].html` and PNG as `[name].png`. Keep the HTML as the editable source — regenerate PNG after any change.

## Design System & Visual Language

### Color Palette (Semantic Mapping)

Use specific `rgba` fills and hex strokes to categorize components:

| Component Type | Fill (rgba) | Stroke (Hex) |
| :--- | :--- | :--- |
| **Frontend** | `rgba(8, 51, 68, 0.4)` | `#22d3ee` (cyan-400) |
| **Backend** | `rgba(6, 78, 59, 0.4)` | `#34d399` (emerald-400) |
| **Database** | `rgba(76, 29, 149, 0.4)` | `#a78bfa` (violet-400) |
| **AWS/Cloud** | `rgba(120, 53, 15, 0.3)` | `#fbbf24` (amber-400) |
| **Security** | `rgba(136, 19, 55, 0.4)` | `#fb7185` (rose-400) |
| **Message Bus** | `rgba(251, 146, 60, 0.3)` | `#fb923c` (orange-400) |
| **External** | `rgba(30, 41, 59, 0.5)` | `#94a3b8` (slate-400) |

**Brighter alternative palette** (use hex fills instead of rgba for more vivid, readable boxes — especially when the double-rect masking technique makes rgba look too dark):

| Component Type | Fill (Hex) | Stroke (Hex) |
| :--- | :--- | :--- |
| **Frontend/API** | `#155e75` | `#22d3ee` |
| **Backend (Server)** | `#065f46` | `#34d399` |
| **Backend (Worker)** | `#155e75` | `#22d3ee` |
| **Database/Storage** | `#4c1d95` | `#a78bfa` |
| **Cloud/Infra** | `#92400e` | `#fbbf24` |
| **Security** | `#881337` | `#fb7185` |
| **External** | `#334155` | `#94a3b8` |

### Typography & Background
- **Font:** JetBrains Mono (Monospace), loaded from Google Fonts
- **Sizes:** 12px (Names), 9px (Sublabels), 8px (Annotations), 7px (Tiny labels)
- **Background:** Slate-950 (`#020617`) with a subtle 40px grid pattern

```svg
<!-- Background Grid Pattern -->
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/>
</pattern>
```

## Technical Implementation Details

### Component Rendering
Components are rounded rectangles (`rx="6"`) with 1.5px strokes. To prevent arrows from showing through semi-transparent fills, use a **double-rect masking technique**:
1. Draw an opaque background rect (`#0f172a`)
2. Draw the semi-transparent styled rect on top

### Connection Rules
- **Z-Order:** Draw arrows *early* in the SVG (after the grid) so they render behind component boxes
- **Arrowheads:** Defined via SVG markers
- **Security Flows:** Use dashed lines in rose color (`#fb7185`)
- **Boundaries:**
  - *Security Groups:* Dashed (`4,4`), rose color
  - *Regions:* Large dashed (`8,4`), amber color, `rx="12"`

### Spacing & Layout Logic
- **Standard Height:** 60px (Services); 80-120px (Large components)
- **Vertical Gap:** Minimum 40px between components
- **Message Buses:** Must be placed *in the gap* between services, not overlapping them
- **Legend Placement:** **CRITICAL.** Must be placed outside all boundary boxes. Calculate the lowest Y-coordinate of all boundaries and place the legend at least 20px below it.

## Document Structure

The generated HTML file follows a four-part layout:
1. **Header:** Title with a pulsing dot indicator and subtitle
2. **Main SVG:** The diagram contained within a rounded border card
3. **Summary Cards:** A grid of three cards below the diagram for high-level details (optional — omit when the diagram is for markdown/doc attachment, keep only for standalone review pages)
4. **Footer:** Minimal metadata

### Info Card Pattern
```html
<div class="card">
  <div class="card-header">
    <div class="card-dot cyan"></div>
    <h3>Title</h3>
  </div>
  <ul>
    <li>• Item one</li>
    <li>• Item two</li>
  </ul>
</div>
```

## Component Naming & Layout Rules

### Interface names, not implementation names
In architecture-level diagrams, use the interface/contract name (e.g., "ControlPlaneStore") not the concrete backend (e.g., "PostgreSQL"). Save implementation names for design/implementation diagrams where showing the plugged default is the purpose.

### Store placement
Persistent stores (databases, object storage, message queues) should be drawn as **separate boxes outside** the Server/Worker boundary boxes, not inside them. They are their own deployable services. Place them between or below the service boundaries they connect to.

### Layer ordering convention
When showing a full-stack system, order layers top-to-bottom:
1. **Clients** (consumer surfaces): GL Chat, Other Apps, external tools
2. **Surface layer** (API/integration): REST API, SDK, CLI
3. **Service layer** (business logic): Server, Worker (in dashed boundary boxes)
4. **Storage layer** (persistence): Stores as separate boxes
5. **Infrastructure layer** (external): Connectors, Observability, cloud services

### Alignment and arrow-hygiene rules (important for review quality)
Use these when iterating with users on visual polish:

- Keep major layer boundary boxes on a shared horizontal frame (`x` and `width` consistent across layers) unless there is a deliberate reason not to.
- Center arrows on source/target box centers. If users say arrows "look off", check numeric center alignment first.
- Avoid crossing lines in dense diagrams by routing long return/event lines outside the main component clusters (edge routes), then re-enter near the target.
- If two adjacent layers look too similar, switch one layer to a different hue family (not just lighter/darker variants of the same hue).
- Keep sub-box heights consistent within the same layer; a single odd-height box is visually jarring even if technically correct.
- For cross-cutting vertical bands (e.g., Observability), use a dedicated side rail and rotate text in the direction users prefer (`rotate(90)` vs `rotate(-90)`) after visual review.

### Terminology consistency with docs
For architecture/internal diagrams, verify labels against `architecture.md` and `design.md` before finalizing:

- Prefer canonical interface names from docs (e.g., `Control Plane API`, `OrchestrationBackend`, `ControlPlaneStore`, `ArtifactStore`, `WorkerHost`, `ExecutionRuntime`, `RunnableAdapter`, `EventPublisher`, `ConnectorClient`).
- Avoid introducing component names not present in docs unless requested.
- Distinguish architecture vs implementation views: architecture should use interface names; implementation may show concrete backends.

### SVG marker IDs
When multiple `<marker>` defs exist on the same page (e.g., different arrowhead colors), use unique IDs like `ah`, `ah-rose`, `ah-amber` to avoid collisions. Same-page SVG elements share a global ID namespace.

## GDP Labs UI/UX Diagram Style Guide (Preferred)

When the user asks for GDP Labs-style diagrams (or provides color-guide references), follow this style guide over generic defaults.

### ① Color semantics (node fills)

Use one semantic color per role group, and keep the same color for all nodes in that same role.

- Default/general process nodes: `Sky Blue #00A0DF`
- Start/End terminals: `Navy Dark #1A3F6F`
- Human review/gates: `Charcoal #1A202C`
- Error/reject nodes and paths: `Pink #CA54B0`
- High-emphasis key node (max 1-2): `Navy #306FB7`
- Inactive/future/disabled: `Light Gray #E8EEF4` with text `#1A202C`

If none of the override conditions apply, use **Sky Blue**.

### ② Override decision rule

Only override from Sky Blue when one of these is true:
1. Start/End terminal -> `#1A3F6F`
2. Human-in-the-loop gate -> `#1A202C`
3. Error/rejection path -> `#CA54B0`
4. Single key CTA/emphasis node -> `#306FB7` (max 1-2 nodes)
5. Inactive/future node -> `#E8EEF4` with dark text

### ③ Connector line rules

- Main forward flow: solid Sky Blue, 2px
- Secondary/branch spine: solid Sky Blue, 1px
- Error/reject flow: solid Pink, 2px
- Feedback/retry loop: dashed Navy Dark, ~1.5px
- Optional/info path: dashed Mid Gray `#8FA3B1`, ~1.2px
- Async/event-triggered: dot-dash Sky Blue, ~1.2px

Rule: solid = active forward flow. Dashed/dot-dash = loop/optional/async semantics.

### ④ Dashed box/container semantics

Use dashed containers only when semantically needed:
- Planned/future scope: Mid Gray dashed
- Expandable/has detail sub-diagram: Navy Dark dashed
- Out of scope: Mid Gray dot-dash
- Error/failure zone: Pink dashed

For normal in-scope system layers, prefer solid or lightly styled group containers, not heavy dashed noise everywhere.

### ⑤ Typography/contrast hierarchy

- White text `#FFFFFF` on dark/saturated node fills
- Body text on white/light cards: `Charcoal #1A202C`
- Secondary captions: `#8FA3B1`
- Use strong heading contrast and keep sublabels lighter and smaller

### ⑥ Practical composition rules

- Keep arrows centered on source/target boxes
- Avoid crossing lines whenever possible (re-layout first, reroute second)
- Use consistent box widths per layer to avoid visual jitter
- If two layers are adjacent, ensure clearly different hue families
- For internal architecture diagrams, minimize external context boxes
- For ecosystem diagrams, place cross-cutting concerns (e.g., observability) as side bands

### ⑧ Rendering and QA loop

For any diagram that will be exported to PNG or embedded in docs:
- Render the HTML first, then inspect the output visually before finalizing.
- If a connector is meant to read as flow, make sure it has an obvious arrowhead; thin unlabeled lines can look like separators.
- Re-center top rows and surface bands if the middle box is too wide or the arrows feel cramped.
- Use browser-based visual inspection when possible to catch subtle spacing issues that text snapshots miss.
- If a legend is present, keep it singular (`Legend`) unless the page truly has multiple separate legend blocks.
- Legend entries should map only to visible box/boundary types; do not use the legend to explain abstract categories that are not rendered as their own boxes.

- Use the singular label `Legend` unless there are multiple separate legend blocks.
- Keep legend entries tied to actual visible box types or boundary types in the diagram.
- Avoid broad semantic categories in the legend if they do not correspond to a real box on the canvas.
- Do not mix cross-cutting concerns and node families into the same legend row unless the diagram explicitly shows them as separate bounded regions.
- In top surface rows, if a connector reads like a divider instead of a flow, move it to the boundary edge and increase stroke width slightly so the arrowhead stays visible in PNG exports.
- Keep the surface row boxes the same height family; a taller middle box or an extra subtitle can make the row look unbalanced.
- For dense deployment overview pages, split into smaller diagrams instead of forcing every topology into one screenful.


### ⑨ Color collision avoidance

- If two roles are adjacent in the diagram, give them clearly different hue families.
- Distinguish red-family colors used for stores / persistent boundaries from pink-family colors used for error or rejection paths.
- Keep store colors, worker colors, and support/integration colors from collapsing into the same family by accident.

## Output Requirements

When maintaining multiple related diagrams (e.g., ecosystem + internal), enforce these checks:

- Terminology parity: if a boundary has a canonical name in one diagram (e.g., `Surface Layer`), use the same name in the others unless explicitly justified.
- Storage placement: when stores are shared by server/control and worker/execution concerns, place store boxes in an intermediate layer between the two major boundaries (not inside only one side).
- Box style consistency: if requested, standardize all small in-boundary component boxes to one visual style (same fill/stroke/text treatment) and reserve alternate colors for special categories like stores.
- Arrowhead consistency: keep one marker geometry across all arrows. Prefer smaller heads for dense diagrams (example: ~7x5 marker with proportional refX/refY) so shaft remains visible.
- Routing priority: avoid arrows crossing boxes. Use orthogonal multi-segment paths (horizontal/vertical only), routed through outer lanes when needed.
- Label placement: for long vertical return paths on tight side margins, use rotated vertical labels instead of cramped horizontal labels.
- If flow-type colors create confusion, collapse to a single arrow color and encode semantics via line style (solid vs dashed/dot-dash) plus explicit labels.

### ⑩ Repo-specific lessons from GL Runner diagram work

- Keep the repo README clear of long-lived visual conventions; the skill is the source of truth.
- For the GL Runner internal architecture view, use `Light Gray #E8EEF4` with a gray border for stores when the goal is to avoid confusing them with error/reject or worker-boundary colors.
- Reserve the worker-boundary purple family for the actual worker/execution boundary; do not re-use it for helper/support boxes.
- For bottom integration boxes, prefer neutral slate/gray fills and borders so they do not compete with the worker or store colors.
- If the observability side band feels cramped, widen the right margin or the band before shrinking the text further.
- For markdown screenshots, render from HTML with a slightly larger viewport and higher device scale factor so legends and small labels remain crisp.
- If the diagram is for docs, keep the legend compact and tied only to real visible box/boundary types.
- When an area becomes text-dense, shorten labels before shrinking font size.
- For dense internal architecture diagrams, equalize sibling box sizes first, then reroute long connectors around boundaries so they do not cut through inner boxes.
- If a box title is long, prefer widening or rebalancing the row before shrinking typography; then add a little more vertical padding so title and subtitle do not feel cramped.
- When a connector crosses an inner box or makes the middle of the diagram feel busy, move the anchor points outward and re-center the row instead of accepting the crossing.
- If the control-plane-to-worker bridge feels too prominent, remove any duplicate helper arrows first and only keep the one route that best matches ownership.
- After any visual cleanup, re-export the PNG and inspect the screenshot again; text snapshots miss spacing problems.

## Practical Lessons from Use
- Prefer HTML→PNG when exact spacing, legend placement, or screenshot fidelity matters; Mermaid was too loose for this workflow.
- Keep the exported HTML body compact. `min-height: 100vh` can create useless blank space in screenshots.
- After each render, check the result visually and compare PNG dimensions before shipping.
- When you update doc image refs, delete superseded PNGs so the markdown cannot drift back to stale assets.
- Place legends outside all boundary boxes, and verify the lowest boundary Y before finalizing.

## Output Requirements
- **Single File:** One self-contained `.html` file
- **No External Dependencies:** All CSS and SVG must be inline (except Google Fonts)
- **No JavaScript:** Use pure CSS for any animations (like pulsing dots)
- **Compatibility:** Must render correctly in any modern web browser

## Practical Refinement Loop
- Treat the HTML as the source of truth, then export a PNG for markdown with a browser screenshot tool (Playwright worked well in this repo).
- Verify the PNG with a visual pass before stopping; small spacing issues are easier to catch there than in SVG/source inspection.
- When polishing spacing, adjust the outer body padding/header margin first, then section heights, then row offsets inside the diagram.
- Common fixes that mattered here: tighten title-to-surface spacing, reduce dead space under a control-plane boundary, and move the lower worker row upward a bit so the execution plane reads as one cluster.
- If the PNG looks oddly cropped or too tall, check for CSS like `min-height: 100vh` or other layout rules that expand the capture canvas.

## Template Reference
When polishing a diagram, especially an internal architecture view:
- Prefer moving boxes over stretching connectors when a node feels detached.
- Keep sibling boxes equal in height/width where possible; make the set read as a grid.
- Increase vertical breathing room between layers before adding more connector bends.
- Remove redundant arrows early; if a route feels like a duplicate or a visual loop, simplify it.
- Use browser vision after each render to catch alignment drift, cramped text, and “one box out of place” issues that are hard to see in raw SVG.
- If a boundary box is the main visual outlier, fix that first; it usually improves the whole composition faster than micro-adjusting everything else.
- When a diagram has shared persistence, draw it as an explicit intermediate storage band between major boundaries instead of embedding the stores inside one service box.
- Normalize the widths of sibling boxes before rerouting arrows; once the row reads as a grid, the connector cleanup is usually much easier.
- If a connector feels dominant or crowded, remove any duplicate/helper arrows first and only reroute the one path that actually carries the ownership semantics.
- After every meaningful HTML change, regenerate the PNG and inspect the screenshot again; the HTML source is the truth, but the PNG is what docs readers will actually see.

---

# Graphviz `.dot` → `.png` Workflow (Fallback)

**Quality warning:** Graphviz with dark-themed HTML-like table nodes scores ~3/10 (text truncation, label overlap, cramped layout). For any diagram with 10+ components, prefer the HTML→PNG workflow above. Use Graphviz only for simple diagrams or when the project specifically requires `.dot` source files.

For projects that attach diagrams to Markdown docs or Google Docs, use Graphviz `.dot` files rendered to PNG. The HTML/SVG skill above is for interactive browser viewing; this section covers the static-image pipeline.

## Dark Theme Palette for Graphviz

Translate the semantic color system to Graphviz HTML-like labels:

| Component Type | Fill (BGCOLOR) | Stroke (COLOR) |
| :--- | :--- | :--- |
| **Frontend/API** | `#0c4a6e` | `#22d3ee` |
| **Backend (Server)** | `#064e3b` | `#34d399` |
| **Backend (Worker)** | `#0c4a6e` | `#22d3ee` |
| **Database/Storage** | `#2e1065` | `#a78bfa` |
| **Cloud/Infra** | `#451a03` | `#fbbf24` |
| **Security** | `#4c0f23` | `#fb7185` |
| **External** | `#1e293b` | `#94a3b8` |

Graph background: `bgcolor="#0f172a"`

## Component Node Pattern

Use HTML-like labels with `TABLE` for styled boxes:

```dot
ComponentName [label=<
    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="10" COLOR="#34d399" BGCOLOR="#064e3b">
        <TR><TD><FONT POINT-SIZE="12" COLOR="#ffffff"><B>Component Name</B></FONT></TD></TR>
        <TR><TD><FONT POINT-SIZE="9" COLOR="#94a3b8">Sublabel text</FONT></TD></TR>
    </TABLE>
>];
```

## Pitfalls and Fixes

### Edge labels with ortho splines

`splines=ortho` does NOT render edge labels. The warning says "try xlabels" but the real fix is:

```dot
splines=polyline   # NOT ortho
```

Then use `xlabel=` (not `label=`) on edges for labels that render alongside polyline edges:

```dot
A -> B [xlabel="handoff", color="#34d399", penwidth=1.5];
```

### Text truncation in nodes

If node text gets cut off, increase `CELLPADDING` or use wider explicit `WIDTH` attributes on `<TD>` elements. Graphviz auto-sizes nodes but sometimes clips long text.

### Cluster subgraph styling

For boundary boxes (Server, Worker, etc.):

```dot
subgraph cluster_server {
    label="GL Runner Server — Control Plane";
    labeljust="l";
    style=dashed;
    color="#34d399";
    penwidth=1;
    fontcolor="#34d399";
    fontsize=12;
    bgcolor="#042f1e";
    // ... nodes inside
}
```

Use a very dark variant of the stroke color for `bgcolor` so it barely tints the background.

### Rank alignment

Force same-rank nodes:

```dot
{rank=same; NodeA; NodeB; NodeC;}
```

## Rendering Commands

```bash
# PNG at 150 DPI (good for docs/screenshots)
dot -Tpng -Gdpi=150 diagram.dot -o diagram.png

# SVG (scalable, good for web)
dot -Tsvg diagram.dot -o diagram.svg

# Higher DPI for print
dot -Tpng -Gdpi=300 diagram.dot -o diagram-hires.png
```

## Multi-Diagram Pattern

For complex systems, create separate `.dot` files per view:

- `[project]-architecture.dot` — high-level boundaries (for `architecture.md`)
- `[project]-design.dot` — plugged implementations showing concrete backends (for `design.md` / `implementation.md`)
- `[project]-ecosystem.dot` — dependency/layer view (for `architecture.md` ecosystem section)

The "plugged" design diagram shows the same structure as the architecture diagram but with concrete implementations wired in (e.g., `OrchestrationBackend` → `plugged: Prefect 3`, `ControlPlaneStore` → `plugged: PostgreSQL`).

## Converting HTML to PNG

See HTML → PNG Conversion above — this is the primary method.

## Operational Lessons (from iterative diagram work)

When applying many visual iterations in a repo worktree:

- Prefer editing one target file at a time and immediately verify with `git diff` before moving on.
- After scripted multi-file edits, always run a post-check to ensure no file was accidentally emptied or truncated.
- If shell utilities are missing (`find`, `sed`, `git` via PATH), use:
  - absolute binaries (for example `/usr/bin/git`), or
  - Python stdlib (`os.walk`, file reads/writes) as a reliable fallback.
- Re-render PNG after every meaningful HTML change; do not assume prior screenshots still represent current HTML.
- Never write `read_file` output back to disk directly. `read_file` returns line-number-prefixed lines (`N|...`) for display; if that content is written into `.html`, the page corrupts and headers/labels render incorrectly. Always strip prefixes before `write_file` (or read raw file content via Python/pathlib in terminal).
- When users report visual defects (off-center arrows, overlaps), treat coordinates as first-class data and realign by center points numerically.
- For review/debug loops, explicitly enumerate all intended arrows/flows in text before final screenshot export so semantic mistakes are caught before visual sign-off.
- For internal diagrams that should visually match an ecosystem companion diagram: standardize column widths, increase label/sub-label font sizes together, and route long return arrows outside boundaries before re-entering to avoid crossings.
- Keep arrowhead geometry consistent across all markers (same `markerWidth/markerHeight/refX/refY`), only changing color by flow type. Oversized heads make short arrows look broken.
- When a layer points into a bounded subsystem, terminate the incoming arrow at the boundary box first (for example, Surface Layer -> GL Runner Server boundary), not directly to an inner component unless explicitly required.
- If users report ambiguous flow ownership, provide an explicit arrow inventory (source -> destination list) and map each label to one concrete path in the SVG.
- If a diagram is for docs review and horizontal space is tight, prefer a stacked/multi-row legend over a single long row.
- Use one arrow color family throughout the diagram when the user wants semantic clarity over style variation; encode differences with line style and labels instead of multiple hues.
- For architecture diagrams, a surface layer that contains multiple consumer surfaces can be modeled with a single entry arrow into the GL Runner boundary when the user wants the boundary emphasized over each individual surface.
- When the control plane owns canonical state, show a direct Control Plane API -> ControlPlaneStore edge instead of implying persistence only through a helper or orchestration path.
- If a worker uses ConnectorClient and EventPublisher, draw them as runtime-owned downstream edges from ExecutionRuntime so the executor ownership is visually obvious.
- If docs need a clean split, keep architecture focused on role/description, design on the chosen tech stack and detailed contracts, and implementation on module layout / code-level rollout.
- If docs or diagrams name a helper like TenantResolver or SandboxRunner but the concept is really a behavior inside a larger boundary, collapse it back into the owning component instead of promoting it to a peer box.
- For GL Runner internal diagrams, make the surface layer arrow go to the GL Runner Server boundary when the goal is boundary emphasis, and show Control Plane API -> ControlPlaneStore directly when canonical state lives in the server.
- If the worker runtime calls external integrations or emits canonical events, draw explicit runtime -> ConnectorClient and runtime -> EventPublisher edges so ownership is obvious.
- If a legend is cramped, split it into multiple rows and move dashed-path notes onto their own row below the rest; if the note disappears, check that it is not clipped beneath the bottom legend rows.
- If docs reference stable asset filenames (for example `gl-runner-architecture-overview.png`), copy/sync the newly rendered PNG to the canonical filename immediately after export so markdown always reflects the latest HTML edits.
- When a team provides screenshot-based visual guidelines, extract them into a repo-local reference markdown (for example a `references/diagram-style-reference.md` file inside the skill), and point all diagram-related skills to that single source of truth. This keeps style updates consistent across authoring, review, and docs-alignment workflows.
- When reviewing docs that contain multiple diagrams, evaluate each diagram separately by artifact type (PNG, Mermaid, class/sequence diagram) and by intent. Do not blend feedback across distinct visuals in the same document.
- For paired diagrams (ecosystem + internal), keep surface-row labels and box names consistent across both views; if one row feels off, fix the box widths/centers numerically rather than by eye.
- If a middle surface box (for example an SDK box) looks too wide or too tall, make it match the neighboring boxes first, then re-center the arrows so the row reads as one band.
- For top-layer connectors, make arrowheads obvious; if a line can be misread as a divider, move the stroke to the boundary edge and thicken it slightly.
- Use the repo’s canonical surface names exactly as the docs and user feedback dictate (for example `GL Runner CLI`, not plain `CLI`) so the legend and labels stay aligned.
- When a lower row feels cramped, increase vertical gap between tiers before shrinking text; then re-render PNG and re-check the screenshot.
- For docs attached to Markdown, keep the PNG as the referenced asset and keep the HTML source beside it as the editable truth; do not point Markdown at SVG unless the repo explicitly wants SVG.
- If an older diagram asset is no longer referenced, delete it in the same pass so the docs cannot drift back to the stale file.
- When users ask for the "latest" diagram, regenerate the PNG from the latest HTML before claiming the branch is done and push the refreshed asset set together with the markdown refs.
- For GL Runner docs, the current pattern is HTML source + PNG export + deleted superseded SVG/PNG assets; treat that as the default workflow unless the user asks otherwise.
- For dense internal architecture diagrams, equalize sibling box sizes first, then reroute long connectors around boundaries so they do not cut through inner boxes.
- If a box title is long, prefer widening or rebalancing the row before shrinking typography; then add a little more vertical padding so title and subtitle do not feel cramped.
- When a connector crosses an inner box or makes the middle of the diagram feel busy, move the anchor points outward and re-center the row instead of accepting the crossing.
- For visual QA on diagram HTML, use browser inspection plus a rendered PNG check; text snapshots alone miss spacing and overlap problems.
- When a shared-store diagram needs the stores to read as "between" server and worker, prefer a simple Stores label plus two store boxes in the gap rather than a full nested Storage Layer box, unless the extra container clearly improves reading.
- If the stores are meant to sit between boundaries, keep them fully outside the green server/control region and verify that the rendered PNG shows zero overlap.
- If a middle-route arrow feels janky, simplify the connector first (straighten it or remove the extra helper leg) before moving more boxes.
- If the user asks whether Scheduler should trigger ExecutionRuntime, prefer the architecture-preserving path first: keep Scheduler in control-plane coordination and route execution through the worker/orchestration path unless the docs explicitly define a direct scheduler-to-runtime edge.
- When users ask for a direct dependency edge (for example Control Plane API -> ControlPlaneStore), keep it direct and remove any extra intermediate storage-layer bounding box unless the user explicitly wants that layer.
- If a straight connector can replace a routed/edge-hugging arrow, prefer the straight connector and shift the neighboring box slightly to create room instead of introducing a longer path.
- Standardize vertical breathing room across all bounded regions: if one layer’s top row and bottom row feel mismatched, adjust both layers together so the diagram reads as one system, not separate local fixes.
- In paired architecture/design diagrams, apply the same spacing logic to both files so the design view does not drift from the architecture view after local edits.

### Doc-role checklist for the GL Runner docs set

When a repo uses multiple related diagrams/doc pages, keep the intent separated like this:

- **Architecture**: abstract boundary view; show ownership, layers, and external boundaries, but avoid code/module inventory.
- **Design**: stack-aligned view; show the same boundary shape with the chosen v1 stack clearly pinned underneath it.
- **Implementation**: concrete defaults and rollout choices; this is where OSS stack, package layout, and code-level decisions belong.
- **Deployment**: operator-facing posture; keep it simpler than architecture/design and focus on where things run, what scales first, and what is managed vs self-hosted.

Use this quick decision rule during review:
- if a box explains **what boundary owns it**, keep it in architecture
- if it explains **which stack was chosen**, keep it in design
- if it explains **which package/service/library is actually used**, keep it in implementation
- if it explains **how it is deployed or sized**, keep it in deployment

If a diagram starts to read like a code inventory or infrastructure bill of materials, it is probably too detailed for architecture or design and should be collapsed or moved down a level.

skill_view(name="architecture-diagram", file_path="templates/template.html")
```

The template contains working examples of every component type (frontend, backend, database, cloud, security), arrow styles (standard, dashed, curved), security groups, region boundaries, and the legend — use it as your structural reference when generating diagrams.
