---
name: google-docs
description: Create, edit, and publish Google Docs with professional formatting, tables, and internal links using natural language.
tags: ["Google", "Docs", "Writing", "Publishing"]
version: 4.1.0
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
*   **When publishing folders**: Ask the user to confirm the directory scope and whether to rewrite internal cross-links (e.g., changing `design.md` to a live Google Doc URL).
*   **When publishing docs sets**: Prefer publishing only the requested Markdown subtree unless the user explicitly asks for specs, commands, or other adjacent content.
*   **When the docs contain Mermaid**: Render the diagrams locally to images, insert them inline after the anchor paragraph/heading, and keep the images sized to fit the page.
*   **When the user wants a doc synced**: Re-export or inspect the result after publishing so you can verify that links, code blocks, and images actually rendered the way you intended.
*   **Operational recipes**:
    *   Auth check: `python3 ~/.hermes/skills/productivity/google-docs/scripts/setup.py --check`
    *   Publish a folder: `python3 ~/.hermes/skills/productivity/google-docs/scripts/publish_pipeline.py /path/to/markdown/folder`
    *   Inspect a doc: `python3 ~/.hermes/skills/productivity/google-docs/scripts/docs_api.py get <doc_id> --md`
    *   Inspect raw structure: `python3 ~/.hermes/skills/productivity/google-docs/scripts/docs_api.py get <doc_id> --raw`
    *   Insert an image: use `scripts/docs_advanced.py` `insert_image(doc_id, image_path, start_index=..., width_pts=..., height_pts=...)`
*   **Technical Reference**: For detailed API limitations (e.g., "Tabs are not supported"), Markdown conversion caveats, and script locations, see `references/api-lessons.md`.
