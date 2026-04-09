---
name: google-docs
description: Create, edit, and publish Google Docs with professional formatting, tables, and internal links using natural language.
tags: ["Google", "Docs", "Writing", "Publishing"]
version: 4.3.0
---

# Google Docs Skill

Use this skill for Google Docs creation, publishing, link rewriting, review comments, and doc sync work.

## Quick capabilities
- Create new docs
- Publish Markdown folders into native Google Docs
- Rewrite internal links to live Google Docs URLs
- Render Mermaid locally and insert it as inline images, using landscape page sections when a diagram is wide
- Inspect docs after publishing to verify the result
- Manage review comments and reply threads

## When to use what
- For auth/setup: `references/auth-and-setup.md`
- For publish scope and cross-links: `references/publishing-scope.md`
- For Markdown import/update behavior: `references/markdown-pipeline.md`
- For Mermaid and image insertion: `references/mermaid-images.md`
- For comments and review threads: `references/review-comments.md`
- For API retries, timeouts, and large-doc handling: `references/reliability-and-timeouts.md`
- For exact shell commands: `references/command-recipes.md`
- For the longer API caveats index: `references/api-lessons.md`

## Operating rule
Keep this top-level file short. Put workflow detail in the linked references so the main skill stays easy to scan.