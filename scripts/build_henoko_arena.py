#!/usr/bin/env python3
"""辺野古高校生死亡事故ページを、正典の「意見」投稿だけから作り直す。

生成対象は、ページ内でアリーナの点と件数・割合を出しているすべての場所
（リード文・調査条件・注目ポイント4枚・論点ブロックの内訳文と賛否の件数・
詳細データ表・アリーナの点）と docs/henoko-arena-data.js。

    python3 scripts/build_henoko_arena.py
    python3 scripts/build_henoko_arena.py --check
    python3 scripts/build_henoko_arena.py --input <候補> --html-template <現行> \
        --output-html <候補HTML> --output-data <候補JS>

前身は scripts/build_henoko_arena.mjs。あれは正典と公開ページを直接読み書きし、
アリーナの点と詳細データ表しか作り直さなかったため、①更新回の候補ページを
組み立てられない（`--promote` に載せられない）②件数を手書きしている残りの場所が
更新のたびに古い数字のまま残る、の2点で自動更新できなかった。

論点ごとの見出し・ナビ・アリーナのセクター件数は scripts/sync_issue_counts.py の
担当なので、ここでは書かない（configs/henoko-student-accident-reaction-map.json の
issue_counts.sync）。同じ場所を2つのスクリプトが書かないこと。
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .issue_card_counts import IssueCountError
    from .sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml
    from .verify_sample_periods import expected_period, summarize
    from .x_embed import period_label
except ImportError:  # python3 scripts/build_henoko_arena.py
    from issue_card_counts import IssueCountError  # type: ignore[no-redef]
    from sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml  # type: ignore[no-redef]
    from verify_sample_periods import expected_period, summarize  # type: ignore[no-redef]
    from x_embed import period_label  # type: ignore[no-redef]

THEME = "henoko-student-accident"
PAGE = Path("docs/henoko-student-accident-reaction-map.html")
ARENA_DATA = Path("docs/henoko-arena-data.js")

# 正典の立場ラベル。ページ側は「評価／疑問／切り分け」の3方向で色分けする。
SUPPORT = "文科省判断を支持"
OPPOSE = "文科省判断に反発"
SPLIT = "論点を切り分ける"
NEUTRAL = "中立・情報共有"
STANCE_VALUE = {SUPPORT: 1, OPPOSE: -1}
INTENSITY_SCALE = {"low": 0.28, "medium": 0.62, "high": 0.94}

# アリーナのセクター順。**入れ替えないこと**（投票は論点の番号で保存されている）。
ISSUE_DEFS: tuple[dict[str, Any], ...] = (
    {
        "main_issue": "政治的中立性",
        "table_label": "政治的中立性",
        "short": "政治的中立性",
        "icon": "⚖️",
        "insight_note": "修学旅行中の活動が教育の範囲を越えたかを問う",
    },
    {
        "main_issue": "安全管理・事故原因",
        "table_label": "安全管理・事故原因",
        "short": "安全管理",
        "icon": "🔥",
        "insight_note": "乗船判断、引率責任、事故原因と再発防止",
    },
    {
        "main_issue": "追悼・被害者の尊厳",
        "table_label": "追悼と被害者の尊厳",
        "short": "追悼・尊厳",
        "icon": "🕊️",
        "insight_note": "政治論争より先に悼むべきだという声",
    },
    {
        "main_issue": "平和教育の萎縮",
        "table_label": "平和教育の萎縮",
        "short": "平和教育",
        "icon": "📚",
        "insight_note": "違反認定が沖縄平和学習を萎縮させるかを問う",
    },
    {
        "main_issue": "政治利用・基地問題",
        "table_label": "政治利用・基地問題",
        "short": "政治利用",
        "icon": "📣",
        "insight_note": "教育か運動への動員かをめぐる責任の追及",
    },
    {
        "main_issue": "報道・行政対応",
        "table_label": "報道・行政の伝え方",
        "short": "報道・行政",
        "icon": "📰",
        "insight_note": "事故と教育問題を結びつけた報道への評価",
    },
)
ISSUE_INDEX = {issue["main_issue"]: index for index, issue in enumerate(ISSUE_DEFS)}
STANCE_TABLE_LABELS = ((1, "文科省判断を評価"), (0, "判断を保留・切り分ける"), (-1, "文科省判断に疑問"))
INTENSITY_TABLE_LABELS = ((0.94, "high（強い）"), (0.62, "medium（中）"), (0.28, "low（弱い）"))


def percent(part: int, whole: int) -> int:
    """四捨五入した百分率。Python の round は 0.5 を偶数へ丸めるため使わない。"""
    if whole <= 0:
        raise IssueCountError("母数が0の割合を求めようとしました")
    return int(part / whole * 100 + 0.5)


def classification(record: dict[str, Any]) -> dict[str, Any]:
    nested = record.get("classification")
    if not isinstance(nested, dict):
        raise IssueCountError("classification を持たないレコードがあります")
    return nested


def load_records(input_path: Path | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """正典（または候補）を読み、全レコードと意見投稿を返す。"""
    themes = parse_themes_yaml(THEMES_YAML)
    sample_file = str(themes[THEME].get("sample_file") or "")
    if not sample_file or "synthetic" in sample_file:
        raise IssueCountError(f"{THEME}: 正典 sample_file が不正です: {sample_file}")
    source = input_path or ROOT / sample_file
    records = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise IssueCountError(f"{THEME}: 正典が空、またはJSON配列ではありません")

    opinions: list[dict[str, Any]] = []
    for number, record in enumerate(records, start=1):
        value = classification(record)
        if not isinstance(value.get("is_opinion"), bool):
            raise IssueCountError(f"{number}件目の classification.is_opinion がboolではありません")
        if value["is_opinion"] and value.get("main_issue") in ISSUE_INDEX:
            opinions.append(record)
    if not opinions:
        raise IssueCountError("意見と判定されたレコードがありません")
    return records, opinions


def stance_value(record: dict[str, Any]) -> int:
    return STANCE_VALUE.get(str(classification(record).get("stance") or ""), 0)


def intensity(record: dict[str, Any]) -> float:
    return INTENSITY_SCALE.get(str(classification(record).get("intensity") or ""), 0.45)


def arena_rows(opinions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "i": ISSUE_INDEX[str(classification(row)["main_issue"])],
            "e": intensity(row),
            "x": stance_value(row),
            "s": str(classification(row).get("summary") or "投稿の要旨"),
            "u": str(row.get("url") or ""),
        }
        for row in opinions
    ]


def stance_counts(opinions: list[dict[str, Any]], main_issue: str) -> Counter[str]:
    return Counter(
        str(classification(row).get("stance") or "")
        for row in opinions
        if classification(row)["main_issue"] == main_issue
    )


class IssueStats:
    """論点ひとつぶんの件数。ページの文言はすべてここから作る。"""

    def __init__(self, opinions: list[dict[str, Any]], issue: dict[str, Any]):
        counts = stance_counts(opinions, str(issue["main_issue"]))
        self.issue = issue
        self.total = sum(counts.values())
        self.support = counts[SUPPORT]
        self.oppose = counts[OPPOSE]
        self.split = counts[SPLIT]
        self.neutral = counts[NEUTRAL]

    @property
    def split_and_neutral(self) -> int:
        return self.split + self.neutral

    def share(self, part: int) -> int:
        return percent(part, self.total)


# ---------------------------------------------------------------- 生成

def arena_data_js(rows: list[dict[str, Any]]) -> str:
    body = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    return "/* Generated by scripts/build_henoko_arena.py. */\nconst HENOKO_ARENA_RAW=" + body + ";\n"


def inline_arena_data(rows: list[dict[str, Any]]) -> str:
    body = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    return (
        "/* HENOKO_ARENA_DATA_START */\nconst HENOKO_ARENA_RAW="
        + body
        + ";\n/* HENOKO_ARENA_DATA_END */"
    )


def total_row(label: str, values: list[int]) -> str:
    bold = ' style="font-weight:900"'
    cells = "".join(f"<td{bold}>{value}</td>" for value in values)
    return f"<tr><th{bold}>{label}</th>{cells}</tr>"


def detail_tables(rows: list[dict[str, Any]]) -> str:
    """詳細データの表。マップが読むのと同じ点から作る（別集計にしない）。"""
    total = len(rows)
    by_issue = Counter(row["i"] for row in rows)
    by_stance = Counter(row["x"] for row in rows)
    by_intensity = Counter(row["e"] for row in rows)
    by_cross = Counter((row["i"], row["x"]) for row in rows)

    issue_rows = "".join(
        f'<tr><th>{html.escape(str(issue["table_label"]))}</th><td>{by_issue.get(index, 0)}</td></tr>'
        for index, issue in enumerate(ISSUE_DEFS)
    ) + total_row("合計（意見投稿）", [total])
    stance_rows = "".join(
        f"<tr><th>{label}</th><td>{by_stance.get(key, 0)}</td></tr>"
        for key, label in STANCE_TABLE_LABELS
    ) + total_row("合計（意見投稿）", [total])
    cross_rows = (
        "<thead><tr><th>論点</th><th>評価</th><th>保留</th><th>疑問</th><th>計</th></tr></thead><tbody>"
        + "".join(
            "<tr><th>{label}</th>{cells}<td>{sum}</td></tr>".format(
                label=html.escape(str(issue["table_label"])),
                cells="".join(
                    f"<td>{by_cross.get((index, key), 0)}</td>" for key in (1, 0, -1)
                ),
                sum=sum(by_cross.get((index, key), 0) for key in (1, 0, -1)),
            )
            for index, issue in enumerate(ISSUE_DEFS)
        )
        + total_row(
            "合計",
            [by_stance.get(1, 0), by_stance.get(0, 0), by_stance.get(-1, 0), total],
        )
        + "</tbody>"
    )
    intensity_rows = "".join(
        f"<tr><th>{label}</th><td>{by_intensity[key]}</td></tr>"
        for key, label in INTENSITY_TABLE_LABELS
        if key in by_intensity
    ) + total_row("合計（意見投稿）", [total])

    def wrap(summary: str, inner: str, open_: bool = False) -> str:
        return (
            f'<details{" open" if open_ else ""}><summary>{summary}</summary>'
            f'<div class="table-wrap"><table>{inner}</table></div></details>'
        )

    return (
        "<!-- DETAIL_TABLES_START -->"
        + wrap("論点別件数", f"<tbody>{issue_rows}</tbody>", True)
        + wrap("立場別件数", f"<tbody>{stance_rows}</tbody>")
        + wrap("論点×立場のクロス集計", cross_rows)
        + wrap("感情の強さ（intensity）", f"<tbody>{intensity_rows}</tbody>")
        + "<!-- DETAIL_TABLES_END -->"
    )


def research_conditions(records: list[dict[str, Any]], opinions: list[dict[str, Any]]) -> str:
    """調査条件（取得元・件数・期間）。

    確認表示は <span class="review-note"> で囲む（verify_number_provenance.py が
    この囲みだけを検査から外す）。落とすと再生成で検査が落ちる。
    取得期間は台帳ではなく正典から数える。昇格処理は adapter のあとに
    THEMES.yaml を書き換えるため、台帳から読むと1回分古くなる。
    """
    period = period_label(expected_period(summarize(records)))
    return (
        "<!-- RESEARCH_CONDITIONS_START -->\n"
        '<aside class="research-conditions" aria-label="SNSデータの調査条件"'
        ' style="padding:16px min(6vw,72px);background:#fff;border-bottom:1px solid var(--line);'
        'font-size:13px;line-height:1.8;color:var(--muted);">\n'
        '  <p style="max-width:1000px;margin:0 auto;">'
        '<strong style="color:var(--ink);">このマップの元データ:</strong> '
        f"Yahooリアルタイム検索で取得した公開投稿 {len(records)}件のうち、"
        f"意見と判定した{len(opinions)}件<br>\n"
        f"  （取得期間: {period}／"
        '<span class="review-note">AI分類。代表投稿は編集部が選定</span>）<br>\n'
        "  <strong>社会全体の世論調査ではありません。</strong></p>\n"
        "</aside>\n"
        "<!-- RESEARCH_CONDITIONS_END -->"
    )


def insight_stats(opinions: list[dict[str, Any]], stats: dict[str, IssueStats]) -> str:
    """注目ポイント4枚。文言の骨は固定で、論点の選び方と数字だけ正典から作る。

    「最も話された論点」は件数が最多の論点。「最も意見が割れた論点」は、
    賛否をはっきり示した投稿（評価＋疑問）の比率が最も高い論点とする。
    どちらも同数のときは ISSUE_DEFS の並び順で先に来るほうを採る。
    """
    total = len(opinions)
    split_total = sum(1 for row in opinions if stance_value(row) == 0)
    top_issue = min(ISSUE_DEFS, key=lambda issue: (-stats[issue["main_issue"]].total, ISSUE_INDEX[issue["main_issue"]]))
    divided = min(
        ISSUE_DEFS,
        key=lambda issue: (
            -stats[issue["main_issue"]].share(
                stats[issue["main_issue"]].support + stats[issue["main_issue"]].oppose
            ),
            ISSUE_INDEX[issue["main_issue"]],
        ),
    )
    top = stats[str(top_issue["main_issue"])]
    split_issue = stats[str(divided["main_issue"])]
    clear = split_issue.support + split_issue.oppose
    return "\n".join(
        [
            "<!-- INSIGHT_STATS_START -->",
            '<section class="stats insight-stats" aria-label="このテーマの4つの注目ポイント">',
            '  <article class="stat insight-stat">',
            '    <div class="insight-head"><span class="insight-icon" aria-hidden="true">🗣️</span>'
            '<span class="insight-label">分析対象の意見</span></div>',
            f'    <strong class="insight-value">{total}<small>件</small></strong>',
            '    <p class="insight-note">事故、教育、政治、追悼を切り分けて比較</p>',
            '    <div class="insight-meter" aria-hidden="true"><i style="width:100%"></i></div>',
            "  </article>",
            '  <article class="stat insight-stat" data-tone="topic">',
            f'    <div class="insight-head"><span class="insight-icon" aria-hidden="true">{top_issue["icon"]}</span>'
            '<span class="insight-label">最も話された論点</span></div>',
            f'    <strong class="insight-value">{html.escape(str(top_issue["short"]))} {top.total}<small>件</small></strong>',
            f'    <p class="insight-note">{html.escape(str(top_issue["insight_note"]))}</p>',
            f'    <div class="insight-meter" aria-hidden="true"><i style="width:{percent(top.total, total)}%"></i></div>',
            "  </article>",
            '  <article class="stat insight-stat" data-tone="option">',
            '    <div class="insight-head"><span class="insight-icon" aria-hidden="true">✂️</span>'
            '<span class="insight-label">単純な賛否ではない声</span></div>',
            f'    <strong class="insight-value">論点を切り分け {split_total}<small>件</small></strong>',
            '    <p class="insight-note">事故検証と教育・政治評価を分ける声が最多</p>',
            f'    <div class="insight-meter" aria-hidden="true"><i style="width:{percent(split_total, total)}%"></i></div>',
            "  </article>",
            '  <article class="stat insight-stat" data-tone="debate">',
            '    <div class="insight-head"><span class="insight-icon" aria-hidden="true">⚔️</span>'
            '<span class="insight-label">最も意見が割れた論点</span></div>',
            f'    <span class="insight-chip">{html.escape(str(divided["short"]))}</span>',
            '    <div class="insight-versus"><span>認定を評価<b>'
            f'{split_issue.share(split_issue.support)}%</b></span><em>VS</em><span>認定に疑問<b>'
            f'{split_issue.share(split_issue.oppose)}%</b></span></div>',
            '    <div class="insight-split" aria-hidden="true">'
            f'<i style="width:{percent(split_issue.support, clear)}%"></i>'
            f'<i style="width:{percent(split_issue.oppose, clear)}%"></i></div>',
            "  </article>",
            "</section>",
            "<!-- INSIGHT_STATS_END -->",
        ]
    )


# ---------------------------------------------------------------- 差し替え

def replace_block(page: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, lambda _: replacement, page, flags=re.DOTALL)
    if count != 1:
        raise IssueCountError(f"{label}の差し替え位置が{count}か所見つかりました（1か所であるべき）")
    return updated


def replace_number(page: str, pattern: str, values: list[int], label: str) -> str:
    """本文中の件数・割合を、正典から数えた値へ入れ替える。

    文そのものはページに置いたままにして、数字だけを書き換える。
    パターンが1か所で当たらなければ落とす（文を書き換えたのに数字だけ
    古いまま残る事故を防ぐ）。
    """
    matches = list(re.finditer(pattern, page))
    if len(matches) != 1:
        raise IssueCountError(f"{label}が{len(matches)}か所見つかりました（1か所であるべき）")
    if len(matches[0].groups()) != len(values):
        raise IssueCountError(f"{label}の数字の数が合いません")
    return re.sub(pattern, lambda found: _substitute(found, values), page, count=1)


def _substitute(found: re.Match[str], values: list[int]) -> str:
    text = found.group(0)
    pieces: list[str] = []
    cursor = found.start()
    for index, value in enumerate(values, start=1):
        start, end = found.span(index)
        pieces.append(text[cursor - found.start() : start - found.start()])
        pieces.append(str(value))
        cursor = end
    pieces.append(text[cursor - found.start() :])
    return "".join(pieces)


def issue_rewrites(stats: dict[str, IssueStats]) -> list[tuple[str, list[int], str]]:
    """論点ブロックの内訳文と賛否の件数。文はページ、数字はここが書く。"""
    churitsu = stats["政治的中立性"]
    anzen = stats["安全管理・事故原因"]
    tsuito = stats["追悼・被害者の尊厳"]
    heiwa = stats["平和教育の萎縮"]
    seiji = stats["政治利用・基地問題"]
    hodo = stats["報道・行政対応"]
    return [
        (
            r"文科省の教育基本法違反認定を評価する声が(\d+)%で最多",
            [churitsu.share(churitsu.support)],
            "政治的中立性の内訳文（評価）",
        ),
        (r"疑問視する声は(\d+)%。", [churitsu.share(churitsu.oppose)], "政治的中立性の内訳文（疑問）"),
        (
            r"<strong>認定を評価（(\d+)件）</strong>",
            [churitsu.support],
            "政治的中立性の賛成側件数",
        ),
        (r"<strong>認定に疑問（(\d+)件）</strong>", [churitsu.oppose], "政治的中立性の反対側件数"),
        (
            r"意見(\d+)件のうち(\d+)件が「切り分け」スタンス",
            [anzen.total, anzen.split],
            "安全管理の内訳文",
        ),
        (
            r"<strong>事故責任の切り分けを主張（(\d+)件）</strong>",
            [anzen.split],
            "安全管理の切り分け件数",
        ),
        (r"(\d+)%が切り分けスタンスで", [tsuito.share(tsuito.split)], "追悼の内訳文"),
        (r"<strong>追悼を優先（(\d+)件）</strong>", [tsuito.split], "追悼の切り分け件数"),
        (
            r"認定に疑問を示す声が(\d+)%、認定を評価する声が(\d+)%",
            [heiwa.share(heiwa.oppose), heiwa.share(heiwa.support)],
            "平和教育の内訳文",
        ),
        (
            r"<strong>認定を評価・萎縮は当然（(\d+)件）</strong>",
            [heiwa.support],
            "平和教育の賛成側件数",
        ),
        (r"<strong>萎縮を懸念（(\d+)件）</strong>", [heiwa.oppose], "平和教育の反対側件数"),
        (
            r"(\d+)%が「切り分け・中立」で、文科省判断",
            [seiji.share(seiji.split_and_neutral)],
            "政治利用の内訳文",
        ),
        (
            r"<strong>事実整理・責任追及（(\d+)件）</strong>",
            [seiji.split_and_neutral],
            "政治利用の切り分け件数",
        ),
        (
            r"(\d+)%が「切り分け・中立」で事実確認",
            [hodo.share(hodo.split_and_neutral)],
            "報道・行政の内訳文",
        ),
        (r"<strong>対応を評価（(\d+)件）</strong>", [hodo.support], "報道・行政の賛成側件数"),
        (r"<strong>報道・行政に疑問（(\d+)件）</strong>", [hodo.oppose], "報道・行政の反対側件数"),
    ]


def build_page(
    page: str,
    records: list[dict[str, Any]],
    opinions: list[dict[str, Any]],
) -> str:
    rows = arena_rows(opinions)
    stats = {str(issue["main_issue"]): IssueStats(opinions, issue) for issue in ISSUE_DEFS}
    total = len(opinions)

    page = replace_block(
        page,
        r"/\* HENOKO_ARENA_DATA_START \*/.*?/\* HENOKO_ARENA_DATA_END \*/",
        inline_arena_data(rows),
        "アリーナの点",
    )
    page = replace_block(
        page,
        r"<!-- DETAIL_TABLES_START -->.*?<!-- DETAIL_TABLES_END -->",
        detail_tables(rows),
        "詳細データ表",
    )
    page = replace_block(
        page,
        r"<!-- RESEARCH_CONDITIONS_START -->.*?<!-- RESEARCH_CONDITIONS_END -->",
        research_conditions(records, opinions),
        "調査条件",
    )
    page = replace_block(
        page,
        r"<!-- INSIGHT_STATS_START -->.*?<!-- INSIGHT_STATS_END -->",
        insight_stats(opinions, stats),
        "注目ポイント",
    )
    page = replace_number(
        page,
        r"公開投稿(\d+)件のうち、意見と判定した(\d+)件をAIが",
        [len(records), total],
        "リード文",
    )
    page = replace_number(
        page, r"<span>(\d+)件 \| Hermes再分類", [total], "SNS反応マップの見出し"
    )
    page = replace_number(page, r"<span>(\d+)件 Hermes再分類</span>", [total], "論点別Xの声の見出し")
    for pattern, values, label in issue_rewrites(stats):
        page = replace_number(page, pattern, values, label)
    return page


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="正典または累積候補のJSON")
    parser.add_argument("--html-template", type=Path, help="組み立ての土台にするHTML")
    parser.add_argument("--output-html", type=Path, help="書き出し先HTML")
    parser.add_argument("--output-data", type=Path, help="書き出し先のアリーナJS")
    parser.add_argument("--check", action="store_true", help="書き換えずに差分の有無だけ返す")
    args = parser.parse_args()

    template = args.html_template or ROOT / PAGE
    output_html = args.output_html or ROOT / PAGE
    output_data = args.output_data or ROOT / ARENA_DATA

    records, opinions = load_records(args.input)
    page = template.read_text(encoding="utf-8")
    updated = build_page(page, records, opinions)
    data = arena_data_js(arena_rows(opinions))

    current_data = output_data.read_text(encoding="utf-8") if output_data.exists() else ""
    current_html = output_html.read_text(encoding="utf-8") if output_html.exists() else ""
    changed = updated != current_html or data != current_data
    if not args.check:
        output_html.parent.mkdir(parents=True, exist_ok=True)
        output_data.parent.mkdir(parents=True, exist_ok=True)
        output_html.write_text(updated, encoding="utf-8")
        output_data.write_text(data, encoding="utf-8")
    state = ("would update" if changed else "unchanged") if args.check else "wrote"
    print(f"{state} {len(opinions)} arena points to {output_data}")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
