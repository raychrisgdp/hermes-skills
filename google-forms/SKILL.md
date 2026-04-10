---
name: google-forms
description: Create and manage Google Forms via Google Apps Script Web App.
tags: ["Google", "Forms", "Automation"]
version: 2.3.0
---

# Google Forms Skill

Create and manage Google Forms through a Google Apps Script Web App.

## What this skill uses
- Web-app flow only for normal use
- No OAuth for the normal path
- One required env var: `GFORMS`
- Optional env var if your deployment enforces it: `GFORMS_SECRET`

## From scratch setup
1. Open [script.new](https://script.new)
2. Paste the full contents of `~/gform_automation/scripts/appscript_code.gs`
3. Save the script
4. Deploy → New deployment → Web app
5. Set Execute as: Me
6. Set Who has access: Anyone
7. Copy the deployed Web App URL into `~/gform_automation/.env`
8. If your script uses a shared secret, generate one and store it in both the Apps Script code and `GFORMS_SECRET`

## Local config
Create `~/gform_automation/.env`:
```bash
cat > ~/gform_automation/.env <<'EOF'
GFORMS=https://script.google.com/macros/s/YOUR_WEBAPP_ID/exec
# Optional, only if your deployed script checks a secret:
# GFORMS_SECRET=YOUR_SHARED_SECRET
EOF
```

Load it in shell sessions with:
```bash
set -a
source ~/gform_automation/.env
set +a
```

## Core workflow
All actions go through the web app.

### Create a form
Writes return a redirect first. Capture the `Location` header, then fetch that URL for the JSON response.
```bash
payload='{"action":"create","title":"My Form","description":"Optional description","questions":[...]}'

resp=$(curl -s -i -X POST "$GFORMS" \
  -H 'Content-Type: application/json' \
  --data-binary "$payload")

loc=$(printf '%s' "$resp" | sed -n 's/^location: //Ip' | tr -d '\r')
curl -s "$loc"
```

If your deployment requires a secret, include it in the JSON body:
```bash
payload='{"secret":"'"$GFORMS_SECRET"'","action":"create",...}'
```

### List forms
```bash
curl -s -L -X POST "$GFORMS" -H 'Content-Type: application/json' -d '{"action":"list"}'
```

### Get form
```bash
curl -s -L -X POST "$GFORMS" -H 'Content-Type: application/json' -d '{"action":"get","formId":"FORM_ID"}'
```

### Add questions
```bash
curl -s -L -X POST "$GFORMS" \
  -H 'Content-Type: application/json' \
  -d '{"action":"addQuestions","formId":"FORM_ID","questions":[{"type":"rating","title":"Rate 1-10","required":true,"scaleMax":10}]}'
```

### Get responses
```bash
curl -s -L -X POST "$GFORMS" -H 'Content-Type: application/json' -d '{"action":"responses","formId":"FORM_ID"}'
```

## Question building blocks
Use these generic patterns when building forms:

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
Google Forms rating questions use `addRatingItem()`. They support 1–10 levels and three icon styles: STAR, HEART, THUMB_UP.

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
4. If your script uses a secret, update `GFORMS_SECRET` to match
5. If `Page Not Found` appears, verify access is still set to Anyone

## Known pitfalls
1. Saving code does not update the web app; you must deploy a new version.
2. Create/update actions may redirect. For writes, capture the `Location` header and fetch that URL.
3. Use `addRatingItem()` for numbered 1-10 rating questions instead of `addScaleItem()`.
4. If a command times out, retry once after a short pause; avoid backgrounding the write path.
5. If you use a shared secret in your deployment, the request body must include the matching `secret` field.

## Legacy OAuth path
The older `scripts/forms_api.py` path exists, but it is not the normal path for this skill. Treat it as legacy/OAuth-only unless you specifically need the OAuth CLI route.
