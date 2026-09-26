"""高齢者免許返納の連動表示に追加した数字を正典へ照合する。"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from bs4 import BeautifulSoup

from scripts.elderly_connected import START as ELDERLY_CONNECTED_START


def verified_selectors(source: str, root: Path) -> dict[str, str]:
    if ELDERLY_CONNECTED_START not in source:
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
        return nodes[0]

    reread_path = "data/elderly-license_issues-reread.json"
    reread = read(reread_path)
    public_path = "data/public/themes/elderly-license-revocation.json"
    public = read(public_path)
    counts = {issue["label"]: issue for issue in public["issues"]}

    for issue_label, buckets in reread["buckets"].items():
        if issue_label not in counts:
            raise ValueError("再読分類の論点が公開JSONにありません: " + issue_label)
        issue = counts[issue_label]
        actual = Counter(item["bucket"] for item in reread["items"] if item.get("main_issue") == issue_label)
        if set(actual) - set(buckets) or any(actual[key] != bucket["count"] for key, bucket in buckets.items()):
            raise ValueError("再読分類の件数と投稿記録が一致しません: " + issue["id"])
        items = {key: {"label": bucket["label"], "count": actual[key]} for key, bucket in buckets.items()}
        gap = issue["count"] - len([item for item in reread["items"] if item.get("main_issue") == issue_label])
        if gap < 0:
            raise ValueError("再読記録が論点の母数を超えています: " + issue["id"])
        if gap:
            items["__unread__"] = {"label": "まだ読み直していない分", "count": gap}
        for bucket_id, item in items.items():
            element_id = f"elc-reason-count-{issue['id']}-{bucket_id}"
            node = verify(element_id, f"{item['count']:,}件", reread_path + " / " + issue_label + " / " + bucket_id)
            label = node.find_previous_sibling("span")
            if label is None or label.get_text(types=None) != item["label"]:
                raise ValueError("再読分類のラベルと元記録が一致しません: " + element_id)

    claims_path = public_path + " / claim_verification / claims"
    for claim in public["claim_verification"]["claims"]:
        for issue_id in claim.get("issue_ids", []):
            verify(
                "elc-claim-finding-" + issue_id + "-" + claim["id"],
                claim["finding"],
                claims_path + " / " + claim["id"] + " / " + issue_id,
            )
    return result
