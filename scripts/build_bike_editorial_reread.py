#!/usr/bin/env python3
"""既存再読と、別工程で本文を読んで版を固定した追加記録を新ページへ接続する。

数値出所用の bike-blue-ticket-reread.json は自動分類を含むため入力にしない。
元の本文・分類は変更せず、IDと既存の編集区分だけを新ページ用にまとめる。
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from build_bike_process_sections import BUCKET_META
from public_registry_common import is_opinion_record

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = "social-samples/bike-blue-ticket_2d_classified.json"
OPPOSITION = "data/bike-blue-ticket_opposition_reread.json"
SUPPLEMENT = "data/bike-blue-ticket_editorial-supplement.json"
OUTPUT = "data/bike-blue-ticket_issues-reread.json"
ADDITIONAL = "data/bike-blue-ticket_editorial-reread-20260906.json"


def build(samples: list[dict], opposition: dict, supplement: dict, additional: dict | None = None) -> dict:
    by_id = {s["tweet_id"]: s for s in samples}
    if len(by_id) != len(samples):
        raise ValueError("正典に重複IDがあります")
    if supplement.get("review_kind") != "editorial_body_reread":
        raise ValueError("追加根拠は本文再読記録である必要があります")
    labels = {key: label for key, label, *_ in BUCKET_META}
    assignments: dict[str, tuple[str, str]] = {}
    groups = [("opposition", [
        {"tweet_id": tid, "bucket": bucket}
        for bucket, ids in opposition["buckets"].items() for tid in ids
    ]), ("supplement", supplement["items"])]
    if additional is not None:
        if additional.get("review_kind") != "editorial_body_reread":
            raise ValueError("追加の本文確認は編集再読の証拠である必要があります")
        extra_labels = additional["bucket_definitions"]
        if set(labels) & set(extra_labels):
            raise ValueError("追加再読の区分キーが既存区分と衝突しています")
        labels.update(extra_labels)
        groups.append(("additional", additional["items"]))
    additional_by_id = {r["tweet_id"]: r for r in additional["items"]} if additional else {}
    for source_id, items in groups:
        for item in items:
            if item.get("body_reviewed") is False or item.get("review_kind") == "automated_classification":
                raise ValueError("自動分類または本文未確認の項目を再読へ変換できません")
            tid, bucket = item["tweet_id"], item["bucket"]
            if tid in assignments:
                raise ValueError("本文再読根拠に重複IDがあります")
            if tid not in by_id or not is_opinion_record(by_id[tid]):
                raise ValueError("本文再読根拠に正典意見以外のIDがあります")
            if source_id == "additional":
                if item.get("body_reviewed") is not True or item.get("review_kind") != "editorial_body_reread":
                    raise ValueError("追加項目に明示的な本文再読証拠がありません")
                current = by_id[tid]
                if item.get("text_sha256") != hashlib.sha256(current["text"].encode()).hexdigest():
                    raise ValueError("追加再読時点から投稿本文が変わっています。再確認が必要です")
                if item.get("main_issue") != current["classification"]["main_issue"]:
                    raise ValueError("追加再読時点から主論点が変わっています。再接続の確認が必要です")
                if not item.get("read_at") or not item.get("reviewer") or not item.get("reason_sha256"):
                    raise ValueError("追加再読の日時・確認者・根拠の指紋がありません")
            if bucket not in labels:
                raise ValueError("本文再読根拠に未登録の区分があります")
            if source_id == "opposition" and bucket == "support":
                raise ValueError("反対再読の根拠に自動分類のsupport区分を混ぜられません")
            if source_id == "additional" and item.get("classification_concern") not in (
                "none", "not_opinion_candidate", "context_missing", "possibly_off_topic"):
                raise ValueError("追加再読の分類確認状態が不明です")
            assignments[tid] = (bucket, source_id)

    out = {
        "theme": "bike-blue-ticket",
        "scope": "過去に本文再読したIDを現行の全論点へ接続。自動分類からの読了推定はしない。",
        "read_at": f"{opposition['assigned_at']}（旧記録の日付） / {supplement['read_at']}（追加分の本文再読日）",
        "connected_at": "2026-09-06",
        "method": "本文再読の既存IDと編集区分を継承。現行正典のmain_issueを使って論点ごとに組み直した。既存部分は今回再読した扱いにしない。",
        "review_kind": "editorial_body_reread",
        "reviewer_type": "ai_or_unspecified_editorial",
        "date_caveat": "旧反対記録の日付は増分再読に追随していない。全件をその日に再読したとの保証はなく、接続日を再読日へ読み替えない。",
        "sources": {
            "opposition": {"file": OPPOSITION, "recorded_at": opposition["assigned_at"], "date_precision": "legacy_metadata_not_updated_for_all_increments", "reviewer_type": "unspecified_editorial"},
            "supplement": {"file": SUPPLEMENT, "read_at": supplement["read_at"], "source_ref": supplement["source_ref"], "reviewer_type": "editorial_ai"},
        },
        "population": {},
    }
    if additional is not None:
        out["read_at"] += f" / {additional['read_at']}（追加本文確認）"
        out["method"] += "追加の本文確認は別台帳の日付・本文指紋・確認者・根拠を検証して接続する。"
        out["sources"]["additional"] = {"file": ADDITIONAL, "read_at": additional["read_at"],
                                              "reviewer_type": additional["reviewer_type"],
                                              "target_sha256": additional["target_sha256"]}
    for issue in sorted({s["classification"]["main_issue"] for s in samples}):
        items = []
        for tid in sorted(assignments):
            if by_id[tid]["classification"]["main_issue"] != issue:
                continue
            bucket, source_id = assignments[tid]
            items.append({"tweet_id": tid, "bucket": bucket, "bucket_label": labels[bucket],
                          "review_kind": "editorial_body_reread", "body_reviewed": True,
                          "source_id": source_id})
            if source_id == "additional":
                items[-1]["classification_concern"] = additional_by_id[tid]["classification_concern"]
                items[-1]["text_sha256"] = additional_by_id[tid]["text_sha256"]
        counts = Counter(x["bucket"] for x in items)
        out["population"][issue] = len(items)
        out[issue] = {"buckets": {b: {"label": labels[b], "count": n} for b, n in sorted(counts.items())}, "items": items}
    return out


def main() -> None:
    inputs = {p: (ROOT / p).read_bytes() for p in (CANONICAL, OPPOSITION, SUPPLEMENT, ADDITIONAL)}
    data = build(*(json.loads(inputs[p]) for p in (CANONICAL, OPPOSITION, SUPPLEMENT, ADDITIONAL)))
    data["input_sha256"] = {p: hashlib.sha256(raw).hexdigest() for p, raw in inputs.items()}
    (ROOT / OUTPUT).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"本文再読の根拠 {sum(data['population'].values())} 件を接続しました")


if __name__ == "__main__":
    main()
