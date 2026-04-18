#!/usr/bin/env python3
"""Additional Docs API operations: tables, images, specific element-level edits."""
import os, re, json
from pathlib import Path

HERMES_HOME = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))
TOKEN_PATH = HERMES_HOME / "google_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]


def get_credentials():
    if not TOKEN_PATH.exists():
        raise FileNotFoundError("Not authenticated. Run setup first.")
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())
    if not creds.valid:
        raise ValueError("Token is invalid. Re-run setup.")
    return creds


def build_service(api, version):
    import httplib2
    from google_auth_httplib2 import AuthorizedHttp
    from googleapiclient.discovery import build

    http = AuthorizedHttp(get_credentials(), http=httplib2.Http(timeout=120))
    return build(api, version, http=http, cache_discovery=False)


def list_tabs(doc_id):
    """List all tabs in a Google Doc (id, title, index)."""
    docs = build_service("docs", "v1")
    resp = docs.documents().get(
        documentId=doc_id,
        fields="tabs(tabProperties(tabId,title,index,parentTabId,nestingLevel))",
    ).execute(num_retries=5)
    tabs = []
    for t in resp.get("tabs", []):
        p = t.get("tabProperties", {})
        tabs.append({
            "tab_id": p.get("tabId"),
            "title": p.get("title"),
            "index": p.get("index"),
            "parent_tab_id": p.get("parentTabId"),
            "nesting_level": p.get("nestingLevel"),
        })
    tabs.sort(key=lambda x: (x.get("index") if x.get("index") is not None else 10**9))
    return tabs


def add_document_tab(doc_id, title, index=None, parent_tab_id=None):
    """Add a new tab to an existing Google Doc."""
    docs = build_service("docs", "v1")
    props = {"title": title}
    if index is not None:
        props["index"] = int(index)
    if parent_tab_id:
        props["parentTabId"] = parent_tab_id

    docs.documents().batchUpdate(
        documentId=doc_id,
        body={
            "requests": [{
                "addDocumentTab": {
                    "tabProperties": props
                }
            }]
        }
    ).execute(num_retries=5)
    return list_tabs(doc_id)


def set_page_orientation(doc_id, landscape=True):
    """Set the document page size to portrait or landscape."""
    docs = build_service("docs", "v1")
    if landscape:
        page_size = {
            "width": {"magnitude": 792, "unit": "PT"},
            "height": {"magnitude": 612, "unit": "PT"},
        }
    else:
        page_size = {
            "width": {"magnitude": 612, "unit": "PT"},
            "height": {"magnitude": 792, "unit": "PT"},
        }
    docs.documents().batchUpdate(documentId=doc_id, body={
        "requests": [{
            "updateDocumentStyle": {
                "documentStyle": {"pageSize": page_size},
                "fields": "pageSize",
            }
        }]
    }).execute(num_retries=5)
    return True


def _get_tab_body_content(docs, doc_id, tab_id=None):
    """Return body.content for a specific tab (or first tab if omitted)."""
    if tab_id:
        resp = docs.documents().get(
            documentId=doc_id,
            includeTabsContent=True,
            fields="tabs(tabProperties(tabId,title,index),documentTab(body/content(startIndex,endIndex,paragraph,sectionBreak,table)))",
        ).execute(num_retries=5)
        for tab in resp.get("tabs", []):
            p = tab.get("tabProperties", {})
            if p.get("tabId") == tab_id:
                return tab.get("documentTab", {}).get("body", {}).get("content", [])
        raise ValueError(f"tab_id not found: {tab_id}")

    resp = docs.documents().get(
        documentId=doc_id,
        fields="body/content(startIndex,endIndex,paragraph,sectionBreak,table)",
    ).execute(num_retries=5)
    return resp.get("body", {}).get("content", [])


def _paragraph_bounds(body_content):
    """Return body paragraph ranges as (start_index, end_index)."""
    bounds = []
    for el in body_content:
        if "paragraph" not in el:
            continue
        start = el.get("startIndex")
        end = el.get("endIndex")
        if isinstance(start, int) and isinstance(end, int) and end > start:
            bounds.append((start, end))
    return bounds


def _find_start_anchor(paragraphs, start_index):
    """Snap start index to the start of containing paragraph."""
    for p_start, p_end in paragraphs:
        if p_start <= start_index < p_end:
            return p_start
    if start_index <= paragraphs[0][0]:
        return paragraphs[0][0]
    return paragraphs[-1][0]


def _find_end_anchor(paragraphs, end_index):
    """Snap end index to the end of containing paragraph (exclusive -> newline slot)."""
    for p_start, p_end in paragraphs:
        if p_start < end_index <= p_end:
            return max(p_start + 1, p_end - 1)
    if end_index <= paragraphs[0][0]:
        return max(paragraphs[0][0] + 1, paragraphs[0][1] - 1)
    return max(paragraphs[-1][0] + 1, paragraphs[-1][1] - 1)


def suggest_orientation_for_range(doc_id, start_index, end_index, tab_id=None, long_line_threshold=120):
    """Heuristic orientation suggestion for a content range.

    Returns landscape=True when the range appears width-heavy (tables, images,
    or very long paragraphs). Otherwise recommends portrait.
    """
    docs = build_service("docs", "v1")
    body_content = _get_tab_body_content(docs, doc_id, tab_id=tab_id)

    max_para_len = 0
    has_table = False
    has_inline_image = False

    for el in body_content:
        s = el.get("startIndex")
        e = el.get("endIndex")
        if not isinstance(s, int) or not isinstance(e, int):
            continue
        if e <= start_index or s >= end_index:
            continue

        if "table" in el:
            has_table = True

        para = el.get("paragraph")
        if para:
            text = "".join(
                p.get("textRun", {}).get("content", "")
                for p in para.get("elements", [])
            )
            max_para_len = max(max_para_len, len(text.strip()))
            for p in para.get("elements", []):
                if p.get("inlineObjectElement", {}).get("inlineObjectId"):
                    has_inline_image = True

    landscape = bool(has_table or has_inline_image or max_para_len >= int(long_line_threshold))
    return {
        "landscape": landscape,
        "signals": {
            "has_table": has_table,
            "has_inline_image": has_inline_image,
            "max_paragraph_chars": max_para_len,
            "long_line_threshold": int(long_line_threshold),
        },
    }


def set_section_orientation(doc_id, start_index, end_index, landscape=True, tab_id=None, snap_to_paragraph=True):
    """Set page orientation for a selected body range by isolating it in a section.

    This mimics the Google Docs UI flow for "Selected content":
    1) insert section break at selection end
    2) insert section break at selection start
    3) set SectionStyle.flipPageOrientation on the isolated section

    Args:
        doc_id: Google Doc ID
        start_index: selection start index in document body
        end_index: selection end index in document body
        landscape: True for landscape, False for portrait
        tab_id: target tab id (required for deterministic multi-tab behavior)
        snap_to_paragraph: snap indices to paragraph-safe boundaries

    Returns:
        dict with anchors and applied orientation metadata.
    """
    if not isinstance(start_index, int) or not isinstance(end_index, int):
        raise TypeError("start_index and end_index must be integers")
    if start_index >= end_index:
        raise ValueError("start_index must be < end_index")

    docs = build_service("docs", "v1")
    body_content = _get_tab_body_content(docs, doc_id, tab_id=tab_id)
    paragraphs = _paragraph_bounds(body_content)
    if not paragraphs:
        raise ValueError("No body paragraphs found; cannot insert section breaks")

    if snap_to_paragraph:
        start_anchor = _find_start_anchor(paragraphs, start_index)
        end_anchor = _find_end_anchor(paragraphs, end_index)
    else:
        start_anchor, end_anchor = start_index, end_index

    if start_anchor >= end_anchor:
        raise ValueError("Selection is too narrow after snapping to paragraph bounds")

    def _loc(idx):
        loc = {"index": idx}
        if tab_id:
            loc["tabId"] = tab_id
        return loc

    # Insert end break first so start anchor remains stable.
    docs.documents().batchUpdate(documentId=doc_id, body={
        "requests": [{
            "insertSectionBreak": {
                "location": _loc(end_anchor),
                "sectionType": "CONTINUOUS",
            }
        }]
    }).execute(num_retries=5)

    docs.documents().batchUpdate(documentId=doc_id, body={
        "requests": [{
            "insertSectionBreak": {
                "location": _loc(start_anchor),
                "sectionType": "CONTINUOUS",
            }
        }]
    }).execute(num_retries=5)

    # Re-fetch and target the section immediately after the start break.
    body_content_2 = _get_tab_body_content(docs, doc_id, tab_id=tab_id)
    section_breaks = [el for el in body_content_2 if "sectionBreak" in el]
    if not section_breaks:
        raise ValueError("No section breaks found after insertion")

    start_break = None
    for el in section_breaks:
        s = el.get("startIndex")
        if isinstance(s, int) and s >= start_anchor:
            start_break = el
            break
    if start_break is None:
        start_break = section_breaks[-1]

    target_start = start_break.get("endIndex")
    if not isinstance(target_start, int):
        raise ValueError("Could not resolve target section start index")

    target_end = None
    start_break_start = start_break.get("startIndex", -1)
    for el in section_breaks:
        s = el.get("startIndex")
        if isinstance(s, int) and s > start_break_start:
            target_end = s
            break

    if target_end is None or target_end <= target_start:
        body_end = body_content_2[-1].get("endIndex", target_start + 1)
        target_end = max(target_start + 1, body_end - 1)

    rng = {
        "startIndex": target_start,
        "endIndex": target_end,
    }
    if tab_id:
        rng["tabId"] = tab_id

    docs.documents().batchUpdate(documentId=doc_id, body={
        "requests": [{
            "updateSectionStyle": {
                "range": rng,
                "sectionStyle": {
                    "flipPageOrientation": bool(landscape)
                },
                "fields": "flipPageOrientation",
            }
        }]
    }).execute(num_retries=5)

    return {
        "start_anchor": start_anchor,
        "end_anchor": end_anchor,
        "target_start": target_start,
        "target_end": target_end,
        "landscape": bool(landscape),
        "tab_id": tab_id,
    }


def set_section_orientation_auto(doc_id, start_index, end_index, tab_id=None, long_line_threshold=120, snap_to_paragraph=True):
    """Auto-detect orientation for a selected range, then apply it."""
    decision = suggest_orientation_for_range(
        doc_id,
        start_index,
        end_index,
        tab_id=tab_id,
        long_line_threshold=long_line_threshold,
    )
    applied = set_section_orientation(
        doc_id,
        start_index,
        end_index,
        landscape=decision["landscape"],
        tab_id=tab_id,
        snap_to_paragraph=snap_to_paragraph,
    )
    return {
        "decision": decision,
        "applied": applied,
    }

# ===============================================================
# Tables
# ===============================================================

def insert_table(doc_id, start_index, rows, cols, data=None):
    """Insert a table at *start_index*.  Optional 2D list *data* fills cells.
    
    data[i][j] may be a string or a list of (text, style_dict) tuples.
    """
    docs = build_service("docs", "v1")
    
    requests = [{
        "insertTable": {
            "rows": rows,
            "columns": cols,
            "location": {"index": start_index}
        }
    }]
    
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute(num_retries=5)
    
    # Fill cells if data provided
    if data:
        # Re-read doc to get table position
        doc = docs.documents().get(documentId=doc_id).execute(num_retries=5)
        table_el = None
        for el in doc["body"]["content"]:
            if "table" in el:
                table_el = el["table"]
                break
        
        if table_el:
            # startIndex lives on the outer element, not in the "table" dict.
            # We find it by locating the element in the content list.
            table_start = None
            for el_idx, el in enumerate(doc["body"]["content"]):
                if "table" in el:
                    table_start = el.get("startIndex")
                    break
            if table_start is None:
                raise ValueError("Could not determine table start position in document")
            for r, row_data in enumerate(data):
                for c, cell_text in enumerate(row_data):
                    cell_reqs = _make_cell_fill_requests(
                        table_start, r, c, cell_text
                    )
                    if cell_reqs:
                        docs.documents().batchUpdate(
                            documentId=doc_id,
                            body={"requests": cell_reqs}
                        ).execute(num_retries=5)
    
    return True


def _make_cell_fill_requests(table_start, row, col, cell_text):
    """Build requests to insert text into a specific table cell."""
    requests = []
    
    if isinstance(cell_text, str):
        text = cell_text
        style = None
    elif isinstance(cell_text, (list, tuple)):
        # Could be [(text, style), ...] or just [text]
        if len(cell_text) > 0 and isinstance(cell_text[0], tuple):
            # Multiple styled segments
            full = ""
            for seg_text, seg_style in cell_text:
                full += seg_text
            text = full
            style = None  # complex — skip for now
        else:
            text = str(cell_text[0])
            style = None
    else:
        text = str(cell_text)
        style = None
    
    # Insert text at cell start
    if text:
        # Approximate cell position: each row+col offset is ~2
        # This is approximate; exact cell positions require parsing the table structure
        cell_offset = 1 + (row * 2) + (col * 2) + 1
        requests.append({
            "insertText": {
                "location": {"index": table_start + cell_offset},
                "text": text
            }
        })
    
    return requests


# ===============================================================
# Images
# ===============================================================

def insert_image(doc_id, image_path_or_url, start_index=None, width_pts=None, height_pts=None, share_publicly=True, tab_id=None, center=True):
    """Insert an image into the document.

    Images are centered by default to keep diagram placement consistent.

    Args:
        doc_id: Document ID
        image_path_or_url: Local path or URL to image
        start_index: Index in document to insert at (default: end of target tab)
        width_pts: Desired display width in points (optional). If set, the image is resized before upload.
        height_pts: Desired display height in points (optional). If set with width_pts, the image is resized before upload.
        tab_id: Optional target tab ID for multi-tab docs
        center: Center-align the paragraph containing the inserted image (default: True)
    """
    import io
    from googleapiclient.http import MediaIoBaseUpload
    from PIL import Image
    docs = build_service("docs", "v1")
    drive = build_service("drive", "v3")

    def _resize_for_docs(src_path_or_url):
        """Return a BytesIO + filename after optional point-based resize."""
        # Load image bytes first
        if src_path_or_url.startswith(("http://", "https://")):
            import urllib.request
            with urllib.request.urlopen(src_path_or_url) as response:
                raw = response.read()
            filename = os.path.basename(src_path_or_url.split("?")[0]) or "image.png"
        else:
            with open(src_path_or_url, "rb") as f:
                raw = f.read()
            filename = os.path.basename(src_path_or_url)

        buf = io.BytesIO(raw)
        if width_pts or height_pts:
            im = Image.open(buf)
            im.load()
            src_w, src_h = im.size
            target_w_px = None
            target_h_px = None
            if width_pts:
                target_w_px = max(1, round(width_pts * 96 / 72))
            if height_pts:
                target_h_px = max(1, round(height_pts * 96 / 72))
            if target_w_px and target_h_px:
                new_size = (target_w_px, target_h_px)
            elif target_w_px:
                new_size = (target_w_px, max(1, round(src_h * (target_w_px / src_w))))
            elif target_h_px:
                new_size = (max(1, round(src_w * (target_h_px / src_h))), target_h_px)
            else:
                new_size = im.size
            if new_size != im.size:
                im = im.resize(new_size, Image.Resampling.LANCZOS)
            out = io.BytesIO()
            ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else 'png'
            if ext in ('jpg', 'jpeg'):
                im = im.convert('RGB')
                im.save(out, format='JPEG', quality=95, optimize=True)
                filename = filename.rsplit('.', 1)[0] + '.jpg'
            else:
                im.save(out, format='PNG', optimize=True)
                if not filename.lower().endswith('.png'):
                    filename = filename.rsplit('.', 1)[0] + '.png'
            out.seek(0)
            return out, filename
        buf.seek(0)
        return buf, filename

    image_data, filename = _resize_for_docs(image_path_or_url)

    # Upload image to Drive first
    file_metadata = {"name": filename}
    mimetype = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
    media = MediaIoBaseUpload(image_data, mimetype=mimetype, resumable=True)
    result = drive.files().create(body=file_metadata, media_body=media, fields="id,webContentLink,thumbnailLink").execute(num_retries=5)
    image_id = result["id"]
    image_uri = result.get("webContentLink") or result.get("thumbnailLink")
    if not image_id:
        raise ValueError("Could not upload image")
    if not image_uri:
        raise ValueError("Could not determine a publicly accessible image URI")

    # Get insert position (end of target tab if not specified)
    if start_index is None:
        content = _get_tab_body_content(docs, doc_id, tab_id=tab_id)
        start_index = content[-1].get("endIndex", 1) - 1

    if share_publicly:
        drive.permissions().create(
            fileId=image_id,
            body={"type": "anyone", "role": "reader"},
            fields="id"
        ).execute(num_retries=5)

    location = {"index": start_index}
    if tab_id:
        location["tabId"] = tab_id

    requests = [{
        "insertInlineImage": {
            "uri": image_uri,
            "location": location,
        }
    }]

    if center:
        para_range = {
            "startIndex": start_index,
            "endIndex": start_index + 1,
        }
        if tab_id:
            para_range["tabId"] = tab_id
        requests.append({
            "updateParagraphStyle": {
                "range": para_range,
                "paragraphStyle": {"alignment": "CENTER"},
                "fields": "alignment",
            }
        })

    docs.documents().batchUpdate(documentId=doc_id, body={
        "requests": requests
    }).execute(num_retries=5)
    return True


def _upload_image_to_drive(drive_service, image_path_or_url):
    """Upload an image file to Google Drive and return its file ID."""
    import io
    from googleapiclient.http import MediaIoBaseUpload
    
    if image_path_or_url.startswith(("http://", "https://")):
        # Download from URL
        import urllib.request
        with urllib.request.urlopen(image_path_or_url) as response:
            image_data = io.BytesIO(response.read())
        filename = os.path.basename(image_path_or_url.split("?")[0]) or "image.jpg"
    else:
        # Local file
        with open(image_path_or_url, "rb") as f:
            image_data = io.BytesIO(f.read())
        filename = os.path.basename(image_path_or_url)
    
    file_metadata = {"name": filename}
    mimetype = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
    media = MediaIoBaseUpload(image_data, mimetype=mimetype, resumable=True)
    
    result = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute(num_retries=5)
    
    return result["id"]


# ===============================================================
# Specific element operations
# ===============================================================

def replace_text(doc_id, find_text, replace_text, match_case=True):
    """Replace all occurrences of *find_text* with *replace_text*."""
    docs = build_service("docs", "v1")
    
    result = docs.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": [{
            "replaceAllText": {
                "containsText": {"text": find_text, "matchCase": match_case},
                "replaceText": replace_text,
            }
        }]}
    ).execute(num_retries=5)
    
    occ = result["replies"][0].get("replaceAllText", {}).get("occurrencesChanged", 0)
    return occ


def insert_text_at(doc_id, index, text, style=None):
    """Insert text at a specific index, optionally with style."""
    docs = build_service("docs", "v1")
    
    requests = [{
        "insertText": {
            "location": {"index": index},
            "text": text,
        }
    }]
    
    if style:
        text_end = index + len(text)
        requests.append({
            "updateTextStyle": {
                "range": {"startIndex": index, "endIndex": text_end},
                "textStyle": style,
                "fields": ",".join(style.keys()),
            }
        })
    
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute(num_retries=5)


def append_paragraph(doc_id, text, heading=None, bullet=False):
    """Append a new paragraph to the end of the document."""
    docs = build_service("docs", "v1")
    
    # Find insert position (before last newline of last element)
    doc = docs.documents().get(documentId=doc_id).execute(num_retries=5)
    content = doc["body"]["content"]
    insert_index = content[-1].get("endIndex", 1) - 1
    
    text_with_newline = text + "\n"
    requests = [{
        "insertText": {
            "location": {"index": insert_index},
            "text": text_with_newline,
        }
    }]
    
    if heading:
        # Apply heading style
        level_map = {1: "HEADING_1", 2: "HEADING_2", 3: "HEADING_3",
                    4: "HEADING_4", 5: "HEADING_5", 6: "HEADING_6"}
        style_name = level_map.get(heading, "NORMAL_TEXT")
        requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": insert_index, "endIndex": insert_index + len(text)},
                "paragraphStyle": {"namedStyleType": style_name},
                "fields": "namedStyleType",
            }
        })
    
    if bullet:
        requests.append({
            "createParagraphBullets": {
                "range": {"startIndex": insert_index, "endIndex": insert_index + len(text)},
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
            }
        })
    
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute(num_retries=5)
