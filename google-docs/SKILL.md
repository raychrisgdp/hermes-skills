---
name: google-docs
description: Full create/edit/list/export for Google Docs with Markdown conversion. Supports headings, inline styles, bullets, tables, and cross-linking.
version: 3.0.0
required_credential_files:
  - path: ~/.hermes/google_token.json
    description: OAuth2 token (auto-refreshes)
  - path: ~/.hermes/google_client_secret.json
    description: OAuth2 client_secret.json from Google Cloud Console
---

# Google Docs

Create and manage Google Docs. Converts Markdown to native Google Docs using the **Drive Import API** (fast, reliable, preserves tables/tables) rather than the slow `batchUpdate` API.

## 📂 Scripts

| File | Purpose |
|---|---|
| `scripts/setup.py` | OAuth2 setup (check/auth-url/auth-code/revoke) |
| `scripts/docs_api.py` | CLI for list, get, create, update, append, find-replace, export |
| `scripts/docs_advanced.py` | Python API: `insert_table`, `insert_image`, etc. |
| `scripts/publish_pipeline.py` | **Multi-doc publishing**: Uploads a directory of Markdown files and fixes internal cross-links. |
| `scripts/md_converter.py` | Google Docs ↔ Markdown library |

## 🚀 Standard Workflow: Drive Import (Single File)

**Do not** use the Docs API (`batchUpdate`) to create a document from scratch line-by-line.
Instead, use the Drive API to upload Markdown as a file stream.

### Why Drive Import?
The Drive API (`files.create` with `mimeType: text/markdown`) **natively renders** complex Markdown formatting, including **Tables**, **Headings**, and **Code blocks**.
Using the standard Docs API to build a document from scratch requires manual row-by-row table construction and complex index math (tracking character offsets for every insertion/deletion), making it incredibly slow and error-prone.

### 1. Create Doc from Markdown
```python
import io
from googleapiclient.http import MediaIoBaseUpload

# 1. Read Markdown
with open("file.md", "r") as f:
    md_content = f.read()

# 2. Upload to Drive as Google Doc
file_metadata = {
    'name': "My Document Title",
    'mimeType': 'application/vnd.google-apps.document'
}
media = MediaIoBaseUpload(io.BytesIO(md_content.encode('utf-8')), mimetype='text/markdown', resumable=True)
file = drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
doc_id = file['id']
```

### 2. Update Doc In-Place (To preserve ID/Links)
To update an existing document without breaking links pointing to it:
1.  **Clear Content**: Delete range `1` to `endIndex - 1`.
2.  **Re-Insert**: Insert the new Markdown text at index `1`.
3.  *Note*: Drive formatting is applied on the first import. If updating, you may need the `docs_api.py` formatting pipeline to re-apply inline styles if the text is inserted via API.

## 🔄 Publishing Pipeline (Cross-Linked Docs)

When publishing multiple Markdown files (e.g., `design.md` linking to `implementation.md`), use this pipeline:

1.  **Scan**: Extract all relative Markdown links (e.g., `[Link](design.md)`).
2.  **Map**: Check Drive for existing Docs matching the filenames. Build `filename -> google_url` map.
3.  **Rewrite**: Replace relative links in the Markdown text with the Google Docs URLs.
4.  **Publish**: Import the rewritten Markdown via Drive Import API (see Standard Workflow above).
5.  **Verify**: Check `publish_pipeline.py` logs for success.

## 📝 Troubleshooting: Document Tabs vs Pages

**Important**: The Google Docs API **does not support** creating "Document Tabs" (the multi-tab UI feature introduced in 2024).
- **Attempted Solution**: `insertSectionBreak` creates distinct *pages* or *sections*, but does not create the top-level Tab UI.
- **Workaround**: Create separate Google Docs for each "tab" and use the **Publishing Pipeline** above to cross-link them.
- **Browser Automation**: Tools like Playwright *could* theoretically click the "+ Tab" UI button, but Google's CAPTCHA/bot detection usually blocks automated logins in cloud environments.

## 🛠️ Core Conversion Pipeline (API Fallback)

*Use this only if you cannot use Drive Import (e.g., editing specific text in an existing doc).*

1.  **Insert Text**: `insertText` at index 1.
2.  **Headings**: Batch `updateParagraphStyle` for `#` lines, then batch `deleteContentRange` for `# ` markers (high-to-low index).
3.  **Inline Styles**:
    -   Find markers: `**`, `*`, `[text](url)`, `~~`
    -   For each paragraph with markers, execute a **single** `batchUpdate`.
    -   Order: **Delete** closing markers first (highest index) → Delete opening markers → **Style** the text range.
    -   *Correction Logic*: Adjust style `startIndex` by subtracting the length of deleted markers that appeared *before* the style range.
4.  **Bullets**: Batch `createParagraphBullets` (sort high-to-low).
5.  **Tables**: `batchUpdate` -> `insertTable` -> Re-read doc -> `insertText` into cell `startIndex`.

## ⚠️ Known API Limitations

-   **Tabs**: The Google Docs REST API **does not support** creating "Document Tabs" (the UI feature introduced in 2024).
    -   *Note*: `insertSectionBreak` exists but only creates page breaks/sections, not Tabs in the UI.
    -   *Workaround*: Create **separate Google Docs** for each topic and use the **Publishing Pipeline** (below) to cross-link them.
    -   *Browser Automation*: Playwright *can* click the "+ Tab" button in the UI, but Google's bot detection usually blocks cloud-hosted browsers.
-   **Rate Limits**: `batchUpdate` is limited to **60 write requests/minute**.
-   **Numbered Lists**: API rejects `NUMBERED_*` bullet presets.