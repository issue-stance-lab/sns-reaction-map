"""副首都の連動表示に出る再読・制度確認・一次資料側件数を照合する。"""
from collections import Counter
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
import yaml

from scripts.fukushuto_connected import START as FUKUSHUTO_CONNECTED_START


def verified_selectors(source: str, root: Path) -> dict[str, str]:
    if FUKUSHUTO_CONNECTED_START not in source:
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

    cfg = yaml.safe_load((root / "configs/planet/fukushuto.yaml").read_text())
    public = read("data/public/themes/fukushuto.json")
    counts = {item["id"]: item["count"] for item in public["issues"]}
    for issue in cfg["issues"]:
        sub = cfg.get("sub_issues", {}).get(issue["key"])
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
        gap = counts[issue["id"]] - len(records)
        if gap < 0:
            raise ValueError("再読記録が論点の母数を超えています: " + issue["id"])
        items = {key: {"label": bucket["label"], "count": actual[key]} for key, bucket in buckets.items()}
        if gap:
            items["__unread__"] = {"label": "まだ読み直していない分", "count": gap}
        for bucket_id, item in items.items():
            verify(
                f"fuk-reason-count-{issue['id']}-{bucket_id}",
                f"{item['count']:,}件",
                sub["file"] + " / " + "/".join(sub["path"]) + " / " + bucket_id,
            )
            node = soup.select_one("#fuk-reason-count-" + issue["id"] + "-" + bucket_id)
            label = node.find_previous_sibling("span") if node else None
            if label is None or label.get_text(types=None) != item["label"]:
                raise ValueError("再読分類のラベルと元記録が一致しません: " + issue["id"] + " / " + bucket_id)

    background_path = "data/verification/fukushuto-background.json"
    for item in read(background_path)["checklist"]["items"]:
        verify("fuk-check-note-" + item["id"], item["found"], background_path + " / checklist / " + item["id"], repeated=True)

    # 副首都の一次資料4件はPLANET_DATAへ統合されており、同じ正典を直接照合する。
    match = re.search(r'<script id="planet-data">window\.PLANET_DATA=(.*?);</script>', source, re.S)
    if not match:
        raise ValueError("PLANET_DATAが見つかりません")
    page_data = json.loads(match.group(1))
    for item in page_data["ocean"]["sunk_continents"]:
        verify("fuk-source-topic-" + item["id"], item["topic"], "PLANET_DATA / ocean / " + item["id"])
        verify("fuk-source-life-" + item["id"], item["life_impact"], "PLANET_DATA / ocean / " + item["id"])
        verify("fuk-source-note-" + item["id"], item["sns_note"] + " 確認日 " + item["checked_on"], "PLANET_DATA / ocean / " + item["id"])
        verify("fuk-source-note-copy-" + item["id"], item["sns_note"], "PLANET_DATA / ocean / " + item["id"])
    return result
