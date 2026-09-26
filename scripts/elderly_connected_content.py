"""高齢者免許返納の論点別読書面を、PLANET_DATAと既存本文から生成する。"""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- ELDERLY_CONNECTED_CONTENT_START -->"
END = "<!-- ELDERLY_CONNECTED_CONTENT_END -->"


def e(value) -> str:
    return escape(str(value), quote=True)


def sources(items: list[dict]) -> str:
    if not items:
        return ""
    return '<details class="elc-sources"><summary>出典をひらく</summary><ul>' + "".join(
        f'<li><a href="{e(x["url"])}" target="_blank" rel="noopener noreferrer">{e(x["name"])}</a>'
        + (f'<p>{e(x["location"])}</p>' if x.get("location") else "") + "</li>"
        for x in items
    ) + "</ul></details>"


def reason_posts() -> dict:
    path = ROOT / "configs" / "elderly-license-reason-posts.json"
    return json.loads(path.read_text(encoding="utf-8"))["issues"]


def reasons(issue: dict) -> str:
    sub = issue.get("sub") or {}
    if sub.get("status") != "reread":
        note = sub.get("note", "この論点は、まだ編集部が投稿を1件ずつ読み直していません")
        return f'<p class="elc-empty">{e(note)}。AIが自動でつけた区分を理由として表示することはしません。</p>'
    configured = reason_posts().get(issue["id"], {})
    rows = []
    for item in sub.get("items", []):
        rid = str(item["id"])
        row = (
            f'<li><span class="elc-reason-row"><span>{e(item["label"])}</span>'
            f'<b id="elc-reason-count-{e(issue["id"])}-{e(rid)}">{int(item["count"]):,}<small>件</small></b></span>'
            f'<span class="elc-reason-track" aria-hidden="true"><i style="width:{float(item.get("pct_in_issue", 0)):.3f}%"></i></span>'
        )
        if item.get("unread"):
            row += "</li>"
            rows.append(row)
            continue
        post = configured.get(rid)
        if not post:
            raise ValueError(f"理由別投稿の登録がありません: {issue['id']} {rid}")
        row += (
            f'<details class="elc-reason-posts" data-elc-reason-posts="{e(rid)}">'
            f'<summary>この理由の投稿例を読む</summary>'
            f'<p class="elc-reason-post-summary">{e(post["summary"])}</p>'
            f'<a data-elc-post-url="{e(post["url"])}" href="{e(post["url"])}" target="_blank" rel="noopener noreferrer">元の投稿をXで読む ↗</a>'
            "</details></li>"
        )
        rows.append(row)
    note = "" if sub.get("show_coverage_note", True) is False else f'<p class="elc-note">{e(sub.get("coverage_note", ""))}。</p>'
    return note + '<ul class="elc-reasons">' + "".join(rows) + "</ul>"


def post_examples(issue_cards_html: str, iid: str) -> str:
    soup = BeautifulSoup(issue_cards_html, "html.parser")
    article = soup.select_one("#issue-" + iid)
    if article is None:
        return '<p class="elc-empty">この論点の既存代表投稿は登録されていません。</p>'
    out = []
    for sample in article.select(".hermes-sample"):
        link = sample.select_one("blockquote a[href]")
        meta = sample.select_one(".hermes-sample-meta")
        if link is None:
            continue
        url = link["href"]
        out.append(
            f'<article class="elc-post" data-elc-post-url="{e(url)}"><p>{e(meta.get_text(" ", strip=True) if meta else "代表投稿")}</p>'
            f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">元の投稿をXで読む ↗</a>'
            f'<details class="elc-embed"><summary>ここで投稿を表示</summary>{str(sample.select_one("blockquote"))}</details></article>'
        )
    return "".join(out) or '<p class="elc-empty">この論点の既存代表投稿は登録されていません。</p>'


def landing_image(fallback_html: str, icon: str, label: str) -> dict:
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
    sunk = {p["id"]: p for p in data["ocean"].get("sunk_continents", [])}
    veins = {p["id"]: p for p in data["ocean"].get("veins", [])}
    out = [START]
    for issue in data["issues"]:
        iid = issue["id"]
        connection = index["issues"][iid]
        image = landing_image(fallback_html, issue["icon"], issue["label"])
        out.append(f'<template id="elderly-license-revocation-reading-{e(iid)}">')
        out.append(
            '<header class="elc-selected-head"><div><p class="elc-eyebrow">選んだ論点</p>'
            f'<h2>{e(issue["icon"])} {e(issue["label"])}</h2></div>'
            f'<button type="button" class="explainer-card elc-image-action" data-img="{e(image["src"])}" data-alt="{e(image["alt"])}">'
            f'<img src="{e(image["src"])}" alt="" loading="lazy"><span>図解をひらく ↗</span></button></header>'
        )
        out.append(
            '<div class="elc-metrics" aria-live="polite" aria-atomic="true"><p><strong data-elc-count></strong><span data-elc-mode></span></p>'
            '<p data-elc-ratio></p><p data-elc-zero hidden></p></div>'
            f'<p class="elc-scope-note">{e(index["scope_note"])}</p>'
        )
        out.append(
            '<div class="elc-columns"><section class="elc-opinions" aria-label="意見の理由と投稿">'
            '<h3>どんな理由で語られている？</h3>' + reasons(issue)
            + '<div class="elc-posts"><h3>論点全体の代表投稿</h3>'
            '<p class="elc-note">編集部が選んだ投稿例です。この論点全体の賛否の割合を表すものではありません。</p>'
            + post_examples(issue_cards_html, iid) + '</div></section>'
        )
        out.append('<aside class="elc-evidence" aria-label="資料">')
        out.append('<h3>投稿の主張と一次資料</h3>')
        if connection["claim_ids"]:
            out.append('<p class="elc-note">照合確認日 2026-08-18。収集した投稿から選んだ主張を資料と照合しています。掲載した投稿例そのものへの判定を示すものではありません。</p>')
        else:
            out.append('<p class="elc-empty">この論点に対応する資料照合は、まだ登録されていません。</p>')
        for j, cid in enumerate(connection["claim_ids"]):
            c = claims[cid]
            label = c.get("verdict_label") or {"fact": "資料どおり", "gap": "少しずれる", "miss": "裏が取れない"}.get(c.get("verdict"), "未確認")
            out.append(
                f'<details class="elc-claim" data-elc-claim="{e(cid)}"{" open" if j == 0 else ""}><summary>「{e(c["claim"])}」</summary>'
                f'<span class="elc-verdict">{e(label)}</span><p id="elc-claim-finding-{e(iid)}-{e(cid)}">{e(c["finding"])}</p>' + sources(c["sources"]) + '</details>'
            )
        if connection["shared_concern_ids"]:
            out.append('<h3>同じ心配から、違う結論へ</h3>')
        for vid in connection["shared_concern_ids"]:
            v = veins[vid]
            sides = " ／ ".join(s["stance_label"] + " " + str(s["post_count"]) + "件" for s in v["sides"])
            out.append(
                f'<details class="elc-concern" data-elc-concern="{e(vid)}"><summary>{e(v["shared_concern"])}</summary><p>{e(v["diverging_reason"])}</p>'
                f'<p class="elc-note">確認した投稿例: {e(sides)}。確認日 {e(v["checked_on"])}</p></details>'
            )
        if connection["source_only_ids"]:
            out.append('<h3>資料にあり、収集投稿で見つからなかったこと</h3>')
        for sid in connection["source_only_ids"]:
            v = sunk[sid]
            scope = "確認時の" if v.get("base_stale") else "今回収集した"
            count_text = (f'{scope}意見{v["sns_base"]:,}件では、この記述に触れた投稿は見つかりませんでした。' if v["sns_count"] == 0 else f'{scope}意見{v["sns_base"]:,}件のうち、この記述に触れた投稿は{v["sns_count"]:,}件でした。')
            out.append(
                f'<details class="elc-source-only" data-elc-source-only="{e(sid)}"><summary>{e(v["topic"])}</summary><p>{e(v["life_impact"])}</p>'
                f'<p class="elc-note">{e(count_text)} 確認日 {e(v["checked_on"])}</p>'
                f'<details><summary>調べた範囲を見る</summary><p>{e(v["sns_note"])}</p></details>' + sources(v["sources"]) + '</details>'
            )
        out.append('</aside></div></template>')
    return "\n".join(out + [END])
