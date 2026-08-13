#!/usr/bin/env python3
"""副首都ページの論点表示を、正典の「意見」投稿だけから一括生成する。

2026-08-08 まで、このページは `page_update_mode: manual` で再生成できなかった。
公開分は2D分類255件（賛否ラベルなし）で、7/14・7/26 にHermesで分類した600件は
「世論の潮目」ウィジェットのためだけに使われ、正典へ統合されていなかった（課題40）。
正典を Hermes 方式へ移したのに合わせて、ページ側の数字の出所もここ1本に集約する。

生成する箇所:

- SM_RAW（アリーナの点）
- ISSUES（アリーナのセクターと件数）
- ヒーローの lead / 議論の中心の件数
- 調査条件（RESEARCH_CONDITIONS）の件数
- 注目ポイント（insight-stats）4枚
- 「6つの論点とXの声」（ナビ・件数・熱量・賛否の内訳・代表投稿）
- スタンス集計（axis-card）
- 詳細データの表
- 論点カードの件数（explainer-count）

**セクターの並びは `fukushuto_taxonomy.ISSUE_ORDER` で固定する。**
件数の降順に並べ替えると投票の `choiceIdx`（論点×立場の21通り）の意味がずれ、
Supabase に入っている既存票が別の論点に付け替わる。並べ替えてよいのは
「6つの論点とXの声」の表示順だけで、そちらは件数の降順にして論点1を最大にする。

**「SNS投稿の収集方法」の本文はここでは書かない。** そこは configs/theme-seo.json を
`apply_theme_trust.py` が {total} / {opinions} を解決して書き込む。両方が同じ場所を
書くと、次にビルダーを流したときに差し替え対象を見失って止まる。

    python3 scripts/build_fukushuto_arena.py
    python3 scripts/build_fukushuto_arena.py --check   # 書き換えず差分の有無だけ見る
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
    from .fukushuto_taxonomy import (
        INTENSITIES,
        ISSUE_ORDER,
        ISSUES,
        NEUTRAL_STANCE,
        OTHER,
        STANCE_ORDER,
        STANCES,
        VOTE_ISSUE_LABELS,
        VOTE_ISSUE_ORDER,
        arena_e,
        arena_x,
    )
    from .issue_card_counts import IssueCountError, span_html
    from .sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml
    from .verify_sample_periods import expected_period, summarize
    from .x_embed import embed_html, period_label
except ImportError:  # python3 scripts/build_fukushuto_arena.py
    from fukushuto_taxonomy import (  # type: ignore[no-redef]
        INTENSITIES,
        ISSUE_ORDER,
        ISSUES,
        NEUTRAL_STANCE,
        OTHER,
        STANCE_ORDER,
        STANCES,
        VOTE_ISSUE_LABELS,
        VOTE_ISSUE_ORDER,
        arena_e,
        arena_x,
    )
    from issue_card_counts import IssueCountError, span_html  # type: ignore[no-redef]
    from sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml  # type: ignore[no-redef]
    from verify_sample_periods import expected_period, summarize  # type: ignore[no-redef]
    from x_embed import embed_html, period_label  # type: ignore[no-redef]

THEME = "fukushuto"
NEG = "法案反対"
POS = "法案賛成・推進"
NEU = NEUTRAL_STANCE
# 「その他」を除いた論点。最大論点・議論の中心・論点1はここから選ぶ
# （「その他」は論点カードにも投票の強調にも出てこないため、最大にすると表示が食い違う）。
NAMED_ISSUES = tuple(name for name in ISSUE_ORDER if name != OTHER)

# 熱量（0〜2）の重み。intensity を数値化して平均する。
INTENSITY_HEAT = {"low": 0.0, "medium": 1.0, "high": 2.0}


def classification(record: dict[str, Any]) -> dict[str, Any]:
    nested = record.get("classification")
    if not isinstance(nested, dict):
        raise IssueCountError("classification を持たないレコードがあります")
    return nested


def load_opinions(
    source: Path | None = None,
) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    """正典を読み、意見と判定されたレコードだけを返す。

    `is_opinion` を持たないレコードは**除外せずエラーで止める**。静かに落とすと、
    あとでページの件数が合わない原因を追えなくなる。
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

    if not isinstance(records, list) or not records:
        raise IssueCountError(f"{THEME}: 正典が空、またはJSON配列ではありません: {sample_file}")

    opinions: list[dict[str, Any]] = []
    for number, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise IssueCountError(f"{number}件目がJSONオブジェクトではありません")
        c = classification(record)
        if not isinstance(c.get("is_opinion"), bool):
            raise IssueCountError(
                f"{number}件目の classification.is_opinion が欠落またはboolではありません"
            )
        if not c["is_opinion"]:
            continue
        issue, stance, intensity = c.get("main_issue"), c.get("stance"), c.get("intensity")
        if issue not in ISSUES:
            raise IssueCountError(f"{number}件目の main_issue が論点体系にありません: {issue!r}")
        if stance not in STANCES:
            raise IssueCountError(f"{number}件目の stance が論点体系にありません: {stance!r}")
        if intensity not in INTENSITIES:
            raise IssueCountError(f"{number}件目の intensity が不正です: {intensity!r}")
        opinions.append(record)
    if not opinions:
        raise IssueCountError(f"{THEME}: 意見と判定されたレコードが0件です: {sample_file}")
    return opinions, sample_file, records


def js_str(text: str) -> str:
    """シングルクォートのJS文字列リテラルの中身に落とす。"""
    return text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")


def build_sm_raw(rows: list[dict[str, Any]]) -> str:
    index = {name: i for i, name in enumerate(ISSUE_ORDER)}
    lines = []
    for row in rows:
        c = classification(row)
        lines.append(
            "{{x:{x},e:{e},c:{c},i:{i},s:'{s}',u:'{u}'}}".format(
                x=arena_x(str(c["stance"]), str(c["intensity"])),
                e=arena_e(str(c["intensity"])),
                c=round(float(c.get("confidence") or 0.7), 2),
                i=index[str(c["main_issue"])],
                s=js_str(str(c.get("summary") or "")[:60]),
                u=js_str(str(row.get("url") or "")),
            )
        )
    return "const SM_RAW = [\n" + ",\n".join(lines) + "\n];"


def build_issues(counts: Counter[str]) -> str:
    body = ",\n    ".join(f"{{k:'{js_str(name)}', n:{counts[name]}}}" for name in ISSUE_ORDER)
    return "const ISSUES = [\n    " + body + "\n  ];"


def stance_stats(rows: list[dict[str, Any]], issue: str | None = None) -> dict[str, Any]:
    subset = [
        row for row in rows if issue is None or classification(row)["main_issue"] == issue
    ]
    counts = Counter(str(classification(row)["stance"]) for row in subset)
    total = len(subset)
    heat = (
        sum(INTENSITY_HEAT[str(classification(row)["intensity"])] for row in subset) / total
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


def ranked_issues(counts: Counter[str]) -> list[str]:
    """「その他」を除いた論点を件数の降順で返す（同数は論点体系の並び）。"""
    return sorted(NAMED_ISSUES, key=lambda name: (-counts[name], NAMED_ISSUES.index(name)))


def build_issue_section(rows: list[dict[str, Any]], blocks: list[dict[str, Any]]) -> str:
    """表示順は件数の降順。アリーナのセクター順（ISSUE_ORDER）とは別物。

    ここを件数降順にしておくと論点1が必ず最大論点になり、verify_theme_page.py の
    最大勢力チェックと矛盾しない。セクター順を並べ替えると投票が壊れるので触らない。
    """
    counts = Counter(str(classification(row)["main_issue"]) for row in rows)
    by_issue = {str(block["main_issue"]): block for block in blocks}
    ordered = [by_issue[name] for name in ranked_issues(counts)]
    heats = {name: stance_stats(rows, name)["heat"] for name in NAMED_ISSUES}
    hottest = max(heats, key=lambda name: heats[name])
    coolest = min(heats, key=lambda name: heats[name])

    nav, articles = [], []
    for number, block in enumerate(ordered, start=1):
        issue = str(block["main_issue"])
        stats = stance_stats(rows, issue)
        if not stats["total"]:
            raise IssueCountError(f"{issue}: 正典の意見に1件もありません")
        anchor = f"issue-{block['slug']}"
        nav.append(
            f'<a href="#{anchor}">{html.escape(str(block["nav_label"]))} {stats["total"]}</a>'
        )
        marks = ["最大勢力"] if number == 1 else []
        heat_note = ""
        if issue == hottest:
            marks.append("最も熱い")
            heat_note = "（最高）"
        elif issue == coolest:
            marks.append("いちばん冷静")
            heat_note = "（最も冷静）"
        badge = "".join("・" + mark for mark in marks)

        samples = "\n".join(
            '<div class="sample-card"><div class="meta">{meta}</div><p>{note}</p>'
            "{embed}</div>".format(
                meta=html.escape(str(sample["meta"])),
                note=html.escape(str(sample["note"])),
                embed=embed_html(sample["url"]),
            )
            for sample in block.get("samples") or []
        )

        articles.append(
            f'<article class="issue-block" id="{anchor}">\n'
            f'<div class="issue-head"><span class="axis-kicker">論点{number}{badge}</span>'
            f'<h3>{html.escape(str(block["heading"]))}'
            f'<span class="issue-count">{stats["total"]}件</span>'
            f'<span class="issue-heat">熱量 {stats["heat"]:.2f}{heat_note}</span></h3>\n'
            f'<p class="issue-desc">{html.escape(str(block["desc"]))}</p>\n'
            f'<div class="issue-sides">'
            f'<div class="side neg"><strong>法案反対（{stats["neg"]}件）</strong>'
            f'{html.escape(str(block["side_neg"]))}</div>'
            f'<div class="side pos"><strong>法案賛成・推進（{stats["pos"]}件）</strong>'
            f'{html.escape(str(block["side_pos"]))}</div></div>\n'
            f"</div>\n"
            f'<div class="sample-grid">\n{samples}\n</div>\n'
            f"</article>"
        )

    return (
        '<nav class="quadrant-nav">' + "".join(nav) + "</nav>\n\n" + "\n\n".join(articles)
    )


def build_insight_stats(rows: list[dict[str, Any]], collected: int) -> str:
    """ヒーロー直下の注目ポイント4枚。

    旧版の4枚目は2D分類の stance_location（大阪指定への評価）を出していたが、
    Hermes 正典にその軸は無い。無い軸は作らず、意見と情報共有の比率に置き換える。
    """
    total = len(rows)
    counts = Counter(str(classification(row)["main_issue"]) for row in rows)
    stats = stance_stats(rows)
    top = ranked_issues(counts)[0]
    neg_pct = round(stats["neg"] / total * 100)
    top_pct = round(counts[top] / total * 100)
    op_pct = round(total / collected * 100)

    return "\n".join(
        [
            '<section class="stats insight-stats" aria-label="このテーマの4つの注目ポイント">',
            '  <article class="stat insight-stat">',
            '    <div class="insight-head"><span class="insight-icon" aria-hidden="true">🗣️</span>'
            '<span class="insight-label">分析対象の意見</span></div>',
            f'    <strong class="insight-value">{total}<small>件</small></strong>',
            f'    <p class="insight-note">収集した{collected}件のうち意見と判定した投稿。'
            f"AIが論点・立場・表現強度を分類</p>",
            '    <div class="insight-meter" aria-hidden="true"><i style="width:100%"></i></div>',
            "  </article>",
            '  <article class="stat insight-stat" data-tone="debate">',
            '    <div class="insight-head"><span class="insight-icon" aria-hidden="true">⚖️</span>'
            '<span class="insight-label">最も多い立場</span></div>',
            f'    <strong class="insight-value">法案反対 {neg_pct}%</strong>',
            f'    <p class="insight-note">意見{total}件のうち{stats["neg"]}件。'
            f'賛成・推進は{stats["pos"]}件、中立・情報は{stats["neu"]}件</p>',
            f'    <div class="insight-meter" aria-hidden="true"><i style="width:{neg_pct}%"></i></div>',
            "  </article>",
            '  <article class="stat insight-stat" data-tone="topic">',
            '    <div class="insight-head"><span class="insight-icon" aria-hidden="true">🔥</span>'
            '<span class="insight-label">最も話された論点</span></div>',
            f'    <strong class="insight-value">{html.escape(top)} {counts[top]}<small>件</small></strong>',
            f'    <p class="insight-note">意見の{top_pct}%がこの論点に集まっています</p>',
            f'    <div class="insight-meter" aria-hidden="true"><i style="width:{top_pct}%"></i></div>',
            "  </article>",
            '  <article class="stat insight-stat" data-tone="insight">',
            '    <div class="insight-head"><span class="insight-icon" aria-hidden="true">💬</span>'
            '<span class="insight-label">意見と情報共有</span></div>',
            f'    <div class="insight-versus"><span>意見<b>{total}</b></span><em>VS</em>'
            f"<span>情報共有<b>{collected - total}</b></span></div>",
            f'    <div class="insight-split" aria-hidden="true">'
            f'<i style="width:{op_pct}%"></i><i style="width:{100 - op_pct}%"></i></div>',
            f'    <p class="insight-note">賛否を述べた投稿が{op_pct}%。残りはニュース共有など</p>',
            "  </article>",
            "</section>",
        ]
    )


def build_stance_summary(rows: list[dict[str, Any]]) -> str:
    total = len(rows)
    stats = stance_stats(rows)
    counts = Counter(str(classification(row)["main_issue"]) for row in rows)
    ranked = ranked_issues(counts)
    heats = {name: stance_stats(rows, name)["heat"] for name in NAMED_ISSUES}
    hottest = max(heats, key=lambda name: heats[name])
    coolest = min(heats, key=lambda name: heats[name])
    heat_all = sum(INTENSITY_HEAT[str(classification(row)["intensity"])] for row in rows) / total

    return "\n".join(
        [
            '<section class="panel conflict-panel"><div class="panel-title"><h2>スタンス集計</h2>'
            "<span>意見のみ・正典から自動集計</span></div>",
            '<div class="axis-grid">',
            '<article class="axis-card"><div class="axis-kicker">法案への態度</div>'
            "<h3>反対・慎重が多数</h3>"
            f'<div class="axis-count">{stats["neg"]}</div>'
            f'<p>法案反対が{stats["neg"]}件で、法案賛成・推進の{stats["pos"]}件を大きく上回ります。'
            f'賛否を明示しない中立・情報は{stats["neu"]}件で、意見{total}件の'
            f'{round(stats["neu"] / total * 100)}%です。</p></article>',
            '<article class="axis-card"><div class="axis-kicker">最も語られた論点</div>'
            f"<h3>{html.escape(ranked[0])}</h3>"
            f'<div class="axis-count">{counts[ranked[0]]}</div>'
            f"<p>意見{total}件のうち{round(counts[ranked[0]] / total * 100)}%。"
            f"次点は{html.escape(ranked[1])}の{counts[ranked[1]]}件です。</p></article>",
            '<article class="axis-card"><div class="axis-kicker">感情温度</div>'
            f"<h3>怒りの中心は「{html.escape(hottest)}」</h3>"
            f'<div class="axis-count">{heat_all:.2f}</div>'
            f"<p>感情の強さを0〜2で数値化した全体平均。論点別では"
            f"{html.escape(hottest)}が{heats[hottest]:.2f}で最も高く、"
            f"{html.escape(coolest)}の{heats[coolest]:.2f}が最も冷静です。</p></article>",
            "</div></section>",
        ]
    )


def build_details(rows: list[dict[str, Any]], collected: int, queries: list[str]) -> str:
    counts = Counter(str(classification(row)["main_issue"]) for row in rows)
    stances = Counter(str(classification(row)["stance"]) for row in rows)
    intensities = Counter(str(classification(row)["intensity"]) for row in rows)
    total = len(rows)
    # 論点別の表は「その他」も含めて全件を出す（合計が意見件数と一致することを示す）
    ranked = ranked_issues(counts) + [OTHER]

    issue_rows = "".join(
        f"<tr><th>{html.escape(name)}</th><td>{counts[name]}</td></tr>" for name in ranked
    )
    stance_rows = "".join(
        f"<tr><th>{html.escape(name)}</th><td>{stances[name]}</td></tr>" for name in STANCE_ORDER
    )
    intensity_rows = "".join(
        f"<tr><th>{label}</th><td>{intensities[key]}</td></tr>"
        for key, label in (("high", "high（強い）"), ("medium", "medium（中）"), ("low", "low（弱い）"))
    )
    # 投票の選択肢 → アリーナのセクター。並びは taxonomy の VOTE_ISSUE_ORDER に従う。
    vote_rows = ""
    for index, name in enumerate(VOTE_ISSUE_ORDER):
        color = (
            f'<td rowspan="{len(VOTE_ISSUE_ORDER)}">賛成=緑 / どちらでもない=灰 / 反対=赤</td>'
            if index == 0
            else ""
        )
        vote_rows += (
            f"<tr><td>{html.escape(VOTE_ISSUE_LABELS[name])}</td>"
            f"<td>{html.escape(name)}</td>{color}</tr>"
        )

    return "\n".join(
        [
            '<section class="panel details-panel" id="detail-data">'
            "<div class=\"panel-title\"><h2>詳細データ</h2><span>折りたたみ</span></div>",
            "<details open><summary>論点別件数（main_issue）</summary>"
            f'<div class="table-wrap"><table><tbody>{issue_rows}'
            '<tr><th style="font-weight:900">合計（意見）</th>'
            f'<td style="font-weight:900">{total}</td></tr></tbody></table></div></details>',
            "<details><summary>法案への態度（stance）</summary>"
            f'<div class="table-wrap"><table><tbody>{stance_rows}</tbody></table></div></details>',
            "<details><summary>感情の強さ（intensity）</summary>"
            f'<div class="table-wrap"><table><tbody>{intensity_rows}</tbody></table></div></details>',
            "<details><summary>投票の選択とアリーナ上の位置</summary>"
            '<div class="table-wrap"><table><thead><tr><th>選んだ論点</th>'
            "<th>マーカーが置かれるセクター</th><th>マーカーの色</th></tr></thead>"
            f"<tbody>{vote_rows}</tbody></table></div></details>",
            "<details><summary>収集クエリ</summary><ul>"
            f'<li>{html.escape(" / ".join(queries))}</li>'
            f"<li>Yahooリアルタイム検索で累計{collected}件を取得（重複除去後）。"
            f"全件をAIが論点・立場・表現強度で分類し、うち意見と判定した{total}件を"
            "マップ・論点・賛否の集計対象にしています。</li></ul></details>",
            "<details><summary>注意</summary><ul>"
            "<li>これは世論調査ではなく、Yahooリアルタイム検索で取得した投稿サンプルの反応整理です。</li>"
            "<li>初回の収集時点が衆院通過直前のため、国会審議・修正合意への反応が"
            "多く出やすいバイアスがあります。</li></ul></details>",
            "</section>",
        ]
    )


def load_queries() -> list[str]:
    themes = parse_themes_yaml(THEMES_YAML)
    path = ROOT / str(themes[THEME].get("refresh_config") or "")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [str(query) for query in (value.get("fetch_queries") or [])]


def sample_period(records: list[dict[str, Any]]) -> str:
    """調査条件に出す収集日の範囲。

    THEMES.yaml の `sample_period` と同じ計算を使う。verify_theme_page.py は
    台帳の値とページの表記を突き合わせるので、別々に数えると必ずいつかズレる。
    """
    period = expected_period(summarize(records))
    return period_label(period)


def replace_once(page: str, pattern: str, replacement: str, label: str, *, flags: int = 0) -> str:
    result, count = re.subn(pattern, lambda _: replacement, page, count=1, flags=flags)
    if count != 1:
        raise IssueCountError(f"{label}: 1箇所だけ一致する必要があります（{count}箇所）")
    return result


def build(
    *,
    check: bool = False,
    source: Path | None = None,
    template: Path | None = None,
    output: Path | None = None,
) -> tuple[list[str], bool]:
    rows, sample_file, records = load_opinions(source)
    collected = len(records)
    counts = Counter(str(classification(row)["main_issue"]) for row in rows)
    total = len(rows)

    config = json.loads(
        (ROOT / "configs" / f"{THEME}-reaction-map.json").read_text(encoding="utf-8")
    )
    arena = config.get("arena")
    if not isinstance(arena, dict):
        raise IssueCountError(f"{THEME}: configs に arena がありません")
    blocks = arena.get("issue_blocks") or []
    block_issues = [str(block["main_issue"]) for block in blocks]
    expected = [name for name in ISSUE_ORDER if name != OTHER]
    if sorted(block_issues) != sorted(expected):
        raise IssueCountError(
            f"arena.issue_blocks が論点体系と一致しません: {block_issues} / {expected}"
        )
    for block in blocks:
        value = block.get("conclusion")
        if not isinstance(value, dict) or not value.get("headline") or not value.get("detail"):
            raise IssueCountError(
                f'{block["main_issue"]}: arena.issue_blocks に conclusion がありません'
                "（最大論点が入れ替わったとき「議論の中心」の見出しを差し替えられません）"
            )

    html_path = Path(template) if template else ROOT / "docs" / f"{THEME}-reaction-map.html"
    before = html_path.read_text(encoding="utf-8")
    page = before

    top = ranked_issues(counts)[0]

    page = replace_once(page, r"const SM_RAW = \[.*?\n\];", build_sm_raw(rows), "SM_RAW", flags=re.S)
    page = replace_once(
        page, r"const ISSUES = \[.*?\n  \];", build_issues(counts), "ISSUES", flags=re.S
    )
    page = replace_once(
        page,
        r'<p class="lead">.*?</p>',
        f'<p class="lead">Yahooリアルタイム検索で取得した公開投稿{collected}件のうち、'
        f"意見と判定した{total}件をAIが{len(blocks)}つの論点に整理しました。"
        "世論調査ではなく、SNS反応サンプルの論点比較です。</p>",
        "ヒーローの lead",
        flags=re.S,
    )
    # 「議論の中心」は最大論点の見出しと件数を並べて出す。件数だけ差し替えていた頃は、
    # 最大論点が入れ替わった瞬間に「定義・中身の見出し＋都構想・維新の件数」になった
    # （2026-08-08 の統合で実際に発生）。見出しも設定から選び直す。
    conclusion = {str(b["main_issue"]): b.get("conclusion") or {} for b in blocks}[top]
    page = replace_once(
        page,
        r'<li class="conclusion-focus">.*?</li>',
        '<li class="conclusion-focus">'
        f'<span class="conclusion-count"><b>{counts[top]}</b>件</span>'
        f'<strong>{html.escape(str(conclusion["headline"]))}</strong>'
        f'<span class="conclusion-detail">{html.escape(str(conclusion["detail"]))}</span></li>',
        "議論の中心",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<p style="max-width:1000px;margin:0 auto;">.*?</p>',
        '<p style="max-width:1000px;margin:0 auto;">'
        '<strong style="color:var(--ink);">このマップの元データ:</strong> '
        f"Yahooリアルタイム検索で取得した公開投稿 {collected}件<br>\n"
        f"  （うち意見と判定した{total}件を、マップ・論点・賛否の分析対象としています）<br>\n"
        # 確認表示は <span class="review-note"> で囲む（apply_review_note.py が中身を書き分け、
        # verify_number_provenance.py がこの囲みだけを検査から外す）。落とすと再生成で検査が落ちる。
        f'  （取得期間: {sample_period(records)}／'
        '<span class="review-note">AI分類。代表投稿は編集部が選定</span>）<br>\n'
        "  <strong>社会全体の世論調査ではありません。</strong></p>",
        "調査条件",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<section class="stats insight-stats".*?\n</section>',
        build_insight_stats(rows, collected),
        "注目ポイント",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<div class="panel-title"><h2>SNS反応マップ</h2><span>[^<]*</span></div>',
        f'<div class="panel-title"><h2>SNS反応マップ</h2><span>意見{total}件 | '
        "セクター=論点 / 中心に近いほど冷静 / 色=賛否 | ホバーで詳細・クリックでXへ</span></div>",
        "マップ見出し",
    )
    page = replace_once(
        page,
        r'<nav class="quadrant-nav">.*?</section>',
        build_issue_section(rows, blocks) + "\n</section>",
        "6つの論点とXの声",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<section class="panel conflict-panel"><div class="panel-title"><h2>スタンス集計</h2>.*?</section>',
        build_stance_summary(rows),
        "スタンス集計",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<section class="panel details-panel" id="detail-data">.*?\n</section>',
        build_details(rows, collected, load_queries()),
        "詳細データ",
        flags=re.S,
    )

    for card in config["issue_counts"]["cards"]:
        card_total = sum(counts[str(issue)] for issue in card["main_issue"])
        page = replace_once(
            page,
            rf'<span class="explainer-count" id="issue-count-{THEME}-{card["slug"]}">\d+件</span>',
            span_html(THEME, str(card["slug"]), card_total),
            f'論点カード {card["slug"]} の件数',
        )

    changed = page != before
    # output 指定時は差分がなくても書き出す（候補ページ同士を突き合わせるため）
    if not check and (changed or output is not None):
        target = Path(output) if output else html_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding="utf-8")

    stats = stance_stats(rows)
    return (
        [
            f"出所: {sample_file}（収集{collected}件 → 意見{total}件）",
            "論点: " + " / ".join(f"{name}={counts[name]}" for name in ISSUE_ORDER),
            f'賛否: {NEG}={stats["neg"]} / {NEU}={stats["neu"]} / {POS}={stats["pos"]}',
            f"マップの点: {total}  論点カード: {len(config['issue_counts']['cards'])}枚",
        ],
        changed,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="副首都ページの論点表示を正典から生成する")
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
    except (IssueCountError, OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("\n".join(lines))
    if args.check and changed:
        print("NG  ページが正典から生成した内容と一致しません", file=sys.stderr)
        return 1
    print("UPDATE: HTMLを更新しました" if changed else "OK: 差分なし")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
