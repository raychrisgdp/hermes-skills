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
- Using a short search fragment (e.g. "Context") that matches multiple paragraphs. Use a longer unique substring from the heading, or read the doc structure first and pick the exact `endIndex`.

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
- `width_pts` and `height_pts` are resize hints before upload, not a Docs API object-size flag.
- When the heading text is imported from Markdown, the `###` markers disappear. Match the plain text heading text in the doc structure instead.
- After insertion, verify `inlineObjects` in the live Docs API response so you know the image really landed.

## Sizing
- Keep the image conservative so it fits within the page.
- Default to **500-560 pt** for the first wide overview diagram if it is sharing space with nearby text.
- Default to **440-500 pt** for the second runtime/boundary diagram so it does not push the surrounding prose down too hard.
- Use **600 pt only when the diagram is still readable and the page is landscape with enough surrounding whitespace**.
- For tall diagrams, cap the width and let the aspect ratio reduce the height.
- If the diagram still feels huge, shrink it again instead of letting it float awkwardly through the text.

## Verify
- Re-export the doc.
- Confirm the image is present and the surrounding paragraph flow still makes sense.
- If a full doc read times out, switch to the reliability notes and avoid repeated full export calls.
