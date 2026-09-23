"""連動候補の読書面を、既存の原稿とPLANET_DATA・#issue-cards・#fallback・制度確認から生成する。

理由の内訳・投稿例2件・資料照合・語られていない争点・共通の心配・関係する制度確認4項目を
1論点1枚にする。制度確認（#bukatsu-check）はdata/verification/ai-copyright-background.jsonの
issue_idsで論点に結ぶ（工程2でタグ付け済み）。年表6件は無タグのままのため、本工程では
どの論点にも表示されない（工程2の設計どおり。issue_idsが後日追加されればcontent_index()が
自動で拾い、この読書面にも反映される）。

bukatsu-chiikiと異なり、生データに立場(stance)別の理由内訳が無いため、理由の件数・割合は
「全立場」の値のみを表示する（立場フィルターで数値が変わる機能は本工程の範囲外）。
理由(reason)からX投稿を開く機能・予想2問との連動は工程3の必須範囲に含めない（計画書のとおり）。
"""
from __future__ import annotations

from html import escape
from bs4 import BeautifulSoup

START = "<!-- AI_COPYRIGHT_CONNECTED_CONTENT_START -->"
END = "<!-- AI_COPYRIGHT_CONNECTED_CONTENT_END -->"


def e(value) -> str:
    return escape(str(value), quote=True)


def sources(items: list[dict]) -> str:
    return '<details class="aic-sources"><summary>出典をひらく</summary><ul>' + ''.join(
        f'<li><a href="{e(x["url"])}" target="_blank" rel="noopener noreferrer">{e(x["name"])}</a>'
        + (f'<p>{e(x["location"])}</p>' if x.get("location") else '') + '</li>' for x in items
    ) + '</ul></details>'


def reasons(issue: dict) -> str:
    sub = issue["sub"]
    if sub["status"] != "reread":
        return (
            f'<p class="aic-empty">{e(sub["note"])}。'
            'AIが自動でつけた区分をここに並べることはしません。人が読んだ結果だけをまとめにします。</p>'
        )
    items = sub["items"]
    rows = ''.join(
        f'<li><span class="aic-reason-row"><span>{e(x["label"])}</span>'
        f'<b>{x["count"]:,}<small>件</small></b></span>'
        f'<span class="aic-reason-track" aria-hidden="true"><i style="width:{x["pct_in_issue"]:.3f}%"></i></span></li>'
        for x in items
    )
    note = f'<p class="aic-note">{e(sub["coverage_note"])}。</p>' if sub.get("show_coverage_note", True) is not False else ''
    return note + f'<ul class="aic-reasons">{rows}</ul>'


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
            f'<article class="aic-post" data-aic-post-url="{e(url)}"><p>{e(meta.get_text() if meta else "")}</p>'
            f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">元の投稿をXで読む ↗</a>'
            f'<details class="aic-embed"><summary>ここで投稿を表示</summary>{str(sample.select_one("blockquote"))}</details></article>'
        )
    return "".join(out)


def landing_image(fallback_html: str, icon: str, label: str) -> dict:
    """#fallbackの図解を論点に結ぶ。各論点固有のicon（絵文字、見出し直後の文字）で照合する。"""
    soup = BeautifulSoup(fallback_html, "html.parser")
    for h2 in soup.select("h2"):
        if h2.get_text(strip=True).startswith(icon):
            node = h2.find_next(class_="landing-image")
            if node and node.get("data-img"):
                return {"src": node["data-img"], "alt": label}
    raise ValueError("連動表示: 図解の原画像がありません: " + label)


def render_templates(data: dict, source: str, index: dict) -> str:
    from scripts.ai_copyright_connected import background_data

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
    background = background_data()
    timelines = {t["id"]: t for t in background["timeline"]}
    checklist = {c["id"]: c for c in background["checklist"]["items"]}
    out = [START]
    for issue in data["issues"]:
        iid = issue["id"]
        connection = index["issues"][iid]
        image = landing_image(fallback_html, issue["icon"], issue["label"])
        out.append(f'<template id="ai-copyright-reading-{e(iid)}">')
        out.append(
            '<header class="aic-selected-head"><div><p class="aic-eyebrow">選んだ論点</p>'
            f'<h2>{e(issue["icon"])} {e(issue["label"])}</h2></div>'
            f'<button type="button" class="explainer-card aic-image-action" data-img="{e(image["src"])}" data-alt="{e(image["alt"])}">'
            f'<img src="{e(image["src"])}" alt="" loading="lazy"><span>図解をひらく ↗</span></button></header>'
        )
        out.append(
            '<div class="aic-metrics" aria-live="polite" aria-atomic="true"><p><strong data-aic-count></strong><span data-aic-mode></span></p>'
            '<p data-aic-ratio></p><p data-aic-zero hidden></p></div>'
            f'<p class="aic-scope-note">{e(index["scope_note"])}</p>'
        )
        out.append(
            '<div class="aic-columns"><section class="aic-opinions" aria-label="意見の理由と投稿">'
            '<h3>どんな理由で語られている？</h3>' + reasons(issue)
        )
        out.append(
            '<div class="aic-posts"><h3>実際の投稿を読む</h3>'
            '<p class="aic-note">編集部が選んだ投稿例です。この論点全体の賛否の割合を表すものではありません。</p>'
            + post_examples(issue_cards_html, iid) + '</div></section>'
        )
        out.append('<aside class="aic-evidence" aria-label="資料">')
        if connection["timeline_ids"]:
            out.append(f'<p class="aic-eyebrow">背景の確認 {e(index["background_checked_on"])}</p><h3>背景のどこが関係する？</h3>')
        for tid in connection["timeline_ids"]:
            t = timelines[tid]
            out.append(
                f'<div class="aic-timeline-item" data-aic-timeline="{e(tid)}">'
                f'<p class="aic-timeline-when">{e(t["when"])}<em>{e(t["era"])}</em></p>'
                f'<p>{e(t["text"])}</p>' + sources(t["sources"]) + '</div>'
            )
        if connection["check_ids"]:
            out.append(f'<p class="aic-eyebrow">制度の確認 {e(index["background_checked_on"])}</p><h3>この論点に関わる制度は？</h3>')
        for cid in connection["check_ids"]:
            c = checklist[cid]
            out.append(
                f'<details class="aic-check" data-aic-check="{e(cid)}"><summary>{e(c["label"])}：{e(c["ask"])}</summary>'
                f'<p id="aic-check-note-{e(cid)}">{e(c["found"])}</p>' + sources(c["sources"]) + '</details>'
            )
        out.append('<h3>投稿の主張と一次資料</h3>')
        if connection["claim_ids"]:
            out.append(f'<p class="aic-note">照合確認日 {e(data["ocean"]["checked_on"])}。収集した投稿から選んだ主張を資料と照合しています。掲載した投稿例そのものへの判定を示すものではありません。</p>')
        else:
            out.append('<p class="aic-empty">この論点に対応する資料照合は、まだ登録されていません。</p>')
        for j, cid in enumerate(connection["claim_ids"]):
            c = claims[cid]
            out.append(
                f'<details class="aic-claim" data-aic-claim="{e(cid)}"{" open" if j == 0 else ""}><summary>「{e(c["claim"])}」</summary>'
                f'<span class="aic-verdict">{e(c["verdict_label"])}</span><p>{e(c["finding"])}</p>' + sources(c["sources"]) + '</details>'
            )
        if connection["shared_concern_ids"]:
            out.append('<h3>同じ心配から、違う結論へ</h3>')
        for vid in connection["shared_concern_ids"]:
            v = veins[vid]
            sides = " ／ ".join(s["stance_label"] + " " + str(s["post_count"]) + "件" for s in v["sides"])
            out.append(
                f'<details class="aic-concern" data-aic-concern="{e(vid)}"><summary>{e(v["shared_concern"])}</summary><p>{e(v["diverging_reason"])}</p>'
                f'<p class="aic-note" id="aic-concern-count-{e(vid)}">確認した投稿例: {e(sides)}。確認日 {e(v["checked_on"])}</p></details>'
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
                f'<details class="aic-source-only" data-aic-source-only="{e(sid)}"><summary>{e(v["topic"])}</summary><p>{e(v["life_impact"])}</p>'
                f'<p class="aic-note">{e(finding)} 確認日 {e(v["checked_on"])}</p>'
                f'<details><summary>調べた範囲を見る</summary><p id="aic-source-note-{e(sid)}">{e(v["sns_note"])}</p></details>' + sources(v["sources"]) + '</details>'
            )
        out.append('</aside></div></template>')
    return '\n'.join(out + [END])
