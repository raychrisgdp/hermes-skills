# Command Recipes

## Auth
- `python3 ~/.hermes/skills/productivity/google-docs/scripts/setup.py --check`

## Publish
- `python3 ~/.hermes/skills/productivity/google-docs/scripts/publish_pipeline.py /path/to/markdown/folder`

## Inspect rendered docs
- `python3 ~/.hermes/skills/productivity/google-docs/scripts/docs_api.py get <doc_id> --md`

## Inspect raw structure
- `python3 ~/.hermes/skills/productivity/google-docs/scripts/docs_api.py get <doc_id> --raw`

## Insert image
- `docs_advanced.insert_image(doc_id, image_path, start_index=..., width_pts=..., height_pts=...)`

## When to use these
- Use the command recipes when the user needs a direct operational step.
- Keep the main skill short; send detailed mechanics to the reference files.
