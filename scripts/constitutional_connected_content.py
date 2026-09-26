"""憲法改正論議の読書面を、既存の原稿とPLANET_DATA・#explainer-section・#fallback・制度確認から生成する。

理由の内訳・投稿例2件・資料照合・語られていない争点・共通の心配・関係する制度確認4項目を
1論点1枚にする。制度確認（#bukatsu-check）はdata/verification/constitutional-amendment-background.jsonの
issue_idsで論点に結ぶ（工程2でタグ付け済み）。年表11件は無タグのままのため、本工程では
どの論点にも表示されない（工程2の設計どおり。issue_idsが後日追加されればcontent_index()が
自動で拾い、この読書面にも反映される）。

bukatsu-chiikiと異なり、生データに立場(stance)別の理由内訳が無いため、理由の件数・割合は
「全立場」の値のみを表示する（立場フィルターで数値が変わる機能は本工程の範囲外）。
理由(reason)からX投稿を開く機能・予想2問との連動は工程3の必須範囲に含めない（計画書のとおり）。
"""
from __future__ import annotations

from html import escape
from bs4 import BeautifulSoup

START = "<!-- CONSTITUTIONAL_CONNECTED_CONTENT_START -->"
END = "<!-- CONSTITUTIONAL_CONNECTED_CONTENT_END -->"


def e(value) -> str:
    return escape(str(value), quote=True)


def sources(items: list[dict]) -> str:
    return '<details class="ca-sources"><summary>出典をひらく</summary><ul>' + ''.join(
        f'<li><a href="{e(x["url"])}" target="_blank" rel="noopener noreferrer">{e(x["name"])}</a>'
        + (f'<p>{e(x["location"])}</p>' if x.get("location") else '') + '</li>' for x in items
    ) + '</ul></details>'


def reasons(issue: dict) -> str:
    sub = issue["sub"]
    if sub["status"] != "reread":
        return (
            f'<p class="ca-empty">{e(sub["note"])}。'
            'AIが自動でつけた区分をここに並べることはしません。人が読んだ結果だけをまとめにします。</p>'
        )
    items = sub["items"]
    rows = ''.join(
        f'<li><span class="ca-reason-row"><span>{e(x["label"])}</span>'
        f'<b id="ca-reason-count-{e(issue["id"])}-{e(x["id"])}">{x["count"]:,}<small>件</small></b></span>'
        f'<span class="ca-reason-track" aria-hidden="true"><i style="width:{x["pct_in_issue"]:.3f}%"></i></span></li>'
        for x in items
    )
    note = f'<p class="ca-note">{e(sub["coverage_note"])}。</p>' if sub.get("show_coverage_note", True) is not False else ''
    return note + f'<ul class="ca-reasons">{rows}</ul>'


def post_examples(issue_cards_html: str, iid: str) -> str:
    """旧ページの論点別代表投稿カード（2件）をそのまま抜き出す。作り直さない。"""
    soup = BeautifulSoup(issue_cards_html, "html.parser")
    article = soup.select_one("#figure-" + iid)
    if article is None:
        # 「その他」は旧ページに代表投稿カードがなく、未登録の事実を画面で明示する。
        # 投稿を新規に作って穴埋めすることはしない。
        return ""
    out = []
    for sample in article.select(".featured-post"):
        link = sample.select_one("blockquote a[href]")
        if link is None:
            continue
        url = link["href"]
        label = sample.select_one("strong")
        summary = sample.select_one("p")
        blockquote = sample.select_one("blockquote")
        out.append(
            f'<article class="ca-post" data-ca-post-url="{e(url)}"><p><strong>{e(label.get_text(" ", strip=True) if label else "代表投稿")}</strong>'
            f'{e("：" + summary.get_text(" ", strip=True) if summary else "")}</p>'
            f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">元の投稿をXで読む ↗</a>'
            f'<details class="ca-embed"><summary>ここで投稿を表示</summary>{str(blockquote) if blockquote else ""}</details></article>'
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
    from scripts.constitutional_connected import background_data

    soup = BeautifulSoup(source, "html.parser")
    issue_cards = soup.select_one("#explainer-section")
    fallback = soup.select_one("#fallback")
    if issue_cards is None or fallback is None:
        raise ValueError("連動表示: #explainer-section または #fallback が見つかりません")
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
        out.append(f'<template id="constitutional-amendment-reading-{e(iid)}">')
        out.append(
            '<header class="ca-selected-head"><div><p class="ca-eyebrow">選んだ論点</p>'
            f'<h2>{e(issue["icon"])} {e(issue["label"])}</h2></div>'
            f'<button type="button" class="explainer-card ca-image-action" data-img="{e(image["src"])}" data-alt="{e(image["alt"])}">'
            f'<img src="{e(image["src"])}" alt="" loading="lazy"><span>図解をひらく ↗</span></button></header>'
        )
        out.append(
            '<div class="ca-metrics" aria-live="polite" aria-atomic="true"><p><strong data-ca-count></strong><span data-ca-mode></span></p>'
            '<p data-ca-ratio></p><p data-ca-zero hidden></p></div>'
            f'<p class="ca-scope-note">{e(index["scope_note"])}</p>'
        )
        out.append(
            '<div class="ca-columns"><section class="ca-opinions" aria-label="意見の理由と投稿">'
            '<h3>どんな理由で語られている？</h3>' + reasons(issue)
        )
        post_html = post_examples(issue_cards_html, iid)
        post_body = post_html or (
            '<p class="ca-empty">この論点には、既存の代表投稿が登録されていません。'
            '理由別の投稿データも未登録です。</p>'
        )
        out.append(
            '<div class="ca-posts"><h3>実際の投稿を読む</h3>'
            '<p class="ca-note">編集部が選んだ投稿例です。この論点全体の賛否の割合を表すものではありません。</p>'
            + post_body + '</div></section>'
        )
        out.append('<aside class="ca-evidence" aria-label="資料">')
        if connection["timeline_ids"]:
            out.append(f'<p class="ca-eyebrow">背景の確認 {e(index["background_checked_on"])}</p><h3>背景のどこが関係する？</h3>')
        for tid in connection["timeline_ids"]:
            t = timelines[tid]
            out.append(
                f'<div class="ca-timeline-item" data-ca-timeline="{e(tid)}">'
                f'<p class="ca-timeline-when">{e(t["when"])}<em>{e(t["era"])}</em></p>'
                f'<p>{e(t["text"])}</p>' + sources(t["sources"]) + '</div>'
            )
        if connection["check_ids"]:
            out.append(f'<p class="ca-eyebrow">制度の確認 {e(index["background_checked_on"])}</p><h3>この論点に関わる制度は？</h3>')
        for cid in connection["check_ids"]:
            c = checklist[cid]
            # 制度確認項目も複数論点にまたがりうる（例: kaijiは学習データ・無断利用と法制度・
            # 規制整備の両方）ため、idを論点で分ける（shared_concernと同じ理由、工程6で発覚）。
            out.append(
                f'<details class="ca-check" data-ca-check="{e(cid)}"><summary>{e(c["label"])}：{e(c["ask"])}</summary>'
                f'<p id="ca-check-note-{e(iid)}-{e(cid)}">{e(c["found"])}</p>' + sources(c["sources"]) + '</details>'
            )
        out.append('<h3>投稿の主張と一次資料</h3>')
        if connection["claim_ids"]:
            out.append(f'<p class="ca-note">照合確認日 {e(data["ocean"]["checked_on"])}。収集した投稿から選んだ主張を資料と照合しています。掲載した投稿例そのものへの判定を示すものではありません。</p>')
        else:
            out.append('<p class="ca-empty">この論点に対応する資料照合は、まだ登録されていません。</p>')
        for j, cid in enumerate(connection["claim_ids"]):
            c = claims[cid]
            out.append(
                f'<details class="ca-claim" data-ca-claim="{e(cid)}"{" open" if j == 0 else ""}><summary>「{e(c["claim"])}」</summary>'
                f'<span class="ca-verdict">{e(c["verdict_label"])}</span><p>{e(c["finding"])}</p>' + sources(c["sources"]) + '</details>'
            )
        if connection["shared_concern_ids"]:
            out.append('<h3>同じ心配から、違う結論へ</h3>')
        for vid in connection["shared_concern_ids"]:
            v = veins[vid]
            sides = " ／ ".join(s["stance_label"] + " " + str(s["post_count"]) + "件" for s in v["sides"])
            # shared_concern（vein）は複数論点にまたがりうるため、idを論点で分ける
            # （同じidが2つのtemplateへ重複するとHTMLとして不正になる。工程6の有効化で発覚）。
            out.append(
                f'<details class="ca-concern" data-ca-concern="{e(vid)}"><summary>{e(v["shared_concern"])}</summary><p>{e(v["diverging_reason"])}</p>'
                f'<p class="ca-note" id="ca-concern-count-{e(iid)}-{e(vid)}">確認した投稿例: {e(sides)}。確認日 {e(v["checked_on"])}</p></details>'
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
                f'<details class="ca-source-only" data-ca-source-only="{e(sid)}"><summary>{e(v["topic"])}</summary><p>{e(v["life_impact"])}</p>'
                f'<p class="ca-note">{e(finding)} 確認日 {e(v["checked_on"])}</p>'
                f'<details><summary>調べた範囲を見る</summary><p id="ca-source-note-{e(sid)}">{e(v["sns_note"])}</p></details>' + sources(v["sources"]) + '</details>'
            )
        out.append('</aside></div></template>')
    return '\n'.join(out + [END])
