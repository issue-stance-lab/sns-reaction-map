"""高齢者免許返納の連動表示を、ページ生成・部分更新の最後に適用する。"""
from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "elderly-license-revocation"
START = "<!-- ELDERLY_CONNECTED_START -->"
END = "<!-- ELDERLY_CONNECTED_END -->"
BRIDGE_START = "/* ELDERLY_CONNECTED_BRIDGE_START */"
BRIDGE_END = "/* ELDERLY_CONNECTED_BRIDGE_END */"
CSS_HREF = "elderly-connected.css?v=1"
JS_SRC = "elderly-connected.js?v=1"
PAGE_JS_SRC = "elderly-connected-page.js?v=1"
DATA_PATTERN = re.compile(r'(<script id="planet-data">window\.PLANET_DATA=)(.*?)(;</script>)', re.S)
REASON_POSTS = ROOT / "configs" / "elderly-license-reason-posts.json"


def enabled(source: str) -> bool:
    return START in source


def planet_data(source: str) -> dict:
    match = DATA_PATTERN.search(source)
    if not match:
        raise ValueError("連動表示: PLANET_DATA が見つかりません")
    data = json.loads(match[2])
    if data.get("theme_id") != TOPIC:
        raise ValueError("連動表示はelderly-license-revocation専用です")
    return data


def reason_posts() -> dict:
    return json.loads(REASON_POSTS.read_text(encoding="utf-8"))["issues"]


def content_index(data: dict) -> dict:
    """論点、主張、資料側項目、再読理由をIDで結ぶ。

    年表は論点へ推測で割り当てず、ページ全体の背景タブに残す。制度確認カードは
    このテーマには独立した登録簿がないため、空のままにして架空の説明を足さない。
    """
    issues = data["issues"]
    issue_ids = {i["id"] for i in issues}
    claims = data["claims"]
    claim_ids = {c["id"] for c in claims}
    if len(claim_ids) != len(claims):
        raise ValueError("連動表示: 資料照合IDが重複しています")
    modes = {m["id"] for m in data["modes"]}
    stances = [{"id": s["id"], "mode_id": s["key"], "short_label": s["label"]} for s in data["stances"]]
    if {s["mode_id"] for s in stances} | {"all"} != modes:
        raise ValueError("連動表示: 立場と山の表示モードが一致しません")
    posts = reason_posts()
    result = {}
    for issue in issues:
        iid = issue["id"]
        related = [c["id"] for c in issue.get("claims", [])]
        if set(related) - claim_ids:
            raise ValueError(f"連動表示: {iid} に未登録の資料照合があります")
        source_only = [x["id"] for x in data["ocean"].get("sunk_continents", []) if x.get("nearest_issue_id") == iid]
        sub = issue.get("sub") or {}
        reason_ids = [str(x["id"]) for x in sub.get("items", []) if not x.get("unread")]
        if sub.get("status") == "reread":
            configured = posts.get(iid, {})
            missing = [rid for rid in reason_ids if rid not in configured]
            if missing:
                raise ValueError(f"連動表示: 再読理由の投稿登録がありません: {iid} {missing}")
        result[iid] = {
            "posts_id": "issue-" + iid,
            "claim_ids": related,
            "source_only_ids": source_only,
            "shared_concern_ids": list(issue.get("veins", [])),
            "timeline_ids": [],
            "check_ids": [],
            "reason_ids": reason_ids,
        }
    return {
        "schema": 1,
        "theme_id": TOPIC,
        "stances": stances,
        "issues": result,
        "scope_note": "理由の分類・投稿例・資料は、この論点全体の内容です。再読済みの理由だけ、対応する投稿例を表示します。",
        "background_checked_on": "2026-08-18",
    }


def _bridge(source: str) -> str:
    if BRIDGE_START in source:
        source = re.sub(re.escape(BRIDGE_START) + r".*?" + re.escape(BRIDGE_END) + r"\n?", "", source, flags=re.S)
    anchor = "/* ---------- 初期化 ----------"
    if source.count(anchor) != 1:
        raise ValueError("連動表示: 山の初期化位置を一意に見つけられません")
    bridge = (ROOT / "scripts/templates/elderly_connected_bridge.js").read_text(encoding="utf-8")
    return source.replace(anchor, BRIDGE_START + "\n" + bridge + "\n" + BRIDGE_END + "\n" + anchor, 1)


def apply(source: str, *, activate: bool = False, topic: str = TOPIC) -> str:
    if topic != TOPIC or not (activate or enabled(source)):
        return source
    from scripts.elderly_connected_content import END as CONTENT_END
    from scripts.elderly_connected_content import START as CONTENT_START
    from scripts.elderly_connected_content import render_templates

    data = planet_data(source)
    index = content_index(data)
    source = _bridge(source)
    content = render_templates(data, source, index)
    if CONTENT_START in source:
        source = re.sub(re.escape(CONTENT_START) + r".*?" + re.escape(CONTENT_END), lambda _: content, source, flags=re.S)
    else:
        source = source.replace("</body>", content + "\n</body>", 1)
    payload = json.dumps(index, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    block = (
        START + f'\n<link rel="stylesheet" href="{CSS_HREF}">\n'
        '<script id="elderly-connected-data" type="application/json">' + payload + "</script>\n"
        f'<script src="{JS_SRC}" defer></script>\n'
        f'<script src="{PAGE_JS_SRC}" defer></script>\n' + END
    )
    if START in source:
        source, n = re.subn(re.escape(START) + r".*?" + re.escape(END), lambda _: block, source, flags=re.S)
        if n != 1:
            raise ValueError("連動表示: 仕上げ処理の目印が1組ではありません")
    else:
        if source.count("</head>") != 1:
            raise ValueError("連動表示: head の終端が1つではありません")
        source = source.replace("</head>", block + "\n</head>", 1)
    problems = validate(source)
    if problems:
        raise ValueError("連動表示の検査に失敗しました:\n  - " + "\n  - ".join(problems))
    return source


def validate(source: str) -> list[str]:
    if not enabled(source):
        return []
    from scripts.elderly_connected_content import END as CONTENT_END
    from scripts.elderly_connected_content import START as CONTENT_START

    problems = []
    soup = BeautifulSoup(source, "html.parser")
    try:
        data = planet_data(source)
        expected = content_index(data)
    except (ValueError, KeyError, TypeError) as exc:
        return [str(exc)]
    blocks = soup.select("#elderly-connected-data")
    if len(blocks) != 1 or json.loads(blocks[0].string or "null") != expected:
        problems.append("論点の接続表が現在の表示データと一致しません")
    if source.count(BRIDGE_START) != 1 or source.count(BRIDGE_END) != 1:
        problems.append("山と共通状態をつなぐ処理が1組ではありません")
    if source.count(CONTENT_START) != 1 or source.count(CONTENT_END) != 1:
        problems.append("読書面の目印が1組ではありません")
    if len(soup.select(f'link[href="{CSS_HREF}"]')) != 1:
        problems.append("連動表示のCSSが1つではありません")
    if len(soup.select(f'script[src="{JS_SRC}"][defer]')) != 1:
        problems.append("ページ配置のJSが1つではありません")
    if len(soup.select(f'script[src="{PAGE_JS_SRC}"][defer]')) != 1:
        problems.append("資料タブ・年表のJSが1つではありません")
    button_ids = {b.get("data-i") for b in soup.select("#stance-glance-buttons .sg-pick-btn")}
    if button_ids != {str(i) for i in range(len(data["stances"]))}:
        problems.append("立場ボタンの並びが立場データと一致しません")
    mode_ids = {m["id"] for m in data["modes"]} - {"all"}
    if mode_ids != {s["key"] for s in data["stances"]}:
        problems.append("立場フィルターと立場データが一致しません")
    for issue in data["issues"]:
        iid = issue["id"]
        connection = expected["issues"][iid]
        nodes = soup.select("#elderly-license-revocation-reading-" + iid)
        if len(nodes) != 1:
            problems.append(f"読書面の入口が1つではありません: {iid} ({len(nodes)})")
            continue
        reading = BeautifulSoup(nodes[0].decode_contents(), "html.parser")
        attrs = (("claim_ids", "data-elc-claim"), ("source_only_ids", "data-elc-source-only"),
                 ("shared_concern_ids", "data-elc-concern"), ("timeline_ids", "data-elc-timeline"),
                 ("check_ids", "data-elc-check"), ("reason_ids", "data-elc-reason-posts"))
        for key, attr in attrs:
            found = [el.get(attr) for el in reading.select("[" + attr + "]")]
            if found != connection[key]:
                problems.append(f"読書面の接続が一致しません: {iid} {key}")
        if issue.get("sub", {}).get("status") == "reread" and not reading.select("[data-elc-post-url]"):
            problems.append(f"再読済み論点に理由別投稿がありません: {iid}")
    return problems
