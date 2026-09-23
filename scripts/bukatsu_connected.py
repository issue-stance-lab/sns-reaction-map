"""部活動の地域移行の連動表示（工程2: 土台／工程3: 読書面／工程4: 年表接続・深いリンク統一）。
候補の目印があるページだけに適用する。

既存の静的本文（STANCE_GLANCE・bukatsu-background・bukatsu-check・PLANET_SECTION）を
書き換えず、IDの接続表・バー↔山の状態共有・論点を選んだときの読書面（理由・投稿例・資料・
関係する年表）を足す。件数や原稿の別コピーを正典にせず、ページ内のPLANET_DATA・#issue-cards・
#fallbackと、`data/verification/bukatsu-chiiki-background.json`のtimelineを読む。
bukatsu-check(制度4項目)は今もissue_idsが無く接続対象外（オーナー確認は年表のみで完了、
工程1の内容確定書の開いたままの課題）。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "bukatsu-chiiki"
START = "<!-- BUKATSU_CONNECTED_START -->"
END = "<!-- BUKATSU_CONNECTED_END -->"
BRIDGE_START = "/* BUKATSU_CONNECTED_BRIDGE_START */"
BRIDGE_END = "/* BUKATSU_CONNECTED_BRIDGE_END */"
DATA_PATTERN = re.compile(r'(<script id="planet-data">window\.PLANET_DATA=)(.*?)(;</script>)', re.S)


def enabled(source: str) -> bool:
    return START in source


def planet_data(source: str) -> dict:
    match = DATA_PATTERN.search(source)
    if not match:
        raise ValueError("連動表示: PLANET_DATA が見つかりません")
    data = json.loads(match[2])
    if data.get("theme_id") != TOPIC:
        raise ValueError("連動表示はbukatsu-chiiki専用です")
    return data


def background_data() -> dict:
    """`data/verification/bukatsu-chiiki-background.json`をそのまま返す。

    工程4でオーナー確認のうえtimelineの6件全てにissue_idsを追加した（1件以上）。
    別コピーを持たず、この1ファイルだけを正典とする。
    """
    path = ROOT / "data/verification/bukatsu-chiiki-background.json"
    return json.loads(path.read_text(encoding="utf-8"))


def content_index(data: dict) -> dict:
    """画面内の要素をIDで結ぶ。件数・原稿・確認日はPLANET_DATAに一元化する。

    bukatsu-check（制度4項目）は今もissue_idsが無く接続しない（工程1の内容確定書の
    開いたままの課題、年表とは別扱い）。語られていない争点3件（sc-2/3/4）は
    nearest_issue_id未確定のまま。テーマ全体の一覧（既存の#ocean）に残し、
    特定の論点へは推測で割り当てない。
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
    for item in timeline:
        if not item.get("issue_ids") or set(item["issue_ids"]) - issue_ids:
            raise ValueError(f"連動表示: 年表の接続先の論点が不明です: {item['id']}")
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
            "timeline_ids": [t["id"] for t in timeline if iid in t["issue_ids"]],
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
    bridge = (ROOT / "scripts/templates/bukatsu_connected_bridge.js").read_text(encoding="utf-8")
    return source.replace(anchor, BRIDGE_START + "\n" + bridge + "\n" + BRIDGE_END + "\n" + anchor, 1)


def apply(source: str, *, activate: bool = False, topic: str = TOPIC) -> str:
    """全更新経路の最後から呼ぶ。同じ入力では同じHTML、他テーマでは完全な無操作。"""
    if topic != TOPIC or not (activate or enabled(source)):
        return source
    from scripts.bukatsu_connected_content import render_templates, START as CONTENT_START, END as CONTENT_END
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
        START + '\n<link rel="stylesheet" href="bukatsu-connected.css?v=3">\n'
        '<script id="bukatsu-connected-data" type="application/json">' + payload + '</script>\n'
        '<script src="bukatsu-connected.js?v=2" defer></script>\n'
        '<script src="bukatsu-connected-page.js?v=1" defer></script>\n' + END
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
    from scripts.bukatsu_connected_content import START as CONTENT_START, END as CONTENT_END

    problems = []
    soup = BeautifulSoup(source, "html.parser")
    try:
        data = planet_data(source)
        expected = content_index(data)
    except (ValueError, KeyError, TypeError) as exc:
        return [str(exc)]
    blocks = soup.select("#bukatsu-connected-data")
    if len(blocks) != 1 or json.loads(blocks[0].string or "null") != expected:
        problems.append("論点の接続表が現在の表示データと一致しません")
    if source.count(BRIDGE_START) != 1 or source.count(BRIDGE_END) != 1:
        problems.append("山と共通状態をつなぐ処理が1組ではありません")
    if source.count(CONTENT_START) != 1 or source.count(CONTENT_END) != 1:
        problems.append("読書面の目印が1組ではありません")
    if len(soup.select('link[href="bukatsu-connected.css?v=3"]')) != 1:
        problems.append("連動表示のCSSが1つではありません")
    for selector, label in (
        ('script[src="bukatsu-connected.js?v=2"][defer]', "ページ配置のJS"),
        ('script[src="bukatsu-connected-page.js?v=1"][defer]', "資料タブ・年表のJS"),
    ):
        if len(soup.select(selector)) != 1:
            problems.append(f"{label}が1つではありません")
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
        tpl = one("#bukatsu-reading-" + iid, iid)
        if tpl is None:
            continue
        reading = BeautifulSoup(tpl.decode_contents(), "html.parser")
        for key, attr in (("claim_ids", "data-bkt-claim"), ("source_only_ids", "data-bkt-source-only"),
                          ("shared_concern_ids", "data-bkt-concern"), ("timeline_ids", "data-bkt-timeline")):
            found = [el.get(attr) for el in reading.select("[" + attr + "]")]
            if found != connection[key]:
                problems.append(f"読書面の接続が一致しません: {iid} {key}")
        posts = reading.select("[data-bkt-post-url]")
        if issue["sub"]["status"] == "reread":
            for x in reading.select("[data-bkt-reason]"):
                if x.get("data-bkt-reason") not in {i["id"] for i in issue["sub"]["items"]}:
                    problems.append(f"読書面の理由分類が一致しません: {iid}")
        if not posts:
            problems.append(f"読書面に投稿例がありません: {iid}")
    return problems
