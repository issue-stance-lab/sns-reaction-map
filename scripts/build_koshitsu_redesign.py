#!/usr/bin/env python3
"""皇室典範改正ページの新デザイン（冒頭＋山なみ＋6論点の読書面＋背景）を、公開候補として組み立てる。

本文は新デザインの生成器（scripts/koshitsu_opening.py・koshitsu_reading.py・koshitsu_background.py）
が公開JSONと設定から作る。現行ページ（元HTML）からは、利用者や外部サービスとの約束になっている
部品だけを引き継ぐ。

  - title・SEOメタ（description・canonical・OGP・Twitter）・Article JSON-LD（そのまま）
  - GA4・AdSense のタグ（release のときだけ。preview には載せない）
  - google-adsense-account・Webフォント
  - 投票（topic_id・論点6つと立場4つの順番・choice_idx の計算・保存キーを変えない）
  - 調査条件（#caution）と PLANET_DATA（既存の公開検査が読む公開データの契約）
  - 対話式の山なみ（PLANET_SECTION の #planet-block・PLANET_DATA・山なみのスクリプト。2026-10-11 に静的SVGから戻した）。
    立場モード・100マス・論点の一覧・見かたをそのまま写し、新デザインで使わない部分（予想2問・一次資料クイズ・
    資料にしかない話・編集部の横断整理・JSなし用の論点別本文）だけを外す。山を押すと読書面へ移る（planet.js）
  - 次に読むテーマ・フッター（運営者情報・訂正窓口・プライバシーポリシーへのリンク）
  - 旧アンカー（#planet-block など）は、新しい置き場所へ読み替える

FAQ の JSON-LD は、新デザインで画面に出す「よくある質問」から作り直す（画面と構造化データを一致させる）。

docs/ へは直接書き出さない（公開切替は scripts/koshitsu_layout.py の finish が行う）。

    python3 scripts/build_koshitsu_redesign.py --mode release --output-dir quality/prototypes/koshitsu-tenpakai-release
    python3 scripts/build_koshitsu_redesign.py --mode preview --output-dir /tmp/koshitsu-preview
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
PAGE = "koshitsu-tenpakai-reaction-map.html"
ASSETS = Path("scripts/koshitsu_redesign")
MARKER = 'name="koshitsu-layout"'
LAYOUT_VERSION = "redesign-v1"
VOTE_TOPIC = "koshitsu-tenpakai-issue-stance-v2"
PROTECTED_BLOCKS = ("SEO_META", "ARTICLE_JSON_LD")
INTEGRATIONS = ("ADSENSE_TAG", "GA_TAG")
# 旧デザインの節 → 新デザインの置き場所。外部から旧アンカー付きで来た人を迷わせない。
ALIASES = {
    "koshitsu-quick-guide": "koshitsu-opening",
    "kq-result": "koshitsu-opening",
    "stance-glance": "koshitsu-opening",
    "stance-map-section": "koshitsu-reading",
    "fallback": "koshitsu-reading",
    "issue-cards": "koshitsu-reading",
    "koshitsu-audit": "koshitsu-reading",
    "koshitsu-tenpakai-tide-widget": "koshitsu-reading",
    "quiz": "koshitsu-reading",
    "ocean": "koshitsu-reading",
    "bukatsu-background": "koshitsu-background",
    "bukatsu-check": "koshitsu-background",
    "editorial": "bg-method",
    "detail-data": "bg-table",
    "classroom-title": "bg-classroom",
    "article-trust-title": "bg-method",
}
# 山なみのスクリプトが要素を探すので残すが、新ページでは隠れている受け皿。旧アンカーで来たら上の読み替え先へ送る。
HIDDEN_RECEIVERS = ("fallback", "quiz")
# 山なみから外す部分（新デザインの読書面・冒頭が同じ役目を持つか、採用しないと決めたもの。生成AIと同じ）
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
    import koshitsu_background as background  # noqa: PLC0415
    import koshitsu_opening as opening  # noqa: PLC0415
    import koshitsu_reading as reading  # noqa: PLC0415

    saved = (opening.ROOT, background.ROOT, reading.ROOT, reading.IMG_DIR)
    opening.ROOT = background.ROOT = reading.ROOT = root
    reading.IMG_DIR = root / "docs" / "images" / "topics" / "koshitsu-tenpakai"
    try:
        yield opening, reading, background
    finally:
        opening.ROOT, background.ROOT, reading.ROOT, reading.IMG_DIR = saved


def render_body(root: Path, as_of: str) -> tuple[str, dict]:
    """冒頭・読書面・背景のHTMLと、組み立てに使うデータを返す。数が合わなければ ValueError。"""
    with _generators(root) as (opening, reading, background):
        try:
            d = reading.load(root / "configs" / "koshitsu-tenpakai-reading.json")
            reading.check_all(d)
            date.fromisoformat(as_of)
            fragment = opening.render_fragment(d["ocfg"], d["public"], as_of)
            body = reading.render_reading(d)
            bg = background.render(d["bg"], as_of, reading.ordered_issues(d), d["ocfg"]["issue_short_labels"])
        except SystemExit as exc:  # 生成器の照合は SystemExit で止まる。更新経路を巻き込まず止めるため変換する
            raise ValueError(f"新デザインの照合で停止しました: {exc}") from None
    return fragment + body + bg, d


def _classroom(soup: BeautifulSoup) -> None:
    """授業用の行を、サイト共通の授業節の約束（印刷ボタン・資料・問い・GA4の計測）に合わせる。"""
    body = soup.select_one("#bg-classroom .kb-body")
    if body is None:
        raise ValueError("背景の「授業や話し合いで使う」が見つかりません")
    inner = soup.new_tag("div", attrs={"class": "classroom-section"})
    for child in list(body.contents):
        inner.append(child.extract())
    body.append(inner)
    labels = inner.select("p.kb-src-label")
    for label, cls, follower in ((labels[0], "classroom-sources", "ul"), (labels[1], "classroom-questions", "ol")):
        box = soup.new_tag("div", attrs={"class": cls})
        nxt = label.find_next_sibling(follower)
        label.insert_before(box)
        box.append(label.extract())
        box.append(nxt.extract())
    button = soup.new_tag("button", type="button", attrs={"class": "classroom-print-btn"})
    button.string = "この節を印刷する"
    wrap = soup.new_tag("p", attrs={"class": "kb-print"})
    wrap.append(button)
    inner.append(wrap)
    inner.insert_before(Comment(" CLASSROOM_START "))
    inner.insert_after(Comment(" CLASSROOM_END "))


def _faq_json_ld(soup: BeautifulSoup) -> str:
    items = soup.select("#bg-faq dl.kb-faq > div")
    if not items:
        raise ValueError("背景の「よくある質問」が見つかりません")
    payload = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": i.dt.get_text(strip=True),
             "acceptedAnswer": {"@type": "Answer", "text": i.dd.get_text(strip=True)}}
            for i in items
        ],
    }
    return ("<!-- FAQ_JSON_LD_START -->\n<script type=\"application/ld+json\">\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + "\n</script>\n<!-- FAQ_JSON_LD_END -->")


def _vote_section(src: BeautifulSoup, source: str) -> str:
    section = _one(src, "#vote-section", "投票")
    if section.get("data-vote-topic") != VOTE_TOPIC:
        raise ValueError(f"投票の topic_id が想定と違います: {section.get('data-vote-topic')}")
    script = next((s for s in src.select("script:not([src])")
                   if s.string and f"var TOPIC='{VOTE_TOPIC}'" in s.string), None)
    if script is None:
        raise ValueError("投票のスクリプトが見つかりません")
    code = script.string
    old_key = "var STORAGE_KEY='sns_vote_'+TOPIC+'_my';"
    if code.count(old_key) != 1 or "choiceIdx:issueIdx*STANCES.length+stanceIdx" not in code:
        raise ValueError("投票の保存キーか choice_idx の計算が想定と違います")
    # 本番ホストでだけ既存の保存キー。確認用の環境では別キーに保存し、本番の投票済み記録に触らない。
    code = code.replace(old_key, "var STORAGE_KEY=(window.SNS_REDESIGN_PRODUCTION?'sns_vote_':'sns_vote_preview_')+TOPIC+'_my';")
    section = BeautifulSoup(str(section), "html.parser").section
    section["class"] = ["ko-band", "ko-vote"]
    return str(section) + "\n<script>" + code + "</script>"


def _related(src: BeautifulSoup) -> str:
    section = BeautifulSoup(str(_one(src, "#related-topics", "次に読むテーマ")), "html.parser").section
    section["class"] = ["ko-band", "ko-related"]
    return str(section)


def _header() -> str:
    # topic-modern.js が後から差し込む共通ヘッダーと同じ中身。JavaScriptなしでもトップへ戻れるよう静的に置く。
    return ('<header class="modern-site-header"><div class="modern-header-inner">'
            '<a class="modern-logo" href="index.html" aria-label="SNS反応まっぷ トップ">'
            '<span class="modern-logo-mark" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i></span>'
            '<span class="modern-logo-text">SNS反応まっぷ</span></a>'
            '<nav class="modern-nav" aria-label="メインナビゲーション">'
            '<a href="index.html#topics">テーマ一覧</a><a href="index.html#featured-questions">注目の問い</a>'
            '<a href="about.html">データについて</a><a href="usage.html">使い方</a>'
            '<a href="usage.html#faq">よくある質問</a></nav>'
            '<a class="modern-header-button" href="index.html#topics">テーマを見る</a></div></header>')


def _phase_script(ocfg: dict) -> str:
    """施行日までの日数は、生成した日ではなく読む日で数え直す（更新の間に日付が古くならないように）。"""
    law, status = ocfg["law"], ocfg["status"]
    data = {"enforcement": law["enforcement_on"], "before": status["before_badge"],
            "after_badge": status["after_unconfirmed_badge"],
            "after": status["after_unconfirmed"].format(enforcement=_ja(law["enforcement_on"])),
            "confirmed": bool(law.get("enforcement_confirmed_on"))}
    return ("<script>(()=>{const c=" + json.dumps(data, ensure_ascii=False) + ";"
            "if(c.confirmed)return;const s=document.querySelector('#koshitsu-opening');if(!s)return;"
            "const b=s.querySelector('.ko-badge'),p=s.querySelector('.ko-status p');if(!b)return;"
            "const now=new Date(new Date().toLocaleString('en-US',{timeZone:'Asia/Tokyo'}));"
            "const t=Date.UTC(now.getFullYear(),now.getMonth(),now.getDate());"
            "const [y,m,d]=c.enforcement.split('-').map(Number);const days=Math.round((Date.UTC(y,m-1,d)-t)/864e5);"
            "if(days>0){b.textContent=c.before.replace('{days}',days);}"
            "else{b.textContent=c.after_badge;b.className='ko-badge ko-badge-after_unconfirmed';if(p)p.textContent=c.after;}"
            "})();</script>")


def _ja(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.year}年{d.month}月{d.day}日"


def _planet(source: str) -> tuple[str, str]:
    """元HTMLの山なみ（PLANET_SECTION）を写す。返り値は（#planet-block を含む節＋PLANET_DATA＋山なみのスクリプト, PLANET_DATA）。

    生成AIと著作権（build_ai_copyright_redesign.py の _planet）と同じ写し方。山なみの見た目・数字・動きは
    元HTMLの生成器（refresh_planet_section.py 系）が作ったものをそのまま使う。ここで変えるのは、
    新デザインで出さない部分を外すことと、調査条件を RESEARCH_CONDITIONS で囲むことだけ。
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
    # 予想2問と一次資料クイズは新デザインで出さない（冒頭・論点ごとの読書面が同じ役目）。
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
    wrap = soup.new_tag("div", attrs={"class": "ko-research", "id": "research-conditions"})
    caution.wrap(wrap)
    wrap.insert_before(Comment(" RESEARCH_CONDITIONS_START "))
    wrap.insert_after(Comment(" RESEARCH_CONDITIONS_END "))
    section["class"] = list(section.get("class") or []) + ["ko-planet"]
    # 山なみのスクリプトは「探ったところ」の進捗表示（#progress）にも書き込む。新デザインでは出さないので、
    # 書き込み先だけを隠して置く（無いとスクリプトが途中で止まり、図が静的表示に戻る）。
    progress = '<div id="progress" class="ko-planet-progress" hidden aria-hidden="true"><i id="pbar"></i><b id="pnum"></b></div>'
    html = str(section) + "\n" + progress + "\n" + str(contract) + "\n" + str(scripts[0])
    return html, str(contract)


def _alias_script() -> str:
    return ("<script>(()=>{const aliases=" + json.dumps(ALIASES) + ";"
            "function resolve(){let id=decodeURIComponent(location.hash.slice(1));"
            "if(!id)return;const cur=document.getElementById(id);if(cur&&cur.getClientRects().length)return;"
            "if(id.startsWith('fb-'))id='issue-'+id.slice(3);else if(aliases[id])id=aliases[id];else return;"
            "location.replace('#'+id);const t=document.getElementById(id);if(t&&t.tagName==='DETAILS')t.open=true;}"
            # 折りたたみの中の場所（背景の行の中・読書面の折りたたみの中）へ来たら、外側の折りたたみも開いて見せる（生成AIと同じ）
            "function openRow(){const t=document.getElementById(decodeURIComponent(location.hash.slice(1)));"
            "if(!t)return;let d=t.tagName==='DETAILS'?t:t.closest('details'),moved=false;"
            "while(d){if(!d.open){d.open=true;moved=true;}d=d.parentElement&&d.parentElement.closest('details');}"
            "if(moved)requestAnimationFrame(()=>t.scrollIntoView({block:'start'}));}"
            "addEventListener('hashchange',()=>{resolve();openRow();});resolve();openRow();})();</script>")


def compose(source: str, root: Path, mode: str, as_of: str) -> str:
    if MARKER in source:
        raise ValueError("新デザインのページは入力にできません。data/page-sources の元HTMLを渡してください。")
    src = BeautifulSoup(source, "html.parser")
    body, d = render_body(root, as_of)
    ocfg = d["ocfg"]
    assets = root / ASSETS
    css = "\n".join((assets / name).read_text(encoding="utf-8")
                    for name in ("opening.css", "reading.css", "production.css"))
    reading_js = (assets / "reading.js").read_text(encoding="utf-8")
    planet_js = (assets / "planet.js").read_text(encoding="utf-8")

    title = _one(src, "head > title", "title").get_text()
    fonts = "\n".join(str(n) for n in src.select('link[rel="preconnect"], link[href*="fonts.googleapis.com/css2"]'))
    adsense_meta = str(_one(src, 'meta[name="google-adsense-account"]', "AdSenseアカウントのmeta"))
    planet, contract_html = _planet(source)
    contract = BeautifulSoup(contract_html, "html.parser").script
    if f'"opinions":{int(d["public"]["opinion_count"])}' not in contract.get_text().replace(" ", ""):
        raise ValueError("PLANET_DATA の意見数が公開JSONと一致しません。元HTMLの更新を先に済ませてください。")

    head = ['<!doctype html>', '<html lang="ja">', '<head>', '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{title}</title>"]
    head += [_block(source, name) for name in PROTECTED_BLOCKS]
    if mode == "preview":
        head.append('<meta name="robots" content="noindex">')
    head += [adsense_meta, fonts,
             '<link rel="stylesheet" href="site-tokens.css?v=3">',
             '<link rel="stylesheet" href="topic-modern.css?v=32">',
             f'<meta name="koshitsu-layout" content="{LAYOUT_VERSION}">',
             "<style>\n" + css + "\n</style>",
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
    # 静的SVGの山なみと論点名リストの代わりに、元HTMLの対話式の山なみを置く（調査条件は山なみの中、図の母数の位置）
    map_box = body_soup.select_one("#koshitsu-reading .kr-map")
    for selector in (".kr-map-shell", "nav.kr-chips"):
        node = map_box.select_one(selector)
        if node is None:
            raise ValueError(f"読書面の全体像に {selector} がありません")
        node.decompose()
    map_box.select("p.kr-fine")[0].insert_after(BeautifulSoup(planet, "html.parser"))
    # 背景の「公開日・最終更新日」を機械可読な日付にする（検索エンジン向け。表示は変えない）
    for row in body_soup.select("#bg-method .kb-facts > div"):
        key = row.dt.get_text()
        iso = {"公開日": str(d["bg"]["theme"]["published_at"]), "最終更新日": d["public"]["updated_on"]}.get(key)
        if iso:
            text = row.dd.get_text()
            row.dd.clear()
            time = body_soup.new_tag("time", datetime=iso)
            time.string = text
            row.dd.append(time)
    _classroom(body_soup)
    # JavaScriptなしでも古くならないよう、施行前の札は日数ではなく施行日を書く（日数はJSが読む日で数える）
    badge = body_soup.select_one("#koshitsu-opening .ko-badge-before")
    if badge is not None:
        badge.string = "施行は" + _ja(ocfg["law"]["enforcement_on"])[5:]
    faq = _faq_json_ld(body_soup)
    head.insert(head.index("</head>"), faq)
    body_html = str(body_soup).replace("../../../docs/images/", "images/")
    if "../../../docs/" in body_html:
        raise ValueError("試作用の相対パスが残っています")
    reading_start = body_html.index("<!-- KOSHITSU_READING_START -->")
    reading_end = body_html.index("<!-- KOSHITSU_READING_END -->") + len("<!-- KOSHITSU_READING_END -->")
    body_html = (body_html[:reading_start] + "<!-- PLANET_SECTION_START -->\n" + body_html[reading_start:reading_end]
                 + "\n<!-- PLANET_SECTION_END -->" + body_html[reading_end:])
    # X投稿は開いたときに読み込む（部活動と同じ部品）。保護対象の head を作り直さないよう、本文だけに掛ける。
    sys.path.insert(0, str(ROOT / "scripts"))
    from bukatsu_redesign.x_embeds import add_x_embeds  # noqa: PLC0415
    embedded = BeautifulSoup(add_x_embeds("<html><head></head><body>" + body_html + "</body></html>"), "html.parser")
    x_style = "".join(str(n) for n in embedded.head.select("style"))
    x_script = str(embedded.body.select("script")[-1].extract())
    body_html = embedded.body.decode_contents()
    head.insert(head.index("</head>"), x_style)
    background_at = body_html.rindex("<section", 0, body_html.index('id="koshitsu-background"'))

    page = "\n".join(head) + "\n"
    page += '<body class="koshitsu-layout">\n'
    if mode == "preview":
        page += '<p class="ko-preview">公開前の確認用ページ（投票は送信されません）</p>\n'
    page += _header() + "\n<main>\n"
    page += body_html[:background_at] + _vote_section(src, source) + "\n" + body_html[background_at:]
    page += _related(src) + "\n</main>\n"
    page += str(_one(src, "body > footer", "フッター")) + "\n"
    page += "<script>" + reading_js + "</script>\n"
    page += "<script>" + planet_js + "</script>\n"
    page += x_script + "\n" + _phase_script(ocfg) + "\n" + _alias_script() + "\n"
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
    # 基準日は既定で公開JSONの更新日。同じデータなら同じページになる（施行までの日数は読む日にJSで数え直す）
    as_of = as_of or json.loads((root / "docs/data/themes/koshitsu-tenpakai.json").read_text(encoding="utf-8"))["updated_on"]
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
    parser.add_argument("--as-of", help="冒頭の基準日 YYYY-MM-DD（既定は公開JSONの更新日）")
    args = parser.parse_args()
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.koshitsu_layout import source_for_refresh
    try:
        result = build(args.source_page or source_for_refresh(ROOT), args.output_dir, args.mode, as_of=args.as_of)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Built {len(result['files'])} file ({args.mode}, as_of {result['as_of']}); no deployment performed.")


if __name__ == "__main__":
    main()
