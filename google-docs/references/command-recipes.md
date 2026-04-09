# Command Recipes

## Auth
- `python3 ~/.hermes/skills/productivity/google-docs/scripts/setup.py --check`

## Publish
- `python3 ~/.hermes/skills/productivity/google-docs/scripts/publish_pipeline.py /path/to/markdown/folder`

## Inspect rendered docs
- `python3 ~/.hermes/skills/productivity/google-docs/scripts/docs_api.py get <doc_id> --md`

## Inspect raw structure
- `python3 ~/.hermes/skills/productivity/google-docs/scripts/docs_api.py get <doc_id> --raw`

## Inspect a narrow structure slice
- `python3 ~/.hermes/skills/productivity/google-docs/scripts/docs_api.py get <doc_id> --raw --fields 'title,body/content(startIndex,endIndex,paragraph(elements(textRun(content),inlineObjectElement),paragraphStyle/namedStyleType))'`

## Insert image
- `docs_advanced.insert_image(doc_id, image_path, start_index=..., width_pts=..., height_pts=...)`

## Recovery when reads time out
- Do not keep retrying `--raw` on a huge doc.
- Prefer `--fields` to fetch only the paragraphs you need.
- Read the source Markdown first.
- Use one doc-structure read, then insert images in reverse order.
- If the helper script still times out, use a direct Docs client with a longer HTTP timeout and then come back to the skill workflow.

## When to use these
- Use the command recipes when the user needs a direct operational step.
- Keep the main skill short; send detailed mechanics to the reference files.
