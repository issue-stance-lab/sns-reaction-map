#!/usr/bin/env python3
"""THEMES.yaml の正典データから docs/index.html の統計を同期する。"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
THEMES_YAML = ROOT / "THEMES.yaml"
INDEX_HTML = ROOT / "docs" / "index.html"


class PortalStatsError(RuntimeError):
    """ポータル統計の入力または置換先が不正なときの例外。"""


def _scalar(block: str, key: str) -> str | None:
    match = re.search(
        rf"^    {re.escape(key)}:[ \t]*([^#\n]*?)(?:[ \t]+#.*)?$",
        block,
        re.MULTILINE,
    )
    if not match:
        return None
    value = match.group(1).strip().strip('"').strip("'")
    return value or None


def parse_themes_yaml(path: Path = THEMES_YAML) -> dict[str, dict[str, Any]]:
    """THEMES.yaml から同期に必要な明示フィールドだけを読み込む。"""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PortalStatsError(f"THEMES.yaml を読めません: {path}: {exc}") from exc

    theme_pattern = re.compile(r"^  (\w[\w-]*):\s*$", re.MULTILINE)
    positions = [(match.start(), match.group(1)) for match in theme_pattern.finditer(text)]
    themes: dict[str, dict[str, Any]] = {}

    for index, (position, name) in enumerate(positions):
        end = positions[index + 1][0] if index + 1 < len(positions) else len(text)
        block = text[position:end]
        themes[name] = {
            "title": _scalar(block, "title"),
            "html": _scalar(block, "html"),
            "published": _scalar(block, "published") == "done",
            "page_v3": _scalar(block, "page_v3") == "done",
            "sample_file": _scalar(block, "sample_file"),
            "verification_file": _scalar(block, "verification_file"),
            "sample_period": _scalar(block, "sample_period"),
            "sample_source": _scalar(block, "sample_source"),
            "refresh_config": _scalar(block, "refresh_config"),
            "page_update_mode": _scalar(block, "page_update_mode"),
            "collect_at": _scalar(block, "collect_at"),
            "published_at": _scalar(block, "published_at"),
            "updated_at": _scalar(block, "updated_at"),
            "refresh_at": _scalar(block, "refresh_at"),
            "collect_delta": _scalar(block, "collect_delta"),
            "x_posted_at": _scalar(block, "x_posted_at"),
        }

    if not themes:
        raise PortalStatsError(f"テーマを1件も読み込めません: {path}")
    return themes


def _parse_iso_date(value: str | None, *, theme: str, field: str) -> date:
    if not value:
        raise PortalStatsError(f"{theme}: {field} がありません")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise PortalStatsError(f"{theme}: {field} が YYYY-MM-DD ではありません: {value}") from exc


def load_sample_records(root: Path, theme: str, relative_path: str | None) -> list[dict[str, Any]]:
    if not relative_path:
        raise PortalStatsError(f"{theme}: sample_file がありません")

    path = (root / relative_path).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise PortalStatsError(f"{theme}: sample_file がリポジトリ外を指しています: {relative_path}") from exc

    try:
        records = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PortalStatsError(f"{theme}: sample_file が存在しません: {relative_path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PortalStatsError(f"{theme}: sample_file を読めません: {relative_path}: {exc}") from exc

    if not isinstance(records, list):
        raise PortalStatsError(f"{theme}: sample_file のルートはJSON配列である必要があります: {relative_path}")
    if not records:
        raise PortalStatsError(f"{theme}: sample_file が0件です: {relative_path}")
    if not all(isinstance(record, dict) for record in records):
        raise PortalStatsError(f"{theme}: sample_file の各レコードはJSONオブジェクトである必要があります: {relative_path}")
    return records


def synthetic_record_count(records: list[dict[str, Any]]) -> int:
    """tweet_id または source が synthetic のレコード数。"""
    return sum(
        str(record.get("tweet_id", "")).lower().startswith("synthetic_")
        or "synthetic" in str(record.get("source", "")).lower()
        for record in records
    )


def count_sample_records(root: Path, theme: str, relative_path: str | None) -> int:
    return len(load_sample_records(root, theme, relative_path))


def compute_stats(
    themes: dict[str, dict[str, Any]],
    root: Path = ROOT,
    *,
    today: date | None = None,
    allow_synthetic: bool = False,
) -> dict[str, Any]:
    published = {name: theme for name, theme in themes.items() if theme["published"]}
    if not published:
        raise PortalStatsError("published: done のテーマがありません")

    counts: dict[str, int] = {}
    updated_dates: list[date] = []
    refresh_dates: list[date] = []
    refresh_at_missing: list[str] = []
    synthetic_counts: dict[str, int] = {}
    today = date.today() if today is None else today
    for name, theme in published.items():
        for field in ("sample_period", "sample_source"):
            if not theme.get(field):
                raise PortalStatsError(f"{name}: {field} がありません")
        records = load_sample_records(
            root, name, theme.get("verification_file") or theme.get("sample_file")
        )
        counts[name] = len(records)
        synthetic_counts[name] = synthetic_record_count(records)
        if synthetic_counts[name] and not allow_synthetic:
            raise PortalStatsError(
                f"{name}: sample_file に synthetic な tweet_id/source が"
                f" {synthetic_counts[name]}件あります"
            )
        updated_dates.append(_parse_iso_date(theme.get("updated_at"), theme=name, field="updated_at"))
        refresh_at = theme.get("refresh_at")
        if refresh_at:
            refresh_dates.append(_parse_iso_date(refresh_at, theme=name, field="refresh_at"))
        else:
            refresh_at_missing.append(name)

    upcoming_refresh_dates = [refresh_at for refresh_at in refresh_dates if refresh_at >= today]
    overdue_refresh_dates = [refresh_at for refresh_at in refresh_dates if refresh_at < today]

    return {
        "total_posts": sum(counts.values()),
        "theme_count": len(published),
        "voting_count": sum(1 for theme in published.values() if theme["page_v3"]),
        "last_updated": max(updated_dates),
        "next_update": min(upcoming_refresh_dates) if upcoming_refresh_dates else None,
        "overdue_count": len(overdue_refresh_dates),
        "badge_data": {
            str(theme.get("html") or name).removeprefix("docs/"): {
                key: value
                for key, value in (
                    ("pub", theme.get("published_at")),
                    ("upd", theme.get("updated_at")),
                    ("delta", theme.get("collect_delta")),
                    ("xpost", theme.get("x_posted_at")),
                )
                if value
            }
            for name, theme in published.items()
        },
        "latest_themes": [
            (name, theme.get("title"), theme.get("collect_delta"))
            for name, theme in published.items()
            if _parse_iso_date(theme.get("updated_at"), theme=str(theme.get("title")), field="updated_at")
            == max(updated_dates)
        ],
        "sample_counts": counts,
        "synthetic_counts": synthetic_counts,
        "refresh_at_missing": refresh_at_missing,
        "today": today,
    }


def replacement_specs(stats: dict[str, Any]) -> list[tuple[str, str, str]]:
    last_updated: date = stats["last_updated"]
    next_update: date | None = stats["next_update"]
    updated_short = f"{last_updated.month}/{last_updated.day}"
    updated_long = f"{last_updated.year}年{last_updated.month}月{last_updated.day}日"
    latest_summary = "・".join(
        f'{title}に<span id="latest-update-delta-{name}">{int(delta):,}</span>件追加' if delta else str(title)
        for name, title, delta in stats["latest_themes"]
    )
    if stats["overdue_count"]:
        next_badge = f'<span class="update-next-badge">更新予定を確認中（{stats["overdue_count"]}テーマ）</span>'
    elif next_update:
        days_until_update = (next_update - stats["today"]).days
        next_days = f"あと{days_until_update}日" if days_until_update > 0 else "本日更新予定"
        next_badge = f'<span class="update-next-badge">次回更新: {next_update.month}月{next_update.day}日（<span id="update-bar-days">{next_days}</span>）</span>'
    else:
        next_badge = '<span class="update-next-badge">更新予定を確認中</span>'
    next_iso = next_update.isoformat() if next_update else stats["today"].isoformat()
    badge_json = json.dumps(stats["badge_data"], ensure_ascii=False, separators=(",", ":"))

    specs = [
        ("分類済み投稿の用語", r"<small>分析済み投稿</small>|<small>分類済み投稿</small>", "<small>分類済み投稿</small>"),
        ("hero-total-samples", r'(<strong id="hero-total-samples">)[^<]*(</strong>)', rf'\g<1>{stats["total_posts"]:,}\2'),
        ("公開中のテーマ", r'(<small>公開中のテーマ</small><strong>)\d+(</strong>)', rf'\g<1>{stats["theme_count"]}\2'),
        ("投票受付中", r'(<em>)\d+テーマで投票受付中(</em>)', rf'\g<1>{stats["voting_count"]}テーマで投票受付中\2'),
        ("em更新日", r'(<strong id="hero-total-samples">[^<]*</strong><em>)[^<]*(</em>)', rf'\g<1>{updated_short}更新\2'),
        ("更新バー本文", r'最終更新: <strong>[^<]+</strong>（.*?）', f'最終更新: <strong>{updated_long}</strong>（{latest_summary}）'),
        ("update-bar次回更新", r'<span class="update-next-badge">.*?</span>(?:）</span>)?', next_badge),
        ("JS次回更新", r"new Date\('\d{4}-\d{2}-\d{2}T00:00:00\+09:00'\)", f"new Date('{next_iso}T00:00:00+09:00')"),
        ("JS期限超過表示", r"txt=days>0\?'あと'\+days\+'日':days===0\?'本日更新予定':'[^']+'", "txt=days>0?'あと'+days+'日':days===0?'本日更新予定':'予定を確認中'"),
        ("バッジデータ", r"var B=\{.*?\};", f"var B={badge_json};"),
    ]
    for theme in (
        "ai-copyright",
        "bike-blue-ticket",
        "bukatsu-chiiki",
        "consumption-tax-cut",
    ):
        specs.append(
            (
                f"注目の問い件数 {theme}",
                rf'(<strong id="featured-count-{re.escape(theme)}">)[^<]*(</strong>)',
                rf'\g<1>{stats["sample_counts"][theme]:,}\2',
            )
        )
    for theme, count in stats["sample_counts"].items():
        specs.append(
            (
                f"テーマカード件数 {theme}",
                rf'(<strong id="topic-count-{re.escape(theme)}">)[^<]*(</strong>)',
                rf'\g<1>{count:,}\2',
            )
        )
    return specs


def update_html(html: str, stats: dict[str, Any]) -> str:
    for label, pattern, replacement in replacement_specs(stats):
        html, count = re.subn(pattern, replacement, html)
        if count == 0:
            raise PortalStatsError(f"置換が0件です: {label}")
    return html


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    dry_run = "--dry-run" in argv
    try:
        themes = parse_themes_yaml()
        stats = compute_stats(themes)
        html_original = INDEX_HTML.read_text(encoding="utf-8")
        html_new = update_html(html_original, stats)
    except (OSError, PortalStatsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("=== sync_portal_stats ===")
    print(f"  分類済み投稿: {stats['total_posts']:,}件")
    print(f"  公開テーマ:   {stats['theme_count']}テーマ")
    print(f"  投票受付中:   {stats['voting_count']}テーマ")
    print(f"  最終更新:       {stats['last_updated'].isoformat()}")
    next_label = stats["next_update"].isoformat() if stats["next_update"] else "未定"
    print(f"  次回更新:       {next_label}")
    print(f"  期限超過:       {stats['overdue_count']}テーマ")

    if html_original == html_new:
        print("  → 変更なし（すでに同期済み）")
    elif dry_run:
        print("  → [dry-run] 変更あり（ファイルは書き換えません）")
    else:
        INDEX_HTML.write_text(html_new, encoding="utf-8")
        print(f"  → {INDEX_HTML} を更新しました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
