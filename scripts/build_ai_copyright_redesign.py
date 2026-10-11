#!/usr/bin/env python3
"""生成AIと著作権ページの新デザイン（冒頭＋山なみ＋7論点の読書面＋背景）を、公開候補として組み立てる。

副首都（scripts/build_fukushuto_redesign.py）・皇室典範改正と同じ型。
本文は新デザインの生成器（scripts/ai_copyright_opening.py・ai_copyright_reading.py・ai_copyright_background.py）
が公開JSON・再読データ・設定から作る。現行ページ（元HTML）からは、利用者や外部サービスとの約束になっている
部品だけを文字どおり引き継ぐ。

  - title・SEOメタ（description・canonical・OGP・Twitter）・Article JSON-LD（そのまま）
  - GA4・AdSense のタグ（release のときだけ。preview には載せない）
  - google-adsense-account（元HTMLにあれば）・Webフォント
  - 投票（topic_id・論点7つと立場3つの順番・V2I・choice_idx の計算・保存キーを変えない）
  - 調査条件（#caution）と PLANET_DATA（既存の公開検査が読む公開データの契約）
  - 対話式の山なみ（PLANET_SECTION の #planet-block・PLANET_DATA・山なみのスクリプト。2026-10-11 に静的SVGから戻した）。
    立場モード・100マス・論点の一覧・見かたをそのまま写し、新デザインで使わない部分（予想2問・一次資料クイズ・
    資料にしかない話・編集部の横断整理・JSなし用の論点別本文）だけを外す。山を押すと読書面へ移る（planet.js）
  - SNS上の意見の推移（TREND_CARD。画像4枚・説明・埋め込みコード。外部から #ai-copyright-trend-panel-* で参照される）
  - このページの作り方（ARTICLE_TRUST）・詳細データ・次に読むテーマ・フッター
  - 旧アンカー（#planet-block・#aic-search-entry・#fb-{論点ID} など）は、新しい置き場所へ読み替える

FAQ の JSON-LD は、新デザインで画面に出す背景の「よくある質問」から作り直す（画面と構造化データを一致させる）。
旧ページの検索入口（scripts/ai_copyright_search_entry.py・docs/ai-copyright-connected-page.js）の問いは使わない。
アリーナデータ（docs/ai-copyright-arena-data.js）は新デザインでは読まない（更新経路では引き続き生成される）。

docs/ へは直接書き出さない（公開切替は scripts/ai_copyright_layout.py の finish が行う）。

    python3 scripts/build_ai_copyright_redesign.py --mode release --output-dir quality/prototypes/ai-copyright-release
    python3 scripts/build_ai_copyright_redesign.py --mode preview --output-dir /tmp/ai-copyright-preview
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parents[1]
PAGE = "ai-copyright-reaction-map.html"
PUBLIC = "docs/data/themes/ai-copyright.json"
ASSETS = Path("scripts/ai_copyright_redesign")
MARKER = 'name="ai-copyright-layout"'
LAYOUT_VERSION = "redesign-v1"
VOTE_TOPIC = "ai-copyright-issue-stance-v1"
VOTE_STORAGE_KEY = "sns_vote_ai_copyright_2step"
PROTECTED_BLOCKS = ("SEO_META", "ARTICLE_JSON_LD")
INTEGRATIONS = ("ADSENSE_TAG", "GA_TAG")
OPENING_ID = "ai-copyright-opening"
# 旧デザインの節 → 新デザインの置き場所。外部から旧アンカー付きで来た人を迷わせない。
# 論点ごとの旧ID（fb-・extras-・ai-copyright-reading-）は issue-{論点ID} へ読み替える（スクリプト側）。
# #issue-{論点ID} は旧ページでも新ページでも「その論点の欄」（旧：論点ごとのX投稿、新：投稿を含む読書面）なので、そのまま残る。
ALIASES = {
    "top": OPENING_ID,
    "progress": OPENING_ID,
    "aic-search-entry": OPENING_ID,
    "aic-search-heading": OPENING_ID,
    "aic-search-panel": OPENING_ID,
    "aic-search-answer": OPENING_ID,
    "stance-glance": "ai-copyright-reading",
    "stance-glance-title": "ai-copyright-reading",
    "fallback": "ai-copyright-reading",
    "fallback-nav": "ai-copyright-reading",
    "issue-cards": "ai-copyright-reading",
    "editorial": "ai-copyright-reading",
    "quiz": "ai-copyright-reading",
    "ocean": "ai-copyright-reading",
    "ai-copyright-audit": "ai-copyright-reading",
    "bukatsu-background": "ai-copyright-background",
    "bg-title": "ai-copyright-background",
    "bukatsu-check": "bg-rules",
    "ck-title": "bg-rules",
    "copyright-entry": "bg-kangaekata",
    "copyright-entry-title": "bg-kangaekata",
    "classroom-title": "bg-classroom",
}
ISSUE_PREFIXES = ("fb-", "extras-", "ai-copyright-reading-")
# 山なみのスクリプトが要素を探すので残すが、新ページでは隠れている受け皿。旧アンカーで来たら上の読み替え先へ送る。
HIDDEN_RECEIVERS = ("fallback", "fallback-nav", "quiz", "progress")
# 山なみから外す部分（新デザインの読書面・冒頭が同じ役目を持つか、採用しないと決めたもの。content-map 11・14・15・17）
PLANET_DROP = ("section.landing-panel", "#ocean", "#editorial")


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
    import ai_copyright_background as background  # noqa: PLC0415
    import ai_copyright_opening as opening  # noqa: PLC0415
    import ai_copyright_reading as reading  # noqa: PLC0415

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
            d = reading.load(root / "configs" / "ai-copyright-reading.json")
            reading.check_all(d)
            as_of = as_of or reading.default_as_of(d)
            date.fromisoformat(as_of)
            fragment = opening.render_fragment(d["data"], as_of)
            body = reading.render_reading(d)
            bg = background.render(d, as_of, reading.ordered_issues(d))
        except SystemExit as exc:  # 生成器の照合は SystemExit で止まる。更新経路を巻き込まず止めるため変換する
            raise ValueError(f"新デザインの照合で停止しました: {exc}") from None
    return fragment + body + bg, d, as_of


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
    return [(i.dt.get_text(strip=True), i.dd.get_text(strip=True)) for i in soup.select("#bg-faq dl.fb-faq > div")]


def _faq_json_ld(soup: BeautifulSoup) -> str:
    items = faq_items(soup)
    if not items:
        raise ValueError("背景の「よくある質問」が見つかりません")
    payload = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items
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
    if code.count(old_key) != 1 or "choiceIdx:selIssue*STANCES.length+stanceIdx" not in code:
        raise ValueError("投票の保存キーか choice_idx の計算が想定と違います")
    # 本番ホストでだけ既存の保存キー。確認用の環境では別キーに保存し、本番の投票済み記録に触らない。
    preview_key = VOTE_STORAGE_KEY.replace("sns_vote_", "sns_vote_preview_", 1)
    code = code.replace(old_key, f"var STORAGE_KEY=window.SNS_REDESIGN_PRODUCTION?'{VOTE_STORAGE_KEY}':'{preview_key}';")
    section = BeautifulSoup(str(section), "html.parser").section
    section["class"] = ["acp-band", "acp-vote"]
    return str(section) + "\n<script>" + code + "</script>"


def _band(src: BeautifulSoup, selector: str, what: str, cls: str) -> str:
    node = BeautifulSoup(str(_one(src, selector, what)), "html.parser").find(True)
    node["class"] = list(node.get("class") or []) + ["acp-band", cls]
    return str(node)


def _trend(source: str) -> tuple[str, str]:
    """「SNS上の意見の推移」（画像4枚と説明）を、枠ごと文字どおり引き継ぐ。CSS も元HTMLの区間から取る。"""
    match = re.search(r'<section class="update-dashboard"><!-- TREND_CARD_START -->.*?<!-- TREND_CARD_END --></section>',
                      source, re.S)
    if not match:
        raise ValueError("現行ページに「意見の推移」（TREND_CARD）がありません。出力は変更していません。")
    css = re.search(r"/\* TREND_CARD_START \*/.*?/\* TREND_CARD_END \*/", source, re.S)
    if not css:
        raise ValueError("現行ページに「意見の推移」の見た目（TREND_CARD の CSS）がありません。")
    images = re.findall(r'<img src="(images/trend/ai-copyright-[a-z-]+\.png)"', match.group())
    if len(images) != 4:
        raise ValueError(f"「意見の推移」の画像が {len(images)} 枚です。4枚のはずです。")
    return match.group(), css.group()


def _header(src: BeautifulSoup) -> str:
    # 共通ヘッダー（ロゴ画像 images/brand/mark.svg・ナビ）は現行ページの静的な部品を文字どおり引き継ぐ。
    # JavaScriptなしでもトップへ戻れる。
    return str(_one(src, "body > header.modern-site-header", "共通ヘッダー"))


def _planet(source: str) -> tuple[str, str]:
    """元HTMLの山なみ（PLANET_SECTION）を写す。返り値は（#planet-block を含む節＋PLANET_DATA＋山なみのスクリプト, PLANET_DATA）。

    山なみの見た目・数字・動きは元HTMLの生成器（refresh_planet_section.py 系）が作ったものをそのまま使う。
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
    # 予想2問と一次資料クイズは新デザインで出さない（冒頭の2問・論点ごとの照合が同じ役目）。
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
    wrap = soup.new_tag("div", attrs={"class": "acp-research", "id": "research-conditions"})
    caution.wrap(wrap)
    wrap.insert_before(Comment(" RESEARCH_CONDITIONS_START "))
    wrap.insert_after(Comment(" RESEARCH_CONDITIONS_END "))
    section["class"] = list(section.get("class") or []) + ["acp-planet"]
    # 山なみのスクリプトは「探ったところ」の進捗表示（#progress）にも書き込む。新デザインでは出さない（content-map 27）ので、
    # 書き込み先だけを隠して置く（無いとスクリプトが途中で止まり、図が静的表示に戻る）。
    progress = '<div id="progress" class="acp-planet-progress" hidden aria-hidden="true"><i id="pbar"></i><b id="pnum"></b></div>'
    html = str(section) + "\n" + progress + "\n" + str(contract) + "\n" + str(scripts[0])
    return html, str(contract)


def _alias_script() -> str:
    return ("<script>(()=>{const aliases=" + json.dumps(ALIASES) + ",prefixes=" + json.dumps(ISSUE_PREFIXES) + ";"
            "function resolve(){let id=decodeURIComponent(location.hash.slice(1));"
            "if(!id)return;const cur=document.getElementById(id);if(cur&&cur.getClientRects().length)return;"
            "const pre=prefixes.find(x=>id.startsWith(x));"
            "if(pre&&document.getElementById('issue-'+id.slice(pre.length)))id='issue-'+id.slice(pre.length);"
            "else if(aliases[id])id=aliases[id];else return;"
            "location.replace('#'+id);const t=document.getElementById(id);if(t&&t.tagName==='DETAILS')t.open=true;}"
            "function openRow(){const t=document.getElementById(decodeURIComponent(location.hash.slice(1)));"
            "if(t&&t.tagName==='DETAILS')t.open=true;}"
            "addEventListener('hashchange',()=>{resolve();openRow();});resolve();openRow();})();</script>")


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
    if f"{opinions:,}件" not in trust:
        raise ValueError("「このページの作り方」の意見数が公開JSONと一致しません。元HTMLの更新を先に済ませてください。")
    trend, trend_css = _trend(source)
    # 推移の「◯月◯日時点」は保存した収集回の最新日（trend_support が元HTMLに貼る）。新規0件の回は公開JSONの更新日より
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
    head += ['<link rel="stylesheet" href="site-tokens.css?v=3">',
             '<link rel="stylesheet" href="topic-modern.css?v=32">',
             f'<meta name="ai-copyright-layout" content="{LAYOUT_VERSION}">',
             "<style>\n" + css + "\n" + trend_css + "\n</style>",
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
    opening_section = body_soup.select_one("section.aic-opening")
    if opening_section is None or opening_section.get("id") != "top":
        raise ValueError("冒頭の部品（section.aic-opening#top）が見つかりません")
    opening_section["id"] = OPENING_ID
    opening_section.select_one(".count-panel")["id"] = "aic-op-count"
    # 静的SVGの山なみと論点名リストの代わりに、元HTMLの対話式の山なみを置く（調査条件は山なみの中、図の母数の位置）
    map_box = body_soup.select_one("#ai-copyright-reading .fr-map")
    for selector in (".fr-map-shell", "nav.fr-chips"):
        node = map_box.select_one(selector)
        if node is None:
            raise ValueError(f"読書面の全体像に {selector} がありません")
        node.decompose()
    map_box.select("p.fr-fine")[0].insert_after(BeautifulSoup(planet, "html.parser"))
    _classroom(body_soup)
    faq = _faq_json_ld(body_soup)
    head.insert(head.index("</head>"), faq)
    body_html = str(body_soup).replace("../../../docs/images/", "images/")
    if "../../../docs/" in body_html:
        raise ValueError("試作用の相対パスが残っています")
    start, end = "<!-- AI_COPYRIGHT_READING_START -->", "<!-- AI_COPYRIGHT_READING_END -->"
    reading_start = body_html.index(start)
    reading_end = body_html.index(end) + len(end)
    body_html = (body_html[:reading_start] + "<!-- PLANET_SECTION_START -->\n" + body_html[reading_start:reading_end]
                 + "\n<!-- PLANET_SECTION_END -->" + body_html[reading_end:])
    # X投稿は開いたときに読み込む（部活動・皇室・副首都と同じ部品）。保護対象の head を作り直さないよう、本文だけに掛ける。
    sys.path.insert(0, str(ROOT / "scripts"))
    from bukatsu_redesign.x_embeds import add_x_embeds  # noqa: PLC0415
    embedded = BeautifulSoup(add_x_embeds("<html><head></head><body>" + body_html + "</body></html>"), "html.parser")
    x_style = "".join(str(n) for n in embedded.head.select("style"))
    x_script = str(embedded.body.select("script")[-1].extract())
    body_html = embedded.body.decode_contents()
    head.insert(head.index("</head>"), x_style)
    background_at = body_html.rindex("<section", 0, body_html.index('id="ai-copyright-background"'))

    page = "\n".join(head) + "\n"
    page += '<body class="ai-copyright-layout">\n'
    if mode == "preview":
        page += '<p class="acp-preview">公開前の確認用ページ（投票は送信されません）</p>\n'
    page += _header(src) + "\n<main>\n"
    page += (body_html[:background_at] + '<div class="acp-trend">' + trend + "</div>\n"
             + _vote_section(src) + "\n" + body_html[background_at:])
    page += '<div class="acp-band acp-trust">' + trust + "</div>\n"
    page += _band(src, "#detail-data", "詳細データ", "acp-detail") + "\n"
    page += _band(src, "#related-topics", "次に読むテーマ", "acp-related") + "\n</main>\n"
    page += str(_one(src, "body > footer", "フッター")) + "\n"
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
    parser.add_argument("--as-of", help="冒頭・背景の基準日 YYYY-MM-DD（既定は公開JSONの更新日）")
    args = parser.parse_args()
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.ai_copyright_layout import source_for_refresh
    try:
        result = build(args.source_page or source_for_refresh(ROOT), args.output_dir, args.mode, as_of=args.as_of)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Built {len(result['files'])} file ({args.mode}, as_of {result['as_of']}); no deployment performed.")


if __name__ == "__main__":
    main()
