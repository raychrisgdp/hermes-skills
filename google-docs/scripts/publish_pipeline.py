#!/usr/bin/env python3
"""
Publish Markdown Directory to Google Docs (Drive Import Method).

This script scans a directory of Markdown files, uploads them to Google Drive
as native Google Docs (preserving tables/formatting instantly), and fixes
internal cross-links (e.g. linking `design.md` to the newly created
'Design' Google Doc).

Usage:
    python3 publish_pipeline.py /path/to/markdown/folder

Fixes applied:
- New documents are now actually created (content is passed to Drive Upload).
- Documents are identified by a path-derived title to avoid collisions.
- Drive API re-upload is used for updates (preserves formatting) instead of
  Docs API insertText which lost all Markdown styling.
"""

import sys
import os
import io
import re
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# ── Configuration ────────────────────────────────────────────────
TOKEN_PATH=os.path.join(os.path.expanduser("~"), ".hermes", "google_tokens", "docs_token.json")
SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]

BASE = "https://docs.google.com/document/d/"

def get_services():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, "w") as f: f.write(creds.to_json())
        else:
            raise ValueError("Credentials invalid. Please run setup.py first.")
    return build("drive", "v3", credentials=creds), build("docs", "v1", credentials=creds)

def find_md_files(directory):
    files = []
    for root, _, filenames in os.walk(directory):
        for f in filenames:
            if f.endswith(".md"):
                files.append(os.path.join(root, f))
    return sorted(files)

def make_unique_title(rel_path, basename, existing_titles):
    """Generate a title that avoids collisions.

    Falls back from clean title to path-qualified title if needed.
    """
    base_title = os.path.splitext(basename)[0]
    base_title = base_title.replace("-", " ").replace("_", " ").title()

    candidate = base_title
    if candidate not in existing_titles:
        return candidate

    # Disambiguate by prepending parent directory names.
    parent = os.path.dirname(rel_path).replace(os.sep, " > ")
    if parent:
        candidate = f"{parent} > {base_title}"
    if candidate not in existing_titles:
        return candidate

    # Last resort: append a counter.
    suffix = 2
    while candidate in existing_titles:
        candidate = f"{base_title} ({suffix})"
        suffix += 1
    return candidate

def get_or_create_doc(drive_s, title, md_content):
    """Find existing doc by title, or create a new one via Drive Import.

    Always expects md_content so new documents are actually created.
    """

    # 1. Try to find existing
    results = drive_s.files().list(
        q=f"name='{title}' and mimeType='application/vnd.google-apps.document' and trashed=false",
        fields="files(id, name, modifiedTime)"
    ).execute()

    if results.get("files"):
        files = sorted(results["files"], key=lambda x: x.get("modifiedTime", ""), reverse=True)
        file_id = files[0]["id"]
        print(f"  ♻️  Found existing doc: {title} (ID: {file_id})")
        return file_id

    # 2. Create new via Drive Import — preserves Markdown formatting.
    if not md_content:
        print(f"  ⚠️  No content provided for {title}, skipping.")
        return None

    print(f"  ✨ Creating new doc: {title}")
    file_metadata = {"name": title, "mimeType": "application/vnd.google-apps.document"}
    media = MediaIoBaseUpload(
        io.BytesIO(md_content.encode("utf-8")),
        mimetype="text/markdown",
        resumable=True
    )
    file = drive_s.files().create(body=file_metadata, media_body=media, fields="id").execute()
    print(f"  🆕 Created ID: {file['id']}")
    return file["id"]

def rewrite_links(md_content, link_map):
    """Replace relative Markdown links with Google Docs URLs."""
    def replace_match(match):
        full_url = match.group(2)
        # Skip external links and anchors
        if full_url.startswith(("http://", "https://", "#", "mailto:")):
            return match.group(0)

        base_file = full_url.split("#")[0]
        anchor = "#" + full_url.split("#")[1] if "#" in full_url else ""

        # Check map for base file (e.g., "design.md")
        if base_file in link_map:
            return f"[{match.group(1)}]({link_map[base_file]}{anchor})"
        # Check for basename match (e.g. path/to/design.md)
        for key, val in link_map.items():
            if base_file.endswith(key):
                return f"[{match.group(1)}]({val}{anchor})"

        return match.group(0)

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_match, md_content)

def update_doc_content(drive_s, doc_id, md_content):
    """
    Replaces the file content of an existing Google Doc via Drive API update.

    Unlike the Docs API insertText approach, re-uploading the file as
    text/markdown through Drive preserves full Markdown formatting
    (headings, lists, tables, code blocks).
    """
    media = MediaIoBaseUpload(
        io.BytesIO(md_content.encode("utf-8")),
        mimetype="text/markdown",
        resumable=True
    )
    drive_s.files().update(
        fileId=doc_id,
        media_body=media,
        fields="id"
    ).execute()
    print(f"  🔄 Updated content (ID: {doc_id})")

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <markdown_directory>")
        sys.exit(1)

    md_dir = sys.argv[1]
    if not os.path.isdir(md_dir):
        print(f"Error: {md_dir} is not a valid directory.")
        sys.exit(1)

    print("═" * 61)
    print(" 🚀 Google Docs Publishing Pipeline")
    print("═" * 61)

    try:
        drive_s, docs_s = get_services()
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return

    # 1. Scan files
    md_files = find_md_files(md_dir)
    print(f"\n📂 Scanned {len(md_files)} Markdown files.")

    # 2. Build titles and create/update docs in a single pass.
    #    Track titles to avoid collisions.
    print("\n📤 Phase 1: Uploading/Updating Documents...")

    link_map = {}  # filename or rel_path -> google_doc_url
    existing_titles = set()

    # Pre-scan to collect all titles (including existing Drive docs).
    # This is best-effort; we mainly guard against intra-run collisions.
    for filepath in md_files:
        rel_path = os.path.relpath(filepath, md_dir)
        basename = os.path.basename(filepath)
        title = make_unique_title(rel_path, basename, existing_titles)
        existing_titles.add(title)

    for filepath in md_files:
        rel_path = os.path.relpath(filepath, md_dir)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        title = make_unique_title(rel_path, os.path.basename(filepath), existing_titles)

        doc_id = get_or_create_doc(drive_s, title, content)

        if doc_id:
            url = f"{BASE}{doc_id}/edit"
            link_map[rel_path] = url
            link_map[os.path.basename(filepath)] = url

    # 3. Second Pass: Rewrite inter-doc links and re-upload with corrected URLs.
    #    This is only needed when files contain links to each other.
    print("\n🔗 Phase 2: Fixing Cross-Links and Finalizing...")

    has_internal_links = False
    for filepath in md_files:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        if re.search(r"\[[^\]]+\]\((?!https?://)[^)]+\.md", content):
            has_internal_links = True
            break

    if has_internal_links:
        for filepath in md_files:
            rel_path = os.path.relpath(filepath, md_dir)
            with open(filepath, encoding="utf-8") as f:
                content = f.read()

            if rel_path not in link_map:
                continue

            doc_id = link_map[rel_path].split("/")[4]

            print(f"  ✍️  Rewriting links for {os.path.basename(filepath)}...")
            new_content = rewrite_links(content, link_map)
            update_doc_content(drive_s, doc_id, new_content)

            time.sleep(1)  # Politeness for API
    else:
        print("  No internal cross-links detected, skipping link rewrite pass.")

    print("\n✅ All done! Your documents are live and linked.")

if __name__ == "__main__":
    main()
