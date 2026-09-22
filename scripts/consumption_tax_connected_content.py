"""連動候補の読書面を、既存の原稿とPLANET_DATAから生成する。"""
from __future__ import annotations

from html import escape

from bs4 import BeautifulSoup

START = "<!-- TAX_CONNECTED_CONTENT_START -->"
END = "<!-- TAX_CONNECTED_CONTENT_END -->"


def e(value) -> str:
    return escape(str(value), quote=True)


def pct(n: int, total: int) -> str:
    return f"{100 * n / total:.1f}%" if total else "算出できません"


def corrected_observations(data: dict) -> list[str]:
    """工程1で確定した訂正文。候補の現在値から生成し、日付は進めない。"""
    total, opinions = data["totals"]["collected"], data["totals"]["opinions"]
    by_id = {i["id"]: i for i in data["issues"]}
    conditional = next(s["count"] for s in data["stances"] if s["id"] == "consumption-tax-cut-conditional")
    political, other = (by_id["consumption-tax-cut-" + k] for k in ("political-trust", "other"))
    return [
        f"収集した{total:,}件のうち、意見と判定した投稿は{opinions:,}件（{pct(opinions, total)}）でした。集計はこの{opinions:,}件を対象にしています。",
        "減税への賛否だけでは『減税には賛成だが、政府案には不満がある』という違いを拾えないため、条件付きを含めた4つの立場で整理しています。"
        f"現在の集計では、条件付きは{conditional:,}件（{pct(conditional, opinions)}）です。",
        f"『{political['label']}』に分類した投稿は{political['count']:,}件で、収集した意見全体の{pct(political['count'], opinions)}でした。",
        f"既存の6論点に分類しきれなかった『その他』は{other['count']:,}件（{pct(other['count'], opinions)}）でした。世論調査の聞き方や制度説明への指摘などを掲載しています。",
    ]


def correct_editorial(data: dict) -> None:
    item = next(i for i in data["issues"] if i["id"] == "consumption-tax-cut-business-burden")
    for finding in data["editorial"]["findings"]:
        if finding["id"] == "consumption-tax-cut-ed-4":
            finding["text"] = (
                f"『{item['label']}』は{item['count']:,}件（全体の{pct(item['count'], data['totals']['opinions'])}）でした。"
                "ここでの件数は、今回収集した投稿で語られた量を示しています。論点としての重要さを表すものではありません。"
            )


def sources(items: list[dict]) -> str:
    return '<details class="tax-sources"><summary>出典をひらく</summary><ul>' + ''.join(
        f'<li><a href="{e(x["url"])}" target="_blank" rel="noopener noreferrer">{e(x["name"])}</a>'
        + (f'<p>{e(x["location"])}</p>' if x.get("location") else '') + '</li>' for x in items
    ) + '</ul></details>'


def reasons(issue: dict) -> str:
    sub = issue["sub"]
    if sub["status"] != "reread":
        return '<p class="tax-empty">この論点では、投稿を理由別に分ける再読をまだ行っていません。</p>'

    def rows(items):
        return '<ul class="tax-reasons">' + ''.join(
            f'<li data-tax-reason="{e(x["id"])}"><div><span>{e(x["label"])}</span><b id="tax-reason-count-{e(issue["id"])}-{e(x["id"])}">{x["count"]:,}<small>件</small></b></div>'
            f'<span class="tax-reason-track" aria-hidden="true"><i style="width:{100*x["count"]/issue["count"] if issue["count"] else 0:.3f}%"></i></span></li>'
            for x in items
        ) + '</ul>'

    items = sub["items"]
    note = f'<p class="tax-note">論点全体{issue["count"]:,}件のうち、{sub["reread_count"]:,}件を理由別に再読しました。</p>'
    if sub.get("unread_count"):
        note += f'<p class="tax-note">その後に増えた{sub["unread_count"]:,}件は、まだ理由別に再読していません。</p>'
    return note + rows(items[:3]) + (
        f'<details class="tax-more-reasons"><summary>残りの理由を見る · {len(items)-3}項目</summary>{rows(items[3:])}</details>'
        if len(items) > 3 else ''
    )


def render_templates(data: dict, source: str, index: dict) -> str:
    from build_consumption_tax_page import BACKGROUND_DATA, ISSUE_CARDS_POSTS
    from x_embed import embed_html

    soup = BeautifulSoup(source, "html.parser")
    claims = {c["id"]: c for c in data["claims"]}
    policies = {p["id"]: p for p in BACKGROUND_DATA["policies"]}
    timelines = {p["id"]: p for p in BACKGROUND_DATA["timeline"]}
    sunk = {p["id"]: p for p in data["ocean"]["sunk_continents"]}
    veins = {p["id"]: p for p in data["ocean"]["veins"]}
    out = [START]
    for issue in data["issues"]:
        iid = issue["id"]
        connection = index["issues"][iid]
        image = soup.select_one('#fb-' + iid + ' .landing-image[data-img]')
        if image is None:
            raise ValueError("連動表示: 図解の原画像がありません: " + iid)
        out.append(f'<template id="tax-reading-{e(iid)}">')
        out.append('<header class="tax-selected-head"><div><p class="tax-eyebrow">選んだ論点</p>'
                   f'<h2>{e(issue["icon"])} {e(issue["label"])}</h2></div>'
                   f'<button type="button" class="explainer-card tax-image-action" data-img="{e(image["data-img"])}" data-alt="{e(issue["label"])}の図解">'
                   f'<img src="{e(image["data-img"])}" alt="" loading="lazy"><span>図解をひらく ↗</span></button></header>')
        out.append('<div class="tax-metrics" aria-live="polite" aria-atomic="true"><p><strong data-tax-count></strong><span data-tax-mode></span></p>'
                   '<p data-tax-ratio></p><p data-tax-zero hidden></p></div>'
                   f'<p class="tax-scope-note">{e(index["scope_note"])}</p>')
        out.append('<div class="tax-columns"><section class="tax-opinions" aria-label="意見の理由と投稿">'
                   '<h3>どんな理由で語られている？</h3>' + reasons(issue))
        out.append('<div class="tax-posts"><h3>実際の投稿を読む</h3>'
                   '<p class="tax-note">編集部が選んだ投稿例です。この論点全体の賛否の割合を表すものではありません。</p>')
        for url, label in ISSUE_CARDS_POSTS[iid]:
            out.append(f'<article class="tax-post" data-tax-post-url="{e(url)}"><p>{e(label)}</p>'
                       f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">元の投稿をXで読む ↗</a>'
                       f'<details class="tax-embed"><summary>ここで投稿を表示</summary>{embed_html(url)}</details></article>')
        out.append('</div></section><aside class="tax-evidence" aria-label="制度と資料">')
        if connection["policy_ids"] or connection["timeline_ids"]:
            out.append(f'<p class="tax-eyebrow">制度・背景の確認 {e(BACKGROUND_DATA["checked_on"])}</p><h3>制度のどこが関係する？</h3>')
        for j, pid in enumerate(connection["policy_ids"]):
            p = policies[pid]
            out.append(f'<details class="tax-policy" data-tax-policy="{e(pid)}"{" open" if j == 0 else ""}><summary>{e(p["question"])}</summary>'
                       f'<p>{e(p["body"])}</p>' + sources([{"url": u, "name": n} for u, n in p["links"]]) + '</details>')
        for tid in connection["timeline_ids"]:
            p = timelines[tid]
            out.append(f'<details class="tax-policy" data-tax-timeline="{e(tid)}"><summary>{e(p["date"])} · {e(p["title"])}</summary>'
                       f'<p>{e(p["body"])}</p>' + sources([{"url": u, "name": n} for u, n in p["links"]]) + '</details>')
        if connection["policy_ids"] or connection["timeline_ids"]:
            out.append(f'<p class="tax-note">{e(BACKGROUND_DATA["checked_on"])}時点では政府方針の段階で、法律はまだ成立していません。</p>')
        out.append('<h3>投稿の主張と一次資料</h3>')
        if connection["claim_ids"]:
            out.append(f'<p class="tax-note">照合確認日 {e(data["ocean"]["checked_on"])}。収集した投稿から選んだ主張を資料と照合しています。ここに並べた投稿例2件への判定を示すものではありません。</p>')
        else:
            out.append('<p class="tax-empty">この論点に対応する資料照合は、まだ登録されていません。</p>')
        for j, cid in enumerate(connection["claim_ids"]):
            c = claims[cid]
            out.append(f'<details class="tax-claim" data-tax-claim="{e(cid)}"{" open" if j == 0 else ""}><summary>「{e(c["claim"])}」</summary>'
                       f'<span class="tax-verdict">{e(c["verdict_label"])}</span><p>{e(c["finding"])}</p>' + sources(c["sources"]) + '</details>')
        if connection["shared_concern_ids"]:
            out.append('<h3>同じ心配から、違う結論へ</h3>')
        for vid in connection["shared_concern_ids"]:
            v = veins[vid]
            out.append(f'<details class="tax-concern" data-tax-concern="{e(vid)}"><summary>{e(v["shared_concern"])}</summary><p>{e(v["diverging_reason"])}</p>'
                       f'<p class="tax-note" id="tax-concern-count-{e(vid)}">確認した投稿例: {e(" ／ ".join(s["stance_label"]+" "+str(s["post_count"])+"件" for s in v["sides"]))}。確認日 {e(v["checked_on"])}</p></details>')
        if connection["source_only_ids"]:
            out.append('<h3>資料にあり、収集投稿で見つからなかったこと</h3>')
        for sid in connection["source_only_ids"]:
            v = sunk[sid]
            scope = '確認時の' if v.get("base_stale") else '今回収集した'
            finding = (f'{scope}意見{v["sns_base"]:,}件では、この記述に触れた投稿は見つかりませんでした。' if v["sns_count"] == 0
                       else f'{scope}意見{v["sns_base"]:,}件のうち、この記述に触れた投稿は{v["sns_count"]:,}件でした。')
            out.append(f'<details class="tax-source-only" data-tax-source-only="{e(sid)}"><summary>{e(v["topic"])}</summary><p>{e(v["life_impact"])}</p>'
                       f'<p class="tax-note">{e(finding)} 確認日 {e(v["checked_on"])}</p>'
                       f'<details><summary>調べた範囲を見る</summary><p id="tax-source-note-{e(sid)}">{e(v["sns_note"])}</p></details>' + sources(v["sources"]) + '</details>')
        if connection["method_link"]:
            out.append(f'<p><a href="{e(connection["method_link"])}">投稿の集め方と分類方法を確認する →</a></p>')
        out.append('</aside></div></template>')
    return '\n'.join(out + [END])
