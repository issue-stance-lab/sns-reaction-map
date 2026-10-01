"""自転車の青切符ページへ課題77の連動表示を適用する。

ページ内のPLANET_DATAを件数の正本として、論点IDから理由・代表投稿・制度確認・
一次資料の入口を結ぶ。既存の山なみページを直接書き換えるのではなく、目印のある
候補だけに適用し、通常の定期更新からも同じ仕上げを再適用できる形にする。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from html import escape

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "bike-blue-ticket"
START = "<!-- BIKE_CONNECTED_START -->"
END = "<!-- BIKE_CONNECTED_END -->"
BRIDGE_START = "/* BIKE_CONNECTED_BRIDGE_START */"
BRIDGE_END = "/* BIKE_CONNECTED_BRIDGE_END */"
CSS_HREF = "bike-blue-ticket-connected.css?v=1"
JS_SRC = "bike-blue-ticket-connected.js?v=1"
PAGE_JS_SRC = "bike-blue-ticket-connected-page.js?v=1"
SEARCH_ENTRY_START = "<!-- BIKE_SEARCH_ENTRY_START -->"
SEARCH_ENTRY_END = "<!-- BIKE_SEARCH_ENTRY_END -->"
SEARCH_ENTRY_CSS = "bike-blue-ticket-search-entry.css?v=2"
SEARCH_ENTRY_JS = "bike-blue-ticket-search-entry.js?v=1"
PROGRESS_LABEL = "探ったところ"
DATA_PATTERN = re.compile(r'<script id="planet-data">window\.PLANET_DATA=(.*?);</script>', re.S)


def enabled(source: str) -> bool:
    return START in source


def planet_data(source: str) -> dict:
    match = DATA_PATTERN.search(source)
    if not match:
        raise ValueError("連動表示: PLANET_DATA が見つかりません")
    data = json.loads(match.group(1))
    if data.get("theme_id") != TOPIC:
        raise ValueError("連動表示は自転車青切符専用です")
    return data


def background_data() -> dict:
    path = ROOT / "data/verification/bike-blue-ticket-background.json"
    return json.loads(path.read_text(encoding="utf-8"))


def content_index(data: dict) -> dict:
    issues = data["issues"]
    issue_ids = {issue["id"] for issue in issues}
    claim_ids = {claim["id"] for claim in data["claims"]}
    if len(claim_ids) != len(data["claims"]):
        raise ValueError("連動表示: 資料照合IDが重複しています")

    background = background_data()
    checks = background["checklist"]["items"]
    for item in checks:
        ids = item.get("issue_ids") or []
        if not ids or set(ids) - issue_ids:
            raise ValueError(f"連動表示: 制度確認の接続先が不明です: {item['label']}")

    modes = {mode["id"] for mode in data["modes"]}
    stances = [
        {"id": stance["id"], "mode_id": stance["key"], "short_label": stance["label"]}
        for stance in data["stances"]
    ]
    if {stance["mode_id"] for stance in stances} | {"all"} != modes:
        raise ValueError("連動表示: 立場と山の表示モードが一致しません")

    result = {}
    default_issue_id = "bike-blue-ticket-other"
    global_source_only_ids = [
        item["id"] for item in data["ocean"]["sunk_continents"]
        if item.get("nearest_issue_id") not in issue_ids
    ]
    for issue in issues:
        iid = issue["id"]
        related = [claim["id"] for claim in issue.get("claims", [])]
        if set(related) - claim_ids:
            raise ValueError(f"連動表示: {iid} に未登録の資料照合があります")
        result[iid] = {
            "static_id": "fb-" + iid,
            "posts_id": "issue-" + iid,
            "claim_ids": related,
            "source_only_ids": [
                item["id"] for item in data["ocean"]["sunk_continents"]
                if item.get("nearest_issue_id") == iid
            ],
            "global_source_only_ids": global_source_only_ids if iid == default_issue_id else [],
            "shared_concern_ids": list(issue.get("veins", [])),
            # 自転車の年表は特定の1論点へ無理に帰属させず、ページ全体のタブとして表示する。
            "timeline_ids": [],
            "check_ids": [item["id"] for item in checks if iid in (item.get("issue_ids") or [])],
        }
    return {
        "schema": 1,
        "theme_id": TOPIC,
        "default_issue_id": default_issue_id,
        "global_source_only_ids": global_source_only_ids,
        "stances": stances,
        "issues": result,
        "background_checked_on": background["checked_on"],
        "scope_note": "理由の分類・投稿例・資料は、この論点全体の内容です。",
    }


AUDIT_SUFFIX = re.compile(
    r"\s*20\d{2}-\d{2}-\d{2}に今回新たに採用した\d+件を本文確認し、"
    r"この事実への新規言及は見つからなかった。母数は前回確認済み分と合わせた全意見数。$"
)


def display_source_note(note: str) -> str:
    """表示からだけ内部の追加確認ログを除く。PLANET_DATA は書き換えない。"""
    return AUDIT_SUFFIX.sub("", str(note)).rstrip()


def _remove_process_copy(source: str, data: dict) -> str:
    """旧HTMLや他のテーマ共通ビルダーから残る自転車ページ内の説明を除く。"""
    source = re.sub(
        r'(<p class="lead">収集したSNS投稿[\d,]+件のうち、分析対象の意見[\d,]+件)をAIで整理し、',
        r"\1を",
        source,
        count=1,
    )
    source = re.sub(
        r'\s*<h3>AIを使用した工程</h3>\s*<p>.*?</p>',
        "",
        source,
        count=1,
        flags=re.S,
    )
    source = source.replace(
        '<span class="review-note">AI分類。代表投稿は編集部が選定</span>', ""
    )
    source = source.replace("／）", "）")
    source = source.replace("<div>Powered by Yahooリアルタイム検索 + AI分類</div>", "")
    source = source.replace("\n    \n    <a href=\"index.html\"", "\n    <a href=\"index.html\"")
    source = source.replace("同じ検索語セットで取得した投稿をAIで分類しています。", "")
    source = source.replace(
        "この論点の中身（編集部が本文を読んで分けたもの）", "この論点の中身"
    )
    source = source.replace(
        'このテーマは、まだ編集部が一次資料を読んで「語られていないこと」を確かめていません。確かめるまで、ここは空のままにします。',
        "",
    )
    source = source.replace(
        "このテーマは、論点をまたいで言えることの整理がまだです。書けるまで、ここは空のままにします。",
        "",
    )
    source = source.replace(
        "論点をまたいで言えることを、編集部がまとめています。", ""
    )
    source = re.sub(
        r'    if \(D\.show_unreviewed_note !== false\)\{\n.*?\n    \}\n',
        "",
        source,
        count=1,
        flags=re.S,
    )
    source = re.sub(
        r'<p class="sub">ここから下は集計ではありません。編集部が一次資料を読んで確かめたことだけを置いています。'
        r'[^<]*AIの下読みを含む[^<]*</p>',
        "",
        source,
        count=1,
    )
    source = re.sub(
        r'<div class="note">[^<]*まだ編集部が投稿を1件ずつ読み直していません.*?</div>',
        "",
        source,
        flags=re.S,
    )

    # Ocean の静的表示は PLANET_DATA と重複するため、そのHTML範囲だけを整える。
    # 埋め込みJSONは再読ログの保存先としてそのまま残す。
    ocean_start = source.find('<section id="ocean"')
    ocean_close = source.find("</section>", ocean_start) if ocean_start >= 0 else -1
    if ocean_start >= 0 and ocean_close >= 0:
        ocean_end = ocean_close + len("</section>")
        ocean_html = source[ocean_start:ocean_end]
        for item in data.get("ocean", {}).get("sunk_continents", []):
            note = str(item.get("sns_note") or "")
            display_note = display_source_note(note)
            if note != display_note:
                ocean_html = ocean_html.replace(escape(note), escape(display_note))
        source = source[:ocean_start] + ocean_html + source[ocean_end:]
    return source


def _bridge(source: str) -> str:
    if BRIDGE_START in source:
        source = re.sub(re.escape(BRIDGE_START) + r".*?" + re.escape(BRIDGE_END) + r"\n?", "", source, flags=re.S)
    anchor = "/* ---------- 初期化 ----------"
    if source.count(anchor) != 1:
        raise ValueError("連動表示: 山の初期化位置を一意に見つけられません")
    bridge = (ROOT / "scripts/templates/bike_blue_ticket_connected_bridge.js").read_text(encoding="utf-8")
    return source.replace(anchor, BRIDGE_START + "\n" + bridge + "\n" + BRIDGE_END + "\n" + anchor, 1)


def _search_entry(source: str) -> str:
    """題名直下の検索入口を、山なみ更新時にも同じ位置へ保つ。"""
    template = (ROOT / "scripts/templates/bike_blue_ticket_search_entry.html").read_text(encoding="utf-8").strip()
    block = SEARCH_ENTRY_START + "\n" + template + "\n" + SEARCH_ENTRY_END
    if SEARCH_ENTRY_START in source or SEARCH_ENTRY_END in source:
        if source.count(SEARCH_ENTRY_START) != 1 or source.count(SEARCH_ENTRY_END) != 1:
            raise ValueError("検索入口: 目印が1組ではありません")
        source = re.sub(re.escape(SEARCH_ENTRY_START) + r".*?" + re.escape(SEARCH_ENTRY_END), "", source, flags=re.S)
    anchor = "  <main>\n"
    if source.count(anchor) != 1:
        raise ValueError("検索入口: ヒーロー直後のmain開始位置を一意に見つけられません")
    source = re.sub(r"(  </svg>\n)[ \t]*\n(?=  <main>)", r"\1", source, count=1)
    source = re.sub(re.escape(anchor) + r"[ \t]*\n", anchor, source, count=1)
    source = source.replace(anchor, anchor + block + "\n", 1)
    return source


def _progress_label(source: str) -> str:
    """操作への参加状況を表す進捗ラベルを、再生成後も維持する。"""
    pattern = re.compile(r'(<div id="progress">\s*<span>)[^<]*(</span>)')
    source, count = pattern.subn(r"\1" + PROGRESS_LABEL + r"\2", source, count=1)
    if count != 1:
        raise ValueError("進捗表示: ラベル位置を一意に見つけられません")
    return source


def apply(source: str, *, activate: bool = False, topic: str = TOPIC) -> str:
    """初回はactivate=True、以後は候補の目印があるときだけ同じHTMLを再生成する。"""
    if topic != TOPIC or not (activate or enabled(source)):
        return source
    from scripts.bike_blue_ticket_connected_content import END as CONTENT_END
    from scripts.bike_blue_ticket_connected_content import START as CONTENT_START
    from scripts.bike_blue_ticket_connected_content import render_templates

    data = planet_data(source)
    index = content_index(data)
    source = _bridge(source)
    source = _search_entry(source)
    source = _progress_label(source)
    content = render_templates(data, source, index)
    if CONTENT_START in source:
        source = re.sub(re.escape(CONTENT_START) + r".*?" + re.escape(CONTENT_END), content, source, flags=re.S)
    else:
        source = source.replace("</body>", content + "\n</body>", 1)

    payload = json.dumps(index, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    block = (
        START + "\n"
        f'<link rel="stylesheet" href="{CSS_HREF}">\n'
        '<script id="bike-connected-data" type="application/json">' + payload + "</script>\n"
        f'<script src="{JS_SRC}" defer></script>\n'
        f'<script src="{PAGE_JS_SRC}" defer></script>\n'
        f'<link rel="stylesheet" href="{SEARCH_ENTRY_CSS}">\n'
        f'<script src="{SEARCH_ENTRY_JS}" defer></script>\n'
        + END
    )
    if START in source:
        source, count = re.subn(re.escape(START) + r".*?" + re.escape(END), block, source, flags=re.S)
        if count != 1:
            raise ValueError("連動表示: 仕上げ処理の目印が1組ではありません")
    else:
        source = source.replace("</head>", block + "\n</head>", 1)
    source = _remove_process_copy(source, data)
    problems = validate(source)
    if problems:
        raise ValueError("連動表示の検査に失敗しました:\n  - " + "\n  - ".join(problems))
    return source


def validate(source: str) -> list[str]:
    if not enabled(source):
        return []
    from scripts.bike_blue_ticket_connected_content import END as CONTENT_END
    from scripts.bike_blue_ticket_connected_content import START as CONTENT_START

    problems = []
    soup = BeautifulSoup(source, "html.parser")
    try:
        data = planet_data(source)
        expected = content_index(data)
        blocks = soup.select("#bike-connected-data")
        if len(blocks) != 1 or json.loads(blocks[0].string or "null") != expected:
            problems.append("論点の接続表が現在の表示データと一致しません")
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return [str(exc)]
    if source.count(BRIDGE_START) != 1 or source.count(BRIDGE_END) != 1:
        problems.append("山と共通状態をつなぐ処理が1組ではありません")
    if source.count(CONTENT_START) != 1 or source.count(CONTENT_END) != 1:
        problems.append("読書面の目印が1組ではありません")
    if len(soup.select(f'link[href="{CSS_HREF}"]')) != 1:
        problems.append("連動表示のCSSが1つではありません")
    if len(soup.select(f'script[src="{JS_SRC}"][defer]')) != 1:
        problems.append("中心部分のJSが1つではありません")
    if len(soup.select(f'script[src="{PAGE_JS_SRC}"][defer]')) != 1:
        problems.append("ページ配置のJSが1つではありません")
    if len(soup.select(f'link[href="{SEARCH_ENTRY_CSS}"]')) != 1:
        problems.append("検索入口のCSSが1つではありません")
    if len(soup.select(f'script[src="{SEARCH_ENTRY_JS}"][defer]')) != 1:
        problems.append("検索入口のJSが1つではありません")
    entry = soup.select("#bike-search-entry")
    if len(entry) != 1 or entry[0].find_parent("main") is None:
        problems.append("検索入口がmainの先頭に1つありません")
    if len(soup.select("#section")) != 1 or not soup.select_one("#bike-search-entry a[href='#section']"):
        problems.append("検索入口から山なみへの移動先がありません")
    progress_label = soup.select_one("#progress > span")
    if progress_label is None or progress_label.get_text(strip=True) != PROGRESS_LABEL:
        problems.append(f"進捗ラベルが『{PROGRESS_LABEL}』ではありません")
    stance_buttons = {button.get("data-i") for button in soup.select("#stance-glance-buttons .sg-pick-btn")}
    if stance_buttons != {str(i) for i in range(len(data["stances"]))}:
        problems.append("立場ボタンの並びが立場データと一致しません")

    # script内の保存データは除外し、初期表示・静的フォールバック・templateを検査する。
    display_soup = BeautifulSoup(source, "html.parser")
    for node in display_soup.select("script, style"):
        node.decompose()
    display_text = display_soup.get_text(" ", strip=True)
    display_text += " " + " ".join(
        BeautifulSoup(node.decode_contents(), "html.parser").get_text(" ", strip=True)
        for node in soup.select("template")
    )
    forbidden = (
        "AIを使用した工程",
        "AIで整理し",
        "AI分類。代表投稿は編集部が選定",
        "Powered by Yahooリアルタイム検索 + AI分類",
        "同じ検索語セットで取得した投稿をAIで分類しています。",
        "理由の区分と個別投稿IDを結ぶ公開台帳はない",
        "この論点に対応する資料照合は、まだ登録されていません。",
        "AIが自動でつけた区分",
        "人が読んだ結果だけをまとめにします",
        "まだ編集部が投稿を1件ずつ読み直していません",
        "AIの下読みを含む",
        "編集部が本文を読んで分けたもの",
        "論点をまたいで言えることを、編集部がまとめています。",
        "今回新たに採用した",
        "まだ編集部が一次資料を読んで",
        "整理がまだです",
    )
    for phrase in forbidden:
        if phrase in display_text:
            problems.append("公開表示に不要な工程説明が残っています: " + phrase)

    for issue in data["issues"]:
        iid = issue["id"]
        templates = soup.select("#bike-blue-ticket-reading-" + iid)
        if len(templates) != 1:
            problems.append(f"読書面の入口が1つではありません: {iid}")
            continue
        reading = BeautifulSoup(templates[0].decode_contents(), "html.parser")
        connection = expected["issues"][iid]
        attrs = (
            ("claim_ids", "data-bike-claim"),
            ("source_only_ids", "data-bike-source-only"),
            ("global_source_only_ids", "data-bike-global-source-only"),
            ("shared_concern_ids", "data-bike-concern"),
            ("check_ids", "data-bike-check"),
        )
        for key, attr in attrs:
            found = [node.get(attr) for node in reading.select("[" + attr + "]")]
            if found != connection[key]:
                problems.append(f"読書面の接続が一致しません: {iid} {key}")
        if len(reading.select("[data-bike-post-url]")) != 2:
            problems.append(f"論点別の代表投稿が2件ではありません: {iid}")
    return problems
