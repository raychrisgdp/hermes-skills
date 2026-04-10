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
- Verify success by reading `inlineObjects` from the Docs API, not by relying only on markdown export.

## Verification fallback
If `docs_api.py get <doc_id> --md` times out:
- use a direct `docs.googleapis.com` client
- set `httplib2.Http(timeout=120)`
- fetch the smallest useful payload
- do not switch back to `--raw` loops
