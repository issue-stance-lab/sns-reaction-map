"""副首都ページへ課題77の連動表示を適用する。"""
from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "fukushuto"
START = "<!-- FUKUSHUTO_CONNECTED_START -->"
END = "<!-- FUKUSHUTO_CONNECTED_END -->"
BRIDGE_START = "/* FUKUSHUTO_CONNECTED_BRIDGE_START */"
BRIDGE_END = "/* FUKUSHUTO_CONNECTED_BRIDGE_END */"
CSS_HREF = "fukushuto-connected.css?v=1"
JS_SRC = "fukushuto-connected.js?v=1"
PAGE_JS_SRC = "fukushuto-connected-page.js?v=1"
DATA_PATTERN = re.compile(r'<script id="planet-data">window\.PLANET_DATA=(.*?);</script>', re.S)


def enabled(source: str) -> bool:
    return START in source


def planet_data(source: str) -> dict:
    match = DATA_PATTERN.search(source)
    if not match:
        raise ValueError("連動表示: PLANET_DATA が見つかりません")
    data = json.loads(match.group(1))
    if data.get("theme_id") != TOPIC:
        raise ValueError("連動表示は副首都専用です")
    return data


def background_data() -> dict:
    return json.loads((ROOT / "data/verification/fukushuto-background.json").read_text(encoding="utf-8"))


def content_index(data: dict) -> dict:
    issue_ids = {issue["id"] for issue in data["issues"]}
    claim_ids = {claim["id"] for claim in data["claims"]}
    if len(claim_ids) != len(data["claims"]):
        raise ValueError("連動表示: 資料照合IDが重複しています")
    checks = background_data()["checklist"]["items"]
    for item in checks:
        ids = item.get("issue_ids") or []
        if not ids or set(ids) - issue_ids:
            raise ValueError(f"連動表示: 制度確認の接続先が不明です: {item['label']}")
    modes = {mode["id"] for mode in data["modes"]}
    stances = [{"id": s["id"], "mode_id": s["key"], "short_label": s["label"]} for s in data["stances"]]
    if {s["mode_id"] for s in stances} | {"all"} != modes:
        raise ValueError("連動表示: 立場と山の表示モードが一致しません")

    result = {}
    for issue in data["issues"]:
        iid = issue["id"]
        related = [claim["id"] for claim in issue.get("claims", [])]
        if set(related) - claim_ids:
            raise ValueError(f"連動表示: {iid} に未登録の資料照合があります")
        result[iid] = {
            "static_id": "fb-" + iid,
            "posts_id": "issue-" + iid,
            "claim_ids": related,
            "source_only_ids": [item["id"] for item in data["ocean"]["sunk_continents"] if item.get("nearest_issue_id") == iid],
            "global_source_only_ids": [],
            "shared_concern_ids": [],
            "timeline_ids": [],
            "check_ids": [item["id"] for item in checks if iid in (item.get("issue_ids") or [])],
        }
    return {
        "schema": 1,
        "theme_id": TOPIC,
        "default_issue_id": "fukushuto-location",
        "global_source_only_ids": [],
        "stances": stances,
        "issues": result,
        "background_checked_on": background_data()["checked_on"],
        "scope_note": "理由の分類・投稿例・資料は、この論点全体の内容です。",
        "reason_post_note": "理由の区分と個別投稿IDを結ぶ公開台帳はないため、投稿は論点全体の代表例として表示しています。",
    }


def _bridge(source: str) -> str:
    if BRIDGE_START in source:
        source = re.sub(re.escape(BRIDGE_START) + r".*?" + re.escape(BRIDGE_END) + r"\n?", "", source, flags=re.S)
    anchor = "/* ---------- 初期化 ----------"
    if source.count(anchor) != 1:
        raise ValueError("連動表示: 山の初期化位置を一意に見つけられません")
    bridge = (ROOT / "scripts/templates/bike_blue_ticket_connected_bridge.js").read_text(encoding="utf-8")
    bridge = (
        bridge.replace("BikeBlueTicketConnectedMap", "FukushutoConnectedMap")
        .replace("bike-blue-ticket", "fukushuto")
        .replace("bike-", "fuk-")
        .replace("bikeVisual", "fukVisual")
        .replace("bikeAnimation", "fukAnimation")
    )
    return source.replace(anchor, BRIDGE_START + "\n" + bridge + "\n" + BRIDGE_END + "\n" + anchor, 1)


def apply(source: str, *, activate: bool = False, topic: str = TOPIC) -> str:
    if topic != TOPIC or not (activate or enabled(source)):
        return source
    from scripts.fukushuto_connected_content import END as CONTENT_END
    from scripts.fukushuto_connected_content import START as CONTENT_START
    from scripts.fukushuto_connected_content import render_templates

    data = planet_data(source)
    index = content_index(data)
    source = _bridge(source)
    content = render_templates(data, source, index)
    if CONTENT_START in source:
        source = re.sub(re.escape(CONTENT_START) + r".*?" + re.escape(CONTENT_END), content, source, flags=re.S)
    else:
        source = source.replace("</body>", content + "\n</body>", 1)
    payload = json.dumps(index, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    block = (
        START + "\n" + f'<link rel="stylesheet" href="{CSS_HREF}">\n'
        + '<script id="fukushuto-connected-data" type="application/json">' + payload + "</script>\n"
        + f'<script src="{JS_SRC}" defer></script>\n<script src="{PAGE_JS_SRC}" defer></script>\n' + END
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
    from scripts.fukushuto_connected_content import END as CONTENT_END
    from scripts.fukushuto_connected_content import START as CONTENT_START

    problems = []
    soup = BeautifulSoup(source, "html.parser")
    try:
        data = planet_data(source)
        expected = content_index(data)
        blocks = soup.select("#fukushuto-connected-data")
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
    if len(soup.select(f'script[src="{JS_SRC}"][defer]')) != 1 or len(soup.select(f'script[src="{PAGE_JS_SRC}"][defer]')) != 1:
        problems.append("連動表示のJSが1組ではありません")
    stance_buttons = {button.get("data-i") for button in soup.select("#stance-glance-buttons .sg-pick-btn")}
    if stance_buttons != {str(i) for i in range(len(data["stances"]))}:
        problems.append("立場ボタンの並びが立場データと一致しません")
    for issue in data["issues"]:
        iid, connection = issue["id"], expected["issues"][issue["id"]]
        templates = soup.select("#fukushuto-reading-" + iid)
        if len(templates) != 1:
            problems.append(f"読書面の入口が1つではありません: {iid}")
            continue
        reading = BeautifulSoup(templates[0].decode_contents(), "html.parser")
        for key, attr in (("claim_ids", "data-fuk-claim"), ("source_only_ids", "data-fuk-source-only"), ("check_ids", "data-fuk-check")):
            found = [node.get(attr) for node in reading.select("[" + attr + "]")]
            if found != connection[key]:
                problems.append(f"読書面の接続が一致しません: {iid} {key}")
        if len(reading.select("[data-fuk-post-url]")) != 2:
            problems.append(f"論点別の代表投稿が2件ではありません: {iid}")
    return problems
