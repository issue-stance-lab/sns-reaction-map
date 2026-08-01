#!/usr/bin/env python3
"""docs/index.html の統計が THEMES.yaml の正典と一致するか検証する。"""

from __future__ import annotations

import re
from pathlib import Path

try:
    from .sync_portal_stats import (
        INDEX_HTML,
        ROOT,
        THEMES_YAML,
        PortalStatsError,
        compute_stats,
        parse_themes_yaml,
        replacement_specs,
    )
except ImportError:  # python3 scripts/verify_top_page.py
    from sync_portal_stats import (  # type: ignore[no-redef]
        INDEX_HTML,
        ROOT,
        THEMES_YAML,
        PortalStatsError,
        compute_stats,
        parse_themes_yaml,
        replacement_specs,
    )


def verify_top_page(
    root: Path = ROOT,
    themes_path: Path = THEMES_YAML,
    index_path: Path = INDEX_HTML,
) -> tuple[list[str], int]:
    """検証結果の行とNG件数を返す。tests/ からも呼び出せる。"""
    themes = parse_themes_yaml(themes_path)
    stats = compute_stats(themes, root, allow_synthetic=True)
    html = index_path.read_text(encoding="utf-8")
    lines = [
        "=== 数値の出所 ===",
        f"分類済み投稿   {stats['total_posts']:,}   ← sample_file の実レコード合計（{stats['theme_count']}テーマ）",
        f"公開テーマ数      {stats['theme_count']}   ← THEMES.yaml published:done",
        f"最終更新    {stats['last_updated'].isoformat()}  ← THEMES.yaml updated_at 最大",
        f"次回更新    {stats['next_update'].isoformat()}  ← THEMES.yaml refresh_at の今日以降の最小",
        "",
        "=== 置換の空振り検査 ===",
    ]

    failures = 0
    for label, pattern, replacement in replacement_specs(stats):
        matches = len(re.findall(pattern, html))
        replaced = re.sub(pattern, replacement, html)
        if matches > 0 and replaced == html:
            lines.append(f"OK  {label:<24} {matches}件マッチ")
        elif matches == 0:
            lines.append(f"NG  {label:<24} 0件マッチ")
            failures += 1
        else:
            lines.append(f"NG  {label:<24} {matches}件マッチ（値不一致）")
            failures += 1

    lines.extend(["", "=== 正典ファイル検査 ==="])
    for name, synthetic_count in stats["synthetic_counts"].items():
        if synthetic_count:
            lines.append(f"NG  {name:<28} synthetic {synthetic_count}件")
            failures += 1
        else:
            lines.append(f"OK  {name:<28} synthetic 0件")

    lines.extend(["", "=== 日付検査 ==="])
    if stats["next_update"] >= stats["today"]:
        lines.append(
            f"OK  次回更新 {stats['next_update'].isoformat()} "
            f"≥ 今日 {stats['today'].isoformat()}"
        )
    else:
        lines.append(
            f"NG  次回更新 {stats['next_update'].isoformat()} "
            f"< 今日 {stats['today'].isoformat()}"
        )
        failures += 1
    missing = stats["refresh_at_missing"]
    if missing:
        lines.append(f"OK  refresh_at 空欄は候補から除外: {', '.join(missing)}")
    else:
        lines.append("OK  refresh_at 空欄 0件")

    # S2以降で検査項目を追加するための枠。
    lines.extend(["", "=== 禁止表示 ===", "", "=== リンク ==="])
    return lines, failures


def main() -> int:
    try:
        lines, failures = verify_top_page()
    except (OSError, PortalStatsError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print("\n".join(lines))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
