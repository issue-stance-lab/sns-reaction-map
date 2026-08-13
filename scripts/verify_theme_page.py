#!/usr/bin/env python3
"""テーマページの論拠、出典、調査条件、件数を検証する。"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import subprocess
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
    from .verification_data import record_id_hash
    from .x_embed import period_label as _period_label
except ImportError:  # python3 scripts/verify_theme_page.py
    from issue_card_counts import (  # type: ignore[no-redef]
        IssueCountError,
        card_counts,
        count_by_issue,
        load_records,
        span_id,
    )
    from sync_portal_stats import ROOT, THEMES_YAML, load_sample_records, parse_themes_yaml  # type: ignore[no-redef]
    from verification_data import record_id_hash  # type: ignore[no-redef]
    from x_embed import period_label as _period_label  # type: ignore[no-redef]


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
MANAGED_COUNT_CLASSES = {"explainer-count", "issue-count", "hermes-issue-count"}


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


def _expected_review_note(root: Path, theme: str) -> str | None:
    """台帳から、そのテーマに表示してよい確認文言を返す。記録が無ければ None。"""
    ledger_path = root / "data/review-ledger.json"
    if not ledger_path.exists():
        return None
    themes = json.loads(ledger_path.read_text(encoding="utf-8")).get("themes") or {}
    entry = themes.get(theme)
    if not entry:
        return None
    if entry.get("status") == "reviewed":
        return f"AI分類。代表投稿{int(entry['samples'])}件の要旨を編集部が確認"
    return "AI分類。代表投稿は編集部が選定"


def _record_hashes(records: list[dict[str, Any]]) -> set[str]:
    hashes = set()
    for record in records:
        try:
            hashes.add(record_id_hash(record))
        except ValueError:
            continue
    return hashes


def _field(record: dict[str, Any], name: str) -> Any:
    nested = record.get("classification")
    if isinstance(nested, dict) and name in nested:
        return nested[name]
    return record.get(name)


def _arena_points(root: Path, page: str, theme: str) -> int | None:
    """公開マップの点数を数える。外部JS化されたテーマも同じ定義を使う。"""
    sources = [page]
    external = root / "docs" / f"{theme}-arena-data.js"
    if external.is_file():
        sources.append(external.read_text(encoding="utf-8"))
    pattern = re.compile(
        r"(?:SM_RAW|const P|[A-Z_]*ARENA_(?:RAW|DATA))\s*=\s*\[(.*?)\];",
        re.DOTALL,
    )
    for source in sources:
        match = pattern.search(source)
        if match:
            return match.group(1).count("{")
    return None


def _metric_line(
    theme: str,
    metric: str,
    base: int,
    actual: int | None,
    exceptions: dict[str, Any],
) -> tuple[str, int]:
    labels = {"issues": "論点", "map": "マップ", "stances": "賛否"}
    label = labels[metric]
    exception = exceptions.get(metric)
    if actual == base:
        if exception is not None:
            return f"NG  {theme}: {label}の例外宣言が不要に残っている", 1
        return f"OK  {label}の合計が母数と一致する（{base}件）", 0
    if actual is None:
        difference = base
        actual_label = "計測不能"
    else:
        difference = base - actual
        actual_label = f"{actual}件"
    if not isinstance(exception, dict):
        return f"NG  {theme}: {label}の合計が母数と一致しない（母数{base}件 / {label}{actual_label}）", 1
    reason = str(exception.get("reason") or "").strip()
    declared = exception.get("difference")
    if reason and isinstance(declared, int) and declared == difference:
        return (
            f"OK  {label}の差分が設定に明記されている"
            f"（母数{base}件 / {label}{actual_label} / 差{difference}件: {reason}）",
            0,
        )
    return (
        f"NG  {theme}: {label}の差分宣言が実際と一致しない"
        f"（実際{difference}件 / 宣言{declared!r} / reason={'あり' if reason else 'なし'}）",
        1,
    )


def verify_denominators(
    theme: str,
    config: dict[str, Any],
    rows: list[dict[str, Any]],
    page: str,
    root: Path,
) -> tuple[list[str], int]:
    block = config.get("issue_counts")
    if not isinstance(block, dict):
        return [f"NG  {theme}: configs に issue_counts がありません"], 1
    basis = str(block.get("basis") or "all")
    if basis not in ("all", "opinion"):
        return [f"NG  {theme}: issue_counts.basis が all / opinion ではありません: {basis}"], 1
    selected = rows if basis == "all" else [row for row in rows if _field(row, "is_opinion") is True]
    base = len(selected)
    issue_total = sum(1 for row in selected if _filled(_field(row, "main_issue")))
    stance_total = sum(1 for row in selected if _filled(_field(row, "stance")))
    map_total = _arena_points(root, page, theme)
    exceptions = block.get("denominator_exceptions") or {}
    if not isinstance(exceptions, dict):
        return [f"NG  {theme}: denominator_exceptions はオブジェクトである必要があります"], 1
    lines = [f"OK  母数は issue_counts.basis={basis}（{base}件）"]
    failures = 0
    for metric, actual in (("issues", issue_total), ("map", map_total), ("stances", stance_total)):
        line, failed = _metric_line(theme, metric, base, actual, exceptions)
        lines.append(line)
        failures += failed
    return lines, failures


def verify_page_count_spans(theme: str, page: str) -> tuple[list[str], int]:
    """ページ全体で、管理対象外の span に書かれた件数を拒否する。"""
    stale: list[str] = []
    for match in re.finditer(r"<span(?P<attrs>[^>]*)>\s*(?P<count>\d+)件\s*</span>", page):
        attrs = match.group("attrs")
        class_match = re.search(r'class=["\']([^"\']*)["\']', attrs)
        classes = set(class_match.group(1).split()) if class_match else set()
        if not classes.intersection(MANAGED_COUNT_CLASSES):
            line = page.count("\n", 0, match.start()) + 1
            stale.append(f"L{line}: {match.group(0)}")
    if stale:
        return [f"NG  {theme}: ページ全体に管理対象外の件数が残っている: " + ", ".join(stale)], 1
    return ["OK  ページ全体に管理対象外の件数が残っていない"], 0


def verify_largest_badge(
    theme: str, config: dict[str, Any], cards: list[dict[str, Any]], page: str
) -> tuple[list[str], int]:
    card_specs = (config.get("issue_counts") or {}).get("cards") or []
    counts = {str(card["slug"]): int(card["count"]) for card in cards}
    maximum = max(counts.values(), default=0)
    emphasized = re.compile(r"(?:最大勢力|(?:論点|争点)\s*[1１](?!\d))")
    checked: list[str] = []
    failures = 0
    for match in re.finditer(r'<span class="axis-kicker">(.*?)</span>\s*<h3>(.*?)</h3>', page, re.DOTALL):
        badge = html_lib.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()
        if not emphasized.search(badge):
            continue
        heading = html_lib.unescape(re.sub(r"<[^>]+>", "", match.group(2))).strip()
        candidates = []
        for spec in card_specs:
            labels = [str(value) for value in spec.get("main_issue") or []]
            title_label = re.split(r"\s+[—–]—?\s+", str(spec.get("title") or ""), maxsplit=1)[0]
            if title_label:
                labels.append(title_label)
            if any(label in heading or (len(label) >= 3 and label[:3] in heading) for label in labels):
                candidates.append(str(spec.get("slug") or ""))
        if len(candidates) != 1 or candidates[0] not in counts:
            checked.append(f"NG  {theme}: 強調表示の論点を特定できない（{badge}: {heading}）")
            failures += 1
            continue
        slug = candidates[0]
        if counts[slug] != maximum:
            checked.append(
                f"NG  {theme}: {badge} が最大論点ではない"
                f"（{slug}={counts[slug]}件 / 最大={maximum}件）"
            )
            failures += 1
        else:
            checked.append(f"OK  {badge} が最大論点に付いている（{slug}={maximum}件）")
    if not checked:
        checked.append("OK  最大勢力・論点1の強調表示はない")
    return checked, failures


def verify_issue_count_source(
    theme: str, config: dict[str, Any], sample_file: str | None
) -> tuple[list[str], int]:
    """論点カードの件数が、正典 sample_file と同じ投稿群から作られていることを確かめる。

    件数の一致だけでは不十分。koshitsu-tenpakai では issue-counts(268件) と
    sample_file(347件) にURLの重なりが1件も無いまま「268件」が表示されていた。
    件数はどちらも「それらしい数字」だったので誰も気づけなかった。
    だから **匿名化した投稿ID単位で部分集合であること** を見る。
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
    canon_hashes = _record_hashes(canon_records)
    if source == sample_file:
        lines.append(f"OK  件数の出所が sample_file そのもの（{len(canon_records)}件）")
    else:
        source_records = load_records(source)
        source_hashes = _record_hashes(source_records)
        if not source_hashes or not canon_hashes:
            lines.append(f"NG  投稿IDを持つレコードが無く部分集合を判定できない: {source}")
            failures += 1
        elif source_hashes <= canon_hashes:
            lines.append(
                f"OK  issue-counts の投稿IDが検証データの部分集合"
                f"（{len(source_hashes)}/{len(canon_hashes)}件）"
            )
        else:
            stray = sorted(source_hashes - canon_hashes)
            lines.append(
                f"NG  issue-counts の投稿IDが検証データの部分集合: "
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
    verification_file = theme_data.get("verification_file") or theme_data.get("sample_file")
    rows = load_sample_records(root, theme, verification_file)
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
    period_label = _period_label(period)
    collected_count_texts = (
        f"{source}で取得した公開投稿 {count}件",
        f"{source}で取得した公開投稿{count}件",
    )
    conditions_ok = (
        any(text in page for text in collected_count_texts)
        and f"取得期間: {period_label}" in page
    )
    if conditions_ok:
        lines.append(f"OK  調査条件（取得元・期間・件数）が表示されている（{period_label}）")
    else:
        lines.append("NG  調査条件（取得元・期間・件数）が表示されている")
        failures += 1

    # 代表投稿の確認表示は data/review-ledger.json の記録と一致していなければならない。
    # かつて全11テーマが同じ「AI分類・人間による代表投稿の確認あり」を表示していたが、
    # 何を何件確認したのかの記録が無く、検証できない主張になっていた（2026-08-12）。
    expected_note = _expected_review_note(root, theme)
    if expected_note is None:
        lines.append("NG  代表投稿の確認表示: data/review-ledger.json に記録がない")
        failures += 1
    # 確認表示は <span class="review-note"> で囲む。この件数は台帳由来で正典からは
    # 導けないため、verify_number_provenance.py が「ここだけ」除外できるようにしている。
    elif f'／<span class="review-note">{expected_note}</span>）' in page:
        lines.append(f"OK  代表投稿の確認表示が台帳と一致する（{expected_note}）")
    elif f"／{expected_note}）" in page:
        lines.append(
            "NG  代表投稿の確認表示が review-note で囲まれていない"
            "（scripts/seo/apply_review_note.py を実行すること）"
        )
        failures += 1
    else:
        lines.append(f"NG  代表投稿の確認表示が台帳と一致する: 「{expected_note}」であるべき")
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
        expected_count_texts = (f"公開投稿 {count}件", f"公開投稿{count}件")
        opinion_count = sum(
            1
            for row in rows
            if bool(
                (row.get("classification") or row).get(
                    "is_opinion", row.get("is_opinion")
                )
            )
        )
        classified_count = sum(
            1
            for row in rows
            if (row.get("classification") or row).get("main_issue")
        )
        map_count_texts = (
            f">{count}件 | セクター=",
            f">意見{opinion_count}件 | セクター=",
            f">{opinion_count}件 | セクター=",
            # アリーナが論点分類済みのレコードだけを描いているテーマ
            f">{classified_count}件 | セクター=",
            # 表示文言に依存しない目印（再設計後のページ。旧キャプションを持たない）
            f'data-arena-total="{opinion_count}"',
        )
        if any(text in page for text in expected_count_texts) and any(
            text in page for text in map_count_texts
        ):
            detail = f"全{count}件 / 意見{opinion_count}件" if opinion_count != count else f"{count}件"
            lines.append(f"OK  件数表示が sample_file の実数と一致する（{detail}）")
        else:
            lines.append(f"NG  件数表示が sample_file の実数と一致する（期待: {count}件）")
            failures += 1

    explainer_pos = page.find('id="explainer-section"')
    map_pos = page.find("<h2>SNS反応マップ</h2>")
    if map_pos < 0:
        # 見出し文言に依存しない目印（再設計後のページ）
        map_pos = page.find('id="issue-arena-section"')
    if arguments is not None:
        if explainer_pos >= 0 and arguments_pos > explainer_pos and map_pos > arguments_pos:
            lines.append("OK  arguments は6つの論点の後、SNS反応マップの前にある")
        else:
            lines.append("NG  arguments は6つの論点の後、SNS反応マップの前にある")
            failures += 1

    lines.append("=== 論点カードのデータ整合 ===")
    source_lines, source_failures = verify_issue_count_source(
        theme, config, verification_file
    )
    lines.extend(source_lines)
    failures += source_failures

    lines.append("=== 母数の統一 ===")
    denominator_lines, denominator_failures = verify_denominators(
        theme, config, rows, page, root
    )
    lines.extend(denominator_lines)
    failures += denominator_failures

    lines.append("=== 論点カード ===")
    try:
        cards = card_counts(theme, config, verification_file)
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

    lines.append("=== ページ全体の件数表示 ===")
    count_lines, count_failures = verify_page_count_spans(theme, page)
    lines.extend(count_lines)
    failures += count_failures

    lines.append("=== 最大勢力バッジ ===")
    badge_lines, badge_failures = verify_largest_badge(theme, config, cards, page)
    lines.extend(badge_lines)
    failures += badge_failures

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
            rebuild = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "verify_builder_rebuildability.py")],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            lines.append(rebuild.stdout.strip())
            if rebuild.stderr.strip():
                lines.append(rebuild.stderr.strip())
            if rebuild.returncode:
                failures += 1
            lines.append(f"=== 全テーマ結果: {len(parse_themes_yaml(THEMES_YAML))}件 / NG {failures}件 ===")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print("\n".join(lines))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
