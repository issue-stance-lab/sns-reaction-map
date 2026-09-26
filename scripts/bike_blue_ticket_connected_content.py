"""自転車テーマの論点別読書面テンプレート。"""
from __future__ import annotations

from html import escape

from bs4 import BeautifulSoup

START = "<!-- BIKE_CONNECTED_CONTENT_START -->"
END = "<!-- BIKE_CONNECTED_CONTENT_END -->"


def e(value) -> str:
    return escape(str(value), quote=True)


def sources(items: list[dict]) -> str:
    return '<details class="bike-sources"><summary>出典をひらく</summary><ul>' + "".join(
        f'<li><a href="{e(item["url"])}" target="_blank" rel="noopener noreferrer">{e(item["name"])}</a></li>'
        for item in items
    ) + "</ul></details>"


def reasons(issue: dict) -> str:
    sub = issue["sub"]
    if sub["status"] != "reread":
        return (
            f'<p class="bike-empty">{e(sub.get("note", "理由の再読結果は未登録です"))}。'
            "AIが自動でつけた区分はここへ表示しません。</p>"
        )
    rows = "".join(
        f'<li><span class="bike-reason-row"><span>{e(item["label"])}</span>'
        f'<b id="bike-reason-count-{e(issue["id"])}-{e(item["id"])}">{item["count"]:,}<small>件</small></b></span>'
        f'<span class="bike-reason-track" aria-hidden="true"><i style="width:{item["pct_in_issue"]:.3f}%"></i></span></li>'
        for item in sub["items"]
    )
    return '<ul class="bike-reasons">' + rows + "</ul>"


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
            f'<article class="bike-post" data-bike-post-url="{e(url)}">'
            f'<p>{e(meta.get_text(" ", strip=True) if meta else "代表投稿")}</p>'
            f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">元の投稿をXで読む ↗</a>'
            f'<details class="bike-embed"><summary>ここで投稿を表示</summary>{str(quote) if quote else ""}</details></article>'
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
    from scripts.bike_blue_ticket_connected import background_data

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
    out = [START]
    for issue in data["issues"]:
        iid = issue["id"]
        connection = index["issues"][iid]
        image = landing_image(fallback_html, issue["icon"], issue["label"])
        out.append(f'<template id="bike-blue-ticket-reading-{e(iid)}">')
        out.append(
            '<header class="bike-selected-head"><div><p class="bike-eyebrow">選んだ論点</p>'
            f'<h2>{e(issue["icon"])} {e(issue["label"])}</h2></div>'
            f'<button type="button" class="explainer-card bike-image-action" data-img="{e(image["src"])}" data-alt="{e(image["alt"])}">'
            f'<img src="{e(image["src"])}" alt="" loading="lazy"><span>図解をひらく ↗</span></button></header>'
        )
        out.append(
            '<div class="bike-metrics" aria-live="polite" aria-atomic="true">'
            '<p><strong data-bike-count></strong><span data-bike-mode></span></p>'
            '<p data-bike-ratio></p><p data-bike-zero hidden></p></div>'
            f'<p class="bike-scope-note">{e(index["scope_note"])}</p>'
        )
        out.append(
            '<div class="bike-columns"><section class="bike-opinions" aria-label="意見の理由と投稿">' +
            '<h3>どんな理由で語られている？</h3>' + reasons(issue) +
            f'<p class="bike-note">{e(index["reason_post_note"])}</p>'
            '<div class="bike-posts"><h3>実際の投稿を読む</h3>'
            '<p class="bike-note">編集部がこの論点全体から選んだ代表例です。賛否の割合を表すものではありません。</p>'
            + post_examples(issue_cards_html, iid) + '</div></section>'
        )
        out.append('<aside class="bike-evidence" aria-label="資料">')
        if connection["check_ids"]:
            out.append(f'<p class="bike-eyebrow">制度の確認 {e(index["background_checked_on"])}</p><h3>この論点に関わる制度は？</h3>')
        for check_id in connection["check_ids"]:
            item = checks[check_id]
            out.append(
                f'<details class="bike-check" data-bike-check="{e(check_id)}"><summary>{e(item["label"])}：{e(item["ask"])}</summary>'
                f'<p id="bike-check-note-{e(check_id)}">{e(item["found"])}</p>{sources(item["sources"])}</details>'
            )
        out.append('<h3>投稿の主張と一次資料</h3>')
        if connection["claim_ids"]:
            out.append(
                f'<p class="bike-note">照合確認日 {e(data["ocean"]["checked_on"])}。'
                '収集した投稿から選んだ主張を資料と照合しています。掲載した投稿例そのものへの判定ではありません。</p>'
            )
        else:
            out.append('<p class="bike-empty">この論点に対応する資料照合は、まだ登録されていません。</p>')
        for position, claim_id in enumerate(connection["claim_ids"]):
            claim = claims[claim_id]
            out.append(
                f'<details class="bike-claim" data-bike-claim="{e(claim_id)}"{" open" if position == 0 else ""}>'
                f'<summary>「{e(claim["claim"])}」</summary>'
                f'<span class="bike-verdict">{e(claim["verdict_label"])}</span><p>{e(claim["finding"])}</p>'
                f'{sources(claim["sources"])}</details>'
            )
        if connection["source_only_ids"]:
            out.append('<h3>資料にあり、収集投稿で見つからなかったこと</h3>')
        for source_id in connection["source_only_ids"]:
            item = sunk[source_id]
            out.append(
                f'<details class="bike-source-only" data-bike-source-only="{e(source_id)}"><summary id="bike-source-topic-{e(source_id)}">{e(item["topic"])}</summary>'
                f'<p id="bike-source-life-{e(source_id)}">{e(item["life_impact"])}</p>'
                f'<p id="bike-source-note-{e(source_id)}" class="bike-note">{e(item["sns_note"])} 確認日 {e(item["checked_on"])}</p>'
                f'<details><summary>調べた範囲を見る</summary><p id="bike-source-note-copy-{e(source_id)}">{e(item["sns_note"])}</p></details>'
                f'{sources(item["sources"])}</details>'
            )
        if iid == index["default_issue_id"] and index["global_source_only_ids"]:
            out.append('<h3>全体に関わる資料</h3>')
            for source_id in index["global_source_only_ids"]:
                item = sunk[source_id]
                out.append(
                    f'<details class="bike-source-only" data-bike-global-source-only="{e(source_id)}"><summary id="bike-source-topic-{e(source_id)}">{e(item["topic"])}</summary>'
                    f'<p id="bike-source-life-{e(source_id)}">{e(item["life_impact"])}</p>'
                    f'<p id="bike-source-note-{e(source_id)}" class="bike-note">{e(item["sns_note"])} 確認日 {e(item["checked_on"])}</p>'
                    f'{sources(item["sources"])}</details>'
                )
        out.append('</aside></div></template>')
    return "\n".join(out + [END])
