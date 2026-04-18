# Command Recipes

## Auth
- `python3 <skill-root>/scripts/setup.py --check`

## Full reproducible diagram/doc workflow
Use this when you want to recreate the Mermaid/PNG/Google-Docs pipeline in any environment.

Keep the instructions reusable:
- do not name specific project files unless the user asked for them
- do not hardcode machine-specific paths
- use placeholders like `<skill-root>` and `<python-with-google-deps>`

Assume:
- `<skill-root>` is where this skill is installed in the current agent environment
- `<python-with-google-deps>` is a Python interpreter that has the Google Docs dependencies installed

1. Find the source Markdown and identify the canonical diagram blocks.
   - Search the project for Markdown, image assets, and Mermaid fences.
   - Read the actual source files directly.
   - The key idea is to decide which Markdown files are authoritative for each diagram family, then treat those files as the input set for the rest of the pipeline.

2. Extract Mermaid blocks and save their anchors.
   - Strip Mermaid fences from the Markdown buffer before import.
   - Record the nearest heading or paragraph before each diagram so you can re-anchor the image later.
   - Do not assume source line numbers survive the import.

3. Render Mermaid locally with Mermaid CLI.
   - Use Mermaid CLI via `npx`.
   - Example command:
     - `npx --yes @mermaid-js/mermaid-cli@11.4.3 -i input.mmd -o output.png -p /tmp/pp.json -b white -s 3 -w 2400`
   - Create `/tmp/pp.json` with:
     - `{"args": ["--no-sandbox"]}`
   - This matters because Google Docs will not turn Mermaid fences into diagrams for you. Raw Mermaid remains text until you render it.

4. Render Graphviz dot separately when it gives better layout control.
   - For layered block diagrams, use Graphviz dot instead of Mermaid.
   - Example:
     - `dot -Tpng diagram.dot -o diagram.png`
   - Keep the source format and the rendered image as separate artifacts.

5. Import the stripped Markdown into Google Docs.
   - For one file, place it in a temporary directory because the bulk pipeline expects a folder.
   - Example:
     - `mkdir /tmp/gdocs-publish && cp myfile.md /tmp/gdocs-publish/`
     - `python3 <skill-root>/scripts/publish_pipeline.py /tmp/gdocs-publish`
   - If you already have a native Google Doc ID and want to update in place, use:
     - `python3 <skill-root>/scripts/docs_api.py update DOC_ID --md FILE`
   - Use the bulk pipeline for many docs; use the direct update path when the target doc already exists.

6. Insert the rendered images after import.
   - Use:
     - `docs_advanced.insert_image(doc_id, image_path, start_index=..., width_pts=..., height_pts=...)`
   - The first argument must be the native Google Doc ID.
   - The helper uploads the image, makes it readable, and inserts it by URI.
   - Prefer a full-resolution Drive URL when available; thumbnail-only insertion can look soft.

7. Read the live doc structure once, then insert from bottom to top.
   - Inspect the doc with:
     - `python3 <skill-root>/scripts/docs_api.py get DOC_ID --raw`
   - Use `--fields` when you only need a narrow slice of the structure.
   - Insert the later diagram first so earlier anchor indices do not shift.

8. Verify the result, then adjust sizing.
   - Re-export with:
     - `python3 <skill-root>/scripts/docs_api.py get DOC_ID --md`
   - Confirm the document contains inline images, not literal Mermaid fences.
   - In the raw export, look for `inlineObjects` to confirm the images landed.
   - Size diagrams by page space and aspect ratio, not by a fixed width.
   - Tall diagrams usually need a narrower width so they do not consume too much vertical space.

## Single-file markdown with one local PNG
When the source of truth is one Markdown file plus an inline PNG asset, use this pattern:

1. Copy the source Markdown into a temporary directory.
   - `publish_pipeline.py` expects a directory, not a single file.
   - Keep the file name stable so the `.doc_ids.json` mapping is easy to read back.

2. Strip the literal `![](...)` image line before the Markdown import.
   - Import the prose/tables/links first so the doc comes in cleanly.
   - Insert the image afterward with `docs_advanced.insert_image(...)`.

3. Publish the temp directory, then rename the doc.
   - Drive import preserved tables and links more reliably than ad hoc Docs styling.
   - Renaming the Drive file after publish keeps the visible doc title aligned with the source.

4. Set page orientation before image insertion if the doc is wide.
   - For deployment and architecture docs, landscape usually gives better layout headroom.

5. Find the insertion anchor from the live doc structure, not from source line numbers.
   - Match the imported paragraph text exactly or by normalized text.
   - Insert the image after the paragraph that introduces it.

6. Insert the PNG inline with a page-space-aware width.
   - Use `docs_advanced.insert_image(doc_id, image_path, start_index=..., width_pts=...)`.
   - Wide overview figures often look best around half-page to full-page width depending on surrounding tables.

7. Validate both structure and rendering.
   - Check headings and tables in the exported Markdown.
   - Check `inlineObjects` in the raw doc structure.
   - Confirm the image is actually inline, not pasted as literal Markdown text.

9. Do a visual QA pass on the rendered asset, not just the source.
   - Capture the doc or the rendered PNG and inspect it visually.
   - Compare the image against the source Markdown and the nearby prose so you can tell whether the issue is diagram structure, render quality, or Docs insertion.
   - The image can be wrong even when the Mermaid source is valid; layout, aspect ratio, and insertion width still matter.
   - If a diagram is blurry or cramped, adjust the render command and the insert width before changing the content.
   - For wide architecture diagrams, set the Google Doc to landscape before inserting images; this usually gives cleaner line breaks and less vertical crowding.
   - When the Markdown contains placeholder anchors for images, replace them after import using the live doc indices from `docs_api.py --raw`, not the source line numbers.
   - Insert multiple diagrams from bottom to top so earlier anchor indices do not drift.

10. If the doc is visually corrupted, recreate or clear it.
   - If a Markdown import turns into plain text or heading styles are wrong, it is often faster to clear/recreate the doc than to patch the malformed structure in place.
   - Then republish the stripped Markdown and reinsert the images.

11. If the skill itself changes, sync the repo and PR.
   - Commit and push the skill change in the repository that owns the skill.
   - If the PR body needs updating, patch it with the repository’s normal GitHub workflow.


## Publish
- `python3 <skill-root>/scripts/publish_pipeline.py /path/to/markdown/folder`
- `publish_pipeline.py` requires a **directory**, not a single file. For a single file: `mkdir /tmp/gdocs-publish && cp myfile.md /tmp/gdocs-publish/ && python3 ... /tmp/gdocs-publish`
- By default, the pipeline may create a new doc on each publish if it does not find a stored mapping.
- If the user wants to keep the same URL stable, update the existing doc in place instead of republishing a fresh one. Reuse the stored `.doc_ids.json` mapping and `update_doc_content()` / `drive.files().update(...)` against the existing doc ID.
## Rename a doc after publish
The Drive import renders the title as HEADING_1, not a separate doc title field. To fully rename:
1. `drive.files().update(fileId=doc_id, body={'name': 'New Title'})` — updates Drive listing
2. `replaceAllText` on the old HEADING_1 text — updates the visible heading in the doc
Both are needed; one does not cover the other.

## Replace a specific live-doc section in place
Use this when the user wants to edit one section of an existing Google Doc without republishing the whole document.

Preferred workflow:
1. Read the live doc first and confirm the exact anchor text already present in the document.
   - Best case: a unique placeholder such as `(please insert here)` under a known heading.
2. Replace only that exact visible text with `replaceAllText`.
3. Verify that the replacement happened exactly once.
4. Re-read the nearby section to confirm the new content landed under the intended heading.

Example request body:

```json
{
  "requests": [
    {
      "replaceAllText": {
        "containsText": {
          "text": "(please insert here)",
          "matchCase": true
        },
        "replaceText": "1. First item\n2. Second item"
      }
    }
  ]
}
```

Notes:
- This is for visible text replacement only. It does not update links, smart chips, or other structured objects.
- Do not use blind replacement when the marker text appears more than once. Make the anchor unique first or switch to a range-based edit workflow.
- For recurring operational docs, keep a stable placeholder or marker so later section refreshes stay deterministic.

## Page numbers in footer
The Docs API cannot insert dynamic page number fields (e.g. "X of Y") programmatically. Must be done manually: Insert > Page numbers > pick the "X of Y" layout.

## Inspect rendered docs
- `python3 <skill-root>/scripts/docs_api.py get <doc_id> --md`

## Inspect raw structure
- `python3 <skill-root>/scripts/docs_api.py get <doc_id> --raw`

## Inspect a narrow structure slice
- `python3 <skill-root>/scripts/docs_api.py get <doc_id> --raw --fields 'title,body/content(startIndex,endIndex,paragraph(elements(textRun(content),inlineObjectElement),paragraphStyle/namedStyleType))'`

## Insert image
- `docs_advanced.insert_image(doc_id, image_path, start_index=..., width_pts=..., height_pts=..., tab_id=...)`
- The first argument should be the native Google Doc ID, not a Drive Markdown file ID.
- Images are center-aligned by default (`updateParagraphStyle.alignment=CENTER` on insert).
- Pass `tab_id` for multi-tab docs to avoid writing into the first tab by mistake.
- The helper now defaults to public Drive access for the uploaded image so Docs can fetch the thumbnail URI.
- `width_pts` / `height_pts` resize the image before upload.
- When inserting multiple diagrams, insert the later one first.
- Verify the final doc with `inlineObjects`, not only with Markdown export.

## Bullet/list style presets

Valid `bulletPreset` values for `createParagraphBullets`:

- `BULLET_DISC_CIRCLE_SQUARE` — standard disc bullets
- `BULLET_STAR_CIRCLE_SQUARE` — star bullets
- `BULLET_ARROW_DIAMOND_DISC` — arrow bullets
- `BULLET_CHECKBOX` — checkbox style
- `NUMBERED_DECIMAL_ALPHA_ROMAN` — numbered: 1, 2, 3
- `NUMBERED_UPPERALPHA_ALPHA_ROMAN` — lettered: A, B, C
- `NUMBERED_DECIMAL_NESTED` — nested decimal
- `NUMBERED_ZERODECIMAL_ALPHA_ROMAN` — zero-padded: 01, 02, 03
- `NUMBERED_UPPERROMAN_UPPERALPHA_DECIMAL` — roman/alpha/decimal

To change an existing list's style (must delete first, then recreate):
```python
requests = [
    {'deleteParagraphBullets': {'range': {'startIndex': start, 'endIndex': end}}},
    {'createParagraphBullets': {'range': {'startIndex': start, 'endIndex': end}, 'bulletPreset': preset}},
]
```

Note: The bullet preset is stored on the list object, not the paragraph. Inspect list styles via `doc['lists']` and check `glyphType` on nesting levels (`DECIMAL`, `UPPER_ALPHA`, etc.), not via paragraph-level `bulletPreset`.

## Switch page orientation
- Whole document: `docs_advanced.set_page_orientation(doc_id, landscape=True)`
- Selected range as its own section: `docs_advanced.set_section_orientation(doc_id, start_index, end_index, landscape=True, tab_id=...)`
- Auto-detect per selected range: `docs_advanced.set_section_orientation_auto(doc_id, start_index, end_index, tab_id=...)`
- For multi-tab docs, include `tabId` in `Location`/`Range` for section-break and section-style requests, or the API applies to the first tab by default.
- Docs `get` field masks cannot mix `tabs(...)` with legacy text/body fields in one request; fetch tab metadata and body/style data in separate calls.

## Tab operations (multi-tab docs)
- List tabs: `docs_advanced.list_tabs(doc_id)`
- Add tab: `docs_advanced.add_document_tab(doc_id, "[EXPERIMENTAL] ...")`
- For content writes in tabbed docs, always pass `tab_id` on insert and section-style requests.

## Recovery when reads time out
- Do not keep retrying `--raw` on a huge doc.
- Prefer `--fields` to fetch only the paragraphs you need.
- Read the source Markdown first.
- Use one doc-structure read, then insert images in reverse order.
- If the helper script still times out, use a direct Docs client with a longer HTTP timeout and then come back to the skill workflow.

## Selective multi-doc creation (not whole directory)
When publishing only some files from a directory, `publish_pipeline.py` doesn't support filtering. Use a standalone script instead:
1. Build an explicit allowlist of existing `.md` paths; do not assume optional docs are present.
2. Strip Mermaid blocks before import, keep the nearest heading as an anchor, and render the diagrams locally to PNG.
3. Convert fenced code to 4-space indented blocks for more reliable Google Docs rendering.
4. Create docs via Drive `MediaIoBaseUpload` with `mimetype="text/markdown"`.
5. Rewrite inter-doc links in a second pass, then `drive.files().update()` each doc in place so URLs stay stable.
6. For wide diagrams, set landscape orientation before inserting images, then insert the rendered PNGs in reverse anchor order so earlier indices do not shift.
7. Verify the final doc with `inlineObjects` after insertion, not just a markdown re-export.

## Execution environment
Google API deps (`google.oauth2`, `googleapiclient`) are not in the default sandbox. Run Google Docs scripts with:
```
<python-with-google-deps> /path/to/script.py
```
Do not use `execute_code` for Google Docs tasks — the sandbox lacks the required packages. Use `terminal` with the appropriate Python interpreter instead.

## When to use these
- Use the command recipes when the user needs a direct operational step.
- Keep the main skill short; send detailed mechanics to the reference files.
