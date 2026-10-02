"""辺野古テーマの連動読書面を静的HTMLとして生成する。"""
from __future__ import annotations

import html
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "henoko-student-accident"
START = "<!-- HENOKO_CONNECTED_CONTENT_START -->"
END = "<!-- HENOKO_CONNECTED_CONTENT_END -->"


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def sources(items: list[dict]) -> str:
    if not items:
        return ""
    links = []
    for item in items:
        label = item.get("name") or item.get("title") or item.get("url")
        url = item.get("url")
        if url:
            links.append(
                f'<a href="{e(url)}" target="_blank" rel="noopener nofollow">{e(label)}</a>'
            )
        else:
            links.append(f"<span>{e(label)}</span>")
    return "<ul>" + "".join(f"<li>{link}</li>" for link in links) + "</ul>"


def source_block(title: str, items: list[dict], class_name: str = "") -> str:
    cls = f' class="{e(class_name)}"' if class_name else ""
    return f'<div{cls}><h5>{e(title)}</h5>{sources(items)}</div>'


def landing_image(source: str, issue_id: str) -> str:
    soup = BeautifulSoup(source, "html.parser")
    node = soup.select_one(f"#fb-{issue_id} .landing-image[data-img]")
    if not node:
        return ""
    image = node.select_one("img")
    if not image:
        return ""
    return (
        '<button type="button" class="henoko-image-action" data-henoko-image>'
        f'<img src="{e(image.get("src", ""))}" alt="{e(image.get("alt", ""))}" loading="lazy">'
        '<span>図解を拡大</span></button>'
    )


def reasons(issue: dict) -> str:
    sub = issue.get("sub") or {}
    items = sub.get("items") or []
    if not items:
        return ""
    rows = []
    for item in items:
        rid = item["id"]
        unread = " unread" if item.get("unread") else ""
        rows.append(
            f'<li class="henoko-reason{unread}" data-henoko-reason="{e(rid)}">'
            f'<span class="henoko-reason-label">{e(item["label"])}</span>'
            f'<span class="henoko-reason-count" id="henoko-reason-count-{e(issue["id"])}-{e(rid)}">{e(item["count"])}件</span>'
            f'<span class="henoko-reason-bar"><i style="width:{e(item.get("pct_in_issue", 0))}%"></i></span>'
            "</li>"
        )
    note = ""
    if sub.get("show_coverage_note") and sub.get("coverage_note"):
        note = f'<p class="henoko-note">{e(sub["coverage_note"])}</p>'
    if sub.get("unread_count"):
        note += f'<p class="henoko-note" id="henoko-reason-coverage-{e(issue["id"])}">本文を読み直した分類は{sub.get("reread_count", 0)}件。未読分{sub["unread_count"]}件は別枠で表示しています。</p>'
    return "<ul class=\"henoko-reasons\">" + "".join(rows) + "</ul>" + note


def render_check(item: dict) -> str:
    return (
        f'<article class="henoko-check" data-henoko-check="{e(item["id"])}">'
        f'<h5>{e(item["label"])}</h5><p><b>確かめる問い：</b>{e(item["ask"])}</p>'
        f'<p id="henoko-check-note-{e(item["id"])}">{e(item["found"])}</p>'
        f'<div class="henoko-sources">{sources(item.get("sources", []))}</div></article>'
    )


def render_timeline(item: dict) -> str:
    return (
        f'<article class="henoko-timeline-item" data-henoko-timeline="{e(item["id"])}">'
        f'<p class="henoko-timeline-when">{e(item["when"])} <b>{e(item["era"])}</b></p>'
        f'<p>{e(item["text"])}</p><div class="henoko-sources">{sources(item.get("sources", []))}</div></article>'
    )


def render_claim(claim: dict) -> str:
    verdict = claim.get("verdict", "")
    return (
        f'<article class="henoko-claim verdict-{e(verdict)}" data-henoko-claim="{e(claim["id"])}">'
        f'<div class="henoko-claim-title"><span class="verdict v-{e(verdict)}">{e(claim.get("verdict_label", verdict))}</span>'
        f'<h5>{e(claim["claim"])}</h5></div>'
        f'<p>{e(claim["finding"])}</p><div class="henoko-sources">{sources(claim.get("sources", []))}</div></article>'
    )


def render_source_only(item: dict) -> str:
    return (
        f'<article class="henoko-source-only" data-henoko-source-only="{e(item["id"])}">'
        f'<h5 id="henoko-source-topic-{e(item["id"])}">{e(item["topic"])}</h5><p class="henoko-source-impact" id="henoko-source-life-{e(item["id"])}">{e(item["life_impact"])}</p>'
        f'<p class="henoko-source-count">集めた投稿での件数：<b>{e(item.get("sns_count", 0))}件</b>（意見{e(item.get("opinion_count_now", 0))}件のうち）</p>'
        f'<p class="henoko-note" id="henoko-source-note-{e(item["id"])}">{e(item["sns_note"])} 確認日 {e(item.get("checked_on", ""))}</p><div class="henoko-sources">{sources(item.get("sources", []))}</div></article>'
    )


def render_vein(vein: dict) -> str:
    issue_labels = "・".join(vein.get("issue_ids", []))
    return (
        f'<article class="henoko-concern" data-henoko-concern="{e(vein["id"])}">'
        f'<h5>{e(vein["shared_concern"])}</h5><p>{e(vein["diverging_reason"])}</p>'
        f'<p class="henoko-note">関わる論点：{e(issue_labels)}</p></article>'
    )


def render_editorial(item: dict) -> str:
    labels = {
        "shared_premise": "共通する前提",
        "real_conflict": "本当の対立",
        "still_unknown": "まだ分からないこと",
    }
    return (
        f'<article class="henoko-editorial" data-henoko-editorial="{e(item["id"])}">'
        f'<span class="henoko-editorial-kind">{e(labels.get(item.get("kind"), item.get("kind", "編集部整理")))}</span>'
        f'<p>{e(item["text"])}</p></article>'
    )


def render_templates(data: dict, source: str, index: dict) -> str:
    background = json_background()
    timeline = {item["id"]: item for item in background["timeline"]}
    checks = {item["id"]: item for item in background["checklist"]["items"]}
    claims = {item["id"]: item for item in data.get("claims", [])}
    sunk = {item["id"]: item for item in data["ocean"].get("sunk_continents", [])}
    veins = {item["id"]: item for item in data["ocean"].get("veins", [])}
    editorials = {item["id"]: item for item in data["editorial"].get("findings", [])}
    templates = []
    for issue in data["issues"]:
        iid = issue["id"]
        conn = index["issues"][iid]
        image = landing_image(source, iid)
        issue_title = f'{issue.get("icon", "")} {issue["label"]}'.strip()
        claim_html = "".join(render_claim(claims[claim_id]) for claim_id in conn["claim_ids"])
        source_html = "".join(render_source_only(sunk[item_id]) for item_id in conn["source_only_ids"])
        concern_html = "".join(render_vein(veins[item_id]) for item_id in conn["shared_concern_ids"])
        timeline_html = "".join(render_timeline(timeline[item_id]) for item_id in conn["timeline_ids"])
        check_html = "".join(render_check(checks[item_id]) for item_id in conn["check_ids"])
        editorial_html = "".join(render_editorial(editorials[item_id]) for item_id in conn["editorial_ids"])
        scope = issue.get("sub", {}).get("coverage_note") or index["scope_note"]
        templates.append(
            f'''<template id="{TOPIC}-reading-{e(iid)}">
  <article class="henoko-reading" data-henoko-reading="{e(iid)}">
    <header class="henoko-selected-head">
      <div class="henoko-selected-copy"><p class="henoko-kicker">選んだ論点</p><h2>{e(issue_title)}</h2>
        <p class="henoko-selected-summary">{e(issue.get("label", ""))}を、投稿の理由と資料の両方から読みます。</p></div>{image}
      <div class="henoko-metrics" aria-live="polite"><strong data-henoko-count>0</strong><span data-henoko-mode>件</span><span data-henoko-ratio></span><span data-henoko-zero hidden></span></div>
    </header>
    <p class="henoko-scope">{e(scope)}</p>
    <div class="henoko-columns">
      <section class="henoko-opinions" aria-labelledby="henoko-reasons-{e(iid)}"><h3 id="henoko-reasons-{e(iid)}">この論点を語る理由</h3>{reasons(issue)}
        </section>
      <section class="henoko-evidence" aria-labelledby="henoko-evidence-{e(iid)}"><h3 id="henoko-evidence-{e(iid)}">資料と照合する</h3>
        <div class="henoko-reading-sources">
          {f'<div class="henoko-checks"><h4>学校の説明で確かめる</h4>{check_html}</div>' if check_html else ''}
          {f'<div class="henoko-timeline"><h4>照合した経緯</h4>{timeline_html}</div>' if timeline_html else ''}
          {f'<div class="henoko-claims"><h4>投稿にあった主張と一次資料</h4>{claim_html}</div>' if claim_html else ''}
          {f'<div class="henoko-source-only-list"><h4>資料にあり、今回の投稿に見当たらなかったこと</h4>{source_html}</div>' if source_html else ''}
          {f'<div class="henoko-concerns"><h4>立場をこえて同じ心配</h4>{concern_html}</div>' if concern_html else ''}
          {f'<div class="henoko-editorials"><h4>編集部の横断整理</h4>{editorial_html}</div>' if editorial_html else ''}
        </div>
      </section>
    </div>
  </article>
</template>'''
        )
    generated = START + "\n" + "\n".join(templates) + "\n" + END
    return re.sub(r"(?m)^[ \t]+$", "", generated)


def json_background() -> dict:
    import json

    path = ROOT / "data/verification/henoko-student-accident-background.json"
    return json.loads(path.read_text(encoding="utf-8"))
