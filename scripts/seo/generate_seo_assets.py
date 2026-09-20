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


MISSION = (
    "SNSの公開投稿サンプルを収集・整理し、さまざまな意見、議論全体の流れ、現在の主要な論点を"
    "難しい社会問題に詳しくない人にも分かる言葉で届けます。"
)
DATA_LIMIT = "SNS公開投稿サンプルの整理であり、社会全体の世論調査ではありません。"
CITATION_TEMPLATE = (
    "SNS反応まっぷ「{テーマ名}」論点「{論点名}」"
    "（{更新年月}時点、SNS公開投稿サンプル{意見件数}件の整理。社会全体の世論調査ではありません）\n"
    "{ページURL}#issue-{論点ID}"
)


def llms_txt(base_url: str, theme_seo: dict[str, Any], catalog: dict[str, Any]) -> str:
    """AIアシスタント向けにサイトの要点と引用のしかたを渡す（llmstxt.org の慣例、課題77 案1）。

    テーマの1行説明は configs/theme-seo.json の description をそのまま使う
    （新しく文章を書くと AI臭検査・使い回し検査の対象が増える）。数字は
    data/public/catalog.json（build_public_registry.py の生成物）から取り、書き足さない。
    """
    theme_seo_by_id = {theme["id"]: theme for theme in theme_seo.get("themes") or []}
    lines = [
        "# SNS反応まっぷ",
        "",
        f"> {MISSION}",
        "",
        "## データの限界",
        "",
        DATA_LIMIT,
        "",
        "## 引用のしかた",
        "",
        "各ページの論点には固定リンクがあります。引用するときは次の形式を使ってください。",
        "",
        "```",
        CITATION_TEMPLATE,
        "```",
        "",
        "## テーマ一覧",
        "",
    ]
    for entry in catalog.get("themes") or []:
        theme_id = entry["theme_id"]
        seo = theme_seo_by_id.get(theme_id)
        if not seo:
            raise ValueError(f"llms.txt: configs/theme-seo.json に無いテーマID: {theme_id}")
        page_url = urljoin(base_url, entry["page_path"])
        json_url = urljoin(base_url, f"data/themes/{theme_id}.json")
        lines.append(
            f"- [{seo['headline']}]({page_url}): {seo['description']}"
            f"（JSON: {json_url} ／更新: {entry['updated_on']} ／意見{entry['opinion_count']:,}件）"
        )
    lines.extend(
        [
            "",
            "## 詳細",
            "",
            f"- [手法（データの集め方・分類方法）]({urljoin(base_url, 'about.html')})",
            f"- [訂正窓口]({urljoin(base_url, 'about.html#corrections')})",
            f"- [免責事項]({urljoin(base_url, 'disclaimer.html')})",
            "",
        ]
    )
    return "\n".join(lines)


def robots_txt(base_url: str) -> str:
    sitemap_url = urljoin(base_url, "sitemap.xml")
    return "\n".join(
        [
            # このファイルは独自ドメインのルートへ同期される。
            # docs/robots.txt を手で直すと次の生成で戻るため、ここを正典とする。
            "# SNS反応まっぷの公開用 robots.txt。",
            "# 正典: scripts/seo/generate_seo_assets.py",
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
    parser.add_argument("--catalog", default="data/public/catalog.json")
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

    catalog = read_json(args.catalog)
    (output_dir / "llms.txt").write_text(llms_txt(base_url, theme_seo, catalog), encoding="utf-8")

    print(f"Generated {output_dir / 'sitemap.xml'} ({len(pages)} pages)")
    print(f"Generated {output_dir / 'robots.txt'}")
    print(f"Generated {output_dir / 'llms.txt'} ({len(catalog.get('themes') or [])} themes)")

    if args.adsense_client:
        pub_id = validate_adsense_client(args.adsense_client)
        (output_dir / "ads.txt").write_text(ads_txt(pub_id), encoding="utf-8")
        print(f"Generated {output_dir / 'ads.txt'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
