#!/usr/bin/env python3
"""Apply description, canonical, OGP, and Twitter Card tags to generated HTML files."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MARKER_START = "<!-- SEO_META_START -->"
MARKER_END = "<!-- SEO_META_END -->"


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


def esc_attr(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def page_meta(config: dict[str, Any]) -> dict[str, dict[str, str]]:
    site_title = str(config.get("site_title") or "SNS反応まっぷ")
    site_subtitle = str(config.get("site_subtitle") or "")
    pages: dict[str, dict[str, str]] = {
        "index.html": {
            "title": site_title,
            "description": site_subtitle,
            "type": "website",
        }
    }

    for case in config.get("cases") or []:
        title = str(case.get("title") or "").strip()
        subtitle = str(case.get("subtitle") or "").strip()
        topic_type = str(case.get("topic_type") or "").strip()
        description = subtitle or f"{title}をめぐるSNS反応を整理したページです。"
        prefix = f"{title} | " if title else ""

        mapping = {
            "reaction_map_url": f"{prefix}SNS反応まっぷ",
            "standard_map_url": f"{prefix}標準反応マップ",
            "summary_url": f"{prefix}反応まとめ",
        }
        for key, page_title in mapping.items():
            url = str(case.get(key) or "").strip()
            if url.endswith(".html"):
                pages[url] = {
                    "title": page_title,
                    "description": description,
                    "type": "article",
                    "section": topic_type,
                }

        for item in case.get("research_urls") or []:
            url = str(item.get("url") or "").strip()
            if url.endswith(".html") and not url.startswith("../"):
                pages[url] = {
                    "title": f"{str(item.get('label') or title)} | {site_title}",
                    "description": description,
                    "type": "article",
                    "section": topic_type,
                }

    return pages


def meta_block(
    base_url: str,
    page: str,
    meta: dict[str, str],
    site_name: str,
    og_image: str,
    include_image: bool,
) -> str:
    page_url = urljoin(base_url, page)
    lines = [
        MARKER_START,
        f'  <meta name="description" content="{esc_attr(meta.get("description"))}">',
        f'  <link rel="canonical" href="{esc_attr(page_url)}">',
        f'  <meta property="og:site_name" content="{esc_attr(site_name)}">',
        f'  <meta property="og:type" content="{esc_attr(meta.get("type") or "article")}">',
        f'  <meta property="og:title" content="{esc_attr(meta.get("title"))}">',
        f'  <meta property="og:description" content="{esc_attr(meta.get("description"))}">',
        f'  <meta property="og:url" content="{esc_attr(page_url)}">',
        '  <meta name="twitter:card" content="summary_large_image">',
        f'  <meta name="twitter:title" content="{esc_attr(meta.get("title"))}">',
        f'  <meta name="twitter:description" content="{esc_attr(meta.get("description"))}">',
    ]
    if include_image:
        image_url = urljoin(base_url, og_image.lstrip("/"))
        lines.insert(8, f'  <meta property="og:image" content="{esc_attr(image_url)}">')
        lines.append(f'  <meta name="twitter:image" content="{esc_attr(image_url)}">')
    if meta.get("section"):
        lines.append(f'  <meta property="article:section" content="{esc_attr(meta.get("section"))}">')
    lines.append(MARKER_END)
    return "\n".join(lines)


def replace_or_insert_seo(content: str, block: str) -> str:
    pattern = re.compile(
        rf"\n?\s*{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}",
        flags=re.DOTALL,
    )
    if pattern.search(content):
        return pattern.sub("\n" + block, content, count=1)

    viewport = re.search(r'  <meta name="viewport"[^>]*>\n', content)
    if viewport:
        return content[: viewport.end()] + block + "\n" + content[viewport.end() :]
    head = re.search(r"<head>\n", content)
    if head:
        return content[: head.end()] + block + "\n" + content[head.end() :]
    raise ValueError("HTML does not contain <head>")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply SEO meta tags to docs/*.html")
    parser.add_argument("--site-url", required=True, help="Published site URL, e.g. https://example.github.io/repo/")
    parser.add_argument("--config", default="configs/site-cases.json")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--og-image", default="ogp/default.png")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    base_url = normalize_base_url(args.site_url)
    config = read_json(args.config)
    docs_dir = resolve(args.docs_dir)
    site_name = str(config.get("site_title") or "SNS反応まっぷ")
    pages = page_meta(config)
    include_image = (docs_dir / args.og_image).exists()

    changed: list[str] = []
    missing: list[str] = []
    for page, meta in pages.items():
        path = docs_dir / page
        if not path.exists():
            missing.append(page)
            continue
        content = path.read_text(encoding="utf-8")
        updated = replace_or_insert_seo(content, meta_block(base_url, page, meta, site_name, args.og_image, include_image))
        if updated != content:
            changed.append(page)
            if not args.dry_run:
                path.write_text(updated, encoding="utf-8")

    action = "Would update" if args.dry_run else "Updated"
    print(f"{action}: {len(changed)} HTML files")
    for page in changed:
        print(f"- {page}")
    if not include_image:
        print(f"Skipped og:image because {docs_dir / args.og_image} does not exist")
    if missing:
        print(f"Missing: {len(missing)} configured files")
        for page in missing:
            print(f"- {page}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
