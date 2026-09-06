#!/usr/bin/env python3
"""既存の高齢者再読を現在本文・設定と照合する。新規の再読は行わない。"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import yaml

THEME = "elderly-license-revocation"
CANONICAL = "social-samples/elderly-license_2d_classified.json"
REREAD = "data/elderly-license_issues-reread.json"
CONFIG = f"configs/planet/{THEME}.yaml"
SNAPSHOT = "5da3a48"


def sha(value):
    return hashlib.sha256(value).hexdigest()


def run(root, private_output):
    sys.path.insert(0, str(root / "scripts"))
    from public_registry_common import source_sha256
    raw = (root / CANONICAL).read_bytes()
    current = {p["tweet_id"]: p for p in json.loads(raw)}
    snapshot_raw = subprocess.check_output(["git", "show", f"{SNAPSHOT}:{CANONICAL}"], cwd=root)
    old = {p["tweet_id"]: p for p in json.loads(snapshot_raw)}
    reread_raw = (root / REREAD).read_bytes()
    reread = json.loads(reread_raw)
    config_raw = (root / CONFIG).read_bytes()
    cfg = yaml.safe_load(config_raw)
    public = json.loads((root / f"data/public/themes/{THEME}.json").read_text())
    opinion = {pid for pid, p in current.items() if p["classification"]["is_opinion"] and p["classification"]["is_relevant"]}
    rows = reread["items"]
    ids = {r["tweet_id"] for r in rows}
    assert len(rows) == len(ids) == 250
    assert ids <= opinion
    assert len(current) == 506 and len(opinion) == public["opinion_count"] == 353
    assert public["source_sha256"] == source_sha256(list(current.values()))
    assert set(cfg["sub_issues"]) == set(reread["buckets"])
    by_issue = []
    private_rows = []
    for issue, sc in cfg["sub_issues"].items():
        assert sc["file"] == REREAD
        assert sc["path"] == ["buckets", issue]
        assert sc["items_path"] == ["items"] and sc["item_issue_field"] == "main_issue"
        selected = [r for r in rows if r["main_issue"] == issue]
        read_ids = {r["tweet_id"] for r in selected}
        issue_ids = {pid for pid in opinion if current[pid]["classification"]["main_issue"] == issue}
        assert read_ids == issue_ids
        counts = Counter(r["bucket"] for r in selected)
        assert dict(counts) == {key: value["count"] for key, value in reread["buckets"][issue].items()}
        config_issue = next(i for i in cfg["issues"] if i["key"] == issue)
        public_issue = next(i for i in public["issues"] if i["id"] == config_issue["id"])
        assert public_issue["count"] == len(selected)
        for row in selected:
            pid = row["tweet_id"]
            assert old[pid]["text"] == current[pid]["text"]
            assert current[pid]["classification"]["main_issue"] == row["main_issue"]
            assert current[pid]["classification"]["stance"] == row["stance"]
            private_rows.append({"post_id": pid, "body_sha256": sha(current[pid]["text"].encode()),
                                 "issue": issue, "bucket": row["bucket"],
                                 "read_at_recorded": reread["read_at"],
                                 "reader_type": "ai", "historical_body_snapshot": SNAPSHOT})
        by_issue.append({"issue": issue, "connected_editorial_count": len(selected),
                         "unread_in_issue": 0, "bucket_count": len(counts),
                         "bucket_counts": dict(sorted(counts.items()))})
    # Existing vote storage is 6 issue positions. Analysis labels differ for the last 3.
    assert cfg["vote_issue_order"] == ["義務化・事故防止", "地方の足・移動権", "適性検査強化", "代替交通整備", "自主返納支援", "その他"]
    summary = {"theme": THEME, "checked_on": "2026-09-06", "new_rereading_performed": False,
               "canonical_sha256": sha(raw), "reread_sha256": sha(reread_raw),
               "config_sha256": sha(config_raw), "historical_body_snapshot": SNAPSHOT,
               "historical_body_snapshot_sha256": sha(snapshot_raw),
               "collected": len(current), "opinions": len(opinion), "connected_editorial": len(ids),
               "remaining_without_editorial_reread": len(opinion - ids),
               "body_version_matched": len(private_rows), "by_issue": by_issue,
               "qualification": "Existing AI editorial evidence, matched to a historical canonical snapshot; no new reading and no independent proof of original reading.",
               "not_reclassified": {"existing_unclear_or_unrelated_buckets": 31},
               "public_readiness": "Data connection only; editorial_summary and ocean_layer remain not_started; parent must verify template, votes, and publication gate."}
    private_output.mkdir(parents=True, exist_ok=True)
    destination = private_output / "elderly-connection-evidence.json"
    if destination.exists():
        raise SystemExit(f"Refusing to overwrite {destination}")
    destination.write_text(json.dumps({"summary": summary, "posts": private_rows}, ensure_ascii=False, indent=2) + "\n")
    (private_output / "elderly-connection-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root.resolve(), args.private_output.resolve()), ensure_ascii=False, indent=2))
