# Reliability and Timeouts

## Why timeouts happen
- Google Docs API calls can time out on large documents.
- `documents().get()` returns a large JSON payload when you ask for the whole doc.
- Repeated full-doc reads inside a loop make the problem worse.
- Transient 500s and quota pressure can happen after several successive batch updates.

## What to do instead
- Avoid repeated full-document reads.
- Read the document once, cache the paragraph map, and reuse it.
- When you only need an anchor, search the source Markdown first.
- Only fetch the doc structure again if the text moved.
- Keep image insertion and structure discovery as separate steps.
- Use `docs_api.py get <doc_id> --raw --fields '...'` when you only need a narrow slice of the document.

## Retry guidance
- Retry 429/500/timeouts with exponential backoff.
- Do not hammer the API with the same request in a tight loop.
- If a single insertion keeps failing, wait and try again with the same input.

## Large-doc fallback
- If a full raw export times out, do not keep asking for `--raw`.
- Try a narrower inspection path or a direct Docs client with a longer HTTP timeout.
- If the doc is huge, use source Markdown anchors and a single structure read instead of repeated exports.
- If even that is too slow, split the work into smaller docs or smaller insertion batches.

## Practical rule
- One read to map structure.
- One pass to render or import.
- One pass to insert images.
- Then verify the result.