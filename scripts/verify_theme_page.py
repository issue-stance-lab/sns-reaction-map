#!/usr/bin/env python3
"""テーマページの論拠、出典、調査条件、件数を検証する。"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

try:
    from .sync_portal_stats import ROOT, THEMES_YAML, load_sample_records, parse_themes_yaml
except ImportError:  # python3 scripts/verify_theme_page.py
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
    representative_positions = [
        pos for pos in (
            page.find("象限別の代表的な声"),
            page.find("代表サンプル"),
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
        map_count_text = f">{count}件 | セクター="
        if expected_count_text in page and map_count_text in page:
            lines.append(f"OK  件数表示が sample_file の実数と一致する（{count}件）")
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
