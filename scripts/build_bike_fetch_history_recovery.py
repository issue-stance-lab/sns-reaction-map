#!/usr/bin/env python3
"""自転車青切符の欠けた取得履歴を、本文を出さずに照合・記録する。

過去ファイルに残る観測日時は、現在の正典へ推測で書き戻さない。代わりに投稿IDと
本文のハッシュで結び、同じ投稿をいつ観測していたかを検証用サマリへ残す。

    python3 scripts/build_bike_fetch_history_recovery.py
    python3 scripts/build_bike_fetch_history_recovery.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from .verification_data import record_id_hash
except ImportError:
    from verification_data import record_id_hash  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "social-samples/bike-blue-ticket_2d_classified.json"
OUTPUT = ROOT / "data/verification/bike-blue-ticket-fetch-history-recovery.json"

# 取得日時を実際に持つ旧保存回だけを固定して照合する。globで拾うと、将来の生成物や
# 一時ファイルが証拠に混ざるため、追加する際は意図を確認してこの一覧を更新する。
HISTORY_FILES = (
    "social-samples/bike-blue-ticket_classified.json",
    "social-samples/bike-blue-ticket_samples.json",
    "social-samples/bike-blue-ticket_samples_merged.json",
    "social-samples/bike-blue-ticket_samples_refresh_20260712.json",
    "social-samples/bike-blue-ticket_samples_refresh_20260726.json",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def text_sha256(record: dict[str, Any]) -> str:
    return sha256_bytes(str(record.get("text") or "").encode("utf-8"))


def id_set_sha256(records: list[dict[str, Any]]) -> str:
    """本文も投稿IDも出さずに、対象集合が同じかを確認できる指紋。"""
    values = sorted(record_id_hash(record) for record in records)
    return sha256_bytes("\n".join(values).encode("utf-8"))


def read_rows(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise SystemExit(f"JSON配列が必要です: {path}")
    return value


def build(canonical_path: Path = CANONICAL) -> dict[str, Any]:
    canonical_bytes = canonical_path.read_bytes()
    canonical = read_rows(canonical_path)
    missing = [row for row in canonical if not row.get("fetched_at")]
    missing_by_id = {str(row.get("tweet_id") or ""): row for row in missing}
    if "" in missing_by_id or len(missing_by_id) != len(missing):
        raise SystemExit("取得日時が欠けた正典に、tweet_idの欠損または重複があります")

    source_sha256: dict[str, str] = {}
    evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for relative in HISTORY_FILES:
        path = ROOT / relative
        if not path.is_file():
            raise SystemExit(f"照合元の旧保存回がありません: {relative}")
        source_sha256[relative] = sha256_bytes(path.read_bytes())
        for row in read_rows(path):
            tweet_id = str(row.get("tweet_id") or "")
            observed_at = row.get("fetched_at")
            if tweet_id not in missing_by_id or not isinstance(observed_at, str) or not observed_at:
                continue
            current = missing_by_id[tweet_id]
            evidence[tweet_id].append({
                "fetched_at": observed_at,
                "source_file": relative,
                "exact_text_match": text_sha256(row) == text_sha256(current),
            })

    records: list[dict[str, Any]] = []
    for tweet_id, current in sorted(missing_by_id.items()):
        observations_by_time: dict[str, dict[str, Any]] = {}
        for item in evidence[tweet_id]:
            existing = observations_by_time.setdefault(
                item["fetched_at"],
                {"fetched_at": item["fetched_at"], "source_files": [], "exact_text_match": False},
            )
            existing["source_files"].append(item["source_file"])
            existing["exact_text_match"] = existing["exact_text_match"] or item["exact_text_match"]
        observations = sorted(observations_by_time.values(), key=lambda item: item["fetched_at"])
        for item in observations:
            item["source_files"].sort()
        exact = any(item["exact_text_match"] for item in observations)
        records.append({
            "record_id_hash": record_id_hash(current),
            "canonical_text_sha256": text_sha256(current),
            # 同一IDだけなら本文が後から変わっている可能性を除外できない。正典への
            # 書き戻しに使わず、再読時点に存在したかを人が確認する候補として残す。
            "status": "confirmed_observation" if exact else "candidate_id_only",
            "observations": observations,
        })

    confirmed = sum(row["status"] == "confirmed_observation" for row in records)
    candidate = sum(row["status"] == "candidate_id_only" for row in records)
    unknown = sum(not row["observations"] for row in records)
    return {
        "schema": 1,
        "topic": "bike-blue-ticket",
        "purpose": "欠損したfetched_atの証拠付き復元候補。正典の値を推測で更新しない。",
        "canonical": {
            "path": str(canonical_path.relative_to(ROOT)),
            "sha256": sha256_bytes(canonical_bytes),
            "records": len(canonical),
            "missing_fetched_at": len(missing),
            "record_id_set_sha256": id_set_sha256(canonical),
            "missing_fetched_at_id_set_sha256": id_set_sha256(missing),
        },
        "source_files_sha256": source_sha256,
        "summary": {
            "confirmed_observation": confirmed,
            "candidate_id_only": candidate,
            "unknown": unknown,
            "multiple_observation_dates": sum(len(row["observations"]) > 1 for row in records),
        },
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="既存の検証サマリとの差だけを確認する")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    rendered = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit(f"取得履歴の検証サマリが最新ではありません: {args.output}")
        print(f"ok: {args.output}")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    data = json.loads(rendered)
    summary = data["summary"]
    print(
        f"wrote: {args.output}  欠損{data['canonical']['missing_fetched_at']}件 / "
        f"本文一致{summary['confirmed_observation']}件 / IDのみ候補{summary['candidate_id_only']}件 / "
        f"不明{summary['unknown']}件"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
