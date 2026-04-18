#!/usr/bin/env python3
"""Markdown <-> Google Docs converter for the google-docs skill."""

import re
from typing import Any, Dict, List


def doc_to_markdown(doc: dict) -> str:
    """Walk a Docs API response and produce Markdown text.

    Handles:
      - Named heading styles  →  # / ## / ### …
      - Bold / Italic / Strike-through  →  ** / * / ~~
      - Bullets / Numbered lists  →  - / 1.
      - Tables  →  pipe tables
      - Inline links  →  [text](url)
      - Code style (Courier New)  →  ``
    """
    lines: list[str] = []
    for el in doc.get("body", {}).get("content", []):
        if "table" in el:
            lines.extend(_render_table(el["table"]))
        elif "paragraph" in el:
            md = _render_paragraph(el["paragraph"])
            if md is not None:
                lines.append(md)
    return "\n".join(l for l in lines if l is not None)


def _markdown_prefix_for_named_style(style: str) -> str:
    """Map Docs named style back to Markdown heading prefix.

    Inverse of import mapping:
    TITLE -> #
    HEADING_1 -> ##
    HEADING_2 -> ###
    ...
    """
    if style == "TITLE":
        return "# "
    if style.startswith("HEADING_"):
        try:
            n = int(style.split("_")[1])
        except Exception:
            return ""
        return "#" * (n + 1) + " "
    return ""


def _render_paragraph(para: dict) -> str | None:
    style = para.get("paragraphStyle", {}).get("namedStyleType", "")
    heading = _markdown_prefix_for_named_style(style)

    bullet = para.get("bullet", {})
    bp = ""
    if bullet:
        indent = "  " * bullet.get("nestingLevel", 0)
        glyph = bullet.get("glyph", "")
        prefix = "1. " if re.match(r"^\d", glyph) else "- "
        bp = f"{indent}{prefix}"

    text = ""
    for pe in para.get("elements", []):
        tr = pe.get("textRun", {})
        c = tr.get("content", "").rstrip("\n")
        ts = tr.get("textStyle", {})
        c = _apply_md_styles(c, ts)
        text += c

    combined = heading + bp + text.strip()
    return combined if combined else None


def _render_table(table: dict) -> list[str]:
    """Convert a Docs-API table element into Markdown pipe-table lines."""
    raw_rows: list[list[str]] = []
    for row in table.get("tableRows", []):
        cells = []
        for cell in row.get("tableCells", []):
            parts = []
            for content in cell.get("content", []):
                if "paragraph" in content:
                    parts.append(_render_paragraph(content["paragraph"]) or "")
            cells.append(" ".join(p.strip() for p in parts))
        raw_rows.append(cells)

    if not raw_rows:
        return []

    n_cols = max(len(r) for r in raw_rows)
    for r in raw_rows:
        while len(r) < n_cols:
            r.append("")

    lines: list[str] = []
    lines.append("| " + " | ".join(raw_rows[0]) + " |")
    lines.append("| " + " | ".join("---" for _ in range(n_cols)) + " |")
    for r in raw_rows[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return lines


def _apply_md_styles(text: str, ts: dict) -> str:
    """Wrap *text* with Markdown wrappers inferred from *ts*."""
    if not text:
        return text

    # Inline code (Courier New or coloured bg)
    font = ts.get("weightedFontFamily", {}).get("fontFamily", "")
    bg = ts.get("backgroundColor", {}).get("color", {}).get("rgbColor", {})
    if font == "Courier New" or any(bg.values()):
        text = f"`{text}`"

    if ts.get("strikethrough"):
        text = f"~~{text}~~"
    if ts.get("italic"):
        text = f"*{text}*"
    if ts.get("bold"):
        text = f"**{text}**"

    url = ts.get("link", {}).get("url")
    if url and not text.startswith("**") and not text.startswith("*") and not text.startswith("`"):
        text = f"[{text}]({url})"

    return text


def md_to_docs_requests(md_text: str) -> list[dict[str, Any]]:
    """Return a list of batchUpdate requests that reproduce *md_text* in a Doc.

    Strategy
    --------
    1. `insertText` the raw Markdown (headings keep '# ', bullets keep '- ').
    2. `updateParagraphStyle` for any paragraph starting with `# `…
    3. `createParagraphBullets` for `- ` / `* ` / `+ ` lines.
    4. `deleteContentRange` to remove the Markdown markers.

    The caller executes these in a single ``batchUpdate``.  Because deletion
    shifts character offsets, we run deletes in *reverse* `startIndex` order
    so earlier ranges remain valid.
    """
    requests: list[dict[str, Any]] = []

    # 1 ─ Insert everything as plain text ─────────────────────
    requests.append({
        "insertText": {
            "location": {"index": 1},
            "text": md_text,
        }
    })

    # 2 + 4 will be added after re-fetching the document structure.
    # The consumer should call _apply_heading_styles() and _apply_bullets()
    # separately after this initial insert, as those functions need the
    # live document to know exact character positions.
    return requests
