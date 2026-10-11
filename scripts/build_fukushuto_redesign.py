#!/usr/bin/env python3
"""副首都ページの新デザイン（冒頭＋山なみ＋7論点の読書面＋背景）を、公開候補として組み立てる。

皇室典範改正（scripts/build_koshitsu_redesign.py）と同じ型。
本文は新デザインの生成器（scripts/fukushuto_opening.py・fukushuto_reading.py・fukushuto_background.py）
が公開JSONと設定から作る。現行ページ（元HTML）からは、利用者や外部サービスとの約束になっている
部品だけを文字どおり引き継ぐ。

  - title・SEOメタ（description・canonical・OGP・Twitter）・Article JSON-LD（そのまま）
  - GA4・AdSense のタグ（release のときだけ。preview には載せない）
  - google-adsense-account・Webフォント
  - 投票（topic_id・論点7つと立場3つの順番・V2I・choice_idx の計算・保存キーを変えない）
  - 調査条件（#caution）と PLANET_DATA（既存の公開検査が読む公開データの契約）
  - このページの作り方（ARTICLE_TRUST）・詳細データ・次に読むテーマ・フッター
  - 旧アンカー（#planet-block など）は、新しい置き場所へ読み替える

FAQ の JSON-LD は、新デザインで画面に出す背景の「よくある質問」から作り直す（画面と構造化データを一致させる）。
旧ページの FAQ（scripts/fukushuto_search_entry.py の6問）は使わない。

docs/ へは直接書き出さない（公開切替は scripts/fukushuto_layout.py の finish が行う）。

    python3 scripts/build_fukushuto_redesign.py --mode release --output-dir quality/prototypes/fukushuto-release
    python3 scripts/build_fukushuto_redesign.py --mode preview --output-dir /tmp/fukushuto-preview
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
PAGE = "fukushuto-reaction-map.html"
ASSETS = Path("scripts/fukushuto_redesign")
MARKER = 'name="fukushuto-layout"'
LAYOUT_VERSION = "redesign-v1"
VOTE_TOPIC = "fukushuto-issue-stance-v1"
PROTECTED_BLOCKS = ("SEO_META", "ARTICLE_JSON_LD")
INTEGRATIONS = ("ADSENSE_TAG", "GA_TAG")
# 旧デザインの節 → 新デザインの置き場所。外部から旧アンカー付きで来た人を迷わせない。
# 論点ごとの旧ID（fb-・extras-・fukushuto-reading-）は issue-{論点ID} へ読み替える（スクリプト側）。
ALIASES = {
    "progress": "fukushuto-opening",
    "fukushuto-now": "fuk-op-route",
    "fuk-now-title": "fuk-op-route",
    "fukushuto-candidates": "fuk-op-map",
    "fuk-candidate-title": "fuk-op-map",
    "fuk-entry-switcher": "fukushuto-opening",
    "stance-glance": "fuk-op-count",
    "stance-glance-title": "fuk-op-count",
    "fukushuto-problems": "fukushuto-reading",
    "fuk-problems-title": "fukushuto-reading",
    "planet-block": "fukushuto-reading",
    "fallback": "fukushuto-reading",
    "fallback-nav": "fukushuto-reading",
    "issue-cards": "fukushuto-reading",
    "editorial": "fukushuto-reading",
    "fukushuto-tide-widget": "fukushuto-reading",
    "fact-check": "fukushuto-reading",
    "fact-check-title": "fukushuto-reading",
    "quiz": "fukushuto-reading",
    "ocean": "fukushuto-reading",
    "bukatsu-background": "fukushuto-background",
    "bukatsu-check": "fukushuto-background",
    "bg-title": "fukushuto-background",
    "fukushuto-faq": "bg-faq",
    "fuk-faq-title": "bg-faq",
    "classroom-title": "bg-classroom",
}
ISSUE_PREFIXES = ("fb-", "extras-", "fukushuto-reading-", "fuk-entry-panel-")


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
    import fukushuto_background as background  # noqa: PLC0415
    import fukushuto_opening as opening  # noqa: PLC0415
    import fukushuto_reading as reading  # noqa: PLC0415

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
            d = reading.load(root / "configs" / "fukushuto-reading.json")
            reading.check_all(d)
            as_of = as_of or reading.default_as_of(d)
            date.fromisoformat(as_of)
            fragment = opening.render_fragment(d["data"], as_of)
            body = reading.render_reading(d)
            bg = background.render(d, as_of, reading.ordered_issues(d))
        except SystemExit as exc:  # 生成器の照合は SystemExit で止まる。更新経路を巻き込まず止めるため変換する
            raise ValueError(f"新デザインの照合で停止しました: {exc}") from None
    return '<div class="fop-page">\n' + fragment + "</div>\n" + body + bg, d, as_of


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
    old_key = "var STORAGE_KEY='sns_vote_'+TOPIC+'_my';"
    if code.count(old_key) != 1 or "choiceIdx:issueIdx*STANCES.length+stanceIdx" not in code:
        raise ValueError("投票の保存キーか choice_idx の計算が想定と違います")
    # 本番ホストでだけ既存の保存キー。確認用の環境では別キーに保存し、本番の投票済み記録に触らない。
    code = code.replace(old_key, "var STORAGE_KEY=(window.SNS_REDESIGN_PRODUCTION?'sns_vote_':'sns_vote_preview_')+TOPIC+'_my';")
    section = BeautifulSoup(str(section), "html.parser").section
    section["class"] = ["fu-band", "fu-vote"]
    return str(section) + "\n<script>" + code + "</script>"


def _band(src: BeautifulSoup, selector: str, what: str, cls: str) -> str:
    node = BeautifulSoup(str(_one(src, selector, what)), "html.parser").find(True)
    node["class"] = list(node.get("class") or []) + ["fu-band", cls]
    return str(node)


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


def _phase_data(opening, ocfg: dict, as_of: str) -> dict:
    """読む日が締切・施行日を過ぎたとき、冒頭の段階表示だけを JS で切り替えるためのデータ。"""
    law_phase, comment_phase = opening.phase_of(ocfg, as_of)
    pt, pv = ocfg["phase_text"], opening.phase_values(ocfg)
    law = "before" if law_phase == "before" else None
    comment = "open" if comment_phase == "open" else None
    after_law = "after_unconfirmed" if law else law_phase
    after_comment = "closed" if comment else comment_phase
    return {
        "closes": ocfg["comment"]["closes_on"],
        "enforcement": ocfg["law"]["enforcement_on"],
        "law": law, "comment": comment,
        "comment_note": pt["comment"][after_comment].format(**pv),
        "enforce_note": pt["enforce"][after_law].format(**pv),
        "unconfirmed_label": pt["state_labels"]["unconfirmed"],
        # 「いつ決まる？」の答え：締切だけ／施行日だけ／両方を過ぎた場合の文
        "answers": {
            f"{c}|{e}": pt["answer_comment"][c].format(**pv) + pt["answer_enforce"][e].format(**pv)
            for c in dict.fromkeys((comment_phase, after_comment)) for e in dict.fromkeys((law_phase, after_law))
        },
        "static": f"{comment_phase}|{law_phase}",
    }


def _phase_script(data: dict) -> str:
    """意見募集の締切と施行日は、生成した日ではなく読む日で判定し直す（更新の間に表示が古くならないように）。"""
    return ("<script>(()=>{const c=" + json.dumps(data, ensure_ascii=False) + ";"
            "if(!c.law&&!c.comment)return;const s=document.querySelector('#fukushuto-opening');if(!s)return;"
            "const now=new Date(new Date().toLocaleString('en-US',{timeZone:'Asia/Tokyo'}));"
            "const p=n=>String(n).padStart(2,'0');const today=now.getFullYear()+'-'+p(now.getMonth()+1)+'-'+p(now.getDate());"
            "const closed=c.comment&&today>c.closes,enforced=c.law&&today>=c.enforcement;if(!closed&&!enforced)return;"
            "const note=(key,text)=>{const li=s.querySelector('.fop-stop[data-step=\"'+key+'\"]');if(!li)return null;"
            "const para=li.querySelector('p');if(para&&para.firstChild&&para.firstChild.nodeType===3)para.firstChild.textContent=text;return li;};"
            "if(closed)note('draft',c.comment_note);"
            "if(enforced){const li=note('enforce',c.enforce_note);if(li){li.className=li.className.replace(/fop-stop--\\w+/,'fop-stop--unconfirmed');"
            "const sr=li.querySelector('.fop-sr');if(sr)sr.textContent='（'+c.unconfirmed_label+'）';}}"
            "const [sc,sl]=c.static.split('|');const key=(closed?'closed':sc)+'|'+(enforced?'after_unconfirmed':sl);"
            "const a=s.querySelector('[data-answer=\"when\"] p:not(.fop-answer__short)');if(a&&c.answers[key])a.textContent=c.answers[key];"
            "})();</script>")


def _alias_script() -> str:
    return ("<script>(()=>{const aliases=" + json.dumps(ALIASES) + ",prefixes=" + json.dumps(ISSUE_PREFIXES) + ";"
            "function resolve(){let id=decodeURIComponent(location.hash.slice(1));"
            "const pre=prefixes.find(x=>id.startsWith(x));"
            "if(pre&&document.getElementById('issue-'+id.slice(pre.length)))id='issue-'+id.slice(pre.length);"
            "else if(id.startsWith('fuk-entry-panel-'))id='fukushuto-opening';"
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
    ocfg = d["ocfg"]
    assets = root / ASSETS
    css = "\n".join((assets / name).read_text(encoding="utf-8")
                    for name in ("opening.css", "reading.css", "production.css"))
    reading_js = (assets / "reading.js").read_text(encoding="utf-8")

    title = _one(src, "head > title", "title").get_text()
    fonts = "\n".join(str(n) for n in src.select('link[rel="preconnect"], link[href*="fonts.googleapis.com/css2"]'))
    adsense_meta = str(_one(src, 'meta[name="google-adsense-account"]', "AdSenseアカウントのmeta"))
    caution = _one(src, "#caution", "調査条件")
    contract = _one(src, "#planet-data", "PLANET_DATA")
    if f'"opinions":{int(d["public"]["opinion_count"])}' not in contract.get_text().replace(" ", ""):
        raise ValueError("PLANET_DATA の意見数が公開JSONと一致しません。元HTMLの更新を先に済ませてください。")
    trust = _block(source, "ARTICLE_TRUST")
    if f'{int(d["public"]["opinion_count"]):,}件' not in trust:
        raise ValueError("「このページの作り方」の意見数が公開JSONと一致しません。元HTMLの更新を先に済ませてください。")

    head = ['<!doctype html>', '<html lang="ja">', '<head>', '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{title}</title>"]
    head += [_block(source, name) for name in PROTECTED_BLOCKS]
    if mode == "preview":
        head.append('<meta name="robots" content="noindex">')
    head += [adsense_meta, fonts,
             '<link rel="stylesheet" href="site-tokens.css?v=3">',
             '<link rel="stylesheet" href="topic-modern.css?v=32">',
             f'<meta name="fukushuto-layout" content="{LAYOUT_VERSION}">',
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

    research = ('<!-- RESEARCH_CONDITIONS_START --><div class="fu-research" id="research-conditions">'
                + str(caution) + "</div><!-- RESEARCH_CONDITIONS_END -->")
    body_soup = BeautifulSoup(body, "html.parser")
    opening_section = body_soup.select_one("section.fop")
    opening_section["id"] = "fukushuto-opening"
    # 段階の切り替え（JS）が読む目印。表示は変えない
    for li, step in zip(opening_section.select(".fop-route__line > li.fop-stop"), ocfg["steps"]):
        li["data-step"] = step["key"]
    for card, answer in zip(opening_section.select(".fop-answers > article.fop-answer"), ocfg["answers"]):
        card["data-answer"] = answer["key"]
    # 調査条件は山なみの注記のすぐ下（件数の図の母数を示す位置）に置く
    map_box = body_soup.select_one("#fukushuto-reading .fr-map")
    map_box.select("p.fr-fine")[0].insert_after(BeautifulSoup(research, "html.parser"))
    _classroom(body_soup)
    faq = _faq_json_ld(body_soup)
    head.insert(head.index("</head>"), faq)
    body_html = str(body_soup).replace("../../../docs/images/", "images/")
    if "../../../docs/" in body_html:
        raise ValueError("試作用の相対パスが残っています")
    start, end = "<!-- FUKUSHUTO_READING_START -->", "<!-- FUKUSHUTO_READING_END -->"
    reading_start = body_html.index(start)
    reading_end = body_html.index(end) + len(end)
    body_html = (body_html[:reading_start] + "<!-- PLANET_SECTION_START -->\n" + body_html[reading_start:reading_end]
                 + "\n<!-- PLANET_SECTION_END -->" + body_html[reading_end:])
    # X投稿は開いたときに読み込む（部活動・皇室と同じ部品）。保護対象の head を作り直さないよう、本文だけに掛ける。
    sys.path.insert(0, str(ROOT / "scripts"))
    from bukatsu_redesign.x_embeds import add_x_embeds  # noqa: PLC0415
    embedded = BeautifulSoup(add_x_embeds("<html><head></head><body>" + body_html + "</body></html>"), "html.parser")
    x_style = "".join(str(n) for n in embedded.head.select("style"))
    x_script = str(embedded.body.select("script")[-1].extract())
    body_html = embedded.body.decode_contents()
    head.insert(head.index("</head>"), x_style)
    background_at = body_html.rindex("<section", 0, body_html.index('id="fukushuto-background"'))

    with _generators(root) as (opening, _reading, _background):
        phase = _phase_data(opening, ocfg, as_of)

    page = "\n".join(head) + "\n"
    page += '<body class="fukushuto-layout">\n'
    if mode == "preview":
        page += '<p class="fu-preview">公開前の確認用ページ（投票は送信されません）</p>\n'
    page += _header() + "\n<main>\n"
    page += body_html[:background_at] + _vote_section(src) + "\n" + body_html[background_at:]
    page += '<div class="fu-band fu-trust">' + trust + "</div>\n"
    page += _band(src, "#detail-data", "詳細データ", "fu-detail") + "\n"
    page += _band(src, "#related-topics", "次に読むテーマ", "fu-related") + "\n</main>\n"
    page += str(_one(src, "body > footer", "フッター")) + "\n"
    page += str(contract) + "\n"
    page += "<script>" + reading_js + "</script>\n"
    page += x_script + "\n" + _phase_script(phase) + "\n" + _alias_script() + "\n"
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
    # 基準日は既定で公開JSONの更新日。同じデータなら同じページになる（締切・施行日は読む日にJSで判定し直す）
    as_of = as_of or json.loads((root / "docs/data/themes/fukushuto.json").read_text(encoding="utf-8"))["updated_on"]
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
    from scripts.fukushuto_layout import source_for_refresh
    try:
        result = build(args.source_page or source_for_refresh(ROOT), args.output_dir, args.mode, as_of=args.as_of)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Built {len(result['files'])} file ({args.mode}, as_of {result['as_of']}); no deployment performed.")


if __name__ == "__main__":
    main()
