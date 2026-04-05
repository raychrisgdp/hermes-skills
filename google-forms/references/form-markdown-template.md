# Form Title Here

description: A short description of what this form is for

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

## Question 4 - Checkboxes (select all)
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

## Question 6 - Scale Rating
type: scale
required: true
scaleMin: 1
scaleMax: 5

---

## Question 7 - Date
type: date
required: false

---

## Question 8 - Grid (multi-row rating)
type: grid
required: true
rows:
  - Row Item A
  - Row Item B
  - Row Item C
cols:
  - Poor
  - Fair
  - Good
  - Excellent

---

## Question 9 - Long Paragraph
type: paragraph
required: false
