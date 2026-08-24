#!/usr/bin/env python3
"""皇室典範改正ページの論点表示を、正典の分類結果から一括生成する。

このページは長らく2つのデータセットが混在していた。

- アリーナ（SM_RAW）と論点カードは 2026-07-17 収集分（268件）
- THEMES.yaml の sample_file は 2026-07-26 収集分（347件）

両者はURLが1件も重ならないため、カードの件数と正典の件数が無関係になっていた。
このスクリプトは **sample_file だけ** を読み、ページの論点まわりを丸ごと作り直す。

数えるのは **意見と判定された投稿だけ**（2026-08-08）。それ以前はマップの点だけが全件で、
論点カード・賛否は意見のみという混在状態だった。収集総数は調査条件と「意見と情報共有」
カードにだけ出し、そこでは必ず意見件数と並べて書く。

生成する箇所:

- SM_RAW（アリーナの点）
- ISSUES（アリーナのセクター）
- VOTE_ISSUES（投票の論点選択肢）
- アリーナの見出し件数・フィルタボタン
- ヒーローの lead / 議論の中心 / insight カードの件数
- 調査条件（件数・取得期間）と詳細データの「収集クエリ」
- 「争点別のXの声」セクション全体（件数・熱量・温度バー・代表投稿）

論点の並びは件数の降順、「その他」は必ず末尾。件数はここでしか作らない。

    python3 scripts/build_koshitsu_arena.py
    python3 scripts/build_koshitsu_arena.py --check   # 書き換えず差分の有無だけ見る
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

import yaml

try:
    from .x_embed import embed_html, period_label
except ImportError:  # python3 scripts/build_koshitsu_arena.py
    from x_embed import embed_html, period_label  # type: ignore[no-redef]

try:
    from .issue_card_counts import IssueCountError, span_html
    from .sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml
    from .verify_sample_periods import expected_period, summarize
except ImportError:  # python3 scripts/build_koshitsu_arena.py
    from issue_card_counts import IssueCountError, span_html  # type: ignore[no-redef]
    from sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml  # type: ignore[no-redef]
    from verify_sample_periods import expected_period, summarize  # type: ignore[no-redef]

THEME = "koshitsu-tenpakai"
OTHER = "その他"

# stance → アリーナのx値（改正への賛否軸）
STANCE_X = {
    "改正賛成（女系容認）": 2.0,
    "改正反対（男系維持）": -2.0,
    "中立・情報": 0.0,
}
# intensity → 中心からの距離（外周ほど感情的）
INTENSITY_E = {"low": 0.6, "medium": 1.3, "high": 2.0}
# 熱量の平均を出すための重み
INTENSITY_HEAT = {"low": 0.0, "medium": 1.0, "high": 2.0}

NEG = "改正反対（男系維持）"
POS = "改正賛成（女系容認）"
NEU = "中立・情報"


def js_str(text: str) -> str:
    """シングルクォートのJS文字列リテラルの中身に落とす。"""
    return text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")


def classification(record: dict[str, Any]) -> dict[str, Any]:
    nested = record.get("classification")
    return nested if isinstance(nested, dict) else record


def select_opinions(records: Any, sample_file: str) -> list[dict[str, Any]]:
    """意見と判定されたレコードだけを返す。

    ニュースのURL共有など意見でない投稿を落とすのは、ページ内の分母を1種類に保つため。
    判定が入っていないレコードは**除外せずエラーで止める**。静かに落とすと、あとで
    件数が合わない原因を追えなくなる。
    """
    if not isinstance(records, list) or not records:
        raise IssueCountError(f"{THEME}: 分類結果がJSON配列ではありません: {sample_file}")
    with_issue = [r for r in records if isinstance(r, dict) and classification(r).get("main_issue")]
    if len(with_issue) != len(records):
        raise IssueCountError(
            f"{THEME}: main_issue を持たないレコードがあります（{len(records) - len(with_issue)}件）"
        )
    unjudged = [r for r in records if "is_opinion" not in classification(r)]
    if unjudged:
        raise IssueCountError(
            f"{THEME}: is_opinion を持たないレコードがあります（{len(unjudged)}件）: {sample_file}"
        )
    rows = [r for r in records if classification(r)["is_opinion"] is True]
    if not rows:
        raise IssueCountError(f"{THEME}: 意見と判定されたレコードが0件です: {sample_file}")
    return rows


def load_canon(source: Path | None = None) -> tuple[list[dict[str, Any]], str, int]:
    """THEMES.yaml の sample_file を唯一の出所として読む。

    staging から呼ぶときだけ source に累積候補を渡す（公開前の候補ページ生成用）。
    返すのは意見と判定されたレコードだけ。3つめは絞り込む前の収集総数。
    """
    if source is not None:
        sample_file = str(source)
        records = json.loads(Path(source).read_text(encoding="utf-8"))
    else:
        themes = parse_themes_yaml(THEMES_YAML)
        if THEME not in themes:
            raise IssueCountError(f"THEMES.yaml にテーマがありません: {THEME}")
        sample_file = str(themes[THEME].get("sample_file") or "")
        if not sample_file:
            raise IssueCountError(f"{THEME}: sample_file が未設定です")
        if "synthetic" in sample_file:
            raise IssueCountError(f"{THEME}: 合成データを正典にはできません: {sample_file}")
        records = json.loads((ROOT / sample_file).read_text(encoding="utf-8"))
    rows = select_opinions(records, sample_file)
    return rows, sample_file, len(records), sample_period(records)


def sample_period(records: list[dict[str, Any]]) -> str:
    """調査条件に出す収集日の範囲。

    THEMES.yaml の `sample_period` と同じ計算を使う。verify_theme_page.py は
    台帳の値とページの表記を突き合わせるので、別々に数えると必ずいつかズレる。
    収集回が増えるたびに変わる値なので、ページ側に固定で書かない。
    """
    period = expected_period(summarize(records))
    return period_label(period)


def load_queries() -> list[str]:
    """収集に実際に使った検索語。refresh_topic.py が読むのと同じファイルから出す。"""
    themes = parse_themes_yaml(THEMES_YAML)
    path = ROOT / str(themes[THEME].get("refresh_config") or "")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [str(query) for query in (value.get("fetch_queries") or [])]


def issue_order(rows: list[dict[str, Any]]) -> list[str]:
    """件数の降順。「その他」は必ず末尾。"""
    counts = Counter(classification(r)["main_issue"] for r in rows)
    ordered = [name for name, _ in counts.most_common() if name != OTHER]
    if counts.get(OTHER):
        ordered.append(OTHER)
    return ordered


def build_sm_raw(rows: list[dict[str, Any]], order: list[str]) -> str:
    index = {name: i for i, name in enumerate(order)}
    lines = []
    for row in rows:
        c = classification(row)
        stance = c["stance"]
        if stance not in STANCE_X:
            raise IssueCountError(f"未知の stance: {stance}")
        lines.append(
            "{{x:{x},e:{e},c:{c},i:{i},s:'{s}',u:'{u}'}}".format(
                x=STANCE_X[stance],
                e=INTENSITY_E.get(c["intensity"], 1.0),
                c=round(float(c.get("confidence", 0.7)), 2),
                i=index[c["main_issue"]],
                s=js_str(str(c.get("summary") or "")[:60]),
                u=js_str(str(row.get("url") or "")),
            )
        )
    return "const SM_RAW = [\n" + ",\n".join(lines) + "\n];"


def build_issues(order: list[str], labels: dict[str, str]) -> str:
    """セクターの件数は n:0 から SM_RAW を数え上げる（数える場所を1箇所に保つ）。"""
    body = ",\n    ".join(f"{{k:'{js_str(labels.get(n, n))}',n:0}}" for n in order)
    return "const ISSUES=[\n    " + body + "\n  ];"


def build_vote_issues(order: list[str], labels: dict[str, str], icons: dict[str, str]) -> str:
    body = ",\n    ".join(
        f"{{k:'{js_str(labels.get(n, n))}',icon:'{icons.get(n, '🤔')}'}}" for n in order
    )
    return "var VOTE_ISSUES=[\n    " + body + "\n  ];"


def stance_stats(rows: list[dict[str, Any]], issue: str) -> dict[str, Any]:
    subset = [r for r in rows if classification(r)["main_issue"] == issue]
    counts = Counter(classification(r)["stance"] for r in subset)
    total = len(subset)
    heat = (
        sum(INTENSITY_HEAT[classification(r)["intensity"]] for r in subset) / total
        if total
        else 0.0
    )
    return {
        "total": total,
        "neg": counts.get(NEG, 0),
        "neu": counts.get(NEU, 0),
        "pos": counts.get(POS, 0),
        "heat": round(heat, 2),
    }


def percent_split(stats: dict[str, Any]) -> tuple[int, int, int]:
    """温度バーの3区画。合計が必ず100になるよう最大区画で吸収する。"""
    total = stats["total"] or 1
    neg = round(stats["neg"] / total * 100)
    pos = round(stats["pos"] / total * 100)
    neu = 100 - neg - pos
    if neu < 0:  # 丸め誤差は最大の区画から引く
        if neg >= pos:
            neg += neu
        else:
            pos += neu
        neu = 0
    return neg, neu, pos


def seg(kind: str, value: int) -> str:
    """幅5%未満は数字を出すと潰れるので空にする。"""
    label = f"{value}%" if value >= 5 else ""
    return f'<div class="temp-seg {kind}" style="width:{value}%">{label}</div>'


def build_issue_section(rows: list[dict[str, Any]], blocks: list[dict[str, Any]]) -> str:
    nav = []
    articles = []
    for number, block in enumerate(blocks, start=1):
        issue = str(block["main_issue"])
        stats = stance_stats(rows, issue)
        if not stats["total"]:
            raise IssueCountError(f"{issue}: 正典に1件もありません")
        neg, neu, pos = percent_split(stats)
        anchor = f"issue-{block['slug']}"
        short = html.escape(str(block["nav_label"]))
        nav.append(f'<a href="#{anchor}">争点{number} {short} {stats["total"]}件</a>')

        samples = "\n".join(
            '<div class="sample-card"><div class="meta">{meta}</div><p>{note}</p>'
            "{embed}</div>".format(
                meta=html.escape(str(s["meta"])),
                note=html.escape(str(s["note"])),
                embed=embed_html(s["url"]),
            )
            for s in block["samples"]
        )

        articles.append(
            f'<article class="issue-block" id="{anchor}">\n'
            f'<div class="issue-head"><span class="axis-kicker">争点{number} · '
            f'{html.escape(str(block["kicker"]))}</span>'
            f'<h3>{html.escape(str(block["heading"]))}'
            f'<span class="issue-count">{stats["total"]}件</span>'
            f'<span class="issue-heat">熱量 {stats["heat"]:.2f}</span></h3>\n'
            f'<div class="temp-bar-wrap"><div class="temp-bar-label">'
            f'<span>{html.escape(str(block["bar_label"]))}</span>'
            f'<span>反対{stats["neg"]} / 中立{stats["neu"]} / 賛成{stats["pos"]}</span></div>'
            f'<div class="temp-bar">{seg("neg", neg)}{seg("neu", neu)}{seg("pos", pos)}</div>'
            f'<div class="temp-bar-legend">'
            f'<span><i style="background:#dc2626"></i>改正反対（男系維持）</span>'
            f'<span><i style="background:#94a3b8"></i>中立・情報</span>'
            f'<span><i style="background:#059669"></i>改正賛成（女系容認）</span></div></div>\n'
            f'<p class="issue-desc">{html.escape(str(block["desc"]))}</p>\n'
            f'<div class="issue-sides">'
            f'<div class="side neg"><strong>改正反対（男系維持） {stats["neg"]}件</strong>'
            f'{html.escape(str(block["side_neg"]))}</div>'
            f'<div class="side pos"><strong>改正賛成（女系容認） {stats["pos"]}件</strong>'
            f'{html.escape(str(block["side_pos"]))}</div></div>\n'
            f"</div>\n"
            f'<div class="sample-grid">\n{samples}\n</div>\n'
            f"</article>"
        )

    return (
        '<nav class="quadrant-nav">' + "".join(nav) + "</nav>\n\n" + "\n\n".join(articles)
    )


def build_insight_stats(
    rows: list[dict[str, Any]], order: list[str], labels: dict[str, str], collected: int
) -> str:
    """ヒーロー直下の注目ポイント4枚。旧2D分類の「皇位継承観」は正典に無いので作らない。

    rows は意見のみなので、収集総数（collected）は必ず意見件数と並べて出す。
    """
    total = len(rows)
    counts = Counter(classification(r)["main_issue"] for r in rows)
    stances = Counter(classification(r)["stance"] for r in rows)
    top = order[0]
    neg, pos = stances[NEG], stances[POS]
    neg_pct = round(neg / (neg + pos) * 100) if neg + pos else 0
    op_pct = round(total / collected * 100)

    return "\n".join(
        [
            '  <article class="stat insight-stat">',
            '    <div class="insight-head"><span class="insight-icon" aria-hidden="true">🗣️</span>'
            '<span class="insight-label">分析対象の意見</span></div>',
            f'    <strong class="insight-value">{total}<small>件</small></strong>',
            f"    <p class=\"insight-note\">収集した{collected}件のうち意見と判定した投稿。"
            f"AIが論点・立場・表現強度を分類</p>",
            '    <div class="insight-meter" aria-hidden="true"><i style="width:100%"></i></div>',
            "  </article>",
            '  <article class="stat insight-stat" data-tone="debate">',
            '    <div class="insight-head"><span class="insight-icon" aria-hidden="true">⚖️</span>'
            '<span class="insight-label">改正への態度</span></div>',
            f'    <span class="insight-chip">{abs(neg - pos)}件差</span>',
            f'    <div class="insight-versus"><span>反対（男系維持）<b>{neg}</b></span><em>VS</em>'
            f"<span>賛成（女系容認）<b>{pos}</b></span></div>",
            f'    <div class="insight-split" aria-hidden="true"><i style="width:{neg_pct}%"></i>'
            f'<i style="width:{100 - neg_pct}%"></i></div>',
            "  </article>",
            '  <article class="stat insight-stat" data-tone="insight">',
            '    <div class="insight-head"><span class="insight-icon" aria-hidden="true">💬</span>'
            '<span class="insight-label">意見と情報共有</span></div>',
            f'    <div class="insight-versus"><span>意見<b>{total}</b></span><em>VS</em>'
            f"<span>情報共有<b>{collected - total}</b></span></div>",
            f'    <div class="insight-split" data-palette="gold-purple" aria-hidden="true">'
            f'<i style="width:{op_pct}%"></i><i style="width:{100 - op_pct}%"></i></div>',
            f"    <p class=\"insight-note\">賛否を述べた投稿が{op_pct}%。残りはニュース共有など</p>",
            "  </article>",
            '  <article class="stat insight-stat" data-tone="topic">',
            '    <div class="insight-head"><span class="insight-icon" aria-hidden="true">🔥</span>'
            '<span class="insight-label">最も話された論点</span></div>',
            f'    <strong class="insight-value">{html.escape(labels.get(top, top))} '
            f"{counts[top]}<small>件</small></strong>",
            '    <p class="insight-note">皇位継承の原則をどこまで変えるかが中心</p>',
            f'    <div class="insight-meter" aria-hidden="true">'
            f'<i style="width:{round(counts[top] / total * 100)}%"></i></div>',
            "  </article>",
        ]
    )


def build_stance_summary(
    rows: list[dict[str, Any]], order: list[str], labels: dict[str, str]
) -> str:
    """スタンス集計。正典に無い軸（旧2D分類の継承観）は作らない。"""
    stances = Counter(classification(r)["stance"] for r in rows)
    total = len(rows)
    counts = Counter(classification(r)["main_issue"] for r in rows)
    top = order[0]
    heat_all = sum(INTENSITY_HEAT[classification(r)["intensity"]] for r in rows) / total
    per_issue = sorted(
        ((n, stance_stats(rows, n)["heat"]) for n in order), key=lambda kv: -kv[1]
    )
    hottest, coolest = per_issue[0], per_issue[-1]

    return "\n".join(
        [
            '<article class="axis-card"><div class="axis-kicker">改正への態度</div>'
            f"<h3>反対・慎重が最多</h3><div class=\"axis-count\">{stances[NEG]}</div>"
            f"<p>改正反対（男系維持）{stances[NEG]}件が最も多く、改正賛成（女系容認）は{stances[POS]}件。"
            f"賛否を明示しない中立・情報が{stances[NEU]}件で、全{total}件の"
            f"{round(stances[NEU] / total * 100)}%を占めます。</p></article>",
            f'<article class="axis-card"><div class="axis-kicker">最も語られた論点</div>'
            f"<h3>{html.escape(labels.get(top, top))}</h3>"
            f'<div class="axis-count">{counts[top]}</div>'
            f"<p>全{total}件のうち{round(counts[top] / total * 100)}%。"
            f"次点は{html.escape(labels.get(order[1], order[1]))}の{counts[order[1]]}件です。</p></article>",
            f'<article class="axis-card"><div class="axis-kicker">感情温度</div>'
            f"<h3>怒りの中心は「{html.escape(labels.get(hottest[0], hottest[0]))}」</h3>"
            f'<div class="axis-count">{heat_all:.2f}</div>'
            f"<p>感情の強さを0〜2で数値化した全体平均。論点別では"
            f"{html.escape(labels.get(hottest[0], hottest[0]))}が{hottest[1]:.2f}で最も高く、"
            f"{html.escape(labels.get(coolest[0], coolest[0]))}の{coolest[1]:.2f}が最も冷静です。</p></article>",
        ]
    )


def build_detail_tables(
    rows: list[dict[str, Any]], order: list[str], labels: dict[str, str]
) -> str:
    counts = Counter(classification(r)["main_issue"] for r in rows)
    stances = Counter(classification(r)["stance"] for r in rows)
    intensities = Counter(classification(r)["intensity"] for r in rows)
    total = len(rows)

    issue_rows = "".join(
        f"<tr><th>{html.escape(labels.get(n, n))}</th><td>{counts[n]}</td></tr>" for n in order
    )
    stance_rows = "".join(
        f"<tr><th>{html.escape(k)}</th><td>{stances[k]}</td></tr>" for k in (NEG, NEU, POS)
    )
    intensity_rows = "".join(
        f"<tr><th>{label}</th><td>{intensities[key]}</td></tr>"
        for key, label in (("high", "high（強い）"), ("medium", "medium（中）"), ("low", "low（弱い）"))
    )
    return (
        "<details open><summary>論点別件数（main_issue）</summary>"
        f'<div class="table-wrap"><table><tbody>{issue_rows}'
        '<tr><th style="font-weight:900">合計</th>'
        f'<td style="font-weight:900">{total}</td></tr></tbody></table></div></details>\n'
        "<details><summary>改正への態度（stance）</summary>"
        f'<div class="table-wrap"><table><tbody>{stance_rows}</tbody></table></div></details>\n'
        "<details><summary>感情の強さ（intensity）</summary>"
        f'<div class="table-wrap"><table><tbody>{intensity_rows}</tbody></table></div></details>'
    )


def replace_once(page: str, pattern: str, replacement: str, what: str, *, flags=0) -> str:
    new_page, n = re.subn(pattern, lambda _: replacement, page, flags=flags)
    if n != 1:
        raise IssueCountError(f"{what}: 1箇所だけ一致する必要があります（{n}箇所）")
    return new_page


def build(
    *,
    check: bool = False,
    source: Path | None = None,
    template: Path | None = None,
    output: Path | None = None,
) -> tuple[list[str], bool]:
    rows, sample_file, collected, period = load_canon(source)
    config_path = ROOT / "configs" / f"{THEME}-reaction-map.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    arena = config.get("arena")
    if not isinstance(arena, dict):
        raise IssueCountError(f"{THEME}: configs に arena がありません")

    labels = {str(k): str(v) for k, v in (arena.get("labels") or {}).items()}
    icons = {str(k): str(v) for k, v in (arena.get("icons") or {}).items()}
    blocks = arena.get("issue_blocks") or []

    order = issue_order(rows)
    counts = Counter(classification(r)["main_issue"] for r in rows)

    # 争点ブロックとカードは、アリーナのセクターと同じ並びでなければ番号がずれる
    block_issues = [str(b["main_issue"]) for b in blocks]
    if block_issues != order[: len(block_issues)]:
        raise IssueCountError(
            "arena.issue_blocks の並びが件数降順と一致しません。"
            f"設定={block_issues} 正典={order[: len(block_issues)]}"
        )
    card_issues = [i for c in config["issue_counts"]["cards"] for i in c["main_issue"]]
    if card_issues != block_issues:
        raise IssueCountError(
            f"issue_counts.cards と arena.issue_blocks の並びが違います: {card_issues} / {block_issues}"
        )
    missing = [n for n in order if n not in labels]
    if missing:
        raise IssueCountError(f"arena.labels に無い論点があります: {', '.join(missing)}")
    total = len(rows)
    top_issue = order[0]

    html_path = Path(template) if template else ROOT / "docs" / f"{THEME}-reaction-map.html"
    before = html_path.read_text(encoding="utf-8")
    page = before

    page = replace_once(
        page, r"const SM_RAW = \[.*?\n\];", build_sm_raw(rows, order), "SM_RAW", flags=re.S
    )
    page = replace_once(
        page,
        r"const ISSUES=\[.*?\n  \];",
        build_issues(order, labels),
        "ISSUES",
        flags=re.S,
    )
    page = replace_once(
        page,
        r"var VOTE_ISSUES=\[.*?\n  \];",
        build_vote_issues(order, labels, icons),
        "VOTE_ISSUES",
        flags=re.S,
    )
    page = replace_once(
        page, r"addBtn\('全件 \(\d+\)',-1\);", f"addBtn('全件 ({total})',-1);", "フィルタの全件ボタン"
    )
    page = replace_once(
        page,
        r"<span>(?:意見)?\d+件 \| セクター=",
        f"<span>意見{total}件 | セクター=",
        "アリーナ見出しの件数",
    )
    page = replace_once(
        page,
        r"収集した[^<]*?つの論点に整理しました。",
        f"収集した公開投稿{collected}件のうち、意見と判定した{total}件を"
        f"AIが{len(blocks)}つの論点に整理しました。",
        "ヒーローの lead",
    )
    # 調査条件・収集方法・収集クエリは、収集総数と意見件数を必ずセットで書く
    # （どちらか一方だけが出ていると、読者はマップの分母を取り違える）
    page = replace_once(
        page,
        r"で取得した公開投稿 \d+件<br>\n(?:  （うち[^\n]*\n)?",
        f"で取得した公開投稿 {collected}件<br>\n"
        f"  （うち意見と判定した{total}件を、マップ・論点・賛否の分析対象としています）<br>\n",
        "調査条件の件数",
    )
    page = replace_once(
        page,
        r"（取得期間: [^／]*／",
        f"（取得期間: {period}／",
        "調査条件の取得期間",
    )
    page = replace_once(
        page,
        r"関連性と[^<]*?件を表示しています。",
        f"関連性と意見性、論点を判定し、収集した{collected:,}件のうち"
        f"意見と判定した{total:,}件を表示しています。",
        "収集方法の件数",
    )
    # 検索語・取得期間・件数は収集回が増えるたびに変わる。ページに固定で書くと、
    # 追加収集のあとも初回の値が残る（2026-08-10 まで、7/17収集時の検索語9本と
    # 「2026-07-17収集分と比較」が公開ページに残っていた）。
    page = replace_once(
        page,
        r"<details><summary>収集クエリ</summary>.*?</details>",
        "<details><summary>収集クエリ</summary><ul>"
        f'<li>{html.escape(" / ".join(load_queries()))}</li>'
        f"<li>{html.escape(period)}にYahooリアルタイム検索で累計{collected}件を取得"
        f"（重複除去後）。全件をAIが論点・立場・表現強度で分類し、"
        f"うち意見と判定した{total}件を集計対象にしています。</li>"
        f"<li>ページ上の件数はすべてこの意見{total}件から生成しています"
        "（scripts/build_koshitsu_arena.py）。"
        "「世論の潮目」ウィジェットだけは例外で、前回の収集分と今回の収集分どうしの"
        "構成比を比較しています（対象日はウィジェット内に表示）。</li>"
        "</ul></details>",
        "収集クエリ",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<span class="conclusion-count"><b>\d+</b>件</span>',
        f'<span class="conclusion-count"><b>{counts[top_issue]}</b>件</span>',
        "議論の中心の件数",
    )
    page = replace_once(
        page,
        r"<!-- INSIGHT_STATS_START -->.*?<!-- INSIGHT_STATS_END -->",
        "<!-- INSIGHT_STATS_START -->\n"
        + build_insight_stats(rows, order, labels, collected)
        + "\n<!-- INSIGHT_STATS_END -->",
        "注目ポイント",
        flags=re.S,
    )
    page = replace_once(
        page,
        r"<!-- ISSUE_VOICES_START -->.*?<!-- ISSUE_VOICES_END -->",
        "<!-- ISSUE_VOICES_START -->\n"
        + build_issue_section(rows, blocks)
        + "\n<!-- ISSUE_VOICES_END -->",
        "争点別のXの声",
        flags=re.S,
    )
    page = replace_once(
        page,
        r"<!-- STANCE_SUMMARY_START -->.*?<!-- STANCE_SUMMARY_END -->",
        "<!-- STANCE_SUMMARY_START -->\n"
        + build_stance_summary(rows, order, labels)
        + "\n<!-- STANCE_SUMMARY_END -->",
        "スタンス集計",
        flags=re.S,
    )
    page = replace_once(
        page,
        r"<!-- DETAIL_TABLES_START -->.*?<!-- DETAIL_TABLES_END -->",
        "<!-- DETAIL_TABLES_START -->\n"
        + build_detail_tables(rows, order, labels)
        + "\n<!-- DETAIL_TABLES_END -->",
        "詳細データの表",
        flags=re.S,
    )

    # 論点カードの件数（sync_issue_counts.py と同じ span を、ここでも合わせておく）
    for card in config["issue_counts"]["cards"]:
        issue_total = sum(counts[str(i)] for i in card["main_issue"])
        page = replace_once(
            page,
            rf'<span class="explainer-count" id="issue-count-{THEME}-{card["slug"]}">\d+件</span>',
            span_html(THEME, str(card["slug"]), issue_total),
            f'論点カード {card["slug"]} の件数',
        )

    changed = page != before
    # output 指定時は差分がなくても書き出す（adapter が候補同士を突き合わせるため）
    if not check and (changed or output is not None):
        target = Path(output) if output else html_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding="utf-8")

    detail = " / ".join(f"{labels.get(n, n)}={counts[n]}" for n in order)
    lines = [
        f"出所: {sample_file}（収集{collected}件 → 意見{total}件）",
        f"論点: {detail}",
        f"投票選択肢: {len(order)}  論点カード: {len(config['issue_counts']['cards'])}枚",
    ]
    return lines, changed


def main() -> int:
    parser = argparse.ArgumentParser(description="皇室典範改正ページの論点表示を正典から生成する")
    parser.add_argument("--check", action="store_true", help="書き換えず、差分があれば exit 1")
    parser.add_argument("--input", type=Path, help="正典の代わりに読む累積候補（staging用）")
    parser.add_argument("--html-template", type=Path, help="読み込むHTML（既定は公開ページ）")
    parser.add_argument("--output-html", type=Path, help="書き出し先（既定は読み込んだHTML）")
    args = parser.parse_args()
    try:
        lines, changed = build(
            check=args.check,
            source=args.input,
            template=args.html_template,
            output=args.output_html,
        )
    except (IssueCountError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("\n".join(lines))
    print("UPDATE" if changed else "OK    ")
    if args.check and changed:
        print("NG  ページが正典から生成した内容と一致しません", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
