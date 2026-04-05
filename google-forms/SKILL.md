---
name: google-forms
description: Create and automate Google Forms via Google Apps Script Web App. No OAuth needed — runs under your personal Google account. Supports create, list, get, addQuestions, responses, and convertListToRating actions.
tags: ["Google", "Forms", "Apps Script", "Automation", "Medical"]
related_skills: ["google-workspace"]
---

# Google Forms

Create and manage Google Forms from the CLI using a Google Apps Script Web App. No OAuth, no Google Cloud Console — just deploy and use curl.

## Architecture

```
┌─────────────┐      ┌────────────────────┐      ┌──────────────────┐
│  CLI / AI   │─────▶│ Apps Script Web App│─────▶│ Google Forms API │
│  curl POST  │      │  (runs as YOU)     │      │  (created/edited)│
└─────────────┘      └────────────────────┘      └──────────────────┘
```

## Setup

① Go to [script.new](https://script.new)
② Delete default code → Paste `scripts/appscript_code.gs`
③ Save
④ Deploy → New deployment → Web app → Execute as: Me → Who has access: Anyone
⑤ Copy the Web App URL

## Usage

```bash
GFORMS="https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec"

# Create a form
curl -L "$GFORMS" \
  -H 'Content-Type: application/json' \
  -d '{"action":"create","title":"My Form","questions":[]}'

# List forms
curl "$GFORMS" -d '{"action":"list"}'

# Get form
curl "$GFORMS" -d '{"action":"get","formId":"FORM_ID"}'

# Add questions
curl -L "$GFORMS" \
  -H 'Content-Type: application/json' \
  -d '{"action":"addQuestions","formId":"FORM_ID","questions":[
    {"type":"rating","title":"Rate 1-10","required":true,"scaleMax":10}
  ]}'

# Get responses
curl "$GFORMS" -d '{"action":"responses","formId":"FORM_ID"}'

# Convert dropdowns to Rating (Stars)
curl -L "$GFORMS" \
  -H 'Content-Type: application/json' \
  -d '{"action":"convertListToRating","formId":"FORM_ID","titleIncludes":["VASCULARITY","PIGMENTATION"],"ratingIcon":"STAR"}'
```

## Question Types

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

## Forms Created

| Form | Form ID | Status |
|------|---------|--------|
| Vancouver Scar Scale (VSS) | 170rIEqaiHG9pb1PmZYFcBFH0pZZYHbj4WqRjIxT3PkU | Multiple choice (created) |
| POSAS Observer Assessment | 1f9TkbEl8iULUJqriLUVUp8AAJOombjXs2mewzfy2Xdo | Rating (Stars 1-10, converted) |
| SCAR-Q Questionnaire | (pending) | Not yet created |

## Lessons Learned & Technical Findings

- **Rating vs Scale**: Do NOT use `type: "scale"` for 1-10 ratings. `ScaleItem.setLowerBound()` often fails with `TypeError` in Web App contexts.
  - **Fix**: Use `type: "rating"` which invokes `FormApp.addRatingItem()`. It supports 1-10 levels, 3 icon styles (STAR, HEART, THUMB_UP), and works reliably in Web Apps.
- **Deployments**: After editing code, you MUST select **"New version"** in "Manage deployments", otherwise the Web App serves old code silently.
- **Redirects**: When curling the Web App URL, always use `-L` (follow redirects) or resolve the execution URL first to avoid `doGet not found` errors.

## Local Project Structure
Raymond manages the local definitions and script at `~/gform_automation/`.
- `GFORM_AUTOMATION.md`: Definitions for VSS, POSAS, SCAR-Q.
- `scripts/appscript_code.gs`: The master script to be pasted into Apps Script.

## Troubleshooting

| Problem | Fix |
|--------|-----|
| `TypeError: item.setLowerBound...` | Change `type: "scale"` to `type: "rating"` in payload. |
| `Unknown action` | Redeploy script with "New version". |
| "Page Not Found" | Check Deployment permissions -> "Anyone". |
| `setLowerBound not found` | Use `rating` type with `addRatingItem()` instead of `scale` type |
| "Page Not Found" (HTML response) | Check "Who has access: Anyone" in deployment settings |