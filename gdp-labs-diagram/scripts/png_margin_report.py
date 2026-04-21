#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Report effective content margins for a diagram PNG.")
    parser.add_argument("png", nargs="+", help="One or more PNG paths")
    parser.add_argument("--white-threshold", type=int, default=248, help="RGB threshold for treating pixels as white background")
    parser.add_argument("--warn-margin-pct", type=float, default=10.0, help="Warn when any margin exceeds this percent of width/height")
    args = parser.parse_args()

    try:
        from PIL import Image
    except Exception as exc:
        raise SystemExit("Pillow is required. Run `python3 -c \"from PIL import Image\"` to verify setup.") from exc

    for raw_path in args.png:
        path = Path(raw_path).expanduser().resolve()
        if not path.exists():
            print(f"ERROR {path}: file not found")
            continue

        image = Image.open(path).convert("RGBA")
        width, height = image.size
        pixels = image.load()

        min_x, min_y = width, height
        max_x, max_y = -1, -1

        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a == 0:
                    continue
                if r >= args.white_threshold and g >= args.white_threshold and b >= args.white_threshold:
                    continue
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

        print(f"FILE: {path}")
        print(f"  size: {width}x{height}")
        if max_x < 0:
            print("  content: none detected")
            continue

        top = min_y
        left = min_x
        right = width - 1 - max_x
        bottom = height - 1 - max_y

        top_pct = (top / height) * 100
        bottom_pct = (bottom / height) * 100
        left_pct = (left / width) * 100
        right_pct = (right / width) * 100

        print(f"  content bbox: x={min_x}..{max_x}, y={min_y}..{max_y}")
        print(f"  margins px: top={top}, bottom={bottom}, left={left}, right={right}")
        print(
            "  margins %: "
            f"top={top_pct:.1f}, bottom={bottom_pct:.1f}, left={left_pct:.1f}, right={right_pct:.1f}"
        )

        warnings: list[str] = []
        if top_pct > args.warn_margin_pct:
            warnings.append("top margin")
        if bottom_pct > args.warn_margin_pct:
            warnings.append("bottom margin")
        if left_pct > args.warn_margin_pct:
            warnings.append("left margin")
        if right_pct > args.warn_margin_pct:
            warnings.append("right margin")
        if warnings:
            print("  warning:", ", ".join(warnings), f"exceeds {args.warn_margin_pct:.1f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
