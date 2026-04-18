#!/usr/bin/env python3
"""Apply inline Markdown styles (bold, italic, code, links) after text insertion."""
import re
from docs_api import build_service, _populate_document


def _apply_inline_styles(doc_id):
    """Parse each paragraph for Markdown markers and apply inline styles.
    
    Handles:
      **text**  →  bold
      *text*    →  italic
      `text`    →  inline code (Courier New + gray background)
      [text](url)  →  hyperlink
    
    Strategy (single batchUpdate per paragraph):
      1. Scan each paragraph for Markdown runs.
      2. Build updateTextStyle requests for bold/italic/links.
      3. Build delete requests for the marker characters (in reverse so
         earlier positions don't shift), then re-read the doc to get
         accurate paragraph boundaries before the next paragraph.
    """
    docs = build_service("docs", "v1")
    doc = docs.documents().get(documentId=doc_id).execute()
    content = doc.get("body", {}).get("content", [])
    
    # Collect all paragraphs that have Markdown markers
    paragraphs_to_process = []
    
    for el in content:
        if "paragraph" not in el:
            continue
        para = el["paragraph"]
        # Skip already-bulleted paragraphs (might confuse things)
        if para.get("bullet"):
            continue
        text = "".join(e.get("textRun", {}).get("content", "") for e in para.get("elements", []))
        
        # Skip paragraphs with no Markdown markers
        has_bold = '**' in text
        has_italic = '*' in text and not has_bold  # careful: ** contains *
        has_backtick = '`' in text
        has_link = '](' in text
        has_underline_link = '](' in text or 'http' in text  # for raw URLs
        
        # Better detection
        has_md = has_bold or has_link or has_backtick
        # Also check for *text* (single asterisk, but not **)
        if not has_md:
            # Check for single * that's not part of **
            temp = text.replace('**', '')
            has_italic = '*' in temp
            has_md = has_italic
        
        if has_md:
            paragraphs_to_process.append((el, text))
    
    if not paragraphs_to_process:
        return
    
    # Process each paragraph individually (re-read after each to get accurate positions)
    processed_count = 0
    
    for max_passes in [30]:
        found = False
        # Re-read document structure
        doc = docs.documents().get(documentId=doc_id).execute()
        
        for el in doc.get("body", {}).get("content", []):
            if "paragraph" not in el:
                continue
            para = el["paragraph"]
            if para.get("bullet"):
                continue
            
            text = "".join(e.get("textRun", {}).get("content", "") for e in para.get("elements", []))
            start = el["startIndex"]
            
            requests = []
            
            # Find bold: **text**
            for m in re.finditer(r'\*\*(.+?)\*\*', text):
                full_start = start + m.start()
                content_start = full_start + 2
                content_end = start + m.end() - 2
                reqs = [{
                    "deleteContentRange": {
                        "range": {"startIndex": full_start, "endIndex": content_start}
                    }
                }, {
                    "updateTextStyle": {
                        "range": {"startIndex": content_start, "endIndex": content_end},
                        "textStyle": {"bold": True},
                        "fields": "bold",
                    }
                }, {
                    "deleteContentRange": {
                        "range": {"startIndex": content_end, "endIndex": start + m.end()}
                    }
                }]
                requests.extend(reqs)
            
            # Find links: [text](url)
            for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', text):
                link_text_start = start + m.start() + 1  # skip [
                link_text_end = link_text_start + len(m.group(1))
                link_open_start = link_text_end
                link_open_end = link_text_end + len('](' + m.group(2) + ')')
                link_url = m.group(2)
                
                reqs = [
                    {
                        "deleteContentRange": {
                            "range": {"startIndex": link_text_start - 1, "endIndex": link_text_start}
                        }
                    },
                    {
                        "updateTextStyle": {
                            "range": {"startIndex": link_text_start, "endIndex": link_text_end},
                            "textStyle": {
                                "link": {"url": link_url},
                                "underline": True,
                            },
                            "fields": "link,underline",
                        }
                    },
                    {
                        "deleteContentRange": {
                            "range": {"startIndex": link_text_end, "endIndex": link_open_end}
                        }
                    },
                ]
                requests.extend(reqs)
            
            # Find inline code: `text` (skip inside ** or links)
            for m in re.finditer(r'`([^`]+)`', text):
                code_full_start = start + m.start()
                code_start = code_full_start + 1
                code_end = start + m.end() - 1
                code_content = m.group(1)
                
                reqs = [
                    {
                        "deleteContentRange": {
                            "range": {"startIndex": code_full_start, "endIndex": code_full_start + 1}
                        }
                    },
                    {
                        "updateTextStyle": {
                            "range": {"startIndex": code_full_start, "endIndex": code_full_start + len(code_content)},
                            "textStyle": {
                                "weightedFontFamily": {"fontFamily": "Courier New"},
                                "backgroundColor": {"color": {"rgbColor": {"red": 0.94, "green": 0.95, "blue": 0.96}}},
                            },
                            "fields": "weightedFontFamily,backgroundColor",
                        }
                    },
                    {
                        "deleteContentRange": {
                            "range": {"startIndex": code_full_start + len(code_content), "endIndex": start + m.end()}
                        }
                    },
                ]
                requests.extend(reqs)
            
            if requests:
                found = True
                processed_count += 1
                
                # Execute all requests for this paragraph in one batch
                # Delete requests are added after style requests — we need to be careful
                # about index shifting. Instead, let's delete from right to left first,
                # then apply styles on the corrected ranges.
                
                # Collect all delete ranges
                delete_ranges = [(r["deleteContentRange"]["range"]["startIndex"], 
                                  r["deleteContentRange"]["range"]["endIndex"])
                                 for r in requests if "deleteContentRange" in r]
                
                # Sort deletes in reverse order
                delete_ranges.sort(reverse=True)
                
                # Build final request list: deletes first (reverse order), then styles
                final_requests = []
                
                # Compute offset table: for each delete range, calculate cumulative shift
                # that affects positions AFTER this range
                offset_map = {}
                cumulative_shift = 0
                for ds, de in reversed(delete_ranges):  # process left to right
                    offset_map[ds] = cumulative_shift
                    cumulative_shift -= (de - ds)
                
                # Apply deletes from right to left (so earlier positions don't shift)
                for ds, de in delete_ranges:
                    final_requests.append({
                        "deleteContentRange": {
                            "range": {"startIndex": ds, "endIndex": de}
                        }
                    })
                
                # Apply style requests with offset corrections
                for r in requests:
                    if not r.get("deleteContentRange"):
                        if "updateTextStyle" in r:
                            range_info = r["updateTextStyle"]["range"]
                            old_start = range_info["startIndex"]
                            old_end = range_info["endIndex"]
                            # Find the delete range that was immediately before this one
                            # and calculate its shift
                            shift = 0
                            for ds, de in delete_ranges:
                                if ds < old_start:
                                    shift -= (de - ds)
                            r["updateTextStyle"]["range"] = {
                                "startIndex": old_start + shift,
                                "endIndex": old_end + shift,
                            }
                            final_requests.append(r)
                
                docs.documents().batchUpdate(documentId=doc_id, body={"requests": final_requests}).execute()
                break  # re-read and continue
        
        if not found:
            break
    
    print(f"Applied inline styles to {processed_count} paragraphs")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 apply_inline_styles.py <doc_id>")
        sys.exit(1)
    
    doc_id = sys.argv[1]
    _apply_inline_styles(doc_id)
    
    # Show results
    docs = build_service("docs", "v1")
    doc = docs.documents().get(documentId=doc_id).execute()
    
    for el in doc.get("body", {}).get("content", []):
        if "paragraph" not in el:
            continue
        para = el["paragraph"]
        text = ""
        style_info = []
        for e in para.get("elements", []):
            tr = e.get("textRun", {})
            c = tr.get("content", "").rstrip("\n")
            ts = tr.get("textStyle", {})
            parts = []
            if ts.get("bold"): parts.append("B")
            if ts.get("italic"): parts.append("I")
            if ts.get("weightedFontFamily", {}).get("fontFamily") == "Courier New": parts.append("C")
            if ts.get("link", {}).get("url"): parts.append(f"L")
            if parts:
                style_info.append(f"[{''.join(parts)}]{c}")
            else:
                style_info.append(c)
        
        full_text = "".join(style_info)
        if full_text.strip():
            style = para.get("paragraphStyle", {}).get("namedStyleType", "")
            if style == "TITLE":
                hp = "# "
            elif style.startswith("HEADING_"):
                hp = "#" * (int(style.split("_")[1]) + 1) + " "
            else:
                hp = ""
            bp = "- " if para.get("bullet") else ""
            print(f"[{style or 'NORMAL'}] {hp}{bp}{full_text.strip()}")
