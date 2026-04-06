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
    from googleapiclient.discovery import build
    return build(api, version, credentials=get_credentials())

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
    
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    
    # Fill cells if data provided
    if data:
        # Re-read doc to get table position
        doc = docs.documents().get(documentId=doc_id).execute()
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
                        ).execute()
    
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

def insert_image(doc_id, image_path_or_url, start_index=None, width_pts=None, height_pts=None):
    """Insert an image into the document.
    
    Args:
        doc_id: The Google Doc ID
        image_path_or_url: Local file path or URL to image
        start_index: Index in document to insert at (default: end)
        width_pts: Width in points (optional)
        height_pts: Height in points (optional)
    """
    docs = build_service("docs", "v1")
    drive = build_service("drive", "v3")
    
    # Upload image to Drive first
    image_id = _upload_image_to_drive(drive, image_path_or_url)
    if not image_id:
        raise ValueError("Could not upload image")
    
    # Get insert position (end of doc if not specified)
    if start_index is None:
        doc = docs.documents().get(documentId=doc_id).execute()
        start_index = doc["body"]["content"][-1].get("endIndex", 1) - 1
    
    # Create inline image request
    # The image must be publicly accessible or shared with the Docs API.
    # We make it readable by "anyone with the link" first.
    drive.permissions().create(
        fileId=image_id,
        body={"type": "anyone", "role": "reader"},
        fields="id"
    ).execute()

    image_request = {
        "insertInlineImage": {
            "uri": f"https://drive.google.com/uc?id={image_id}",
            "location": {"index": start_index},
        }
    }
    if width_pts and height_pts:
        image_request["objectSize"] = {
            "width": {"magnitude": width_pts, "unit": "PT"},
            "height": {"magnitude": height_pts, "unit": "PT"},
        }
    
    docs.documents().batchUpdate(documentId=doc_id, body={
        "requests": [image_request]
    }).execute()
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
    media = MediaIoBaseUpload(image_data, mimetype="image/jpeg", resumable=True)
    
    result = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()
    
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
    ).execute()
    
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
    
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()


def append_paragraph(doc_id, text, heading=None, bullet=False):
    """Append a new paragraph to the end of the document."""
    docs = build_service("docs", "v1")
    
    # Find insert position (before last newline of last element)
    doc = docs.documents().get(documentId=doc_id).execute()
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
    
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
