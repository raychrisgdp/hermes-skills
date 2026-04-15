# Deterministic Markdown + Diagram Sync

## Goal
- Publish a Markdown doc family to Google Docs in a repeatable order.
- Keep cross-links stable.
- Convert Mermaid and image references into actual inline images.
- Avoid ad hoc manual repairs after import.

## Recommended flow
1. Create or reuse all Google Doc IDs first.
2. Rewrite relative links to live Google Docs URLs.
3. Strip Mermaid fences and image placeholder lines from the Markdown buffer.
4. Render each Mermaid block to a PNG locally.
5. Import the stripped Markdown into Google Docs.
6. Read the imported doc structure once.
7. Find the paragraph or heading immediately before each removed diagram.
8. Insert images in reverse document order so indices do not drift.
9. Re-export and confirm that the images landed inline and the doc still reads cleanly.

## Deterministic parsing rules
- Use the source Markdown order as the source of truth.
- For every Mermaid block, record the last non-empty paragraph before the block as the anchor.
- For every image reference, record the last non-empty paragraph before the image line as the anchor.
- Normalize anchors before matching:
  - strip backticks
  - collapse whitespace
  - compare lowercase text
- If multiple anchors match, prefer the first anchor that appears after the previous insertion point.

## Mermaid rendering rules
- Render Mermaid locally with Mermaid CLI before publishing.
- Use a white background and a high enough scale for Docs readability.
- Keep the rendered images in a temp directory so the publishing pass is reproducible.
- If Mermaid fails to parse, first inspect the node labels.
- Quote labels that contain parentheses, slashes, or other punctuation that Mermaid may treat as syntax.
- If a label needs a line break, prefer a Mermaid-safe form such as a quoted label with a line break that the CLI accepts.

## Suggested command pattern
- `npx --yes @mermaid-js/mermaid-cli@11.4.3 -i input.mmd -o output.png -p /tmp/pp.json -b white -s 3 -w 2400`
- `pp.json` should contain `{"args": ["--no-sandbox"]}`.

## Publish order
- Insert images from highest document index to lowest.
- When two images share the same anchor, insert the later source item first.
- This avoids re-reading the doc after each insertion.

## Verification
- Re-export the docs after publishing.
- Make sure the headings still map to the intended sections.
- Confirm that image placeholders were removed from the imported Markdown and replaced with actual inline images.
- If the doc is long, verify the first and last inserted images separately rather than exporting the entire body every time.
