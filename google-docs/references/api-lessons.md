# Google Docs API — Lessons Learned

## Authentication

### OAuth Flow (Desktop App)
- Use port 8085 or random (0) for `flow.run_local_server()` — ports < 1024 are blocked by Chrome (`ERR_UNSAFE_PORT`)
- Token auto-refreshes; store at `~/.hermes/google_token.json`
- `prompt="consent"` forces re-consent screen; omit for silent refresh

### Service Account vs Personal OAuth
- Service Account (`service_account.Credentials`) = robot identity, not user
- OAuth2 Desktop (`flow.from_client_secrets_file()`) = user identity
- For personal account access (`user@gmail.com`), use OAuth, not Service Account

## Content Manipulation

### Two-Pass Pattern (Proven Working)
You cannot reliably calculate character positions in advance, because the
Google Docs API processes requests sequentially and each `insertText` shifts
all subsequent indices. The correct approach:

1. **Insert all text** with `insertText` at index 1
2. **Re-read the doc** with `documents().get()` to get actual paragraph positions
3. **Apply styles and deletes** based on real positions

### Single BatchUpdate (Speed Critical)
After re-reading, build ALL requests (styles + deletes) in one `batchUpdate`
call. Do NOT call `batchUpdate` per-paragraph — each call is a network round-trip
and takes 1-3 seconds. For a doc with 10 headings, that's 30 seconds.

### Offset Calculation for Deletes
When deleting prefix characters (e.g. `# `) from multiple paragraphs, the
first delete shifts all subsequent positions. Fix:

- **Option A**: Execute individual `batchUpdate` calls in REVERSE index order
  (highest `startIndex` first) so earlier positions stay valid. Slow.
- **Option B**: Calculate offset in batch: `new_index = original_index - sum(all_plen_deleted_above)`
  where "above" means any delete with `original_start > current_start`. Fast.

### Paragraph Range Math
- `startIndex`: first character of paragraph content
- `endIndex`: includes the trailing newline character
- When styling: `range = {startIndex, endIndex - 1}` to avoid styling the `\n`
- When deleting: `range = {startIndex, startIndex + prefix_len}`

### Fresh Document Structure
A newly created doc has:
```json
{
  "body": {
    "content": [
      {
        "endIndex": 1,
        "sectionBreak": {
          "sectionStyle": {
            "columnSeparatorStyle": "NONE",
            "contentDirection": "LEFT_TO_RIGHT",
            "sectionType": "CONTINUOUS"
          }
        }
      }
    ]
  }
}
```
- **Only 1 element** (the sectionBreak)
- **endIndex = 1** — this is NOT text content
- Never try to `deleteContentRange` on the sectionBreak
- Insert text at `index: 1` (before the sectionBreak)

### Clearing Document Content
To clear an existing doc while preserving the sectionBreak:
```python
for element in content:
    if element.get("sectionBreak"):
        continue  # Skip the sectionBreak
    if element.get("endIndex", 1) > 1:
        requests.append({
            "deleteContentRange": {
                "range": {"startIndex": 1, "endIndex": element["endIndex"] - 1}
            }
        })
```

## Common Errors

| Error Message | Cause | Fix |
|--------------|-------|-----|
| `Invalid requests[0].deleteContentRange: The range should not be empty` | `startIndex == endIndex` | Ensure range has at least 1 character |
| `Cannot operate on the first section break in the document` | Trying to style the sectionBreak element | Only style `paragraph` elements |
| `Index must be less than the end index of the referenced segment` | Calculated index out of bounds after previous operations | Recalculate offsets, or do operations in reverse order |
| `Cannot find field: deleteRange` | API uses `deleteContentRange` not `deleteRange` | Use correct field name |

## Publishing Scope

- Prefer publishing the requested Markdown subtree only; do not silently include adjacent agent commands, specs, or roadmap files unless the user asks for them.
- When a published document links to another published Markdown file, rewrite that relative link to the target Google Docs URL.
- If a Markdown target is intentionally excluded from the publish set, use a stable source URL instead of leaving a broken relative link behind.
- Keep the cross-link map deterministic so re-runs preserve navigation.

## Markdown Conversion

### MD → Docs (Headings)
Google Docs API doesn't understand Markdown — you must:
1. Insert raw `# Heading\n` text
2. Apply `updateParagraphStyle` with `namedStyleType: HEADING_1`
3. Delete the `# ` prefix characters
4. Do all of this in a single `batchUpdate` (with offset calculations)

### MD → Docs (Bullets)
Similarly for bullets:
1. Insert raw `- item\n` text
2. Apply `createParagraphBullets` with `bulletPreset: BULLET_DISC_CIRCLE_SQUARE`
3. Delete the `- ` prefix characters
4. Do ALL deletes first (reverse order), then ALL creates (one batch)

### Docs → Markdown
Walk `body.content[]` and for each element:
- **Paragraph**: Extract `textRun.content` and check `textStyle` for bold/italic/link
- **Named styles**: Map `HEADING_1` → `# `, `HEADING_2` → `## `, etc.
- **Bullets**: Check `paragraph.bullet` exists, prepend `- `
- **Tables**: Walk `tableRows[].tableCells[].content[]` and extract text

## Performance
- `documents().get()`: ~1-2 seconds
- `batchUpdate()`: ~1-3 seconds
- Keep API calls minimal — avoid round-trips inside loops
- A typical create+populate with headings should be: 2-3 API calls total

## Critical Findings from Clone Testing (2025-04-05)

### Inline Style Application: Delete BEFORE Style (Not After)

When converting `**bold**`, `*italic*`, or `[link](url)`:
1. **Delete markers FIRST** in reverse index order (right-to-left)
2. **Apply styles SECOND** on recalculated positions

If you call `updateTextStyle` first, the API splits the paragraph:
```
Before:    paragraph = ["**bold**\n"]
After:     paragraph = ["**", "bold (BOLD)", "**\n"]
```
Then deleting ranges `0-2` and `6-8` deletes `**` and `\n`, leaving the marker
characters orphaned. Always delete markers before the text they surround gets
replaced by styled textRuns.

### HEADING Paragraphs Must Be Skipped by Inline Processor

After heading prefix deletion, the paragraph still contains its content text
(e.g., `**Issues**` in a HEADING_2 paragraph). The inline style processor
will loop infinitely trying to match and delete `**` markers on headings.
Solution: skip any paragraph where `namedStyleType` starts with `HEADING_`.

### Rate Limit Hits Fast on Real Documents

The 60 write-requests-per-minute quota gets consumed quickly:
- Each individual `batchUpdate` = 1 request
- Cloning a weekly report (8KB, 125 paragraphs) with per-paragraph inline
  style processing consumes ~288 requests in one shot
- Mitigation: batch all deletes + styles per paragraph into ONE call, or
  use the single-batch approach with pre-calculated offsets

### Google's Markdown Exporter Adds Escape Sequences

`drive.files.export(fileId, mimeType='text/markdown')` returns text with
literal `\[`, `\-`, `\*` for characters that are special in markdown. When
re-inserted via `insertText`, these display as literal backslashes. Strip
them before importing.

### Clone Accuracy Metrics (vs Original Weekly Report)

| Metric | Original | Clone | % Match |
|---|---|---|---|
| Italic runs | 19 | 19 | 100% |
| Link runs | 34 | 34 | 100% |
| Bold runs | 17 | 11 | 65% (heading bold skipped) |
| Bullets/nested lists | 69 | 0 | 0% (rate-limited) |

Inline styles (italic, links, code) are highly reliable. Bullets and heading
bold are the remaining gaps.

### Numbered List Presets — ALL Rejected

Tested and confirmed rejected by the v1 API:
- `NUMBERED_DIGITAL_ROMAN`
- `NUMBERED_DIGITAL_ALPHA_ROMAN`
- `NUMBERED_DIGITAL_PARENS`
- `NUMBERED_ARABIC_PERIOD`
- `NUMBERED_ARABIC_PARENS`
- `NUMBERED_UPPERCASE_LETTER_ALPHA_ROMAN`
- `NUMBERED_LOWERCASE_LETTER_ALPHA_ROMAN`
- `NUMBERED_UPPERCASE_ROMAN_NUMERAL_ALPHA_ROMAN`

Only `BULLET_*` presets work in `createParagraphBullets`.
