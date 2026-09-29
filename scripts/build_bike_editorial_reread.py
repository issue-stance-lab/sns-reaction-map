#!/usr/bin/env python3
"""既存再読と、別工程で本文を読んで版を固定した追加記録を新ページへ接続する。

数値出所用の bike-blue-ticket-reread.json は自動分類を含むため入力にしない。
元の本文・分類は変更せず、IDと既存の編集区分だけを新ページ用にまとめる。
"""
from __future__ import annotations

import argparse
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
UPDATES = "data/bike-blue-ticket_editorial-updates"


def build(samples: list[dict], opposition: dict, supplement: dict, additional: dict | None = None) -> dict:
    by_id = {s["tweet_id"]: s for s in samples}
    if len(by_id) != len(samples):
        raise ValueError("正典に重複IDがあります")
    if supplement.get("review_kind") != "editorial_body_reread":
        raise ValueError("追加根拠は本文再読記録である必要があります")
    labels = {key: label for key, label, *_ in BUCKET_META}
    assignments: dict[str, tuple[str, str]] = {}
    excluded: list[dict] = []
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
            if tid not in by_id:
                raise ValueError("本文再読根拠に正典に無いIDがあります")
            if not is_opinion_record(by_id[tid]):
                # 意見から外した投稿。ただし「なぜ外したか」が正典に記録されている
                # ときだけ受け入れる。理由の無い除外は、正典が黙って変わった合図
                # なので今までどおり止める。
                if not by_id[tid].get("opinion_exclusion_reason"):
                    raise ValueError("本文再読根拠に正典意見以外のIDがあります"
                                     "（意見から外すなら opinion_exclusion_reason を正典へ記録する）")
                excluded.append({
                    "tweet_id": tid, "bucket": bucket, "source_id": source_id,
                    "main_issue_at_exclusion": by_id[tid]["classification"]["main_issue"],
                    "exclusion_reason": by_id[tid]["opinion_exclusion_reason"],
                    "decided_at": by_id[tid].get("opinion_exclusion_decided_at", ""),
                })
                continue
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
    if excluded:
        out["excluded_from_opinions"] = {
            "decided_at": "2026-09-06",
            "decided_by": "CEO（オーナー）承認",
            "reason": "意見でない投稿（ニュース共有・制度の告知・話題の例示・文脈不足）を意見の母数から外す。"
                      "自転車だけが全件を意見扱いにしており、他テーマと数え方が違っていた。",
            "note": "本文を読んだ記録として保持する。意見へ戻す判断をした場合はここから復元できる。",
            "count": len(excluded),
            "breakdown": dict(Counter(x["exclusion_reason"] for x in excluded)),
            "items": sorted(excluded, key=lambda x: x["tweet_id"]),
        }
    return out


def apply_review_updates(data: dict, samples: list[dict], updates: dict[str, dict]) -> dict:
    """定期収集の確認記録を接続し、次の再生成で追加分が消えるのを防ぐ。"""
    by_id = {str(row["tweet_id"]): row for row in samples}
    seen = {str(item["tweet_id"]) for issue in data["population"] for item in data[issue]["items"]}
    seen.update(str(item["tweet_id"]) for item in data.get("excluded_from_opinions", {}).get("items", []))
    existing_items = {
        str(item["tweet_id"]): (issue, item)
        for issue in data["population"]
        for item in data[issue]["items"]
    }
    updated_ids: set[str] = set()
    for source, update in sorted(updates.items()):
        if (update.get("review_kind") != "editorial_body_reread" or
                not update.get("finalized_by") or not update.get("read_at")):
            raise ValueError("定期更新には本文確認・最終確認者・読了日時が必要です")
        pending_ids = [str(item["tweet_id"]) for item in update["items"]
                       if item.get("decision") != "hold"]
        present_ids = [tid for tid in pending_ids if tid in by_id]
        if pending_ids and not present_ids:
            # A review record is staged before publication. Do not let a pending wave
            # break regeneration from the still-current canonical sample.
            continue
        if len(present_ids) != len(pending_ids):
            raise ValueError("定期更新の採用・除外投稿が正典へ一部だけ反映されています")
        excluded = []
        held = []
        overlap_ids = []
        bucket_reassignments = []
        for item in update["items"]:
            if (item.get("body_reviewed") is not True or
                    item.get("review_kind") != "editorial_body_reread" or
                    item.get("independently_checked") is not True or
                    not item.get("reviewer") or not item.get("read_at") or
                    not item.get("reason") or
                    item.get("reason_sha256") != hashlib.sha256(item["reason"].encode()).hexdigest()):
                raise ValueError("定期更新の各投稿に本文確認・独立確認・個別根拠の記録が必要です")
            tid = str(item["tweet_id"])
            if item["decision"] == "hold":
                if tid in seen:
                    raise ValueError("保留投稿のIDが既存記録または更新回と重複しています")
                seen.add(tid)
                if tid in by_id:
                    raise ValueError("保留投稿を正式候補へ混ぜることはできません")
                held.append(tid)
                continue
            row = by_id.get(tid)
            if (row is None or item.get("text_sha256") != hashlib.sha256(row["text"].encode()).hexdigest()
                    or item.get("main_issue") != row["classification"]["main_issue"]
                    or item.get("stance") != row["classification"]["stance"] or not item.get("reason")):
                raise ValueError("定期更新の本文・論点・賛否・確認根拠が候補と一致しません")
            if item["decision"] == "exclude":
                if is_opinion_record(row) or not row.get("opinion_exclusion_reason"):
                    raise ValueError("除外記録と候補の意見判定・理由が一致しません")
                if tid in seen:
                    raise ValueError("定期更新の本文確認IDが既存記録または更新回と重複しています")
                excluded.append(tid)
                seen.add(tid)
                updated_ids.add(tid)
                continue
            if item["decision"] != "adopt" or not is_opinion_record(row):
                raise ValueError("定期更新の採用状態が不正です")
            if (item.get("intensity") not in ("low", "medium", "high") or
                    item["intensity"] != row["classification"].get("intensity")):
                raise ValueError("定期更新の表現強度の確認が候補と一致しません")
            group = data[item["main_issue"]]
            bucket = item["bucket"]
            if bucket not in group["buckets"]:
                raise ValueError("定期更新の区分が既存の論点内区分にありません")
            if tid in seen:
                prior = existing_items.get(tid)
                if (tid in updated_ids or prior is None or prior[1].get("source_id") != "opposition"
                        or prior[0] != item["main_issue"]):
                    raise ValueError("定期更新の本文確認IDが既存記録または更新回と重複しています")
                previous_bucket = prior[1]["bucket"]
                prior[1].update({
                    "bucket": bucket,
                    "bucket_label": group["buckets"][bucket]["label"],
                    "source_id": source,
                    "text_sha256": item["text_sha256"],
                    "classification_concern": item.get("classification_concern", "none"),
                })
                overlap_ids.append(tid)
                if previous_bucket != bucket:
                    bucket_reassignments.append({"tweet_id": tid, "from": previous_bucket, "to": bucket})
                updated_ids.add(tid)
                continue
            seen.add(tid)
            updated_ids.add(tid)
            group["items"].append({"tweet_id": tid, "bucket": bucket,
                "bucket_label": group["buckets"][bucket]["label"],
                "review_kind": "editorial_body_reread", "body_reviewed": True,
                "source_id": source, "text_sha256": item["text_sha256"],
                "classification_concern": "none"})
        data["sources"][source] = {"file": source, "read_at": update["read_at"],
                                   "reviewer_type": "editorial_ai"}
        data.setdefault("update_dispositions", {})[source] = {
            "excluded_ids": excluded, "held_ids": held,
            "overlap_ids": overlap_ids, "bucket_reassignments": bucket_reassignments,
            "note": "過去の除外承認とは別の今回の本文確認。保留は原本候補の外に保持。"}
    for issue in data["population"]:
        group = data[issue]
        group["items"].sort(key=lambda item: str(item["tweet_id"]))
        counts = Counter(item["bucket"] for item in group["items"])
        for key, bucket in group["buckets"].items():
            bucket["count"] = counts[key]
        data["population"][issue] = len(group["items"])
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="候補の累積正典（省略時は THEMES.yaml の正典）")
    parser.add_argument("--output", type=Path, help="書き出し先（省略時は data/bike-blue-ticket_issues-reread.json）")
    args = parser.parse_args()
    source = args.input or ROOT / CANONICAL
    output = args.output or ROOT / OUTPUT
    if not source.is_absolute():
        source = ROOT / source
    if not output.is_absolute():
        output = ROOT / output
    source_label = source.relative_to(ROOT).as_posix()
    inputs = {p: (ROOT / p).read_bytes() for p in (OPPOSITION, SUPPLEMENT, ADDITIONAL)}
    inputs[source_label] = source.read_bytes()
    samples, opposition, supplement, additional = (
        json.loads(inputs[source_label]), json.loads(inputs[OPPOSITION]),
        json.loads(inputs[SUPPLEMENT]), json.loads(inputs[ADDITIONAL]),
    )
    data = build(samples, opposition, supplement, additional)
    updates = {path.relative_to(ROOT).as_posix(): path.read_bytes()
               for path in sorted((ROOT / UPDATES).glob("*.json"))}
    if updates:
        data = apply_review_updates(data, samples,
                                    {path: json.loads(raw) for path, raw in updates.items()})
        applied_updates = set(data.get("update_dispositions", {}))
        inputs.update({path: raw for path, raw in updates.items() if path in applied_updates})
    data["input_sha256"] = {p: hashlib.sha256(raw).hexdigest() for p, raw in inputs.items()}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"本文再読の根拠 {sum(data['population'].values())} 件を接続しました")


if __name__ == "__main__":
    main()
