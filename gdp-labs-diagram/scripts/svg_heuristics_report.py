#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


SVG_NS = "{http://www.w3.org/2000/svg}"


@dataclass
class RectShape:
    kind: str
    x: float
    y: float
    w: float
    h: float
    rx: float
    label: str


@dataclass
class TextItem:
    x: float
    y: float
    text: str
    cls: str
    font_size: float
    anchor: str


def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]


def extract_svg_text(html_text: str) -> str:
    match = re.search(r"(<svg\b.*?</svg>)", html_text, flags=re.DOTALL)
    if not match:
        raise SystemExit("No <svg> block found in HTML file")
    return match.group(1)


def parse_num(raw: str | None, default: float = 0.0) -> float:
    if raw is None:
        return default
    value = raw.strip().replace("px", "")
    if value.endswith("%"):
        return default
    return float(value)


def text_style_from_class(cls: str, font_size_attr: str | None, anchor_attr: str | None) -> tuple[float, str]:
    if font_size_attr:
        font_size = parse_num(font_size_attr, 16.0)
    elif "container-label" in cls:
        font_size = 22.0
    elif "edge-label" in cls:
        font_size = 14.0
    elif "node-title" in cls:
        font_size = 18.0
    else:
        font_size = 18.0

    if anchor_attr:
        anchor = anchor_attr
    elif "node-title" in cls:
        anchor = "middle"
    else:
        anchor = "start"
    return font_size, anchor


def estimate_text_box(text: TextItem) -> tuple[float, float, float, float]:
    width = max(1.0, len(text.text)) * text.font_size * 0.58
    height = text.font_size * 1.1
    if text.anchor == "middle":
        left = text.x - (width / 2.0)
        right = text.x + (width / 2.0)
    elif text.anchor == "end":
        left = text.x - width
        right = text.x
    else:
        left = text.x
        right = text.x + width
    top = text.y - height
    bottom = text.y
    return left, top, right, bottom


def rects_intersect(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1


def path_to_segments(d: str) -> list[tuple[float, float, float, float]]:
    tokens = re.findall(r"[A-Za-z]|-?\d+(?:\.\d+)?", d)
    i = 0
    cmd = None
    x = y = 0.0
    start_x = start_y = 0.0
    segments: list[tuple[float, float, float, float]] = []

    def read_num() -> float:
        nonlocal i
        value = float(tokens[i])
        i += 1
        return value

    while i < len(tokens):
        token = tokens[i]
        if re.fullmatch(r"[A-Za-z]", token):
            cmd = token
            i += 1
            if cmd in {"Z", "z"}:
                segments.append((x, y, start_x, start_y))
                x, y = start_x, start_y
            continue

        if cmd in {"M", "L"}:
            new_x = read_num()
            new_y = read_num()
            if cmd == "M":
                x, y = new_x, new_y
                start_x, start_y = x, y
                cmd = "L"
            else:
                segments.append((x, y, new_x, new_y))
                x, y = new_x, new_y
        elif cmd in {"m", "l"}:
            dx = read_num()
            dy = read_num()
            if cmd == "m":
                x += dx
                y += dy
                start_x, start_y = x, y
                cmd = "l"
            else:
                segments.append((x, y, x + dx, y + dy))
                x += dx
                y += dy
        elif cmd in {"H"}:
            new_x = read_num()
            segments.append((x, y, new_x, y))
            x = new_x
        elif cmd in {"h"}:
            dx = read_num()
            segments.append((x, y, x + dx, y))
            x += dx
        elif cmd in {"V"}:
            new_y = read_num()
            segments.append((x, y, x, new_y))
            y = new_y
        elif cmd in {"v"}:
            dy = read_num()
            segments.append((x, y, x, y + dy))
            y += dy
        else:
            break

    return segments


def segment_hits_rect(segment: tuple[float, float, float, float], rect: tuple[float, float, float, float]) -> bool:
    x1, y1, x2, y2 = segment
    rx1, ry1, rx2, ry2 = rect
    if x1 == x2:
        x = x1
        if rx1 <= x <= rx2:
            sy1, sy2 = sorted((y1, y2))
            return sy1 < ry2 and sy2 > ry1
        return False
    if y1 == y2:
        y = y1
        if ry1 <= y <= ry2:
            sx1, sx2 = sorted((x1, x2))
            return sx1 < rx2 and sx2 > rx1
        return False
    return rects_intersect((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)), rect)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SVG layout heuristics on a diagram HTML file.")
    parser.add_argument("html", nargs="+", help="One or more diagram HTML files")
    args = parser.parse_args()

    for raw_path in args.html:
        path = Path(raw_path).expanduser().resolve()
        if not path.exists():
            print(f"ERROR {path}: file not found")
            continue

        svg_xml = extract_svg_text(path.read_text(encoding="utf-8"))
        root = ET.fromstring(svg_xml)
        canvas_w = parse_num(root.get("width"), 0.0)
        canvas_h = parse_num(root.get("height"), 0.0)

        rects: list[RectShape] = []
        texts: list[TextItem] = []
        segments: list[tuple[float, float, float, float]] = []

        for elem in root.iter():
            tag = strip_ns(elem.tag)
            if tag == "rect":
                rects.append(
                    RectShape(
                        kind="rect",
                        x=parse_num(elem.get("x")),
                        y=parse_num(elem.get("y")),
                        w=parse_num(elem.get("width")),
                        h=parse_num(elem.get("height")),
                        rx=parse_num(elem.get("rx")),
                        label=elem.get("class", ""),
                    )
                )
            elif tag == "text":
                cls = elem.get("class", "")
                font_size, anchor = text_style_from_class(cls, elem.get("font-size"), elem.get("text-anchor"))
                texts.append(
                    TextItem(
                        x=parse_num(elem.get("x")),
                        y=parse_num(elem.get("y")),
                        text="".join(elem.itertext()).strip(),
                        cls=cls,
                        font_size=font_size,
                        anchor=anchor,
                    )
                )
            elif tag == "line":
                segments.append((
                    parse_num(elem.get("x1")),
                    parse_num(elem.get("y1")),
                    parse_num(elem.get("x2")),
                    parse_num(elem.get("y2")),
                ))
            elif tag == "path" and elem.get("d"):
                segments.extend(path_to_segments(elem.get("d", "")))

        rounded_rects = [r for r in rects if r.rx > 0]
        container_rects = [r for r in rects if r.rx == 0 and r.w > 0 and r.h > 0]

        print(f"FILE: {path}")
        print(f"  canvas: {canvas_w}x{canvas_h}")

        diagonal_count = 0
        for seg in segments:
            x1, y1, x2, y2 = seg
            if not math.isclose(x1, x2) and not math.isclose(y1, y2):
                diagonal_count += 1
        print(f"  diagonal segments: {diagonal_count}")

        overlaps: list[str] = []
        for i, a in enumerate(rounded_rects):
            a_box = (a.x, a.y, a.x + a.w, a.y + a.h)
            for b in rounded_rects[i + 1 :]:
                b_box = (b.x, b.y, b.x + b.w, b.y + b.h)
                if rects_intersect(a_box, b_box):
                    overlaps.append(f"rounded rect overlap: ({a.x},{a.y},{a.w},{a.h}) vs ({b.x},{b.y},{b.w},{b.h})")

        title_zone_hits: list[str] = []
        for container in container_rects:
            title_texts = [
                t for t in texts
                if container.x <= t.x <= container.x + container.w and container.y <= t.y <= container.y + 60
            ]
            if not title_texts:
                continue
            max_title_y = max(t.y for t in title_texts)
            title_zone = (container.x, container.y, container.x + container.w, max(container.y + 46, max_title_y + 10))

            for rect in rounded_rects:
                rect_box = (rect.x, rect.y, rect.x + rect.w, rect.y + rect.h)
                if rects_intersect(rect_box, title_zone):
                    title_zone_hits.append(f"node overlaps container title zone at ({container.x},{container.y},{container.w},{container.h})")
            for seg in segments:
                if segment_hits_rect(seg, title_zone):
                    title_zone_hits.append(f"connector crosses container title zone at ({container.x},{container.y},{container.w},{container.h})")

        text_overflow: list[str] = []
        for text in texts:
            if not text.text:
                continue
            tbox = estimate_text_box(text)
            containing = None
            for rect in rounded_rects:
                rx1, ry1, rx2, ry2 = rect.x, rect.y, rect.x + rect.w, rect.y + rect.h
                if rx1 <= text.x <= rx2 and ry1 <= text.y <= ry2:
                    containing = rect
                    break
            if containing:
                cbox = (containing.x + 8, containing.y + 8, containing.x + containing.w - 8, containing.y + containing.h - 8)
                if not (
                    cbox[0] <= tbox[0]
                    and tbox[2] <= cbox[2]
                    and cbox[1] <= tbox[1]
                    and tbox[3] <= cbox[3]
                ):
                    text_overflow.append(f"text may overflow rounded rect near ({containing.x},{containing.y},{containing.w},{containing.h}): {text.text}")

        print(f"  overlapping rounded rects: {len(overlaps)}")
        for item in overlaps:
            print(f"    - {item}")

        dedup_title_hits = list(dict.fromkeys(title_zone_hits))
        print(f"  title zone hits: {len(dedup_title_hits)}")
        for item in dedup_title_hits:
            print(f"    - {item}")

        print(f"  text overflow warnings: {len(text_overflow)}")
        for item in text_overflow:
            print(f"    - {item}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
