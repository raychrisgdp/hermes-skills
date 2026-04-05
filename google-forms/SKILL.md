---
name: google-forms
description: Create and manage Google Forms using natural language. The AI handles the technical details.
tags: ["Google", "Forms", "Automation", "Productivity"]
---

# Google Forms Skill

This skill allows you to create, edit, and manage Google Forms just by asking. You don't need to know about APIs, code, or technical setups—I handle all that in the background.

## What can I do with this skill?

You can simply ask me:

### 📝 Create a New Survey
* "Create a survey for customer feedback on our new website."
* "Make a form for employee satisfaction with ratings from 1-10."
* "I need a registration form for the upcoming workshop with name, email, and dietary preferences."

### 🔍 View Existing Forms
* "Show me a list of all my Google Forms."
* "How many responses has my 'Customer Feedback' form received?"
* "Who filled out the 'Holiday Party RSVP' form?"

### ✏️ Edit a Form
* "Add a question to my 'Feedback' survey asking for suggestions."
* "Change the title of Form ID 123... to '2026 Annual Review'."

### 📊 Export Responses
* "Download the responses from the 'Employee Satisfaction' form."
* "Link the responses from 'Workshop RSVP' to a Google Sheet so I can analyze them."

---

## ⚙️ Initial Setup (Do this once)

*To give me permission to create forms on your behalf, I need you to authorize a "Script" to act as you. This takes about 2 minutes.*

1.  **Open Google Scripts**: Go to [script.new](https://script.new) (this opens a blank script in your Google account).
2.  **Paste the Code**: 
    *   Delete the few lines of text currently there.
    *   Copy the code I provide (usually located in the `scripts/appscript_code.gs` file of this skill) and paste it there.
3.  **Save**: Click the floppy disk icon (💾) or press `Ctrl+S`. Name it "GL Forms Automation" or similar.
4.  **Deploy**: 
    *   Click the blue **"Deploy"** button (top right).
    *   Select **"New deployment"**.
    *   Click the **Gear icon ⚙️** next to "Select type" and choose **"Web app"**.
    *   **Description**: "Forms Tool"
    *   **Execute as**: `Me` (raymond.christopher@gdplabs.id)
    *   **Who has access**: ✅ **Anyone** (This is important so I can talk to the script).
5.  **Authorize**: 
    *   Click **"Deploy"**.
    *   Google will ask for permission. Click **"Review permissions"**, choose your account, and if it says "Google hasn't verified this app", click **"Advanced"** -> **"Go to (unsafe)"**. This is safe—it's *your* script.
6.  **Copy the URL**: You will see a "Web App URL" ending in `/exec`. **Copy this link** and send it back to me.
    *   *Example:* `https://script.google.com/macros/s/...A.../exec`

Once you give me that link, I can create and manage forms for you instantly!

---

## 📋 Supported Question Types

When we create forms, I can handle all these question types:

*   **Short Answer / Paragraph**: For open text feedback.
*   **Multiple Choice**: For selecting one option (like "Yes/No").
*   **Checkboxes**: For selecting multiple options (like "Which topics interest you?").
*   **Dropdown**: For a compact list of options.
*   **Rating (Stars/Hearts/Thumbs)**: For scoring satisfaction (1-5 or 1-10).
*   **Date / Time**: For scheduling.
*   **Grid**: For complex matrices (e.g., rate 5 different aspects on a scale of 1-5).

## 📍 Where is the code?

The local scripts and automation definitions are managed in your local folder here:
📂 `~/gform_automation/`
