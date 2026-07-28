#!/usr/bin/env python3
"""Validate published theme SEO, Article JSON-LD, links, and protected integrations."""

from __future__ import annotations

import argparse
import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_PAGE_TOKENS = (
    "G-K10S4YCZFH",
    "ca-pub-2542211932832864",
    "topic-modern.css?v=23",
    "topic-modern.js",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def content(source: str, pattern: str) -> str | None:
    match = re.search(pattern, source, re.DOTALL | re.IGNORECASE)
    return html.unescape(match.group(1).strip()) if match else None


def local_references(source: str) -> set[str]:
    references = set(
        re.findall(r'(?:href|src)=["\']([^"\'#?]+)(?:[?#][^"\']*)?["\']', source, re.IGNORECASE)
    )
    return {
        ref
        for ref in references
        if ref
        and not re.match(r"^(?:https?:)?//|^(?:mailto:|tel:|data:|javascript:)", ref)
    }


def validate_article(
    theme: dict[str, Any],
    config: dict[str, Any],
    source: str,
    path: Path,
) -> list[str]:
    errors: list[str] = []
    expected_title = f'{theme["headline"]}｜SNS反応まっぷ'
    checks = {
        "title": (content(source, r"<title>(.*?)</title>"), expected_title),
        "description": (
            content(source, r'<meta\s+name="description"\s+content="(.*?)">'),
            theme["description"],
        ),
        "og:title": (
            content(source, r'<meta\s+property="og:title"\s+content="(.*?)">'),
            theme["headline"],
        ),
        "og:description": (
            content(source, r'<meta\s+property="og:description"\s+content="(.*?)">'),
            theme["description"],
        ),
        "twitter:title": (
            content(source, r'<meta\s+name="twitter:title"\s+content="(.*?)">'),
            theme["headline"],
        ),
        "twitter:description": (
            content(source, r'<meta\s+name="twitter:description"\s+content="(.*?)">'),
            theme["description"],
        ),
        "H1": (
            content(source, r"<h1[^>]*>(.*?)</h1>"),
            theme["headline"],
        ),
    }
    for label, (actual, expected) in checks.items():
        if actual != expected:
            errors.append(f"{path.name}: {label} mismatch: {actual!r} != {expected!r}")

    canonical = urljoin(config["site_url"], theme["url"])
    image_url = urljoin(config["site_url"], theme["image"])
    for label, pattern, expected in (
        ("canonical", r'<link\s+rel="canonical"\s+href="(.*?)">', canonical),
        ("og:url", r'<meta\s+property="og:url"\s+content="(.*?)">', canonical),
        ("og:image", r'<meta\s+property="og:image"\s+content="(.*?)">', image_url),
        ("twitter:image", r'<meta\s+name="twitter:image"\s+content="(.*?)">', image_url),
    ):
        if content(source, pattern) != expected:
            errors.append(f"{path.name}: {label} mismatch")

    payloads: list[dict[str, Any]] = []
    for raw in re.findall(
        r'<script\s+type="application/ld\+json">\s*(.*?)\s*</script>',
        source,
        re.DOTALL | re.IGNORECASE,
    ):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}: invalid JSON-LD: {exc}")
            continue
        if isinstance(parsed, dict):
            payloads.append(parsed)
    articles = [item for item in payloads if item.get("@type") in {"Article", "NewsArticle"}]
    if len(articles) != 1:
        errors.append(f"{path.name}: expected one Article JSON-LD, found {len(articles)}")
    else:
        article = articles[0]
        expected_fields = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": theme["headline"],
            "description": theme["description"],
            "image": [image_url],
            "datePublished": theme["datePublished"],
            "dateModified": theme["dateModified"],
        }
        for key, expected in expected_fields.items():
            if article.get(key) != expected:
                errors.append(f"{path.name}: JSON-LD {key} mismatch")
        if article.get("mainEntityOfPage", {}).get("@id") != canonical:
            errors.append(f"{path.name}: JSON-LD mainEntityOfPage mismatch")
        for role in ("author", "publisher"):
            entity = article.get(role) or {}
            if (
                entity.get("@type") != "Organization"
                or entity.get("name") != config["organization"]["name"]
                or entity.get("url") != urljoin(config["site_url"], config["organization"]["url"])
            ):
                errors.append(f"{path.name}: JSON-LD {role} mismatch")

    for value in (theme["datePublished"], theme["dateModified"]):
        if f'<time datetime="{value}">' not in source:
            errors.append(f"{path.name}: visible date missing for {value}")
    for required in (
        config["organization"]["name"],
        "世論調査ではなく",
        "AIを使用した工程",
        'href="about.html#corrections"',
    ):
        if required not in source:
            errors.append(f"{path.name}: visible trust detail missing: {required}")
    if source.count("<strong>データの集め方:</strong>"):
        errors.append(f"{path.name}: duplicate legacy collection-method block remains")

    for token in REQUIRED_PAGE_TOKENS:
        if token not in source:
            errors.append(f"{path.name}: protected token missing: {token}")
    if not re.search(r'id="vote-section"|id="vote-buttons"', source):
        errors.append(f"{path.name}: vote UI missing")
    if not re.search(r"twitter\.com/intent/tweet|x\.com/intent/post|share-x-btn|id=\"share-x\"", source):
        errors.append(f"{path.name}: X share UI missing")

    for ref in local_references(source):
        target = (path.parent / ref).resolve()
        if not target.exists():
            errors.append(f"{path.name}: broken local reference: {ref}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/theme-seo.json")
    parser.add_argument("--site-cases", default="configs/site-cases.json")
    parser.add_argument("--themes-registry", default="THEMES.yaml")
    parser.add_argument("--docs-dir", default="docs")
    args = parser.parse_args()

    config = load_json(PROJECT_ROOT / args.config)
    site_cases = load_json(PROJECT_ROOT / args.site_cases)
    themes_registry = yaml.safe_load(
        (PROJECT_ROOT / args.themes_registry).read_text(encoding="utf-8")
    ).get("themes") or {}
    docs_dir = PROJECT_ROOT / args.docs_dir
    themes = config.get("themes") or []
    errors: list[str] = []
    supabase_pages = 0

    theme_urls = {theme["url"] for theme in themes}
    case_urls = {
        case["reaction_map_url"]
        for case in site_cases.get("cases") or []
        if case.get("reaction_map_url")
    }
    if theme_urls != case_urls:
        errors.append("theme URL sets differ between theme-seo and site-cases")

    index_source = (docs_dir / "index.html").read_text(encoding="utf-8")
    for theme in themes:
        path = docs_dir / theme["url"]
        if not path.is_file():
            errors.append(f"missing theme page: {theme['url']}")
            continue
        source = path.read_text(encoding="utf-8")
        errors.extend(validate_article(theme, config, source, path))
        registry_theme = themes_registry.get(theme["id"]) or {}
        for config_key, registry_key in (
            ("datePublished", "published_at"),
            ("dateModified", "updated_at"),
        ):
            registry_value = registry_theme.get(registry_key)
            registry_date = registry_value.isoformat() if hasattr(registry_value, "isoformat") else str(registry_value)
            if registry_date != theme[config_key]:
                errors.append(
                    f"{path.name}: {config_key} does not match THEMES.yaml {registry_key}"
                )
        if not (docs_dir / theme["image"]).is_file():
            errors.append(f"{path.name}: configured Article image is missing: {theme['image']}")
        if re.search("supabase", source, re.IGNORECASE):
            supabase_pages += 1
        if f'href="{theme["url"]}"' not in index_source:
            errors.append(f"index.html: missing crawlable link to {theme['url']}")
        related = {
            ref
            for ref in re.findall(r'href=["\']([^"\']+reaction-map[^"\']*\.html)["\']', source)
            if Path(urlparse(ref).path).name != theme["url"]
        }
        if not related:
            errors.append(f"{path.name}: no crawlable related-theme link")

    tree = ET.parse(docs_dir / "sitemap.xml")
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_dates: dict[str, str | None] = {}
    for url_node in tree.findall("sm:url", namespace):
        loc_node = url_node.find("sm:loc", namespace)
        lastmod_node = url_node.find("sm:lastmod", namespace)
        page = Path(urlparse(loc_node.text or "").path).name if loc_node is not None else ""
        sitemap_dates[page] = lastmod_node.text if lastmod_node is not None else None
    sitemap_paths = set(sitemap_dates)
    fixed_pages = {
        page["url"]: page.get("lastmod")
        for page in site_cases.get("site_pages") or []
    }
    fixed_urls = set(fixed_pages)
    expected_sitemap = theme_urls | fixed_urls
    if sitemap_paths != expected_sitemap:
        errors.append(
            "sitemap URL mismatch: "
            f"missing={sorted(expected_sitemap - sitemap_paths)}, "
            f"extra={sorted(sitemap_paths - expected_sitemap)}"
        )
    expected_dates = fixed_pages | {
        theme["url"]: theme["dateModified"]
        for theme in themes
    }
    for page, expected_date in expected_dates.items():
        if sitemap_dates.get(page) != expected_date:
            errors.append(
                f"sitemap lastmod mismatch for {page}: "
                f"{sitemap_dates.get(page)!r} != {expected_date!r}"
            )

    if errors:
        print(f"FAILED: {len(errors)} validation error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"OK: themes={len(themes)}, Article JSON-LD={len(themes)}, "
        f"sitemap URLs={len(sitemap_paths)}, Supabase-related pages retained={supabase_pages}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
