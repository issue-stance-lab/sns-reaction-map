"""学校あだ名禁止テーマの論点別読書面テンプレート。"""
from __future__ import annotations

import hashlib
import json
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- SCHOOL_NICKNAME_CONNECTED_CONTENT_START -->"
END = "<!-- SCHOOL_NICKNAME_CONNECTED_CONTENT_END -->"


def e(value) -> str:
    return escape(str(value), quote=True)


def sources(items: list[dict]) -> str:
    return '<details class="school-nickname-sources"><summary>出典をひらく</summary><ul>' + "".join(
        f'<li><a href="{e(item["url"])}" target="_blank" rel="noopener noreferrer">{e(item["name"])}</a></li>'
        for item in items
    ) + "</ul></details>"


def reason_posts() -> dict[tuple[str, str], list[dict]]:
    """再読台帳の理由IDへ、正典投稿の要旨とリンクを接続する。"""
    reread = json.loads((ROOT / "data/school-nickname-ban_issues-reread.json").read_text(encoding="utf-8"))
    canonical = json.loads(
        (ROOT / "social-samples/school-nickname-ban_hermes_arena_classified.json").read_text(encoding="utf-8")
    )
    by_key = {
        hashlib.sha256(str(row["tweet_id"]).encode()).hexdigest(): row
        for row in canonical
        if row.get("tweet_id") and row.get("url")
    }
    grouped: dict[tuple[str, str], list[dict]] = {}
    for item in reread["items"]:
        row = by_key.get(item["post_key"])
        if row is None:
            continue
        classification = row.get("classification") or {}
        summary = str(classification.get("summary") or "投稿の要旨は未登録です").strip()
        key = (str(item["main_issue"]), str(item["bucket"]))
        grouped.setdefault(key, []).append(
            {
                "url": row["url"],
                "summary": summary,
                "tweet_id": str(row["tweet_id"]),
            }
        )
    for rows in grouped.values():
        rows.sort(key=lambda row: row["tweet_id"])
    return grouped


def reason_post_cards(rows: list[dict]) -> str:
    try:
        from scripts.x_embed import embed_html
    except ModuleNotFoundError:
        from x_embed import embed_html  # type: ignore[no-redef]

    return "".join(
        '<article class="school-nickname-reason-post" '
        f'data-school-nickname-reason-post-url="{e(row["url"])}">'
        f'<p>{e(row["summary"])}</p>'
        f'<a href="{e(row["url"])}" target="_blank" rel="noopener noreferrer">この理由の投稿をXで読む ↗</a>'
        f'<details class="school-nickname-embed"><summary>ここで投稿を表示</summary>{embed_html(row["url"])}</details>'
        "</article>"
        for row in rows[:2]
    )


def reasons(issue: dict, grouped: dict[tuple[str, str], list[dict]]) -> str:
    sub = issue["sub"]
    if sub["status"] != "reread":
        return (
            f'<p class="school-nickname-empty">{e(sub.get("note", "理由の再読結果は未登録です"))}。'
            "AIが自動でつけた区分はここへ表示しません。</p>"
        )
    rows = []
    for item in sub["items"]:
        cards = reason_post_cards(grouped.get((issue["label"], item["id"]), []))
        empty_cards = '<p class="school-nickname-empty">この理由の代表投稿はありません。</p>'
        rows.append(
            f'<li><details class="school-nickname-reason-detail" data-school-nickname-reason="{e(item["id"])}">'
            f'<summary><span class="school-nickname-reason-row"><span>{e(item["label"])}</span>'
            f'<b id="school-nickname-reason-count-{e(issue["id"])}-{e(item["id"])}">{item["count"]:,}<small>件</small></b></span>'
            f'<span class="school-nickname-reason-track" aria-hidden="true"><i style="width:{item["pct_in_issue"]:.3f}%"></i></span></summary>'
            f'<div class="school-nickname-reason-reading"><p class="school-nickname-note">この理由に分類された投稿を読み直す</p>'
            f'{cards or empty_cards}</div></details></li>'
        )
    return '<ul class="school-nickname-reasons">' + "".join(rows) + "</ul>"


def post_examples(issue_cards_html: str, iid: str) -> str:
    soup = BeautifulSoup(issue_cards_html, "html.parser")
    article = soup.select_one("#issue-" + iid)
    if article is None:
        raise ValueError("連動表示: 論点別X投稿が見つかりません: " + iid)
    out = []
    for sample in article.select(".hermes-sample"):
        link = sample.select_one("blockquote a[href]")
        meta = sample.select_one(".hermes-sample-meta")
        if link is None:
            continue
        url = link["href"]
        quote = sample.select_one("blockquote")
        out.append(
            f'<article class="school-nickname-post" data-school-nickname-post-url="{e(url)}">'
            f'<p>{e(meta.get_text(" ", strip=True) if meta else "代表投稿")}</p>'
            f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">元の投稿をXで読む ↗</a>'
            f'<details class="school-nickname-embed"><summary>ここで投稿を表示</summary>{str(quote) if quote else ""}</details></article>'
        )
    return "".join(out)


def landing_image(fallback_html: str, icon: str, label: str) -> dict:
    soup = BeautifulSoup(fallback_html, "html.parser")
    for heading in soup.select("h2"):
        if heading.get_text(strip=True).startswith(icon):
            node = heading.find_next(class_="landing-image")
            if node and node.get("data-img"):
                return {"src": node["data-img"], "alt": label}
    raise ValueError("連動表示: 図解の原画像がありません: " + label)


def render_templates(data: dict, source: str, index: dict) -> str:
    try:
        from scripts.school_nickname_connected import background_data
    except ModuleNotFoundError:
        from school_nickname_connected import background_data  # type: ignore[no-redef]

    soup = BeautifulSoup(source, "html.parser")
    issue_cards = soup.select_one("#issue-cards")
    fallback = soup.select_one("#fallback")
    if issue_cards is None or fallback is None:
        raise ValueError("連動表示: #issue-cards または #fallback が見つかりません")
    issue_cards_html = str(issue_cards)
    fallback_html = str(fallback)
    claims = {claim["id"]: claim for claim in data["claims"]}
    sunk = {item["id"]: item for item in data["ocean"]["sunk_continents"]}
    checks = {item["id"]: item for item in background_data()["checklist"]["items"]}
    background = background_data()
    timeline = {item["id"]: item for item in background["timeline"]}
    veins = {item["id"]: item for item in data["ocean"].get("veins", [])}
    grouped_reason_posts = reason_posts()
    out = [START]
    for issue in data["issues"]:
        iid = issue["id"]
        connection = index["issues"][iid]
        image = landing_image(fallback_html, issue["icon"], issue["label"])
        out.append(f'<template id="school-nickname-ban-reading-{e(iid)}">')
        out.append(
            '<header class="school-nickname-selected-head"><div><p class="school-nickname-eyebrow">選んだ論点</p>'
            f'<h2>{e(issue["icon"])} {e(issue["label"])}</h2></div>'
            f'<button type="button" class="explainer-card school-nickname-image-action" data-img="{e(image["src"])}" data-alt="{e(image["alt"])}">'
            f'<img src="{e(image["src"])}" alt="" loading="lazy"><span>図解をひらく ↗</span></button></header>'
        )
        out.append(
            '<div class="school-nickname-metrics" aria-live="polite" aria-atomic="true">'
            '<p><strong data-school-nickname-count></strong><span data-school-nickname-mode></span></p>'
            '<p data-school-nickname-ratio></p><p data-school-nickname-zero hidden></p></div>'
            f'<p class="school-nickname-scope-note">{e(index["scope_note"])}</p>'
        )
        out.append(
            '<div class="school-nickname-columns"><section class="school-nickname-opinions" aria-label="意見の理由と投稿">' +
            '<h3>どんな理由で語られている？</h3>' + reasons(issue, grouped_reason_posts) +
            f'<p class="school-nickname-note">{e(index["reason_post_note"])}</p>'
            '<div class="school-nickname-posts"><h3>実際の投稿を読む</h3>'
            '<p class="school-nickname-note">この論点を具体的に読むため、編集部が投稿内容を確認して2件を抜き出しています。分布の代表値ではありません。</p>'
            + post_examples(issue_cards_html, iid) + '</div></section>'
        )
        out.append('<aside class="school-nickname-evidence" aria-label="資料">')
        if connection["check_ids"]:
            out.append(f'<p class="school-nickname-eyebrow">制度の確認 {e(index["background_checked_on"])}</p><h3>この論点に関わる制度は？</h3>')
        for check_id in connection["check_ids"]:
            item = checks[check_id]
            out.append(
                f'<details class="school-nickname-check" data-school-nickname-check="{e(check_id)}"><summary>{e(item["label"])}：{e(item["ask"])}</summary>'
                f'<p id="school-nickname-check-note-{e(check_id)}">{e(item["found"])}</p>{sources(item["sources"])}</details>'
            )
        if connection["shared_concern_ids"]:
            out.append('<h3>同じ心配から、違う結論へ</h3>')
            for concern_id in connection["shared_concern_ids"]:
                concern = veins[concern_id]
                out.append(
                    f'<details class="school-nickname-concern" data-school-nickname-concern="{e(concern_id)}">'
                    f'<summary>{e(concern["shared_concern"])}</summary><p>{e(concern["diverging_reason"])}</p>'
                    f'<p class="school-nickname-note">同じ心配を含む論点：{e("・".join(concern["issue_ids"]))}</p></details>'
                )
        if connection["timeline_ids"]:
            out.append('<h3>制度の経緯</h3><p class="school-nickname-note">国の資料に書かれた経緯と、学校ごとの呼称ルールは分けて読みます。</p>')
            for timeline_id in connection["timeline_ids"]:
                item = timeline[timeline_id]
                out.append(
                    f'<details class="school-nickname-timeline" data-school-nickname-timeline="{e(timeline_id)}">'
                    f'<summary>{e(item["when"])}：{e(item["era"])}</summary><p>{e(item["text"])}</p>{sources(item["sources"])}</details>'
                )
        out.append('<h3>投稿の主張と一次資料</h3>')
        if connection["claim_ids"]:
            out.append(
                f'<p class="school-nickname-note">照合確認日 {e(data["ocean"]["checked_on"])}。'
                '投稿の中から整理した主張を、公的な資料と照らし合わせた結果です。個別の投稿を採点する欄ではありません。</p>'
            )
        else:
            out.append('<p class="school-nickname-empty">この論点に対応する資料照合は、まだ登録されていません。</p>')
        for position, claim_id in enumerate(connection["claim_ids"]):
            claim = claims[claim_id]
            out.append(
                f'<details class="school-nickname-claim" data-school-nickname-claim="{e(claim_id)}"{" open" if position == 0 else ""}>'
                f'<summary>「{e(claim["claim"])}」</summary>'
                f'<span class="school-nickname-verdict">{e(claim["verdict_label"])}</span><p>{e(claim["finding"])}</p>'
                f'{sources(claim["sources"])}</details>'
            )
        if connection["source_only_ids"]:
            out.append('<h3>資料にあり、収集投稿で見つからなかったこと</h3>')
        for source_id in connection["source_only_ids"]:
            item = sunk[source_id]
            out.append(
                f'<details class="school-nickname-source-only" data-school-nickname-source-only="{e(source_id)}"><summary id="school-nickname-source-topic-{e(source_id)}">{e(item["topic"])}</summary>'
                f'<p id="school-nickname-source-life-{e(source_id)}">{e(item["life_impact"])}</p>'
                f'<p id="school-nickname-source-note-{e(source_id)}" class="school-nickname-note">{e(item["sns_note"])} 確認日 {e(item["checked_on"])}</p>'
                f'<details><summary>調べた範囲を見る</summary><p id="school-nickname-source-note-copy-{e(source_id)}">{e(item["sns_note"])}</p></details>'
                f'{sources(item["sources"])}</details>'
            )
        if iid == index["default_issue_id"] and index["global_source_only_ids"]:
            out.append('<h3>全体に関わる資料</h3>')
            for source_id in index["global_source_only_ids"]:
                item = sunk[source_id]
                out.append(
                    f'<details class="school-nickname-source-only" data-school-nickname-global-source-only="{e(source_id)}"><summary id="school-nickname-source-topic-{e(source_id)}">{e(item["topic"])}</summary>'
                    f'<p id="school-nickname-source-life-{e(source_id)}">{e(item["life_impact"])}</p>'
                    f'<p id="school-nickname-source-note-{e(source_id)}" class="school-nickname-note">{e(item["sns_note"])} 確認日 {e(item["checked_on"])}</p>'
                    f'{sources(item["sources"])}</details>'
                )
        out.append('</aside></div></template>')
    return "\n".join(out + [END])
