#!/usr/bin/env python3
"""テーマページの論拠、出典、調査条件、件数を検証する。"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

try:
    from .issue_card_counts import (
        IssueCountError,
        card_counts,
        count_by_issue,
        load_records,
        span_id,
    )
    from .sync_portal_stats import ROOT, THEMES_YAML, load_sample_records, parse_themes_yaml
except ImportError:  # python3 scripts/verify_theme_page.py
    from issue_card_counts import (  # type: ignore[no-redef]
        IssueCountError,
        card_counts,
        count_by_issue,
        load_records,
        span_id,
    )
    from sync_portal_stats import ROOT, THEMES_YAML, load_sample_records, parse_themes_yaml  # type: ignore[no-redef]


REQUIRED_ARGUMENT_FIELDS = (
    "summary_30s",
    "side_a",
    "side_b",
    "shared_premise",
    "real_conflict",
    "unresolved",
    "sources",
)
REQUIRED_SIDE_FIELDS = ("label", "strongest", "basis")


def _filled(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, dict):
        return bool(value)
    return value is not None


def _arguments_complete(arguments: Any) -> bool:
    if not isinstance(arguments, dict):
        return False
    if not all(_filled(arguments.get(field)) for field in REQUIRED_ARGUMENT_FIELDS):
        return False
    for side_name in ("side_a", "side_b"):
        side = arguments.get(side_name)
        if not isinstance(side, dict) or not all(_filled(side.get(field)) for field in REQUIRED_SIDE_FIELDS):
            return False
    sources = arguments.get("sources")
    return isinstance(sources, list) and all(
        isinstance(source, dict)
        and _filled(source.get("label"))
        and _filled(source.get("url"))
        for source in sources
    )


def _record_urls(records: list[dict[str, Any]]) -> set[str]:
    urls = set()
    for record in records:
        nested = record.get("classification")
        source = nested if isinstance(nested, dict) else record
        url = record.get("url") or source.get("url")
        if url:
            urls.add(str(url))
    return urls


def verify_issue_count_source(
    theme: str, config: dict[str, Any], sample_file: str | None
) -> tuple[list[str], int]:
    """論点カードの件数が、正典 sample_file と同じ投稿群から作られていることを確かめる。

    件数の一致だけでは不十分。koshitsu-tenpakai では issue-counts(268件) と
    sample_file(347件) にURLの重なりが1件も無いまま「268件」が表示されていた。
    件数はどちらも「それらしい数字」だったので誰も気づけなかった。
    だから **URL単位で部分集合であること** を見る。
    """
    lines: list[str] = []
    failures = 0
    block = config.get("issue_counts")
    if not isinstance(block, dict):
        return [f"NG  {theme}: configs に issue_counts がありません"], 1
    if not sample_file:
        return [f"NG  {theme}: THEMES.yaml に sample_file がありません"], 1

    source = str(block.get("source") or sample_file)
    basis = str(block.get("basis") or "all")

    if "synthetic" in source or "synthetic" in sample_file:
        lines.append(f"NG  合成データを件数の出所にしていない: {source} / {sample_file}")
        failures += 1
    else:
        lines.append("OK  合成データを件数の出所にしていない")

    canon_records = load_records(sample_file)
    canon_urls = _record_urls(canon_records)
    if source == sample_file:
        lines.append(f"OK  件数の出所が sample_file そのもの（{len(canon_records)}件）")
    else:
        source_records = load_records(source)
        source_urls = _record_urls(source_records)
        if not source_urls or not canon_urls:
            lines.append(f"NG  URLを持つレコードが無く部分集合を判定できない: {source}")
            failures += 1
        elif source_urls <= canon_urls:
            lines.append(
                f"OK  issue-counts のURLが sample_file の部分集合"
                f"（{len(source_urls)}/{len(canon_urls)}件）"
            )
        else:
            stray = sorted(source_urls - canon_urls)
            lines.append(
                f"NG  issue-counts のURLが sample_file の部分集合: "
                f"はみ出し{len(stray)}件 例 {stray[0]}"
            )
            failures += 1

        if len(source_records) <= len(canon_records):
            lines.append(
                f"OK  issue-counts の件数が sample_file 以下"
                f"（{len(source_records)} ≤ {len(canon_records)}）"
            )
        else:
            lines.append(
                f"NG  issue-counts の件数が sample_file 以下"
                f"（{len(source_records)} > {len(canon_records)}）"
            )
            failures += 1

    # カードのラベルが分類結果に実在するか（正規表現などで後から作った擬似ラベルを弾く）。
    # sample_file が2D分類のみで main_issue を持たないテーマでは、論点ラベルの出所は
    # issue-counts 側になる。その場合ラベル照合は card_counts に任せ、ここでは出所の
    # 素性（合成でない・URLが部分集合）だけを見る。
    canon_labels = set(count_by_issue(canon_records, basis))
    if not canon_labels:
        lines.append(
            f"OK  カードの main_issue は issue-counts 側が出所"
            f"（sample_file に main_issue なし: {sample_file}）"
        )
        return lines, failures

    unknown = [
        str(issue)
        for card in block.get("cards") or []
        if isinstance(card, dict)
        for issue in (card.get("main_issue") or [])
        if str(issue) not in canon_labels
    ]
    if not unknown:
        lines.append(f"OK  全カードの main_issue が sample_file に実在する（{len(canon_labels)}ラベル）")
    else:
        lines.append(
            f"NG  全カードの main_issue が sample_file に実在する: "
            f"{', '.join(unknown)}（実在: {', '.join(sorted(canon_labels))}）"
        )
        failures += 1

    return lines, failures


def _http_200(url: str) -> bool:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "issue-stance-aggregator-theme-verifier/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


def verify_theme_page(
    theme: str,
    *,
    root: Path = ROOT,
    themes_path: Path = THEMES_YAML,
    config_path: Path | None = None,
    html_path: Path | None = None,
    url_checker: Callable[[str], bool] = _http_200,
) -> tuple[list[str], int]:
    themes = parse_themes_yaml(themes_path)
    if theme not in themes:
        raise ValueError(f"THEMES.yaml にテーマがありません: {theme}")
    theme_data = themes[theme]
    config_path = config_path or root / "configs" / f"{theme}-reaction-map.json"
    html_path = html_path or root / str(theme_data.get("html") or f"docs/{theme}-reaction-map.html")

    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.is_file() else {}
    page = html_path.read_text(encoding="utf-8")
    rows = load_sample_records(root, theme, theme_data.get("sample_file"))
    count = len(rows)
    arguments = config.get("arguments")
    lines = [f"=== {theme} ==="]
    failures = 0

    if arguments is not None:
        if _arguments_complete(arguments):
            lines.append("OK  arguments 全フィールドが埋まっている")
        else:
            lines.append("NG  arguments 全フィールドが埋まっている")
            failures += 1

    sources = arguments.get("sources", []) if isinstance(arguments, dict) else []
    invalid_sources = [
        str(source.get("url") or "")
        for source in sources
        if not url_checker(str(source.get("url") or ""))
    ]
    if arguments is not None:
        if sources and not invalid_sources:
            lines.append(f"OK  sources のリンクが全て有効（HTTP 200、{len(sources)}件）")
        else:
            detail = ", ".join(invalid_sources) if invalid_sources else "sources なし"
            lines.append(f"NG  sources のリンクが全て有効（HTTP 200）: {detail}")
            failures += 1

    arguments_pos = page.find('id="strongest-arguments"')
    issue_voices = re.search(r"\d+つの論点とXの声", page)
    representative_positions = [
        pos for pos in (
            page.find("象限別の代表的な声"),
            page.find("代表サンプル"),
            issue_voices.start() if issue_voices else -1,
        ) if pos >= 0
    ]
    representative_pos = min(representative_positions, default=-1)
    if arguments is not None:
        if arguments_pos >= 0 and representative_pos >= 0 and arguments_pos < representative_pos:
            lines.append("OK  両側の論拠が代表投稿より前に出現する")
        else:
            lines.append("NG  両側の論拠が代表投稿より前に出現する")
            failures += 1

    lines.append("=== 数字の分離 ===")

    if "社会全体の世論調査ではありません。" in page:
        lines.append("OK  「世論調査ではありません」が存在する")
    else:
        lines.append("NG  「世論調査ではありません」が存在する")
        failures += 1

    conditions_pos = page.find("<!-- RESEARCH_CONDITIONS_START -->")
    stats_pos = page.find('<section class="stats')
    if conditions_pos >= 0 and stats_pos >= 0 and conditions_pos < stats_pos:
        lines.append("OK  注意書きが最初の数値表示より前にある")
    else:
        lines.append("NG  注意書きが最初の数値表示より前にある")
        failures += 1

    topic_script = (root / "docs" / "topic-modern.js").read_text(encoding="utf-8")
    vote_script = (root / "docs" / "vote2d.js").read_text(encoding="utf-8")
    if (
        "参加者投票 n=" in topic_script
        and "参加者投票 n=" in vote_script
        and 'data-vote-topic="' in page
    ):
        lines.append("OK  参加者投票に n=表記がある")
    else:
        lines.append("NG  参加者投票に n=表記がある")
        failures += 1

    source = str(theme_data.get("sample_source") or "")
    period = str(theme_data.get("sample_period") or "")
    period_label = "記録なし" if period.lower() == "unknown" else period
    conditions_ok = (
        f"{source}で取得した公開投稿 {count}件" in page
        and f"取得期間: {period_label}" in page
        and "AI分類・人間による代表投稿の確認あり" in page
    )
    if conditions_ok:
        lines.append(f"OK  調査条件（取得元・期間・件数）が表示されている（{period_label}）")
    else:
        lines.append("NG  調査条件（取得元・期間・件数）が表示されている")
        failures += 1

    gate_text = page + "\n" + topic_script + "\n" + vote_script
    gate_tokens = ("lockArenaUntilVote", "arena-is-locked", "まず投票してから", "blur(8px)")
    found_gates = [token for token in gate_tokens if token in gate_text]
    if not found_gates:
        lines.append("OK  投票ゲート（blur / lockArenaUntilVote）が存在しない")
    else:
        lines.append(f"NG  投票ゲートが存在する: {', '.join(found_gates)}")
        failures += 1

    if arguments is not None:
        expected_count_text = f"公開投稿 {count}件"
        opinion_count = sum(
            1
            for row in rows
            if bool((row.get("classification") or row).get("is_opinion"))
        )
        classified_count = sum(
            1
            for row in rows
            if (row.get("classification") or row).get("main_issue")
        )
        map_count_texts = (
            f">{count}件 | セクター=",
            f">意見{opinion_count}件 | セクター=",
            # アリーナが論点分類済みのレコードだけを描いているテーマ
            f">{classified_count}件 | セクター=",
        )
        if expected_count_text in page and any(text in page for text in map_count_texts):
            detail = f"全{count}件 / 意見{opinion_count}件" if opinion_count != count else f"{count}件"
            lines.append(f"OK  件数表示が sample_file の実数と一致する（{detail}）")
        else:
            lines.append(f"NG  件数表示が sample_file の実数と一致する（期待: {count}件）")
            failures += 1

    explainer_pos = page.find('id="explainer-section"')
    map_pos = page.find("<h2>SNS反応マップ</h2>")
    if arguments is not None:
        if explainer_pos >= 0 and arguments_pos > explainer_pos and map_pos > arguments_pos:
            lines.append("OK  arguments は6つの論点の後、SNS反応マップの前にある")
        else:
            lines.append("NG  arguments は6つの論点の後、SNS反応マップの前にある")
            failures += 1

    lines.append("=== 論点カードのデータ整合 ===")
    source_lines, source_failures = verify_issue_count_source(
        theme, config, theme_data.get("sample_file")
    )
    lines.extend(source_lines)
    failures += source_failures

    lines.append("=== 論点カード ===")
    try:
        cards = card_counts(theme, config, theme_data.get("sample_file"))
    except IssueCountError as exc:
        lines.append(f"NG  論点カードの件数を分類結果から計算できる: {exc}")
        return lines, failures + 1

    missing = [
        card["slug"]
        for card in cards
        if f'id="{span_id(theme, str(card["slug"]))}"' not in page
    ]
    if not missing:
        lines.append(f"OK  全カードに件数が併記されている（id付き、{len(cards)}枚）")
    else:
        lines.append(f"NG  全カードに件数が併記されている（id付き）: 欠落 {', '.join(missing)}")
        failures += 1

    mismatched = []
    for card in cards:
        marker = re.search(
            rf'<span class="explainer-count" id="{re.escape(span_id(theme, str(card["slug"])))}">(\d+)件</span>',
            page,
        )
        if not marker or int(marker.group(1)) != int(card["count"]):
            shown = marker.group(1) + "件" if marker else "なし"
            mismatched.append(f'{card["slug"]}（表示{shown} / 分類{card["count"]}件）')
    if not mismatched:
        detail = " / ".join(f'{card["slug"]}={card["count"]}' for card in cards)
        lines.append(f"OK  論点カードの件数が分類結果と一致する（{detail}）")
    else:
        lines.append(f"NG  論点カードの件数が分類結果と一致する: {', '.join(mismatched)}")
        failures += 1

    # 生成した span 以外に同じ件数が書かれていると、次のデータ補充で片方だけ古くなる
    stale = []
    for block in re.finditer(r'<article class="explainer-card".*?</article>', page, re.DOTALL):
        card_html = block.group(0)
        for card in cards:
            marker = f'id="{span_id(theme, str(card["slug"]))}"'
            if marker not in card_html:
                continue
            stripped = re.sub(r'<span class="explainer-count"[^>]*>[^<]*</span>', "", card_html)
            if re.search(rf'(?<!\d){card["count"]}件', stripped):
                stale.append(f'{card["slug"]}（{card["count"]}件）')
    if not stale:
        lines.append("OK  ハードコードされた件数が残っていない")
    else:
        lines.append(f"NG  ハードコードされた件数が残っている: {', '.join(stale)}")
        failures += 1

    return lines, failures


def main() -> int:
    parser = argparse.ArgumentParser(description="テーマページの完成条件を検証する")
    parser.add_argument("theme", nargs="?", help="THEMES.yaml のテーマslug（省略時は全テーマ）")
    parser.add_argument("--config", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--html", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.theme:
            lines, failures = verify_theme_page(
                args.theme,
                config_path=args.config,
                html_path=args.html,
            )
        else:
            if args.config or args.html:
                parser.error("--config/--html は個別テーマ指定時のみ使用できます")
            lines = []
            failures = 0
            for theme in parse_themes_yaml(THEMES_YAML):
                theme_lines, theme_failures = verify_theme_page(theme)
                lines.extend(theme_lines)
                failures += theme_failures
            lines.append(f"=== 全テーマ結果: {len(parse_themes_yaml(THEMES_YAML))}件 / NG {failures}件 ===")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print("\n".join(lines))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
