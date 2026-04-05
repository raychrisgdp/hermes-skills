#!/usr/bin/env python3
"""Publish a directory of Markdown files as Google Docs with cross-linking.

This pipeline supports two modes:
1. **Standard**: Publish each MD file as a separate Google Doc, resolving cross-links.
2. **Combined**: Combine all MD files into ONE Google Doc with page breaks.

The primary method uses the **Drive API** (`text/markdown` import), which preserves
formatting (headings, lists, tables, links) natively in a single API call.
"""
import os, re, sys, io, time
sys.path.insert(0, "/home/raymond-christopher/.hermes/skills/productivity/google-docs/scripts")

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Import formatting functions for fallback/manual styling
try:
    from docs_api import _apply_heading_styles, _apply_inline_styles, _apply_bullets
except ImportError:
    _apply_heading_styles = None
    _apply_inline_styles = None
    _apply_bullets = None

TOKEN = "/home/raymond-christopher/.hermes/google_token.json"
creds = Credentials.from_authorized_user_file(TOKEN)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    with open(TOKEN, "w") as f: f.write(creds.to_json())

drive = build("drive", "v3", credentials=creds)
docs = build("docs", "v1", credentials=creds)

def find_md_files(directory):
    md_files = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith('.md'):
                md_files.append(os.path.join(root, f))
    return md_files

def title_from_filename(filename):
    """Convert filename to Title Case."""
    base = os.path.splitext(os.path.basename(filename))[0]
    return base.replace('-', ' ').replace('_', ' ').title()

def get_gdoc_url(doc_id):
    return f"https://docs.google.com/document/d/{doc_id}/edit"

def upload_md_to_drive(title, md_content):
    """
    Upload Markdown content to Drive, creating a Google Doc.
    Uses the native Drive import which preserves formatting (Tables, Lists, Headers).
    Returns the doc_id.
    """
    file_metadata = {
        'name': title,
        'mimeType': 'application/vnd.google-apps.document'
    }
    media = MediaIoBaseUpload(
        io.BytesIO(md_content.encode('utf-8')), 
        mimetype='text/markdown', 
        resumable=True,
        chunksize=1024*1024  # 1MB chunks
    )
    
    # Retry loop for 429s
    for attempt in range(3):
        try:
            file = drive.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            return file['id']
        except Exception as e:
            if "429" in str(e) or "Rate" in str(e):
                wait = 20 * (attempt + 1)
                print(f"    Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                raise e
    return None

def clear_and_update_doc(doc_id, rewritten_md):
    """
    Update an existing Google Doc in place (keeps same ID).
    Uses Docs API to clear and re-insert, then formats manually.
    """
    try:
        doc = docs.documents().get(documentId=doc_id).execute()
        if 'body' in doc and 'content' in doc['body'] and len(doc['body']['content']) > 0:
            end_index = doc['body']['content'][-1].get('endIndex', 1)
            if end_index > 1:
                docs.documents().batchUpdate(documentId=doc_id, body={
                    "requests": [{"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end_index - 1}}}]
                }).execute()
        
        docs.documents().batchUpdate(documentId=doc_id, body={
            "requests": [{"insertText": {"location": {"index": 1}, "text": rewritten_md}}]
        }).execute()
        
        if _apply_heading_styles: _apply_heading_styles(doc_id)
        # _apply_inline_styles is slow, so might be skipped if content is large
        # but for accuracy we call it.
        # if _apply_inline_styles: _apply_inline_styles(doc_id) 
        if _apply_bullets: _apply_bullets(doc_id)
        
        return True
    except Exception as e:
        print(f"  Error updating {doc_id}: {e}")
        return False

def rewrite_markdown_links(md_content, link_map):
    """Replace relative Markdown links with Google Docs URLs."""
    def replace_link(m):
        full_url = m.group(2)
        # Skip external URLs, anchors, and mailto links
        if full_url.startswith(('http://', 'https://', '#', 'mailto:')):
            return m.group(0)
        
        base_file = full_url.split('#')[0]
        anchor = '#' + full_url.split('#')[1] if '#' in full_url else ''
        
        # Match logic: exact basename or relative path
        target_url = None
        for key, value in link_map.items():
            if base_file == key or base_file.endswith('/' + key) or base_file.endswith(key):
                target_url = value
                break
        
        if target_url:
            return f"[{m.group(1)}]({target_url}{anchor})"
        return m.group(0)
    
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, md_content)

def publish_combined(mega_title, md_files_and_content):
    """
    Publish multiple MD files into ONE Google Doc separated by page breaks.
    Returns the URL.
    """
    combined = ""
    for filename, title, content in md_files_and_content:
        combined += f"# {title}\n\n"
        combined += content
        combined += "\n\n\f\n\n"  # Form feed creates page/section break
    
    print(f"Combined size: {len(combined)} bytes")
    doc_id = upload_md_to_drive(mega_title, combined)
    return get_gdoc_url(doc_id) if doc_id else None

def publish_individual(md_files, update_existing=True):
    """
    Publish each MD file as a separate Google Doc.
    Resolves cross-links to point to the new Docs.
    """
    print("Step 1: Checking for existing Google Docs...")
    gdoc_map = {}
    link_map = {}
    
    for f_path in md_files:
        basename = os.path.basename(f_path)
        title = title_from_filename(basename)
        
        # Check for existing
        res = drive.files().list(
            q=f"name='{title}' and mimeType='application/vnd.google-apps.document' and trashed=false",
            fields="files(id)"
        ).execute()
        
        doc_id = None
        if res['files']:
            doc_id = res['files'][0]['id']
        
        gdoc_map[basename] = {
            'path': f_path,
            'id': doc_id,
            'title': title,
            'url': get_gdoc_url(doc_id) if doc_id else None
        }

    print("Step 2: Building Link Map for Cross-Referencing...")
    for basename, info in gdoc_map.items():
        link_map[basename] = info['url']

    print("Step 3: Publishing Files...")
    for basename, info in gdoc_map.items():
        with open(info['path'], 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Rewrite internal links
        new_content = rewrite_markdown_links(content, link_map)
        
        # Determine URL
        current_url = None
        
        if update_existing and info['id']:
            # Delete old and re-create to get native Drive formatting
            print(f"  Re-creating '{info['title']}' (to use native Drive import)...")
            drive.files().delete(fileId=info['id']).execute()
            new_id = upload_md_to_drive(info['title'], new_content)
            current_url = get_gdoc_url(new_id)
        elif info['id']:
            # In-place update (no Drive import quality)
            print(f"  Updating '{info['title']}' in-place...")
            # Use clear_and_update_doc logic here
            clear_and_update_doc(info['id'], new_content)
            current_url = get_gdoc_url(info['id'])
        else:
            # New creation
            print(f"  Creating '{info['title']}'...")
            new_id = upload_md_to_drive(info['title'], new_content)
            current_url = get_gdoc_url(new_id)
            
        gdoc_map[basename]['url'] = current_url
        print(f"    -> {current_url}")

    return gdoc_map

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help="Directory containing Markdown files")
    parser.add_argument("--combined", action="store_true", help="Combine all files into one document")
    parser.add_argument("--title", default="Combined Markdown Export", help="Title for combined doc")
    args = parser.parse_args()
    
    md_files = find_md_files(args.directory)
    
    if args.combined:
        print(f"Publishing {len(md_files)} files as ONE combined doc...")
        combined_content = []
        for f_path in md_files:
            basename = os.path.basename(f_path)
            with open(f_path) as f: combined_content.append((basename, title_from_filename(basename), f.read()))
        
        url = publish_combined(args.title, combined_content)
        if url:
            print(f"\nSUCCESS: {url}")
        else:
            print("Failed to publish.")
    else:
        print(f"Publishing {len(md_files)} files individually...")
        results = publish_individual(md_files)
