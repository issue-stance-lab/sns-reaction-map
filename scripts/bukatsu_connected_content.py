"""連動候補の読書面を、既存の原稿とPLANET_DATA・#issue-cards・#fallbackから生成する。

理由(reason)からX投稿を開く機能は工程3の必須範囲に含めない（計画書のとおり）。
理由の内訳・投稿例2件・資料照合・語られていない争点・共通の心配だけを1論点1枚にする。
"""
from __future__ import annotations

from html import escape
from bs4 import BeautifulSoup

START = "<!-- BUKATSU_CONNECTED_CONTENT_START -->"
END = "<!-- BUKATSU_CONNECTED_CONTENT_END -->"


def e(value) -> str:
    return escape(str(value), quote=True)


def sources(items: list[dict]) -> str:
    return '<details class="bkt-sources"><summary>出典をひらく</summary><ul>' + ''.join(
        f'<li><a href="{e(x["url"])}" target="_blank" rel="noopener noreferrer">{e(x["name"])}</a>'
        + (f'<p>{e(x["location"])}</p>' if x.get("location") else '') + '</li>' for x in items
    ) + '</ul></details>'


def reasons(issue: dict, show_unreviewed_note: bool) -> str:
    sub = issue["sub"]
    if sub["status"] != "reread":
        suffix = 'AIが自動でつけた区分をここに並べることはしません。人が読んだ結果だけをまとめにします。' if show_unreviewed_note is not False else ''
        return f'<p class="bkt-empty">{e(sub["note"])}。' + (f'<br>{suffix}' if suffix else '') + '</p>'
    items = sub["items"]
    rows = ''.join(
        f'<li data-bkt-reason="{e(x["id"])}"><span class="bkt-reason-row"><span>{e(x["label"])}</span>'
        f'<b id="bkt-reason-count-{e(issue["id"])}-{e(x["id"])}">{x["count"]:,}<small>件</small></b></span>'
        f'<span class="bkt-reason-track" aria-hidden="true"><i style="width:{x["pct_in_issue"]:.3f}%"></i></span></li>'
        for x in items
    )
    # 再読範囲の説明はcoverage_note（既存の原稿）をそのまま使う。自前の文は作らない。
    # 未読分は__unread__という通常の理由項目として一覧に含まれるため、
    # show_coverage_noteがfalseの論点（現在は再読済み5論点すべて）ではここに何も出さない。
    note = f'<p class="bkt-note">{e(sub["coverage_note"])}。</p>' if sub.get("show_coverage_note", True) is not False else ''
    return note + f'<ul class="bkt-reasons">{rows}</ul>'


def post_examples(issue_cards_html: str, iid: str) -> str:
    """#issue-cardsが既に組み立てた投稿例（2件）をそのまま抜き出す。作り直さない。"""
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
        out.append(
            f'<article class="bkt-post" data-bkt-post-url="{e(url)}"><p>{e(meta.get_text() if meta else "")}</p>'
            f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">元の投稿をXで読む ↗</a>'
            f'<details class="bkt-embed"><summary>ここで投稿を表示</summary>{str(sample.select_one("blockquote"))}</details></article>'
        )
    return "".join(out)


def landing_image(fallback_html: str, icon: str, label: str) -> dict:
    """#fallbackの図解を論点に結ぶ。data-altはその他だけ独自文言（"その他に見られた意見例"）
    でlabelと一致しないため、各論点固有のicon（絵文字、見出し直後の文字）で照合する。
    """
    soup = BeautifulSoup(fallback_html, "html.parser")
    for h2 in soup.select("h2"):
        if h2.get_text(strip=True).startswith(icon):
            node = h2.find_next(class_="landing-image")
            if node and node.get("data-img"):
                return {"src": node["data-img"], "alt": label}
    raise ValueError("連動表示: 図解の原画像がありません: " + label)


def render_templates(data: dict, source: str, index: dict) -> str:
    soup = BeautifulSoup(source, "html.parser")
    issue_cards = soup.select_one("#issue-cards")
    fallback = soup.select_one("#fallback")
    if issue_cards is None or fallback is None:
        raise ValueError("連動表示: #issue-cards または #fallback が見つかりません")
    issue_cards_html = str(issue_cards)
    fallback_html = str(fallback)
    claims = {c["id"]: c for c in data["claims"]}
    sunk = {p["id"]: p for p in data["ocean"]["sunk_continents"]}
    veins = {p["id"]: p for p in data["ocean"]["veins"]}
    out = [START]
    for issue in data["issues"]:
        iid = issue["id"]
        connection = index["issues"][iid]
        image = landing_image(fallback_html, issue["icon"], issue["label"])
        out.append(f'<template id="bukatsu-reading-{e(iid)}">')
        out.append(
            '<header class="bkt-selected-head"><div><p class="bkt-eyebrow">選んだ論点</p>'
            f'<h2>{e(issue["icon"])} {e(issue["label"])}</h2></div>'
            f'<button type="button" class="explainer-card bkt-image-action" data-img="{e(image["src"])}" data-alt="{e(image["alt"])}">'
            f'<img src="{e(image["src"])}" alt="" loading="lazy"><span>図解をひらく ↗</span></button></header>'
        )
        out.append(
            '<div class="bkt-metrics" aria-live="polite" aria-atomic="true"><p><strong data-bkt-count></strong><span data-bkt-mode></span></p>'
            '<p data-bkt-ratio></p><p data-bkt-zero hidden></p></div>'
            f'<p class="bkt-scope-note">{e(index["scope_note"])}</p>'
        )
        out.append(
            '<div class="bkt-columns"><section class="bkt-opinions" aria-label="意見の理由と投稿">'
            '<h3>どんな理由で語られている？</h3>' + reasons(issue, data.get("show_unreviewed_note", True))
        )
        out.append(
            '<div class="bkt-posts"><h3>実際の投稿を読む</h3>'
            '<p class="bkt-note">編集部が選んだ投稿例です。この論点全体の賛否の割合を表すものではありません。</p>'
            + post_examples(issue_cards_html, iid) + '</div></section>'
        )
        out.append('<aside class="bkt-evidence" aria-label="資料">')
        out.append('<h3>投稿の主張と一次資料</h3>')
        if connection["claim_ids"]:
            out.append(f'<p class="bkt-note">照合確認日 {e(data["ocean"]["checked_on"])}。収集した投稿から選んだ主張を資料と照合しています。掲載した投稿例そのものへの判定を示すものではありません。</p>')
        else:
            out.append('<p class="bkt-empty">この論点に対応する資料照合は、まだ登録されていません。</p>')
        for j, cid in enumerate(connection["claim_ids"]):
            c = claims[cid]
            out.append(
                f'<details class="bkt-claim" data-bkt-claim="{e(cid)}"{" open" if j == 0 else ""}><summary>「{e(c["claim"])}」</summary>'
                f'<span class="bkt-verdict">{e(c["verdict_label"])}</span><p>{e(c["finding"])}</p>' + sources(c["sources"]) + '</details>'
            )
        if connection["shared_concern_ids"]:
            out.append('<h3>同じ心配から、違う結論へ</h3>')
        for vid in connection["shared_concern_ids"]:
            v = veins[vid]
            sides = " ／ ".join(s["stance_label"] + " " + str(s["post_count"]) + "件" for s in v["sides"])
            out.append(
                f'<details class="bkt-concern" data-bkt-concern="{e(vid)}"><summary>{e(v["shared_concern"])}</summary><p>{e(v["diverging_reason"])}</p>'
                f'<p class="bkt-note" id="bkt-concern-count-{e(vid)}">確認した投稿例: {e(sides)}。確認日 {e(v["checked_on"])}</p></details>'
            )
        if connection["source_only_ids"]:
            out.append('<h3>資料にあり、収集投稿で見つからなかったこと</h3>')
        for sid in connection["source_only_ids"]:
            v = sunk[sid]
            scope = '確認時の' if v.get("base_stale") else '今回収集した'
            finding = (
                f'{scope}意見{v["sns_base"]:,}件では、この記述に触れた投稿は見つかりませんでした。' if v["sns_count"] == 0
                else f'{scope}意見{v["sns_base"]:,}件のうち、この記述に触れた投稿は{v["sns_count"]:,}件でした。'
            )
            out.append(
                f'<details class="bkt-source-only" data-bkt-source-only="{e(sid)}"><summary>{e(v["topic"])}</summary><p>{e(v["life_impact"])}</p>'
                f'<p class="bkt-note">{e(finding)} 確認日 {e(v["checked_on"])}</p>'
                f'<details><summary>調べた範囲を見る</summary><p id="bkt-source-note-{e(sid)}">{e(v["sns_note"])}</p></details>' + sources(v["sources"]) + '</details>'
            )
        out.append('</aside></div></template>')
    return '\n'.join(out + [END])
