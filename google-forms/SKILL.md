---
name: google-forms
description: Create and manage Google Forms using natural language.
tags: ["Google", "Forms", "Automation", "Productivity"]
---

# Google Forms Skill

Create surveys, feedback forms, or quizzes by simply asking. I handle the setup and creation.

## 📝 What can I do for you?

*   **Create a Form**: "Make a form for my team's daily standup."
*   **Check Responses**: "How many responses has the 'VSS' form received?"
*   **Edit Forms**: "Add a rating question to the 'Customer Feedback' form."
*   **Link Data**: "Link the 'Workshop RSVP' responses to a new Google Sheet."

## ⚙️ Setup (Do this once)
To create forms, I need a "Bridge" to your Google account.
1.  I will provide you with a script to paste into Google Apps Script (script.new).
2.  You deploy it as a "Web App" with access set to "Anyone".
3.  You give me the "Web App URL" the script generates.

## 🤖 Agent Interaction Guide
*   **Always check for script setup first.** If the user hasn't provided a Web App URL, guide them through the setup in `references/form-setup.md`.
*   **Ask for details:** If creating a form, ask "What kind of questions do you want?" or "Should we use a template?".
