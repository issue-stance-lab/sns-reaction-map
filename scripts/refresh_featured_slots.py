#!/usr/bin/env python3
"""トップページの「今週の注目テーマ」「いま考えたい4つの問い」を自動で選び直す。

選定基準（GROWTH.yaml の featured_questions.criteria にも記録する）:
- 公開テーマのうち、意見300件以上のものだけを対象にする
- THEMES.yaml の updated_at が新しい順に5件選ぶ
- 1件目を「今週の注目テーマ」、2〜5件目を「いま考えたい4つの問い」にする

テーマの画像・カテゴリ・alt文言は docs/index.html の「話題のテーマ」一覧
（topic-grid、新テーマ公開時に人が1回だけ登録する箇所）を正典として読み直す。
問いの文言は各テーマ自身のページの <p class="question-line"> を正典として読み直す。
どちらも新しい文章を書き起こさず、既にある公開済みの文言を再利用する。
"""

from __future__ import annotations

import argparse
import html as html_lib
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .sync_portal_stats import (
        FEATURED_MIN_OPINIONS,
        INDEX_HTML,
        ROOT,
        THEMES_YAML,
        PortalStatsError,
        compute_stats,
        parse_themes_yaml,
        select_featured_themes,
    )
except ImportError:  # python3 scripts/refresh_featured_slots.py
    from sync_portal_stats import (  # type: ignore[no-redef]
        FEATURED_MIN_OPINIONS,
        INDEX_HTML,
        ROOT,
        THEMES_YAML,
        PortalStatsError,
        compute_stats,
        parse_themes_yaml,
        select_featured_themes,
    )

GROWTH_YAML = ROOT / "GROWTH.yaml"

TOPIC_CARD_RE = re.compile(
    r'<a class="topic-card"[^>]*href="(?P<href>[^"]+)">'
    r'<div class="topic-thumb"><img src="(?P<img>[^"]+)" alt="(?P<alt>[^"]*)"'
    r'.*?<span class="category">(?P<category>[^<]*)</span>',
    re.DOTALL,
)


def _topic_grid_metadata(html: str) -> dict[str, dict[str, str]]:
    """docs/index.html の「話題のテーマ」一覧から href→画像/カテゴリを読む。"""
    return {
        match.group("href"): {
            "img": match.group("img"),
            "alt": match.group("alt"),
            "category": match.group("category"),
        }
        for match in TOPIC_CARD_RE.finditer(html)
    }


def _question_line(root: Path, href: str) -> str:
    page_path = root / "docs" / href
    text = page_path.read_text(encoding="utf-8")
    match = re.search(r'<p class="question-line">([^<]*)</p>', text)
    if not match:
        raise PortalStatsError(f"{href}: question-line が見つかりません")
    return match.group(1)


def build_card_data(
    root: Path,
    themes: dict[str, dict[str, Any]],
    topic_grid: dict[str, dict[str, str]],
    theme_id: str,
) -> dict[str, str]:
    href = Path(themes[theme_id]["html"]).name
    grid_entry = topic_grid.get(href)
    if not grid_entry:
        raise PortalStatsError(f"{theme_id}: 話題のテーマ一覧に見つかりません（href={href}）")
    return {
        "theme_id": theme_id,
        "href": href,
        "title": themes[theme_id]["title"],
        "question_line": _question_line(root, href),
        "img": grid_entry["img"],
        "alt": grid_entry["alt"],
        "category": grid_entry["category"],
    }


def render_feature_card(data: dict[str, str], count: int) -> str:
    e = html_lib.escape
    return (
        f'<a class="feature-card" href="{e(data["href"])}">'
        f'<div class="feature-image"><img src="{e(data["img"])}" alt="{e(data["alt"])}" loading="eager">'
        f'<span class="live-pill">投票受付中</span></div>'
        f'<div class="feature-body"><span class="category">{e(data["category"])}</span>'
        f'<h3>{e(data["title"])}</h3><p>{e(data["question_line"])}</p>'
        f'<div class="stance-chips"><span class="stance-chip con">反対・慎重</span>'
        f'<span class="stance-chip hold">どちらでもない</span>'
        f'<span class="stance-chip pro">賛成・推進</span></div></div>'
        f'<div class="feature-data"><h4>このテーマの状況</h4>'
        f'<ul class="feature-points"><li>収集 '
        f'<strong id="feature-count-{data["theme_id"]}">{count:,}</strong>件</li></ul>'
        f'<div class="feature-button">詳細を見る ›</div></div></a>'
    )


def render_question_card(data: dict[str, str], count: int) -> str:
    e = html_lib.escape
    return (
        f'<a class="question-card" data-theme="{data["theme_id"]}" href="{e(data["href"])}">'
        f'<span class="question-theme">{e(data["title"])}</span>'
        f'<h3>{e(data["question_line"])}</h3>'
        f'<span class="question-count">収集 '
        f'<strong id="featured-count-{data["theme_id"]}">{count:,}</strong>件</span>'
        f'<span class="question-arrow">理由を読む →</span></a>'
    )


def update_index_html(index_html: str, feature_html: str, question_cards_html: str) -> str:
    index_html, n = re.subn(
        r'<a class="feature-card" href="[^"]*">.*?</a>',
        lambda _match: feature_html,
        index_html,
        count=1,
        flags=re.DOTALL,
    )
    if n != 1:
        raise PortalStatsError("docs/index.html: feature-card を置換できません")

    index_html, n = re.subn(
        r'(<div class="question-grid">)(.*?)(</div></section>)',
        lambda m: m.group(1) + question_cards_html + m.group(3),
        index_html,
        count=1,
        flags=re.DOTALL,
    )
    if n != 1:
        raise PortalStatsError("docs/index.html: question-grid を置換できません")
    return index_html


def update_growth_yaml(growth_text: str, hero: str, questions: list[dict[str, str]], today_iso: str) -> str:
    growth_text, n = re.subn(
        r"^featured:\s*[\w-]+(?:[ \t]*#.*)?$",
        f"featured: {hero}   # 現在のポータル注目テーマ（自動選定、scripts/refresh_featured_slots.py）",
        growth_text,
        count=1,
        flags=re.MULTILINE,
    )
    if n != 1:
        raise PortalStatsError("GROWTH.yaml: featured 行を置換できません")

    items_yaml = "\n".join(
        f"    - theme: {q['theme_id']}\n      question: {q['question_line']}" for q in questions
    )
    new_block = (
        "featured_questions:\n"
        f"  updated_at: {today_iso}\n"
        "  criteria: |\n"
        f"    - 公開テーマのうち意見{FEATURED_MIN_OPINIONS}件以上を対象にする\n"
        "    - THEMES.yaml の updated_at が新しい順に5件選び、1件目を「今週の注目テーマ」、\n"
        "      2〜5件目を「いま考えたい4つの問い」にする\n"
        "    - 選定は scripts/refresh_featured_slots.py が自動で行い、\n"
        "      実行のたびにこのファイルとページを同期する\n"
        "  items:\n"
        f"{items_yaml}\n\n"
    )
    growth_text, n = re.subn(
        r"^featured_questions:\n(?:.*\n)*?(?=^activity_log:)",
        lambda _match: new_block,
        growth_text,
        count=1,
        flags=re.MULTILINE,
    )
    if n != 1:
        raise PortalStatsError("GROWTH.yaml: featured_questions ブロックを置換できません")
    return growth_text


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="ファイルは書き換えず、選定結果だけ表示する")
    args = parser.parse_args(argv)

    try:
        themes = parse_themes_yaml(THEMES_YAML)
        stats = compute_stats(themes, ROOT)
        hero_id, *question_ids = select_featured_themes(themes, stats)

        index_html = INDEX_HTML.read_text(encoding="utf-8")
        topic_grid = _topic_grid_metadata(index_html)

        hero_data = build_card_data(ROOT, themes, topic_grid, hero_id)
        question_data = [build_card_data(ROOT, themes, topic_grid, tid) for tid in question_ids]

        feature_html = render_feature_card(hero_data, stats["sample_counts"][hero_id])
        question_cards_html = "".join(
            render_question_card(data, stats["sample_counts"][data["theme_id"]])
            for data in question_data
        )

        new_index_html = update_index_html(index_html, feature_html, question_cards_html)
        growth_text = GROWTH_YAML.read_text(encoding="utf-8")
        new_growth_text = update_growth_yaml(
            growth_text, hero_id, question_data, stats["today"].isoformat()
        )
    except (OSError, PortalStatsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("=== refresh_featured_slots ===")
    print(f"  今週の注目テーマ: {hero_id}（{themes[hero_id]['title']}、updated_at={themes[hero_id]['updated_at']}）")
    print("  いま考えたい4つの問い:")
    for data in question_data:
        print(f"    - {data['theme_id']}（{themes[data['theme_id']]['updated_at']}）: {data['question_line']}")

    if new_index_html == index_html and new_growth_text == growth_text:
        print("  → 変更なし（すでに同期済み）")
    elif args.dry_run:
        print("  → [dry-run] 変更あり（ファイルは書き換えません）")
    else:
        INDEX_HTML.write_text(new_index_html, encoding="utf-8")
        GROWTH_YAML.write_text(new_growth_text, encoding="utf-8")
        print(f"  → {INDEX_HTML} と {GROWTH_YAML} を更新しました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
