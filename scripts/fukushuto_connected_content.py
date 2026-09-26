"""副首都テーマの論点別読書面を、既存の代表投稿・資料から組み立てる。"""
from __future__ import annotations

from html import escape

from bs4 import BeautifulSoup

START = "<!-- FUKUSHUTO_CONNECTED_CONTENT_START -->"
END = "<!-- FUKUSHUTO_CONNECTED_CONTENT_END -->"


def e(value) -> str:
    return escape(str(value), quote=True)


def sources(items: list[dict]) -> str:
    links = "".join(
        f'<li><a href="{e(item["url"])}" target="_blank" rel="noopener noreferrer">{e(item["name"])}</a></li>'
        for item in items
    )
    return f'<details class="fuk-sources"><summary>出典をひらく</summary><ul>{links}</ul></details>'


def reasons(issue: dict) -> str:
    sub = issue["sub"]
    if sub["status"] != "reread":
        return f'<p class="fuk-empty">{e(sub.get("note", "理由の再読結果は未登録です"))}。AIが自動でつけた区分はここへ表示しません。</p>'
    rows = "".join(
        f'<li><span class="fuk-reason-row"><span>{e(item["label"])}</span>'
        f'<b id="fuk-reason-count-{e(issue["id"])}-{e(item["id"])}">{item["count"]:,}<small>件</small></b></span>'
        f'<span class="fuk-reason-track" aria-hidden="true"><i style="width:{item["pct_in_issue"]:.3f}%"></i></span></li>'
        for item in sub["items"]
    )
    return f'<ul class="fuk-reasons">{rows}</ul>'


def post_examples(issue_cards_html: str, iid: str) -> str:
    soup = BeautifulSoup(issue_cards_html, "html.parser")
    article = soup.select_one("#issue-" + iid)
    if article is None:
        raise ValueError("連動表示: 論点別X投稿が見つかりません: " + iid)
    out = []
    for sample in article.select(".hermes-sample"):
        link = sample.select_one("blockquote a[href]")
        if link is None:
            continue
        meta = sample.select_one(".hermes-sample-meta")
        quote = sample.select_one("blockquote")
        out.append(
            f'<article class="fuk-post" data-fuk-post-url="{e(link["href"])}">'
            f'<p>{e(meta.get_text(" ", strip=True) if meta else "代表投稿")}</p>'
            f'<a href="{e(link["href"])}" target="_blank" rel="noopener noreferrer">元の投稿をXで読む ↗</a>'
            f'<details class="fuk-embed"><summary>ここで投稿を表示</summary>{str(quote) if quote else ""}</details></article>'
        )
    if len(out) != 2:
        raise ValueError(f"連動表示: 論点別X投稿は2件必要です: {iid} ({len(out)}件)")
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
    from scripts.fukushuto_connected import background_data

    soup = BeautifulSoup(source, "html.parser")
    issue_cards = soup.select_one("#issue-cards")
    fallback = soup.select_one("#fallback")
    if issue_cards is None or fallback is None:
        raise ValueError("連動表示: #issue-cards または #fallback が見つかりません")
    cards_html, fallback_html = str(issue_cards), str(fallback)
    claims = {claim["id"]: claim for claim in data["claims"]}
    sunk = {item["id"]: item for item in data["ocean"]["sunk_continents"]}
    checks = {item["id"]: item for item in background_data()["checklist"]["items"]}
    out = [START]
    for issue in data["issues"]:
        iid, connection = issue["id"], index["issues"][issue["id"]]
        image = landing_image(fallback_html, issue["icon"], issue["label"])
        out.append(f'<template id="fukushuto-reading-{e(iid)}">')
        out.append(
            '<header class="fuk-selected-head"><div><p class="fuk-eyebrow">選んだ論点</p>'
            f'<h2>{e(issue["icon"])} {e(issue["label"])}</h2></div>'
            f'<button type="button" class="explainer-card fuk-image-action" data-img="{e(image["src"])}" data-alt="{e(image["alt"])}">'
            f'<img src="{e(image["src"])}" alt="" loading="lazy"><span>図解をひらく ↗</span></button></header>'
        )
        out.append(
            '<div class="fuk-metrics" aria-live="polite" aria-atomic="true">'
            '<p><strong data-fuk-count></strong><span data-fuk-mode></span></p>'
            '<p data-fuk-ratio></p><p data-fuk-zero hidden></p></div>'
            f'<p class="fuk-scope-note">{e(index["scope_note"])}</p>'
        )
        out.append(
            '<div class="fuk-columns"><section class="fuk-opinions" aria-label="意見の理由と投稿">'
            + '<h3>どんな理由で語られている？</h3>' + reasons(issue)
            + f'<p class="fuk-note">{e(index["reason_post_note"])}</p>'
            + '<div class="fuk-posts"><h3>実際の投稿を読む</h3>'
            + '<p class="fuk-note">副首都をめぐる投稿から、論点を読み進める手がかりとして2件を選んでいます。賛否の割合ではありません。</p>'
            + post_examples(cards_html, iid) + '</div></section>'
        )
        out.append('<aside class="fuk-evidence" aria-label="資料">')
        if connection["check_ids"]:
            out.append(f'<p class="fuk-eyebrow">制度の確認 {e(index["background_checked_on"])}</p><h3>この論点に関わる制度は？</h3>')
        for check_id in connection["check_ids"]:
            item = checks[check_id]
            out.append(
                f'<details class="fuk-check" data-fuk-check="{e(check_id)}"><summary>{e(item["label"])}：{e(item["ask"])}</summary>'
                f'<p id="fuk-check-note-{e(check_id)}">{e(item["found"])}</p>{sources(item["sources"])}</details>'
            )
        out.append('<h3>投稿の主張と一次資料</h3>')
        if connection["claim_ids"]:
            out.append(f'<p class="fuk-note">主張と資料の照合は{e(data["ocean"]["checked_on"])}時点です。投稿の正誤ではなく、投稿内の主張と一次資料の関係を示します。</p>')
        else:
            out.append('<p class="fuk-empty">この論点に対応する資料照合は、まだ登録されていません。</p>')
        for position, claim_id in enumerate(connection["claim_ids"]):
            claim = claims[claim_id]
            out.append(
                f'<details class="fuk-claim" data-fuk-claim="{e(claim_id)}"{" open" if position == 0 else ""}>'
                f'<summary>「{e(claim["claim"])}」</summary><span class="fuk-verdict">{e(claim["verdict_label"])}</span>'
                f'<p>{e(claim["finding"])}</p>{sources(claim["sources"])}</details>'
            )
        if connection["source_only_ids"]:
            out.append('<h3>資料にあり、収集投稿で見つからなかったこと</h3>')
        for source_id in connection["source_only_ids"]:
            item = sunk[source_id]
            out.append(
                f'<details class="fuk-source-only" data-fuk-source-only="{e(source_id)}"><summary id="fuk-source-topic-{e(source_id)}">{e(item["topic"])}</summary>'
                f'<p id="fuk-source-life-{e(source_id)}">{e(item["life_impact"])}</p>'
                f'<p id="fuk-source-note-{e(source_id)}" class="fuk-note">{e(item["sns_note"])} 確認日 {e(item["checked_on"])}</p>'
                f'<details><summary>調べた範囲を見る</summary><p id="fuk-source-note-copy-{e(source_id)}">{e(item["sns_note"])}</p></details>{sources(item["sources"])}</details>'
            )
        out.append('</aside></div></template>')
    return "\n".join(out + [END])
