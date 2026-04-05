---
name: google-docs
description: Create, edit, and publish Google Docs with professional formatting, tables, and internal links using natural language.
tags: ["Google", "Docs", "Writing", "Publishing"]
---

# Google Docs Skill

This skill allows you to create and manage Google Docs directly from the chat. You don't need to worry about formatting, APIs, or technical setup — I handle the complexity in the background.

## 📝 What can I do for you?

Simply ask me in plain English:

### 📄 Create a Document
* "Create a new document for our weekly team meeting."
* "Make a document from this text..."
* "Draft a project proposal titled 'Project Alpha'."

### 📤 Publish a Collection (The "Pipeline")
If you have a folder of technical documents (like a design spec) where one file points to another, I can publish them all at once.
* "Publish the docs in the `specs/` folder."
* "Update my documentation and make sure all the links between them work."
* "Create a 'Mega-Doc' that combines all these files into one Google Doc."

> **How cross-linking works**: I automatically convert links like `[Link to Design](design.md)` into clickable links to the actual live Google Docs, so your team can navigate between documents seamlessly.

### ✏️ Edit & Convert Formats
* "Export the 'Architecture' doc to Markdown."
* "Find and replace all mentions of 'Project X' with 'Project Y' in my document."
* "Add a table to the bottom of the document."

## ⚙️ Setup (Do this once)

To let me create documents on your behalf, I need access to your Google Drive. The system is typically already set up with your credentials. 

If I need a specific permission, I will guide you through it step-by-step.

## 🔧 The Publishing Pipeline (Technical Details)

For AI reference, the pipeline works as follows:

### The Key Insight: Drive Import vs. batchUpdate
The **critical lesson** discovered was that the Google Docs API's `batchUpdate` method is fundamentally broken for creating documents from Markdown:
- Requires 50+ API calls per document
- Hits rate limits (60 writes/minute) and times out often
- Index math breaks when deleting/replacing text
- Cannot create tables
- Produces garbled, broken formatting

**✅ The working solution**: Upload Markdown directly via the Drive Import API.
This creates a native Google Doc in a single call with perfect tables, headings, bold/italic, and lists.

### Pipeline Steps
1. **Scan**: Find all Markdown files in a directory.
2. **Map**: For each file, find an existing Google Doc with the same title (to preserve links pointing to it).
3. **Publish**: Upload via Drive API as `text/markdown`. This creates a natively formatted Google Doc instantly.
4. **Cross-link**:
   - Extract all relative links from the Markdown (e.g., `[Link to Design](design.md)`).
   - Build a map: `filename.md → Google Docs URL`.
   - Rewrite the content with those permanent Google Docs URLs.
   - Update the doc content with the rewritten text.
5. **Report**: Provide the user with links to all published documents.

### Local Scripts
* `scripts/publish_pipeline.py`: The main pipeline script.
* `scripts/docs_api.py`: Core CRUD operations (get, list, append, find-replace, export).
* `scripts/docs_advanced.py`: Handling tables and images within the Doc.
* `scripts/setup.py`: OAuth2 credential management.

### Key Limitations
* **Tabs**: The Google Docs API does not support creating "Document Tabs" (the UI tabs in Google Docs). For a tabbed experience, we either create multiple docs with cross-links or use section breaks (Pages) within a single doc.
* **Numbered Lists**: The API does not support creating nested numbered lists natively.
* **Cross-link updates**: If a document's title/ID changes, links in other documents pointing to it become stale.
