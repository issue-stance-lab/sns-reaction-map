"""辺野古高校生死亡事故の課題77連動表示を組み立てる。

ページ内のPLANET_DATAを件数の正本として、論点ごとの理由・資料照合・
一次資料の確認事項・年表・「資料にありSNSにないこと」を読書面へ接続する。
公開済みの理由別投稿台帳がないため、投稿例は生成しない。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "henoko-student-accident"
DEFAULT_ISSUE_ID = TOPIC + "-safety"
START = "<!-- HENOKO_CONNECTED_START -->"
END = "<!-- HENOKO_CONNECTED_END -->"
BRIDGE_START = "/* HENOKO_CONNECTED_BRIDGE_START */"
BRIDGE_END = "/* HENOKO_CONNECTED_BRIDGE_END */"
CSS_HREF = "henoko-connected.css?v=1"
JS_SRC = "henoko-connected.js?v=1"
PAGE_JS_SRC = "henoko-connected-page.js?v=1"
PROGRESS_LABEL = "探ったところ"
BANNED_USER_COPY = (
    "AIを使用した工程",
    "この回は分類モデルの切り替えと重なりました。",
    "このテーマには理由別の公開投稿台帳がないため",
    "AIの下読みを含む",
)
DATA_PATTERN = re.compile(r'(<script id="planet-data">window\.PLANET_DATA=)(.*?)(;</script>)', re.S)

# 背景台帳にはissue_idsがないため、既存の本文の内容に基づく接続をここで固定する。
# すべての項目は、未接続のまま捨てず、既定論点の読書面にも表示する。
CHECK_ISSUES = {
    "operator": [TOPIC + "-safety"],
    "alternative": [TOPIC + "-safety"],
    "briefing": [TOPIC + "-safety", TOPIC + "-peace-education"],
    "views": [TOPIC + "-neutrality", TOPIC + "-peace-education"],
}
TIMELINE_ISSUES = {
    "accident": [TOPIC + "-safety"],
    "notice": [TOPIC + "-safety", TOPIC + "-peace-education"],
    "findings": [TOPIC + "-safety", TOPIC + "-public-response"],
    "governor": [TOPIC + "-neutrality", TOPIC + "-peace-education"],
    "follow-up": [TOPIC + "-safety"],
    "diet-scope": [TOPIC + "-neutrality", TOPIC + "-peace-education"],
    "diet-followup": [TOPIC + "-safety", TOPIC + "-neutrality"],
    "diet-nhk": [TOPIC + "-public-response"],
    "prefecture-inquiry": [TOPIC + "-public-response"],
}


def enabled(source: str) -> bool:
    return START in source


def planet_data(source: str) -> dict:
    match = DATA_PATTERN.search(source)
    if not match:
        raise ValueError("連動表示: PLANET_DATA が見つかりません")
    data = json.loads(match.group(2))
    if data.get("theme_id") != TOPIC:
        raise ValueError("連動表示は辺野古高校生死亡事故専用です")
    return data


def background_data() -> dict:
    path = ROOT / "data/verification/henoko-student-accident-background.json"
    return json.loads(path.read_text(encoding="utf-8"))


def content_index(data: dict) -> dict:
    issues = data["issues"]
    issue_ids = {issue["id"] for issue in issues}
    if DEFAULT_ISSUE_ID not in issue_ids:
        raise ValueError("連動表示: 辺野古の既定論点がありません")
    claim_ids = {claim["id"] for claim in data["claims"]}
    if len(claim_ids) != len(data["claims"]):
        raise ValueError("連動表示: 資料照合IDが重複しています")

    background = background_data()
    checks = background["checklist"]["items"]
    check_ids = {item["id"] for item in checks}
    if check_ids != set(CHECK_ISSUES):
        raise ValueError("連動表示: 制度確認の接続表が不足または過剰です")
    if set(TIMELINE_ISSUES) != {item["id"] for item in background["timeline"]}:
        raise ValueError("連動表示: 年表の接続表が不足または過剰です")
    for item_id, targets in CHECK_ISSUES.items():
        if not targets or set(targets) - issue_ids:
            raise ValueError(f"連動表示: 制度確認の接続先が不明です: {item_id}")
    for item_id, targets in TIMELINE_ISSUES.items():
        if not targets or set(targets) - issue_ids:
            raise ValueError(f"連動表示: 年表の接続先が不明です: {item_id}")

    modes = {mode["id"] for mode in data["modes"]}
    stances = [
        {"id": stance["id"], "mode_id": stance["key"], "short_label": stance["label"]}
        for stance in data["stances"]
    ]
    if {stance["mode_id"] for stance in stances} | {"all"} != modes:
        raise ValueError("連動表示: 立場と山の表示モードが一致しません")

    source_items = data["ocean"]["sunk_continents"]
    veins = {vein["id"]: vein for vein in data["ocean"]["veins"]}
    timeline_all = [item["id"] for item in background["timeline"]]
    result = {}
    for issue in issues:
        iid = issue["id"]
        related = [claim["id"] for claim in issue.get("claims", [])]
        if set(related) - claim_ids:
            raise ValueError(f"連動表示: {iid} に未登録の資料照合があります")
        timeline_ids = [
            item_id for item_id, targets in TIMELINE_ISSUES.items() if iid in targets
        ]
        if iid == DEFAULT_ISSUE_ID:
            timeline_ids = timeline_all
        result[iid] = {
            "static_id": "fb-" + iid,
            "claim_ids": related,
            "source_only_ids": [
                item["id"] for item in source_items if item.get("nearest_issue_id") == iid
            ],
            "shared_concern_ids": [vein_id for vein_id in issue.get("veins", []) if vein_id in veins],
            "timeline_ids": timeline_ids,
            "check_ids": [item_id for item_id, targets in CHECK_ISSUES.items() if iid in targets],
            "editorial_ids": [
                item["id"] for item in data["editorial"]["findings"]
            ] if iid == DEFAULT_ISSUE_ID else [],
            "post_status": "unavailable",
        }
    return {
        "schema": 1,
        "theme_id": TOPIC,
        "default_issue_id": DEFAULT_ISSUE_ID,
        "stances": stances,
        "issues": result,
        "background_checked_on": background["checked_on"],
        "scope_note": "理由・資料照合・年表は、この論点を読むための補助線です。件数は選んだ立場の分類結果です。",
    }


def _bridge(source: str) -> str:
    if BRIDGE_START in source:
        source = re.sub(re.escape(BRIDGE_START) + r".*?" + re.escape(BRIDGE_END) + r"\n?", "", source, flags=re.S)
    anchor = "/* ---------- 初期化 ----------"
    if source.count(anchor) != 1:
        raise ValueError("連動表示: 山の初期化位置を一意に見つけられません")
    bridge = (ROOT / "scripts/templates/henoko_connected_bridge.js").read_text(encoding="utf-8")
    return source.replace(anchor, BRIDGE_START + "\n" + bridge + "\n" + BRIDGE_END + "\n" + anchor, 1)


def _progress_copy(source: str) -> str:
    """操作済み地点の表示を、読了率と誤解されない辺野古専用文言にする。"""
    pattern = re.compile(r'(<div id="progress"[^>]*>\s*<span[^>]*>)([^<]*)(</span>)')
    matches = pattern.findall(source)
    if len(matches) != 1:
        raise ValueError("連動表示: 探査記録の見出しを一意に見つけられません")
    return pattern.sub(lambda match: match.group(1) + PROGRESS_LABEL + match.group(3), source, count=1)


def _remove_mechanical_copy(source: str) -> str:
    """辺野古ページに残った制作工程と内部事情の説明を接続時にも除く。"""
    source = re.sub(
        r"\s*<h3>AIを使用した工程</h3>\s*<p>.*?</p>",
        "",
        source,
        count=1,
        flags=re.S,
    )
    source = re.sub(
        r"\s*<li>この回は分類モデルの切り替えと重なりました。.*?</li>",
        "",
        source,
        count=1,
        flags=re.S,
    )
    source = source.replace("／AIの下読みを含む", "")
    return source


def apply(source: str, *, activate: bool = False, topic: str = TOPIC) -> str:
    if topic != TOPIC or not (activate or enabled(source)):
        return source
    from scripts.henoko_connected_content import END as CONTENT_END
    from scripts.henoko_connected_content import START as CONTENT_START
    from scripts.henoko_connected_content import render_templates

    data = planet_data(source)
    index = content_index(data)
    source = _bridge(source)
    source = _progress_copy(source)
    source = _remove_mechanical_copy(source)
    content = render_templates(data, source, index)
    if CONTENT_START in source:
        source = re.sub(re.escape(CONTENT_START) + r".*?" + re.escape(CONTENT_END), content, source, flags=re.S)
    else:
        source = source.replace("</body>", content + "\n</body>", 1)
    payload = json.dumps(index, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    block = (
        START + "\n"
        f'<link rel="stylesheet" href="{CSS_HREF}">\n'
        '<script id="henoko-connected-data" type="application/json">' + payload + "</script>\n"
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
    from scripts.henoko_connected_content import END as CONTENT_END
    from scripts.henoko_connected_content import START as CONTENT_START

    problems = []
    soup = BeautifulSoup(source, "html.parser")
    try:
        data = planet_data(source)
        expected = content_index(data)
        blocks = soup.select("#henoko-connected-data")
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
    progress = soup.select("#progress > span:first-child")
    if len(progress) != 1 or progress[0].get_text(strip=True) != PROGRESS_LABEL:
        problems.append("探査記録が操作数と分かる見出しになっていません")
    stance_buttons = {button.get("data-i") for button in soup.select("#stance-glance-buttons .sg-pick-btn")}
    if stance_buttons != {str(i) for i in range(len(data["stances"]))}:
        problems.append("立場ボタンの並びが立場データと一致しません")

    for issue in data["issues"]:
        iid = issue["id"]
        templates = soup.select("#" + TOPIC + "-reading-" + iid)
        if len(templates) != 1:
            problems.append(f"読書面の入口が1つではありません: {iid}")
            continue
        reading = BeautifulSoup(templates[0].decode_contents(), "html.parser")
        connection = expected["issues"][iid]
        for key, attr in (
            ("claim_ids", "data-henoko-claim"),
            ("source_only_ids", "data-henoko-source-only"),
            ("shared_concern_ids", "data-henoko-concern"),
            ("timeline_ids", "data-henoko-timeline"),
            ("check_ids", "data-henoko-check"),
            ("editorial_ids", "data-henoko-editorial"),
        ):
            found = [node.get(attr) for node in reading.select("[" + attr + "]")]
            if found != connection[key]:
                problems.append(f"読書面の接続が一致しません: {iid} {key}")
        if reading.select("[data-henoko-post-unavailable]"):
            problems.append(f"投稿台帳の内部事情が表示されています: {iid}")
    for phrase in BANNED_USER_COPY:
        if phrase in source:
            problems.append(f"利用者向けではない説明が残っています: {phrase}")
    return problems
