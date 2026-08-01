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

    config = json.loads(config_path.read_text(encoding="utf-8"))
    page = html_path.read_text(encoding="utf-8")
    rows = load_sample_records(root, theme, theme_data.get("sample_file"))
    count = len(rows)
    arguments = config.get("arguments")
    lines = [f"=== {theme} ==="]
    failures = 0

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
    if arguments_pos >= 0 and representative_pos >= 0 and arguments_pos < representative_pos:
        lines.append("OK  両側の論拠が代表投稿より前に出現する")
    else:
        lines.append("NG  両側の論拠が代表投稿より前に出現する")
        failures += 1

    if "社会全体の世論調査ではありません。" in page:
        lines.append("OK  「世論調査ではありません」が存在する")
    else:
        lines.append("NG  「世論調査ではありません」が存在する")
        failures += 1

    expected_count_text = f"公開投稿 {count}件"
    map_count_text = f">{count}件 | セクター="
    if expected_count_text in page and map_count_text in page:
        lines.append(f"OK  件数表示が sample_file の実数と一致する（{count}件）")
    else:
        lines.append(f"NG  件数表示が sample_file の実数と一致する（期待: {count}件）")
        failures += 1

    explainer_pos = page.find('id="explainer-section"')
    map_pos = page.find("<h2>SNS反応マップ</h2>")
    if explainer_pos >= 0 and arguments_pos > explainer_pos and map_pos > arguments_pos:
        lines.append("OK  arguments は6つの論点の後、SNS反応マップの前にある")
    else:
        lines.append("NG  arguments は6つの論点の後、SNS反応マップの前にある")
        failures += 1

    return lines, failures


def main() -> int:
    parser = argparse.ArgumentParser(description="テーマページの完成条件を検証する")
    parser.add_argument("theme", help="THEMES.yaml のテーマslug")
    parser.add_argument("--config", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--html", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        lines, failures = verify_theme_page(
            args.theme,
            config_path=args.config,
            html_path=args.html,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print("\n".join(lines))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
