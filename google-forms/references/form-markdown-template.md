# Form Markdown Template

Copy-paste this template to define a form in markdown, then convert to JSON for the Apps Script endpoint.

## Template

```
# Form Title Here

description: A short description of what this form is for.

---

## Question 1 - Short Text
type: text
required: true

---

## Question 2 - Email
type: email
required: true

---

## Question 3 - Multiple Choice
type: multiple_choice
required: true
options:
  - Option A
  - Option B
  - Option C

---

## Question 4 - Checkboxes
type: checkbox
required: false
options:
  - Choice X
  - Choice Y
  - Choice Z

---

## Question 5 - Dropdown
type: dropdown
required: false
options:
  - Choice 1
  - Choice 2
  - Choice 3

---

## Question 6 - Rating
type: rating
required: true
scaleMax: 10
ratingIcon: STAR

---

## Question 7 - Date
type: date
required: false

---

## Question 8 - Grid
type: grid
required: true
rows:
  - Row A
  - Row B
  - Row C
cols:
  - Poor
  - Fair
  - Good
  - Excellent

---

## Question 9 - Long Paragraph
type: paragraph
required: false
```

## Format Rules

- H1 (`# Title`) → form title
- `description: ...` line → form description
- Separate questions with `---`
- Each question block: H2 = title, then `type`, `required`, and type-specific fields

## Markdown Type → JSON Mapping

| markdown type | JSON fields |
|---|---|
| `text` | `{type: "text", title, required}` |
| `paragraph` | `{type: "paragraph", title, required}` |
| `email` | `{type: "email", title, required}` |
| `multiple_choice` | `{type: "multiple_choice", title, required, options[]}` |
| `checkbox` | `{type: "checkbox", title, required, options[]}` |
| `dropdown` | `{type: "dropdown", title, required, options[]}` |
| `rating` | `{type: "rating", title, required, scaleMax, ratingIcon}` |
| `date` | `{type: "date", title, required}` |
| `time` | `{type: "time", title, required}` |
| `grid` | `{type: "grid", title, required, rows[], cols[]}` |

## Notes

- Use `rating` (not `scale`) — `scale` is broken in the Apps Script backend.
- `scaleMax`: 3–10. `ratingIcon`: `STAR`, `HEART`, or `THUMB_UP`.
- The SKILL.md JSON examples are the source of truth for the API. This template is a shorthand for planning forms before assembling the curl payload.
