#!/usr/bin/env python3
"""生成AIと著作権ページの数字を、正典の分類結果から一括生成する。

このページは長らく3つの数字の体系が混在していた（2026-08-07 に判明）。

- 論点カードとアリーナ: 2D分類由来の7論点
- 「世論の潮目」ウィジェット: 2026-07-26 に新設した分類器の5論点
- 「詳細データ」の分類別件数: さらに古い original_category

正典を単一 taxonomy へ統一したので、このスクリプトが **sample_file だけ** を読み、
ページの数字まわりとアリーナの点を丸ごと作り直す。論点・立場・座標の定義は
`scripts/ai_copyright_taxonomy.py` からのみ読む。

生成する箇所:

- docs/ai-copyright-arena-data.js の SM_RAW（アリーナの点）
- 調査条件の「公開投稿 N件」
- ヒーローの lead 文の件数
- insight カード3枚（分析対象の意見 / 最も多い立場 / 最も話された論点）
- 「詳細データ」の分類別件数（論点別・立場別へ置き換える）
- 論点カードの件数（sync_issue_counts.py を呼ぶ）

潮目ウィジェットは更新回どうしの比較なので adapter 側で扱う。

    python3 scripts/build_ai_copyright_arena.py            # 公開ページを更新
    python3 scripts/build_ai_copyright_arena.py --check    # 書き換えず差分があれば exit 1
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_copyright_taxonomy import (  # noqa: E402
    ARENA_LABELS,
    ISSUE_ORDER,
    OTHER,
    SHORT_ISSUE_LABELS,
    SHORT_STANCE_LABELS,
    STANCE_NOTES,
    STANCE_ORDER,
    arena_e,
    arena_x,
    issue_index,
)
from sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml  # noqa: E402

THEME = "ai-copyright"
PAGE = ROOT / "docs" / "ai-copyright-reaction-map.html"
ARENA_DATA = ROOT / "docs" / "ai-copyright-arena-data.js"


class BuildError(RuntimeError):
    pass


def classification(record: dict[str, Any]) -> dict[str, Any]:
    nested = record.get("classification")
    return nested if isinstance(nested, dict) else record


def load_canon(source: Path | None = None) -> tuple[list[dict[str, Any]], str]:
    """THEMES.yaml の sample_file を唯一の出所として読む。staging からは source を渡す。"""
    if source is not None:
        path, label = Path(source), str(source)
    else:
        themes = parse_themes_yaml(THEMES_YAML)
        relative = str(themes.get(THEME, {}).get("sample_file") or "")
        if not relative:
            raise BuildError(f"{THEME}: sample_file が未設定です")
        if "synthetic" in relative:
            raise BuildError(f"{THEME}: 合成データを正典にはできません: {relative}")
        path, label = ROOT / relative, relative

    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise BuildError(f"{THEME}: 分類結果がJSON配列ではありません: {label}")
    missing = [r for r in records if not classification(r).get("main_issue")]
    if missing:
        raise BuildError(f"{THEME}: main_issue を持たないレコードが{len(missing)}件あります")
    unknown = {classification(r)["main_issue"] for r in records} - set(ISSUE_ORDER)
    if unknown:
        raise BuildError(f"{THEME}: taxonomy 外の論点があります: {sorted(unknown)}")
    return records, label


def replace_once(page: str, pattern: str, replacement: str, label: str, flags: int = 0) -> str:
    updated, count = re.subn(pattern, lambda _: replacement, page, count=1, flags=flags)
    if count != 1:
        raise BuildError(f"{label} の置換に失敗しました（{count}件マッチ）")
    return updated


def apply_tide(page_path: Path, records: list[dict[str, Any]]) -> None:
    """潮目ウィジェットを正典の更新回スライスから作り直す。

    以前は 2026-07-26 に新設した分類器の5論点で作られており、ページの他の場所
    （7論点）と食い違っていた。正典を fetched_at で切って同じ taxonomy で描く。
    """
    import tempfile

    sys.path.insert(0, str(ROOT / "scripts"))
    from inject_tide_widget import (  # type: ignore[import-not-found]
        THEMES,
        _load_tide_css,
        generate_tide_section,
        inject_into_html,
        load_classified,
    )

    dates = sorted({str(r.get("fetched_at") or "")[:10] for r in records if r.get("fetched_at")})
    if len(dates) < 2:
        raise BuildError(f"潮目に使える収集日が足りません: {dates}")
    previous_date, current_date = dates[-2], dates[-1]
    base = next(item for item in THEMES if item["slug"] == THEME).copy()
    base["prev_label"] = f"{int(previous_date[5:7])}月{int(previous_date[8:10])}日"
    base["cur_label"] = f"{int(current_date[5:7])}月{int(current_date[8:10])}日"
    base["note"] = (
        f"比較対象：{base['prev_label']}収集分のうち意見投稿／{base['cur_label']}収集分のうち意見投稿。"
        "同じ検索語セットで取得した投稿をAIで分類しています。サンプルの構成比の変化であり、"
        "同じ人の意見が移動したことや世論全体の変化を示すものではありません。"
    )

    def slice_for(date: str) -> list[dict[str, Any]]:
        return [r for r in records if str(r.get("fetched_at") or "")[:10] == date]

    with tempfile.TemporaryDirectory() as directory:
        paths = {}
        for name, date in (("prev", previous_date), ("cur", current_date)):
            path = Path(directory) / f"{name}.json"
            path.write_text(json.dumps(slice_for(date), ensure_ascii=False), encoding="utf-8")
            paths[name] = path
        previous = load_classified(paths["prev"], base["use_relevance_filter"])
        current = load_classified(paths["cur"], base["use_relevance_filter"])
    tide = generate_tide_section(base, previous, current)
    page_path.write_text(inject_into_html(page_path, tide, _load_tide_css()), encoding="utf-8")


def set_insight(page: str, label: str, value: str, note: str, meter: int) -> str:
    """ラベルで article を特定してから中身を書き換える。

    以前はページ全体に対する正規表現で置換していたため、3枚目のカード用の
    パターンが1枚目に当たって値が入れ替わった（2026-08-07）。カードの境界を
    先に特定してから中を書き換える。
    """
    pattern = re.compile(
        r'(<article class="stat insight-stat"[^>]*>\s*<div class="insight-head">.*?'
        r'<span class="insight-label">' + re.escape(label) + r'</span></div>\s*)'
        r'<strong class="insight-value">.*?</strong>\s*'
        r'<p class="insight-note">.*?</p>\s*'
        r'(<div class="insight-meter" aria-hidden="true"><i style="width:)\d+(%"></i></div>)',
        re.S,
    )
    match = pattern.search(page)
    if not match:
        raise BuildError(f"insight『{label}』のカードが見つかりません")
    replacement = (
        match.group(1)
        + f'<strong class="insight-value">{value}</strong>\n'
        + f'        <p class="insight-note">{note}</p>\n        '
        + match.group(2) + str(meter) + match.group(3)
    )
    return page[: match.start()] + replacement + page[match.end() :]


def build_arena_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """アリーナの点。意見投稿だけを描く（非意見は論点の分布を歪めるため）。"""
    rows = []
    for record in records:
        value = classification(record)
        if not value.get("is_opinion"):
            continue
        summary = str(value.get("summary") or "").strip()
        url = str(record.get("url") or "").strip()
        if not summary or not url:
            continue
        rows.append(
            {
                "x": arena_x(str(value.get("stance") or ""), str(value.get("intensity") or "")),
                "e": arena_e(str(value.get("intensity") or "")),
                "c": round(float(value.get("confidence") or 0.5), 2),
                "i": issue_index(str(value["main_issue"])),
                "s": summary[:60],
                "u": url,
            }
        )
    rows.sort(key=lambda r: (r["i"], r["u"]))
    return rows


def render_arena_data(rows: list[dict[str, Any]]) -> str:
    body = ",\n".join(
        "{{x:{x},e:{e},c:{c},i:{i},s:{s},u:{u}}}".format(
            x=r["x"], e=r["e"], c=r["c"], i=r["i"],
            s=json.dumps(r["s"], ensure_ascii=False),
            u=json.dumps(r["u"], ensure_ascii=False),
        )
        for r in rows
    )
    return (
        "/* generated by scripts/build_ai_copyright_arena.py — 手で編集しない */\n"
        f"const SM_RAW=[\n{body}\n];\n"
    )


def build_issue_bars(counts: Counter, total: int) -> str:
    """詳細データの「分類別件数」を論点別のバーに置き換える。"""
    top = counts.most_common(1)[0][1] if counts else 1
    parts = []
    for name in ISSUE_ORDER:
        value = counts.get(name, 0)
        if not value:
            continue
        width = max(4, round(value / top * 100))
        parts.append(
            '<div class="bar-row" data-category="{name}"><div class="bar-meta">'
            '<span>{name}</span><strong>{value}</strong></div>'
            '<div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div></div>'.format(
                name=html.escape(name), value=value, width=width
            )
        )
    return "\n".join(parts)


def atlas_row(label: str, value: int, top: int, *, other: bool = False) -> str:
    width = max(2, round(value / top * 100)) if value else 0
    label_html = html.escape(label)
    if other:
        label_html += "<small>分類保留</small>"
    return (
        '<div class="theme-atlas-row{extra}"><span class="theme-atlas-label">{label}</span>'
        '<span class="theme-atlas-track"><span class="theme-atlas-bar" style="width:{width}%"></span>'
        '<strong class="theme-atlas-count">{value}<small>件</small></strong></span></div>'
    ).format(extra=" is-other" if other else "", label=label_html, width=width, value=value)


def build_theme_atlas(counts: Counter) -> str:
    """テーマ内の「論点アトラス」の行を分類結果から作る。

    行ラベルと件数を手書きすると、論点体系を変えたときに追随しない。潮目ウィジェットが
    旧5論点のまま1ヶ月気づかれなかったのと同じ壊れ方なので、ここでは書かずに生成する。
    並びは ISSUE_ORDER と同じにして、下のアリーナのセクター順と揃える。
    「その他」は論点ではなく分類保留なので、本体の論点と分けて最後に置く。
    """
    main = [name for name in ISSUE_ORDER if name != OTHER]
    top = max((counts.get(name, 0) for name in main), default=0) or 1
    rows = [atlas_row(ARENA_LABELS.get(name, name), counts.get(name, 0), top) for name in main]
    rows.append(atlas_row(ARENA_LABELS.get(OTHER, OTHER), counts.get(OTHER, 0), top, other=True))
    return "\n".join(rows)


def build_stance_bars(counts: Counter) -> str:
    top = counts.most_common(1)[0][1] if counts else 1
    parts = []
    for name in STANCE_ORDER:
        value = counts.get(name, 0)
        if not value:
            continue
        width = max(4, round(value / top * 100))
        parts.append(
            '<div class="bar-row" data-category="{name}"><div class="bar-meta">'
            '<span>{name}</span><strong>{value}</strong></div>'
            '<div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div></div>'.format(
                name=html.escape(name), value=value, width=width
            )
        )
    return "\n".join(parts)


def build(
    *,
    check: bool = False,
    source: Path | None = None,
    template: Path | None = None,
    output: Path | None = None,
    data_output: Path | None = None,
) -> tuple[list[str], bool]:
    records, label = load_canon(source)
    opinions = [r for r in records if classification(r).get("is_opinion")]
    total, opinion_total = len(records), len(opinions)
    if not opinion_total:
        raise BuildError(f"{THEME}: 意見投稿が0件です")

    issue_counts = Counter(classification(r)["main_issue"] for r in opinions)
    stance_counts = Counter(str(classification(r).get("stance") or "") for r in opinions)
    ranked = [(n, c) for n, c in issue_counts.most_common() if n != OTHER]
    top_issue, top_issue_count = ranked[0]
    top_stance, top_stance_count = stance_counts.most_common(1)[0]
    stance_pct = round(top_stance_count / opinion_total * 100)
    issue_pct = round(top_issue_count / opinion_total * 100)

    arena_rows = build_arena_rows(records)
    arena_text = render_arena_data(arena_rows)
    arena_path = Path(data_output) if data_output else ARENA_DATA
    arena_before = arena_path.read_text(encoding="utf-8") if arena_path.is_file() else ""

    html_path = Path(template) if template else PAGE
    before = html_path.read_text(encoding="utf-8")
    page = before

    page = replace_once(
        page,
        r"で取得した公開投稿 [\d,]+件",
        f"で取得した公開投稿 {total}件",
        "調査条件の件数",
    )
    page = replace_once(
        page,
        r"分析対象となった意見[\d,]+件をAIが\d+つの論点に整理しました",
        f"分析対象となった意見{opinion_total}件をAIが{len(ISSUE_ORDER) - 1}つの論点に整理しました",
        "lead文の件数",
    )
    page = replace_once(
        page,
        r'data-arena-total="[\d,]*"',
        f'data-arena-total="{opinion_total}"',
        "アリーナの母数",
    )
    # 再設計で入った見出しと代替テキストの件数。生成側を持たないと次の更新で古くなる
    page = replace_once(
        page,
        r"問いから分かれる、[\d,]+件の意見",
        f"問いから分かれる、{opinion_total:,}件の意見",
        "アリーナの見出し件数",
    )
    page = replace_once(
        page,
        r"の\d+つの論点と分類保留に[\d,]+件の意見を配置した図",
        f"の{len(ISSUE_ORDER) - 1}つの論点と分類保留に{opinion_total:,}件の意見を配置した図",
        "アリーナ図の代替テキスト",
    )
    page = set_insight(
        page,
        "分析対象の意見",
        f"{opinion_total:,}<small>件</small>",
        "権利保護、規制、競争力、モラルの声を整理",
        100,
    )
    page = set_insight(
        page,
        "最も多い立場",
        f"{SHORT_STANCE_LABELS.get(top_stance, top_stance)} {stance_pct}%",
        f"{top_stance_count:,}件。{STANCE_NOTES.get(top_stance, '')}",
        stance_pct,
    )
    page = set_insight(
        page,
        "最も話された論点",
        f"{SHORT_ISSUE_LABELS.get(top_issue, top_issue)} {top_issue_count:,}<small>件</small>",
        "学習データを許諾なしで使えるかが最大争点",
        issue_pct,
    )

    marker = re.search(r"(<!-- THEME_ATLAS_START -->)(.*?)(<!-- THEME_ATLAS_END -->)", page, re.S)
    if not marker:
        raise BuildError("論点アトラスの位置（THEME_ATLAS_START / END）を特定できません")
    page = page[: marker.start(2)] + "\n" + build_theme_atlas(issue_counts) + "\n  " + page[marker.end(2) :]

    marker = re.search(
        r'(<summary>分類別件数</summary>\s*<div class="details-body">\s*<div class="bar-list">)(.*?)(</div>\s*</div>\s*</details>)',
        page,
        re.S,
    )
    if not marker:
        raise BuildError("詳細データ『分類別件数』の位置を特定できません")
    page = page[: marker.start(2)] + "\n" + build_issue_bars(issue_counts, opinion_total) + "\n" + page[marker.end(2) :]

    marker = re.search(
        r'(<summary>カテゴリ × スタンス</summary>\s*<div class="details-body">\s*<div class="bar-list">)(.*?)(</div>\s*</div>\s*</details>)',
        page,
        re.S,
    )
    if marker:
        page = page[: marker.start(2)] + "\n" + build_stance_bars(stance_counts) + "\n" + page[marker.end(2) :]

    # 潮目は一時ファイル経由で当てて、結果を文字列に戻す（--check でも比較できるように）
    import tempfile as _tempfile

    with _tempfile.TemporaryDirectory() as directory:
        scratch = Path(directory) / "page.html"
        scratch.write_text(page, encoding="utf-8")
        apply_tide(scratch, records)
        page = scratch.read_text(encoding="utf-8")

    changed_page = page != before
    changed_arena = arena_text != arena_before
    if not check:
        if changed_page or output is not None:
            target = Path(output) if output else html_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(page, encoding="utf-8")
        if changed_arena or data_output is not None:
            arena_path.parent.mkdir(parents=True, exist_ok=True)
            arena_path.write_text(arena_text, encoding="utf-8")

    detail = " / ".join(f"{n}={c}" for n, c in issue_counts.most_common())
    lines = [
        f"出所: {label}（全{total}件 / 意見{opinion_total}件）",
        f"論点: {detail}",
        f"立場: " + " / ".join(f"{n}={stance_counts.get(n, 0)}" for n in STANCE_ORDER),
        f"アリーナの点: {len(arena_rows)}件",
    ]
    return lines, (changed_page or changed_arena)


def main() -> int:
    parser = argparse.ArgumentParser(description="生成AIと著作権ページを正典から生成する")
    parser.add_argument("--check", action="store_true", help="書き換えず、差分があれば exit 1")
    parser.add_argument("--input", type=Path, help="正典の代わりに読む累積候補（staging用）")
    parser.add_argument("--html-template", type=Path, help="読み込むHTML（既定は公開ページ）")
    parser.add_argument("--output-html", type=Path, help="書き出し先（既定は読み込んだHTML）")
    parser.add_argument("--output-data", type=Path, help="アリーナデータの書き出し先")
    parser.add_argument("--skip-issue-counts", action="store_true", help="sync_issue_counts.py を呼ばない")
    args = parser.parse_args()
    try:
        lines, changed = build(
            check=args.check,
            source=args.input,
            template=args.html_template,
            output=args.output_html,
            data_output=args.output_data,
        )
    except (BuildError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("\n".join(lines))
    print("UPDATE" if changed else "OK    ")
    if args.check and changed:
        print("NG  ページが正典から生成した内容と一致しません", file=sys.stderr)
        return 1
    if not args.check and not args.skip_issue_counts and args.output_html is None:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "sync_issue_counts.py"), THEME], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
