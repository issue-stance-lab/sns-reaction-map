#!/usr/bin/env python3
"""学校でのあだ名禁止ページの新デザイン（冒頭＋山なみ＋6論点の読書面＋背景）を、公開候補として組み立てる。

高齢者免許返納（scripts/build_elderly_redesign.py。自転車の青切符・憲法改正論議と同じ型）を写した。
本文は新デザインの生成器（scripts/nickname_opening.py・nickname_reading.py・nickname_background.py）が
公開JSON・再読データ・立場の対応表・設定・一次資料メモから作る。現行ページ（元HTML）からは、利用者や外部サービスとの約束に
なっている部品だけを文字どおり引き継ぐ。

  - title・SEOメタ（description・canonical・OGP・Twitter）・Article JSON-LD（そのまま）
  - GA4・AdSense のタグ（release のときだけ。preview には載せない）
  - google-adsense-account（元HTMLにあれば）・Webフォント
  - 投票（topic_id・論点6つと立場3つの順番と中身・choiceIdx の計算・保存キーを変えない。前置きの文も元のまま）。
    元のスクリプトは投票の後に、旧ページにも無い #issue-arena-section へ移ろうとして止まる（TypeError）。この1文だけを外す
  - 調査条件（#caution）と PLANET_DATA（既存の公開検査が読む公開データの契約）
  - 対話式の山なみ（PLANET_SECTION の #planet-block・PLANET_DATA・山なみのスクリプト）。立場モード・100マス・論点の一覧・
    見かたをそのまま写し、新デザインで使わない部分（予想2問・一次資料クイズ・資料にしかない話・編集部の横断整理・
    JSなし用の論点別本文）だけを外す。山を押すと読書面へ移る（planet.js）
  - 前の収集回との比較（潮目のカード TIDE_CARD。adapter の _apply_tide が元HTMLに貼る）。
    要約（小さな折れ線と見出し）の下の折りたたみへ1文字も変えずに入れる。論点ごとの小さな折れ線もこの数字から描く
  - このページの作り方（ARTICLE_TRUST）・調査上の注意（#detail-data。あだ名禁止の元HTMLでは表を持たず「読み方」の注意だけ）
    を1つの折りたたみに入れる。次に読むテーマとそのクリック計測・フッター
  - 旧アンカー（#school-nickname-guide・#stance-glance・#bukatsu-background・#fb-{論点ID} など）は、新しい置き場所へ読み替える

FAQ の JSON-LD は、新デザインで画面に出す問い（冒頭の短答2問と背景の「よくある質問」4問）から作り直す
（画面と構造化データを一致させる。元HTMLの SCHOOL_NICKNAME_FAQ_JSONLD は使わない）。旧ページの検索入口
（SCHOOL_NICKNAME_SEARCH_ENTRY）・連動表示（scripts/school_nickname_connected*.py・docs/school-nickname-connected*.js/css）・
アリーナの点（docs/school-nickname-ban-arena-data.js）・論点カード（NICKNAME_ISSUE_MEDIA）は新デザインでは読み込まない
（更新経路では元HTMLの中で引き続き作り直され、アリーナの点のファイルも更新経路で生成され続ける）。

docs/ へは直接書き出さない（公開切替は scripts/nickname_layout.py の finish が行う）。

    python3 scripts/build_nickname_redesign.py --mode release --output-dir quality/prototypes/school-nickname-ban-release
    python3 scripts/build_nickname_redesign.py --mode preview --output-dir /tmp/nickname-preview
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import re
import sys
from datetime import date
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parents[1]
PAGE = "school-nickname-ban-reaction-map.html"
PUBLIC = "docs/data/themes/school-nickname-ban.json"
ASSETS = Path("scripts/nickname_redesign")
MARKER = 'name="nickname-layout"'
LAYOUT_VERSION = "redesign-v1"
VOTE_TOPIC = "school-nickname-ban-issue-stance-v1"
VOTE_STORAGE_KEY = "nickname-arena-vote"
VOTE_CHOICE = "choiceIdx:issueIndex*stances.length+stanceIndex"
# 投票の後に、旧ページにも無い #issue-arena-section へ移ろうとする1文（getElementById が null で TypeError になる）。
# 新ページでは結果をその場に出すだけにする。元HTMLのこの1文が変わったら止まる
VOTE_ARENA_SCROLL = ("if(shouldScroll!==false)setTimeout(function(){document.getElementById('issue-arena-section')"
                     ".scrollIntoView({behavior:'smooth'});},450);")
PROTECTED_BLOCKS = ("SEO_META", "ARTICLE_JSON_LD")
INTEGRATIONS = ("ADSENSE_TAG", "GA_TAG")
OPENING_ID = "school-nickname-open"
COUNT_ID = "school-nickname-opening-count"
READING_ID = "school-nickname-ban-reading"
BACKGROUND_ID = "school-nickname-ban-background"
FAQ_ID = "school-nickname-faq"
TIDE_ID = "school-nickname-ban-tide-widget"
# 旧デザインの節 → 新デザインの置き場所。外部から旧アンカー付きで来た人を迷わせない。
# 論点ごとの旧ID（fb-・extras-・school-nickname-ban-reading-）は issue-{論点ID} へ読み替える（スクリプト側）。
# #issue-{論点ID} は旧ページでも新ページでも「その論点の欄」（旧：論点カード、新：投稿を含む読書面）なので、そのまま残る。
# #school-nickname-faq は旧ページのFAQの節で、新ページでは背景の「よくある質問」の行（同じid）。
ALIASES = {
    "progress": OPENING_ID,
    # 旧検索入口（3つのタブ：国のルール・いじめとの関係・止める呼び方の範囲）
    "school-nickname-guide": OPENING_ID,
    "school-nickname-guide-title": OPENING_ID,
    "school-nickname-guide-tab-national-rule": "nop-q-rule",
    "school-nickname-guide-panel-national-rule": "nop-q-rule",
    "school-nickname-guide-tab-harm": "bg-voices",
    "school-nickname-guide-panel-harm": "bg-voices",
    "school-nickname-guide-tab-scope": "nop-scope-title",
    "school-nickname-guide-panel-scope": "nop-scope-title",
    "stance-glance": COUNT_ID,
    "stance-glance-title": COUNT_ID,
    "stance-glance-buttons": COUNT_ID,
    "stance-glance-result": COUNT_ID,
    "stance-glance-result-text": COUNT_ID,
    "bukatsu-background": "bg-why",
    "bg-title": "bg-why",
    # 旧「同じ「禁止」でも、何をやめるルールなのか」（範囲・目的・本人の経験・見直しの確認）→ 学校のルールの決め方と見直しの行
    "bukatsu-check": "bg-school",
    "ck-title": "bg-school",
    "fallback": READING_ID,
    "fallback-nav": READING_ID,
    "quiz": READING_ID,
    "ocean": READING_ID,
    "editorial": READING_ID,
    "issue-cards": READING_ID,
    "classroom-title": "bg-classroom",
    "school-nickname-faq-title": FAQ_ID,
    # 2026-09-06 の訂正の告知（CORRECTIONS.yaml の published_urls）。告知の枠は 2026-09-13 に旧ページから外した（オーナーの指摘）ので、
    # 訂正窓口への案内がある「このページの作り方」へ送る（折りたたみを開く）
    "correction-20260906": "article-trust-title",
}
ISSUE_PREFIXES = ("fb-", "extras-", "school-nickname-ban-reading-")
# 山なみのスクリプトが要素を探すので残すが、新ページでは隠れている受け皿。旧アンカーで来たら上の読み替え先へ送る。
HIDDEN_RECEIVERS = ("fallback", "fallback-nav", "quiz", "progress")
# 山なみから外す部分（新デザインの読書面・冒頭が同じ役目を持つか、採用しないと決めたもの）
PLANET_DROP = ("section.landing-panel", "#ocean", "#editorial")
# 読み込み時の自動着地（連動表示の橋渡し SCHOOL_NICKNAME_CONNECTED_BRIDGE の initialLand）。件数最多の論点へ land() し、
# location.hash を書く（履歴が1つ増える）。さらに旧ページの論点テンプレートが無いと同じ論点へもう一度着地する
AUTO_LAND = ("    else if ((!location.hash || ['planet-block','modes','list'].indexOf(location.hash.slice(1)) >= 0) && st.landed === null){\n"
             "      var top = issues.reduce(function(a,b){ return b.count > a.count ? b : a; }); landSilently(idIndex[top.id]);\n"
             "    }\n"
             "    if (st.landed !== null && !document.getElementById('panel').querySelector('.school-nickname-selected-head')) landSilently(st.landed);\n")
# 読み込み時は、読書面の既定の論点（data-default-issue）を、ハッシュ・履歴・フォーカス・スクロールに触れずに選んでおく
AUTO_LAND_OFF = ("    /* 新デザイン（scripts/build_nickname_redesign.py）：読み込み時は読書面の既定の論点を、ハッシュ・履歴・フォーカス・位置に触れずに選ぶ */\n"
                 "    else if ((!location.hash || ['planet-block','modes','list'].indexOf(location.hash.slice(1)) >= 0) && st.landed === null){\n"
                 "      var reading = document.querySelector('[data-default-issue]'), first = reading && reading.getAttribute('data-default-issue');\n"
                 "      if (first && Object.prototype.hasOwnProperty.call(idIndex, first)){ st.landed = idIndex[first]; evacuateChart(); drawPanel(); syncList(); render(); placeChart(); }\n"
                 "    }\n")


def _block(source: str, name: str) -> str:
    match = re.search(r"<!-- " + name + r"_START -->.*?<!-- " + name + r"_END -->", source, re.S)
    if not match:
        raise ValueError(f"現行ページに保護対象 {name} がありません。出力は変更していません。")
    return match.group()


def _one(soup: BeautifulSoup, selector: str, what: str):
    nodes = soup.select(selector)
    if len(nodes) != 1:
        raise ValueError(f"現行ページの{what}（{selector}）が {len(nodes)} 個あります。1個のはずです。")
    return nodes[0]


@contextlib.contextmanager
def _generators(root: Path):
    """新デザインの生成器を、指定した root（公開候補の隔離コピーなど）の入力で動かす。"""
    sys.path.insert(0, str(ROOT / "scripts"))
    import nickname_background as background  # noqa: PLC0415
    import nickname_opening as opening  # noqa: PLC0415
    import nickname_reading as reading  # noqa: PLC0415

    saved = (opening.ROOT, background.ROOT, reading.ROOT)
    opening.ROOT = background.ROOT = reading.ROOT = root
    try:
        yield opening, reading, background
    finally:
        opening.ROOT, background.ROOT, reading.ROOT = saved


def render_body(root: Path, as_of: str | None) -> tuple[str, dict, str]:
    """冒頭・読書面・背景のHTMLと、組み立てに使うデータ・基準日を返す。数が合わなければ ValueError。"""
    with _generators(root) as (opening, reading, background):
        try:
            d = reading.load(root / "configs" / "school-nickname-ban-reading.json")
            reading.check_all(d)
            as_of = as_of or reading.default_as_of(d)
            date.fromisoformat(as_of)
            fragment = opening.fragment_for(root / d["cfg"]["opening_config"])
            body = reading.render_reading(d)
            bg = background.render(d, as_of, reading.ordered_issues(d))
        except SystemExit as exc:  # 生成器の照合は SystemExit で止まる。更新経路を巻き込まず止めるため変換する
            raise ValueError(f"新デザインの照合で停止しました: {exc}") from None
    return '<div class="nop-page">' + fragment + "</div>\n" + body + bg, d, as_of


def _classroom(soup: BeautifulSoup) -> None:
    """授業用の行を、サイト共通の授業節の約束（印刷ボタン・資料・問い・GA4の計測）に合わせる。"""
    body = soup.select_one("#bg-classroom .fb-body")
    if body is None:
        raise ValueError("背景の「授業や話し合いで使う」が見つかりません")
    inner = soup.new_tag("div", attrs={"class": "classroom-section"})
    for child in list(body.contents):
        inner.append(child.extract())
    body.append(inner)
    labels = inner.select("p.fb-src-label")
    if len(labels) != 2:
        raise ValueError("授業の行に「資料」と「問い」の見出しがそろっていません")
    for label, cls, follower in ((labels[0], "classroom-sources", "ul"), (labels[1], "classroom-questions", "ol")):
        box = soup.new_tag("div", attrs={"class": cls})
        nxt = label.find_next_sibling(follower)
        if nxt is None:
            raise ValueError(f"授業の行の「{label.get_text()}」の一覧が見つかりません")
        label.insert_before(box)
        box.append(label.extract())
        box.append(nxt.extract())
    button = soup.new_tag("button", type="button", attrs={"class": "classroom-print-btn"})
    button.string = "この節を印刷する"
    wrap = soup.new_tag("p", attrs={"class": "fb-print"})
    wrap.append(button)
    inner.append(wrap)
    inner.insert_before(Comment(" CLASSROOM_START "))
    inner.insert_after(Comment(" CLASSROOM_END "))


def faq_items(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """画面に出す問いと答え：冒頭の短答2問（問いと、その下の1文の答え）と、背景の「よくある質問」4問。
    冒頭の「確認できたこと／確認できないこと」の箇条は答えの根拠なので、構造化データの答えには入れない。"""
    opening = [(a.select_one(".nop-answer__q").get_text(strip=True), a.select_one(".nop-answer__short").get_text(strip=True))
               for a in soup.select("article.nop-answer")]
    background = [(i.dt.get_text(strip=True), i.dd.get_text(strip=True)) for i in soup.select(f"#{FAQ_ID} dl.fb-faq > div")]
    return opening + background


def _faq_json_ld(soup: BeautifulSoup) -> str:
    if not soup.select(f"#{FAQ_ID} dl.fb-faq > div") or not soup.select("article.nop-answer"):
        raise ValueError("冒頭の短答か背景の「よくある質問」が見つかりません")
    payload = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq_items(soup)
        ],
    }
    return ("<!-- FAQ_JSON_LD_START -->\n<script type=\"application/ld+json\">\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + "\n</script>\n<!-- FAQ_JSON_LD_END -->")


def _vote_section(src: BeautifulSoup) -> str:
    section = _one(src, "#vote-section", "投票")
    if section.get("data-vote-topic") != VOTE_TOPIC:
        raise ValueError(f"投票の topic_id が想定と違います: {section.get('data-vote-topic')}")
    script = next((s for s in src.select("script:not([src])")
                   if s.string and f"var TOPIC='{VOTE_TOPIC}'" in s.string), None)
    if script is None:
        raise ValueError("投票のスクリプトが見つかりません")
    code = script.string
    old_key = f"var STORAGE_KEY='{VOTE_STORAGE_KEY}';"
    if code.count(old_key) != 1 or VOTE_CHOICE not in code:
        raise ValueError("投票の保存キーか choiceIdx の計算が想定と違います")
    if code.count(VOTE_ARENA_SCROLL) != 1:
        raise ValueError("投票の後のアリーナへの移動（#issue-arena-section）が想定どおりにありません。元HTMLの投票を確かめてください。")
    # 本番ホストでだけ既存の保存キー。確認用の環境では別キーに保存し、本番の投票済み記録に触らない。
    preview_key = VOTE_STORAGE_KEY + "-preview"
    code = code.replace(old_key, f"var STORAGE_KEY=window.SNS_REDESIGN_PRODUCTION?'{VOTE_STORAGE_KEY}':'{preview_key}';")
    # 旧ページにも無い #issue-arena-section へ移ろうとして TypeError になる1文を外す（結果はその場に出る）
    code = code.replace(VOTE_ARENA_SCROLL, "/* 新デザイン：投票の結果はその場に出す（旧ページのアリーナへの移動は外した） */")
    section = BeautifulSoup(str(section), "html.parser").section
    section["class"] = ["cap-band", "cap-vote"]
    return str(section) + "\n<script>" + code + "</script>"


def _band(src: BeautifulSoup, selector: str, what: str, cls: str) -> BeautifulSoup:
    node = BeautifulSoup(str(_one(src, selector, what)), "html.parser").find(True)
    node["class"] = list(node.get("class") or []) + ["cap-band", cls]
    return node


def _detail(src: BeautifulSoup) -> str:
    """調査上の注意（#detail-data）：あだ名禁止の元HTMLでは表を持たず、「読み方」の注意だけ。元HTMLのまま残す。"""
    node = _band(src, "#detail-data", "調査上の注意", "cap-detail")
    if not node.find_all("details", recursive=False):
        raise ValueError("調査上の注意（#detail-data）に中身がありません")
    return str(node)


def _tide(source: str) -> tuple[str, str]:
    """前回の収集との比較（潮目のカード）を、枠ごと文字どおり引き継ぐ。CSS も元HTMLの区間から取る。"""
    match = re.search(r'<section class="update-dashboard"[^>]*><!-- TIDE_CARD_START -->.*?<!-- TIDE_CARD_END --></section>',
                      source, re.S)
    if not match:
        raise ValueError("現行ページに「前回の収集との比較」（TIDE_CARD）がありません。出力は変更していません。")
    css = re.search(r"/\* TIDE_CARD_START \*/.*?/\* TIDE_CARD_END \*/", source, re.S)
    if not css:
        raise ValueError("現行ページに「前回の収集との比較」の見た目（TIDE_CARD の CSS）がありません。")
    if f'id="{TIDE_ID}"' not in match.group():
        raise ValueError(f"潮目のカードの id が {TIDE_ID} ではありません。")
    return match.group(), css.group()


def _tide_data(tide: str) -> dict:
    """潮目のカードのスクリプトが持つ前回・今回の割合（立場・論点）と、比べた収集日を読む。小さな折れ線はこの数字だけで描く。"""
    match = re.search(r"const datasets = (\{.*?\});\n", tide, re.S)
    period = re.search(r'<span class="tide-widget-period">(\d{1,2})月(\d{1,2})日 → (\d{1,2})月(\d{1,2})日</span>', tide)
    if not match or not period:
        raise ValueError("潮目のカードに前回・今回の割合（datasets）か比べた日付がありません。")
    data = json.loads(match.group(1))
    for key in ("stance", "issue"):
        rows = (data.get(key) or {}).get("rows") or []
        if not rows or any(not isinstance(r.get("previous"), (int, float)) or not isinstance(r.get("current"), (int, float))
                           for r in rows):
            raise ValueError(f"潮目のカードの {key} の割合が読めません。")
    m1, d1, m2, d2 = map(int, period.groups())
    data["labels"] = (f"{m1}月{d1}日", f"{m2}月{d2}日")
    return data


def _spark(rows: list[dict], colors: list[str], label: str, width: int = 320, height: int = 72) -> str:
    """前回と今回を結ぶ小さな折れ線（軸の目盛りなし）。割合だけを使い、件数は描かない。"""
    left, right, top, bottom = 6, width - 6, 8, height - 8
    values = [v for r in rows for v in (r["previous"], r["current"])]
    lo, hi = min(values), max(values)
    pad = max(2.0, (hi - lo) * 0.15)
    lo, hi = max(0.0, lo - pad), min(100.0, hi + pad)
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">',
           f'<line x1="{left}" x2="{right}" y1="{bottom}" y2="{bottom}" stroke="#d9dee4"/>']
    for row, color in zip(rows, colors):
        ys = [bottom - (bottom - top) * (v - lo) / (hi - lo) for v in (row["previous"], row["current"])]
        out.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round" '
                   f'points="{left:.1f},{ys[0]:.1f} {right:.1f},{ys[1]:.1f}"/>')
        for x, y in ((left, ys[0]), (right, ys[1])):
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}" stroke="#fff" stroke-width="1.5"/>')
    out.append("</svg>")
    return "".join(out)


def _issue_glances(body_soup: BeautifulSoup, tide: dict, compact: dict) -> None:
    """読書面の「前の収集回との違い」に、潮目の論点の前回・今回の割合から小さな折れ線と数字2つを入れる。
    「その他」は潮目の論点に無いので、注記と比較への案内だけになる。"""
    rows = {r["label"]: r for r in tide["issue"]["rows"]}
    first, last = tide["labels"]
    for box in body_soup.select(".fr-glance[data-glance]"):
        row = rows.get(box["data-glance"])
        if row is None:
            continue
        cap = compact["glance_caption"].format(first_date=first, first=f'{row["previous"]:.1f}',
                                               last_date=last, last=f'{row["current"]:.1f}')
        chart = box.select_one(".fr-glance-chart")
        chart.append(BeautifulSoup(_spark([row], ["currentColor"], box["data-glance"] + "。" + cap)
                                   + f'<p class="fr-glance-cap">{escape(cap)}</p>', "html.parser"))


def _tide_band(tide_html: str, tide: dict, d: dict, compact: dict) -> str:
    """前回の収集との比較：要約（見出し・立場ごとの小さな折れ線・カードの見出しの1文）と、元の潮目のカードを丸ごと入れた折りたたみ。
    潮目のカード（TIDE_CARD）は1文字も変えずに折りたたみの中へ入れる。"""
    card = BeautifulSoup(tide_html, "html.parser")
    headline = card.select_one("[data-tide-headline]")
    period = card.select_one(".tide-widget-period")
    if headline is None or period is None:
        raise ValueError("潮目のカードの見出しか比べた日付が見つかりません。")
    color = {s["label"]: s["color"] for s in d["planet"]["stances"]}
    rows = tide["stance"]["rows"]
    if any(r["label"] not in color for r in rows):
        raise ValueError("潮目のカードの立場が planet 設定にありません。")
    colors = [color[r["label"]] for r in rows]
    legend = "".join(f'<li><i style="background:{escape(color[r["label"]])}"></i>{escape(r["label"])}</li>' for r in rows)
    first, last = tide["labels"]
    aria = f"{first}収集分と{last}収集分の、立場ごとの割合の比較"
    return ('<div class="cap-trend" id="cap-trend"><section class="cap-trend-glance" aria-labelledby="cap-trend-title">'
            f'<p class="fr-eyebrow">{escape(compact["trend_eyebrow"])}</p>'
            f'<h2 id="cap-trend-title">{escape(compact["trend_title"])}</h2>'
            f'<div class="cap-trend-spark">{_spark(rows, colors, aria, 480, 96)}</div>'
            f'<ul class="cap-trend-legend">{legend}</ul>'
            f'<p class="cap-trend-lead">{escape(period.get_text())}：{escape(headline.get_text())}</p>'
            f'<p class="fr-fine">{escape(compact["trend_note"])}</p>'
            f'<details class="fr-fold cap-trend-more" id="cap-trend-more"><summary>{escape(compact["trend_more"])}</summary>'
            + tide_html + "</details></section></div>")


def _header() -> str:
    # topic-modern.js が後から差し込む共通ヘッダーと同じ中身（皇室典範・副首都・憲法と同じ）。JavaScriptなしでもトップへ戻れるよう静的に置く。
    # 元HTMLには静的な共通ヘッダーが無い（ヒーローの「トップ」リンクだけ）ので、ここで作る。
    return ('<header class="modern-site-header"><div class="modern-header-inner">'
            '<a class="modern-logo" href="index.html" aria-label="SNS反応まっぷ トップ">'
            '<span class="modern-logo-mark" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></span>'
            '<span class="modern-logo-text">SNS反応まっぷ</span></a>'
            '<nav class="modern-nav" aria-label="メインナビゲーション">'
            '<a href="index.html#topics">テーマ一覧</a><a href="index.html#featured-questions">注目の問い</a>'
            '<a href="about.html">データについて</a><a href="usage.html">使い方</a>'
            '<a href="usage.html#faq">よくある質問</a></nav>'
            '<a class="modern-header-button" href="index.html#topics">テーマを見る</a></div></header>')


def _planet(source: str) -> tuple[str, str]:
    """元HTMLの山なみ（PLANET_SECTION）を写す。返り値は（#planet-block を含む節＋PLANET_DATA＋山なみのスクリプト, PLANET_DATA）。

    山なみの見た目・数字・動きは元HTMLの生成器（refresh_planet_section.py --for-docs と連動表示の橋渡し）が作ったものをそのまま使う。
    ここで変えるのは、新デザインで出さない部分を外すことと、調査条件を RESEARCH_CONDITIONS で囲むことだけ。
    """
    match = re.search(r"<!-- PLANET_SECTION_START -->(.*?)<!-- PLANET_SECTION_END -->", source, re.S)
    if not match:
        raise ValueError("現行ページに山なみ（PLANET_SECTION）がありません。出力は変更していません。")
    soup = BeautifulSoup(match.group(1), "html.parser")
    sections = soup.select("section.planet-panel")
    contracts = soup.select("script#planet-data")
    if len(sections) != 1 or len(contracts) != 1:
        raise ValueError("山なみの節（section.planet-panel）か PLANET_DATA が1つではありません。")
    section, contract = sections[0], contracts[0]
    scripts = [s for s in soup.find_all("script", recursive=False) if s is not contract]
    if len(scripts) != 1 or "window.PLANET_DATA" not in (scripts[0].string or ""):
        raise ValueError("山なみのスクリプトが見つからないか、想定と違います。")
    block = section.select_one("#planet-block")
    for selector in ("#modes", "#section", "#panel", "#dotbox", "#waffle", "#fallback-nav", "#list", "#meta",
                     "#caution", "#guesses", "#quiz", "#dive"):
        if block is None or len(block.select(selector)) != 1:
            raise ValueError(f"山なみの部品 {selector} が1つではありません。")
    for selector in PLANET_DROP:
        for node in block.select(selector):
            node.decompose()
    # 旧ページで JSなし用の論点別本文の前にあった目印（span.issue-anchor）。あだ名禁止の元HTMLには無いが、あれば外す
    # （新ページでは #issue-{論点ID} は読書面の欄が持つ。同じidを2つ置かない）
    for node in block.select("span.issue-anchor"):
        node.decompose()
    # 予想2問と一次資料クイズは新デザインで出さない（冒頭の短答・論点ごとの照合が同じ役目）。
    # 山なみのスクリプトが中身を作るので、受け皿だけ隠して残す。
    block.select_one("#guesses")["hidden"] = ""
    quiz = block.select_one("#quiz")
    quiz["hidden"] = ""
    heading = quiz.find_previous_sibling("h3")
    if heading is not None and "sec-live" in (heading.get("class") or []):
        heading.decompose()
    # JSなしの論点一覧は、新デザインの読書面（#issue-{論点ID}）へ直接つなぐ
    for a in block.select("#fallback-nav a[href^='#fb-']"):
        a["href"] = "#issue-" + a["href"][len("#fb-"):]
    caution = block.select_one("#caution")
    wrap = soup.new_tag("div", attrs={"class": "cap-research", "id": "research-conditions"})
    caution.wrap(wrap)
    wrap.insert_before(Comment(" RESEARCH_CONDITIONS_START "))
    wrap.insert_after(Comment(" RESEARCH_CONDITIONS_END "))
    # 連動表示の橋渡し（SCHOOL_NICKNAME_CONNECTED_BRIDGE）は、読み込み時に件数最多の論点へ自動で着地する（location.hash を書き、履歴が1つ増え、
    # 読書面もその論点に切り替わる）。新ページでは読書面の既定の論点を保ち、「戻る」で前のページへ戻れるよう、この自動着地を
    # 「読書面の既定の論点を、ハッシュ・履歴・フォーカス・位置に触れずに選ぶ」に置き換える（#issue-… などのハッシュ付きで来たときの着地はそのまま）。
    # 旧ページの論点テンプレート（template#school-nickname-ban-reading-…）は写さないので、選択パネルは山なみ本来の表示（100マス・件数・立場）になる。
    code = scripts[0].string
    if code.count(AUTO_LAND) != 1:
        raise ValueError("山なみのスクリプトに、読み込み時の自動着地（initialLand）が想定どおりにありません。")
    scripts[0].string = code.replace(AUTO_LAND, AUTO_LAND_OFF)
    section["class"] = list(section.get("class") or []) + ["cap-planet"]
    # 山なみのスクリプトは「探ったところ」の進捗表示（#progress）にも書き込む。新デザインでは出さない（内容対応表 4）ので、
    # 書き込み先だけを隠して置く（無いとスクリプトが途中で止まり、図が静的表示に戻る）。
    progress = ('<div id="progress" class="cap-planet-progress" hidden aria-hidden="true">'
                '<i id="pbar"></i><span id="pseg"></span><b id="pnum"></b></div>')
    html = str(section) + "\n" + progress + "\n" + str(contract) + "\n" + str(scripts[0])
    return html, str(contract)


def _alias_script() -> str:
    # 旧ページの検索入口は、論点の素のID（#school-nickname-ban-uniform-rule など）も節の目印に使っていた。
    # 外から素のIDで来たときだけ（読み込み時）その論点の欄へ送る。読み込み後の素のIDのハッシュは山なみ自身の着地（planet.js）に任せる
    return ("<script>(()=>{const aliases=" + json.dumps(ALIASES) + ",prefixes=" + json.dumps(ISSUE_PREFIXES) + ";"
            "function resolve(initial){let id=decodeURIComponent(location.hash.slice(1));"
            "if(!id)return;const cur=document.getElementById(id);if(cur&&cur.getClientRects().length)return;"
            "const pre=prefixes.find(x=>id.startsWith(x));"
            "if(pre&&document.getElementById('issue-'+id.slice(pre.length)))id='issue-'+id.slice(pre.length);"
            "else if(aliases[id])id=aliases[id];"
            "else if(initial&&!cur&&document.getElementById('issue-'+id))id='issue-'+id;else return;"
            "location.replace('#'+id);const t=document.getElementById(id);if(t&&t.tagName==='DETAILS')t.open=true;}"
            # 折りたたみの中の場所（潮目のカード・作り方・詳細データ・背景の行など）へ来たら、外側の折りたたみを開いて見せる
            "function openRow(){const t=document.getElementById(decodeURIComponent(location.hash.slice(1)));"
            "if(!t)return;let d=t.tagName==='DETAILS'?t:t.closest('details'),moved=false;"
            "while(d){if(!d.open){d.open=true;moved=true;}d=d.parentElement&&d.parentElement.closest('details');}"
            "if(moved)requestAnimationFrame(()=>t.scrollIntoView({block:'start'}));}"
            # 読書面の「収集回ごとの比較へ」：折りたたみを開き、潮目のカードを「論点の変化」に切り替えてから移る
            "document.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('a[data-tide-mode]');if(!a)return;"
            "const id=a.getAttribute('href').slice(1),t=document.getElementById(id);if(!t)return;e.preventDefault();"
            "const d=t.closest('details');if(d)d.open=true;"
            "const b=t.querySelector('[data-tide-mode=\"'+a.dataset.tideMode+'\"]');if(b&&b.getAttribute('aria-pressed')!=='true')b.click();"
            "history.replaceState(null,'','#'+id);requestAnimationFrame(()=>t.scrollIntoView({block:'start'}));});"
            "addEventListener('hashchange',()=>{resolve(false);openRow();});resolve(true);openRow();})();</script>")


def compose(source: str, root: Path, mode: str, as_of: str | None = None) -> str:
    if MARKER in source:
        raise ValueError("新デザインのページは入力にできません。data/page-sources の元HTMLを渡してください。")
    src = BeautifulSoup(source, "html.parser")
    body, d, as_of = render_body(root, as_of)
    assets = root / ASSETS
    css = "\n".join((assets / name).read_text(encoding="utf-8")
                    for name in ("opening.css", "reading.css", "production.css"))
    reading_js = (assets / "reading.js").read_text(encoding="utf-8")
    planet_js = (assets / "planet.js").read_text(encoding="utf-8")

    title = _one(src, "head > title", "title").get_text()
    fonts = "\n".join(str(n) for n in src.select('link[rel="preconnect"], link[href*="fonts.googleapis.com/css2"]'))
    adsense_meta = "\n".join(str(n) for n in src.select('meta[name="google-adsense-account"]'))
    planet, contract_html = _planet(source)
    contract = BeautifulSoup(contract_html, "html.parser").script
    opinions = int(d["public"]["opinion_count"])
    if f'"opinions":{opinions}' not in contract.get_text().replace(" ", ""):
        raise ValueError("PLANET_DATA の意見数が公開JSONと一致しません。元HTMLの更新を先に済ませてください。")
    trust = _block(source, "ARTICLE_TRUST")
    if f"{opinions:,}件" not in trust and f"{opinions}件" not in trust:
        raise ValueError("「このページの作り方」の意見数が公開JSONと一致しません。元HTMLの更新を先に済ませてください。")
    tide_html, tide_css = _tide(source)
    tide = _tide_data(tide_html)
    # 潮目の「今回」は adapter が比べた収集回（新規0件の回は前回のまま残り得る）。公開JSONの更新日より後なら入力の取り違えとして止める。
    updated = date.fromisoformat(d["public"]["updated_on"])
    m, dd = map(int, re.match(r"(\d+)月(\d+)日", tide["labels"][1]).groups())
    # カードの日付に年は無い。更新日より半年以上先の月なら前の年の収集とみなす（12月の収集を1月に更新する場合）
    compared = date(updated.year - (1 if m > updated.month + 6 else 0), m, dd)
    if compared > updated:
        raise ValueError("潮目のカードの比較日が公開JSONの更新日より後です。元HTMLの更新を先に済ませてください。")

    head = ['<!doctype html>', '<html lang="ja">', '<head>', '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{title}</title>"]
    head += [_block(source, name) for name in PROTECTED_BLOCKS]
    if mode == "preview":
        head.append('<meta name="robots" content="noindex">')
    head += [x for x in (adsense_meta, fonts) if x]
    head += ['<link rel="stylesheet" href="site-tokens.css?v=3">',
             '<link rel="stylesheet" href="topic-modern.css?v=32">',
             f'<meta name="nickname-layout" content="{LAYOUT_VERSION}">',
             "<style>\n" + css + "\n" + tide_css + "\n</style>",
             '<script src="topic-modern.js?v=13" defer></script>',
             '<script src="vote-config.js?v=1"></script>',
             "<script>window.SNS_REDESIGN_PRODUCTION=" +
             ("location.hostname==='sns-reaction-map.jp'" if mode == "release" else "false") +
             ";if(!window.SNS_REDESIGN_PRODUCTION)window.SNS_VOTE_CONFIG={};</script>",
             '<script src="vote-store.js?v=1"></script>']
    if mode == "release":
        head += [_block(source, name) for name in INTEGRATIONS]
    head.append("</head>")

    body_soup = BeautifulSoup(body, "html.parser")
    opening_section = body_soup.select_one("div.nop-page > section.nop")
    if opening_section is None:
        raise ValueError("冒頭の部品（section.nop）が見つかりません")
    opening_section["id"] = OPENING_ID
    if body_soup.select_one(f"#{COUNT_ID}") is None:
        raise ValueError(f"冒頭の件数欄（#{COUNT_ID}）が見つかりません")
    # 元HTMLの対話式の山なみを、読書面の見出しと論点タブのあいだに置く（調査条件は山なみの中、図の母数の位置）
    reading_section = body_soup.select_one(f"#{READING_ID}")
    panels = reading_section.select_one(".fr-panels") if reading_section else None
    if panels is None:
        raise ValueError("読書面の論点の欄（.fr-panels）が見つかりません")
    map_box = body_soup.new_tag("div", attrs={"class": "fr-map cap-map"})
    map_box.append(BeautifulSoup(planet, "html.parser"))
    panels.insert_before(map_box)
    compact = d["cfg"]["compact"]
    _issue_glances(body_soup, tide, compact)
    _classroom(body_soup)
    faq = _faq_json_ld(body_soup)
    head.insert(head.index("</head>"), faq)
    body_html = str(body_soup)
    if "../../../docs/" in body_html:
        raise ValueError("試作用の相対パスが残っています")
    start, end = "<!-- SCHOOL_NICKNAME_READING_START -->", "<!-- SCHOOL_NICKNAME_READING_END -->"
    reading_start = body_html.index(start)
    reading_end = body_html.index(end) + len(end)
    body_html = (body_html[:reading_start] + "<!-- PLANET_SECTION_START -->\n" + body_html[reading_start:reading_end]
                 + "\n<!-- PLANET_SECTION_END -->" + body_html[reading_end:])
    # X投稿は開いたときに読み込む（部活動・皇室・副首都・生成AI・憲法・自転車と同じ部品）。保護対象の head を作り直さないよう、本文だけに掛ける。
    sys.path.insert(0, str(ROOT / "scripts"))
    from bukatsu_redesign.x_embeds import add_x_embeds  # noqa: PLC0415
    embedded = BeautifulSoup(add_x_embeds("<html><head></head><body>" + body_html + "</body></html>"), "html.parser")
    x_style = "".join(str(n) for n in embedded.head.select("style"))
    x_script = str(embedded.body.select("script")[-1].extract())
    body_html = embedded.body.decode_contents()
    head.insert(head.index("</head>"), x_style)
    background_at = body_html.rindex("<section", 0, body_html.index(f'id="{BACKGROUND_ID}"'))

    page = "\n".join(head) + "\n"
    page += '<body class="nickname-layout">\n'
    if mode == "preview":
        page += '<p class="cap-preview">公開前の確認用ページ（投票は送信されません）</p>\n'
    page += _header() + "\n<main>\n"
    page += (body_html[:background_at] + _tide_band(tide_html, tide, d, compact) + "\n"
             + _vote_section(src) + "\n" + body_html[background_at:])
    # 作り方と調査上の注意は、部活動・生成AI・憲法・高齢者と同じく1つの折りたたみに入れる（どちらも元HTMLのまま）
    page += (f'<details class="cap-band cap-fold cap-method" id="cap-method"><summary>{escape(compact["method_fold"])}</summary>'
             '<div class="cap-trust">' + trust + "</div>\n" + _detail(src) + "</details>\n")
    page += str(_band(src, "#related-topics", "次に読むテーマ", "cap-related")) + "\n</main>\n"
    page += str(_one(src, "body > footer", "フッター")) + "\n"
    # 次に読むテーマのクリック計測（GA4 の related_theme_click）。元HTMLのスクリプトを文字どおり引き継ぐ
    page += str(_one(src, "script#related-theme-tracking", "次に読むテーマの計測")) + "\n"
    page += "<script>" + reading_js + "</script>\n"
    page += "<script>" + planet_js + "</script>\n"
    page += x_script + "\n" + _alias_script() + "\n"
    page += '<script src="share-x-btn.js"></script>\n</body>\n</html>\n'
    return page


def build(source_page: Path, output_dir: Path, mode: str = "preview", root: Path = ROOT,
          as_of: str | None = None) -> dict:
    source_page, output_dir, root = Path(source_page).resolve(), Path(output_dir).resolve(), Path(root).resolve()
    docs = (root / "docs").resolve()
    if output_dir == docs or docs in output_dir.parents:
        raise ValueError("公開先docsへ直接出力できません。公開候補用の別フォルダを指定してください。")
    if mode not in ("preview", "release"):
        raise ValueError(f"mode は preview か release です: {mode}")
    source = source_page.read_text(encoding="utf-8")
    # 基準日は既定で公開JSONの更新日。同じデータなら同じページになる
    as_of = as_of or json.loads((root / PUBLIC).read_text(encoding="utf-8"))["updated_on"]
    page = compose(source, root, mode, as_of)
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / PAGE
    temporary = target.with_suffix(".html.tmp")
    temporary.write_text(page, encoding="utf-8")
    temporary.replace(target)
    manifest = {
        "mode": mode,
        "as_of": as_of,
        "layout": LAYOUT_VERSION,
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "files": {PAGE: hashlib.sha256(page.encode()).hexdigest()},
    }
    (output_dir / "build-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                                    encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source-page", type=Path, default=None, help="元HTML（既定は更新元。新デザイン公開後は data/page-sources）")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("preview", "release"), default="preview")
    parser.add_argument("--as-of", help="背景の基準日 YYYY-MM-DD（既定は公開JSONの更新日）")
    args = parser.parse_args()
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.nickname_layout import source_for_refresh
    try:
        result = build(args.source_page or source_for_refresh(ROOT), args.output_dir, args.mode, as_of=args.as_of)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Built {len(result['files'])} file ({args.mode}, as_of {result['as_of']}); no deployment performed.")


if __name__ == "__main__":
    main()
