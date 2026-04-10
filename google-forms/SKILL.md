---
name: google-forms
description: Create and manage Google Forms via Google Apps Script Web App.
tags: ["Google", "Forms", "Automation"]
version: 3.1.0
---

# Google Forms Skill

Create and manage Google Forms through a Google Apps Script Web App.

## What this skill uses
- Web-app flow only, no OAuth
- One env var: `GFORMS` (the deployed Web App URL)
- Python helper: `scripts/gform.py` (handles redirects, no shell pipes)

## Pre-flight check
Before using any command, run this:

```bash
python3 scripts/gform.py list
```

- If it returns JSON with forms → proceed with the user's request
- If it returns `GFORMS not set` → run the **From scratch setup** below
- If it returns an HTTP error or timeout → the web app URL may be wrong or not deployed as Anyone access

## From scratch setup
1. Open [script.new](https://script.new)
2. Paste the full contents of `~/gform_automation/scripts/appscript_code.gs`
3. Save the script
4. Deploy → New deployment → Web app
5. Set Execute as: Me
6. Set Who has access: Anyone
7. Copy the deployed Web App URL into `~/gform_automation/.env`

## Local config
Create `~/gform_automation/.env`:
```bash
cat > ~/gform_automation/.env <<'EOF'
GFORMS=https://script.google.com/macros/s/YOUR_WEBAPP_ID/exec
EOF
```

## Core workflow — Python helper (primary)

Use `scripts/gform.py` for all actions. It handles the redirect automatically and works in sandboxed environments where `curl | sed` piping is blocked.

### List forms
```bash
python3 scripts/gform.py list
```

### Get form
```bash
python3 scripts/gform.py get FORM_ID
```

### Create a form
```bash
python3 scripts/gform.py create --title "My Form" --description "Optional desc"
```

For forms with questions, use a JSON file:
```bash
cat > /tmp/questions.json <<'JSON'
[
  {"type": "text", "title": "Your name", "required": true},
  {"type": "paragraph", "title": "Your feedback", "required": true}
]
JSON
python3 scripts/gform.py create --title "Feedback Form" --questions /tmp/questions.json
```

### Add questions to existing form
```bash
python3 scripts/gform.py add-questions FORM_ID /tmp/questions.json
```

### Get responses
```bash
python3 scripts/gform.py responses FORM_ID
```

### Raw JSON mode
```bash
python3 scripts/gform.py '{"action":"list"}'
```

## Core workflow — bash helper (fallback)

If Python is unavailable, define this bash function first:

```bash
gform() {
  resp=$(curl -s -i -X POST "$GFORMS" -H 'Content-Type: application/json' --data-binary "$1")
  loc=$(printf '%s' "$resp" | sed -n 's/^location: //Ip' | tr -d '\r')
  if [ -z "$loc" ]; then printf '%s' "$resp" | tail -c 500; else curl -s "$loc"; fi
}
```

Then: `gform '{"action":"list"}'`

**Warning:** Some sandbox environments block `curl ... | sed ...` piping. Use the Python helper instead when this happens.

## Markdown template
For a copy-paste starting point with every question type, see `references/form-markdown-template.md`. Write the form structure in markdown first, then convert to JSON for the payload.

## Question patterns
Use generic, reusable patterns when building forms:

- `text`: short free-text answer
- `paragraph`: longer free-text answer
- `multiple_choice`: one answer from a list
- `checkbox`: many answers from a list
- `dropdown`: one answer from a compact list
- `rating`: numeric rating from 1 to N
- `date`: date picker
- `time`: time picker
- `grid`: matrix-style question with rows and columns
- `email`: email field with validation

### Generic examples
```json
{"type":"text","title":"Your name","required":true}
```

```json
{"type":"multiple_choice","title":"Which option best fits?","required":true,"options":["Option A","Option B","Option C"]}
```

```json
{"type":"checkbox","title":"Select all that apply","required":false,"options":["Option A","Option B","Option C"]}
```

```json
{"type":"rating","title":"Rate this item","required":true,"scaleMax":10}
```

## Supported question types
| Type | Fields | Notes |
|------|--------|-------|
| `text` | `title`, `required` | Short answer |
| `paragraph` | `title`, `required` | Long answer |
| `multiple_choice` | `title`, `required`, `options[]` | Radio buttons |
| `checkbox` | `title`, `required`, `options[]` | Multi-select |
| `dropdown` | `title`, `required`, `options[]` | Dropdown list |
| `rating` | `title`, `required`, `scaleMax` | 1-N stars/hearts/thumbs |
| `date` | `title`, `required` | Date picker |
| `time` | `title`, `required` | Time picker |
| `grid` | `title`, `required`, `rows[]`, `cols[]` | Grid table |
| `email` | `title`, `required` | Email validation |

## Rating questions
Google Forms rating questions use `addRatingItem()`. They support 1-10 levels and three icon styles: STAR, HEART, THUMB_UP.

```json
{
  "type": "rating",
  "title": "Rate this section",
  "required": true,
  "scaleMax": 10,
  "ratingIcon": "STAR"
}
```

## Deploy checklist
After editing `scripts/appscript_code.gs`:
1. Save in Apps Script
2. Deploy → Manage deployments → Edit → New version → Deploy
3. Copy the new Web App URL into `~/gform_automation/.env` if it changed
4. If `Page Not Found` appears, verify access is still set to Anyone

## Known pitfalls
1. Saving code does not update the web app; you must deploy a new version.
2. **All actions redirect** (302 + Location). `curl -L` returns HTML instead of JSON. Always use the Python helper or the bash redirect pattern.
3. Use `addRatingItem()` for numbered 1-10 rating questions instead of `addScaleItem()`.
4. If a command times out, retry once after a short pause; avoid backgrounding the write path.
5. If create fails silently, check the raw response for errors. Do not blindly retry create or you will produce duplicate forms.
