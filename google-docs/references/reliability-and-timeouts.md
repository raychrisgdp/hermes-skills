# Reliability and Timeout Guidance

## The support path
When a docs workflow fails, follow this order:
1. Check auth.
2. Check the Drive file MIME type.
3. If the file is not `application/vnd.google-apps.document`, stop and fix the import step.
4. Keep the write path in one foreground script or notebook cell.
5. If you need a retry, rerun the same foreground script after a short backoff.
6. Only use a direct Google API client with a longer HTTP timeout for verification.

## Preferred execution pattern
- One script creates/imports the doc.
- The same script checks MIME type.
- The same script renders Mermaid.
- The same script inserts images.
- The same script prints the doc ID and the exact next verification step.
- If any step fails, stop and fix that step before starting another background job.

## What usually breaks
- Hiding writes behind `nohup` or a background shell process.
- Calling Docs API edits on a Drive Markdown file instead of a native Google Doc.
- Using a fake anchor like `start_index=1` instead of a real heading end index.
- Re-reading the full raw document repeatedly on a large doc.

## Minimum checks before image insertion
- The imported file is a native Google Doc.
- The diagram PNG is public.
- The page is landscape if the diagram is wide.
- The insert runs in the same foreground process that created the anchor data.
- If there are multiple diagrams, insert the later one first.
- Match plain text headings in the doc structure; Markdown heading markers disappear during import.
- Verify success by reading `inlineObjects` from the Docs API, not by relying only on markdown export.

## Batch multi-doc creation
When creating several docs from a folder of Markdown files:
- Use `publish_pipeline.py /path/to/folder` for the initial import. It handles large files and retries better than ad-hoc Drive API calls.
- The pipeline generates titles from filenames: `"architecture.md"` becomes `"Architecture"` (filename.title() with hyphens/underscores replaced by spaces).
- If you want a different naming convention (e.g. "GL Runner - Architecture"), search for existing docs first to avoid duplicates, or rename after creation with `drive.files().update(fileId=..., body={"name": new_title})`.
- Import the docs first, then insert Mermaid images in a second pass. Mixing import and image insertion in one script is fine but keep them as separate steps.
- If direct `MediaIoBaseUpload` times out on a large Markdown file (84KB+), the pipeline script typically succeeds where the one-off call fails.

## Verification fallback
If `docs_api.py get <doc_id> --md` times out:
- use a direct `docs.googleapis.com` client
- set `httplib2.Http(timeout=120)`
- fetch the smallest useful payload
- do not switch back to `--raw` loops
