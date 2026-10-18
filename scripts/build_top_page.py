#!/usr/bin/env python3
"""トップページ（docs/index.html）を configs/top-page.json と正典から生成する。

入力:
- configs/top-page.json … 手書きの文言（見出し・疑問・1行の答え・並び順・画像の登録）
- THEMES.yaml / data/public/catalog.json … 件数・更新日（sync_portal_stats.compute_stats と同じ経路）
- GROWTH.yaml … 注目枠の選定は refresh_featured_slots と同じ規則（意見300件以上・updated_at 順）
- configs/{テーマ}-opening.json … 「いまの段階」を日付から計算する

出力は sync_portal_stats.py / refresh_featured_slots.py / verify_top_page.py が読む
目印（id・class・正規表現）をそのまま保つ。生成後に sync_portal_stats.py を流しても
差分が出ないことを tests/test_top_page_build.py が確かめる。

使い方:
  python3 scripts/build_top_page.py                 # docs/index.html を書き換える
  python3 scripts/build_top_page.py --check         # 差分があれば exit 1（書き換えない）
  python3 scripts/build_top_page.py --output /tmp/x.html --as-of 2026-10-15
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sync_portal_stats import (  # noqa: E402
    INDEX_HTML,
    THEMES_YAML,
    PortalStatsError,
    compute_stats,
    parse_themes_yaml,
    select_featured_themes,
)
from refresh_featured_slots import (  # noqa: E402
    _question_line,
    render_feature_card,
    render_question_card,
)

CONFIG_PATH = ROOT / "configs" / "top-page.json"
GROWTH_YAML = ROOT / "GROWTH.yaml"

e = html_lib.escape


class TopPageError(RuntimeError):
    """設定が正典と食い違うときの例外。"""


# ---------------------------------------------------------------- phase rules


def _d(value: Any) -> date | None:
    return date.fromisoformat(str(value)) if value else None


def _mmdd(value: date) -> str:
    return f"{value.month}月{value.day}日"


def _load_opening(theme_id: str) -> dict[str, Any]:
    path = ROOT / "configs" / f"{theme_id}-opening.json"
    return json.loads(path.read_text(encoding="utf-8"))


PHASE_RULES = {"consumption-tax-cut", "constitutional-amendment", "koshitsu-tenpakai", "fukushuto", "henoko-student-accident", "bukatsu-chiiki"}


def phase_text(theme_id: str, rule: dict[str, Any], today: date) -> str:
    """「いまの段階」の短い文。static ならそのまま、rule なら日付から決める。"""
    if "static" in rule:
        return str(rule["static"])
    name = str(rule.get("rule") or "")
    if name not in PHASE_RULES:
        raise TopPageError(f"{theme_id}: 未知の phase rule {name!r}（使えるのは {sorted(PHASE_RULES)}）")
    cfg = _load_opening(name)
    if name == "consumption-tax-cut":
        law = cfg["law"]
        enacted, start, end = _d(law.get("enacted_on")), _d(law.get("start_on")), _d(law.get("end_on"))
        if not enacted:
            if start and today >= start:
                return "引下げ開始の予定日を過ぎました。法律の成立は未確認"
            return "法律案を国会で審議中。まだ成立していません"
        if start and today < start:
            return "法律は成立。引下げはまだ始まっていません"
        if end and today <= end:
            return "食料品の税率を引下げ中"
        return "引下げの期間は終了"
    if name == "constitutional-amendment":
        return str(cfg["status"]["text"]).rstrip("。")
    if name in {"koshitsu-tenpakai", "fukushuto"}:
        law = cfg["law"]
        enforce, confirmed = _d(law.get("enforcement_on")), _d(law.get("enforcement_confirmed_on"))
        subject = "改正法" if name == "koshitsu-tenpakai" else "法律"
        tail = "" if name == "koshitsu-tenpakai" else "。指定の時期は未定"
        if enforce and today < enforce:
            verb = "施行" if name == "koshitsu-tenpakai" else "施行予定"
            return f"{subject}は{_mmdd(enforce)}に{verb}{tail}"
        if confirmed:
            return f"{subject}は施行済み{tail}"
        return f"施行予定日を過ぎました。施行後の条文は未確認{tail}"
    if name == "henoko-student-accident":
        report = cfg["report"]
        published, checked = _d(report.get("published_on")), _d(report.get("content_checked_on"))
        if not published:
            return "事故調査報告書は未公表"
        if not checked:
            return "事故調査報告書が公表されました。内容は確認中"
        return "事故調査報告書は公表済み"
    if name == "bukatsu-chiiki":
        p = cfg["period"]
        zf, zt, kf, kt = _d(p["zenki_from"]), _d(p["zenki_to"]), _d(p["kouki_from"]), _d(p["kouki_to"])
        if today < zf:
            return "国が重点的に支援する改革推進期間"
        if today <= zt:
            year = (today.year - zf.year) + (1 if (today.month, today.day) >= (zf.month, zf.day) else 0)
            return f"改革実行期間の前期（{year}年目）"
        if today <= kt:
            return "改革実行期間の後期"
        return "改革実行期間は終了。その後の方針は未確認"
    raise TopPageError(f"{theme_id}: 未知の phase rule {name!r}")


# ---------------------------------------------------------------- rendering


def render_head(cfg: dict[str, Any]) -> str:
    h = cfg["head"]
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="google-site-verification" content="m7TnCK7r49LynKemf0lmuJkzY4MoTTHDFgL3fW2bPlc">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{e(h['description'])}">
  <meta property="og:site_name" content="SNS反応まっぷ">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{e(h['og_title'])}">
  <meta property="og:description" content="{e(h['og_description'])}">
  <meta property="og:url" content="https://sns-reaction-map.jp/">
  <meta property="og:image" content="https://sns-reaction-map.jp/ogp/default.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{e(h['og_title'])}">
  <meta name="twitter:description" content="{e(h['twitter_description'])}">
  <meta name="twitter:image" content="https://sns-reaction-map.jp/ogp/default.png">
  <title>{e(h['title'])}</title>
  <link rel="canonical" href="https://sns-reaction-map.jp/">
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <link rel="alternate icon" href="favicon.ico">
  <link rel="apple-touch-icon" href="apple-touch-icon.png">
  <link rel="stylesheet" href="site-tokens.css">
  <link rel="stylesheet" href="home-story.css">
  <link rel="stylesheet" href="top-page.css?v=6">
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2542211932832864" crossorigin="anonymous"></script>
  <script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@type": "WebSite", "name": "SNS反応まっぷ", "url": "https://sns-reaction-map.jp/", "description": h["description"]}, ensure_ascii=False)}</script>
<!-- GA_TAG_START -->
  <script>
    (function(){{
      var allowedHosts = ["sns-reaction-map.jp"];
      if (allowedHosts.indexOf(window.location.hostname) === -1) return;
      window.dataLayer = window.dataLayer || [];
      window.gtag = window.gtag || function(){{window.dataLayer.push(arguments);}};
      var script = document.createElement('script');
      script.async = true;
      script.src = 'https://www.googletagmanager.com/gtag/js?id=G-K10S4YCZFH';
      document.head.appendChild(script);
      window.gtag('js', new Date());
      window.gtag('config', 'G-K10S4YCZFH');
    }})();
  </script>
<!-- GA_TAG_END -->
  <style id="topic-atlas-overview">
    .topic-atlas-legend .protect i{{background:#d94c2c}}.topic-atlas-legend .neutral i{{background:#66758c}}.topic-atlas-legend .promote i{{background:#075ef2}}
    .topic-atlas-issue.protect{{color:#d94c2c;background:#fff7f3}}.topic-atlas-issue.protect:before{{content:"← ";}}.topic-atlas-issue.promote{{color:#075ef2;background:#f2f6ff}}.topic-atlas-issue.promote:before{{content:"→ ";}}.topic-atlas-issue.neutral{{color:#66758c;background:#f8fafc}}.topic-atlas-issue.neutral:before{{content:"・ ";}}
  </style>
</head>
"""


def render_header(cfg: dict[str, Any]) -> str:
    nav = "".join(f'<a href="{e(item["href"])}">{e(item["label"])}</a>' for item in cfg["nav"])
    return (
        '<header class="site-header"><div class="shell header-inner">'
        '<a class="logo" href="index.html" aria-label="SNS反応まっぷ トップ"><img class="logo-mark" src="images/brand/mark.svg" alt=""><span class="logo-text">SNS反応まっぷ</span></a>'
        f'<nav class="main-nav" aria-label="メインナビゲーション">{nav}</nav>'
        '<div class="header-actions"><a class="icon-button" href="https://x.com/sns_hannou_ma" target="_blank" rel="noopener" aria-label="Xを見る">'
        '<svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></a>'
        '<a class="outline-button" href="usage.html">はじめての方</a><a class="primary-button" href="#entries">疑問から選ぶ</a></div></div></header>\n'
    )


def render_hero(cfg: dict[str, Any], stats: dict[str, Any]) -> str:
    h = cfg["hero"]
    lines = []
    for index, line in enumerate(h["h1_lines"]):
        text = e(line)
        lines.append(f'<span class="gradient-text">{text}</span>' if index == h["accent_line"] else text)
    h1 = "<br>".join(lines)
    legend_classes = ["label-pro", "label-con", "label-condition", "label-hold"]
    legend = "".join(
        f'<span class="map-label {cls}">{e(label)}</span>' for cls, label in zip(legend_classes, h["map_legend"])
    )
    s = cfg["stats"]
    last_updated: date = stats["last_updated"]
    updated_short = f"{last_updated.month}/{last_updated.day}"
    return (
        '<section class="hero" id="top"><div class="shell hero-inner">'
        f'<div class="hero-copy"><span class="eyebrow">{e(h["eyebrow"])}</span><h1>{h1}</h1>'
        f'<p class="hero-lead">{e(h["lead"])}</p>'
        f'<p class="hero-note">{e(h["disclaimer"])}</p>'
        f'<a class="hero-cta" href="{e(h["cta"]["href"])}"><span>{e(h["cta"]["label"])}</span><span>›</span></a></div>'
        f'<div class="hero-map-wrap" aria-label="{e(h["map_aria"])}"><span class="map-image-label">{e(h["map_label"])}</span><canvas id="hero-map"></canvas>{legend}</div>'
        "</div></section>\n"
        '<div class="shell"><div class="hero-stats reveal">'
        f'<div class="hero-stat"><small>{e(s["posts_label"])}</small><strong id="hero-total-samples">{stats["total_posts"]:,}</strong><em>{updated_short}更新</em></div>'
        f'<div class="hero-stat"><small>{e(s["opinions_label"])}</small><strong id="hero-total-opinions">{stats["total_opinions"]:,}</strong></div>'
        f'<div class="hero-stat"><small>{e(s["themes_label"])}</small><strong>{stats["theme_count"]}</strong><em>{stats["voting_count"]}テーマで投票受付中</em></div>'
        f'<a class="hero-stat hero-stat-link" href="{e(s["method"]["href"])}"><small>{e(s["method"]["small"])}</small><strong>{e(s["method"]["strong"])}</strong><em>{e(s["method"]["em"])}</em></a>'
        "</div></div>\n"
    )


def render_entries(cfg: dict[str, Any], themes: dict[str, dict[str, Any]], today: date) -> str:
    sec = cfg["entries_section"]
    cards = cfg["topics_section"]["cards"]
    chips = "".join(
        f'<button class="entry-chip" type="button" data-term="{e(term)}">{e(term)}</button>' for term in sec["filter_chips"]
    )
    items = []
    for entry in cfg["entries"]:
        tid = entry["theme_id"]
        href = Path(themes[tid]["html"]).name
        phase = phase_text(tid, entry["phase"], today)
        terms = "".join(f"<span>{e(t)}</span>" for t in entry["search_terms"])
        keywords = " ".join([entry["keywords"], entry["question"], entry["answer"], phase, cards[tid]["category"]])
        items.append(
            f'<a class="entry-card" data-theme="{tid}" data-keywords="{e(keywords)}" href="{e(href)}">'
            '<div class="entry-heading">'
            f'<span class="entry-category">{e(cards[tid]["category"])}</span>'
            f'<h3>{e(entry["question"])}</h3>'
            f'<span class="entry-cta">{e(sec["card_cta"])}</span></div>'
            '<div class="entry-detail">'
            f'<p class="entry-answer">{e(entry["answer"])}</p>'
            f'<p class="entry-phase"><span class="entry-phase-label">{e(sec["phase_label"])}</span>{e(phase)}</p>'
            f'<p class="entry-terms"><span class="entry-terms-label">{e(sec["terms_label"])}</span>{terms}</p></div>'
            '<span class="entry-arrow" aria-hidden="true">→</span></a>'
        )
    return (
        '<section class="section entries reveal" id="entries" aria-labelledby="entries-title">'
        f'<div class="section-head section-head--stack"><span class="story-kicker">{e(sec["kicker"])}</span>'
        f'<h2 class="section-title" id="entries-title">{e(sec["title"])}</h2><p class="section-lead">{e(sec["lead"])}</p></div>'
        '<form class="entry-filter" role="search" onsubmit="return false">'
        f'<label class="entry-filter-label" for="entry-filter-input">{e(sec["filter_label"])}</label>'
        f'<input id="entry-filter-input" class="entry-filter-input" type="search" placeholder="{e(sec["filter_placeholder"])}" autocomplete="off">'
        f'<div class="entry-chips">{chips}<button class="entry-chip entry-chip--all" type="button" data-term="">{e(sec["filter_all"])}</button></div></form>'
        f'<div class="entry-grid">{"".join(items)}</div>'
        f'<p class="entry-empty" hidden>{e(sec["filter_empty"])}</p>'
        "</section>\n"
    )


def render_articles(cfg: dict[str, Any]) -> str:
    """疑問ごとの解説記事（content/articles。scripts/build_articles.py の entry_articles）への入口。記事が無ければ出さない。
    テーマごとに1列（見出しにテーマの画像と名前）。各記事は短い問い（link_label）と1行の答え（link_answer）で並べる。"""
    from build_articles import entry_articles, entry_script, load_theme  # noqa: PLC0415

    sec = cfg["articles_section"]
    articles = entry_articles(root=ROOT)
    if not articles:
        return ""
    cards = cfg["topics_section"]["cards"]
    groups: dict[str, list[Any]] = {}
    for article in articles:
        groups.setdefault(article.theme, []).append(article)
    columns = []
    for theme, group in groups.items():
        card = cards[theme]
        items = "".join(
            f'<li><a href="{e(a.url)}" data-article-entry="top"><span class="ta-q">{e(a.link_label)}</span>'
            f'<span class="ta-a">{e(a.link_answer)}</span></a></li>'
            for a in group
        )
        columns.append(
            '<div class="ta-col">'
            f'<a class="ta-head" href="{e(load_theme(theme).url)}"><img src="{e(card["img"])}" alt="" loading="lazy" width="56" height="56">'
            f'<span><small>{e(card["category"])}</small><strong>{e(card["title"])}</strong></span></a>'
            f'<ul class="ta-list">{items}</ul></div>'
        )
    return (
        '<section class="section top-articles reveal" id="articles" aria-labelledby="articles-title">'
        f'<div class="section-head section-head--stack"><span class="story-kicker">{e(sec["kicker"])}</span>'
        f'<h2 class="section-title" id="articles-title">{e(sec["title"])}</h2><p class="section-lead">{e(sec["lead"])}</p></div>'
        f'<div class="ta-grid">{"".join(columns)}</div>'
        f'<p class="top-articles-all"><a href="articles/index.html" data-article-entry="top">{e(sec["all_label"])} ›</a></p>'
        "</section>\n" + entry_script("top") + "\n"
    )


def render_update_bar(stats: dict[str, Any]) -> str:
    last_updated: date = stats["last_updated"]
    next_update: date | None = stats["next_update"]
    updated_long = f"{last_updated.year}年{last_updated.month}月{last_updated.day}日"
    latest_summary = "・".join(
        f'{title}に<span id="latest-update-delta-{name}">{int(delta):,}</span>件追加' if delta else str(title)
        for name, title, delta in stats["latest_themes"]
    )
    if stats["overdue_count"]:
        next_badge = f'<span class="update-next-badge">更新予定を確認中（{stats["overdue_count"]}テーマ）</span>'
    elif next_update:
        next_badge = f'<span class="update-next-badge">次回更新: {next_update.month}月{next_update.day}日<span id="update-bar-days"></span></span>'
    else:
        next_badge = '<span class="update-next-badge">更新予定を確認中</span>'
    return (
        '<div class="update-bar reveal"><span class="update-pulse"></span>'
        f'<span class="update-body">最終更新: <strong>{updated_long}</strong>（{latest_summary}）</span>{next_badge}</div>\n'
    )


def _card_data(themes: dict[str, dict[str, Any]], cards: dict[str, Any], theme_id: str) -> dict[str, str]:
    href = Path(themes[theme_id]["html"]).name
    card = cards[theme_id]
    return {
        "theme_id": theme_id,
        "href": href,
        "title": themes[theme_id]["title"],
        "question_line": _question_line(ROOT, href),
        "img": card["img"],
        "alt": card["alt"],
        "category": card["category"],
    }


def render_recent(cfg: dict[str, Any], themes: dict[str, dict[str, Any]], stats: dict[str, Any]) -> tuple[str, str, list[str]]:
    sec = cfg["recent_section"]
    cards = cfg["topics_section"]["cards"]
    hero_id, *question_ids = select_featured_themes(themes, stats)
    feature = render_feature_card(_card_data(themes, cards, hero_id), stats["sample_counts"][hero_id])
    questions = "".join(
        render_question_card(_card_data(themes, cards, tid), stats["sample_counts"][tid]) for tid in question_ids
    )
    html = (
        '<section class="section reveal" id="recent"><div class="section-head">'
        f'<h2 class="section-title">{e(sec["title"])}</h2>'
        f'<a class="section-link" href="#topics">{e(sec["more_label"])}</a></div>'
        f'<p class="section-note">{e(sec["note"])}</p>{feature}</section>\n'
        '<section class="section reveal" id="featured-questions"><div class="section-head">'
        f'<h2 class="section-title">{e(sec["questions_title"])}</h2>'
        f'<span class="section-link">{e(sec["questions_link"])}</span></div>'
        f'<div class="question-grid">{questions}</div></section>\n'
    )
    return html, hero_id, question_ids


def render_topics(cfg: dict[str, Any], themes: dict[str, dict[str, Any]], stats: dict[str, Any]) -> str:
    sec = cfg["topics_section"]
    cards = sec["cards"]
    filters = "".join(
        f'<button class="filter{" active" if f["key"] == "all" else ""}" type="button" data-filter="{e(f["key"])}">{e(f["label"])}</button>'
        for f in sec["filters"]
    )
    items = []
    for entry in cfg["entries"]:
        tid = entry["theme_id"]
        card = cards[tid]
        href = Path(themes[tid]["html"]).name
        items.append(
            f'<a class="topic-card" data-category="{e(card["data_category"])}" href="{e(href)}">'
            f'<div class="topic-thumb"><img src="{e(card["img"])}" alt="{e(card["alt"])}" loading="lazy"></div>'
            f'<div class="topic-info"><span class="category">{e(card["category"])}</span>'
            f'<div class="topic-title-row"><h3>{e(card["title"])}</h3></div>'
            f'<div class="topic-meta">収集 <strong id="topic-count-{tid}">{stats["sample_counts"][tid]:,}</strong>件・意見 '
            f'<strong id="topic-opinion-{tid}">{stats["opinion_counts"][tid]:,}</strong>件・主要'
            f'<strong id="topic-issues-{tid}">{stats["issue_counts"][tid]}</strong>論点  |  {e(sec["format_label"])}</div></div></a>'
        )
    landscape = cfg["story_section"]["landscape_img"]
    return (
        f'<div class="topics-band reveal"><img src="{e(landscape)}" alt="" loading="lazy"></div>\n'
        '<section class="section reveal" id="topics"><div class="section-head">'
        f'<h2 class="section-title">{e(sec["title"])}</h2>'
        f'<div class="topics-toolbar">{filters}</div></div><div class="topic-grid">{"".join(items)}</div></section>\n'
    )


def render_atlas(cfg: dict[str, Any], themes: dict[str, dict[str, Any]]) -> str:
    sec = cfg["atlas_section"]
    legend = "".join(f'<span class="{e(item["key"])}"><i></i>{e(item["label"])}</span>' for item in sec["legend"])
    rows = []
    for tid, row in sec["rows"].items():
        href = Path(themes[tid]["html"]).name
        issues = "".join(f'<span class="topic-atlas-issue {e(kind)}">{e(label)}</span>' for kind, label in row["issues"])
        rows.append(
            f'<a class="topic-atlas-row" href="{e(href)}"><span class="topic-atlas-topic">{e(row["label"])}</span>'
            f'<span class="topic-atlas-track">{issues}</span></a>'
        )
    return (
        '<details class="fold reveal" id="atlas"><summary>'
        f'<span class="fold-title">{e(sec["summary"])}</span><span class="fold-hint">開く</span></summary>'
        '<section class="topic-atlas" aria-labelledby="topic-atlas-title">'
        f'<h2 id="topic-atlas-title">{e(sec["title"])}</h2><p>{e(sec["lead"])}</p>'
        f'<div class="topic-atlas-legend" aria-label="論点の立場">{legend}</div>'
        f'<div class="topic-atlas-rows">{"".join(rows)}</div>'
        f'<a class="topic-atlas-more" href="#topics">{e(sec["more_label"])}</a></section></details>\n'
    )


def render_story(cfg: dict[str, Any]) -> str:
    sec = cfg["story_section"]
    steps = []
    for step in sec["steps"]:
        chips = ""
        if step.get("chips"):
            chips = '<div class="story-chips" aria-label="4つの意見分類">' + "".join(f"<span>{e(c)}</span>" for c in step["chips"]) + "</div>"
        steps.append(
            '<div class="story-step">'
            f'<figure class="story-step-art"><img src="{e(step["img"])}" alt="{e(step["alt"])}" loading="lazy"></figure>'
            f'<div class="story-step-copy"><span class="story-number">{e(step["number"])}</span><span class="story-kicker">{e(step["kicker"])}</span>'
            f'<h3>{e(step["title"])}</h3><p>{e(step["text"])}</p>{chips}</div></div>'
        )
    guide = sec["reading_guide"]
    guide_html = (
        f'<div class="reading-guide"><h3>{e(guide["title"])}</h3><ol>'
        + "".join(f"<li>{e(s)}</li>" for s in guide["steps"])
        + f'</ol><a href="{e(guide["link"]["href"])}">{e(guide["link"]["label"])}</a></div>'
    )
    return (
        '<details class="fold reveal" id="how-it-works"><summary>'
        f'<span class="fold-title">{e(sec["summary"])}</span><span class="fold-hint">開く</span></summary>'
        '<div class="home-story home-story--compact">'
        f'<header class="story-intro"><span class="story-kicker">{e(sec["kicker"])}</span><h2>{e(sec["title"])}</h2><p>{e(sec["lead"])}</p></header>'
        f'<div class="story-steps">{"".join(steps)}</div>{guide_html}'
        f'<div class="story-divider"><img src="{e(sec["divider_img"])}" alt="" aria-hidden="true"></div>'
        "</div></details>\n"
    )


def render_footer(cfg: dict[str, Any], themes: dict[str, dict[str, Any]]) -> str:
    f = cfg["footer"]
    theme_links = "".join(
        f'<a href="{e(Path(themes[tid]["html"]).name)}">{e(cfg["topics_section"]["cards"][tid]["title"])}</a>'
        for tid in f["theme_links"]
    )
    site_links = "".join(
        f'<a href="{e(item["href"])}"' + (' target="_blank" rel="noopener"' if item.get("external") else "") + f'>{e(item["label"])}</a>'
        for item in f["site_links"]
    )
    notes = cfg["notes"]
    return (
        f'<aside class="notes reveal"><strong>{e(notes["title"])}</strong>{e(notes["text"])}</aside>\n'
        "</main>\n"
        f'<footer class="site-footer"><img class="footer-landscape" src="{e(f["landscape_img"])}" alt="" loading="lazy"><div class="footer-inner">'
        f'<div><div class="footer-brand"><img src="images/brand/mark.svg" alt=""><h3>SNS反応まっぷ</h3></div><p>{e(f["about"])}</p></div>'
        f'<div><h4>テーマ</h4><div class="footer-links">{theme_links}</div></div>'
        f'<div><h4>サイト情報</h4><div class="footer-links">{site_links}</div></div></div>'
        f'<div class="footer-bottom"><span>{f["copyright"]}</span><span>{e(f["tagline"])}</span></div></footer>\n'
    )


def render_script(stats: dict[str, Any]) -> str:
    next_update: date | None = stats["next_update"]
    next_iso = next_update.isoformat() if next_update else stats["today"].isoformat()
    badge_json = json.dumps(stats["badge_data"], ensure_ascii=False, separators=(",", ":"))
    # 文字列の中身（特に topic-delta の id 付与）は verify_top_page.py が検査する。変えない。
    return (
        "<script>\n(function(){\n"
        "var canvas=document.getElementById('hero-map');\n"
        "if(canvas&&canvas.getContext){var ctx=canvas.getContext('2d');"
        "function rand(seed){var x=Math.sin(seed*999.91)*43758.5453;return x-Math.floor(x)}"
        "function drawMap(){var dpr=Math.min(window.devicePixelRatio||1,2),rect=canvas.getBoundingClientRect();if(!rect.width)return;canvas.width=rect.width*dpr;canvas.height=rect.height*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,rect.width,rect.height);var points=[];var clusters=[{x:.32,y:.38,c:'#1680ff',n:56,s:.16},{x:.67,y:.4,c:'#ff5c31',n:49,s:.15},{x:.42,y:.7,c:'#36b8a3',n:37,s:.13},{x:.64,y:.7,c:'#a153ee',n:31,s:.12}];clusters.forEach(function(g,gi){for(var i=0;i<g.n;i++){var a=rand(i+gi*151)*Math.PI*2,r=Math.sqrt(rand(i+gi*277+8))*g.s;points.push({x:(g.x+Math.cos(a)*r)*rect.width,y:(g.y+Math.sin(a)*r)*rect.height,c:g.c,r:1.2+rand(i+33)*3.2,g:gi})}});ctx.lineWidth=.55;points.forEach(function(p,i){for(var j=i+1;j<points.length;j++){var q=points[j],dx=p.x-q.x,dy=p.y-q.y,dist=Math.sqrt(dx*dx+dy*dy);if(dist<52&&(p.g===q.g||dist<26)){ctx.globalAlpha=.12;ctx.strokeStyle=p.g===q.g?p.c:'#aab8cf';ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.stroke()}}});points.forEach(function(p){ctx.globalAlpha=.8;ctx.fillStyle=p.c;ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fill()});ctx.globalAlpha=1}"
        "drawMap();window.addEventListener('resize',drawMap,{passive:true});}\n"
        "if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches){var obs=new IntersectionObserver(function(entries){entries.forEach(function(en){if(en.isIntersecting){en.target.classList.add('visible');obs.unobserve(en.target)}})},{threshold:.05});document.querySelectorAll('.reveal').forEach(function(el){obs.observe(el)})}else{document.querySelectorAll('.reveal').forEach(function(el){el.classList.add('visible')})}\n"
        "document.querySelectorAll('.filter').forEach(function(btn){btn.addEventListener('click',function(){document.querySelectorAll('.filter').forEach(function(b){b.classList.remove('active')});btn.classList.add('active');var f=btn.dataset.filter;document.querySelectorAll('.topic-card').forEach(function(card){card.style.display=f==='all'||card.dataset.category===f?'grid':'none'})})});\n"
        "(function(){var input=document.getElementById('entry-filter-input'),cards=document.querySelectorAll('.entry-card'),empty=document.querySelector('.entry-empty'),chips=document.querySelectorAll('.entry-chip');if(!input)return;"
        "function norm(s){return (s||'').toLowerCase().replace(/[\\s　]+/g,' ').replace(/％/g,'%').replace(/・/g,' ')}"
        "function apply(){var q=norm(input.value).trim(),words=q?q.split(' ').filter(Boolean):[],shown=0;cards.forEach(function(card){var hay=norm(card.dataset.keywords);var ok=words.every(function(w){return hay.indexOf(w)>=0});card.hidden=!ok;if(ok)shown++});if(empty)empty.hidden=shown>0;chips.forEach(function(c){c.classList.toggle('active',norm(c.dataset.term)===q&&q!=='')});}"
        "input.addEventListener('input',apply);chips.forEach(function(c){c.addEventListener('click',function(){input.value=c.dataset.term;apply();})});})();\n"
        f"(function(){{var next=new Date('{next_iso}T00:00:00+09:00'),now=new Date(),days=Math.ceil((next-now)/864e5),txt=days>0?'（あと'+days+'日）':days===0?'（本日更新予定）':'（予定を確認中）';var el=document.getElementById('update-bar-days');if(el)el.textContent=txt;}})();\n"
        "(function(){\n"
        f"var B={badge_json};\n"
        "var t=new Date();t.setHours(0,0,0,0);"
        "function ago(s){if(!s)return 9999;var d=new Date(s);d.setHours(0,0,0,0);return Math.floor((t-d)/864e5);}"
        "document.querySelectorAll('.feature-card,.topic-card').forEach(function(card){"
        "var data=B[card.getAttribute('href')];if(!data)return;var isFeat=card.classList.contains('feature-card');"
        "var xd=ago(data.xpost),pd=ago(data.pub),ud=ago(data.upd);var txt=null,hot=false;"
        "if(xd<=2){txt='🔥 注目';hot=true;}else if(pd<=14){txt='NEW';}"
        "var old=card.querySelector(isFeat?'.live-pill':'.topic-new');if(old)old.remove();"
        "if(txt){var el=document.createElement('span');el.className=isFeat?'live-pill':'topic-new';if(hot)el.classList.add('hot');el.textContent=txt;var c=card.querySelector(isFeat?'.feature-image':'.topic-thumb');if(c)c.appendChild(el);}"
        "if(!isFeat){var meta=card.querySelector('.topic-meta');if(meta){var f=meta.querySelector('.topic-fresh');if(f)f.remove();if(ud<=7&&data.delta){var fn=document.createElement('span'),countEl=meta.querySelector('[id^=\"topic-count-\"]');fn.className='topic-fresh';if(countEl)fn.id=countEl.id.replace('topic-count-','topic-delta-');fn.textContent=' +'+data.delta+'件 更新';meta.appendChild(fn);}}}"
        "});\n})();\n"
        "})();\n</script>\n"
    )


# ---------------------------------------------------------------- assembly


def validate_config(cfg: dict[str, Any], themes: dict[str, dict[str, Any]]) -> None:
    published = {name for name, theme in themes.items() if theme["published"]}
    entry_ids = [entry["theme_id"] for entry in cfg["entries"]]
    if sorted(entry_ids) != sorted(published):
        raise TopPageError(f"entries のテーマ {sorted(entry_ids)} が公開テーマ {sorted(published)} と一致しません")
    if len(set(entry_ids)) != len(entry_ids):
        raise TopPageError("entries にテーマの重複があります")
    missing_cards = [tid for tid in entry_ids if tid not in cfg["topics_section"]["cards"]]
    if missing_cards:
        raise TopPageError(f"topics_section.cards に無いテーマ: {missing_cards}")
    missing_rows = [tid for tid in entry_ids if tid not in cfg["atlas_section"]["rows"]]
    if missing_rows:
        raise TopPageError(f"atlas_section.rows に無いテーマ: {missing_rows}")
    for entry in cfg["entries"]:
        text = entry["question"] + entry["answer"] + entry["keywords"] + " ".join(entry["search_terms"])
        if re.search(r"\d[\d,]*\s*件", text):
            raise TopPageError(f"{entry['theme_id']}: 疑問・答えに「○件」を書かない（件数は正典から生成する）")
        if re.search(r"\d{1,3}(?:\.\d+)?%", text):
            raise TopPageError(f"{entry['theme_id']}: 半角の % は使わない（全角の ％ にする）")
    for tid, card in cfg["topics_section"]["cards"].items():
        if not (ROOT / "docs" / card["img"]).is_file():
            raise TopPageError(f"{tid}: 画像が無い {card['img']}")


def build_html(cfg: dict[str, Any], *, today: date | None = None) -> str:
    themes = parse_themes_yaml(THEMES_YAML)
    stats = compute_stats(themes, ROOT, today=today, allow_synthetic=True)
    if stats["opinion_counts"] is None:
        raise TopPageError("公開データcatalogが読めない（scripts/build_public_registry.py --all を先に実行する）")
    today = stats["today"]
    validate_config(cfg, themes)
    recent_html, _hero_id, _question_ids = render_recent(cfg, themes, stats)
    parts = [
        render_head(cfg),
        "<body>\n",
        render_header(cfg),
        render_hero(cfg, stats),
        '<main class="shell">\n',
        render_entries(cfg, themes, today),
        render_articles(cfg),
        render_update_bar(stats),
        recent_html,
        render_topics(cfg, themes, stats),
        render_atlas(cfg, themes),
        render_story(cfg),
        render_footer(cfg, themes),
        render_script(stats),
        "</body>\n</html>\n",
    ]
    return "".join(parts)


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, default=INDEX_HTML, help="出力先（既定は docs/index.html）")
    parser.add_argument("--as-of", type=date.fromisoformat, default=None, help="「いまの段階」を計算する日（既定は今日）")
    parser.add_argument("--check", action="store_true", help="出力先と差分があれば exit 1。書き換えない")
    args = parser.parse_args(argv)
    try:
        html = build_html(load_config(), today=args.as_of)
    except (OSError, PortalStatsError, TopPageError, KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    current = args.output.read_text(encoding="utf-8") if args.output.exists() else None
    if args.check:
        if current == html:
            print("OK  docs/index.html は configs/top-page.json と正典から再生成した結果と一致")
            return 0
        print("NG  docs/index.html が再生成の結果と違う（scripts/build_top_page.py を実行する）")
        return 1
    if current == html:
        print(f"変更なし: {args.output}")
        return 0
    args.output.write_text(html, encoding="utf-8")
    print(f"書き出し: {args.output}（{len(html):,}バイト）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
