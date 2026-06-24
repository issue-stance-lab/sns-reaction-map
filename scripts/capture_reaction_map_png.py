#!/usr/bin/env python3
"""Capture reaction map HTML into Substack-friendly PNG files."""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture reaction map HTML panels as PNG")
    parser.add_argument("--html", required=True)
    parser.add_argument("--output-dir", default="docs")
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--width", type=int, default=1400)
    parser.add_argument("--height", type=int, default=1200)
    parser.add_argument("--scale", type=int, default=2)
    args = parser.parse_args()

    html_path = resolve(args.html)
    output_dir = resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": args.width, "height": args.height},
            device_scale_factor=args.scale,
        )
        page.goto(html_path.as_uri(), wait_until="networkidle")
        full = output_dir / f"{args.prefix}-full.png"
        page.screenshot(path=str(full), full_page=True)

        panels = page.locator("section.panel")
        panel_names = [
            "category-counts",
            "by-query",
            "by-stance",
            "samples",
        ]
        count = panels.count()
        for i in range(min(count, len(panel_names))):
            out = output_dir / f"{args.prefix}-{panel_names[i]}.png"
            panels.nth(i).screenshot(path=str(out))
            print(out)
        print(full)
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
