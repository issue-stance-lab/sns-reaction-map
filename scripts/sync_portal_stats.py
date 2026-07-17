#!/usr/bin/env python3
"""
THEMES.yaml を読み込み、docs/index.html のポータル統計を自動更新する。

更新対象:
  - 分析済み投稿数 (classify2d 件数の合計)
  - 公開中のテーマ数 (published: done のテーマ数)
  - 投票受付中テーマ数 (page_v3: done のテーマ数)
  - 最終更新日・更新バーのテキスト

使い方:
  python scripts/sync_portal_stats.py
  python scripts/sync_portal_stats.py --dry-run   # 変更内容を表示するだけ
"""

import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
THEMES_YAML = ROOT / "THEMES.yaml"
INDEX_HTML  = ROOT / "docs" / "index.html"

DRY_RUN = "--dry-run" in sys.argv


def parse_themes_yaml(path: Path) -> dict:
    """
    PyYAML なしで THEMES.yaml を簡易パース。
    classify2d コメントから件数を抽出する。
    """
    text = path.read_text(encoding="utf-8")

    # テーマブロックを抽出（インデント2スペース + キー名）
    theme_pattern = re.compile(r"^  (\w[\w-]*):\s*$", re.MULTILINE)
    themes = {}
    positions = [(m.start(), m.group(1)) for m in theme_pattern.finditer(text)]

    for i, (pos, name) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        block = text[pos:end]

        published  = bool(re.search(r"published:\s*done", block))
        page_v3    = bool(re.search(r"page_v3:\s*done", block))

        # classify2d コメントから件数を抽出（例: # 708件 or # 255件（エラー率...））
        c2d_match = re.search(r"classify2d:\s*done\s*#\s*(\d+)件", block)
        count = int(c2d_match.group(1)) if c2d_match else 0

        themes[name] = {
            "published": published,
            "page_v3":   page_v3,
            "count":     count,
        }

    return themes


def compute_stats(themes: dict) -> dict:
    published = [t for t in themes.values() if t["published"]]
    total_posts   = sum(t["count"] for t in published)
    theme_count   = len(published)
    voting_count  = sum(1 for t in published if t["page_v3"])
    today         = date.today().strftime("%-m/%-d")   # 例: 7/16
    today_long    = date.today().strftime("%Y年%-m月%-d日")  # 例: 2026年7月16日
    return {
        "total_posts":  total_posts,
        "theme_count":  theme_count,
        "voting_count": voting_count,
        "today":        today,
        "today_long":   today_long,
    }


def update_html(html: str, s: dict) -> str:
    # 分析済み投稿数
    html = re.sub(
        r'(<strong id="hero-total-samples">)[^<]*(</strong>)',
        rf'\g<1>{s["total_posts"]:,}\2',
        html,
    )

    # 公開中のテーマ数（hero-stat の strong）
    html = re.sub(
        r'(<small>公開中のテーマ</small><strong>)\d+(</strong>)',
        rf'\g<1>{s["theme_count"]}\2',
        html,
    )

    # 投票受付中テーマ数
    html = re.sub(
        r'(<em>)\d+テーマで投票受付中(</em>)',
        rf'\g<1>{s["voting_count"]}テーマで投票受付中\2',
        html,
    )

    # ヒーロー統計の em（更新日表示）
    html = re.sub(
        r'(<em>)\d+/\d+更新 \+[\d,]+件追加(</em>)',
        rf'\g<1>{s["today"]}更新\2',
        html,
    )

    # update-bar の最終更新日
    html = re.sub(
        r'最終更新: <strong>[^<]+</strong>',
        f'最終更新: <strong>{s["today_long"]}</strong>',
        html,
    )

    return html


def main():
    themes = parse_themes_yaml(THEMES_YAML)
    s = compute_stats(themes)

    print(f"=== sync_portal_stats ===")
    print(f"  分析済み投稿: {s['total_posts']:,}件")
    print(f"  公開テーマ:   {s['theme_count']}テーマ")
    print(f"  投票受付中:   {s['voting_count']}テーマ")
    print(f"  更新日:       {s['today_long']}")

    html_orig = INDEX_HTML.read_text(encoding="utf-8")
    html_new  = update_html(html_orig, s)

    if html_orig == html_new:
        print("  → 変更なし（すでに最新）")
        return

    if DRY_RUN:
        print("  → [dry-run] 変更あり（ファイルは書き換えません）")
        return

    INDEX_HTML.write_text(html_new, encoding="utf-8")
    print(f"  → {INDEX_HTML} を更新しました")


if __name__ == "__main__":
    main()
