#!/usr/bin/env python3
"""
Publish Markdown Directory to Google Docs (Drive Import Method).

This script scans a directory of Markdown files, uploads them to Google Drive
as native Google Docs (preserving tables/formatting instantly), and fixes
internal cross-links (e.g. linking `design.md` to the newly created
'Design' Google Doc).

Usage:
    python3 publish_pipeline.py /path/to/markdown/folder
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
TOKEN_PATH = os.path.expanduser("~/.hermes/google_token.json")
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

def get_or_create_doc(drive_s, title, md_content=None):
    """Find existing doc by title, or create a new one via Drive Import."""
    
    # 1. Try to find existing
    results = drive_s.files().list(
        q=f"name='{title}' and mimeType='application/vnd.google-apps.document' and trashed=false",
        fields="files(id, name, modifiedTime)"
    ).execute()
    
    if results.get("files"):
        # Return the most recently modified one
        files = sorted(results["files"], key=lambda x: x.get("modifiedTime", ""), reverse=True)
        file_id = files[0]["id"]
        print(f"  ♻️  Found existing doc: {title} (ID: {file_id})")
        return file_id

    # 2. Create new via Drive Import (Fast & Perfect Formatting)
    if md_content:
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
    return None

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
    Updates a Google Doc in place by clearing its content and re-inserting.
    Note: This uses the Docs API which doesn't fully replicate Drive's native
    Markdown import styling, but it keeps the Document ID intact.
    """
    docs_s = build("docs", "v1", credentials=drive_s._http.credentials) # Reuse creds
    try:
        doc = docs_s.documents().get(documentId=doc_id).execute()
        end_index = doc["body"]["content"][-1].get("endIndex", 1)
        
        # Clear content
        if end_index > 1:
            docs_s.documents().batchUpdate(documentId=doc_id, body={
                "requests": [{"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end_index - 1}}}]
            }).execute()
            
        # Insert text
        docs_s.documents().batchUpdate(documentId=doc_id, body={
            "requests": [{"insertText": {"location": {"index": 1}, "text": md_content}}]
        }).execute()
        print(f"  🔄 Updated content (ID: {doc_id})")
    except Exception as e:
        print(f"  ⚠️  Failed to update doc {doc_id}: {e}")

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <markdown_directory>")
        sys.exit(1)

    md_dir = sys.argv[1]
    if not os.path.isdir(md_dir):
        print(f"Error: {md_dir} is not a valid directory.")
        sys.exit(1)

    print("═══════════════════════════════════════════════════════════════")
    print(" 🚀 Google Docs Publishing Pipeline")
    print("═══════════════════════════════════════════════════════════════")
    
    try:
        drive_s, docs_s = get_services()
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return

    # 1. Scan files
    md_files = find_md_files(md_dir)
    print(f"\n📂 Scanned {len(md_files)} Markdown files.")

    # 2. Initial Pass: Create Docs (without links fixed) to get IDs
    #    We do this first so we have a map of IDs for the links in the content.
    print("\n📤 Phase 1: Uploading/Updating Documents (Initial Pass)...")
    
    link_map = {} # filename -> google_doc_url
    
    # Sort to ensure we process files in a deterministic order
    # We strip path relative to md_dir for the map keys
    for filepath in md_files:
        rel_path = os.path.relpath(filepath, md_dir)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        
        # Generate a clean title from filename
        title = os.path.splitext(os.path.basename(filepath))[0]
        title = title.replace("-", " ").replace("_", " ").title()
        if title == "Readme": title = "Readme"
        
        doc_id = get_or_create_doc(drive_s, title, None)
        
        if doc_id:
            url = f"{BASE}{doc_id}/edit"
            link_map[rel_path] = url
            # Also map just the filename for simplicity
            link_map[os.path.basename(filepath)] = url

    # 3. Second Pass: Rewrite links and Update Content
    print("\n🔗 Phase 2: Fixing Cross-Links and Finalizing...")
    
    for filepath in md_files:
        rel_path = os.path.relpath(filepath, md_dir)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
            
        if not rel_path in link_map:
            continue
            
        doc_id = link_map[rel_path].split("/")[4] # Extract ID
        
        # Rewrite links
        print(f"  ✍️  Rewriting links for {os.path.basename(filepath)}...")
        new_content = rewrite_links(content, link_map)
        
        # Update doc
        update_doc_content(drive_s, doc_id, new_content)
        
        time.sleep(1) # Politeness for API

    print("\n✅ All done! Your documents are live and linked.")

if __name__ == "__main__":
    main()
