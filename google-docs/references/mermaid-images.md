# Mermaid and Inline Images

## Rule
- Render Mermaid locally first.
- Do not rely on the Docs API to render Mermaid fences.

## Recommended command
- `npx --yes @mermaid-js/mermaid-cli@11.4.3 -i input.mmd -o output.png -p /tmp/pp.json`
- Use a `pp.json` containing `{"args": ["--no-sandbox"]}`.

## Insert the image
- Use `scripts/docs_advanced.py insert_image(doc_id, image_path, start_index=..., width_pts=..., height_pts=...)`.
- Insert after the paragraph or heading that introduces the diagram.
- Do not insert at the raw fence location.

## Sizing
- Keep the image conservative so it fits within the page.
- For tall diagrams, cap the width and let the aspect ratio reduce the height.
- If the ERD or diagram still feels huge, shrink it again instead of letting it float awkwardly through the text.

## Verify
- Re-export the doc.
- Confirm the image is present and the surrounding paragraph flow still makes sense.
