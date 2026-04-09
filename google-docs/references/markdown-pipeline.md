# Markdown Pipeline

## Core decision
- Use Drive import with `text/markdown` when you want a clean native Google Doc from Markdown.
- Use Drive `files.update(..., media_body=MediaIoBaseUpload(..., mimetype='text/markdown'))` when you want to replace an existing doc in place.

## What this handles well
- headings
- tables
- lists
- inline formatting
- simple code blocks

## Code blocks
- Convert fenced code blocks to 4-space indented blocks before import.
- That makes Google Docs preserve them as monospace paragraphs more reliably than raw fences.

## Tables and headings
- If a publish path needs element-level control, re-read the doc after import and then style against real indices.
- Do not assume Markdown positions survive the import unchanged.

## Verify after import
- Re-export with `docs_api.py get <doc_id> --md`.
- Check that headings, tables, code blocks, and links still look right.
