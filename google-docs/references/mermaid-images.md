# Mermaid and Inline Images

## Rule
- Render Mermaid locally first.
- Do not rely on the Docs API to render Mermaid fences.

## Recommended sequence
1. Read the source Markdown and extract every ```mermaid block.
2. Record the paragraph or heading immediately before each block as the anchor.
3. Strip the Mermaid fences from the Markdown before Drive import.
4. Import the stripped Markdown into Google Docs.
5. Render each Mermaid block locally to PNG.
6. Read the doc structure once, locate the anchor paragraphs, and insert the images after those anchors.
7. Re-export the doc and confirm the images sit in the right place.
8. Do the import and insert steps in one foreground script or notebook cell so you can see success/failure immediately.

## Common mistakes
- Importing the original Markdown after already producing `content_no_mermaid`.
- Using `start_index=1` as a generic anchor instead of the end index of the real heading paragraph.
- Hiding the doc write behind `nohup` or a background shell process, which makes API failures invisible.

## Recommended command
- `npx --yes @mermaid-js/mermaid-cli@11.4.3 -i input.mmd -o output.png -p /tmp/pp.json`
- Use a `pp.json` containing `{"args": ["--no-sandbox"]}`.

## Insert the image
- Use `scripts/docs_advanced.py insert_image(doc_id, image_path, start_index=..., width_pts=..., height_pts=...)`.
- Insert after the paragraph or heading that introduces the diagram.
- Do not insert at the raw fence location.
- Prefer one structure read, then insert all images in reverse order so indices stay stable.
- If there are multiple Mermaid blocks, insert the last one first so earlier indices do not shift.
- Make the uploaded image public before inserting it; the Docs API is much more reliable when the thumbnail URI is readable.
- `width_pts` and `height_pts` are now resize hints before upload, not a Docs API object-size flag.
- When the heading text is imported from Markdown, the `###` markers disappear. Match the plain text heading text in the doc structure instead.
- After insertion, verify `inlineObjects` in the live Docs API response so you know the image really landed.

## Sizing
- Keep the image conservative so it fits within the page.
- Use a larger cap for landscape-ready diagrams; portrait layouts often look cramped around 400-450 pt wide, while landscape layouts can usually take 600-640 pt.
- For tall diagrams, cap the width and let the aspect ratio reduce the height.
- If the ERD or diagram still feels huge, either move it to a landscape page section or shrink it again instead of letting it float awkwardly through the text.

## Verify
- Re-export the doc.
- Confirm the image is present and the surrounding paragraph flow still makes sense.
- If a full doc read times out, switch to the reliability notes and avoid repeated full export calls.
