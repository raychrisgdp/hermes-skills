# Diagram Visual Review Rules

This file is the human-readable reference for the current GDP Labs visual-only diagram review checklist.

Canonical locations:

- repository: `gdp-labs-diagram/references/diagram-visual-review-rules.md`
- loaded local skill: `~/.config/opencode/skill/gdp-labs-diagram/references/diagram-visual-review-rules.md`

Use this file when reviewing rendered diagram artifacts for Docs, slides, and markdown attachments.

For diagram creation guidance (format choice, style defaults, export workflow), use `references/diagram-authoring-playbook.md`.

## Status Key

| Symbol | Meaning |
| :--- | :--- |
| 🟢 | Satisfied |
| 🟡 | Partial / needs review |
| 🔴 | Not satisfied |
| ⚪ | N/A |

## Why Some Diagrams Still Show Extra Whitespace

Most whitespace issues come from a combination of:

- fixed SVG canvas sizes that are larger than the actual occupied content
- header + wrapper padding that is still included in the screenshot
- split diagrams that do not use the full width or height of the canvas
- no automatic post-render crop step yet

So yes, there is a standardized way to evaluate fit:

1. Render `HTML -> PNG`.
2. Generate a Docs/slides fit-check PNG.
3. Run a margin report on the PNG.
4. If the margins are too large, either:
   - tighten the HTML/SVG layout, or
   - split the diagram, or
   - crop more aggressively in a future automation step.

Current margin heuristic:

- any margin above about `10%` of canvas width/height is suspicious and should be reviewed for `G1`

## Standardized Validation Workflow

### Setup

Required for the standard HTML/SVG workflow:

- `python3`
- Playwright Python package with Chromium available
- Pillow available for PNG analysis

Quick checks:

```bash
python3 -c "from playwright.sync_api import sync_playwright; print('playwright-ok')"
python3 -c "from PIL import Image; print('pillow-ok')"
```

### Helper Scripts

| Script | Purpose |
| :--- | :--- |
| `scripts/docs_fit_check.py` | create a standardized Docs/slides fit preview from a PNG |
| `scripts/png_margin_report.py` | report blank margins and content bounding box from a PNG |
| `scripts/svg_heuristics_report.py` | detect diagonal segments, title-zone crossings, likely text overflow, and some layout conflicts from HTML/SVG |

Run these from the `gdp-labs-diagram/` directory, or use absolute paths.

### Canonical Review Pipeline

1. Inspect HTML/SVG only if needed for diagnosis.
2. Render HTML to PNG.
3. Generate fit-check PNG:

```bash
python3 scripts/docs_fit_check.py /absolute/path/to/diagram.png
```

4. Run margin report:

```bash
python3 scripts/png_margin_report.py /absolute/path/to/diagram.png
```

5. Run SVG heuristics when useful:

```bash
python3 scripts/svg_heuristics_report.py /absolute/path/to/diagram.html
```

6. Validate `G1` from the fit-check PNG or an inserted Docs/slides screenshot when available.
7. Validate `G2-G9` from the rendered PNG at normal and zoomed inspection.
8. Use script output as supporting evidence, not as the final visual verdict.

Required two-pass scoring:

1. Composition pass: `G1`, `G2`, `G5`, `G6`, `G8`, `G9`.
2. Mechanical pass: `G3`, `G4`, `G7` with zoomed endpoint and boundary checks.

Do not call a diagram clean until both passes are complete.

## Visual-Only Rules

These rules are intentionally visual-only. They do not attempt to validate architecture truth or code correctness.

| Rule | Meaning | How To Validate | Auto-Fix vs Ask User |
| :--- | :--- | :--- | :--- |
| `G1` | **Fit readability and canvas efficiency**. At Docs/slides `Fit`, the smallest visible text must still be readable, and the canvas should not waste large blank margins that reduce useful content size. | Validate from the fit-check PNG or inserted Docs/slides screenshot. Use `png_margin_report.py` to flag suspicious blank margins. | Auto-fix by cropping, resizing, reducing low-value text, or splitting the diagram. Ask if the fix requires a real format tradeoff. |
| `G2` | **Header discipline and text economy**. Default is title-only header. No subtitle unless truly necessary. Optional eyebrow/pre-title only when it materially improves orientation. | Inspect the rendered PNG. Check whether the title is dominant and whether subtitles or extra support text are actually needed. | Auto-fix by removing subtitles/support text, wrapping titles, or widening the canvas. Ask only if the user explicitly wants an editorial/header-heavy style. |
| `G3` | **Connector geometry**. All connectors must be straight or orthogonal only. No diagonal or curved segments. | Inspect the rendered PNG and use `svg_heuristics_report.py` for diagonal-segment detection. | Auto-fix by rerouting orthogonally. Ask only if the user explicitly wants a non-standard visual style. |
| `G4` | **Connector anchoring and clearance**. Connectors must start and end on box or boundary edges, not in whitespace, and must not cut through boxes, titles, labels, legends, or box content. | Visually trace routes in the rendered PNG. Use `svg_heuristics_report.py` for title-zone and overlap clues. | Auto-fix by moving boxes and rerouting lines. Ask only if repeated layout attempts cannot avoid the conflict. |
| `G5` | **Arrow alignment and balance**. Branches should feel balanced, routes should avoid unnecessary bends/bulges/intersections, and boxes should be repositioned before accepting awkward routing. Split and rejoin geometry both matter. | Compare sibling branches, tee points, split symmetry, and merge symmetry in the rendered PNG. This is mostly a visual-composition judgment. | Auto-fix by rebalancing routes and moving boxes. Ask if the cleaner layout would materially change the storytelling split. |
| `G6` | **Color semantics and legend necessity**. The diagram should be understandable without a legend when possible. If different colors, dashed paths, or boundary styles are not self-evident, a legend is required. | Perform a cold-reader check on the rendered PNG. If meaning is not obvious, add a compact legend and re-check `G1`. | Auto-fix by simplifying colors or adding a compact legend. Ask if the choice is between richer semantic colors vs a simpler palette. |
| `G7` | **Boundary containment and internal padding**. Titles, nodes, and inner content must stay fully inside intended boxes with comfortable padding. Literal code/path/token text must either fit cleanly or move out of the node. | Inspect the rendered PNG. Use `svg_heuristics_report.py` for likely overflow warnings. | Auto-fix by widening nodes, moving boxes, shortening text, or using monospace for literal fragments. Ask only if shortening would lose meaning the user may care about. |
| `G8` | **Box alignment and rail/grid placement**. Sibling boxes should align and space consistently. Repeated actors, roles, or stages should sit on stable rails so routing stays clean. Node-to-node clearance must stay comfortable. | Inspect rows, columns, repeated actors, lane alignment, and node spacing in the rendered PNG. Heuristics can hint at collisions, but final judgment is visual. | Auto-fix by aligning boxes and standardizing spacing. Ask only if alignment would conflict with a user-requested narrative emphasis. |
| `G9` | **Flow direction consistency**. If arrows indicate flow/sequence, they must do so consistently. Missing arrowheads or mixed directional conventions are not allowed. | Inspect the rendered PNG. Verify that all important flows use consistent arrow language. | Auto-fix by adding or normalizing arrowheads and line styles. Ask only if the user explicitly wants a non-directional conceptual diagram. |

## Which Rules Are Script-Backed vs Visual

| Rule | Script-Backed? | Notes |
| :--- | :--- | :--- |
| `G1` | strong | fit-check + margin report |
| `G2` | visual | editorial judgment |
| `G3` | strong | diagonal check from SVG heuristics |
| `G4` | partial | heuristics help, but final judgment is visual |
| `G5` | visual | balance/elegance is still visual |
| `G6` | visual | cold-reader clarity is still visual |
| `G7` | partial | overflow heuristics help |
| `G8` | partial | placement still mostly visual |
| `G9` | visual | arrowhead consistency still mostly visual |

## Review Discipline

- Validate from the rendered artifact, not the raw HTML, unless diagnosing a source-level issue.
- When a user points out a defect, verify it visually before scoring it.
- Mark `🔴` only for directly visible defects.
- Mark `🟡` only when the issue is visible but arguable, acceptable for draft review, or polish-level.
- If the user provides a screenshot, treat that screenshot as source of truth for the current review pass.
- Connector endpoint rule: any start or end in whitespace is `G4` red.
- Connector anchoring rule: visibly off-center endpoint on a clearly centered target is at least `G4` yellow; escalate to red when it misses the edge entirely.
- Boundary-title rule: title crossing boundary stroke is `G7` red; visibly tight but inside is `G7` yellow.
- Branch-balance rule: for 1-to-2 or 1-to-3 splits, check tee symmetry and branch length balance explicitly when scoring `G5` and `G8`.
- Split-and-merge symmetry rule: if branches rejoin downstream, compare symmetry at both split and merge; large mismatch in bend count or merge geometry is at least `G5` yellow.
- Spacing rule: touching/overlapping nodes are `G8` red; near-touching stacks with poor breathing room are `G8` yellow.
- Report each finding as `Rule -> object -> defect -> severity`.
- Ignore browser/editor chrome such as selection handles, toolbar overlays, and temporary highlights.
