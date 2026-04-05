---
name: google-forms
description: Create and manage Google Forms via Google Apps Script Web App.
tags: ["Google", "Forms", "Automation"]
---

# Google Forms Skill

Create and manage Google Forms from the CLI using a Google Apps Script Web App.

## 📍 Active Local Configuration
**⚠️ DO NOT ASK USER TO REDEPLOY UNLESS NECESSARY.**
The following URL is valid for the current user (raymond.christopher@gdplabs.id):
`https://script.google.com/macros/s/AKfycbwF-9jdH5fM8JmLfttqc9OhvJTawGzeaf3fzRVQWVYezI-oyB2dVEhuhI7Vw2RVJQfLfg/exec`

## 📖 For Other Users (Setup Guide)
*To create forms on a new account, you must deploy the script:*
1.  **Open**: [script.new](https://script.new)
2.  **Paste Code**: Copy `scripts/appscript_code.gs` and paste it.
3.  **Deploy**: New deployment -> Web app -> Execute as: **Me** -> Access: **Anyone**.
4.  **Share URL**: Copy the generated URL and provide it to the agent.

## 🤖 Agent Instructions
1.  **Check for Active URL**: Look at the "Active Local Configuration" section.
2.  **If URL exists**: Use it immediately for curl commands.
3.  **If URL is missing / User is new**: Guide them through "For Other Users (Setup Guide)" above.

## 📝 Architecture & Scripts
*   **CLI Wrapper**: `scripts/forms_api.py` (Handles OAuth if not using Web App).
*   **Web App Script**: `scripts/appscript_code.gs`.
