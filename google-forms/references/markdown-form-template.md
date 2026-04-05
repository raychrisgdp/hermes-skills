# Markdown-Based Form Definition Format

Convert a simple Markdown file into a Google Form via the Apps Script endpoint.

## Format Rules

```
# Form Title

description: Optional description text for the form.

---

## Question 1
type: text|paragraph|multiple_choice|checkbox|dropdown|scale|date|time|email|grid|duration
required: true or false
options:    (for multiple_choice, checkbox, dropdown)
  - Option 1
  - Option 2
  - Option 3
scaleMin: 1  (for scale type, default 1)
scaleMax: 5  (for scale type, default 5)
rows:         (for grid type)
  - Row 1
  - Row 2
cols:         (for grid type)
  - Col 1
  - Col 2
  - Col 3
```

Each question is separated by `---`. The `---` acts as a delimiter.

## Example

```
# Event RSVP Form

description: Please RSVP by Friday.

---

## Full Name
type: text
required: true

---

## Will you attend?
type: multiple_choice
required: true
options:
  - Yes, count me in
  - Can't make it
  - Maybe later

---

## Dietary Restrictions
type: checkbox
required: false
options:
  - Vegetarian
  - Vegan
  - Gluten-free
  - None

---

## Rate your excitement (1-5)
type: scale
required: true
scaleMin: 1
scaleMax: 5

---

## Rate the following topics
type: grid
required: false
rows:
  - AI
  - Blockchain
  - Cloud
cols:
  - Not interested
  - Somewhat interested
  - Very interested

---

## Any comments?
type: paragraph
required: false
```

## Parser Logic (Python)

To convert markdown into the JSON payload for the Apps Script endpoint:

1. H1 (`# Title`) → form title
2. `description: ...` line → form description
3. Split remaining content by `---` to get question blocks
4. For each block:
   - H2 (`## Question`) → question title
   - `type:` → question type
   - `required:` → boolean
   - `options:` / `rows:` / `cols:` → list items (lines starting with `  - `)

## Question Type to JSON Mapping

| markdown type | JSON action |
|---|---|
| text | `{type: "text", title, required}` |
| paragraph | `{type: "paragraph", title, required}` |
| multiple_choice | `{type: "multiple_choice", title, required, options[]}` |
| checkbox | `{type: "checkbox", title, required, options[]}` |
| dropdown | `{type: "dropdown", title, required, options[]}` |
| scale | `{type: "scale", title, required, scaleMin, scaleMax}` |
| date | `{type: "date", title, required}` |
| time | `{type: "time", title, required}` |
| email | `{type: "email", title, required}` |
| grid | `{type: "grid", title, required, rows[], cols[]}` |
| duration | `{type: "duration", title, required}` |
