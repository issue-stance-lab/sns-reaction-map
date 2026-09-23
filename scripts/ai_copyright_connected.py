"""生成AIと著作権の連動表示（工程2: 土台）。候補の目印があるページだけに適用する。

既存の静的本文（STANCE_GLANCE・bukatsu-background・bukatsu-check・PLANET_SECTION）を
書き換えず、IDの接続表とバー↔山の状態共有（STANCE_GLANCEの3ボタン⇄#modesの立場フィルター）
を足す。件数や原稿の別コピーを正典にせず、ページ内のPLANET_DATA・
data/verification/ai-copyright-background.jsonを読む。

論点を選んだときの読書面（理由・投稿例・資料照合・年表・制度確認）は工程3で追加する。
ここではまだ#panelの中身を差し替えない（drawPanel()は無変更）。

制度確認4項目（#bukatsu-check、「法律」と「任意のルールを分けて確かめる」）は、工程1の
内容確定書のドラフト案どおり、項目名が論点名と直接対応するため本工程でissue_idsを追加した
（data/verification/ai-copyright-background.jsonのchecklist.items[]）。年表6件は対応する
論点が一意に定まらないため無タグのまま維持する（V01の要件は日付切替のみで論点連動は
必須ではない。bukatsu-chikiのように後日タグ付けする場合はtimeline側へissue_idsを足せば
content_index()が自動で拾う）。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "ai-copyright"
START = "<!-- AI_COPYRIGHT_CONNECTED_START -->"
END = "<!-- AI_COPYRIGHT_CONNECTED_END -->"
BRIDGE_START = "/* AI_COPYRIGHT_CONNECTED_BRIDGE_START */"
BRIDGE_END = "/* AI_COPYRIGHT_CONNECTED_BRIDGE_END */"
CSS_HREF = "ai-copyright-connected.css?v=1"
DATA_PATTERN = re.compile(r'(<script id="planet-data">window\.PLANET_DATA=)(.*?)(;</script>)', re.S)


def enabled(source: str) -> bool:
    return START in source


def planet_data(source: str) -> dict:
    match = DATA_PATTERN.search(source)
    if not match:
        raise ValueError("連動表示: PLANET_DATA が見つかりません")
    data = json.loads(match[2])
    if data.get("theme_id") != TOPIC:
        raise ValueError("連動表示はai-copyright専用です")
    return data


def background_data() -> dict:
    """`data/verification/ai-copyright-background.json`をそのまま返す。別コピーを持たない。"""
    path = ROOT / "data/verification/ai-copyright-background.json"
    return json.loads(path.read_text(encoding="utf-8"))


def content_index(data: dict) -> dict:
    """画面内の要素をIDで結ぶ。件数・原稿・確認日はPLANET_DATAに一元化する。

    claim_ids・source_only_ids・shared_concern_idsはPLANET_DATA側（論点ごとに
    既に解決済み）をそのまま転記する。check_idsは全項目にissue_idsがある前提で
    厳格に検査する（本工程で4件とも追加済み）。timeline_idsは無タグのままなので
    現状は常に空配列になる（該当なし。タグが増えれば自動で反映される）。
    """
    issues = data["issues"]
    issue_ids = {i["id"] for i in issues}
    claim_ids = {c["id"] for c in data["claims"]}
    if len(claim_ids) != len(data["claims"]):
        raise ValueError("連動表示: 資料照合IDが重複しています")
    modes = {m["id"] for m in data["modes"]}
    stances = [{"id": s["id"], "mode_id": s["key"], "short_label": s["label"]} for s in data["stances"]]
    if {s["mode_id"] for s in stances} | {"all"} != modes:
        raise ValueError("連動表示: 立場と山の表示モードが一致しません")
    background = background_data()
    timeline = background["timeline"]
    checklist = background["checklist"]["items"]
    for item in checklist:
        if not item.get("issue_ids") or set(item["issue_ids"]) - issue_ids:
            raise ValueError(f"連動表示: 制度確認の接続先の論点が不明です: {item['label']}")
    result = {}
    for issue in issues:
        iid = issue["id"]
        related = [c["id"] for c in issue["claims"]]
        if set(related) - claim_ids:
            raise ValueError(f"連動表示: {iid} に未登録の資料照合があります")
        result[iid] = {
            "posts_id": "issue-" + iid,
            "claim_ids": related,
            "source_only_ids": [x["id"] for x in data["ocean"]["sunk_continents"]
                                if x.get("nearest_issue_id") == iid],
            "shared_concern_ids": list(issue.get("veins", [])),
            "timeline_ids": [t["id"] for t in timeline if iid in (t.get("issue_ids") or [])],
            "check_ids": [c["id"] for c in checklist if iid in c["issue_ids"]],
        }
    return {
        "schema": 1, "theme_id": TOPIC,
        "stances": stances, "issues": result,
        "scope_note": "理由の分類・投稿例・資料は、この論点全体の内容です。",
        "background_checked_on": background["checked_on"],
    }


def _bridge(source: str) -> str:
    """既存の山の状態を唯一の状態として公開する。別の選択状態を複製しない。"""
    if BRIDGE_START in source:
        source = re.sub(re.escape(BRIDGE_START) + r".*?" + re.escape(BRIDGE_END) + r"\n?", "", source, flags=re.S)
    anchor = "/* ---------- 初期化 ----------"
    if source.count(anchor) != 1:
        raise ValueError("連動表示: 山の初期化位置を一意に見つけられません")
    bridge = (ROOT / "scripts/templates/ai_copyright_connected_bridge.js").read_text(encoding="utf-8")
    return source.replace(anchor, BRIDGE_START + "\n" + bridge + "\n" + BRIDGE_END + "\n" + anchor, 1)


def apply(source: str, *, activate: bool = False, topic: str = TOPIC) -> str:
    """全更新経路の最後から呼ぶ。同じ入力では同じHTML、他テーマでは完全な無操作。

    工程2時点では、山の立場フィルターとSTANCE_GLANCEの状態共有のみを行う。
    論点を選んだときの読書面（`<template>`生成・#panel差し替え）は工程3で追加する。
    """
    if topic != TOPIC or not (activate or enabled(source)):
        return source
    data = planet_data(source)
    index = content_index(data)
    source = _bridge(source)
    payload = json.dumps(index, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    block = (
        START + f'\n<link rel="stylesheet" href="{CSS_HREF}">\n'
        '<script id="ai-copyright-connected-data" type="application/json">' + payload + '</script>\n' + END
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
    problems = validate(source)
    if problems:
        raise ValueError("連動表示の検査に失敗しました:\n  - " + "\n  - ".join(problems))
    return source


def validate(source: str) -> list[str]:
    """接続表の一致・目印の対応・バー↔山の共有状態の配線を見る（工程2の範囲）。"""
    if not enabled(source):
        return []
    problems = []
    soup = BeautifulSoup(source, "html.parser")
    try:
        data = planet_data(source)
        expected = content_index(data)
    except (ValueError, KeyError, TypeError) as exc:
        return [str(exc)]
    blocks = soup.select("#ai-copyright-connected-data")
    if len(blocks) != 1 or json.loads(blocks[0].string or "null") != expected:
        problems.append("論点の接続表が現在の表示データと一致しません")
    if source.count(BRIDGE_START) != 1 or source.count(BRIDGE_END) != 1:
        problems.append("山と共通状態をつなぐ処理が1組ではありません")
    if len(soup.select(f'link[href="{CSS_HREF}"]')) != 1:
        problems.append("連動表示のCSSが1つではありません")
    button_ids = {b.get("data-i") for b in soup.select("#stance-glance-buttons .sg-pick-btn")}
    if button_ids != {str(i) for i in range(len(data["stances"]))}:
        problems.append("立場ボタン（STANCE_GLANCE）の並びが立場データと一致しません")
    mode_ids = {m["id"] for m in data["modes"]} - {"all"}
    stance_keys = {s["key"] for s in data["stances"]}
    if mode_ids != stance_keys:
        problems.append("立場フィルター（#modes）と立場データが一致しません")
    return problems
