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
SEARCH_START = "<!-- SCHOOL_NICKNAME_SEARCH_ENTRY_START -->"
SEARCH_END = "<!-- SCHOOL_NICKNAME_SEARCH_ENTRY_END -->"
FAQ_START = "<!-- SCHOOL_NICKNAME_FAQ_START -->"
FAQ_END = "<!-- SCHOOL_NICKNAME_FAQ_END -->"
FAQ_JSONLD_START = "<!-- SCHOOL_NICKNAME_FAQ_JSONLD_START -->"
FAQ_JSONLD_END = "<!-- SCHOOL_NICKNAME_FAQ_JSONLD_END -->"


FAQS = [
    (
        "学校のあだ名禁止は法律で決まっていますか？",
        "今回確認した、いじめ防止対策推進法、文部科学省の基本方針、生徒指導提要には、あだ名禁止を全国一律に求める記述は見当たりません。学校ごとの方針と、国の法律・通知は分けて確認する必要があります。",
    ),
    (
        "文部科学省は、あだ名禁止や全員のさん付けを求めていますか？",
        "今回確認した文部科学省資料には、あだ名禁止や全員のさん付けを全国一律に求める記述は見当たりません。生徒指導提要は、校則の理由を説明し、児童生徒や保護者の意見を聞きながら見直すことが望ましいとしています。",
    ),
    (
        "なぜ小学校であだ名禁止が行われるのですか？",
        "嫌な呼び方やからかいを未然に防ぐこと、性別で敬称を分けないことなどが理由として挙げられます。ただし目的や適用範囲は学校によって異なるため、その学校の説明を確認する必要があります。",
    ),
    (
        "嫌なあだ名は、いじめに当たりますか？",
        "あだ名という形式だけでは決まりません。法律は、一定の関係にある相手から影響を受け、本人が心身の苦痛を感じている行為をいじめと定義しています。冗談やふざけ合いに見えても、受け手の被害性を確認する必要があります。",
    ),
    (
        "あだ名禁止と、全員をさん付けで呼ぶことは同じですか？",
        "同じではありません。悪意ある呼び方を止める、あだ名を一律に使わない、呼び捨てを避ける、敬称をさんに統一する、という選択はそれぞれ範囲と目的が違います。",
    ),
    (
        "あだ名禁止のメリットとして挙げられることは何ですか？",
        "SNSでは、嫌な呼び方を早い段階で止めやすいことや、呼ばれる側が断りにくい状況を減らせることが期待として語られています。これは制度の効果を証明したものではなく、収集した投稿に見られた意見です。",
    ),
    (
        "あだ名禁止のデメリット・懸念は何ですか？",
        "SNSでは、親しい愛称まで失われること、表面的な禁止だけでは悪意や関係性が変わらないこと、本人の希望が置き去りになることが懸念として語られています。これも収集した投稿に見られた意見です。",
    ),
    (
        "本人が希望するあだ名も禁止すべきですか？",
        "国の資料だけから一律の答えは出せません。本人の希望を認めるか、どの場面までルールを適用するかは学校ごとの選択です。本人が嫌だと言えることと、希望する呼び方を伝えられることの両方を確認する必要があります。",
    ),
    (
        "学校独自の呼び方のルールは見直せますか？",
        "生徒指導提要は、校則を絶えず見直し、児童生徒や保護者の意見を聞く機会を設けることが望ましいとしています。まず学校の方針、対象となる場面、理由、見直しの手続きを確認します。",
    ),
    (
        "このページのSNS比率は、世論調査ですか？",
        "いいえ。特定の検索語、期間、検索サービスで収集できた公開投稿のサンプルです。全国の賛否の割合や、あだ名禁止を導入している学校の割合を表すものではありません。",
    ),
]


def render_search_entry(data: dict, background: dict) -> str:
    checked_on = background["checked_on"]
    opinions = int(data["totals"]["opinions"])
    return f'''{SEARCH_START}
<section class="panel school-nickname-search-entry" id="school-nickname-guide" aria-labelledby="school-nickname-guide-title">
  <div class="school-nickname-guide-head">
    <p class="school-nickname-guide-kicker">最初に知りたいこと</p>
    <h2 id="school-nickname-guide-title">学校のあだ名禁止はなぜ？ 先に3点</h2>
    <p>国の資料で確認できること、学校ごとに決めること、SNSで分かれている意見を混ぜずに読みます。</p>
  </div>
  <div class="school-nickname-answer-grid">
    <article><span>国の資料</span><b>全国一律の禁止ではない</b><p>確認した法令・文科省資料には、あだ名禁止や全員のさん付けを全国一律に求める記述は見当たりません。</p></article>
    <article><span>いじめの判断</span><b>嫌な呼び名は、いじめになりうる</b><p>冗談かどうかだけでなく、呼ばれた本人が心身の苦痛を感じているかを個別に確認します。</p></article>
    <article><span>学校ごとの選択</span><b>3つのルールは別</b><p>悪意ある呼び方を止めること、あだ名を一律禁止すること、全員をさん付けにすることは別の選択です。</p></article>
  </div>
  <div class="school-nickname-opinion-bridge" aria-label="SNSで見られた期待と懸念">
    <p class="school-nickname-opinion-label">ここからはSNS上の意見</p>
    <div><article><span>期待</span><b>嫌な呼び方を先に止め、傷つく子を減らしたい</b></article><article><span>懸念</span><b>一律禁止だけでは悪意や関係性まで変わらない</b></article></div>
    <p>どちらも「子どもを傷つけたくない」という心配から、ルールの範囲について違う結論に進んでいます。</p>
  </div>
  <nav class="school-nickname-guide-links" aria-label="このページの読み方">
    <a href="#planet-block">SNS {opinions:,}意見を6論点で比べる</a>
    <a href="#school-nickname-faq">よくある質問を先に読む</a>
  </nav>
  <p class="school-nickname-guide-date">国の資料の確認日 {e(checked_on)}。個別校のルールの有無や導入校の割合を示すものではありません。</p>
</section>
{SEARCH_END}'''


def render_faq() -> str:
    rows = []
    for question, answer in FAQS:
        rows.append(f'<details><summary>{e(question)}</summary><p>{e(answer)}</p></details>')
    return f'''{FAQ_START}
<section class="panel school-nickname-faq" id="school-nickname-faq" aria-labelledby="school-nickname-faq-title">
  <div class="panel-title"><h2 id="school-nickname-faq-title">よくある質問</h2><span>法律・文科省・さん付け・いじめ</span></div>
  <p class="school-nickname-faq-lead">全国の決まりと学校ごとの運用、確認できた事実とSNS上の意見を分けて答えます。</p>
  <div class="school-nickname-faq-list">{"".join(rows)}</div>
  <aside class="school-nickname-safety-note"><b>今、嫌な呼び方でつらい場合</b><p>ルールへの賛否を決めるより先に、嫌だと感じていることを、保護者・先生・養護教諭など信頼できる大人へ伝えてください。このページは個別の相談窓口の代わりではありません。</p></aside>
</section>
{FAQ_END}'''


def render_faq_jsonld() -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": question, "acceptedAnswer": {"@type": "Answer", "text": answer}}
            for question, answer in FAQS
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return f'{FAQ_JSONLD_START}\n<script type="application/ld+json">{encoded}</script>\n{FAQ_JSONLD_END}'


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
