#!/usr/bin/env python3
"""部活動の地域移行ページの新デザイン（最新の型：冒頭＋山なみ＋7論点の読書面＋背景）を、公開候補として組み立てる。

消費税減税（scripts/build_consumption_tax_redesign.py。辺野古・あだ名禁止・高齢者・自転車・憲法と同じ型）を写した。
2026-10-10 に公開した初期型（scripts/build_bukatsu_redesign.py。凍結した editorial-source.html・template.html・parity.py を
build.py で組み、データが1件変わると editorial-review.json の指紋で止まる仕組み）の後継で、指紋は持たない。
本文は新デザインの生成器（scripts/bukatsu_opening.py・bukatsu_reading.py・bukatsu_background.py）が
公開JSON・再読データ・立場の対応表・設定・一次資料メモ・自治体カタログから作り、照合が合わなければ止まる。
現行ページ（元HTML data/page-sources/bukatsu-chiiki.html）からは、利用者や外部サービスとの約束になっている部品だけを文字どおり引き継ぐ。

  - title・SEOメタ（description・canonical・OGP・Twitter）・Article JSON-LD（そのまま）
  - GA4・AdSense のタグ（release のときだけ。preview には載せない）
  - google-adsense-account・Webフォント・site-tokens.css と topic-modern.css/js（元HTMLの版のまま）
  - 投票（topic_id・論点7つと立場3つの定義 VOTE_ISSUES・V2I・STANCES の並びと中身・choiceIdx の計算を変えない。前置きと保存の注記の文も元のまま）。
    保存キーは本番ホストだけ既存キー（確認用の環境では別キーにして本番の投票済み記録に触らない）。失敗の案内（window.voteMsg）も元HTMLの部品
  - 調査条件（#caution）と PLANET_DATA（既存の公開検査が読む公開データの契約）
  - 対話式の山なみ（PLANET_SECTION の #planet-block・PLANET_DATA・山なみのスクリプト）。立場モード・100マス・論点の一覧・
    見かたをそのまま写し、新デザインで使わない部分（予想2問・一次資料クイズ・資料にしかない話・編集部の横断整理・
    JSなし用の論点別本文）だけを外す。山なみのスクリプトは3か所だけ書き換える（PLANET_PATCHES。元の文が無ければ止まる）。
    山を押すと読書面へ移る（planet_v2.js）
  - 意見の推移（TREND_CARD。adapter が元HTMLに貼る。外部の埋め込みコードが #bukatsu-chiiki-trend-panel-stance・-issue を指す）。
    ひと目で見る要約の下の折りたたみへ1文字も変えずに入れる。論点ごとの折れ線（ひと目で見る、この論点の推移）は読書面の生成器が
    同じ数字（この元HTMLの推移）から描く
  - このページの作り方（ARTICLE_TRUST）・詳細データ（#detail-data。折りたたみは最初どれも閉じる）を1つの折りたたみに入れる。
    次に読むテーマとそのクリック計測・フッター
  - 旧アンカー（初期型の #map・#reading・#heading-{n}・#{論点ID}--{理由}・#faq・#classroom、さらに前の旧形式の #bukatsu-background・
    #fb-{論点ID}・#stance-glance など）は、新しい置き場所へ読み替える

FAQ の JSON-LD は、背景の「よくある質問」と同じ設定の items（bukatsu_background.faq_jsonld）から作り、画面の問いと答えと一致しなければ止まる
（元HTMLの build_bukatsu_arena.py の SEARCH_FAQ_JSONLD は引き継がない）。
初期型の部品（scripts/bukatsu_redesign/build.py・template.html・editorial-source.html・editorial-review.json・parity.*・refresh_inputs.py・
app.js・lower_design.py・public_trends.py・site_chrome.*・planet.js・planet.css）はこの生成器では読まない。

docs/ へは直接書き出さない（公開切替は scripts/bukatsu_layout.py の finish が行う）。全文・印刷版（bukatsu-chiiki-full.html）は、
このページと同じ生成結果からスクリプトを除いて作る（scripts/bukatsu_redesign_readable.py の readable_v2）。

    python3 scripts/build_bukatsu_redesign_v2.py --mode release --output-dir quality/prototypes/bukatsu-chiiki-release-v2
    python3 scripts/build_bukatsu_redesign_v2.py --mode preview --output-dir /tmp/bukatsu-preview
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
PAGE = "bukatsu-chiiki-reaction-map.html"
READ_PAGE = "bukatsu-chiiki-full.html"
PRINT_PAGE = "bukatsu-chiiki-classroom.html"
PUBLIC = "docs/data/themes/bukatsu-chiiki.json"
READING_CONFIG = "configs/bukatsu-chiiki-reading.json"
ASSETS = Path("scripts/bukatsu_redesign")
MARKER = 'name="bukatsu-layout"'
LAYOUT_VERSION = "redesign-v2"
VOTE_TOPIC = "bukatsu-chiiki-issue-stance-v1"
VOTE_STORAGE = "var STORAGE_KEY='sns_vote_'+TOPIC+'_my';"
VOTE_STORAGE_KEY = "sns_vote_bukatsu-chiiki-issue-stance-v1_my"
VOTE_CHOICE = "choiceIdx:issueIdx*STANCES.length+stanceIdx"
VOTE_NOTE = "※ サイト参加者の集計であり、世論調査ではありません。回答と、24時間の重複防止用に一方向変換した接続元情報をサーバーに保存します。"
PROTECTED_BLOCKS = ("SEO_META", "ARTICLE_JSON_LD")
INTEGRATIONS = ("ADSENSE_TAG", "GA_TAG")
OPENING_ID = "bukatsu-open"
COUNT_ID = "bko-count"
STEPS_ID = "bko-steps"
READING_ID = "bukatsu-chiiki-reading"
BACKGROUND_ID = "bukatsu-chiiki-background"
FAQ_ID = "bg-faq"
TREND_ID = "bukatsu-chiiki-trend"
TREND_PANELS = ("bukatsu-chiiki-trend-panel-stance", "bukatsu-chiiki-trend-panel-issue")
ISSUE = "bukatsu-chiiki-"
# 初期型の読書面の見出し #heading-{n} の n は PLANET_DATA の論点の並び（scripts/bukatsu_taxonomy.py の順）
LEGACY_ORDER = ("kyoin", "seido", "kyoiku", "ukezara", "hiyo", "sonota", "kakusa")
# 旧デザイン（初期型 2026-10-10〜、さらに前の旧形式）の節 → 新デザインの置き場所。外部から旧アンカー付きで来た人を迷わせない。
# 論点ごとの旧ID（fb-・extras-・bukatsu-reading-・illustration-）は issue-{論点ID} へ、初期型の理由の欄（{論点ID}--{理由}）は
# 新しい理由の説明（fr-r-{論点ID}-{理由}。無ければ論点の欄）へ読み替える（スクリプト側）。
# #issue-{論点ID} は旧ページでも新ページでも「その論点の場所」なので、そのまま残る。#vote-section・#detail-data・#related-topics・
# #planet-block・#caution・#research-conditions・#modes・#bukatsu-chiiki-trend-panel-* は新ページにもそのまま残る。
ALIASES = {
    # 初期型の冒頭（短答・日程の開閉・目次）
    "answers": OPENING_ID,
    "schedule": STEPS_ID,
    "faq": FAQ_ID,
    "faq-guide": FAQ_ID,
    # 初期型の「意見の全体像」（山なみの節）と読書面
    "map": "planet-block",
    "reading": READING_ID,
    "reading-announcement": READING_ID,
    "reading-progress": READING_ID,
    "issue-tabs": READING_ID,
    "comparison": READING_ID,
    "source-only": READING_ID,
    "editorial-notes": READING_ID,
    "trends": "cap-trend",
    # 初期型の背景（さらに、背景から確かめる）
    "background": BACKGROUND_ID,
    "local": "bg-municipal",
    "classroom": "bg-classroom",
    "method": "cap-method",
    # 旧形式の節
    "progress": OPENING_ID,
    "bukatsu-search-entry-title": OPENING_ID,
    "stance-glance": COUNT_ID,
    "stance-glance-title": COUNT_ID,
    "stance-glance-buttons": COUNT_ID,
    "stance-glance-result": COUNT_ID,
    "stance-glance-result-text": COUNT_ID,
    "bukatsu-background": "bg-system",
    "bg-title": "bg-system",
    "bukatsu-check": "bg-municipal",
    "ck-title": "bg-municipal",
    "local-check-tool-title": "bg-municipal",
    "classroom-title": "bg-classroom",
    "stance-map-section": "planet-block",
    "issue-cards": READING_ID,
    "bukatsu-chiiki-audit": READING_ID,
    "bukatsu-connected-data": READING_ID,
    "bukatsu-role-title": READING_ID,
    "editorial": READING_ID,
    "ocean": READING_ID,
    "fallback": READING_ID,
    "fallback-nav": READING_ID,
    "quiz": READING_ID,
    "guesses": READING_ID,
    **{f"heading-{n}": "issue-" + ISSUE + key for n, key in enumerate(LEGACY_ORDER)},
    **{f"sources-{n}": "issue-" + ISSUE + key for n, key in enumerate(LEGACY_ORDER)},
}
ISSUE_PREFIXES = ("fb-", "extras-", "bukatsu-reading-", "illustration-")
# 山なみから外す部分（新デザインの読書面・冒頭が同じ役目を持つか、採用しないと決めたもの）
PLANET_DROP = ("section.landing-panel", "#ocean", "#editorial", "span.issue-anchor")
# 山なみのスクリプトの書き換え（元の文が1回だけ無ければ止まる）。
# 1. 論点を選ぶと URL を素の論点ID（#bukatsu-chiiki-kyoin）にして履歴を1つ増やしていた。新ページの URL は読書面の #issue-{論点ID}
#    （reading.js・planet_v2.js が replaceState で書く）なので、山なみは URL に触れない
# 2. 読み込み時の「URL が素の論点IDなら land()」（画面を動かす）は外す。連動表示の橋渡しの initialLand が、
#    素の論点ID・#issue-… のどちらでも、ハッシュが無ければ件数1位の論点を、画面を動かさずに選ぶ（landSilently）
# 3. landSilently（画面を動かさない着地）は、選択パネルの見出しへフォーカスを移していた。押した人のフォーカスを残す
PLANET_PATCHES = (
    ("  location.hash=issues[i].id;\n",
     "  /* 新デザイン（scripts/build_bukatsu_redesign_v2.py）：URL は読書面の #issue-… が持つ。山なみは URL と履歴に触れない */\n"),
    ("  const h = location.hash.slice(1);\n  if (h && idIndex[h] !== undefined) land(idIndex[h]);\n",
     "  /* 新デザイン（scripts/build_bukatsu_redesign_v2.py）：読み込み時の論点は、連動表示の橋渡しの initialLand が画面を動かさずに選ぶ */\n"),
    ("  function landSilently(i){\n    var real = bringIntoView;\n    bringIntoView = function(){};\n    land(i);\n    bringIntoView = real;\n  }\n",
     "  function landSilently(i){\n    var real = bringIntoView, active = document.activeElement;\n    bringIntoView = function(){};\n"
     "    land(i);\n    bringIntoView = real;\n"
     "    /* 新デザイン（scripts/build_bukatsu_redesign_v2.py）：画面を動かさない着地では、フォーカスも元の場所に残す */\n"
     "    if (document.activeElement !== active) {\n"
     "      if (active && active !== document.body && active.focus) active.focus({preventScroll: true});\n"
     "      else if (document.activeElement && document.activeElement.blur) document.activeElement.blur();\n"
     "    }\n  }\n"),
)


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
    import bukatsu_background as background  # noqa: PLC0415
    import bukatsu_opening as opening  # noqa: PLC0415
    import bukatsu_reading as reading  # noqa: PLC0415

    saved = (opening.ROOT, background.ROOT, reading.ROOT)
    opening.ROOT = background.ROOT = reading.ROOT = root
    try:
        yield opening, reading, background
    finally:
        opening.ROOT, background.ROOT, reading.ROOT = saved


def _trend_rounds(trend: str) -> dict:
    """「意見の推移」のスクリプトが持つ回ごとの割合（立場・論点）を読む。小さな折れ線はこの数字だけで描く。"""
    match = re.search(r"const panels = (\{.*?\});\n", trend, re.S)
    if not match:
        raise ValueError("「意見の推移」のスクリプトに回ごとの割合（panels）がありません。")
    panels = json.loads(match.group(1))
    for key in ("stance", "issue"):
        panel = panels.get(key) or {}
        rounds = panel.get("rounds") or []
        if len(rounds) < 2 or any(len(r["v"]) != len(panel["labels"]) for r in rounds):
            raise ValueError(f"「意見の推移」の {key} の回ごとの割合が読めません。")
        dates = [r["d"] for r in rounds]
        if dates != sorted(set(dates)):
            raise ValueError(f"「意見の推移」の {key} の日付が重複しているか、逆順です。")
    return panels


def render_body(root: Path, as_of: str | None, panels: dict) -> tuple[str, dict, str]:
    """冒頭・読書面・背景のHTMLと、組み立てに使うデータ・基準日を返す。数が合わなければ ValueError。

    論点ごとの折れ線（読書面の生成器）は、組み立てに使う元HTMLの推移（panels）から描く。生成器の既定の入力
    （data/page-sources/bukatsu-chiiki.html）は、公開候補の隔離コピーでは finish が保存し直すまで古いままなので使わない。
    """
    with _generators(root) as (opening, reading, background):
        try:
            d = reading.load(root / READING_CONFIG)
            d["trend"] = panels
            as_of = as_of or reading.default_as_of(d)
            date.fromisoformat(as_of)
            d["as_of"] = as_of
            reading.check_all(d)
            fragment = opening.fragment_for(root / d["cfg"]["opening_config"], as_of)
            body = reading.render_reading(d)
            bg = background.render(d, as_of, reading.ordered_issues(d))
            faq = background.faq_jsonld(d, as_of)
        except SystemExit as exc:  # 生成器の照合は SystemExit で止まる。更新経路を巻き込まず止めるため変換する
            raise ValueError(f"新デザインの照合で停止しました: {exc}") from None
    d["faq_jsonld"] = faq
    return '<div class="bko-page">' + fragment + "</div>\n" + body + bg, d, as_of


def _classroom(soup: BeautifulSoup) -> None:
    """授業用の行を、サイト共通の授業節の約束（印刷ボタン・資料・問い）に合わせ、授業用の印刷画面への案内を足す。"""
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
    link = soup.new_tag("a", href=PRINT_PAGE, attrs={"class": "classroom-print-link"})
    link.string = "授業用の印刷画面を開く"
    wrap = soup.new_tag("p", attrs={"class": "fb-print"})
    wrap.append(button)
    wrap.append(" ")
    wrap.append(link)
    inner.append(wrap)
    inner.insert_before(Comment(" CLASSROOM_START "))
    inner.insert_after(Comment(" CLASSROOM_END "))


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def faq_items(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """画面に出す問いと答え（背景の「よくある質問」）。出典リンクの名前は答えではないので含めない。"""
    out = []
    for item in soup.select(f"#{FAQ_ID} dl.fb-faq > div"):
        dd = BeautifulSoup(str(item.dd), "html.parser").dd
        for node in dd.select("a, .fb-links, ul, small"):
            node.decompose()
        out.append((_norm(item.dt.get_text()), _norm(dd.get_text())))
    return out


def _faq_json_ld(soup: BeautifulSoup, payload: dict) -> str:
    """背景の設定の items から作った FAQPage を、画面の問いと答えに突き合わせてから埋め込む。"""
    shown = faq_items(soup)
    data = [(_norm(q["name"]), _norm(q["acceptedAnswer"]["text"])) for q in payload["mainEntity"]]
    if not shown or shown != data:
        raise ValueError("FAQ の構造化データが、背景の「よくある質問」の画面と一致しません。")
    return ("<!-- FAQ_JSON_LD_START -->\n<script type=\"application/ld+json\">\n"
            + json.dumps(payload, ensure_ascii=False, indent=2).replace("</", "<\\/")
            + "\n</script>\n<!-- FAQ_JSON_LD_END -->")


def _vote_section(src: BeautifulSoup) -> str:
    section = _one(src, "#vote-section", "投票")
    if section.get("data-vote-topic") != VOTE_TOPIC:
        raise ValueError(f"投票の topic_id が想定と違います: {section.get('data-vote-topic')}")
    note = section.select_one(".vote-storage-note")
    if note is None or note.get_text(strip=True) != VOTE_NOTE:
        raise ValueError("投票の保存の注記が想定と違います（本番ホストで送信される旨の文）。")
    scripts = [s for s in src.select("script:not([src])") if s.string and f"var TOPIC='{VOTE_TOPIC}'" in s.string]
    helpers = [s for s in src.select("script:not([src])") if s.string and "window.voteMsg = function" in s.string]
    if len(scripts) != 1 or len(helpers) != 1:
        raise ValueError("投票のスクリプトか、失敗の案内（voteMsg）のスクリプトが1つではありません")
    code = scripts[0].string
    if code.count(VOTE_STORAGE) != 1 or VOTE_CHOICE not in code:
        raise ValueError("投票の保存キーか choiceIdx の計算が想定と違います")
    # 本番ホストでだけ既存の保存キー。確認用の環境では別キーに保存し、本番の投票済み記録に触らない。
    code = code.replace(VOTE_STORAGE, "var STORAGE_KEY=window.SNS_REDESIGN_PRODUCTION?'sns_vote_'+TOPIC+'_my':'sns_vote_'+TOPIC+'_my_preview';")
    section = BeautifulSoup(str(section), "html.parser").section
    section["class"] = ["cap-band", "cap-vote"]
    return str(section) + "\n<script>" + helpers[0].string + "</script>\n<script>" + code + "</script>"


def _band(src: BeautifulSoup, selector: str, what: str, cls: str) -> BeautifulSoup:
    node = BeautifulSoup(str(_one(src, selector, what)), "html.parser").find(True)
    node["class"] = list(node.get("class") or []) + ["cap-band", cls]
    return node


def _articles_band(root: Path) -> str:
    """記事で詳しく読む：content/articles/bukatsu-chiiki の記事への入口（並びは原稿の order）。
    記事が無ければ何も出さない（記事側の生成は scripts/build_articles.py）。"""
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_articles import entry_articles, entry_script  # noqa: PLC0415
    articles = entry_articles("bukatsu-chiiki", root)
    if not articles:
        return ""
    items = "".join(f'<li><a href="{escape(a.url)}" data-article-entry="theme">{escape(a.title)}</a></li>' for a in articles)
    return ('<section class="panel cap-band cap-articles" id="theme-articles"><div class="panel-title"><h2>記事で詳しく読む</h2>'
            '<span>費用・問題点・賛否の理由・市ごとの違いを、1本ずつまとめました</span></div>'
            f'<ul>{items}</ul><p class="cap-articles-all"><a href="articles/index.html" data-article-entry="theme">記事の一覧へ</a></p>'
            "</section>\n" + entry_script("bukatsu-chiiki") + "\n")


def _detail(src: BeautifulSoup, d: dict) -> str:
    """詳細データ（#detail-data）：元HTMLの表（収集・分類件数・論点別・スタンス別・注意）をそのまま写す。
    表の数字が公開JSONと合わなければ止める。折りたたみは最初どれも閉じる。"""
    node = _band(src, "#detail-data", "詳細データ", "cap-detail")
    public = d["public"]
    tables = {x.summary.get_text(): x for x in node.find_all("details", recursive=False) if x.summary}
    by_issue = next((t for name, t in tables.items() if name.startswith("論点別件数")), None)
    by_stance = next((t for name, t in tables.items() if name.startswith(("立場別件数", "スタンス別件数"))), None)
    if by_issue is None or by_stance is None or not any(name == "注意" for name in tables):
        raise ValueError("詳細データ（#detail-data）に論点別・立場別の表か注意がありません")
    rows = {r.th.get_text(): int(r.td.get_text().replace(",", "")) for r in by_issue.select("tr") if r.th and r.td}
    expected = {i["label"]: int(i["count"]) for i in public["issues"] if int(i["count"])}
    if rows != expected:
        raise ValueError("詳細データの論点別件数が公開JSONと一致しません。元HTMLの更新を先に済ませてください。")
    stances: dict[str, int] = {}
    for issue in public["issues"]:
        for s in issue["stances"]:
            stances[s["label"]] = stances.get(s["label"], 0) + int(s["count"])
    rows = {r.th.get_text(): int(r.td.get_text().replace(",", "")) for r in by_stance.select("tr") if r.th and r.td}
    if rows != {k: v for k, v in stances.items() if v}:
        raise ValueError("詳細データの立場別件数が公開JSONと一致しません。元HTMLの更新を先に済ませてください。")
    for x in node.select("details[open]"):
        del x["open"]
    return str(node)


def _trend(source: str) -> tuple[str, str]:
    """「意見の推移」（表・折れ線・画像・埋め込みコード）を、枠ごと文字どおり引き継ぐ。CSS も元HTMLの区間から取る。"""
    match = re.search(r'<section class="update-dashboard"><!-- TREND_CARD_START -->.*?<!-- TREND_CARD_END --></section>',
                      source, re.S)
    if not match:
        raise ValueError("現行ページに「意見の推移」（TREND_CARD）がありません。出力は変更していません。")
    css = re.search(r"/\* TREND_CARD_START \*/.*?/\* TREND_CARD_END \*/", source, re.S)
    if not css:
        raise ValueError("現行ページに「意見の推移」の見た目（TREND_CARD の CSS）がありません。")
    for panel in (TREND_ID, *TREND_PANELS):
        if match.group().count(f'id="{panel}"') != 1:
            raise ValueError(f"「意見の推移」に {panel} が1つではありません（外部の埋め込みコードが指す id）。")
    return match.group(), css.group()


def _jp_md(iso: str, year: bool = False) -> str:
    d = date.fromisoformat(iso)
    return (f"{d.year}年" if year else "") + f"{d.month}月{d.day}日"


def _spark(rounds: list[dict], series: list[tuple[int, str]], label: str, width: int = 320, height: int = 72) -> str:
    """小さな折れ線（軸の目盛りなし）。series は（列の番号, 色）。割合だけを使い、件数は描かない。"""
    left, right, top, bottom = 6, width - 6, 8, height - 8
    values = [r["v"][j] for r in rounds for j, _ in series]
    lo, hi = min(values), max(values)
    pad = max(2.0, (hi - lo) * 0.15)
    lo, hi = max(0.0, lo - pad), min(100.0, hi + pad)
    xs = [left + (right - left) * i / (len(rounds) - 1) for i in range(len(rounds))]
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">',
           f'<line x1="{left}" x2="{right}" y1="{bottom}" y2="{bottom}" stroke="#d5e1ef"/>']
    for j, color in series:
        ys = [bottom - (bottom - top) * (r["v"][j] - lo) / (hi - lo) for r in rounds]
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
        out.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round" points="{pts}"/>')
        for x, y in ((xs[0], ys[0]), (xs[-1], ys[-1])):
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}" stroke="#fff" stroke-width="1.5"/>')
    out.append("</svg>")
    return "".join(out)


def trend_note(trend: str, panels: dict, compact: dict) -> str:
    """ひと目の注記1行：小さい標本（1回あたりの意見の件数とぶれ）・古い投稿の混入・分類AIの切替。
    数字と日付は推移の立場の注意書き（scripts/build_trend_section.py の note_lines・model_break_notes）から写す。手では書かない。
    要約の折れ線は立場なので、分類AIの切替も立場の注意書きにあるものだけを出す（部活動は論点だけ 2026-10-01 に切り替えた。
    立場は 2026-10-06 に全回を同じ基準・同じAIで判定し直している）。"""
    card = BeautifulSoup(trend, "html.parser")
    notes = card.select_one(f"#{TREND_PANELS[0]} .trend-note")
    if notes is None:
        raise ValueError("「意見の推移」の立場の注意書きが見つかりません。")
    text = re.sub(r"\s+", "", notes.get_text())
    size = re.search(r"各回の意見は(\d[\d,]*)〜(\d[\d,]*)件です。.*?±(\d+(?:\.\d+)?)ポイント", text)
    fresh = re.search(r"投稿の(\d+)%以上は、収集日の前の(\d+)日間", text)
    if size is None or fresh is None:
        raise ValueError("「意見の推移」の注意書きから、件数の幅・ぶれ・新しい投稿の割合を読めません。")
    rounds = panels["stance"]["rounds"]
    if (f"{min(r['n'] for r in rounds)}", f"{max(r['n'] for r in rounds)}") != (size.group(1).replace(",", ""), size.group(2).replace(",", "")):
        raise ValueError("「意見の推移」の注意書きの件数の幅が、回ごとの件数と一致しません。")
    out = compact["trend_note"].format(lo=size.group(1), hi=size.group(2), margin=size.group(3),
                                       days=fresh.group(2), old=100 - int(fresh.group(1)))
    for when in sorted(set(re.findall(r"(\d{4}年\d{1,2}月\d{1,2}日)の回から、分類に使うAIを切り替えました", text))):
        out += compact["trend_note_break"].format(break_date=when)
    return out


def _trend_band(trend: str, panels: dict, compact: dict) -> str:
    """意見の推移：ひと目で見る要約（見出し・立場ごとの小さな折れ線・最初と最新の回の1行・注記1行）と、
    元の推移カードを丸ごと入れた折りたたみ。推移カード（TREND_CARD）は1文字も変えずに折りたたみの中へ入れる。"""
    stance = panels["stance"]
    rounds = stance["rounds"]
    span = f"{_jp_md(rounds[0]['d'])}から{_jp_md(rounds[-1]['d'])}までの{len(rounds)}回"
    # 要約の1文は、最初と最新の回で最も多かった立場（推移の数字から作る）。前回から今回への1行・全期間の説明はカードの中で読める
    # （消費税減税の要約は「前回から今回にかけて」の1行を使うので、書き出しが同じにならないよう別の文にした）
    def top(r):
        j = max(range(len(stance["labels"])), key=lambda k: (r["v"][k], -k))
        return stance["labels"][j], f'{r["v"][j]:.1f}'
    (first_top, first_pct), (last_top, last_pct) = top(rounds[0]), top(rounds[-1])
    lead = compact["trend_lead"].format(first_date=_jp_md(rounds[0]["d"]), last_date=_jp_md(rounds[-1]["d"]),
                                        first_top=first_top, first_pct=first_pct, last_top=last_top, last_pct=last_pct)
    series = list(enumerate(stance["colors"]))
    legend = "".join(f'<li><i style="background:{escape(c)}"></i>{escape(lab)}</li>' for lab, c in zip(stance["labels"], stance["colors"]))
    aria = f"{span}の収集の、立場ごとの割合の推移"
    return ('<div class="cap-trend" id="cap-trend"><section class="cap-trend-glance" aria-labelledby="cap-trend-title">'
            f'<p class="fr-eyebrow">{escape(compact["trend_eyebrow"])}</p>'
            f'<h2 id="cap-trend-title">{escape(compact["trend_title"].format(rounds=len(rounds)))}</h2>'
            f'<div class="cap-trend-spark">{_spark(rounds, series, aria, 480, 96)}</div>'
            f'<ul class="cap-trend-legend">{legend}</ul>'
            f'<p class="cap-trend-lead">{escape(lead)}</p>'
            f'<p class="fr-fine cap-trend-note">{escape(trend_note(trend, panels, compact))}</p>'
            f'<details class="fr-fold cap-trend-more" id="cap-trend-more"><summary>{escape(compact["trend_more"].format(rounds=len(rounds)))}</summary>'
            + trend + "</details></section></div>")


def _header() -> str:
    # topic-modern.js が後から差し込む共通ヘッダーと同じ中身（消費税・辺野古と同じ）。JavaScriptなしでもトップへ戻れるよう静的に置く。
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

    山なみの見た目・数字・動きは元HTMLの生成器（refresh_planet_section.py と連動表示の橋渡し bukatsu_connected.py）が
    作ったものをそのまま使う。ここで変えるのは、新デザインで出さない部分を外すこと、調査条件を RESEARCH_CONDITIONS で囲むこと、
    URL と読み込み時の着地とフォーカスの扱い（PLANET_PATCHES）だけ。連動表示の本体（docs/bukatsu-connected.js）と
    読書面のテンプレート（template#bukatsu-reading-…）は読み込まないので、選択パネルは山なみの元の描き方（100マス・立場の内訳）になる。
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
    if "window.BukatsuConnectedMap" not in scripts[0].string:
        raise ValueError("山なみのスクリプトに連動表示の橋渡し（BukatsuConnectedMap）がありません。")
    block = section.select_one("#planet-block")
    for selector in ("#modes", "#section", "#panel", "#dotbox", "#waffle", "#fallback-nav", "#list", "#meta",
                     "#caution", "#guesses", "#quiz", "#dive"):
        if block is None or len(block.select(selector)) != 1:
            raise ValueError(f"山なみの部品 {selector} が1つではありません。")
    for selector in PLANET_DROP:
        for node in block.select(selector):
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
    code = scripts[0].string
    for old, new in PLANET_PATCHES:
        if code.count(old) != 1:
            raise ValueError("山なみのスクリプトに、書き換える箇所が想定どおりにありません: " + old.strip().splitlines()[0])
        code = code.replace(old, new)
    scripts[0].string = code
    section["class"] = list(section.get("class") or []) + ["cap-planet"]
    # 山なみのスクリプトは「探ったところ」の進捗表示（#progress）にも書き込む。新デザインでは出さないので、
    # 書き込み先だけを隠して置く（無いとスクリプトが途中で止まり、図が静的表示に戻る）。
    progress = ('<div id="progress" class="cap-planet-progress" hidden aria-hidden="true">'
                '<i id="pbar"></i><span id="pseg"></span><b id="pnum"></b></div>')
    html = str(section) + "\n" + progress + "\n" + str(contract) + "\n" + str(scripts[0])
    return html, str(contract)


def _alias_script() -> str:
    return ("<script>(()=>{const aliases=" + json.dumps(ALIASES) + ",prefixes=" + json.dumps(ISSUE_PREFIXES) + ";"
            "function resolve(){let id;try{id=decodeURIComponent(location.hash.slice(1));}catch(_){return;}"
            "if(!id)return;const cur=document.getElementById(id);if(cur&&cur.getClientRects().length)return;"
            "const pre=prefixes.find(x=>id.startsWith(x));const two=id.match(/^(.+?)--(.+)$/);"
            "if(pre&&document.getElementById('issue-'+id.slice(pre.length)))id='issue-'+id.slice(pre.length);"
            # 初期型の理由の欄（{論点ID}--{理由}）→ 新しい理由の説明（無ければ論点の欄）
            "else if(two&&document.getElementById('issue-'+two[1]))id=document.getElementById('fr-r-'+two[1]+'-'+two[2])?'fr-r-'+two[1]+'-'+two[2]:'issue-'+two[1];"
            "else if(aliases[id])id=aliases[id];"
            # 初期型の読書面の欄と、旧ページの山なみの着地は、論点の素のID（#bukatsu-chiiki-kyoin など）を URL に書いていた
            "else if(!cur&&document.getElementById('issue-'+id))id='issue-'+id;else return;"
            "location.replace('#'+id);const t=document.getElementById(id);if(t&&t.tagName==='DETAILS')t.open=true;}"
            # 推移の折れ線は閉じた折りたたみの中では幅0で描かれるので、開いたときに描き直させる（推移のスクリプトは resize で描き直す）
            "function redraw(){requestAnimationFrame(()=>dispatchEvent(new Event('resize')));}"
            # 折りたたみの中の場所（推移のタブ・作り方・詳細データ・背景の行など）へ来たら、外側の折りたたみを開いて見せる。
            # 推移のタブ（外部の埋め込みコードが指す #bukatsu-chiiki-trend-panel-issue など）なら、そのタブに切り替える
            "function show(t,scroll){let d=t.tagName==='DETAILS'?t:t.closest('details'),moved=false;"
            "while(d){if(!d.open){d.open=true;moved=true;}d=d.parentElement&&d.parentElement.closest('details');}"
            "const tab=document.querySelector('[aria-controls=\"'+t.id+'\"]');"
            "if(tab&&tab.getAttribute('aria-pressed')!=='true'){tab.click();moved=true;}"
            "if(moved)redraw();if(moved||scroll)requestAnimationFrame(()=>t.scrollIntoView({block:'start'}));}"
            "function openRow(){let h;try{h=decodeURIComponent(location.hash.slice(1));}catch(_){return;}"
            "const t=h&&document.getElementById(h);if(t)show(t,false);}"
            # 読書面の「推移のグラフを開く」：折りたたみを開き、推移を「論点の変化」に切り替えてから移る（履歴は増やさない）
            "document.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('a[data-tide-mode]');if(!a)return;"
            "const id=a.getAttribute('href').slice(1),t=document.getElementById(id);if(!t)return;e.preventDefault();"
            "history.replaceState(null,'','#'+id);show(t,true);});"
            "document.querySelectorAll('#cap-trend-more').forEach(d=>d.addEventListener('toggle',()=>{if(d.open)redraw();}));"
            "addEventListener('hashchange',()=>{resolve();openRow();});resolve();openRow();})();</script>")


def _full_link() -> str:
    return ('<p class="cap-full"><a href="' + READ_PAGE + '">全文・印刷版</a>'
            '<span>すべての論点・理由・資料を、スクリプトなしで続けて読める版です。</span></p>')


def compose(source: str, root: Path, mode: str, as_of: str | None = None) -> str:
    if MARKER in source:
        raise ValueError("新デザインのページは入力にできません。data/page-sources の元HTMLを渡してください。")
    src = BeautifulSoup(source, "html.parser")
    trend, trend_css = _trend(source)
    panels = _trend_rounds(trend)
    body, d, as_of = render_body(root, as_of, panels)
    assets = root / ASSETS
    css = "\n".join((assets / name).read_text(encoding="utf-8")
                    for name in ("opening.css", "reading.css", "production.css"))
    scripts = {name: (assets / name).read_text(encoding="utf-8") for name in ("reading.js", "planet_v2.js")}

    title = _one(src, "head > title", "title").get_text()
    fonts = "\n".join(str(n) for n in src.select('link[rel="preconnect"], link[href*="fonts.googleapis.com/css2"]'))
    adsense_meta = "\n".join(str(n) for n in src.select('meta[name="google-adsense-account"]'))
    # サイト共通の見た目と共通ヘッダー（topic-modern.js）は元HTMLの版のまま読む
    common_css = [str(_one(src, f'link[rel="stylesheet"][href^="{name}"]', name)) for name in ("site-tokens.css", "topic-modern.css")]
    common_js = str(_one(src, 'script[src^="topic-modern.js"]', "topic-modern.js"))
    planet, contract_html = _planet(source)
    contract = BeautifulSoup(contract_html, "html.parser").script
    opinions = int(d["public"]["opinion_count"])
    if f'"opinions":{opinions}' not in contract.get_text().replace(" ", ""):
        raise ValueError("PLANET_DATA の意見数が公開JSONと一致しません。元HTMLの更新を先に済ませてください。")
    trust = _block(source, "ARTICLE_TRUST")
    if f"{opinions:,}件" not in trust and f"{opinions}件" not in trust:
        raise ValueError("「このページの作り方」の意見数が公開JSONと一致しません。元HTMLの更新を先に済ませてください。")
    # 推移の「◯年◯月◯日時点」は保存した収集回の最新日（adapter が元HTMLに貼る）。新規0件の回は公開JSONの更新日より
    # 前のままになり得るので一致までは求めないが、更新日より後の日付なら入力の取り違えとして止める。
    asof = re.search(r'<span class="trend-asof">(\d{4})年(\d{1,2})月(\d{1,2})日時点</span>', trend)
    if asof is None or date(*map(int, asof.groups())).isoformat() > d["public"]["updated_on"]:
        raise ValueError("「意見の推移」の時点が読めないか、公開JSONの更新日より後です。元HTMLの更新を先に済ませてください。")

    head = ['<!doctype html>', '<html lang="ja">', '<head>', '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{title}</title>"]
    head += [_block(source, name) for name in PROTECTED_BLOCKS]
    if mode == "preview":
        head.append('<meta name="robots" content="noindex">')
    head += [x for x in (adsense_meta, fonts) if x]
    head += common_css + [
        f'<meta name="bukatsu-layout" content="{LAYOUT_VERSION}">',
        "<style>\n" + css + "\n" + trend_css + "\n</style>",
        common_js,
        '<script src="vote-config.js?v=1"></script>',
        "<script>window.SNS_REDESIGN_PRODUCTION=" +
        ("location.hostname==='sns-reaction-map.jp'" if mode == "release" else "false") +
        ";if(!window.SNS_REDESIGN_PRODUCTION)window.SNS_VOTE_CONFIG={};</script>",
        '<script src="vote-store.js?v=1"></script>']
    if mode == "release":
        head += [_block(source, name) for name in INTEGRATIONS]
    head.append("</head>")

    body_soup = BeautifulSoup(body, "html.parser")
    opening_section = body_soup.select_one("div.bko-page > section.bko")
    if opening_section is None:
        raise ValueError("冒頭の部品（section.bko）が見つかりません")
    opening_section["id"] = OPENING_ID
    for needed in (COUNT_ID, STEPS_ID):
        if body_soup.select_one(f"#{needed}") is None:
            raise ValueError(f"冒頭の部品 #{needed} が見つかりません")
    # 元HTMLの対話式の山なみを、読書面の見出しと論点タブのあいだに置く（調査条件は山なみの中、図の母数の位置）
    reading_section = body_soup.select_one(f"#{READING_ID}")
    panels_box = reading_section.select_one(".fr-panels") if reading_section else None
    if panels_box is None:
        raise ValueError("読書面の論点の欄（.fr-panels）が見つかりません")
    map_box = body_soup.new_tag("div", attrs={"class": "fr-map cap-map"})
    map_box.append(BeautifulSoup(planet, "html.parser"))
    panels_box.insert_before(map_box)
    reading_section.append(BeautifulSoup(_full_link(), "html.parser"))
    compact = d["cfg"]["compact"]
    _classroom(body_soup)
    head.insert(head.index("</head>"), _faq_json_ld(body_soup, d["faq_jsonld"]))
    body_html = str(body_soup)
    if "../../../docs/" in body_html or "試作" in BeautifulSoup(body_html, "html.parser").get_text():
        raise ValueError("試作用の相対パスか「試作」の語が残っています")
    start, end = "<!-- BUKATSU_READING_START -->", "<!-- BUKATSU_READING_END -->"
    reading_start = body_html.index(start)
    reading_end = body_html.index(end) + len(end)
    body_html = (body_html[:reading_start] + "<!-- PLANET_SECTION_START -->\n" + body_html[reading_start:reading_end]
                 + "\n<!-- PLANET_SECTION_END -->" + body_html[reading_end:])
    # X投稿は開いたときに読み込む（他の新デザイン9テーマと同じ部品）。保護対象の head を作り直さないよう、本文だけに掛ける。
    sys.path.insert(0, str(ROOT / "scripts"))
    from bukatsu_redesign.x_embeds import add_x_embeds  # noqa: PLC0415
    embedded = BeautifulSoup(add_x_embeds("<html><head></head><body>" + body_html + "</body></html>"), "html.parser")
    x_style = "".join(str(n) for n in embedded.head.select("style"))
    x_script = str(embedded.body.select("script")[-1].extract())
    body_html = embedded.body.decode_contents()
    head.insert(head.index("</head>"), x_style)
    background_at = body_html.rindex("<section", 0, body_html.index(f'id="{BACKGROUND_ID}"'))

    page = "\n".join(head) + "\n"
    page += '<body class="bukatsu-layout">\n'
    if mode == "preview":
        page += '<p class="cap-preview">公開前の確認用ページ（投票は送信されません）</p>\n'
    page += _header() + "\n<main>\n"
    page += (body_html[:background_at] + _trend_band(trend, panels, compact) + "\n"
             + _vote_section(src) + "\n" + body_html[background_at:])
    page += _articles_band(root)
    # 作り方と詳細データは、他の新デザインと同じく1つの折りたたみに入れる
    page += (f'<details class="cap-band cap-fold cap-method" id="cap-method"><summary>{escape(compact["method_fold"])}</summary>'
             '<div class="cap-trust">' + trust + "</div>\n" + _detail(src, d) + "</details>\n")
    page += str(_band(src, "#related-topics", "次に読むテーマ", "cap-related")) + "\n</main>\n"
    page += str(_one(src, "body > footer", "フッター")) + "\n"
    # 次に読むテーマのクリック計測（GA4 の related_theme_click）。元HTMLのスクリプトを文字どおり引き継ぐ
    page += str(_one(src, "script#related-theme-tracking", "次に読むテーマの計測")) + "\n"
    page += "<script>" + scripts["reading.js"] + "</script>\n"
    page += "<script>" + scripts["planet_v2.js"] + "</script>\n"
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
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.bukatsu_redesign_readable import readable_v2  # noqa: PLC0415
    full = readable_v2(page, PAGE)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, text in ((PAGE, page), (READ_PAGE, full)):
        target = output_dir / name
        temporary = target.with_suffix(".html.tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(target)
        files[name] = hashlib.sha256(text.encode()).hexdigest()
    manifest = {
        "mode": mode,
        "as_of": as_of,
        "layout": LAYOUT_VERSION,
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "files": files,
    }
    (output_dir / "build-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                                    encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source-page", type=Path, default=None, help="元HTML（既定は更新元。新デザイン公開後は data/page-sources）")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("preview", "release"), default="preview")
    parser.add_argument("--as-of", help="冒頭・読書面・背景の基準日 YYYY-MM-DD（既定は公開JSONの更新日）")
    args = parser.parse_args()
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.bukatsu_layout import source_for_refresh
    try:
        result = build(args.source_page or source_for_refresh(ROOT), args.output_dir, args.mode, as_of=args.as_of)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Built {len(result['files'])} files ({args.mode}, as_of {result['as_of']}); no deployment performed.")


if __name__ == "__main__":
    main()
