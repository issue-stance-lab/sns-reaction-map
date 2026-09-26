"""辺野古連動読書面に表示する再読・資料側の数字を正典と照合する。"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from bs4 import BeautifulSoup

from scripts.henoko_connected import START, content_index, planet_data


def verified_selectors(source: str, root: Path) -> dict[str, str]:
    if START not in source:
        return {}
    soup = BeautifulSoup(source, "html.parser")

    def read(path: str):
        return json.loads((root / path).read_text(encoding="utf-8"))

    result: dict[str, str] = {}

    def verify(element_id: str, expected: str, evidence: str, *, repeated: bool = False) -> None:
        nodes = soup.select("#" + element_id)
        if not nodes or any(node.get_text(types=None) != expected for node in nodes):
            raise ValueError(f"辺野古連動表示の正典照合に失敗しました: {element_id} ← {evidence}")
        if not repeated and len(nodes) != 1:
            raise ValueError(f"辺野古連動表示のIDが重複しています: {element_id} ← {evidence}")
        result["#" + element_id] = evidence

    data = planet_data(source)
    index = content_index(data)
    public = read("data/public/themes/henoko-student-accident.json")
    counts = {item["id"]: item["count"] for item in public["issues"]}
    reread = read("data/henoko-student-accident_issues-reread.json")
    records = reread["items"]
    buckets = reread["buckets"]
    for issue in data["issues"]:
        iid = issue["id"]
        label = issue["label"]
        issue_records = [item for item in records if item.get("main_issue") == label]
        actual = Counter(item["bucket"] for item in issue_records)
        expected_buckets = buckets.get(label, {})
        if set(actual) - set(expected_buckets):
            raise ValueError(f"再読分類に未登録の理由があります: {iid}")
        if any(actual[key] != bucket["count"] for key, bucket in expected_buckets.items()):
            raise ValueError(f"再読分類の件数と投稿記録が一致しません: {iid}")
        gap = counts[iid] - len(issue_records)
        if gap < 0:
            raise ValueError(f"再読記録が論点の母数を超えています: {iid}")
        items = list(expected_buckets.items())
        if gap:
            items.append(("__unread__", {"label": "まだ読み直していない分", "count": gap}))
        for bucket_id, item in items:
            verify(
                f"henoko-reason-count-{iid}-{bucket_id}",
                f"{item['count']}件",
                f"data/henoko-student-accident_issues-reread.json / {label} / {bucket_id}",
            )
            label_node = soup.select_one(f"#henoko-reason-count-{iid}-{bucket_id}")
            if not label_node or label_node.find_previous("span", class_="henoko-reason-label").get_text(types=None) != item["label"]:
                raise ValueError(f"再読分類のラベルと正典が一致しません: {iid} / {bucket_id}")
        if gap:
            verify(
                f"henoko-reason-coverage-{iid}",
                f"本文を読み直した分類は{issue['sub'].get('reread_count', 0)}件。未読分{gap}件は別枠で表示しています。",
                f"PLANET_DATA / issues / {iid} / sub",
            )

    background_path = "data/verification/henoko-student-accident-background.json"
    background = read(background_path)
    for item in background["checklist"]["items"]:
        verify(f"henoko-check-note-{item['id']}", item["found"], f"{background_path} / checklist / {item['id']}", repeated=True)

    for item in data["ocean"].get("sunk_continents", []):
        verify(f"henoko-source-topic-{item['id']}", item["topic"], f"PLANET_DATA / ocean / {item['id']}")
        verify(f"henoko-source-life-{item['id']}", item["life_impact"], f"PLANET_DATA / ocean / {item['id']}")
        verify(f"henoko-source-note-{item['id']}", item["sns_note"] + " 確認日 " + item["checked_on"], f"PLANET_DATA / ocean / {item['id']}")
    return result
