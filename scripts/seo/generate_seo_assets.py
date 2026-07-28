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


def page_entries(
    config: dict[str, Any],
    theme_seo: dict[str, Any],
    output_dir: Path,
) -> list[tuple[str, str | None]]:
    entries: dict[str, str | None] = {}
    for page in config.get("site_pages") or []:
        value = str(page.get("url") or "").strip()
        if value.endswith(".html"):
            entries[value] = str(page.get("lastmod") or "").strip() or None

    case_urls: set[str] = set()
    for case in config.get("cases") or []:
        value = str(case.get("reaction_map_url") or "").strip()
        if value.endswith(".html"):
            case_urls.add(value)

    seo_dates = {
        str(theme["url"]): str(theme["dateModified"])
        for theme in theme_seo.get("themes") or []
    }
    if case_urls != set(seo_dates):
        raise ValueError(
            "reaction map mismatch between site-cases and theme-seo: "
            f"site_cases_only={sorted(case_urls - set(seo_dates))}, "
            f"theme_seo_only={sorted(set(seo_dates) - case_urls)}"
        )
    entries.update(seo_dates)

    missing = sorted(page for page in entries if not (output_dir / page).is_file())
    if missing:
        raise FileNotFoundError(f"sitemap pages missing from output directory: {missing}")
    return sorted(entries.items())


def sitemap_xml(
    base_url: str,
    pages: list[tuple[str, str | None]],
    fallback_lastmod: str | None = None,
) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for page, page_lastmod in pages:
        loc = urljoin(base_url, page)
        priority = "1.0" if page == "index.html" else "0.8"
        lines.extend(["  <url>", f"    <loc>{html.escape(loc)}</loc>"])
        lastmod = page_lastmod or fallback_lastmod
        if lastmod:
            date.fromisoformat(lastmod)
            lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.extend(
            [
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


def validate_adsense_client(client_id: str) -> str:
    cleaned = client_id.strip()
    if cleaned.startswith("ca-"):
        cleaned = cleaned[3:]
    if not cleaned.startswith("pub-") or not cleaned[4:].isdigit():
        raise ValueError("AdSense client ID must look like ca-pub-XXXXXXXXXXXXXXXX or pub-XXXXXXXXXXXXXXXX")
    return cleaned


def ads_txt(pub_id: str) -> str:
    return f"google.com, {pub_id}, DIRECT, f08c47fec0942fa0\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate SEO assets into docs/")
    parser.add_argument("--site-url", required=True, help="Published site URL, e.g. https://example.github.io/repo/")
    parser.add_argument("--config", default="configs/site-cases.json")
    parser.add_argument("--theme-seo-config", default="configs/theme-seo.json")
    parser.add_argument("--output-dir", default="docs")
    parser.add_argument(
        "--lastmod",
        help="Fallback lastmod for pages without a repository-backed date; omitted by default",
    )
    parser.add_argument("--adsense-client", help="Google AdSense client ID (e.g. ca-pub-XXXXXXXXXXXXXXXX) to generate ads.txt")
    args = parser.parse_args()

    base_url = normalize_base_url(args.site_url)
    config = read_json(args.config)
    theme_seo = read_json(args.theme_seo_config)
    output_dir = resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pages = page_entries(config, theme_seo, output_dir)

    (output_dir / "sitemap.xml").write_text(
        sitemap_xml(base_url, pages, args.lastmod),
        encoding="utf-8",
    )
    (output_dir / "robots.txt").write_text(robots_txt(base_url), encoding="utf-8")

    print(f"Generated {output_dir / 'sitemap.xml'} ({len(pages)} pages)")
    print(f"Generated {output_dir / 'robots.txt'}")

    if args.adsense_client:
        pub_id = validate_adsense_client(args.adsense_client)
        (output_dir / "ads.txt").write_text(ads_txt(pub_id), encoding="utf-8")
        print(f"Generated {output_dir / 'ads.txt'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
