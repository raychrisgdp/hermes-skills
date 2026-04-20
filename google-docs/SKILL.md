---
name: google-docs
description: Create, edit, and publish Google Docs with professional formatting, tables, and internal links using natural language.
tags: ["Google", "Docs", "Writing", "Publishing"]
version: 1.1
---

# Publishing Scope

## Default rule
- Publish only the Markdown subtree the user asked for.
- Do not silently include adjacent agent commands, specs, or roadmap files.
- For an end-to-end replication recipe with exact CLI/script commands, see `references/command-recipes.md`.
- For preview validation rules, orientation decisions, and diagram-fit checks, see `references/preview-validation.md`.

## Multi-doc cross-link sync workflow

When publishing multiple Markdown files that cross-link each other, use this order:

### Step 1: Create all docs and collect URLs

```
doc_ids = {}
for filename in order:
    doc_id = get_or_create(doc, title)
    doc_ids[filename] = doc_id
link_map[filename] = f"https://docs.google.com/document/d/{doc_id}/edit"
```

### Step 2: Rewrite links before publishing

```
for filename in order:
    md_content = rewrite_links(original_md, link_map)
    md_content = strip_mermaid(md_content)
    md_content = convert_fenced_to_indented(md_content)
    update_or_create_doc(drive, doc_id, md_content)
```

### Step 3: Insert Mermaid images after import

After content import, read the doc structure, find heading anchors, and insert rendered PNGs.

### Why order matters

- If you publish doc A before doc B exists, links from A to B become broken `.md` paths.
- Create all docs first (get all IDs), build the link map, then do a single pass to rewrite + republish.
- If a new doc has no existing ID, create it first, collect its URL, add it to the link map, then resync the other docs that may link to it.

### Performance: insert images in reverse order

When inserting images after a heading, read the doc structure once, find all anchor indices, then insert from **highest index to lowest**. This avoids needing to re-read the doc after every insertion because earlier indices don't shift when you insert later.

### For long syncs (5+ docs with diagrams)

Use background execution with `notify_on_complete=true` to avoid shell timeouts:

```
<python-with-google-deps> sync_script.py 2>&1
```

## Cross-link rewrite
- Rewrite relative links between published Markdown files into live Google Docs URLs.
- If a linked Markdown file is intentionally excluded, replace the link with a stable source URL instead of leaving a broken `.md` path.
- Keep the cross-link map deterministic so reruns preserve navigation.
- If the user gives a canonical combined Google Doc URL for a doc family, update the sibling docs in place so every stale intra-family link points to that canonical URL.
- To retarget an existing link in a live Google Doc, read the raw structure, collect the exact text ranges that carry the old URL, and use `updateTextStyle` with the new `link.url` on those ranges; then verify with a second raw export that no stale URLs remain.
- If a narrow `--fields` read becomes awkward or errors on nested selectors, fall back to `--raw` and filter the structure yourself.

## Multi-doc handoff
- If the user wants separate docs that later point back into a tabbed parent doc, keep the original tab URLs as canonical destinations.
- Rewrite links inside the separate docs toward those original tab URLs when asked.
- If the user explicitly asks for a separate Google Doc generated from the latest markdown, do not mutate the existing live doc; create a fresh doc from the source file and return the new URL.
- For that first-pass standalone doc, use the clean Markdown publish pipeline when possible instead of ad hoc create/update calls; it is much more reliable for native tables, links, bold, and heading rendering.
- If a doc still shows raw Markdown artifacts after import, recreate it from the source Markdown rather than repeatedly patching the malformed import in place.
- When a doc create/update hits Docs API write quota limits (429 rate limit), back off and retry later rather than hammering the endpoint in the same minute.

## Cross-linking between Markdown siblings and Google Docs
- When a doc family contains links to other markdown files in the same set, rewrite those links to the corresponding Google Docs URLs before publishing.
- Build the full URL map first, then publish in a second pass so links never point at `.md` paths inside Google Docs.
- If a document is recreated with a new Google Doc ID, update the link map immediately and republish the other docs that reference it.
- If the target document is being recreated because the old import is malformed (for example, a plain-text doc that should have been markdown-formatted), prefer creating a brand-new doc ID rather than trying to salvage the broken one.
- After recreation, treat the new doc ID as canonical and rewrite every inbound link to the new URL before the next publish pass.

## Markdown import fallback for stubborn docs
- If `text/markdown` import times out or the formatting is wrong, recreate the doc via the Docs API and apply formatting programmatically.
- For architecture-style docs, it can be safer to create a fresh doc than to try to repair a badly imported one.
- If the existing doc is malformed or visually corrupted, prefer creating a brand-new Google Doc from the source Markdown rather than trying to salvage the broken import in place.
- Use heading styles, bullets, bold/link styles, and inline images to recover the formatting model.
- If the markdown import leaves the document as plain text, clear the broken import and reinsert content through the Docs API so headings and links are styled correctly.
- If the markdown import leaves image syntax like `![alt](path.png)` as literal text, insert the PNG inline with the Docs API (`docs_advanced.insert_image`) at the target paragraph index, then remove the placeholder line.
- Diagram/image inserts should be center-aligned by default for consistency (`insert_image(..., center=True)`).
- In multi-tab docs, pass `tab_id` on insert and section-orientation requests so operations land in the intended tab.
- For tab-aware reads, use `documents.get(..., includeTabsContent=True)` and read from `tabs[].documentTab.body.content`; note that field masks cannot mix `tabs(...)` and legacy top-level `body/documentStyle` fields in one request.
- You can append a new tab to an existing doc with `addDocumentTab` (helper: `docs_advanced.add_document_tab`).
- Prefer a full-resolution public image URI from Drive (`webContentLink` when available) instead of a thumbnail URL; thumbnail-based insertion can look soft in Docs.
- If a multi-doc refresh stalls on an existing Google Doc, create fresh docs for the affected files, republish from rewritten Markdown, and update inbound links to the new IDs.
|- For diagram-heavy docs, prefer a deterministic pipeline: render Mermaid locally to SVG/PNG first, import stripped Markdown, then insert the rendered images inline after the imported structure is available.
|- When matching insertion anchors, normalize text by stripping backticks, collapsing whitespace, and comparing lowercase text.
|- Insert images from bottom to top so document indices do not drift.
|- When publishing a wide, diagram-heavy implementation doc, set page orientation before image insertion: use whole-doc landscape for globally wide docs, or isolate only the wide block with section breaks and apply section orientation for selected-content behavior.
- Orientation helpers now support both paths: `docs_advanced.set_page_orientation(doc_id, landscape=...)` for whole-doc changes and `docs_advanced.set_section_orientation(doc_id, start_index, end_index, landscape=...)` for selected ranges.
|- Before inserting into an existing doc, reset or recreate the target paragraph style; if the cursor is sitting in Heading 1, pasted Markdown or images can inherit the wrong styling and make the whole section look broken.
|- Use high-DPI PNGs for Google Docs if text clarity matters; keep the SVG as the source-of-truth asset when you want easy regeneration and comparison.
|- For render-comparison docs, add a short text note between the heading and the image so spacing and wrap behavior are obvious at a glance.
|- Mermaid is the canonical source for diagram content; PNG/SVG are derivative renders. When auditing a figure family, map each asset back to the exact Mermaid block and nearest heading in the source docs before judging quality.
|- Check the actual source docs first, not just generated images. QA should compare the prose, Mermaid source, and rendered asset family together.
|- After publish, verify by exporting the doc and checking that Mermaid fences are gone, headings and tables survived, and the inline image count matches the number of rendered diagrams.
- If the user names a specific worktree or revision as canonical, publish from that checkout. Do not silently switch to a different tree or to generated copies when the source documents are the point of the task.
- If a user provides a canonical combined Google Doc with tab/heading URLs, rewrite the source Markdown links to those exact live URLs before republishing so cross-doc navigation lands on the final destination instead of stale per-doc IDs.
- If the user wants one final compiled doc family, update the source Markdown first, then republish from that source so every exported doc inherits the final URLs instead of leaving `.md` links behind.
- After rewriting, verify the source tree has no remaining intra-family `.md` links before uploading; a quick regex scan is enough.
- When the docs have already been published and only links need correction, update the live docs in place with Docs API text-style link rewrites instead of republishing everything from scratch.
- For surgical edits to an existing live Google Doc, prefer targeted in-place replacement over republishing the full document. Read the live structure, identify a unique placeholder or anchor text, use `replaceAllText` for the visible-text swap, then verify both the replacement count and the surrounding section text.
- Before publishing a diagram family, render each Mermaid fence from the source Markdown individually. Fix parse/layout issues in the source block first; don't try to compensate in Google Docs.
- When picking image size, use page-space-aware sizing rather than a fixed width. Wide flow diagrams can often take full width, while tall ERDs and roadmaps may need a narrower placement or a deliberate page break.
- If the current page has little remaining space, it can be better to let the next figure start on the next page than to force a cramped insert.
- Sequence diagrams tend to blur sooner than wide block diagrams in Google Docs, so give them extra care when choosing scale and placement.
- For HTML-derived diagram PNGs, inspect the rendered canvas bounds and crop away excess page/background padding before embedding; aim for a small, consistent edge margin instead of accepting whatever the export produced.
- If multiple related diagrams need the same link destinations, update the links in the source Markdown folder first so the next publish/import pass inherits the corrected navigation everywhere.
- For doc-embedded figures, reduce wrapper padding in the HTML source first, then crop the PNG export if needed; changing the source frame plus trimming the rendered canvas is usually faster than trying to fight extra whitespace inside Google Docs.
- When the source Markdown contains both Mermaid and existing image references, resolve relative image paths against the source file's directory, not the nested assets directory, or you'll accidentally duplicate `assets/` in the path.
- After Markdown import, match image insertion anchors against the imported plain heading text, not the raw `###` line; normalize whitespace and strip backticks before searching.
- If a Google Doc import is visibly malformed or partially plain-text, create a fresh doc from the source Markdown rather than trying to salvage the broken import in place.
- If the user requires zero `.md` links in the published package, do not leave companion docs as local-relative placeholders; publish them as first-class Google Docs too, collect their URLs, and then rewrite every intra-package reference to those live URLs.
- For a zero-`.md` pass, include local navigation docs such as `README.md`, `SUMMARY.md`, `low-code-sdk.md`, and `gitbook-guide.md` in the publish/link-map step so they become real doc targets instead of dangling markdown stubs.
- After the rewrite pass, verify with a regex search that no `.md` links remain anywhere in the source package before considering the family complete.

|- For QA, a sample doc with one PNG image and one linked SVG source is a good way to compare render fidelity before republishing the full doc family.
|- If a Google Doc import becomes visually corrupted, clear or recreate the doc instead of trying to salvage malformed heading structure in place.
|- For architecture-style docs that are sensitive to layout/style, it is acceptable to delete/trash the broken doc and recreate it from the source Markdown, then rewire links to the new ID.
|- When the user wants docs aligned across architecture/design/implementation, keep the split explicit: architecture = role/description, design = chosen tech stack and detailed contracts, implementation = code-level layout and rollout.
|- If a component name feels like a helper but is really just behavior inside another boundary (for example tenant resolution or sandboxing), keep it out of the architecture component list and describe it as an internal behavior or mode instead.
|- For Google Docs publishing of longer product docs, prefer the user's chosen document font when available and apply it consistently after import so recreated docs do not visually drift from sibling docs.
|- For PR-pushed Mermaid assets, prefer straighter layouts or crisp sequence diagrams; avoid curvy/looped routing when a clearer render is available.
|- Markdown import can succeed even when post-import styling hits Docs write quotas; if the raw import is fine, prefer publishing the Markdown first and doing link rewrites / image insertion in a second pass instead of running a heavy paragraph-style pass immediately.
|- When publishing multiple related docs, create every target doc first, collect all Google Doc URLs, then rewrite internal links and republish. This avoids temporary `.md` links and broken cross-doc navigation.
|- If a link like `README.md` is meant as a local-relative reference, rewrite it to the correct published Google Doc URL before exporting or republishing so the imported doc doesn't show a misleading literal Markdown link.
|- A lighter import path is often more reliable than a full style-rewrite pipeline for first-pass publication; only add per-paragraph styling or inline cleanup after confirming the doc is live.

## Practical check
- After publishing, inspect the rendered doc and make sure the links point where the user expects.
- If a recreated doc uses a new ID, make sure every sibling doc and any summary links are updated to the new canonical URL.
- For doc families with a shared diagram, verify that the diagram nodes/arrows, the terminology table, and the prose all describe the same component set before you stop.
- If the source is a specific worktree or revision, publish from that checkout rather than a sibling copy so the published doc matches the user's canonical source exactly.
- If the existing Google Doc is visibly malformed or flattened, create a fresh doc ID instead of trying to salvage the broken import in place.
- For diagram-heavy docs, import stripped Markdown first, then insert rendered Mermaid or image assets inline after stable heading anchors. Validate by re-exporting and checking that no Mermaid fences remain and the inline image count matches the source diagrams.
- When matching insertion anchors, normalize headings by stripping `#`, numeric list prefixes, bullet markers, backticks, and extra whitespace before searching the imported doc.
