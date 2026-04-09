#!/usr/bin/env python3
"""Google Docs API CLI for Hermes Agent.

Full create/edit/list/export Google Docs with Markdown conversion.
Uses OAuth2 token from ~/.hermes/google_token.json.

Usage:
  python3 docs_api.py list [--max 10] [--query "..."]
  python3 docs_api.py get  DOC_ID [--md] [--raw]
  python3 docs_api.py create TITLE [--md FILE]
  python3 docs_api.py update DOC_ID --md FILE
  python3 docs_api.py append DOC_ID --md FILE
  python3 docs_api.py replace DOC_ID --find "text" --with "replacement"
  python3 docs_api.py export DOC_ID [--format md|html|txt]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

HERMES_HOME = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))
TOKEN_PATH = HERMES_HOME / "google_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]


# ===========================================================
# Auth helpers
# ===========================================================

def get_credentials():
    """Load and auto-refresh credentials from token file."""
    if not TOKEN_PATH.exists():
        print("Not authenticated. Run setup first.", file=sys.stderr)
        sys.exit(1)
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())
    if not creds.valid:
        print("Token is invalid. Re-run setup.", file=sys.stderr)
        sys.exit(1)
    return creds


def build_service(api, version):
    """Build a Google API service with a longer HTTP timeout."""
    import httplib2
    from google_auth_httplib2 import AuthorizedHttp
    from googleapiclient.discovery import build

    http = AuthorizedHttp(get_credentials(), http=httplib2.Http(timeout=120))
    return build(api, version, http=http, cache_discovery=False)


# ===========================================================
# Markdown-to-Docs population — single-batch approach
#
# Strategy (3 batchUpdate calls total):
# 1. Insert all text with `insertText`.
# 2. Read the document to find exact paragraph positions, then:
#    a. Apply heading paragraph styles (HEADING_1 etc.)
#    b. Delete "# " prefix characters via deleteContentRange
#    (all in ONE batchUpdate call per operation - no per-paragraph
#    round-trips)
# ===========================================================

def _apply_heading_styles(doc_id):
    """Style paragraphs starting with #/##/### and delete prefixes.
    
    Two steps, each a single batchUpdate:
    1. updateParagraphStyle for each heading
    2. deleteContentRange for each # prefix, applied from highest
       index to lowest so earlier indices don't shift.
    """
    docs = build_service("docs", "v1")
    doc = docs.documents().get(documentId=doc_id).execute(num_retries=5)
    content = doc.get("body", {}).get("content", [])

    # ── Step 1: apply paragraph styles ───────────────────────
    style_reqs = []
    heading_items = []  # (start, plen) for later deletion

    for el in content:
        if "paragraph" not in el:
            continue
        para = el["paragraph"]
        text = "".join(e.get("textRun", {}).get("content", "")
                       for e in para.get("elements", []))

        level, plen = _heading_level_and_len(text)
        if level is None:
            continue

        s = el["startIndex"]
        e = el["endIndex"]
        style_reqs.append({
            "updateParagraphStyle": {
                "range": {"startIndex": s, "endIndex": e - 1},
                "paragraphStyle": {"namedStyleType": f"HEADING_{level}"},
                "fields": "namedStyleType",
            }
        })
        heading_items.append((s, plen))

    if style_reqs:
        docs.documents().batchUpdate(documentId=doc_id,
                                      body={"requests": style_reqs}).execute(num_retries=5)

    # ── Step 2: delete heading prefixes (reverse order) ──
    # Each delete runs individually to avoid index collisions, from
    # highest start index to lowest so earlier positions are stable.
    for start_pos, plen in sorted(heading_items, key=lambda x: x[0], reverse=True):
        docs.documents().batchUpdate(documentId=doc_id, body={
            "requests": [{
                "deleteContentRange": {
                    "range": {"startIndex": start_pos,
                              "endIndex": start_pos + plen}
                }
            }]
        }).execute(num_retries=5)


def _heading_level_and_len(text: str):
    """Return (heading_level:int, prefix_byte_len:int) or (None, 0)."""
    for level in range(6, 0, -1):
        prefix = "#" * level
        if text.startswith(prefix + " "):
            return level, len(prefix + " ")
    return None, 0


def _apply_bullets(doc_id):
    """Turn paragraphs starting with ``- `` / ``* `` / ``+ `` / ``1. `` into
    Doc bullets.  Handles simple (single-level) lists.

    Processes bullets in **reverse index order** (highest → lowest).
    """
    docs = build_service("docs", "v1")
    doc = docs.documents().get(documentId=doc_id).execute(num_retries=5)
    content = doc.get("body", {}).get("content", [])

    bullets = []  # (startIndex, endIndex-1, prefix_len)
    for el in content:
        if "paragraph" not in el:
            continue
        para = el["paragraph"]
        if para.get("bullet"):
            continue
        text = "".join(
            e.get("textRun", {}).get("content", "")
            for e in para.get("elements", [])
        )
        m = re.match(r'^[-*+]\s+', text)
        if not m:
            continue
        bullets.append((el["startIndex"], el["endIndex"] - 1, len(m.group(0))))
    # Sort highest index first
    bullets.sort(key=lambda x: x[0], reverse=True)

    requests = []
    for s, e, plen in bullets:
        requests.append({
            "deleteContentRange": {
                "range": {"startIndex": s, "endIndex": s + plen}
            }
        })
        requests.append({
            "createParagraphBullets": {
                "range": {"startIndex": s, "endIndex": e},
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
            }
        })

    if requests:
        docs.documents().batchUpdate(documentId=doc_id,
                                      body={"requests": requests}).execute(num_retries=5)


def _populate_document(doc_id, md_text, clear_first=True):
    """
    Insert markdown text into a doc.

    1. Optionally clear existing content.
    2. Insert all text with `insertText`.
    3. Apply heading styles + delete "# " prefixes.
    4. Apply bullet styles + delete "- " prefixes.
    5. Apply inline styles (bold/italic/code/links) + delete markers.
    """
    docs = build_service("docs", "v1")

    if clear_first:
        _clear_document(doc_id)

    # Insert all text at once.
    docs.documents().batchUpdate(documentId=doc_id, body={
        "requests": [{
            "insertText": {"location": {"index": 1}, "text": md_text}
        }]
    }).execute(num_retries=5)

    _apply_heading_styles(doc_id)
    _apply_inline_styles(doc_id)
    _apply_bullets(doc_id)


def _apply_inline_styles(doc_id):
    """Convert inline Markdown to Docs API text styles.

    Handles per paragraph:
      **bold** → textStyle.bold
      *italic* → textStyle.italic
      `code`  → Courier New + background
      ~~strike~~ → strikethrough
      [text](url) → hyperlink + underline

    Processes one paragraph at a time, re-reading the doc after each
    modification.  Safety-capped at 200 passes.
    """
    docs = build_service("docs", "v1")

    for _pass in range(200):
        found = False
        doc = docs.documents().get(documentId=doc_id).execute(num_retries=5)

        for el in doc.get("body", {}).get("content", []):
            if "paragraph" not in el:
                continue

            para = el["paragraph"]
            elements = para.get("elements", [])
            if not elements:
                continue

            # Skip HEADING paragraphs — their ** markers are intentional bold
            # heading text, not markdown to convert.
            nst = para.get("paragraphStyle", {}).get("namedStyleType", "")
            if nst.startswith("HEADING_"):
                continue

            full_text = "".join(e.get("textRun", {}).get("content", "") for e in elements)
            para_start = el["startIndex"]

            ops = _parse_inline_md(full_text)
            if not ops:
                continue

            found = True
            requests = []
            delete_ranges = []  # (abs_start, abs_end)

            for op in ops:
                kind = op[0]
                if kind in ("bold", "italic", "code", "strikethrough"):
                    # op = ("kind", start_rel, end_rel)
                    _, s_rel, e_rel = op
                    if kind in ("bold", "strikethrough"):
                        marker_len = 2
                    else:
                        marker_len = 1

                    ts = {}
                    fields = []
                    if kind == "bold":
                        ts = {"bold": True}
                        fields = ["bold"]
                    elif kind == "italic":
                        ts = {"italic": True}
                        fields = ["italic"]
                    elif kind == "code":
                        ts = {
                            "weightedFontFamily": {"fontFamily": "Courier New"},
                            "backgroundColor": {"color": {"rgbColor": {"red": 0.94, "green": 0.95, "blue": 0.96}}},
                        }
                        fields = ["weightedFontFamily", "backgroundColor"]
                    elif kind == "strikethrough":
                        ts = {"strikethrough": True}
                        fields = ["strikethrough"]

                    abs_s = para_start + s_rel + marker_len
                    abs_e = para_start + e_rel - marker_len
                    if abs_s < abs_e:
                        requests.append({
                            "updateTextStyle": {
                                "range": {"startIndex": abs_s, "endIndex": abs_e},
                                "textStyle": ts,
                                "fields": ",".join(fields),
                            }
                        })
                    # Record delete ranges (marker characters)
                    delete_ranges.append((para_start + s_rel, para_start + s_rel + marker_len))
                    delete_ranges.append((para_start + e_rel - marker_len, para_start + e_rel))

                elif kind == "link":
                    # op = ("link", link_text, url, m_start, m_end)
                    _, link_text, url, m_start, m_end = op
                    link_start_abs = para_start + m_start + 1  # after [
                    link_end_abs = link_start_abs + len(link_text)
                    suffix_end_abs = para_start + m_end

                    if link_start_abs < link_end_abs:
                        requests.append({
                            "updateTextStyle": {
                                "range": {"startIndex": link_start_abs, "endIndex": link_end_abs},
                                "textStyle": {"link": {"url": url}, "underline": True},
                                "fields": "link,underline",
                            }
                        })
                    delete_ranges.append((para_start + m_start, link_start_abs))  # [
                    delete_ranges.append((link_end_abs, suffix_end_abs))  # ](url)

            # Execute: delete markers right-to-left FIRST, then apply styles.
            # Markers must be removed before styling because updateTextStyle
            # splits the paragraph and shifts positions.
            if delete_ranges:
                delete_ranges.sort(key=lambda x: x[0], reverse=True)
                for ds, de in delete_ranges:
                    if ds < de:
                        docs.documents().batchUpdate(documentId=doc_id, body={
                            "requests": [{"deleteContentRange": {
                                "range": {"startIndex": ds, "endIndex": de}
                            }}]
                        }).execute(num_retries=5)

            # Re-read to get correct positions after deletes, then apply styles
            if requests:
                # Recalculate style ranges based on current doc structure
                doc2 = docs.documents().get(documentId=doc_id).execute(num_retries=5)
                for el2 in doc2.get("body", {}).get("content", []):
                    if "paragraph" not in el2:
                        continue
                    para2 = el2["paragraph"]
                    elements2 = para2.get("elements", [])
                    if not elements2:
                        continue
                    text2 = "".join(e.get("textRun", {}).get("content", "") for e in elements2)
                    ops2 = _parse_inline_md(text2)
                    if not ops2:
                        continue
                    para_start2 = el2["startIndex"]
                    style_reqs = []
                    for op2 in ops2:
                        kind2 = op2[0]
                        if kind2 in ("bold", "italic", "code", "strikethrough"):
                            _, s2, e2 = op2
                            if kind2 in ("bold", "strikethrough"): ml = 2
                            else: ml = 1
                            ts2 = {}
                            fields2 = []
                            if kind2 == "bold": ts2 = {"bold": True}; fields2 = ["bold"]
                            elif kind2 == "italic": ts2 = {"italic": True}; fields2 = ["italic"]
                            elif kind2 == "code":
                                ts2 = {"weightedFontFamily": {"fontFamily": "Courier New"},
                                       "backgroundColor": {"color": {"rgbColor": {"red": 0.94, "green": 0.95, "blue": 0.96}}}}
                                fields2 = ["weightedFontFamily", "backgroundColor"]
                            elif kind2 == "strikethrough": ts2 = {"strikethrough": True}; fields2 = ["strikethrough"]
                            a_s = para_start2 + s2 + ml
                            a_e = para_start2 + e2 - ml
                            if a_s < a_e:
                                style_reqs.append({
                                    "updateTextStyle": {
                                        "range": {"startIndex": a_s, "endIndex": a_e},
                                        "textStyle": ts2,
                                        "fields": ",".join(fields2),
                                    }
                                })
                        elif kind2 == "link":
                            _, lt, url2, ms2, me2 = op2
                            ls = para_start2 + ms2 + 1
                            le = ls + len(lt)
                            if ls < le:
                                style_reqs.append({
                                    "updateTextStyle": {
                                        "range": {"startIndex": ls, "endIndex": le},
                                        "textStyle": {"link": {"url": url2}, "underline": True},
                                        "fields": "link,underline",
                                    }
                                })
                    if style_reqs:
                        docs.documents().batchUpdate(documentId=doc_id,
                                                      body={"requests": style_reqs}).execute(num_retries=5)
                    break  # only process this paragraph

            break  # re-read doc after modifying one paragraph

        if not found:
            break


def _parse_inline_md(text: str):
    """Return list of (kind, ...) describing inline Markdown spans in *text*."""
    import re

    spans = []
    claimed = set()

    def _claim(start, end):
        for i in range(start, end):
            claimed.add(i)

    def _claimed(start, end):
        return any(i in claimed for i in range(start, end))

    # 1. Links: [text](url)
    for m in re.finditer(r'(?<!!)\[([^\]]+)\]\(([^)]+)\)', text):
        spans.append(("link", m.group(1), m.group(2), m.start(), m.end()))
        _claim(m.start(), m.end())

    # 2. Bold: **text**
    for m in re.finditer(r'[*][*](.+?)[*][*]', text):
        spans.append(("bold", m.start(), m.end()))
        _claim(m.start(), m.end())

    # 3. Code: `text`
    for m in re.finditer(r'`([^`]+)`', text):
        if not _claimed(m.start(), m.end()):
            spans.append(("code", m.start(), m.end()))
            _claim(m.start(), m.end())

    # 4. Italic: *text*  (skip if already claimed by bold)
    for m in re.finditer(r'[*](?![*])(.+?)(?<![*])[*]', text):
        if not _claimed(m.start(), m.end()) and len(m.group(1)):
            spans.append(("italic", m.start(), m.end()))
            _claim(m.start(), m.end())

    # 5. Strikethrough: ~~text~~
    for m in re.finditer(r'~~(.+?)~~', text):
        if not _claimed(m.start(), m.end()):
            spans.append(("strikethrough", m.start(), m.end()))
            _claim(m.start(), m.end())

    return spans


def _clear_document(doc_id):
    """Delete all paragraph content in a single batchUpdate call (reverse order)."""
    docs = build_service("docs", "v1")
    doc = docs.documents().get(documentId=doc_id).execute(num_retries=5)
    content = doc.get("body", {}).get("content", [])
    if len(content) <= 1:
        return
    del_reqs = []
    for el in reversed(content):
        if "paragraph" not in el:
            continue
        start = el.get("startIndex", 0)
        end = el.get("endIndex", 0)
        if end - start - 1 > 0:
            del_reqs.append({
                "deleteContentRange": {
                    "range": {"startIndex": start, "endIndex": end - 1}
                }
            })
    if del_reqs:
        docs.documents().batchUpdate(documentId=doc_id, body={
            "requests": del_reqs
        }).execute(num_retries=5)


# ===========================================================
# Doc ↔ Markdown conversion
# ===========================================================

def doc_to_markdown(doc: dict) -> str:
    """Convert a Google Docs document (from docs.documents().get()) to Markdown."""
    lines: list[str] = []
    for el in doc.get("body", {}).get("content", []):
        if "table" in el:
            lines.extend(_render_table(el["table"]))
        elif "paragraph" in el:
            lines.append(_render_paragraph(el["paragraph"]))
    return "\n".join(l for l in lines if l is not None)


def _render_paragraph(para: dict) -> str:
    style = para.get("paragraphStyle", {}).get("namedStyleType", "")
    heading = ""
    if style.startswith("HEADING_"):
        level = style.split("_")[1]
        heading = "#" * int(level) + " "

    bullet = para.get("bullet", {})
    bp = ""
    if bullet:
        indent = "  " * bullet.get("nestingLevel", 0)
        glyph = bullet.get("glyph", "")
        if re.match(r"^\d", glyph):
            bp = f"{indent}1. "
        else:
            bp = f"{indent}- "

    text = ""
    for pe in para.get("elements", []):
        tr = pe.get("textRun", {})
        c = tr.get("content", "").rstrip("\n")
        ts = tr.get("textStyle", {})
        c = _apply_md_styles(c, ts)
        text += c

    if heading:
        return heading + text.strip()
    elif bp:
        return bp + text.strip()
    else:
        return text


def _render_table(table: dict) -> list[str]:
    """Render a table element as a pipe-delimited Markdown table."""
    rows_raw: list[list[str]] = []
    for row in table.get("tableRows", []):
        cells = []
        for cell in row.get("tableCells", []):
            inner = ""
            for content in cell.get("content", []):
                if "paragraph" in content:
                    inner += _render_paragraph(content["paragraph"]).strip() + " "
            cells.append(inner.strip())
        rows_raw.append(cells)

    if not rows_raw:
        return []

    max_cols = max(len(r) for r in rows_raw)
    lines = []
    lines.append("| " + " | ".join(c.ljust(max_cols) for c in rows_raw[0]) + " |")
    lines.append("| " + " | ".join("---" for _ in range(max_cols)) + " |")
    for r in rows_raw[1:]:
        while len(r) < max_cols:
            r.append("")
        lines.append("| " + " | ".join(c.ljust(max_cols) for c in r) + " |")
    return lines


def _apply_md_styles(text: str, ts: dict) -> str:
    """Wrap text with Markdown based on its inline text style."""
    if not text:
        return text

    ff = ts.get("weightedFontFamily", {}).get("fontFamily", "")
    bg = ts.get("backgroundColor", {}).get("color", {}).get("rgbColor", {})
    if ff == "Courier New" or bg:
        text = f"`{text}`"

    if ts.get("strikethrough"):
        text = f"~~{text}~~"
    if ts.get("italic"):
        text = f"*{text}*"
    if ts.get("bold"):
        text = f"**{text}**"

    link = ts.get("link", {}).get("url")
    if link and not text.startswith("**") and not text.startswith("*"):
        text = f"[{text}]({link})"

    return text


# ===========================================================
# CLI commands
# ===========================================================

def docs_list(args):
    drive = build_service("drive", "v3")
    q = "mimeType='application/vnd.google-apps.document'"
    if args.query:
        q += f" and fullText contains '{args.query}'"
    results = drive.files().list(
        q=q, pageSize=args.max,
        fields="files(id, name, modifiedTime, webViewLink)",
        orderBy="modifiedTime desc"
    ).execute(num_retries=5)
    print(json.dumps(results.get("files", []), indent=2))


def docs_get(args):
    docs = build_service("docs", "v1")
    get_kwargs = {"documentId": args.doc_id}
    if getattr(args, "fields", None):
        get_kwargs["fields"] = args.fields
    doc = docs.documents().get(**get_kwargs).execute(num_retries=5)

    if args.raw:
        print(json.dumps(doc, indent=2))
        return

    if args.md:
        print(doc_to_markdown(doc))
        return

    lines = []
    for element in doc.get("body", {}).get("content", []):
        if "paragraph" in element:
            text = "".join(
                e.get("textRun", {}).get("content", "").rstrip("\n")
                for e in element["paragraph"].get("elements", [])
            )
            if text.strip():
                lines.append(text.strip())

    print(json.dumps({
        "title": doc.get("title", ""),
        "documentId": doc.get("documentId", ""),
        "content": "\n".join(lines),
    }, indent=2, ensure_ascii=False))


def docs_create(args):
    docs = build_service("docs", "v1")
    doc = docs.documents().create(body={"title": args.title}).execute(num_retries=5)
    doc_id = doc["documentId"]
    url = f"https://docs.google.com/document/d/{doc_id}/edit"

    populated = False
    if args.md:
        md_path = Path(args.md)
        if md_path.exists():
            _populate_document(doc_id, md_path.read_text(encoding="utf-8"))
            populated = True
        else:
            print(f"File not found: {args.md}", file=sys.stderr)
            sys.exit(1)

    print(json.dumps({
        "status": "created",
        "title": doc.get("title", ""),
        "documentId": doc_id,
        "url": url,
        "populated_from_markdown": populated,
    }, indent=2))


def docs_update(args):
    md_path = Path(args.md)
    if not md_path.exists():
        print(f"File not found: {args.md}", file=sys.stderr)
        sys.exit(1)
    _populate_document(args.doc_id, md_path.read_text(encoding="utf-8"))
    print(json.dumps({"status": "updated", "documentId": args.doc_id}, indent=2))


def docs_append(args):
    md_path = Path(args.md)
    if not md_path.exists():
        print(f"File not found: {args.md}", file=sys.stderr)
        sys.exit(1)
    docs = build_service("docs", "v1")
    doc = docs.documents().get(documentId=args.doc_id).execute(num_retries=5)
    content = doc.get("body", {}).get("content", [])
    insert_index = 1
    if content:
        last = content[-1]
        insert_index = last.get("endIndex", 1) - 1
    md_text = "\n" + md_path.read_text(encoding="utf-8")
    docs.documents().batchUpdate(documentId=args.doc_id, body={
        "requests": [{
            "insertText": {"location": {"index": insert_index}, "text": md_text}
        }]
    }).execute(num_retries=5)
    _apply_heading_styles(args.doc_id)
    _apply_bullets(args.doc_id)
    print(json.dumps({"status": "appended", "documentId": args.doc_id}, indent=2))


def docs_replace(args):
    docs = build_service("docs", "v1")
    result = docs.documents().batchUpdate(
        documentId=args.doc_id,
        body={"requests": [{
            "replaceAllText": {
                "containsText": {"text": args.find, "matchCase": True},
                "replaceText": args.with_text,
            }
        }]}
    ).execute(num_retries=5)
    occ = result["replies"][0].get("replaceAllText", {}).get("occurrencesChanged", 0)
    print(json.dumps({
        "status": "replaced",
        "documentId": args.doc_id,
        "occurrencesChanged": occ,
    }, indent=2))


def docs_export(args):
    drive = build_service("drive", "v3")
    mime_map = {"md": "text/markdown", "html": "text/html", "txt": "text/plain"}
    mime = mime_map.get(args.format or "md", "text/markdown")
    result = drive.files().export(fileId=args.doc_id, mimeType=mime).execute(num_retries=5)
    content = result.decode("utf-8") if isinstance(result, bytes) else str(result)
    print(content)


# ===========================================================
# CLI entry point
# ===========================================================

def main():
    parser = argparse.ArgumentParser(description="Google Docs API CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list")
    p.add_argument("--max", type=int, default=20)
    p.add_argument("--query", default="")
    p.set_defaults(func=docs_list)

    p = sub.add_parser("get")
    p.add_argument("doc_id")
    p.add_argument("--md", action="store_true", help="Output as Markdown")
    p.add_argument("--raw", action="store_true", help="Raw JSON from API")
    p.add_argument("--fields", help="Docs API fields selector for narrower reads")
    p.set_defaults(func=docs_get)

    p = sub.add_parser("create")
    p.add_argument("title")
    p.add_argument("--md", help="Markdown file path to populate doc")
    p.set_defaults(func=docs_create)

    p = sub.add_parser("update")
    p.add_argument("doc_id")
    p.add_argument("--md", required=True, help="Markdown file to replace doc content")
    p.set_defaults(func=docs_update)

    p = sub.add_parser("append")
    p.add_argument("doc_id")
    p.add_argument("--md", required=True, help="Markdown file to append")
    p.set_defaults(func=docs_append)

    p = sub.add_parser("replace")
    p.add_argument("doc_id")
    p.add_argument("--find", required=True, help="Text to find")
    p.add_argument("--with", dest="with_text", required=True, help="Replacement text")
    p.set_defaults(func=docs_replace)

    p = sub.add_parser("export")
    p.add_argument("doc_id")
    p.add_argument("--format", choices=["md", "html", "txt"], default="md")
    p.set_defaults(func=docs_export)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
