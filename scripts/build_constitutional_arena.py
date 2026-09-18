#!/usr/bin/env python3
"""憲法改正ページを正典の「意見」だけから再生成する。

入力は THEMES.yaml に記載した正典だけ。マップ、論点別の声、スタンス集計、
詳細表、論点カードの件数を同じ意見集合から作る。

    python3 scripts/build_constitutional_arena.py
    python3 scripts/build_constitutional_arena.py --check

adapter（refresh_topic.py --promote）から呼ぶときは、正典も公開ページも触らずに
候補だけを組み立てる。読み書きの3点はまとめて指定する。

    python3 scripts/build_constitutional_arena.py \\
      --input <stage>/cumulative-candidate.json \\
      --html-template docs/constitutional-amendment-reaction-map.html \\
      --output-html <stage>/page-candidate.html
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
    from .issue_card_counts import IssueCountError, span_html
    from .verify_sample_periods import expected_period, summarize
    from .x_embed import embed_html, period_label
except ImportError:
    from issue_card_counts import IssueCountError, span_html  # type: ignore[no-redef]
    from verify_sample_periods import expected_period, summarize  # type: ignore[no-redef]
    from x_embed import embed_html, period_label  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parent.parent
THEME = "constitutional-amendment"
PAGE = ROOT / "docs" / "constitutional-amendment-reaction-map.html"
CONFIG = ROOT / "configs" / "constitutional-amendment-reaction-map.json"
PUBLIC_THEME = ROOT / "data" / "public" / "themes" / f"{THEME}.json"

# 先頭6件は投票 choiceIdx と論点カードの順序なので固定する。「その他」は投票対象に
# 加えないが、正典の main_issue を改変せずマップと詳細集計へ含める。
ISSUES = [
    ("改憲全般", "憲法を時代に合わせるべきか、現行憲法の原則を守るべきか。"),
    ("9条・自衛隊", "自衛隊を憲法に明記する意義と、9条の平和主義への影響。"),
    ("緊急事態条項", "災害などへの迅速な対応と、政府への権限集中リスク。"),
    ("国民投票・広告", "CM・ネット広告・資金力の差を含む国民投票の公平性。"),
    ("政党・発議手続き", "政党の姿勢、国会での合意形成、発議までの進め方。"),
    ("情報・議論の質", "事実確認、過激な断定、論点を理解できる情報環境。"),
    ("その他", "主要6論点に収まらない憲法改正に関する意見。"),
]
ISSUE_INDEX = {name: idx for idx, (name, _) in enumerate(ISSUES)}

STANCES = ("慎重・反対", "中立", "手続き重視", "改正推進")
STANCE_KEY = {
    "慎重・反対": "con",
    "中立": "neutral",
    "手続き重視": "process",
    "改正推進": "pro",
}
STANCE_COLORS = {
    "慎重・反対": "#dc2626",
    "中立": "#64748b",
    "手続き重視": "#059669",
    "改正推進": "#2563eb",
}
INTENSITY = {"low": 0.34, "medium": 0.66, "high": 0.94}


def classification(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("classification")
    return value if isinstance(value, dict) else {}


def sample_period(records: list[dict[str, Any]]) -> str:
    """調査条件に出す収集日の範囲。

    THEMES.yaml の `sample_period` と同じ計算を使う。verify_theme_page.py が台帳の値と
    ページの表記を突き合わせるので、別々に数えるといつか必ずズレる。収集回が増える
    たびに変わる値なので、ページ側にも固定で書かない。
    """
    return period_label(expected_period(summarize(records)))


def load_canon(input_path: Path | None = None) -> tuple[list[dict[str, Any]], int, str]:
    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
    sample_file = str(themes[THEME]["sample_file"])
    if "synthetic" in sample_file:
        raise IssueCountError(f"合成データは正典にできません: {sample_file}")
    records = json.loads((input_path or ROOT / sample_file).read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise IssueCountError(f"正典が空、またはJSON配列ではありません: {sample_file}")

    missing_opinion = [r for r in records if "is_opinion" not in classification(r)]
    if missing_opinion:
        raise IssueCountError(
            f"is_opinion を持たないレコードがあります（{len(missing_opinion)}件）: {sample_file}"
        )
    rows = [r for r in records if classification(r).get("is_opinion") is True]
    if not rows:
        raise IssueCountError("意見と判定されたレコードが0件です")

    missing_issue = [r for r in rows if classification(r).get("main_issue") not in ISSUE_INDEX]
    if missing_issue:
        values = Counter(str(classification(r).get("main_issue")) for r in missing_issue)
        raise IssueCountError(f"未知または未設定の main_issue があります: {dict(values)}")
    missing_stance = [r for r in rows if classification(r).get("stance") not in STANCE_KEY]
    if missing_stance:
        values = Counter(str(classification(r).get("stance")) for r in missing_stance)
        raise IssueCountError(f"未知または未設定の stance があります: {dict(values)}")
    source = str(input_path) if input_path else sample_file
    return rows, len(records), source, sample_period(records)


def js_string(value: object) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False)


def build_map_data(rows: list[dict[str, Any]]) -> str:
    issue_lines = [f"  {{k:{js_string(name)},n:0}}" for name, _ in ISSUES]
    point_lines = []
    for row in rows:
        value = classification(row)
        point_lines.append(
            "  {i:%d,t:%.2f,s:%s,u:%s,k:%s}"
            % (
                ISSUE_INDEX[str(value["main_issue"])],
                INTENSITY.get(str(value.get("intensity")), 0.66),
                js_string(str(value.get("summary") or "")[:120]),
                js_string(row.get("url") or ""),
                js_string(STANCE_KEY[str(value["stance"])]),
            )
        )
    return (
        "const ISSUES=[\n" + ",\n".join(issue_lines) + "\n];\n"
        "const SM_RAW = [\n" + ",\n".join(point_lines) + "\n];\n"
        "SM_RAW.forEach(p=>{if(ISSUES[p.i])ISSUES[p.i].n+=1;});\n"
    )


def sample_cards(rows: list[dict[str, Any]], issue: str) -> str:
    candidates = [
        r for r in rows
        if classification(r)["main_issue"] == issue
        and r.get("url")
        and classification(r).get("article_usable", True)
        and classification(r).get("risk", "low") != "high"
    ]
    candidates.sort(key=lambda r: -float(classification(r).get("confidence") or 0))
    picked: list[dict[str, Any]] = []
    used: set[str] = set()
    for stance in STANCES:
        for row in candidates:
            url = str(row["url"])
            if classification(row)["stance"] == stance and url not in used:
                picked.append(row)
                used.add(url)
                break
        if len(picked) == 2:
            break
    for row in candidates:
        if len(picked) == 2:
            break
        if str(row["url"]) not in used:
            picked.append(row)
            used.add(str(row["url"]))

    return "".join(
        '<div class="sample-card"><div class="meta">{stance} / conf {confidence:.2g}</div>'
        "<p>{summary}</p>{embed}</div>".format(
            stance=html.escape(str(classification(row)["stance"])),
            confidence=float(classification(row).get("confidence") or 0),
            summary=html.escape(str(classification(row).get("summary") or "")),
            embed=embed_html(row["url"]),
        )
        for row in picked
    )


def build_issue_section(rows: list[dict[str, Any]]) -> str:
    blocks = []
    for idx, (issue, desc) in enumerate(ISSUES[:6], start=1):
        subset = [r for r in rows if classification(r)["main_issue"] == issue]
        counts = Counter(str(classification(r)["stance"]) for r in subset)
        total = len(subset)
        segments = []
        legends = []
        for stance in STANCES:
            count = counts[stance]
            if not count:
                continue
            pct = count / total * 100
            label = f"{round(pct)}%" if pct >= 7 else ""
            key = STANCE_KEY[stance]
            segments.append(
                f'<div class="temp-seg {key}" style="width:{pct:.2f}%">{label}</div>'
            )
            legends.append(
                f'<span><i class="{key}"></i>{html.escape(stance)}（{count}件）</span>'
            )
        blocks.append(
            f'<article class="issue-block" id="issue-{idx - 1}">'
            f'<div class="issue-head"><span class="axis-kicker">論点 {idx}</span>'
            f'<h3>{html.escape(issue)}<span class="issue-count">{total}件</span></h3></div>'
            f'<p class="issue-desc">{html.escape(desc)}</p>'
            '<div class="temp-bar-wrap"><div class="temp-bar-label">'
            f'<span>X投稿のスタンス構成</span><span>合計 {total}件</span></div>'
            f'<div class="temp-bar">{"".join(segments)}</div>'
            f'<div class="temp-bar-legend">{"".join(legends)}</div></div>'
            f'<div class="sample-grid">{sample_cards(rows, issue)}</div></article>'
        )
    other = sum(1 for r in rows if classification(r)["main_issue"] == "その他")
    return (
        '<section class="panel conflict-panel"><div class="panel-title">'
        '<h2>6つの論点とXの声</h2><span>論点ごとに立場を読み比べる</span></div>'
        + "".join(blocks)
        + f'<p class="data-method">主要6論点のほか「その他」{other}件も、マップと詳細集計には含めています。</p>'
        + "</section>"
    )


def build_insights_from_counts(
    issues: Counter[str], stances: Counter[str], total: int, collected: int
) -> str:
    top_issue, top_issue_count = issues.most_common(1)[0]
    top_stance, top_stance_count = stances.most_common(1)[0]
    opinion_pct = round(total / collected * 100)
    return f'''<section class="stats insight-stats" aria-label="このテーマの4つの注目ポイント">
      <article class="stat insight-stat">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">🗣️</span><span class="insight-label">分析対象の意見</span></div>
        <strong class="insight-value">{total}<small>件</small></strong>
        <p class="insight-note">収集した{collected}件のうち意見と判定した投稿</p>
        <div class="insight-meter" aria-hidden="true"><i style="width:{opinion_pct}%"></i></div>
      </article>
      <article class="stat insight-stat" data-tone="debate">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">⚖️</span><span class="insight-label">最も多い立場</span></div>
        <strong class="insight-value">{html.escape(top_stance)} {round(top_stance_count / total * 100)}%</strong>
        <p class="insight-note">{top_stance_count}件。4つの立場を同じ意見{total}件から集計</p>
        <div class="insight-meter" aria-hidden="true"><i style="width:{round(top_stance_count / total * 100)}%"></i></div>
      </article>
      <article class="stat insight-stat" data-tone="topic">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">🔥</span><span class="insight-label">最も話された論点</span></div>
        <strong class="insight-value">{html.escape(top_issue)} {top_issue_count}<small>件</small></strong>
        <p class="insight-note">正典の main_issue をそのまま集計</p>
        <div class="insight-meter" aria-hidden="true"><i style="width:{round(top_issue_count / total * 100)}%"></i></div>
      </article>
      <article class="stat insight-stat" data-tone="insight">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">💬</span><span class="insight-label">意見と情報共有</span></div>
        <div class="insight-versus"><span>意見<b>{total}</b></span><em>VS</em><span>情報共有<b>{collected-total}</b></span></div>
        <p class="insight-note">マップ・論点・賛否は意見だけを対象</p>
      </article>
    </section>'''


def build_insights(rows: list[dict[str, Any]], collected: int) -> str:
    issues = Counter(str(classification(r)["main_issue"]) for r in rows)
    stances = Counter(str(classification(r)["stance"]) for r in rows)
    return build_insights_from_counts(issues, stances, len(rows), collected)


def build_details(rows: list[dict[str, Any]]) -> str:
    issues = Counter(str(classification(r)["main_issue"]) for r in rows)
    stances = Counter(str(classification(r)["stance"]) for r in rows)
    intensities = Counter(str(classification(r).get("intensity") or "未設定") for r in rows)
    total = len(rows)

    def table(counter: Counter[str], order: list[str]) -> str:
        body = "".join(
            f"<tr><th>{html.escape(label)}</th><td>{counter[label]}</td></tr>" for label in order
        )
        return (
            f'<div class="table-wrap"><table><tbody>{body}'
            f'<tr><th style="font-weight:900">合計</th><td style="font-weight:900">{total}</td>'
            "</tr></tbody></table></div>"
        )

    issue_table = table(issues, [name for name, _ in ISSUES])
    stance_table = table(stances, list(STANCES))
    intensity_table = table(intensities, ["high", "medium", "low"])
    return (
        '<section class="panel details-panel" id="detail-data">'
        '<div class="panel-title"><h2>詳細データ</h2><span>必要な人向けに折りたたみ</span></div>'
        f'<details open><summary>論点別件数（main_issue）</summary>{issue_table}</details>'
        f'<details><summary>改正への態度（stance）</summary>{stance_table}</details>'
        f'<details><summary>感情の強さ（intensity）</summary>{intensity_table}</details>'
        f'<details><summary>件数の出所</summary><p>ページ上の件数はすべて正典の意見{total}件から'
        ' scripts/build_constitutional_arena.py が生成しています。</p></details></section>'
    )


def _public_counts(data: dict[str, Any]) -> tuple[int, int, Counter[str], Counter[str], Counter[str]]:
    """公開JSONの論点・立場・強度集計をページ生成用に検査して読み込む。"""
    if data.get("theme_id") != THEME:
        raise IssueCountError(f"憲法改正の公開JSONではありません: {data.get('theme_id')}")
    items = {str(item["label"]): item for item in data.get("issues", [])}
    issue_order = [name for name, _desc in ISSUES]
    if set(items) != set(issue_order):
        raise IssueCountError("公開JSONの論点がページ定義と一致しません: " + ", ".join(sorted(items)))
    issues: Counter[str] = Counter()
    stances: Counter[str] = Counter()
    intensities: Counter[str] = Counter()
    for name in issue_order:
        item = items[name]
        count = int(item["count"])
        issues[name] = count
        by_stance = {str(value["label"]): int(value["count"]) for value in item.get("stances", [])}
        if set(by_stance) != set(STANCES) or sum(by_stance.values()) != count:
            raise IssueCountError(f"公開JSONの立場集計が一致しません: {name}")
        stances.update(by_stance)
        by_intensity = {str(value["id"]): int(value["count"]) for value in item.get("intensities", [])}
        if set(by_intensity) != set(INTENSITY) or sum(by_intensity.values()) != count:
            raise IssueCountError(f"公開JSONの強度集計が一致しません: {name}")
        intensities.update(by_intensity)
    collected = int(data["collected_count"])
    opinions = int(data["opinion_count"])
    if sum(issues.values()) != opinions or sum(stances.values()) != opinions or sum(intensities.values()) != opinions:
        raise IssueCountError("公開JSONの意見数と集計値が一致しません")
    return collected, opinions, issues, stances, intensities


def build_details_from_counts(
    issues: Counter[str], stances: Counter[str], intensities: Counter[str], total: int
) -> str:
    def table(counter: Counter[str], order: list[str]) -> str:
        body = "".join(
            f"<tr><th>{html.escape(label)}</th><td>{counter[label]}</td></tr>" for label in order
        )
        return (
            f'<div class="table-wrap"><table><tbody>{body}'
            f'<tr><th style="font-weight:900">合計</th><td style="font-weight:900">{total}</td>'
            "</tr></tbody></table></div>"
        )
    return (
        '<section class="panel details-panel" id="detail-data">'
        '<div class="panel-title"><h2>詳細データ</h2><span>必要な人向けに折りたたみ</span></div>'
        f'<details open><summary>論点別件数（main_issue）</summary>{table(issues, [name for name, _ in ISSUES])}</details>'
        f'<details><summary>改正への態度（stance）</summary>{table(stances, list(STANCES))}</details>'
        f'<details><summary>感情の強さ（intensity）</summary>{table(intensities, ["high", "medium", "low"])}</details>'
        f'<details><summary>件数の出所</summary><p>ページ上の件数はすべて正典の意見{total}件から'
        ' scripts/build_constitutional_arena.py が生成しています。</p></details></section>'
    )


def add_featured_posts(page: str, rows: list[dict], data: dict) -> str:
    """本文照合した投稿を図解に添え、山の詳細と相互リンクする。"""
    import hashlib
    selected = json.loads((ROOT / "data/constitutional-amendment-featured-posts.json").read_text())["items"]
    by_key = {hashlib.sha256(str(r["tweet_id"]).encode()).hexdigest(): r for r in rows}
    issue_ids = {it["label"]: it["id"] for it in data["issues"]}
    page = re.sub(r"<!-- FEATURED_POSTS_START -->.*?<!-- FEATURED_POSTS_END -->", "", page, flags=re.S)
    def card(match):
        art = match.group(0)
        issue = re.search(r'data-alt="([^"]+)"', art).group(1)
        iid = issue_ids[issue]
        art = re.sub(r' id="figure-[^"]+"', '', art, count=1)
        art = art.replace('<article ', f'<article id="figure-{iid}" ', 1)
        samples = []
        for item in selected:
            if item["issue"] != issue:
                continue
            row = by_key.get(item["post_key"])
            if row is None or classification(row)["main_issue"] != issue or hashlib.sha256(row["text"].encode()).hexdigest() != item["text_sha256"]:
                raise IssueCountError("代表投稿の本文・論点が変わっています: " + item["post_key"])
            samples.append('<div class="featured-post"><strong>' + html.escape(item["label"]) + '</strong><p>' + html.escape(item["summary"]) + '</p>' + embed_html(row["url"]) + '</div>')
        if len(samples) != 2:
            raise IssueCountError("図解には確認済み投稿2件が必要です: " + issue)
        extra = '<!-- FEATURED_POSTS_START --><div class="featured-posts">' + ''.join(samples) + '</div><a class="featured-issue-link" href="#' + iid + '">この論点の内訳を見る →</a><!-- FEATURED_POSTS_END -->'
        return art.replace('</article>', extra + '</article>')
    page = re.sub(r'<article[^>]*class="explainer-card"[^>]*>.*?</article>', card, page, flags=re.S)
    css = '<!-- FEATURED_POSTS_START --><style>#explainer-section .explainer-grid{grid-template-columns:1fr}#explainer-section .explainer-card{cursor:default;scroll-margin-top:140px}.featured-posts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;padding:16px}.featured-post{min-width:0;border:1px solid #dce3ef;border-radius:10px;padding:14px;font-size:14px;line-height:1.7;overflow-wrap:anywhere}.featured-post p{margin:8px 0}.featured-post iframe{max-width:100%!important}.featured-issue-link{display:inline-block;margin:0 16px 18px;font-weight:700}@media(max-width:600px){.featured-posts{grid-template-columns:1fr}}</style><!-- FEATURED_POSTS_END -->'
    page = page.replace('<section class="panel" id="explainer-section">', css + '<section class="panel" id="explainer-section">')
    page = page.replace("card.addEventListener('click',function(){", "card.addEventListener('click',function(e){if(e.target.tagName!=='IMG')return;")
    return page


# 論点ごとの図解画像。キーは山なみの issue id、値は (画像ファイルの接尾辞, ラベル)。
# ファイル名の接尾辞とissue idの接尾辞が一致しない2件（procedure→process、
# deliberation→information）があるため、決め打ちで対応づける。「その他」は図解を持たない。
LANDING_IMAGE_BY_ISSUE_ID = {
    "constitutional-amendment-general": ("general", "改憲全般"),
    "constitutional-amendment-article9": ("article9", "9条・自衛隊"),
    "constitutional-amendment-emergency": ("emergency", "緊急事態条項"),
    "constitutional-amendment-referendum": ("referendum", "国民投票・広告"),
    "constitutional-amendment-procedure": ("process", "政党・発議手続き"),
    "constitutional-amendment-deliberation": ("information", "情報・議論の質"),
}


def _landing_image_html(slug: str, label: str) -> str:
    path = f"images/topics/constitutional-amendment/constitutional-infographic-wide-{slug}.webp"
    return (
        f'<div class="explainer-card landing-image" data-img="{path}" data-alt="{label}">'
        f'<img src="{path}" alt="論点図解：{label}" loading="lazy"></div>'
    )


def apply_landing_images(page: str) -> str:
    """論点ごとの図解画像を、山なみ再生成後の各論点パネルへ差し戻す。

    render_planet()（build_planet_page_preview.py、10テーマ共通）は憲法改正専用の
    画像を知らないため、apply_planet_counts() が山なみ区画（PLANET_SECTION）全体を
    作り直すたびにこの画像が消える。もとは「このテーマを読み解く、6つの論点」という
    別建てのカード（explainer-section）にあったが、山なみの各論点パネルと内容が
    重複するため、起承転結の再構成（課題69・オーナー指摘、fukushuto の
    apply_landing_images() と同型）でこちらへ一本化した。フォールバック側（無JS用の
    #fallback 配下）と、実際の操作画面を作るJS（drawPanel相当）の両方に差し戻す。
    """
    def add_to_fallback(m: re.Match) -> str:
        issue_id, heading = m.group(1), m.group(0)
        found = LANDING_IMAGE_BY_ISSUE_ID.get(issue_id)
        if not found:
            return heading
        slug, label = found
        return heading + _landing_image_html(slug, label)

    page, n = re.subn(
        r'<section class="landing-panel" id="fb-(constitutional-amendment-[a-z0-9]+)"[^>]*>\s*<h2>[^<]*</h2>',
        add_to_fallback,
        page,
    )
    expected_panels = len(LANDING_IMAGE_BY_ISSUE_ID) + 1  # 「その他」を含む全landing-panel数
    if n != expected_panels:
        raise IssueCountError(
            f"論点画像(フォールバック側): landing-panelが{expected_panels}件必要です（{n}件）"
        )

    slug_map_js = ",".join(f'"{k}":"{v[0]}"' for k, v in LANDING_IMAGE_BY_ISSUE_ID.items())
    old_draw_panel_head = (
        "  const it = issues[st.landed];\n"
        "  const n = m.counts[it.id];\n"
        "  let h = '<h2>'+it.icon+' '+it.label+'</h2>'"
    )
    # 画像パスは先に1つの変数へ組み立ててから src / data-img へ埋め込む。
    # "images/…-" のように末尾が結合前で切れた断片を直接 src="…" の形で書くと、
    # validate_theme_seo.py の参照チェックが実在しないパスとして誤検知する
    # （fukushuto・consumption-tax-cutの起承転結の再構成で発見、課題69）。
    new_draw_panel_head = (
        "  const it = issues[st.landed];\n"
        "  const n = m.counts[it.id];\n"
        "  const caImgSlug = {" + slug_map_js + "}[it.id];\n"
        "  const caImgPath = caImgSlug ? ('images/topics/constitutional-amendment/constitutional-infographic-wide-'+caImgSlug+'.webp') : '';\n"
        "  const caImgHtml = caImgSlug ? ('<div class=\"explainer-card landing-image\" data-img=\"'+caImgPath+'\" data-alt=\"'+it.label+'\">'\n"
        "    +'<img src=\"'+caImgPath+'\" alt=\"論点図解：'+it.label+'\" loading=\"lazy\"></div>') : '';\n"
        "  let h = '<h2>'+it.icon+' '+it.label+'</h2>' + caImgHtml"
    )
    if old_draw_panel_head not in page:
        raise IssueCountError("論点画像(drawPanel側): JSテンプレートの差し込み位置が見つかりません")
    page = page.replace(old_draw_panel_head, new_draw_panel_head, 1)
    return page


def apply_planet_counts(page: str, collected: int, total: int, issues: Counter,
                        stances: Counter, intensities: Counter) -> str:
    """正典との集計一致と再読ゲートを確認し、山なみと残す集計を同時に更新する。"""
    if __package__:
        from .build_planet_page_preview import bpd, build_section, render_planet, split_prototype, build_background
    else:
        from build_planet_page_preview import bpd, build_section, render_planet, split_prototype, build_background
    rows, canonical_collected, _, period = load_canon(None)
    expected = (canonical_collected, len(rows),
                Counter(classification(r)["main_issue"] for r in rows),
                Counter(classification(r)["stance"] for r in rows),
                Counter(classification(r)["intensity"] for r in rows))
    if (collected, total, issues, stances, intensities) != expected:
        raise IssueCountError("山なみと集計の入力が正典に一致しません")
    data = bpd.build(THEME)
    cfg = bpd.yaml.safe_load((ROOT / "configs/planet" / f"{THEME}.yaml").read_text())
    failures = bpd.independence_gate(data, cfg)
    if failures:
        raise IssueCountError("山なみの再読・独自性検査に不合格: " + " / ".join(failures))
    block = build_section(split_prototype(render_planet(bpd.stabilize(data)))).replace(".chart-box svg rect:first-of-type", ".chart-box svg > rect:first-of-type")
    page = replace_once(page, r"<!-- PLANET_SECTION_START -->.*?<!-- PLANET_SECTION_END -->",
                        block, "山なみ全体", flags=re.S)
    page = replace_once(page, r'<span class="conclusion-count"><b>\d+</b>件</span>',
                        f'<span class="conclusion-count"><b>{issues["改憲全般"]}</b>件</span>', "議論の中心")
    page = replace_once(page,
        r'Yahooリアルタイム検索で取得した公開投稿 \d+件のうち、\s*意見と判定した\d+件を分析対象としています。',
        f'Yahooリアルタイム検索で取得した公開投稿 {collected}件のうち、意見と判定した{total}件を分析対象としています。',
        "調査条件の件数", flags=re.S)
    page = replace_once(page, r'<section class="panel details-panel" id="detail-data">.*?</section>',
                        build_details_from_counts(issues, stances, intensities, total), "詳細データ", flags=re.S)
    page = replace_once(page, r'（取得期間: .*?／', f'（取得期間: {period}／', "取得期間")
    page = replace_once(page,
        r'(?<=<!-- RESEARCH_CONDITIONS_END -->).*?(?=<!-- PLANET_SECTION_START -->)',
        "\n" + build_background(THEME) + "\n", "背景と確認事項", flags=re.S)
    config = json.loads(CONFIG.read_text())
    for card in config["issue_counts"]["cards"]:
        count = sum(issues[str(issue)] for issue in card["main_issue"])
        page = replace_once(page,
            rf'<span class="explainer-count" id="issue-count-{THEME}-{card["slug"]}">\d+件</span>',
            span_html(THEME, str(card["slug"]), count), f'論点カード {card["slug"]}')
    page = add_featured_posts(page, rows, data)
    page = apply_landing_images(page)
    return page.replace("<span>SNSの声を見る前に</span>", "<span>ここまで読んだうえで</span>")


def apply_public_counts(page: str, public_theme: Path = PUBLIC_THEME) -> str:
    """候補公開JSONを正典に、ページ上の集計表示を貼り直す。"""
    collected, total, issues, stances, intensities = _public_counts(
        json.loads(public_theme.read_text(encoding="utf-8"))
    )
    if "<!-- PLANET_SECTION_START -->" in page:
        if __package__:
            from .public_registry_common import build_theme_json, dumps_theme_json
        else:
            from public_registry_common import build_theme_json, dumps_theme_json
        if dumps_theme_json(json.loads(public_theme.read_text())) != dumps_theme_json(build_theme_json(THEME)):
            raise IssueCountError("公開JSONが現在の正典・照合資料と一致しません")
        return apply_planet_counts(page, collected, total, issues, stances, intensities)
    lead = (
        f'<p class="lead">Yahooリアルタイム検索で取得した公開投稿{collected}件のうち、'
        f'意見と判定した{total}件を分析対象としています。AIが主要6論点とその他に整理しました。'
        '世論調査ではなく、SNS反応サンプルの論点比較です。</p>'
    )
    page = replace_once(page, r'<p class="lead">.*?</p>', lead, "ヒーローの母数表記", flags=re.S)
    page = replace_once(
        page, r'<span class="conclusion-count"><b>\d+</b>件</span>',
        f'<span class="conclusion-count"><b>{issues["改憲全般"]}</b>件</span>', "議論の中心",
    )
    page = replace_once(
        page,
        r'Yahooリアルタイム検索で取得した公開投稿 \d+件のうち、\s*意見と判定した\d+件を分析対象としています。',
        f'Yahooリアルタイム検索で取得した公開投稿 {collected}件のうち、意見と判定した{total}件を分析対象としています。',
        "調査条件の件数", flags=re.S,
    )
    page = replace_once(
        page, r'<section class="stats insight-stats".*?</section>',
        build_insights_from_counts(issues, stances, total, collected), "注目ポイント", flags=re.S,
    )
    page = replace_once(
        page, r'<div class="panel-title"><h2>SNS反応マップ</h2><span>.*?</span></div>',
        f'<div class="panel-title"><h2>SNS反応マップ</h2><span>意見{total}件 | セクター=main_issue / '
        '中心に近いほど冷静 / 色=立場 | ホバーで詳細・クリックでXへ</span></div>', "マップ見出し",
    )
    page = replace_once(
        page, r'<section class="panel details-panel" id="detail-data">.*?</section>',
        build_details_from_counts(issues, stances, intensities, total), "詳細データ", flags=re.S,
    )
    page = replace_once(
        page, r'主要6論点のほか「その他」\d+件も、マップと詳細集計には含めています。',
        f'主要6論点のほか「その他」{issues["その他"]}件も、マップと詳細集計には含めています。',
        "その他の件数", flags=re.S,
    )
    return page


def replace_once(source: str, pattern: str, replacement: str, label: str, *, flags: int = 0) -> str:
    updated, count = re.subn(pattern, lambda _: replacement, source, count=1, flags=flags)
    if count != 1:
        raise IssueCountError(f"{label}: 1箇所だけ一致する必要があります（{count}箇所）")
    return updated


def build(
    *,
    check: bool = False,
    input_path: Path | None = None,
    html_template: Path | None = None,
    output_html: Path | None = None,
) -> tuple[list[str], bool]:
    rows, collected, sample_file, period = load_canon(input_path)
    total = len(rows)
    issue_counts = Counter(str(classification(r)["main_issue"]) for r in rows)
    stance_counts = Counter(str(classification(r)["stance"]) for r in rows)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    template = html_template or PAGE
    destination = output_html or PAGE
    before = template.read_text(encoding="utf-8")
    page = before
    if "<!-- PLANET_SECTION_START -->" in page:
        if input_path is not None:
            sample = yaml.safe_load((ROOT / "THEMES.yaml").read_text())["themes"][THEME]["sample_file"]
            if json.loads(input_path.read_text()) != json.loads((ROOT / sample).read_text()):
                raise IssueCountError("山なみの候補入力が正典の全レコードと一致しません")
        intensities = Counter(str(classification(r)["intensity"]) for r in rows)
        page = apply_planet_counts(page, collected, total, issue_counts, stance_counts, intensities)
        changed = page != before
        if not check and (changed or destination != template):
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(page, encoding="utf-8")
        return [f"山なみ: 収集{collected}件 / 意見{total}件（再読ゲート確認済み）"], changed

    lead = (
        f'<p class="lead">Yahooリアルタイム検索で取得した公開投稿{collected}件のうち、'
        f'意見と判定した{total}件を分析対象としています。AIが主要6論点とその他に整理しました。'
        '世論調査ではなく、SNS反応サンプルの論点比較です。</p>'
    )
    page = replace_once(page, r'<p class="lead">.*?</p>', lead, "ヒーローの母数表記", flags=re.S)
    page = replace_once(
        page,
        r'<span class="conclusion-count"><b>\d+</b>件</span>',
        f'<span class="conclusion-count"><b>{issue_counts["改憲全般"]}</b>件</span>',
        "議論の中心",
    )
    research = (
        '<!-- RESEARCH_CONDITIONS_START -->\n'
        '<aside class="research-conditions" aria-label="SNSデータの調査条件" '
        'style="padding:16px min(6vw,72px);background:#fff;border-bottom:1px solid var(--line);'
        'font-size:13px;line-height:1.8;color:var(--muted);">\n'
        '<p style="max-width:1000px;margin:0 auto;"><strong style="color:var(--ink);">'
        f'このマップの元データ:</strong> Yahooリアルタイム検索で取得した公開投稿 {collected}件のうち、'
        f'意見と判定した{total}件を分析対象としています。<br>\n'
        # 確認表示は <span class="review-note"> で囲む。scripts/seo/apply_review_note.py が
        # data/review-ledger.json に合わせて中身を書き分け、
        # verify_number_provenance.py がこの囲みだけを検査から外す。
        # 囲みを落とすと再生成のたびに検査が落ちる。
        f'  （取得期間: {period}／'
        '<span class="review-note">AI分類。代表投稿は編集部が選定</span>）<br>\n'
        '  <strong>社会全体の世論調査ではありません。</strong></p>\n'
        '</aside>\n<!-- RESEARCH_CONDITIONS_END -->'
    )
    page = replace_once(
        page,
        r'<!-- RESEARCH_CONDITIONS_START -->.*?<!-- RESEARCH_CONDITIONS_END -->',
        research,
        "調査条件",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<section class="stats insight-stats".*?</section>',
        build_insights(rows, collected),
        "注目ポイント",
        flags=re.S,
    )
    # 「SNS投稿の収集方法」の本文はここでは作らない。
    # configs/theme-seo.json の collection を apply_theme_trust.py が {total} / {opinions} を
    # 解決して書き込む。昇格処理はビルダーの後に apply_theme_trust.py を呼ぶため、両方が
    # 別々の文言で同じ段落を書くと、次にビルダーを流したとき差分ありのまま止まる
    # （2026-08-08 に高齢者免許でも同じ事故が起きた）。書き手を1つに保ち、既存の段落を残す。
    existing_method = re.search(r"<h3>SNS投稿の収集方法</h3>\s*<p>.*?</p>", page, re.S)
    if not existing_method:
        raise SystemExit("ERROR: 収集方法の段落が見つかりません")
    # 「収集・分類で分かったこと」も同じ理由で作らず、既存のものをそのまま残す。
    # 書き手は configs/theme-seo.json の observations と apply_theme_trust.py。
    # ここで落とすと、ビルダーを流すたびに分析メモが消えて差分ありのまま止まる。
    existing_observations = re.search(
        r'<h3>収集・分類で分かったこと</h3>\s*<ul class="article-trust-observations">.*?</ul>',
        page,
        re.S,
    )
    observations_block = (
        f"\n    {existing_observations.group(0)}" if existing_observations else ""
    )
    trust_method = (
        '<div class="article-trust-method">\n'
        f'    {existing_method.group(0)}\n'
        '    <h3>AIを使用した工程</h3>\n'
        '    <p>収集後の投稿について、AIを関連性・意見性の判定、論点・立場・表現強度の分類、'
        '要旨作成の補助に使用しています。ページ内にAI生成の図解・漫画がある場合は、その制作補助にも'
        '使用しています。AIによる分類には誤りや偏りが含まれる可能性があります。</p>'
        f'{observations_block}\n'
        '  </div>'
    )
    page = replace_once(
        page,
        r'<div class="article-trust-method">.*?</div>',
        trust_method,
        "収集方法",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<div class="panel-title"><h2>SNS反応マップ</h2><span>.*?</span></div>',
        f'<div class="panel-title"><h2>SNS反応マップ</h2><span>意見{total}件 | セクター=main_issue / '
        '中心に近いほど冷静 / 色=立場 | ホバーで詳細・クリックでXへ</span></div>',
        "マップ見出し",
    )
    page = replace_once(
        page,
        r'const ISSUES=.*?(?=const colors=)',
        build_map_data(rows),
        "SM_RAW と ISSUES",
        flags=re.S,
    )
    page = page.replace("P.forEach((p,j)=>", "SM_RAW.forEach((p,j)=>")
    if "main_issue の小セクター同士でラベルが重ならないよう離す" not in page:
        page = replace_once(
            page,
            r"    const rad=v\.mid\*Math\.PI/180,lx=CX\+R_LBL\*Math\.cos\(rad\),ly=CY\+R_LBL\*Math\.sin\(rad\),c=Math\.cos\(rad\);",
            "    const rad=v.mid*Math.PI/180,lx=CX+R_LBL*Math.cos(rad),c=Math.cos(rad);\n"
            "    let ly=CY+R_LBL*Math.sin(rad);\n"
            "    // main_issue の小セクター同士でラベルが重ならないよう離す\n"
            "    if(i===5)ly-=18;if(i===6)ly+=18;",
            "マップのラベル衝突回避",
        )
    page = replace_once(
        page,
        r'<section class="panel conflict-panel">.*?(?=<section class="panel background-panel">)',
        build_issue_section(rows) + "\n",
        "論点別の声",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<section class="panel details-panel" id="detail-data">.*?</section>',
        build_details(rows),
        "詳細データ",
        flags=re.S,
    )

    # 6枚のカード順は投票 choiceIdx と同じなので変更せず、件数だけ正典から更新する。
    cards = config["issue_counts"]["cards"]
    if len(cards) != 6:
        raise IssueCountError(f"論点カードは6枚である必要があります: {len(cards)}枚")
    for card in cards:
        count = sum(issue_counts[str(issue)] for issue in card["main_issue"])
        page = replace_once(
            page,
            rf'<span class="explainer-count" id="issue-count-{THEME}-{card["slug"]}">\d+件</span>',
            span_html(THEME, str(card["slug"]), count),
            f'論点カード {card["slug"]}',
        )

    if page.count("const SM_RAW = [") != 1 or page.count("SM_RAW.forEach(p=>") != 1:
        raise IssueCountError("SM_RAW の生成ブロックが1箇所ではありません")
    if sum(issue_counts.values()) != total or sum(stance_counts.values()) != total:
        raise IssueCountError("論点またはスタンスの合計が意見件数と一致しません")

    changed = page != before
    if not check and (changed or destination != template):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(page, encoding="utf-8")
    lines = [
        f"出所: {sample_file}（収集{collected}件 → 意見{total}件 / 取得期間 {period}）",
        "論点: " + " / ".join(f"{name}={issue_counts[name]}" for name, _ in ISSUES),
        "賛否: " + " / ".join(f"{stance}={stance_counts[stance]}" for stance in STANCES),
        f"マップ: {total}点 / 論点カード: {len(cards)}枚 / スタンス: {len(STANCES)}種",
    ]
    return lines, changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="書き換えず、差分があれば exit 1")
    parser.add_argument("--public-counts-only", action="store_true", help="公開JSONからページの集計表示を貼り直す")
    parser.add_argument("--input", type=Path, help="正典の代わりに読む累積候補（adapter用）")
    parser.add_argument("--html-template", type=Path, help="読み込むHTML（既定は公開ページ）")
    parser.add_argument("--output-html", type=Path, help="書き出し先（既定は読み込んだHTML）")
    args = parser.parse_args()
    candidate_args = (args.input, args.html_template, args.output_html)
    if args.public_counts_only:
        if args.check or args.input or args.html_template:
            parser.error("--public-counts-onlyは--output-html以外と併用できません")
        target = args.output_html or PAGE
        try:
            target.write_text(apply_public_counts(target.read_text(encoding="utf-8")), encoding="utf-8")
        except (IssueCountError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"updated public JSON counts in {target}")
        return 0
    if args.check and any(candidate_args):
        parser.error("--checkは公開ページと正典の一致確認専用です")
    if any(candidate_args) and not all(candidate_args):
        parser.error("候補生成では--input/--html-template/--output-htmlをすべて指定してください")
    try:
        lines, changed = build(
            check=args.check,
            input_path=args.input,
            html_template=args.html_template,
            output_html=args.output_html,
        )
    except (IssueCountError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("\n".join(lines))
    print("UPDATE" if changed else "OK")
    if args.check and changed:
        print("NG  ページが正典から生成した内容と一致しません", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
