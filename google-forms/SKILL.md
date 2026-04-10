---
name: google-forms
description: Create and manage Google Forms via Google Apps Script Web App.
tags: ["Google", "Forms", "Automation"]
version: 2.1.0
---

# Google Forms Skill

Create and manage Google Forms from the CLI using a Google Apps Script Web App.

## Active Local Configuration
Use a simple shell env or `.env` file with one variable:
- `GFORMS=https://script.google.com/macros/s/.../exec`

For a fresh local setup, create `~/gform_automation/.env`:
```bash
cat > ~/gform_automation/.env <<'EOF'
GFORMS=https://script.google.com/macros/s/YOUR_WEBAPP_ID/exec
EOF
```

Load it in shell sessions with:
```bash
set -a
source ~/gform_automation/.env
set +a
```

## Setup (new account)
1. Open [script.new](https://script.new)
2. Paste the full contents of `~/gform_automation/scripts/appscript_code.gs`
3. Save
4. Deploy → New deployment → Web app
5. Set Execute as: Me
6. Set Who has access: Anyone
7. Copy the Web App URL into `~/gform_automation/.env`

## Usage
All commands go through the Forms web app.

### Create a form
Writes are a two-step redirect flow. Capture the `Location` header, then fetch that URL for the JSON response.
```bash
resp=$(curl -s -i -X POST "$GFORMS" \
  -H 'Content-Type: application/json' \
  --data-binary '{"action":"create","title":"My Form","questions":[...]}' )
loc=$(printf '%s' "$resp" | sed -n 's/^location: //Ip' | tr -d '\r')
curl -s "$loc"
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

### Convert dropdowns to Rating (Stars) in-place
```bash
curl -s -L -X POST "$GFORMS" \
  -H 'Content-Type: application/json' \
  -d '{"action":"convertListToRating","formId":"FORM_ID","titleIncludes":["VASCULARITY","PIGMENTATION"],"ratingIcon":"STAR"}'
```

## Supported Question Types
| Type | Fields | Notes |
|------|--------|-------|
| `text` | `title`, `required` | Short answer |
| `paragraph` | `title`, `required` | Long answer |
| `multiple_choice` | `title`, `required`, `options[]` | Radio buttons |
| `checkbox` | `title`, `required`, `options[]` | Multi-select |
| `dropdown` | `title`, `required`, `options[]` | Dropdown list |
| `rating` | `title`, `required`, `scaleMax` | 1-N Stars/Hearts/Thumbs |
| `date` | `title`, `required` | Date picker |
| `time` | `title`, `required` | Time picker |
| `grid` | `title`, `required`, `rows[]`, `cols[]` | Grid table |
| `email` | `title`, `required` | Email validation |

## Rating Questions (Stars 1-10)
Google Forms Rating questions use `addRatingItem()`. They support 1–10 levels and three icon styles: STAR, HEART, THUMB_UP.

```json
{
  "type": "rating",
  "title": "Rate your pain (1 = Not at all, 10 = Worst possible)",
  "required": true,
  "scaleMax": 10,
  "ratingIcon": "STAR"
}
```

## Deploy Checklist
After editing `scripts/appscript_code.gs`:
1. Save in Apps Script
2. Deploy → Manage deployments → Edit → New version → Deploy
3. Copy the new Web App URL into `~/gform_automation/.env` if it changed
4. If `Page Not Found` appears, verify access is still set to Anyone

## Known Pitfalls
1. Saving code does not update the web app; you must deploy a new version.
2. Create/update actions are redirected by Google. For writes, capture the `Location` header and fetch that URL.
3. Use `addRatingItem()` for numbered 1-10 rating questions instead of `addScaleItem()`.
4. If a command times out, retry once after a short pause; avoid backgrounding the write path.

## Forms Created
| Form | Status | Type |
|------|--------|------|
| Vancouver Scar Scale (VSS) | ✅ Created | Multiple choice with point labels |
| POSAS Observer Assessment | ✅ Created + converted to Rating | 6 parameters, Stars 1-10 |
| SCAR-Q Questionnaire | ⏳ Pending creation | 12 questions, 5-point Likert |
