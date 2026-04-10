# Publishing Scope

## Default rule
- Publish only the Markdown subtree the user asked for.
- Do not silently include adjacent agent commands, specs, or roadmap files.

## Cross-link rewrite
- Rewrite relative links between published Markdown files into live Google Docs URLs.
- If a linked Markdown file is intentionally excluded, replace the link with a stable source URL instead of leaving a broken `.md` path.
- Keep the cross-link map deterministic so reruns preserve navigation.

## Multi-doc handoff
- If the user wants separate docs that later point back into a tabbed parent doc, keep the original tab URLs as canonical destinations.
- Rewrite links inside the separate docs toward those original tab URLs when asked.

## Practical check
- After publishing, inspect the rendered doc and make sure the links point where the user expects.
