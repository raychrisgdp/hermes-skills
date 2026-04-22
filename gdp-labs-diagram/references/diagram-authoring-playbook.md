# Diagram Authoring Playbook

Use this guide when creating or revising GDP Labs diagrams.

For validation and scoring, use `references/diagram-visual-review-rules.md`.

## 1) Choose Format by Use Case

| Intent | Preferred Format | Why |
| :--- | :--- | :--- |
| Presentation-grade architecture/topology | HTML/SVG | deterministic layout, precise routing, clean PNG export |
| Runtime/lifecycle flow with strict geometry | HTML/SVG | orthogonal routing and anchor control |
| Sequence or compact conceptual flow | Mermaid | easier source editing in docs |
| ER/state diagrams | Mermaid | concise syntax and maintainability |

Rule: if you keep fighting Mermaid layout, switch to HTML/SVG.

## 2) HTML/SVG Authoring Defaults

### Base structure

- White background, no viewport-driven responsive behavior.
- Use static canvas sizing and `display: inline-block` for clean screenshots.
- Prefer title-only header unless subtitle materially improves clarity.

### Color system

Process nodes default to Sky Blue (`#00A0DF`) with white text. Use overrides only for clear meaning:

- terminal: Navy Dark (`#1A3F6F`)
- human gate: Charcoal (`#1A202C`)
- error path: Pink (`#CA54B0`)
- emphasis (limited): Navy (`#306FB7`)
- inactive/store: Light Gray (`#E8EEF4`) with dark text

Container tints use semantic group colors (blue/green/amber/purple/rose/gray).

### Connectors

- Orthogonal or straight only. No diagonal/curved routes.
- Endpoints must start/end on valid edges (never whitespace).
- Keep branch split and rejoin geometry visually balanced.
- Keep readable connector shafts; avoid arrowhead-only stubs.

### Layout

- Node radius: `rx=12`; container radius: square by default.
- Horizontal sibling gap: at least 40px.
- Node-to-node clearance: at least 20px.
- Repeated roles should align to stable rails.
- If two nodes touch or overlap, re-space before polish.

## 3) Mermaid Authoring Defaults

Use `templates/sample-agent-workflow.md` for classDef baseline.

Compatibility rules:

- no `%%{init:...}%%` blocks,
- no HTML tags in labels,
- keep edge labels short,
- avoid deep nested subgraphs.

## 4) Creation Workflow (HTML/SVG)

From the diagram directory:

```bash
python3 scripts/render_tight_png.py /absolute/path/to/diagram.html --out /absolute/path/to/diagram.png
python3 scripts/docs_fit_check.py /absolute/path/to/diagram.png --out /absolute/path/to/diagram.fitcheck.png
python3 scripts/png_margin_report.py /absolute/path/to/diagram.png
python3 scripts/svg_heuristics_report.py /absolute/path/to/diagram.html
```

Notes:

- helper scripts are support evidence, not final visual verdict,
- final quality judgment comes from rendered PNG and fit-check inspection.

## 5) Pre-Validation Authoring Checklist

- format matches use case,
- title/readability sized for Docs/slides fit,
- no diagonal/curved connectors,
- no whitespace endpoint anchors,
- split and merge symmetry checked,
- no touching/overlapping nodes,
- exported PNG and fit-check regenerated in same pass.
