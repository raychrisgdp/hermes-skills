#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a diagram HTML file to a tightly cropped PNG using Playwright.")
    parser.add_argument("html", help="Absolute or relative path to the diagram HTML")
    parser.add_argument("--out", help="Optional output PNG path")
    parser.add_argument("--scale", type=float, default=2.0, help="Device scale factor for export (default: 2.0)")
    parser.add_argument("--selector", default=".container", help="Element selector to screenshot (default: .container)")
    args = parser.parse_args()

    html_path = Path(args.html).expanduser().resolve()
    if not html_path.exists():
        raise SystemExit(f"Input HTML not found: {html_path}")

    out_path = Path(args.out).expanduser().resolve() if args.out else html_path.with_suffix(".png")

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise SystemExit(
            "Playwright is required for HTML -> PNG rendering. "
            "Run `python3 -c \"from playwright.sync_api import sync_playwright\"` to verify setup."
        ) from exc

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1200}, device_scale_factor=args.scale)
        page.goto(html_path.as_uri())
        page.wait_for_timeout(1000)

        locator = page.locator(args.selector)
        if locator.count() == 0:
            raise SystemExit(f"Selector not found in HTML: {args.selector}")

        locator.first.screenshot(path=str(out_path))
        browser.close()

    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
