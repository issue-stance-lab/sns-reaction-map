#!/usr/bin/env python3
"""論点カードに、分類結果から計算した件数を併記する。

`configs/{theme}-reaction-map.json` の `issue_counts` を読み、各カードの
`<p class="explainer-card-title">` の末尾に

    <span class="explainer-count" id="issue-count-{theme}-{slug}">N件</span>

を差し込む（既にあれば数字を更新する）。何度実行しても結果は同じ。

    python3 scripts/sync_issue_counts.py            # 全テーマ
    python3 scripts/sync_issue_counts.py ai-copyright
    python3 scripts/sync_issue_counts.py --check    # 書き換えず差分の有無だけ見る

件数はここでしか作らない。HTMLに数字を直接書かないこと。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from .issue_card_counts import IssueCountError, card_counts, span_html, span_id
    from .sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml
except ImportError:  # python3 scripts/sync_issue_counts.py
    from issue_card_counts import IssueCountError, card_counts, span_html, span_id  # type: ignore[no-redef]
    from sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml  # type: ignore[no-redef]


STYLE_MARKER = "/* issue-count: scripts/sync_issue_counts.py */"
STYLE_BLOCK = (
    f"<style>{STYLE_MARKER}\n"
    ".explainer-count{display:inline-block;margin-left:8px;padding:1px 9px;border-radius:999px;"
    "background:var(--accent-soft,#eef2ff);color:var(--accent,#1e1b4b);font-size:11px;font-weight:800;"
    "vertical-align:middle;white-space:nowrap;letter-spacing:0}\n"
    "</style>"
)


def _ensure_style(page: str) -> str:
    if STYLE_MARKER in page:
        return page
    head_close = page.find("</head>")
    if head_close < 0:
        raise IssueCountError("</head> が見つからず .explainer-count のCSSを入れられません")
    return page[:head_close] + STYLE_BLOCK + "\n" + page[head_close:]


def apply_counts(page: str, theme: str, cards: list[dict[str, object]]) -> str:
    page = _ensure_style(page)
    for card in cards:
        slug = str(card["slug"])
        title = str(card["title"])
        span = span_html(theme, slug, int(card["count"]))
        # 既存のタイトル（件数span付き/なしの両方）を拾って差し替える
        pattern = re.compile(
            r'(<p class="explainer-card-title">)'
            + re.escape(title)
            + r'(?:<span class="explainer-count"[^>]*>[^<]*</span>)?'
            + r"(</p>)"
        )
        page, replaced = pattern.subn(lambda m: m.group(1) + title + span + m.group(2), page)
        if replaced != 1:
            raise IssueCountError(
                f"{theme}: 論点カードが1件だけ見つかる必要があります（{replaced}件）: {title}"
            )
    return page


def sync_theme(theme: str, *, check: bool = False) -> tuple[str, bool]:
    themes = parse_themes_yaml(THEMES_YAML)
    if theme not in themes:
        raise IssueCountError(f"THEMES.yaml にテーマがありません: {theme}")
    theme_data = themes[theme]
    config_path = ROOT / "configs" / f"{theme}-reaction-map.json"
    if not config_path.is_file():
        raise IssueCountError(f"{theme}: config がありません: {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    html_path = ROOT / str(theme_data.get("html") or f"docs/{theme}-reaction-map.html")

    cards = card_counts(theme, config, theme_data.get("sample_file"))
    before = html_path.read_text(encoding="utf-8")
    after = apply_counts(before, theme, cards)
    changed = after != before
    if changed and not check:
        html_path.write_text(after, encoding="utf-8")
    detail = " / ".join(f"{card['slug']}={card['count']}件" for card in cards)
    return f"{theme}: {len(cards)}カード  {detail}", changed


def main() -> int:
    parser = argparse.ArgumentParser(description="論点カードに分類結果の件数を併記する")
    parser.add_argument("theme", nargs="?", help="THEMES.yaml のテーマslug（省略時は全テーマ）")
    parser.add_argument("--check", action="store_true", help="書き換えず、差分があれば exit 1")
    args = parser.parse_args()

    targets = [args.theme] if args.theme else list(parse_themes_yaml(THEMES_YAML))
    dirty = []
    try:
        for theme in targets:
            line, changed = sync_theme(theme, check=args.check)
            print(("UPDATE " if changed else "OK     ") + line)
            if changed:
                dirty.append(theme)
    except (IssueCountError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.check and dirty:
        print(f"NG  件数がHTMLと一致しません: {', '.join(dirty)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
