"""自転車青切符の連動表示に出る再読・制度確認・資料側件数を照合する。

一般の立場・論点集計とは母集団が違うため、値の許可リストには追加しない。
元記録と一致した要素だけを、数字検査へ根拠付きで返す。
"""

from collections import Counter
import json
from pathlib import Path

from bs4 import BeautifulSoup
import yaml

from scripts.bike_blue_ticket_connected import START as BIKE_CONNECTED_START


def verified_selectors(source: str, root: Path) -> dict[str, str]:
    if BIKE_CONNECTED_START not in source:
        return {}
    soup = BeautifulSoup(source, "html.parser")
    result: dict[str, str] = {}

    def read(path: str):
        return json.loads((root / path).read_text(encoding="utf-8"))

    def verify(element_id: str, expected: str, evidence: str, *, repeated: bool = False):
        nodes = soup.select("#" + element_id)
        if not nodes or any(node.get_text(types=None) != expected for node in nodes):
            raise ValueError(f"連動表示の数字が元記録と一致しません: {element_id} ← {evidence}")
        if not repeated and len(nodes) != 1:
            raise ValueError(f"連動表示の数字IDが重複しています: {element_id} ← {evidence}")
        result["#" + element_id] = evidence

    cfg = yaml.safe_load((root / "configs/planet/bike-blue-ticket.yaml").read_text())
    public = read("data/public/themes/bike-blue-ticket.json")
    counts = {item["id"]: item["count"] for item in public["issues"]}
    for issue in cfg["issues"]:
        sub = cfg["sub_issues"].get(issue["key"])
        if not sub:
            continue
        raw = read(sub["file"])
        buckets = raw
        for part in sub["path"]:
            buckets = buckets[part]
        records = raw
        for part in sub.get("items_path", sub["path"][:-1] + ["items"]):
            records = records[part]
        actual = Counter(record["bucket"] for record in records)
        if set(actual) - set(buckets) or any(actual[key] != bucket["count"] for key, bucket in buckets.items()):
            raise ValueError("再読分類の件数と投稿記録が一致しません: " + issue["id"])
        items = {key: {"label": bucket["label"], "count": actual[key]} for key, bucket in buckets.items()}
        gap = counts[issue["id"]] - len(records)
        if gap < 0:
            raise ValueError("再読記録が論点の母数を超えています: " + issue["id"])
        if gap:
            items["__unread__"] = {"label": "まだ読み直していない分", "count": gap}
        for bucket_id, item in items.items():
            element_id = f"bike-reason-count-{issue['id']}-{bucket_id}"
            verify(
                element_id,
                f"{item['count']:,}件",
                sub["file"] + " / " + "/".join(sub["path"]) + " / " + bucket_id,
            )
            node = soup.select_one("#" + element_id)
            label = node.find_previous_sibling("span") if node else None
            if label is None or label.get_text(types=None) != item["label"]:
                raise ValueError("再読分類のラベルと元記録が一致しません: " + element_id)

    background_path = "data/verification/bike-blue-ticket-background.json"
    for item in read(background_path)["checklist"]["items"]:
        verify(
            "bike-check-note-" + item["id"],
            item["found"],
            background_path + " / checklist / " + item["id"],
            repeated=True,
        )

    sunk_path = "data/verification/bike-blue-ticket-sunk-continents.json"
    for item in read(sunk_path)["items"]:
        verify("bike-source-topic-" + item["id"], item["topic"], sunk_path + " / " + item["id"])
        verify("bike-source-life-" + item["id"], item["life_impact"], sunk_path + " / " + item["id"])
        verify("bike-source-note-" + item["id"], item["sns_note"] + " 確認日 " + item["checked_on"], sunk_path + " / " + item["id"])
        if item.get("issue_bucket"):
            verify("bike-source-note-copy-" + item["id"], item["sns_note"], sunk_path + " / " + item["id"])
    return result
