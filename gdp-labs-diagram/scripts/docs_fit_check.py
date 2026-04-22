#!/usr/bin/env python3
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path


def build_html(image_uri: str, width_px: int, padding_px: int) -> str:
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <style>
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; background: #FFFFFF; width: max-content; height: max-content; overflow: hidden; }}
    body {{ display: inline-block; font-family: Inter, Arial, sans-serif; }}
    .frame {{ width: max-content; padding: {padding_px}px; background: #FFFFFF; }}
    img {{ display: block; width: {width_px}px; height: auto; }}
  </style>
</head>
<body>
  <div class=\"frame\">
    <img src=\"{image_uri}\" alt=\"Fit check preview\" />
  </div>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a Docs/slides fit-check preview for a diagram PNG.")
    parser.add_argument("png", help="Absolute or relative path to the rendered PNG")
    parser.add_argument("--width", type=int, default=907, help="Target displayed width in CSS px (default: 907, about 680pt)")
    parser.add_argument("--padding", type=int, default=24, help="Outer white padding in CSS px")
    parser.add_argument("--out", help="Optional output path for fit-check PNG")
    args = parser.parse_args()

    png_path = Path(args.png).expanduser().resolve()
    if not png_path.exists():
        raise SystemExit(f"Input PNG not found: {png_path}")

    out_path = Path(args.out).expanduser().resolve() if args.out else png_path.with_name(f"{png_path.stem}.fitcheck.png")

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise SystemExit(
            "Playwright is required for docs fit-check rendering. "
            "Run `python3 -c \"from playwright.sync_api import sync_playwright\"` to verify setup."
        ) from exc

    html = build_html(png_path.as_uri(), args.width, args.padding)
    viewport_width = args.width + (args.padding * 2)

    with tempfile.TemporaryDirectory(prefix="diagram-fitcheck-") as tmpdir:
        html_path = Path(tmpdir) / "fitcheck.html"
        html_path.write_text(html, encoding="utf-8")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": viewport_width, "height": 1200}, device_scale_factor=1)
            page.goto(html_path.as_uri())
            page.wait_for_timeout(500)
            page.screenshot(path=str(out_path), full_page=True)
            browser.close()

    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
