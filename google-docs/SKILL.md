---
name: google-docs
description: Create, edit, and publish Google Docs with professional formatting, tables, and internal links using natural language.
tags: ["Google", "Docs", "Writing", "Publishing"]
version: 4.0.0
---

# Google Docs Skill

This skill allows you to create and manage Google Docs directly from the chat. You don't need to worry about formatting, APIs, or technical setup—I handle the complexity in the background.

## ✍️ What can I do for you?

You can simply ask me in plain English:

*   **Create a Document**: "Draft a weekly report titled 'Q3 Goals'."
*   **Publish a Collection**: "Publish all docs in my `specs/` folder and make sure the links between them work."
*   **Create a Mega-Doc**: "Combine these files into one single Google Doc with sections."
*   **Edit & Convert**: "Export the 'Architecture' doc to Markdown" or "Find and replace 'Project X' with 'Project Y'."

## ⚙️ Setup (Do this once)

1.  **Authentication**: Ensure I have access to your Google Workspace (via `google_token.json`).
2.  **Just start asking**: You usually don't need to do anything else.

## 🤖 Agent Interaction Guide

*   **When creating a doc**: Ask the user for a title if they don't provide one.
*   **When publishing folders**: Ask the user to confirm the directory and if they want me to fix internal cross-links (e.g., changing `design.md` to a live Google Doc URL).
*   **Technical Reference**: For detailed API limitations (e.g., "Tabs are not supported") and script locations, see `references/publishing-guide.md`.
