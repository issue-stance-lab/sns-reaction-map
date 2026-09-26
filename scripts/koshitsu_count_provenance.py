"""皇室典範の連動読書面に出る再読・制度確認・資料側件数を照合する。"""

from collections import Counter
import json
from pathlib import Path

from bs4 import BeautifulSoup
import yaml


def verified_selectors(source: str, root: Path) -> dict[str, str]:
    if '<!-- KOSHITSU_CONNECTED_START -->' not in source:
        return {}
    soup = BeautifulSoup(source, "html.parser")
    result: dict[str, str] = {}

    def read(path: str):
        return json.loads((root / path).read_text(encoding="utf-8"))

    def verify(element_id: str, expected: str, evidence: str):
        nodes = soup.select("#" + element_id)
        if len(nodes) != 1 or nodes[0].get_text(types=None) != expected:
            raise ValueError(f"連動表示の数字が元記録と一致しません: {element_id} ← {evidence}")
        result["#" + element_id] = evidence

    cfg = yaml.safe_load((root / "configs/planet/koshitsu-tenpakai.yaml").read_text())
    public = read("data/public/themes/koshitsu-tenpakai.json")
    counts = {item["id"]: item["count"] for item in public["issues"]}
    reread_path = "data/koshitsu-tenpakai_issues-reread.json"
    reread = read(reread_path)
    for issue in cfg["issues"]:
        sub = cfg["sub_issues"].get(issue["key"])
        if not sub:
            continue
        buckets = reread
        for part in sub["path"]:
            buckets = buckets[part]
        records = reread
        for part in sub.get("items_path", sub["path"][:-1] + ["items"]):
            records = records[part]
        if sub.get("item_issue_field"):
            records = [record for record in records if record.get(sub["item_issue_field"]) == issue["key"]]
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
            element_id = f"aic-reason-count-{issue['id']}-{bucket_id}"
            verify(element_id, f"{item['count']:,}件", reread_path + " / " + "/".join(sub["path"]) + " / " + bucket_id)
            node = soup.select_one("#" + element_id)
            label = node.find_previous_sibling("span") if node else None
            if label is None or label.get_text(types=None) != item["label"]:
                raise ValueError("再読分類のラベルと元記録が一致しません: " + element_id)

    background_path = "data/verification/koshitsu-tenpakai-background.json"
    for item in read(background_path)["checklist"]["items"]:
        for issue in item.get("issue_ids", []):
            verify(
                f"aic-check-note-{issue}-{item['id']}",
                item["found"],
                background_path + " / checklist / " + item["id"],
            )

    public_path = "data/public/themes/koshitsu-tenpakai.json"
    for item in public["ocean_layer"]["veins"]:
        sides = " ／ ".join(s["stance_label"] + " " + str(s["post_count"]) + "件" for s in item["sides"])
        text = f"確認した投稿例: {sides}。確認日 {item['checked_on']}"
        for issue in item.get("issue_ids", []):
            verify(f"aic-concern-count-{issue}-{item['id']}", text, public_path + " / " + item["id"])

    for item in public["ocean_layer"]["sunk_continents"]:
        scope = "確認時の" if item.get("base_stale") else "皇室典範テーマで確認した"
        finding = (
            f'{scope}意見{item["sns_base"]:,}件では、この記述に触れた投稿は見つかりませんでした。'
            if item["sns_count"] == 0
            else f'{scope}意見{item["sns_base"]:,}件のうち、この記述に触れた投稿は{item["sns_count"]:,}件でした。'
        )
        verify(
            "aic-source-count-" + item["id"],
            finding + " 確認日 " + item["checked_on"],
            public_path + " / " + item["id"],
        )
        verify("aic-source-note-" + item["id"], item["sns_note"], public_path + " / " + item["id"])
    return result
