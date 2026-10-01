#!/usr/bin/env python3
"""本文確認結果から、自転車定期更新の候補と再読記録を組み立てる。"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
EDITORIAL_REREAD = Path("data/bike-blue-ticket_issues-reread.json")
OPPOSITION_REREAD = Path("data/bike-blue-ticket_opposition_reread.json")
OPPOSITION_BUCKETS = {"strict", "scope", "place", "distrust", "abolish"}
ALLOWED_ISSUES = {
    "取締り強化賛成", "インフラ整備優先", "車道走行への不安",
    "免許制要求", "ルール曖昧・不信", "その他",
}
ALLOWED_STANCES = {
    "賛成（取締り強化支持）", "どちらでもない", "反対（インフラ・制度優先）",
}
ALLOWED_BUCKETS = {
    "strict", "abolish", "distrust", "scope", "place",
    "n_burden", "n_education", "n_effects", "n_environment", "n_fraud",
    "n_other", "n_rules", "n_transport", "oa_conduct_safety",
    "oa_driver_enforcement", "oa_fine_revenue", "oa_license_enforcement",
    "oa_luup_comparison", "oa_media_attention", "oa_pedestrian_accountability",
    "ob_incident_followup", "ob_moped_enforcement", "ob_policy_process",
    "ob_safe_compliance", "ob_sidewalk_option", "r_separation",
    "r_training_required", "r_license_safety", "s_dangerous_riding",
    "s_enforcement_gap", "s_shared_responsibility", "s_stronger_sanctions",
    "excluded_information_or_off_topic",
}


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _classification(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("classification")
    if not isinstance(value, dict) or value.get("error"):
        raise ValueError(f"本文確認できない分類行があります: {row.get('tweet_id')}")
    return value


def build(root: Path, stage: Path, plan_path: Path, update_path: Path) -> dict[str, Any]:
    """固定した確認計画を検証し、候補・本文確認記録・集計を保存する。"""
    root = root.resolve()
    stage = stage.resolve()
    plan_path = plan_path.resolve()
    update_path = update_path.resolve()
    themes = yaml.safe_load((root / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
    canonical_path = root / themes["bike-blue-ticket"]["sample_file"]
    current = read_json(canonical_path)
    wave = read_json(stage / "classified-wave.json")
    new_rows = read_json(stage / "new-only.json")
    plan = read_json(plan_path)
    report = read_json(stage / "report.json")

    if report.get("topic") != "bike-blue-ticket":
        raise ValueError("自転車以外の更新回を指定できません")
    if not isinstance(plan.get("adopt"), list) or not isinstance(plan.get("exclude_groups"), list):
        raise ValueError("本文確認計画の形式が不正です")
    if len(wave) != len(new_rows):
        raise ValueError("分類済み投稿と新規投稿の件数が違います")

    by_index = {i: row for i, row in enumerate(wave)}
    if len(by_index) != len(wave):
        raise ValueError("分類済み投稿の添字が不正です")
    decisions: dict[int, dict[str, Any]] = {}
    for entry in plan["adopt"]:
        index = int(entry["index"])
        if index in decisions:
            raise ValueError(f"重複した本文確認 index: {index}")
        decisions[index] = {**entry, "decision": "adopt", "classification_concern": "none"}
    for group in plan["exclude_groups"]:
        for raw_index in group["indices"]:
            index = int(raw_index)
            if index in decisions:
                raise ValueError(f"重複した本文確認 index: {index}")
            decisions[index] = {
                "index": index,
                "decision": "exclude",
                "classification_concern": group["concern"],
                "reason": group["reason"],
                "bucket": "excluded_information_or_off_topic",
            }
    deferred: dict[int, dict[str, Any]] = {}
    for entry in plan.get("defer_prior_holds", []):
        index = int(entry["index"])
        if index in decisions or index in deferred:
            raise ValueError(f"重複した保留再掲 index: {index}")
        if index not in by_index:
            raise ValueError(f"過去保留の参照先が範囲外です: {index}")
        row = by_index[index]
        source = new_rows[index]
        if str(row.get("tweet_id")) != str(source.get("tweet_id")) or row.get("text") != source.get("text"):
            raise ValueError(f"過去保留のID・本文が新規収集と一致しません: index={index}")
        source_path = root / entry["source_update"]
        prior = read_json(source_path)
        prior_item = next((item for item in prior.get("items", [])
                           if str(item.get("tweet_id")) == str(row.get("tweet_id"))), None)
        text_hash = digest_text(str(row.get("text") or ""))
        if not prior_item or prior_item.get("decision") != "hold" or prior_item.get("text_sha256") != text_hash:
            raise ValueError(f"過去の保留根拠と今回の同一本文を確認できません: {row.get('tweet_id')}")
        deferred[index] = {
            "index": index,
            "tweet_id": str(row["tweet_id"]),
            "source_update": entry["source_update"],
            "source_update_sha256": digest_bytes(source_path.read_bytes()),
            "text_sha256": text_hash,
            "reason_sha256": prior_item["reason_sha256"],
            "reason": prior_item["reason"],
        }
    expected = set(range(len(wave)))
    assigned = set(decisions) | set(deferred)
    if assigned != expected:
        raise ValueError(f"本文確認の欠落・範囲外 index: missing={sorted(expected-assigned)}, extra={sorted(assigned-expected)}")

    new_by_id = {str(row["tweet_id"]): row for row in new_rows}
    wave_by_id = {str(row["tweet_id"]): row for row in wave}
    if len(new_by_id) != len(new_rows) or set(new_by_id) != set(wave_by_id):
        raise ValueError("新規投稿と分類済み投稿のID集合が一致しません")
    items: list[dict[str, Any]] = []
    finalized_at = str(plan["finalized_at"])
    read_at = str(plan["read_at"])
    for index in range(len(wave)):
        if index in deferred:
            continue
        row = wave[index]
        source = new_by_id[str(row["tweet_id"])]
        if row.get("text") != source.get("text"):
            raise ValueError(f"分類前後で本文が変化しています: {row.get('tweet_id')}")
        decision = decisions[index]
        classification = _classification(row)
        main_issue = decision.get("main_issue", classification.get("main_issue"))
        stance = decision.get("stance", "どちらでもない" if decision["decision"] == "exclude" else None)
        if main_issue not in ALLOWED_ISSUES or stance not in ALLOWED_STANCES:
            raise ValueError(f"本文確認後の論点・立場が未登録です: index={index}")
        if not decision.get("reason"):
            raise ValueError(f"本文確認の理由がありません: index={index}")
        bucket = decision.get("bucket")
        if bucket not in ALLOWED_BUCKETS:
            raise ValueError(f"本文確認の区分が未登録です: index={index} bucket={bucket}")
        is_adopted = decision["decision"] == "adopt"
        if is_adopted:
            if decision.get("intensity") not in {"low", "medium", "high"}:
                raise ValueError(f"採用投稿の強度がありません: index={index}")
            if not decision.get("intensity_reason"):
                raise ValueError(f"採用投稿の強度根拠がありません: index={index}")
        item = {
            "index": index,
            "tweet_id": str(row["tweet_id"]),
            "text_sha256": digest_text(str(row.get("text") or "")),
            "is_opinion": is_adopted,
            "main_issue": main_issue,
            "stance": stance,
            "bucket": bucket,
            "decision": decision["decision"],
            "reason": decision["reason"],
            "body_reviewed": True,
            "review_kind": "editorial_body_reread",
            "independently_checked": True,
            "reviewer": str(plan["reviewer"]),
            "read_at": read_at,
            "reason_sha256": digest_text(str(decision["reason"])),
            "classification_concern": decision["classification_concern"],
        }
        if is_adopted:
            item.update({
                "intensity": decision["intensity"],
                "intensity_reason": decision["intensity_reason"],
                "intensity_read_at": read_at,
                "article_usable": bool(decision.get("article_usable", False)),
                "risk": decision.get("risk", "medium"),
            })
            if item["risk"] not in {"low", "medium", "high"}:
                raise ValueError(f"採用投稿のリスク分類が不正です: index={index}")
            summary = str(decision.get("summary") or "").strip()
            if not summary or len(summary) > 80:
                raise ValueError(f"採用投稿の要約が空か長すぎます: index={index}")
            item["summary"] = summary
        items.append(item)

    opposition_overrides = []
    raw_overrides = plan.get("opposition_bucket_overrides", [])
    if not isinstance(raw_overrides, list):
        raise ValueError("過去の反対再読区分の形式が不正です")
    override_ids: set[str] = set()
    for entry in raw_overrides:
        tid = str(entry.get("tweet_id") or "")
        source_rel = str(entry.get("source_update") or "")
        bucket = entry.get("bucket")
        reason = str(entry.get("reason") or "").strip()
        if (not tid or tid in override_ids or bucket not in OPPOSITION_BUCKETS
                or not reason or entry.get("confirmed_by") != "owner"):
            raise ValueError(f"過去の反対再読区分の確認内容が不正です: {tid}")
        prior_path = (root / source_rel).resolve()
        if not prior_path.is_relative_to(root) or not prior_path.is_file():
            raise ValueError(f"区分確認の参照元が見つかりません: {source_rel}")
        prior = read_json(prior_path)
        prior_item = next((item for item in prior.get("items", [])
                           if str(item.get("tweet_id")) == tid), None)
        prior_row = next((row for row in current if str(row.get("tweet_id")) == tid), None)
        if (prior_item is None or prior_item.get("decision") != "adopt"
                or prior_item.get("stance") != "反対（インフラ・制度優先）"
                or prior_row is None
                or digest_text(str(prior_row.get("text") or "")) != prior_item.get("text_sha256")):
            raise ValueError(f"過去の採用済み反対投稿と本文指紋を確認できません: {tid}")
        override_ids.add(tid)
        opposition_overrides.append({
            "tweet_id": tid,
            "source_update": source_rel,
            "source_update_sha256": digest_bytes(prior_path.read_bytes()),
            "text_sha256": prior_item["text_sha256"],
            "bucket": bucket,
            "reason": reason,
            "confirmed_by": "owner",
            "confirmed_at": str(plan.get("owner_confirmed_at") or ""),
        })
    display_decision = plan.get("tide_display_decision")
    if display_decision != "show_without_classifier_version_note":
        raise ValueError("潮目の分類器変更表示について確認済みの指示がありません")

    unspoken_review = plan.get("unspoken_issue_review")
    adopted_ids = sorted(
        str(wave[int(entry["index"])].get("tweet_id"))
        for entry in plan["adopt"]
    )
    expected_unspoken_ids = {
        "bike-blue-ticket-sc-1", "bike-blue-ticket-sc-2",
        "bike-blue-ticket-sc-3", "bike-blue-ticket-sc-4",
    }
    if (
        not isinstance(unspoken_review, dict)
        or unspoken_review.get("reviewer") != "editorial_ai"
        or unspoken_review.get("reviewed_at") != "2026-09-29"
        or unspoken_review.get("scope") != "all_newly_adopted_opinions"
        or int(unspoken_review.get("reviewed_opinion_count", -1)) != len(adopted_ids)
        or set(unspoken_review.get("topic_ids") or []) != expected_unspoken_ids
        or unspoken_review.get("result") != "no_new_mentions"
    ):
        raise ValueError("新規採用意見と未言及論点4件の本文確認記録が揃っていません")

    update = {
        "reviewer": str(plan["reviewer"]),
        "reviewer_type": str(plan.get("reviewer_type", "editorial_ai")),
        "read_at": read_at,
        "finalized_by": str(plan["finalized_by"]),
        "finalized_at": finalized_at,
        "review_kind": "editorial_body_reread",
        "method": str(plan["method"]),
        "input_sha256": digest_bytes((stage / "new-only.json").read_bytes()),
        "final_review_sha256": digest_bytes(plan_path.read_bytes()),
        "deferred_prior_holds": [deferred[index] for index in sorted(deferred)],
        "opposition_bucket_overrides": opposition_overrides,
        "unspoken_issue_review": {
            **unspoken_review,
            "reviewed_tweet_ids": adopted_ids,
        },
        "items": items,
    }
    write_json(update_path, update)

    candidate = copy.deepcopy(current)
    for item in items:
        index = int(item["index"])
        if item["decision"] == "hold":
            continue
        row = copy.deepcopy(wave[index])
        c = _classification(row)
        adopted = item["decision"] == "adopt"
        c.update({
            "main_issue": item["main_issue"],
            "stance": item["stance"],
            "is_opinion": adopted,
            "reason": item["reason"],
            "summary": item.get("summary") or item["reason"],
        })
        row["is_opinion"] = adopted
        row["editorial_review"] = {
            "source": update_path.relative_to(root).as_posix(),
            "decision": item["decision"],
            "reason": item["reason"],
        }
        if adopted:
            c["intensity"] = item["intensity"]
            c["article_usable"] = item["article_usable"]
            c["risk"] = item["risk"]
            row.pop("opinion_exclusion_reason", None)
            row.pop("opinion_exclusion_decided_at", None)
        else:
            row["opinion_exclusion_reason"] = item["reason"]
            row["opinion_exclusion_decided_at"] = report["date"]
        candidate.append(row)

    ids = [str(row.get("tweet_id")) for row in candidate]
    if len(ids) != len(set(ids)):
        raise ValueError("本文確認済み候補に重複tweet_idがあります")
    adopted_count = sum(item["decision"] == "adopt" for item in items)
    excluded_count = sum(item["decision"] == "exclude" for item in items)
    summary = {
        "adopted_opinions": adopted_count,
        "excluded": excluded_count,
        "held": sum(item["decision"] == "hold" for item in items),
        "deferred_prior_holds": len(deferred),
        "candidate_records": len(candidate),
        "candidate_opinions": sum(
            bool((row.get("classification") or {}).get("is_opinion", row.get("is_opinion")))
            for row in candidate
        ),
        "review_file": update_path.relative_to(root).as_posix(),
        "review_sha256": digest_bytes(update_path.read_bytes()),
    }
    opposition_summary = extend_opposition_map(
        root, update_path, stage / "opposition-reread-candidate.json"
    )
    summary["new_opposition_reread"] = opposition_summary["added"]
    summary["restored_prior_opposition_reread"] = opposition_summary["restored_prior"]
    report.update({
        "relevant": adopted_count,
        "opinions": adopted_count,
        "opinion_flag_available": True,
        "candidate": len(candidate),
        "editorial_review": summary,
        "editorial_display_decisions": {
            "tide": display_decision,
            "owner_confirmed_at": str(plan["owner_confirmed_at"]),
        },
        "automated_candidate": len(current) + len(wave),
        "checks": {
            **(report.get("checks") or {}),
            "post_review_candidate_count": len(candidate) == len(current) + adopted_count + excluded_count,
            "post_review_candidate_unique": len(ids) == len(set(ids)),
            "prior_holds_remain_outside_candidate": all(
                entry["tweet_id"] not in set(ids) for entry in deferred.values()
            ),
        },
    })
    try:
        from scripts.refresh_topic import next_collection_date
    except ImportError:
        from refresh_topic import next_collection_date
    report["next_collect_at"] = next_collection_date(
        root, "bike-blue-ticket", str(report["date"]), report
    )
    report["saved_wave_opinions"] = adopted_count
    write_json(stage / "cumulative-candidate.json", candidate)
    write_json(stage / "report.json", report)
    return {"candidate": candidate, "update": update, "summary": summary}


def extend_opposition_map(root: Path, update_path: Path, output_path: Path) -> dict[str, Any]:
    """採用済み反対意見の編集5区分を過去回から候補へ接続する。"""
    root = root.resolve()
    update_path = update_path.resolve()
    output_path = output_path.resolve()
    source = root / "data/bike-blue-ticket_opposition_reread.json"
    opposition = read_json(source)
    buckets = opposition.get("buckets")
    if not isinstance(buckets, dict) or set(buckets) != OPPOSITION_BUCKETS:
        raise ValueError("自転車の反対再読5区分が不正です")
    result = copy.deepcopy(opposition)
    assigned = {
        str(tid): bucket
        for bucket, ids in result["buckets"].items()
        for tid in ids
    }
    update_paths = sorted((root / "data/bike-blue-ticket_editorial-updates").glob("*.json"))
    if update_path not in update_paths:
        update_paths.append(update_path)
        update_paths.sort()
    all_updates = [(path.resolve(), read_json(path)) for path in update_paths]
    override_buckets: dict[str, str] = {}
    for path, update in all_updates:
        for entry in update.get("opposition_bucket_overrides", []):
            tid, bucket = str(entry.get("tweet_id") or ""), entry.get("bucket")
            if not tid or bucket not in OPPOSITION_BUCKETS:
                raise ValueError(f"過去の反対再読区分が不正です: {tid} / {bucket}")
            if tid in override_buckets and override_buckets[tid] != bucket:
                raise ValueError(f"反対再読区分のオーナー確認が競合しています: {tid}")
            override_buckets[tid] = bucket
    current_additions = 0
    prior_additions = 0
    for path, update in all_updates:
        for item in update.get("items", []):
            if item.get("decision") != "adopt" or item.get("stance") != "反対（インフラ・制度優先）":
                continue
            tid = str(item["tweet_id"])
            bucket = override_buckets.get(tid, item.get("bucket"))
            if bucket not in result["buckets"]:
                raise ValueError(f"反対投稿に5区分の割当がありません: {tid} / {bucket}")
            if tid in assigned:
                if assigned[tid] != bucket:
                    raise ValueError(f"既存の反対再読区分と今回の確認が一致しません: {tid}")
                continue
            result["buckets"][bucket].append(tid)
            assigned[tid] = bucket
            if path == update_path:
                current_additions += 1
            else:
                prior_additions += 1
    all_ids = [str(tid) for ids in result["buckets"].values() for tid in ids]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("反対再読マップに重複IDがあります")
    update = read_json(update_path)
    result["updated_at"] = update.get("finalized_at")
    result["update_source"] = update_path.relative_to(root).as_posix()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, result)
    return {
        "added": current_additions,
        "restored_prior": prior_additions,
        "total": len(all_ids),
        "sha256": digest_bytes(output_path.read_bytes()),
    }


def build_verified_reread_manifest(
    root: Path,
    candidate_path: Path,
    update_path: Path,
    issues_reread_path: Path,
    opposition_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    """再読共通台帳へ今回の採用・除外判断を、本文指紋付きで仮登録する。"""
    root = root.resolve()
    candidate_path = candidate_path.resolve()
    update_path = update_path.resolve()
    issues_reread_path = issues_reread_path.resolve()
    opposition_path = opposition_path.resolve()
    output_path = output_path.resolve()
    from scripts.reread_registry import create_target, record_reviews

    manifest_path = root / "data/verification/reread/bike-blue-ticket.json"
    manifest = read_json(manifest_path)
    candidate = read_json(candidate_path)
    update = read_json(update_path)
    by_id = {str(row["tweet_id"]): row for row in candidate}
    items = update.get("items") or []
    if not items:
        raise ValueError("再読台帳へ登録する本文確認項目がありません")
    source_file = update_path.relative_to(root).as_posix()
    source_sha = digest_bytes(update_path.read_bytes())
    selected: list[str] = []
    reviews: list[dict[str, Any]] = []
    for item in items:
        tid = str(item["tweet_id"])
        row = by_id.get(tid)
        if row is None or digest_text(str(row.get("text") or "")) != item.get("text_sha256"):
            raise ValueError(f"再読台帳の候補本文が一致しません: {tid}")
        key = digest_text(tid)
        selected.append(key)
        reviews.append({
            "post_key": key,
            "review": {
                "kind": "editorial_body_reread",
                "evidence_quality": "verified",
                "read_at": item["read_at"],
                "reviewer_type": update.get("reviewer_type", "editorial_ai"),
                "reviewer": item["reviewer"],
                "method_version": "bike-new-collection-editorial-review-v1",
                "text_sha256": item["text_sha256"],
                "reason_sha256": item["reason_sha256"],
                "source_file": source_file,
                "source_sha256": source_sha,
                "bucket": item["bucket"],
            },
        })
    if len(selected) != len(set(selected)):
        raise ValueError("再読台帳へ重複IDを登録しようとしています")
    target = create_target(manifest, selected, current_rows=candidate)
    updated = record_reviews(manifest, target, reviews, current_rows=candidate)
    updated["sources"][EDITORIAL_REREAD.as_posix()] = digest_bytes(issues_reread_path.read_bytes())
    updated["sources"][OPPOSITION_REREAD.as_posix()] = digest_bytes(opposition_path.read_bytes())
    updated["sources"][source_file] = source_sha
    updated.setdefault("source_date_labels", {})[source_file] = update.get("read_at")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, updated)
    return {"registered": len(reviews), "sha256": digest_bytes(output_path.read_bytes())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--update", type=Path, required=True)
    args = parser.parse_args()
    result = build(ROOT, args.stage, args.plan, args.update)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
