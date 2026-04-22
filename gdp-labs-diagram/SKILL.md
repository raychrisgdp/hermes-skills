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

Lean skill index for creating and validating GDP Labs diagrams.

This file is intentionally brief. Use the reference docs and scripts below as the source of truth for use-case-specific guidance.

## Canonical Source and Sync

- Treat `~/.config/opencode/skill/gdp-labs-diagram/` as the canonical local source of latest learned rules.
- Sync `hermes-skills` branches and PRs from local canonical content, not from stale branch snapshots.
- Keep version at `1.1` for iterative rule/process refinements.
- Do not modify unrelated OpenCode global config when updating this skill.

## Use-Case Entry Points

| Use Case | Format | Primary Reference | Typical Output |
| :--- | :--- | :--- | :--- |
| Polished architecture or topology figure | HTML/SVG | `references/diagram-authoring-playbook.md` | `.html` source + `.png` + `.fitcheck.png` |
| Runtime/lifecycle flow with strict visual control | HTML/SVG | `references/diagram-authoring-playbook.md` | `.html` source + `.png` + `.fitcheck.png` |
| Source-editable sequence/ER/simple flow | Mermaid | `references/diagram-authoring-playbook.md` | `.md` Mermaid source (+ optional rendered PNG) |
| Visual QA and acceptance scoring | N/A | `references/diagram-visual-review-rules.md` | `G1-G9` status + evidence list |

## Validation Source of Truth

- Use `references/diagram-visual-review-rules.md` for all `G1-G9` scoring.
- Use screenshot-first review when the user provides screenshots.
- Use mandatory two-pass scoring:
  1. Composition pass: `G1`, `G2`, `G5`, `G6`, `G8`, `G9`
  2. Mechanical pass: `G3`, `G4`, `G7`
- Report findings as: `Rule -> object -> defect -> severity`.

## Creation Source of Truth

- Use `references/diagram-authoring-playbook.md` for:
  - format selection by use case,
  - style system (color/connector/typography/layout defaults),
  - HTML/SVG and Mermaid authoring workflow,
  - anti-pattern checks before export.

## Script References

- `scripts/render_tight_png.py` - render HTML to tightly cropped PNG.
- `scripts/docs_fit_check.py` - create Docs/slides fit preview PNG.
- `scripts/png_margin_report.py` - measure blank margin usage.
- `scripts/svg_heuristics_report.py` - detect diagonal/title-zone/overflow heuristics.

## Templates

- `templates/sample-agent-workflow.md` - Mermaid sample with GDP Labs classDef mappings.

## Standard Execution Sequence

1. Pick the format and workflow from `references/diagram-authoring-playbook.md`.
2. Author or update diagram source (`.html` or Mermaid `.md`).
3. For HTML/SVG, render with `scripts/render_tight_png.py`.
4. Generate fit-check with `scripts/docs_fit_check.py`.
5. Run helper checks (`png_margin_report.py`, `svg_heuristics_report.py`) as supporting evidence.
6. Score with `references/diagram-visual-review-rules.md` and record findings.

## Scope Guardrails

- Keep this file as an index, not a duplicate of full rule text.
- Put detailed rules in `references/*.md` and deterministic checks in `scripts/*.py`.
