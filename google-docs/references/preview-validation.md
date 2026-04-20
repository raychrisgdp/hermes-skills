# Preview Validation Rules

## Purpose
- Use these rules when validating a Google Docs preview rebuilt from Markdown.
- The goal is deterministic review: the preview should be source-faithful, readable, and free of layout accidents before it replaces a live shared doc.

## Rules

### R1: Source-driven preview
- Rebuild the preview from the current local Markdown source.
- Do not patch the preview manually in ways that diverge from source unless the change is a documented Docs-only formatting fix.

### R2: Heading mapping
- Omit the top-level Markdown `#` title from the body and treat it as the document title only.
- Map headings deterministically:
  - `##` -> `Heading 1`
  - `###` -> `Heading 2`
  - `####` -> `Heading 3`
  - continue similarly for deeper headings

### R3: Mermaid and asset transform
- Do not leave raw Mermaid fences in the Google Doc.
- Render Mermaid locally to PNG.
- Upload and insert diagrams and local assets as inline images.
- After rebuild, verify that no Mermaid fences or placeholder tokens remain.

### R4: Ordered lists only
- Preserve ordered lists from source as ordered lists in the preview.
- Do not introduce generic unordered bullets where the source expresses sequence, procedure, or numbered obligations.

### R5: Block placement and fit
- Center inline diagrams.
- Keep standalone tables and figures aligned cleanly with surrounding content.
- Do not let a figure or table create an avoidable blank page or a visibly broken text/figure split.

#### R5a: Diagram fit rule
- Oversized diagrams must be corrected before review is considered complete.
- Do not use one fixed insertion width for every diagram.
- Size each inserted diagram from its aspect ratio.
- Portrait defaults for inline diagrams:
  - max width: `440pt`
  - target max height: about `360pt`
- Landscape defaults for inline diagrams when landscape is already justified:
  - max width: `620pt`
  - target max height: about `420pt`
- If a diagram is too tall at portrait size, fix it in this order:
  1. change the source layout so the diagram is shorter, for example `flowchart LR` instead of `flowchart TD`
  2. reduce insertion width using aspect-ratio-aware sizing
  3. split the diagram into two diagrams if the logic is still readable that way
  4. use landscape only when width, not height, is the true readability constraint

### R6: Orientation must be justified
- Portrait is the default.
- Landscape is allowed only when portrait-first fitting still leaves a table or figure unreadable.
- Apply landscape to a dedicated section only.
- Restore portrait immediately after the justified landscape section.

### R7: No fully blank pages
- The exported PDF must not contain real blank pages.
- A trailing text-extraction artifact does not count as a real page.

### R8: Sparse pages require justification
- Sparse pages are acceptable only when they are a deliberate section-boundary tradeoff that preserves readability.
- If a sparse page exists, verify that removing it would require a worse failure such as unreadable landscape content, broken figure placement, or a merged section orientation.

### R9: Code blocks
- Code blocks should remain monospace.
- Normalize spacing so code does not look like broken prose paragraphs.

### R10: Default Google Docs style
- Use default Google Docs document styling unless a deliberate override is needed.
- Any override should serve readability or source fidelity, not decoration.

## Decision Matrix

### Orientation matrix

| Content type | Portrait-first action | When landscape is justified | Required follow-up |
| --- | --- | --- | --- |
| Normal prose section | Keep portrait | Never, unless the section contains a genuinely wide figure or table | None |
| Small or medium inline diagram | Fit within portrait sizing caps | Not justified if portrait remains readable | Keep centered |
| Tall flowchart | Shorten source layout first, then resize | Usually not justified; landscape does not solve height-driven overflow well | Prefer `LR` layout or split diagram |
| Wide matrix or cross-check table | Try portrait only if still readable | Justified when labels or columns become cramped or unreadable in portrait | Use dedicated landscape section and restore portrait after |
| Mixed section with one wide artifact | Keep surrounding prose portrait | Justified only for the artifact subsection | Surround with section breaks |

### Diagram sizing matrix

| Condition | Decision |
| --- | --- |
| Diagram fits portrait at `<= 440pt` wide and `<= 360pt` tall | Keep portrait and center it |
| Diagram is too tall but conceptually simple | Change source layout first, for example `TD` -> `LR` |
| Diagram is still tall after layout improvement | Reduce width using aspect-ratio-aware sizing |
| Diagram becomes too small to read after width reduction | Split the diagram or simplify labels |
| Diagram is wide rather than tall and remains unreadable in portrait | Put only that section in landscape |

### Sparse-page matrix

| Situation | Decision |
| --- | --- |
| Full blank page appears | Must fix |
| Sparse page caused by an oversized diagram | Fix the diagram sizing or source layout |
| Sparse page caused by justified section orientation change | Accept only if the next section genuinely needs that orientation |
| Sparse page caused by accidental page break or bad block placement | Must fix |

## Review checklist
- Source and preview match in structure and order.
- Heading promotion is correct.
- No raw Mermaid or placeholder tokens remain.
- Inline diagrams are centered and fit the page.
- Landscape appears only where justified and returns to portrait afterward.
- No real blank pages remain in the PDF export.
- Any sparse pages are explicitly justified.
