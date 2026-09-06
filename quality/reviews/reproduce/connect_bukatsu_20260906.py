#!/usr/bin/env python3
"""Convert existing bukatsu editorial records, without reclassifying or rereading posts."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

THEME = "bukatsu-chiiki"
TEACHER_REF = "c12c50b41b06040863edcd979c29d9f721e1c002"
BASE = "a3a6557"
TEACHER = "data/bukatsu-chiiki_teacher-reread.json"
COST = "data/bukatsu-chiiki_cost-receiver-reread.json"
PLAN = "data/bukatsu-chiiki_plan-child-reread.json"
ADAPTER = "data/verification/bukatsu-chiiki-plan-child-subissues.json"
CANONICAL = "social-samples/bukatsu-chiiki_hermes_classified.json"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo", type=Path)
    ap.add_argument("--private-dir", type=Path, required=True)
    a = ap.parse_args()
    root = a.repo.resolve()
    git = lambda ref, path: subprocess.check_output(["git", "-C", str(root), "show", f"{ref}:{path}"])
    raw = (root / CANONICAL).read_bytes()
    canonical = json.loads(raw)
    posts = {p["tweet_id"]: p for p in canonical if p["classification"].get("is_opinion") is True}
    assert len(posts) == 1139
    teacher_raw = git(TEACHER_REF, TEACHER)
    teacher = json.loads(teacher_raw)
    old_teacher = json.loads(git(BASE, TEACHER))
    current = {p["tweet_id"]: p for p in teacher["items"]}
    assert len(current) == len(teacher["items"]) == 323
    assert all(current[p["tweet_id"]] == p for p in old_teacher["items"])
    assert len(current.keys() - {p["tweet_id"] for p in old_teacher["items"]}) == 54
    assert (root / TEACHER).read_bytes() == teacher_raw, "Import the teacher source verbatim first"
    cost_raw, plan_raw = (root / COST).read_bytes(), (root / PLAN).read_bytes()
    assert cost_raw == git(BASE, COST) and plan_raw == git(BASE, PLAN)
    cost, plan = json.loads(cost_raw), json.loads(plan_raw)
    out = {
        "theme": THEME,
        "read_at": plan["checked_at"],
        "method": "既存のnote制作時本文再読を主論点別に変換。新規再読・区分変更なし。",
        "source": PLAN,
        "source_sha256": sha(plan_raw),
        "source_method": plan["method"],
        "curated_by": plan["curated_by"],
        "inherited_on": "2026-09-06",
        "body_version_note": "読了時の個別本文指紋は記録されていない。継承時の本文指紋は非公開台帳に保存。",
    }
    assert len({p["tweet_id"] for p in plan["records"]}) == len(plan["records"]) == 471
    assert Counter(p["reread_group"] for p in plan["records"]) == plan["counts"]
    for key, issue, expected in [("plan_side", "制度・移行プロセス", 256), ("child_side", "教育的意義・機会", 215)]:
        records = [p for p in plan["records"] if p["main_issue"] == issue]
        assert len(records) == expected
        counts = Counter(p["reread_group"] for p in records)
        out[key] = {
            "total": len(records),
            "buckets": {key: {"label": label, "count": counts[key]} for key, label in plan["groups"].items() if counts[key]},
            "items": [{"tweet_id": p["tweet_id"], "bucket": p["reread_group"]} for p in records],
        }
    sections = [
        ("教員の働き方", teacher, TEACHER, sha(teacher_raw)),
        ("費用・家庭負担", cost["cost_side"], COST, sha(cost_raw)),
        ("受け皿・指導者", cost["receiver_side"], COST, sha(cost_raw)),
        ("制度・移行プロセス", out["plan_side"], PLAN, sha(plan_raw)),
        ("教育的意義・機会", out["child_side"], PLAN, sha(plan_raw)),
    ]
    ledger = []
    for issue, section, source, source_hash in sections:
        assert Counter(p["bucket"] for p in section["items"]) == {k: v["count"] for k, v in section["buckets"].items()}
        for p in section["items"]:
            original = posts[p["tweet_id"]]
            assert original["classification"]["main_issue"] == issue
            if "stance" in p:
                assert original["classification"]["stance"] == p["stance"]
            ledger.append({"tweet_id": p["tweet_id"], "main_issue": issue, "bucket": p["bucket"],
                "source": source, "source_sha256": source_hash,
                "current_text_sha256": sha(original["text"].encode()),
                "historical_text_sha256": None,
                "historical_body_identity": "not_recorded; do not infer a new reading",
                "inherited_on": "2026-09-06"})
    connected = {p["tweet_id"] for p in ledger}
    assert len(connected) == len(ledger) == 966
    source_plan = {p["tweet_id"] for p in plan["records"]}
    assert source_plan == {p["tweet_id"] for p in out["plan_side"]["items"] + out["child_side"]["items"]}
    write(root / ADAPTER, out)
    private = {"theme": THEME, "canonical_source": CANONICAL, "canonical_sha256": sha(raw),
        "opinion_count": len(posts), "connected_count": len(connected),
        "records": ledger, "not_editorially_reread_ids": sorted(posts.keys() - connected),
        "note": "173件は編集再読記録なし。限定目的の本文確認5件を含む。新規再読はしていない。"}
    write(a.private_dir / "connection-ledger.json", private)
    assert (root / CANONICAL).read_bytes() == raw
    print(json.dumps({"connected": len(connected), "not_editorially_reread": len(posts.keys() - connected),
        "issues": {issue: len(section["items"]) for issue, section, _, _ in sections},
        "canonical_sha256": sha(raw), "adapter_sha256": sha((root / ADAPTER).read_bytes())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
