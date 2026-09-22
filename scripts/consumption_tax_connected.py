"""消費税の連動表示の共通仕上げ。候補の目印があるページだけに適用する。

既存の静的本文を維持し、IDの接続表・共有の閲覧状態・論点ごとの読書面を登録する。
件数や原稿の別コピーを正典にせず、ページ内のPLANET_DATAと既存の生成元を読む。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "consumption-tax-cut"
START = "<!-- TAX_CONNECTED_START -->"
END = "<!-- TAX_CONNECTED_END -->"
BRIDGE_START = "/* TAX_CONNECTED_BRIDGE_START */"
BRIDGE_END = "/* TAX_CONNECTED_BRIDGE_END */"
DATA_PATTERN = re.compile(r'(<script id="planet-data">window\.PLANET_DATA=)(.*?)(;</script>)', re.S)


def enabled(source: str) -> bool:
    return START in source


def planet_data(source: str) -> dict:
    match = DATA_PATTERN.search(source)
    if not match:
        raise ValueError("連動表示: PLANET_DATA が見つかりません")
    data = json.loads(match[2])
    if data.get("theme_id") != TOPIC:
        raise ValueError("連動表示は消費税専用です")
    return data


def content_index(data: dict) -> dict:
    """画面内の要素をIDで結ぶ。件数・原稿・確認日はPLANET_DATAに一元化する。"""
    # import時にページを生成しない。通常ビルドから呼ぶ場合も原稿定義だけを読む。
    from build_consumption_tax_page import BACKGROUND_DATA, ISSUE_CARDS_POSTS, STANCE_META

    issues = data["issues"]
    issue_ids = {i["id"] for i in issues}
    if issue_ids != set(ISSUE_CARDS_POSTS):
        raise ValueError("連動表示: 論点と投稿例の登録が一致しません")
    for item in [*BACKGROUND_DATA["policies"], *BACKGROUND_DATA["timeline"], *data["ocean"]["veins"]]:
        if not item["issue_ids"] or set(item["issue_ids"]) - issue_ids:
            raise ValueError(f"連動表示: 接続先の論点が不明です: {item['id']}")
    for item in data["ocean"]["sunk_continents"]:
        if item["nearest_issue_id"] not in issue_ids:
            raise ValueError(f"連動表示: 資料側の項目の接続先が不明です: {item['id']}")
    claim_ids = {c["id"] for c in data["claims"]}
    if len(claim_ids) != len(data["claims"]):
        raise ValueError("連動表示: 資料照合IDが重複しています")
    modes = {m["id"] for m in data["modes"]}
    stances = [{"id": s["id"], "mode_id": s["key"], "short_label": STANCE_META[s["key"]]["label"]} for s in data["stances"]]
    if {s["mode_id"] for s in stances} | {"all"} != modes:
        raise ValueError("連動表示: 立場と山の表示モードが一致しません")
    result = {}
    for issue in issues:
        iid = issue["id"]
        related = [c["id"] for c in issue["claims"]]
        if set(related) - claim_ids:
            raise ValueError(f"連動表示: {iid} に未登録の資料照合があります")
        result[iid] = {
            "static_id": "fb-" + iid,
            "posts_id": "issue-" + iid,
            "post_urls": [url for url, _ in ISSUE_CARDS_POSTS[iid]],
            "claim_ids": related,
            "source_only_ids": [x["id"] for x in data["ocean"]["sunk_continents"]
                                if x["nearest_issue_id"] == iid],
            "shared_concern_ids": [x["id"] for x in data["ocean"]["veins"] if iid in x["issue_ids"]],
            "policy_ids": [x["id"] for x in BACKGROUND_DATA["policies"] if iid in x["issue_ids"]],
            "timeline_ids": [x["id"] for x in BACKGROUND_DATA["timeline"] if iid in x["issue_ids"]],
            "method_link": "about.html#method" if iid == TOPIC + "-other" else None,
        }
    return {
        "schema": 1, "theme_id": TOPIC,
        "default_issue_id": TOPIC + "-scope",
        "stances": stances, "issues": result,
        "background_checked_on": BACKGROUND_DATA["checked_on"],
        "scope_note": "理由の分類・投稿例・資料は、この論点全体の内容です。",
    }


def _bridge(source: str) -> str:
    """既存の山の状態を唯一の状態として公開する。別の選択状態を複製しない。"""
    if BRIDGE_START in source:
        source = re.sub(re.escape(BRIDGE_START) + r".*?" + re.escape(BRIDGE_END) + r"\n?", "", source, flags=re.S)
    anchor = "/* ---------- 初期化 ----------"
    if source.count(anchor) != 1:
        raise ValueError("連動表示: 山の初期化位置を一意に見つけられません")
    bridge = (ROOT / "scripts/templates/consumption_tax_connected_bridge.js").read_text()
    return source.replace(anchor, BRIDGE_START + "\n" + bridge + "\n" + BRIDGE_END + "\n" + anchor, 1)


def apply(source: str, *, activate: bool = False, topic: str = TOPIC) -> str:
    """全更新経路の最後から呼ぶ。同じ入力では同じHTML、他テーマでは完全な無操作。"""
    if topic != TOPIC or not (activate or enabled(source)):
        return source
    # 公開時に参加者数の修正版を取得する。将来の版番号は巻き戻さない。
    source = source.replace('src="topic-modern.js?v=13"', 'src="topic-modern.js?v=14"')
    from consumption_tax_connected_content import correct_editorial, corrected_observations, corrected_focus, render_templates, START as CONTENT_START, END as CONTENT_END
    from build_planet_data import static_editorial
    from html import escape
    data = planet_data(source)
    correct_editorial(data)
    encoded = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    source = DATA_PATTERN.sub(lambda m: m[1] + encoded + m[3], source)
    focus = corrected_focus(data)
    source, n = re.subn(
        r'(<div class="thirty-summary".*?<span class="conclusion-count"><b>)[\d,]+(</b>件</span>\s*<strong>).*?(</strong>\s*<span class="conclusion-detail">).*?(</span>)',
        lambda m: m[1] + str(focus['count']) + m[2] + escape(focus['headline']) + m[3] + escape(focus['detail']) + m[4],
        source, flags=re.S,
    )
    if n != 1:
        raise ValueError('連動表示: 議論の中心の見出しが1か所ではありません')
    source, n = re.subn(r'<section id="editorial"[^>]*>.*?</section>',
                       lambda _: static_editorial(data).lstrip(), source, flags=re.S)
    if n != 1:
        raise ValueError("連動表示: 編集部整理が1か所ではありません")
    observations = '<ul class="article-trust-observations">\n' + ''.join(
        '      <li>' + escape(text) + '</li>\n' for text in corrected_observations(data)
    ) + '    </ul>'
    source, n = re.subn(r'<ul class="article-trust-observations">.*?</ul>', lambda _: observations, source, flags=re.S)
    if n != 1:
        raise ValueError("連動表示: 編集情報の観察記録が1か所ではありません")
    index = content_index(data)
    # 山だけを再生成する経路でも、ページ全体の数値同期が使う見出しを維持する。
    source, headings = re.subn(
        r'(<div class="panel-title"><h2>SNS反応マップ</h2><span>).*?(</span></div>)',
        lambda m: m[1] + f'意見{data["totals"]["opinions"]}件 | 幅＝意見の数 / 高さ＝強い表現の割合' + m[2],
        source, flags=re.S,
    )
    if headings != 1:
        raise ValueError("連動表示: 反応マップの見出しが1つではありません")
    from build_consumption_tax_page import background_context, issue_cards, stance_glance
    # バーと投稿欄の件数も、山と同じ入力でそろえる。独立した固定値を残さない。
    counts = {s["key"]: s["count"] for s in data["stances"]}
    opinions = data["totals"]["opinions"]
    shares = {key: 100 * n / opinions if opinions else 0 for key, n in counts.items()}
    stance_ids = {s["key"]: s["id"] for s in data["stances"]}
    stance_colors = {s["key"]: s["color"] for s in data["stances"]}
    for name, body in (("STANCE_GLANCE", stance_glance(opinions, counts, shares, stance_ids=stance_ids, stance_colors=stance_colors)),
                       ("ISSUE_CARDS", issue_cards(data=data)),
                       ("BACKGROUND_CONTEXT", background_context())):
        pattern = r"<!-- " + name + r"_START -->.*?<!-- " + name + r"_END -->"
        source, n = re.subn(pattern, lambda _: body, source, flags=re.S)
        if n != 1:
            raise ValueError(f"連動表示: {name} の本文が1組ではありません")
    source = _bridge(source)
    from consumption_tax_connected_vote import apply as connect_vote
    source = connect_vote(source, data)
    content = render_templates(data, source, index)
    if CONTENT_START in source:
        source = re.sub(re.escape(CONTENT_START) + r".*?" + re.escape(CONTENT_END), lambda _: content, source, flags=re.S)
    else:
        source = source.replace('</body>', content + '\n</body>', 1)
    payload = json.dumps(index, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    block = (
        START + '\n<link rel="stylesheet" href="consumption-tax-connected.css?v=5">\n'
        '<script id="tax-connected-data" type="application/json">' + payload + '</script>\n'
        '<script src="consumption-tax-connected.js?v=5" defer></script>\n'
        '<script src="consumption-tax-connected-page.js?v=5" defer></script>\n' + END
    )
    if START in source:
        pattern = re.escape(START) + r".*?" + re.escape(END)
        source, n = re.subn(pattern, lambda _: block, source, flags=re.S)
        if n != 1:
            raise ValueError("連動表示: 仕上げ処理の目印が1組ではありません")
    else:
        if source.count("</head>") != 1:
            raise ValueError("連動表示: head の終端が1つではありません")
        source = source.replace("</head>", block + "\n</head>", 1)
    # 各部分更新が古いブロックを抜いて挿し直しても、マーカー前の空行を増やさない。
    source = re.sub(r"\n[ \t]*\n+(?=<!-- [A-Z_]+_(?:START|END) -->)", "\n\n", source)
    source = re.sub(r"(<!-- [A-Z_]+_END -->)\n(?:[ \t]*\n)+", r"\1\n\n", source)
    problems = validate(source)
    if problems:
        raise ValueError("連動表示の検査に失敗しました:\n  - " + "\n  - ".join(problems))
    return source


def validate(source: str) -> list[str]:
    """旧配置の前後関係ではなく、本文・所属・出典・入口が残っていることを見る。"""
    if not enabled(source):
        return []
    from build_consumption_tax_page import BACKGROUND_CHECKS, BACKGROUND_DATA, BACKGROUND_TIMELINE, CLAIM_AUDIT, CHECKED_ON, ISSUE_CARDS_POSTS

    problems = []
    soup = BeautifulSoup(source, "html.parser")
    try:
        data = planet_data(source)
        expected = content_index(data)
        from consumption_tax_reason_posts import load as load_reason_posts, validate_reading
        reason_posts = load_reason_posts(data)
        blocks = soup.select("#tax-connected-data")
        if len(blocks) != 1 or json.loads(blocks[0].string or "null") != expected:
            problems.append("論点の接続表が現在の表示データと一致しません")
    except (ValueError, KeyError, TypeError) as exc:
        return [str(exc)]

    def one(selector: str):
        nodes = soup.select(selector)
        if len(nodes) != 1:
            problems.append(f"必要な入口が1つではありません: {selector} ({len(nodes)})")
        return nodes[0] if len(nodes) == 1 else None

    for selector in ("#stance-glance", "#planet-block", "#panel", "#list", "#vote-section",
                     "#bg-title", "#ck-title", "#claim-audit", "#issue-cards", "#guesses", "#quiz", "#ocean",
                     'link[href="consumption-tax-connected.css?v=5"]',
                     'script[src="consumption-tax-connected.js?v=5"][defer]',
                     'script[src="consumption-tax-connected-page.js?v=5"][defer]'):
        one(selector)
    if source.count(BRIDGE_START) != 1 or source.count(BRIDGE_END) != 1:
        problems.append("山と共通状態をつなぐ処理が1組ではありません")
    button_ids = [b.get("data-stance-id") for b in soup.select("#stance-glance .sg-pick-btn")]
    if len(button_ids) != len(data["stances"]) or set(button_ids) != {s["id"] for s in data["stances"]}:
        problems.append("立場ボタンがIDで一意に登録されていません")
    if len(soup.select("#ocean .sunk")) != len(data["ocean"]["sunk_continents"]):
        problems.append("資料側の項目の静的本文が欠落しています")
    for vein in data["ocean"]["veins"]:
        one('[data-vein="' + vein["id"] + '"]')
    for issue in data["issues"]:
        iid = issue["id"]
        static = one("#fb-" + iid)
        posts = one("#issue-" + iid)
        reading = one("#tax-reading-" + iid)
        if reading:
            problems.extend(validate_reading(reading, iid, reason_posts))
            connections = expected["issues"][iid]
            for key, attr in (("claim_ids", "data-tax-claim"), ("policy_ids", "data-tax-policy"),
                              ("timeline_ids", "data-tax-timeline"), ("source_only_ids", "data-tax-source-only"),
                              ("shared_concern_ids", "data-tax-concern")):
                if [el.get(attr) for el in reading.select('[' + attr + ']')] != connections[key]:
                    problems.append(f"読書面の接続が一致しません: {iid} {key}")
            if {el.get("data-tax-post-url") for el in reading.select('[data-tax-post-url]')} != set(connections["post_urls"]):
                problems.append(f"読書面の投稿例が一致しません: {iid}")
            if {el.get("data-tax-reason") for el in reading.select('[data-tax-reason]')} != {x["id"] for x in issue["sub"].get("items", [])}:
                problems.append(f"読書面の理由分類が一致しません: {iid}")
            for claim in issue["claims"]:
                card = reading.select_one('[data-tax-claim="' + claim["id"] + '"]')
                if card and not {x["url"] for x in claim["sources"]}.issubset({a.get("href") for a in card.select('a[href]')}):
                    problems.append(f"読書面の資料照合の出典が欠落しています: {iid} {claim['id']}")
            for item in BACKGROUND_DATA["policies"]:
                card = reading.select_one('[data-tax-policy="' + item["id"] + '"]')
                if card and not {u for u, _ in item["links"]}.issubset({a.get("href") for a in card.select('a[href]')}):
                    problems.append(f"読書面の制度説明の出典が欠落しています: {iid}")
            for key, attr, items in (
                ("年表", "data-tax-timeline", [{"id": x["id"], "urls": {u for u, _ in x["links"]}}
                                           for x in BACKGROUND_DATA["timeline"]]),
                ("資料側", "data-tax-source-only", [{"id": x["id"], "urls": {s["url"] for s in x["sources"]}}
                                                  for x in data["ocean"]["sunk_continents"]]),
            ):
                for item in items:
                    card = reading.select_one(f'[{attr}="{item["id"]}"]')
                    if card and not item["urls"].issubset({a.get("href") for a in card.select('a[href]')}):
                        problems.append(f"読書面の{key}の出典が欠落しています: {iid} {item['id']}")
        if static and not static.get_text(strip=True):
            problems.append(f"静的本文が空です: {iid}")
        if posts:
            urls = {a.get("href") for a in posts.select("a[href]")}
            if not {u for u, _ in ISSUE_CARDS_POSTS[iid]}.issubset(urls):
                problems.append(f"投稿例が所属論点から欠落しています: {iid}")
        # 画像の拡大入口は静的本文にも残す。選択中の論点だけに閉じ込めない。
        if static and not static.select_one(".landing-image[data-img]"):
            problems.append(f"静的本文から図解を開けません: {iid}")
    audit = soup.select_one("#claim-audit")
    if audit:
        cards = audit.select("[data-claim-id]")
        if {c.get("data-claim-id") for c in cards} != {c["key"] for c in CLAIM_AUDIT} or len(cards) != len(CLAIM_AUDIT):
            problems.append("資料照合の6件がIDで一意に登録されていません")
        for entry in CLAIM_AUDIT:
            card = audit.select_one('[data-claim-id="' + entry["key"] + '"]')
            if card and not {u for u, _ in entry["links"]}.issubset({a.get("href") for a in card.select("a[href]")}):
                problems.append(f"資料照合の出典が欠落しています: {entry['key']}")
        if CHECKED_ON not in audit.get_text():
            problems.append("資料照合の確認日が欠落しています")
    if len(soup.select("#bukatsu-background .bg-tl > li")) != len(BACKGROUND_TIMELINE):
        problems.append("経緯3段階の本文が欠落しています")
    if len(soup.select("#bukatsu-check .ck")) != len(BACKGROUND_CHECKS):
        problems.append("政府方針4項目の本文が欠落しています")
    for row in [*BACKGROUND_TIMELINE, *BACKGROUND_CHECKS]:
        for url, _ in row[-1]:
            if not soup.find("a", href=url):
                problems.append("制度説明の出典が欠落しています: " + url)
    for key, attr in (("policies", "data-policy-id"), ("timeline", "data-timeline-id")):
        for item in BACKGROUND_DATA[key]:
            node = one(f'[{attr}="{item["id"]}"]')
            if node and not {u for u, _ in item["links"]}.issubset({a.get("href") for a in node.select("a[href]")}):
                problems.append("制度説明の項目内に出典がありません: " + item["id"])
    return problems
