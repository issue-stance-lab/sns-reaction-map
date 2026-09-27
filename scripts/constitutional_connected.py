"""憲法改正論議の連動表示（工程2: 土台／工程3: 読書面・選択体験／工程4: ページ全体の再配置）。
候補の目印があるページだけに適用する。

既存の静的本文（STANCE_GLANCE・bukatsu-background・bukatsu-check・PLANET_SECTION）を
書き換えず、IDの接続表・バー↔山の状態共有（STANCE_GLANCEの4ボタン⇄#modesの立場フィルター）・
論点を選んだときの読書面（理由・投稿例・資料照合・制度確認）を足す。件数や原稿の別コピーを
正典にせず、ページ内のPLANET_DATA・data/verification/constitutional-amendment-background.jsonを読む。

制度確認4項目（#bukatsu-check、「法律」と「任意のルールを分けて確かめる」）は、工程1の
内容確定書のドラフト案どおり、項目名が論点名と直接対応するため工程2でissue_idsを追加した
（data/verification/constitutional-amendment-background.jsonのchecklist.items[]）。年表11件は対応する
論点が一意に定まらないため無タグのまま維持する（V01の要件は日付切替のみで論点連動は
必須ではない。bukatsu-chikiのように後日タグ付けする場合はtimeline側へissue_idsを足せば
content_index()が自動で拾う。本工程の読書面は空のまま生成される）。

読書面（`<template id="constitutional-amendment-reading-{id}">`）の生成は
`scripts/constitutional_connected_content.py`が担当し、実際にdrawPanel()を差し替えて
表示する処理・山の選択色（V05）・480msの滑らかな変化（V11）・初期表示の自動着地・
深いリンクの名前空間統一・出典操作の計測は`scripts/templates/constitutional_connected_bridge.js`
（生成HTMLへ挿入）が担当する。`docs/constitutional-connected.js`がバー・山・論点ボタンの
配置（V02〜V04）、`docs/constitutional-connected-page.js`が年表の日付タブ化・資料3タブ化・
旧代表投稿・ocean・bukatsu-checkの非表示・判断の入口の
折りたたみ（V07〜V10、理由別X投稿=V07はconstitutional-amendmentに理由別の投稿データが無いため
対象外・工程1内容確定書の方針）を担当する。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "constitutional-amendment"
START = "<!-- CONSTITUTIONAL_CONNECTED_START -->"
END = "<!-- CONSTITUTIONAL_CONNECTED_END -->"
BRIDGE_START = "/* CONSTITUTIONAL_CONNECTED_BRIDGE_START */"
BRIDGE_END = "/* CONSTITUTIONAL_CONNECTED_BRIDGE_END */"
CSS_HREF = "constitutional-connected.css?v=3"
JS_SRC = "constitutional-connected.js?v=1"
PAGE_JS_SRC = "constitutional-connected-page.js?v=1"
DATA_PATTERN = re.compile(r'(<script id="planet-data">window\.PLANET_DATA=)(.*?)(;</script>)', re.S)


def enabled(source: str) -> bool:
    return START in source


def planet_data(source: str) -> dict:
    match = DATA_PATTERN.search(source)
    if not match:
        raise ValueError("連動表示: PLANET_DATA が見つかりません")
    data = json.loads(match[2])
    if data.get("theme_id") != TOPIC:
        raise ValueError("連動表示はconstitutional-amendment専用です")
    return data


def background_data() -> dict:
    """`data/verification/constitutional-amendment-background.json`をそのまま返す。別コピーを持たない。"""
    path = ROOT / "data/verification/constitutional-amendment-background.json"
    return json.loads(path.read_text(encoding="utf-8"))


def content_index(data: dict) -> dict:
    """画面内の要素をIDで結ぶ。件数・原稿・確認日はPLANET_DATAに一元化する。

    claim_ids・shared_concern_idsはPLANET_DATA側（論点ごとに既に解決済み）をそのまま
    転記する。check_idsは背景データのissue_idsを使う。沈んだ大陸のうち、nearest_issue_id
    が未確定の2件は論点へ推測で割り当てず、資料3タブのテーマ全体一覧で保持する。
    timeline_idsは無タグのままなので現状は常に空配列になる（年表はページ全体の後段で
    日付切替表示する）。
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
    bridge = (ROOT / "scripts/templates/constitutional_connected_bridge.js").read_text(encoding="utf-8")
    return source.replace(anchor, BRIDGE_START + "\n" + bridge + "\n" + BRIDGE_END + "\n" + anchor, 1)


def apply(source: str, *, activate: bool = False, topic: str = TOPIC) -> str:
    """全更新経路の最後から呼ぶ。同じ入力では同じHTML、他テーマでは完全な無操作。"""
    if topic != TOPIC or not (activate or enabled(source)):
        return source
    from scripts.constitutional_connected_content import render_templates, START as CONTENT_START, END as CONTENT_END
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
        '<script id="constitutional-connected-data" type="application/json">' + payload + '</script>\n'
        f'<script src="{JS_SRC}" defer></script>\n'
        f'<script src="{PAGE_JS_SRC}" defer></script>\n' + END
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
    """接続表の一致・目印の対応・共有状態の配線と、論点ごとの読書面の接続を見る。"""
    if not enabled(source):
        return []
    from scripts.constitutional_connected_content import START as CONTENT_START, END as CONTENT_END

    problems = []
    soup = BeautifulSoup(source, "html.parser")
    try:
        data = planet_data(source)
        expected = content_index(data)
    except (ValueError, KeyError, TypeError) as exc:
        return [str(exc)]
    blocks = soup.select("#constitutional-connected-data")
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
        problems.append("立場ボタン（STANCE_GLANCE）の並びが立場データと一致しません")
    mode_ids = {m["id"] for m in data["modes"]} - {"all"}
    stance_keys = {s["key"] for s in data["stances"]}
    if mode_ids != stance_keys:
        problems.append("立場フィルター（#modes）と立場データが一致しません")

    def one(selector: str, label: str):
        nodes = soup.select(selector)
        if len(nodes) != 1:
            problems.append(f"読書面の入口が1つではありません: {label} ({len(nodes)})")
        return nodes[0] if len(nodes) == 1 else None

    for issue in data["issues"]:
        iid = issue["id"]
        connection = expected["issues"][iid]
        tpl = one("#constitutional-amendment-reading-" + iid, iid)
        if tpl is None:
            continue
        reading = BeautifulSoup(tpl.decode_contents(), "html.parser")
        for key, attr in (("claim_ids", "data-ca-claim"), ("source_only_ids", "data-ca-source-only"),
                          ("shared_concern_ids", "data-ca-concern"), ("timeline_ids", "data-ca-timeline"),
                          ("check_ids", "data-ca-check")):
            found = [el.get(attr) for el in reading.select("[" + attr + "]")]
            if found != connection[key]:
                problems.append(f"読書面の接続が一致しません: {iid} {key}")
        posts = reading.select("[data-ca-post-url]")
        if not posts and not iid.endswith("-other"):
            problems.append(f"読書面に投稿例がありません: {iid}")
    return problems
