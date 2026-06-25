#!/usr/bin/env python3
"""Generate robots.txt and sitemap.xml for the static SNS reaction map site."""

from __future__ import annotations

import argparse
import html
import json
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urljoin


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def read_json(path: str) -> Any:
    return json.loads(resolve(path).read_text(encoding="utf-8"))


def normalize_base_url(site_url: str) -> str:
    cleaned = site_url.strip()
    if not cleaned.startswith(("https://", "http://")):
        raise ValueError("--site-url must start with https:// or http://")
    return cleaned.rstrip("/") + "/"


def page_urls(config: dict[str, Any]) -> list[str]:
    pages = ["index.html"]
    for case in config.get("cases") or []:
        for key in ("reaction_map_url", "standard_map_url", "summary_url"):
            value = str(case.get(key) or "").strip()
            if value and value.endswith(".html"):
                pages.append(value)
        for group_key in ("article_urls", "research_urls"):
            for item in case.get(group_key) or []:
                value = str(item.get("url") or "").strip()
                if value.endswith(".html") and not value.startswith("../"):
                    pages.append(value)
    return sorted(dict.fromkeys(pages))


def sitemap_xml(base_url: str, pages: list[str], lastmod: str) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for page in pages:
        loc = urljoin(base_url, page)
        priority = "1.0" if page == "index.html" else "0.8"
        lines.extend(
            [
                "  <url>",
                f"    <loc>{html.escape(loc)}</loc>",
                f"    <lastmod>{lastmod}</lastmod>",
                "    <changefreq>weekly</changefreq>",
                f"    <priority>{priority}</priority>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def robots_txt(base_url: str) -> str:
    sitemap_url = urljoin(base_url, "sitemap.xml")
    return "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "",
            f"Sitemap: {sitemap_url}",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate SEO assets into docs/")
    parser.add_argument("--site-url", required=True, help="Published site URL, e.g. https://example.github.io/repo/")
    parser.add_argument("--config", default="configs/site-cases.json")
    parser.add_argument("--output-dir", default="docs")
    parser.add_argument("--lastmod", default=date.today().isoformat())
    args = parser.parse_args()

    base_url = normalize_base_url(args.site_url)
    config = read_json(args.config)
    pages = page_urls(config)
    output_dir = resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "sitemap.xml").write_text(sitemap_xml(base_url, pages, args.lastmod), encoding="utf-8")
    (output_dir / "robots.txt").write_text(robots_txt(base_url), encoding="utf-8")

    print(f"Generated {output_dir / 'sitemap.xml'} ({len(pages)} pages)")
    print(f"Generated {output_dir / 'robots.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
