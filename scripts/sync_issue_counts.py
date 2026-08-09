#!/usr/bin/env python3
"""論点カードに、分類結果から計算した件数を併記する。

`configs/{theme}-reaction-map.json` の `issue_counts` を読み、各カードの
`<p class="explainer-card-title">` の末尾に

    <span class="explainer-count" id="issue-count-{theme}-{slug}">N件</span>

を差し込む（既にあれば数字を更新する）。何度実行しても結果は同じ。

`issue_counts.sync` に名前を挙げたテーマでは、同じ件数を次の場所にも書く。
論点カードだけを更新して他を放置すると、1つのページに新旧2つの件数が並ぶ
（2026-08-09、生成AIのページで「126件」と「340件」が同時に出ていた）。

    headings   … <article id="{anchor}"> 内の <span class="issue-count">N件</span>
    nav        … <nav class="quadrant-nav"><a href="#{anchor}">ラベル N</a>
    conclusion … 「議論の中心」の <span class="conclusion-count"><b>N</b>件</span>
    arena      … アリーナのセクター配列 const ISSUES=[{k:'ラベル', n:N}]

`conclusion` は最大件数の論点を指す見出しなので、`conclusion` に指定したカードが
最大でなくなったら書き換えず失敗する（見出しの文章を人が直す必要があるため）。

ビルダーが同じ場所を書くテーマ（副首都・消費税・皇室・憲法改正・高齢者）は
`sync` に入れない。1つの文の書き手は1つに保つ。

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
    from .issue_card_counts import IssueCountError, card_counts, other_count, span_html, span_id
    from .sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml
except ImportError:  # python3 scripts/sync_issue_counts.py
    from issue_card_counts import (  # type: ignore[no-redef]
        IssueCountError,
        card_counts,
        other_count,
        span_html,
        span_id,
    )
    from sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml  # type: ignore[no-redef]


SYNC_TARGETS = ("headings", "nav", "conclusion", "arena")


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


def apply_headings(page: str, theme: str, cards: list[dict[str, object]]) -> str:
    """論点セクションの見出しに出る <span class="issue-count">N件</span> を合わせる。"""
    for card in cards:
        anchor = str(card["anchor"])
        count = int(card["count"])
        # 該当セクションの開始位置から、次のセクションまでの間だけを書き換える
        start = page.find(f'id="{anchor}"')
        if start < 0:
            raise IssueCountError(f"{theme}: 論点セクションが見つかりません: id={anchor}")
        end = page.find('class="issue-block"', start + 1)
        segment = page[start : end if end > 0 else len(page)]
        updated, replaced = re.subn(
            r'<span class="issue-count">[\d,]+件</span>',
            f'<span class="issue-count">{count}件</span>',
            segment,
            count=1,
        )
        if replaced != 1:
            raise IssueCountError(
                f"{theme}: {anchor} の見出しに issue-count が1つだけ必要です（{replaced}個）"
            )
        page = page[:start] + updated + page[start + len(segment) :]
    return page


def apply_nav(page: str, theme: str, cards: list[dict[str, object]]) -> str:
    """論点ナビ <a href="#anchor">ラベル N</a> の末尾の数字を合わせる。"""
    for card in cards:
        anchor = str(card["anchor"])
        count = int(card["count"])
        pattern = re.compile(r'(<a href="#' + re.escape(anchor) + r'">[^<]*?)[\d,]+(</a>)')
        page, replaced = pattern.subn(lambda m: f"{m.group(1)}{count}{m.group(2)}", page)
        if replaced != 1:
            raise IssueCountError(
                f"{theme}: 論点ナビのリンクが1件だけ見つかる必要があります（{replaced}件）: #{anchor}"
            )
    return page


def apply_conclusion(page: str, theme: str, cards: list[dict[str, object]], slug: str) -> str:
    """「議論の中心」の件数を合わせる。最大論点が入れ替わったら書き換えずに失敗する。"""
    target = next((card for card in cards if str(card["slug"]) == slug), None)
    if target is None:
        raise IssueCountError(f"{theme}: issue_counts.conclusion のカードがありません: {slug}")
    top = max(cards, key=lambda card: int(card["count"]))
    if int(top["count"]) > int(target["count"]):
        raise IssueCountError(
            f"{theme}: 最大の論点が {target['slug']}({target['count']}件) から "
            f"{top['slug']}({top['count']}件) へ入れ替わりました。"
            "「議論の中心」の文章を書き直し、configs の issue_counts.conclusion も更新してください"
        )
    page, replaced = re.subn(
        r'(<span class="conclusion-count"><b>)[\d,]+(</b>件</span>)',
        lambda m: f"{m.group(1)}{int(target['count'])}{m.group(2)}",
        page,
        count=1,
    )
    if replaced != 1:
        raise IssueCountError(f"{theme}: conclusion-count が1つだけ必要です（{replaced}個）")
    return page


def apply_arena(page: str, theme: str, cards: list[dict[str, object]], other: int) -> str:
    """アリーナのセクター配列 const ISSUES=[{k:'ラベル', n:N}] を合わせる。

    セクターの角度と濃さはこの n から計算されるので、古いままだと点の分布と
    扇の広さが食い違う。並び順は SM_RAW の i と対応するため入れ替えない。
    """
    labels = {str(card["arena_label"]): int(card["count"]) for card in cards if card["arena_label"]}
    if not labels:
        raise IssueCountError(f"{theme}: arena を同期するには cards に arena_label が必要です")

    pattern = re.compile(
        r"(?P<head>\{\s*k\s*:\s*'(?P<label>(?:[^'\\]|\\.)*)'\s*,\s*n\s*:\s*)\d+"
    )
    found = [match.group("label") for match in pattern.finditer(page)]
    if not found:
        raise IssueCountError(f"{theme}: アリーナのセクター配列が見つかりません")
    missing = [label for label in labels if found.count(label) != 1]
    if missing:
        raise IssueCountError(
            f"{theme}: アリーナのセクターが1つだけ見つかる必要があります: {', '.join(missing)}"
            f"（ページ側のセクター: {', '.join(found)}）"
        )
    # カードに載らない論点はまとめて1つの「その他」セクターに入る
    extra = [label for label in found if label not in labels]
    if len(extra) > 1:
        raise IssueCountError(
            f"{theme}: カードに対応しないセクターが複数あります: {', '.join(extra)}。"
            "configs の cards に arena_label を足してください"
        )

    def replace(match: re.Match[str]) -> str:
        label = match.group("label")
        return f"{match.group('head')}{labels.get(label, other)}"

    return pattern.sub(replace, page)


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

    cards = card_counts(
        theme, config, theme_data.get("verification_file") or theme_data.get("sample_file")
    )
    sample_file = theme_data.get("verification_file") or theme_data.get("sample_file")
    block = config.get("issue_counts") or {}
    sync = [str(name) for name in (block.get("sync") or [])]
    unknown = [name for name in sync if name not in SYNC_TARGETS]
    if unknown:
        raise IssueCountError(
            f"{theme}: issue_counts.sync に未知の指定があります: {', '.join(unknown)}"
            f"（使えるのは {', '.join(SYNC_TARGETS)}）"
        )

    before = html_path.read_text(encoding="utf-8")
    after = apply_counts(before, theme, cards)
    if "headings" in sync:
        after = apply_headings(after, theme, cards)
    if "nav" in sync:
        after = apply_nav(after, theme, cards)
    if "conclusion" in sync:
        after = apply_conclusion(after, theme, cards, str(block.get("conclusion") or ""))
    if "arena" in sync:
        after = apply_arena(after, theme, cards, other_count(theme, config, sample_file))

    changed = after != before
    if changed and not check:
        html_path.write_text(after, encoding="utf-8")
    detail = " / ".join(f"{card['slug']}={card['count']}件" for card in cards)
    extra = f"  [+{','.join(sync)}]" if sync else ""
    return f"{theme}: {len(cards)}カード{extra}  {detail}", changed


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
