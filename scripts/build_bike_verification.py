#!/usr/bin/env python3
"""自転車の旧・新形式の判定を保持した、本文なしの正典検証データ。"""
import copy
import json
from pathlib import Path
from verification_data import make_verification_records

ROOT = Path(__file__).resolve().parents[1]


def build(records):
    normalized = copy.deepcopy(records)
    for row in normalized:
        classification = row.setdefault("classification", {})
        for key in ("is_opinion", "is_relevant"):
            if key not in classification and key in row:
                classification[key] = row[key]
    return make_verification_records(normalized)


if __name__ == "__main__":
    rows = json.loads((ROOT / "social-samples/bike-blue-ticket_2d_classified.json").read_text())
    safe = build(rows)
    output = ROOT / "data/verification/bike-blue-ticket.json"
    output.write_text("[\n" + ",\n".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in safe) + "\n]\n")
    print(f"自転車の検証データ {len(safe)}件を生成しました")
