"""学校あだ名禁止ページへ課題77の連動表示を適用する。

PLANET_DATAを件数の正本として、論点IDから理由・投稿・制度確認・一次資料を結ぶ。
初回だけ ``activate=True`` で有効化し、以後はページ内の目印を見て定期更新にも
同じ仕上げを再適用する。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "school-nickname-ban"
START = "<!-- SCHOOL_NICKNAME_CONNECTED_START -->"
END = "<!-- SCHOOL_NICKNAME_CONNECTED_END -->"
SEARCH_START = "<!-- SCHOOL_NICKNAME_SEARCH_ENTRY_START -->"
SEARCH_END = "<!-- SCHOOL_NICKNAME_SEARCH_ENTRY_END -->"
FAQ_START = "<!-- SCHOOL_NICKNAME_FAQ_START -->"
FAQ_END = "<!-- SCHOOL_NICKNAME_FAQ_END -->"
FAQ_JSONLD_START = "<!-- SCHOOL_NICKNAME_FAQ_JSONLD_START -->"
FAQ_JSONLD_END = "<!-- SCHOOL_NICKNAME_FAQ_JSONLD_END -->"
BRIDGE_START = "/* SCHOOL_NICKNAME_CONNECTED_BRIDGE_START */"
BRIDGE_END = "/* SCHOOL_NICKNAME_CONNECTED_BRIDGE_END */"
CSS_HREF = "school-nickname-connected.css?v=4"
JS_SRC = "school-nickname-connected.js?v=1"
PAGE_JS_SRC = "school-nickname-connected-page.js?v=2"
DATA_PATTERN = re.compile(r'<script id="planet-data">window\.PLANET_DATA=(.*?);</script>', re.S)

CHECK_ISSUES = {
    "scope": ["school-nickname-ban-school-practice", "school-nickname-ban-uniform-rule"],
    "reason": ["school-nickname-ban-uniform-rule", "school-nickname-ban-gender-consideration"],
    "voice": ["school-nickname-ban-psychological-safety", "school-nickname-ban-individual-choice"],
    "revision": ["school-nickname-ban-school-practice", "school-nickname-ban-uniform-rule"],
}


def enabled(source: str) -> bool:
    return START in source


def planet_data(source: str) -> dict:
    match = DATA_PATTERN.search(source)
    if not match:
        raise ValueError("連動表示: PLANET_DATA が見つかりません")
    data = json.loads(match.group(1))
    if data.get("theme_id") != TOPIC:
        raise ValueError("連動表示は学校あだ名禁止テーマ専用です")
    return data


def background_data() -> dict:
    path = ROOT / "data/verification/school-nickname-ban-background.json"
    return json.loads(path.read_text(encoding="utf-8"))


def content_index(data: dict) -> dict:
    issues = data["issues"]
    issue_ids = {issue["id"] for issue in issues}
    claim_ids = {claim["id"] for claim in data["claims"]}
    if len(claim_ids) != len(data["claims"]):
        raise ValueError("連動表示: 資料照合IDが重複しています")

    background = background_data()
    checks = background["checklist"]["items"]
    check_ids = {item["id"] for item in checks}
    if check_ids != set(CHECK_ISSUES):
        raise ValueError("連動表示: 制度確認の接続表が不足または過剰です")
    for check_id, ids in CHECK_ISSUES.items():
        if not ids or set(ids) - issue_ids:
            raise ValueError(f"連動表示: 制度確認の接続先が不明です: {check_id}")

    modes = {mode["id"] for mode in data["modes"]}
    stances = [
        {"id": stance["id"], "mode_id": stance["key"], "short_label": stance["label"]}
        for stance in data["stances"]
    ]
    if {stance["mode_id"] for stance in stances} | {"all"} != modes:
        raise ValueError("連動表示: 立場と山の表示モードが一致しません")

    default_issue_id = "school-nickname-ban-uniform-rule"
    source_items = data["ocean"]["sunk_continents"]
    global_source_only_ids = [item["id"] for item in source_items if not item.get("nearest_issue_id")]
    veins = {vein["id"]: vein for vein in data["ocean"].get("veins", [])}
    timeline_ids = [item["id"] for item in background["timeline"]]
    result = {}
    for issue in issues:
        iid = issue["id"]
        related = [claim["id"] for claim in issue.get("claims", [])]
        if set(related) - claim_ids:
            raise ValueError(f"連動表示: {iid} に未登録の資料照合があります")
        shared = [vein_id for vein_id in issue.get("veins", []) if vein_id in veins]
        result[iid] = {
            "static_id": "fb-" + iid,
            "posts_id": "issue-" + iid,
            "claim_ids": related,
            "source_only_ids": [item["id"] for item in source_items if item.get("nearest_issue_id") == iid],
            "global_source_only_ids": global_source_only_ids if iid == default_issue_id else [],
            "shared_concern_ids": shared,
            "timeline_ids": timeline_ids if iid == default_issue_id else [],
            "check_ids": [check_id for check_id, ids in CHECK_ISSUES.items() if iid in ids],
        }
    return {
        "schema": 1,
        "theme_id": TOPIC,
        "default_issue_id": default_issue_id,
        "global_source_only_ids": global_source_only_ids,
        "stances": stances,
        "issues": result,
        "background_checked_on": background["checked_on"],
        "scope_note": "件数は収集投稿の分類結果です。理由・投稿例・資料は、この論点を読むための補助線です。",
        "reason_post_note": "理由は編集部が読み直した投稿をまとめたものです。下の投稿は各理由から選んだ代表例で、賛否の割合を表しません。",
    }


def _bridge(source: str) -> str:
    if BRIDGE_START in source:
        source = re.sub(re.escape(BRIDGE_START) + r".*?" + re.escape(BRIDGE_END) + r"\n?", "", source, flags=re.S)
    anchor = "/* ---------- 初期化 ----------"
    if source.count(anchor) != 1:
        raise ValueError("連動表示: 山の初期化位置を一意に見つけられません")
    bridge = (ROOT / "scripts/templates/school_nickname_connected_bridge.js").read_text(encoding="utf-8")
    return source.replace(anchor, BRIDGE_START + "\n" + bridge + "\n" + BRIDGE_END + "\n" + anchor, 1)


def apply(source: str, *, activate: bool = False, topic: str = TOPIC) -> str:
    """初回はactivate=True、以後は目印があるときだけ再生成する。"""
    if topic != TOPIC or not (activate or enabled(source)):
        return source
    try:
        from scripts.school_nickname_connected_content import END as CONTENT_END
        from scripts.school_nickname_connected_content import FAQ_END, FAQ_JSONLD_END, FAQ_JSONLD_START, FAQ_START
        from scripts.school_nickname_connected_content import SEARCH_END, SEARCH_START
        from scripts.school_nickname_connected_content import START as CONTENT_START
        from scripts.school_nickname_connected_content import render_faq, render_faq_jsonld, render_search_entry, render_templates
    except ModuleNotFoundError:
        from school_nickname_connected_content import END as CONTENT_END  # type: ignore[no-redef]
        from school_nickname_connected_content import FAQ_END, FAQ_JSONLD_END, FAQ_JSONLD_START, FAQ_START  # type: ignore[no-redef]
        from school_nickname_connected_content import SEARCH_END, SEARCH_START  # type: ignore[no-redef]
        from school_nickname_connected_content import START as CONTENT_START  # type: ignore[no-redef]
        from school_nickname_connected_content import render_faq, render_faq_jsonld, render_search_entry, render_templates  # type: ignore[no-redef]

    data = planet_data(source)
    index = content_index(data)
    background = background_data()
    source = source.replace(
        '<div id="progress"><span>読んだところ</span>',
        '<div id="progress"><span>探ったところ</span>',
        1,
    )
    source = source.replace(
        '<span class="how">質問に答える・山を押す・クイズに答えると増えます</span>',
        '<span class="how">論点を選ぶなど、このページで記録対象の操作をすると増えます</span>',
        1,
    )
    source = re.sub(r"<title>.*?</title>", "<title>学校のあだ名禁止はなぜ？さん付け・いじめとの関係と賛否｜SNS反応まっぷ</title>", source, count=1, flags=re.S)
    # description系metaは configs/theme-seo.json と apply_theme_trust.py が正典。
    # ここで書き換えると、公開昇格順（builder→trust）の後にbuilderを再実行した際、
    # 信頼情報の文面を巻き戻してしまうため触らない。
    source = re.sub(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="学校のあだ名禁止はなぜ？さん付け・いじめとの関係と賛否">', source, count=1)
    source = re.sub(r'<meta name="twitter:title" content="[^"]*">', '<meta name="twitter:title" content="学校のあだ名禁止はなぜ？さん付け・いじめとの関係と賛否">', source, count=1)
    source = re.sub(
        r'(<!-- ARTICLE_JSON_LD_START -->.*?"headline": ")[^"]*',
        r'\1学校のあだ名禁止はなぜ？さん付け・いじめとの関係と賛否',
        source,
        count=1,
        flags=re.S,
    )
    source = re.sub(
        r'(<!-- ARTICLE_JSON_LD_START -->.*?"description": ")[^"]*',
        r'\1学校のあだ名禁止は全国一律の決まり？文科省・法律資料で根拠を確認し、さん付け指導との違い、いじめ防止への期待と懸念、賛成・反対の理由をSNS意見から整理します。',
        source,
        count=1,
        flags=re.S,
    )
    source = source.replace("<h1>学校のあだ名禁止は必要？賛成・反対の理由</h1>", "<h1>学校のあだ名禁止はなぜ？ さん付け・いじめとの関係と賛否</h1>", 1)

    search_block = render_search_entry(data, background)
    if SEARCH_START in source:
        source = re.sub(re.escape(SEARCH_START) + r".*?" + re.escape(SEARCH_END), search_block, source, flags=re.S)
    else:
        source = source.replace("<!-- STANCE_GLANCE_START -->", search_block + "\n<!-- STANCE_GLANCE_START -->", 1)
    faq_block = render_faq()
    if FAQ_START in source:
        source = re.sub(re.escape(FAQ_START) + r".*?" + re.escape(FAQ_END), faq_block, source, flags=re.S)
    else:
        source = source.replace('<section class="panel" id="related-topics">', faq_block + '\n<section class="panel" id="related-topics">', 1)
    faq_jsonld = render_faq_jsonld()
    if FAQ_JSONLD_START in source:
        source = re.sub(re.escape(FAQ_JSONLD_START) + r".*?" + re.escape(FAQ_JSONLD_END), faq_jsonld, source, flags=re.S)
    else:
        source = source.replace("</head>", faq_jsonld + "\n</head>", 1)
    source = _bridge(source)
    content = render_templates(data, source, index)
    if CONTENT_START in source:
        source = re.sub(re.escape(CONTENT_START) + r".*?" + re.escape(CONTENT_END), content, source, flags=re.S)
    else:
        source = source.replace("</body>", content + "\n</body>", 1)

    payload = json.dumps(index, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    block = (
        START + "\n"
        f'<link rel="stylesheet" href="{CSS_HREF}">\n'
        '<script id="school-nickname-connected-data" type="application/json">' + payload + "</script>\n"
        f'<script src="{JS_SRC}" defer></script>\n'
        f'<script src="{PAGE_JS_SRC}" defer></script>\n'
        + END
    )
    if START in source:
        source, count = re.subn(re.escape(START) + r".*?" + re.escape(END), block, source, flags=re.S)
        if count != 1:
            raise ValueError("連動表示: 仕上げ処理の目印が1組ではありません")
    else:
        source = source.replace("</head>", block + "\n</head>", 1)
    problems = validate(source)
    if problems:
        raise ValueError("連動表示の検査に失敗しました:\n  - " + "\n  - ".join(problems))
    return source


def validate(source: str) -> list[str]:
    if not enabled(source):
        return []
    try:
        from scripts.school_nickname_connected_content import END as CONTENT_END
        from scripts.school_nickname_connected_content import START as CONTENT_START
    except ModuleNotFoundError:
        from school_nickname_connected_content import END as CONTENT_END  # type: ignore[no-redef]
        from school_nickname_connected_content import START as CONTENT_START  # type: ignore[no-redef]

    problems = []
    soup = BeautifulSoup(source, "html.parser")
    try:
        data = planet_data(source)
        expected = content_index(data)
        blocks = soup.select("#school-nickname-connected-data")
        if len(blocks) != 1 or json.loads(blocks[0].string or "null") != expected:
            problems.append("論点の接続表が現在の表示データと一致しません")
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return [str(exc)]
    if source.count(BRIDGE_START) != 1 or source.count(BRIDGE_END) != 1:
        problems.append("山と共通状態をつなぐ処理が1組ではありません")
    if source.count(CONTENT_START) != 1 or source.count(CONTENT_END) != 1:
        problems.append("読書面の目印が1組ではありません")
    for start, end, label in (
        (SEARCH_START, SEARCH_END, "検索入口"),
        (FAQ_START, FAQ_END, "FAQ"),
        (FAQ_JSONLD_START, FAQ_JSONLD_END, "FAQ構造化データ"),
    ):
        if source.count(start) != 1 or source.count(end) != 1:
            problems.append(f"{label}の目印が1組ではありません")
    if len(soup.select("#school-nickname-guide")) != 1 or len(soup.select("#school-nickname-faq")) != 1:
        problems.append("検索入口またはFAQが1つではありません")
    guide_tabs = soup.select("#school-nickname-guide [data-school-nickname-guide-tab]")
    guide_panels = soup.select("#school-nickname-guide [data-school-nickname-guide-panel]")
    if len(guide_tabs) != 3 or len(guide_panels) != 3:
        problems.append("検索入口の論点タブと表示面が3組ではありません")
    elif any(tab.get("aria-controls") != panel.get("id") for tab, panel in zip(guide_tabs, guide_panels)):
        problems.append("検索入口の論点タブと表示面の接続が一致しません")
    guide_issue_ids = {panel.get("data-school-nickname-issue-id") for panel in guide_panels}
    known_issue_ids = {issue["id"] for issue in data["issues"]}
    if guide_issue_ids != {
        "school-nickname-ban-school-practice",
        "school-nickname-ban-psychological-safety",
        "school-nickname-ban-uniform-rule",
    } or not guide_issue_ids <= known_issue_ids:
        problems.append("検索入口から山並みマップへの論点接続が一致しません")
    if len(soup.select("#school-nickname-faq details")) != 10:
        problems.append("FAQが10問ではありません")
    progress = soup.select_one("#progress")
    if progress is None or not progress.select_one("span") or progress.select_one("span").get_text(strip=True) != "探ったところ":
        problems.append("進捗表示が操作数に合う『探ったところ』ではありません")
    if progress is not None and "記録対象の操作" not in progress.get_text(" ", strip=True):
        problems.append("進捗表示に操作記録である説明がありません")
    if len(soup.select(f'link[href="{CSS_HREF}"]')) != 1:
        problems.append("連動表示のCSSが1つではありません")
    if len(soup.select(f'script[src="{JS_SRC}"][defer]')) != 1:
        problems.append("中心部分のJSが1つではありません")
    if len(soup.select(f'script[src="{PAGE_JS_SRC}"][defer]')) != 1:
        problems.append("ページ配置のJSが1つではありません")
    stance_buttons = {button.get("data-i") for button in soup.select("#stance-glance-buttons .sg-pick-btn")}
    if stance_buttons != {str(i) for i in range(len(data["stances"]))}:
        problems.append("立場ボタンの並びが立場データと一致しません")

    for issue in data["issues"]:
        iid = issue["id"]
        templates = soup.select("#school-nickname-ban-reading-" + iid)
        if len(templates) != 1:
            problems.append(f"読書面の入口が1つではありません: {iid}")
            continue
        reading = BeautifulSoup(templates[0].decode_contents(), "html.parser")
        connection = expected["issues"][iid]
        attrs = (
            ("claim_ids", "data-school-nickname-claim"),
            ("source_only_ids", "data-school-nickname-source-only"),
            ("global_source_only_ids", "data-school-nickname-global-source-only"),
            ("shared_concern_ids", "data-school-nickname-concern"),
            ("timeline_ids", "data-school-nickname-timeline"),
            ("check_ids", "data-school-nickname-check"),
        )
        for key, attr in attrs:
            found = [node.get(attr) for node in reading.select("[" + attr + "]")]
            if found != connection[key]:
                problems.append(f"読書面の接続が一致しません: {iid} {key}")
        if len(reading.select("[data-school-nickname-post-url]")) != 2:
            problems.append(f"論点別の代表投稿が2件ではありません: {iid}")
    return problems
