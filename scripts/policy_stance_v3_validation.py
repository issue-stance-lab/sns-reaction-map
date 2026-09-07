#!/usr/bin/env python3
"""Prepare and compare the bounded policy-stance v3 validation packet."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts.verification_data import record_id_hash
except ModuleNotFoundError:
    from verification_data import record_id_hash


ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = Path("/Volumes/HD-LE-B/issue-stance-private-backups/data-repairs/body-review-pilot")
PRIOR_PACKET = EXTERNAL / "20260907-policy-stance-check-v1/packet.private.json"
RECHECK_PACKET = EXTERNAL / "20260907-policy-stance-recheck-v2/packet.private.json"
LEDGER = ROOT / "data/verification/editorial-adoption-current.json"
SPEC = ROOT / "quality/designs/body-review/POLICY_STANCE_MAPPING_V3.md"
FIELDS = ("is_relevant", "is_opinion", "main_issue", "stance")

CANONICAL = {
    "ai-copyright": ROOT / "social-samples/ai-copyright_hermes_classified.json",
    "fukushuto": ROOT / "social-samples/fukushuto_hermes_classified.json",
}

AI_ISSUES = {
    "AI生成物の権利・創作性",
    "学習データ・無断利用",
    "クリエイター保護・権利",
    "法制度・規制整備",
    "利用者モラル・倫理",
    "技術競争・推進",
    "その他",
}
AI_STANCES = {"推進・活用支持", "規制・制限強化支持", "中立・情報"}
FUKUSHUTO_ISSUES = {"都構想・維新", "候補地", "定義・中身", "防災・災害", "優先順位", "費用・財源", "その他"}
FUKUSHUTO_STANCES = {"法案賛成・推進", "法案反対", "中立・情報", None}

AI_CASES = [
    ("ai-new-01", "sha256:0e8160f99af596fd1955d7b9d63d3dfd6c269fd0aa57fe2b9196802e8533c40f", "use_and_rights_anxiety"),
    ("ai-new-02", "sha256:03327b26e38b84a53e13caeba7c307cabd35289c0b24a9d235d76935e500c548", "rights_view_negative"),
    ("ai-new-03", "sha256:0177abee2bbc334897ca2efb0910075666a9d3eace000e41c5a486663d709f93", "legal_view_only"),
    ("ai-new-04", "sha256:00ba77c4319a0e5cb36de6c6d97251e5ccedeeed49f09e7078c6545918b030e4", "explicit_use_support_with_limits"),
    ("ai-new-05", "sha256:01bc72766c93bb41e22eab71e039eea1dbedb3a32ebea31f817958f7206cdbe7", "explicit_use_benefit"),
    ("ai-new-06", "sha256:008079972da87ba701772933e0cfc834f70af4550651e68352878c7b11a2401c", "training_harm"),
    ("ai-new-07", "sha256:02b931696f0c84c04af7e0562dcac6e5da76ae2acb2b9df462d77a4ca3271813", "use_restriction"),
    ("ai-new-08", "sha256:0434abff4a4b7c819576f3c057feaea70633b4fa6267eb70f2947cb01db669e6", "positive_expression_and_training_ban"),
    ("ai-new-09", "sha256:0222b4dca037f9dd2a6c98db3798f52e465d4989726379500c237c40a3cc06d5", "support_and_restriction"),
    ("ai-new-10", "sha256:0387b313756a83e7b6b4fff6983d803d46a9b65344d14c195905df2e7edd3eb6", "opponent_criticism_boundary"),
]

FUKUSHUTO_CASES = [
    ("fuku-new-01", "sha256:1699669d8288f2ffb567fd3dbbebf7dba5743104d90912e2b50c309de322c854", "local_bid_oppose_fukuoka"),
    ("fuku-new-02", "sha256:14cc7799a35bd35d5d8b85d5a9a4918cc1bcf1a95b43e4b98b37a8e1bb0cae10", "local_bid_oppose_osaka"),
    ("fuku-new-03", "sha256:137260cc7f8acd72199222553a60135426593da696870786a8377833c4a02578", "local_bid_support_gunma"),
    ("fuku-new-04", "sha256:15c14f015729b06a250ac0d7ecbac4cc3f1d64c1356327662d716fa85ebd7913", "local_bid_mixed"),
    ("fuku-new-05", "sha256:102c2dfce049f47315ab3d119ecb03f25e492d72da6751470c526e33794e2d8c", "whole_support_local_oppose"),
    ("fuku-new-06", "sha256:037ef70a8e5b3e98ea51bf0be5c679a2b515aa5bf3481367d2388f4f0dbe0d24", "whole_oppose_all_locations"),
    ("fuku-new-07", "sha256:06d9753ffdf7c81fe1bc01ab90f2c5c69cc7e4c25489cd2990235c3cdbedbb65", "whole_support_with_location_options"),
    ("fuku-new-08", "sha256:1968f3fc78cd5ffd3a76bc87caa582fd386f4cce5758ded34c4af998a0e7df78", "explicit_whole_support"),
    ("fuku-new-09", "sha256:0888335a0865e2c8b76d5e666787aefa5a7b6f49723efd185912500f7013bc04", "explicit_whole_oppose"),
    ("fuku-new-10", "sha256:054fd9cffcdea1111ac476010ef5f34bc7cac03b0e80a28f20c13e7a57dfcc83", "priority_oppose"),
]


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def canonical_index(topic: str) -> dict[str, dict[str, Any]]:
    rows = read(CANONICAL[topic])
    indexed = {record_id_hash(row): row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError(f"duplicate canonical identity: {topic}")
    return indexed


def prepare(output: Path) -> None:
    if output.exists():
        raise ValueError("do not overwrite an existing validation directory")
    prior = read(PRIOR_PACKET)
    recheck = read(RECHECK_PACKET)
    ledger = read(LEDGER)
    if ledger["reviewed_records"] != 4000 or ledger["counts"] != {
        "accepted": 2214,
        "hold": 1764,
        "pending_evidence": 22,
    }:
        raise ValueError("the 4,000-record adoption baseline changed")

    prior_ids = {row["record_id_hash"] for row in prior["records"]}
    selected = AI_CASES + FUKUSHUTO_CASES
    if len(selected) != 20 or len({item[1] for item in selected}) != 20:
        raise ValueError("twenty unique unused cases required")
    if prior_ids & {item[1] for item in selected}:
        raise ValueError("new cases overlap the known policy-stance twenty")

    ledger_by_key = {(row["topic"], row["record_id_hash"]): row for row in ledger["records"]}
    canon = {topic: canonical_index(topic) for topic in CANONICAL}
    records: list[dict[str, Any]] = []
    baseline: list[dict[str, Any]] = []

    known_by_index = {row["index"]: row for row in recheck["records"]}
    for case_id, index, case_type in (("known-ai-04", 4, "known_boundary"), ("known-fuku-18", 18, "known_boundary")):
        row = known_by_index[index]
        records.append({
            "case_id": case_id,
            "set": "known_boundary",
            "topic": row["topic"],
            "record_id_hash": row["record_id_hash"],
            "body_sha256": row["body_sha256"],
            "text": row["text"],
            "selection_reason": case_type,
        })
        baseline.append({
            "case_id": case_id,
            "topic": row["topic"],
            "record_id_hash": row["record_id_hash"],
            "body_sha256": row["body_sha256"],
            "current": row["classification"],
            "source": "20260907-policy-stance-recheck-v2",
        })

    for case_id, identity, reason in selected:
        topic = "ai-copyright" if case_id.startswith("ai-") else "fukushuto"
        key = (topic, identity)
        if key not in ledger_by_key:
            raise ValueError(f"selected case is outside the 4,000-record ledger: {case_id}")
        if identity not in canon[topic]:
            raise ValueError(f"selected case is outside current canonical data: {case_id}")
        saved = ledger_by_key[key]
        current = canon[topic][identity]
        body_sha256 = hashlib.sha256(current["text"].encode("utf-8")).hexdigest()
        if body_sha256 != saved["body_sha256"]:
            raise ValueError(f"body version changed: {case_id}")
        records.append({
            "case_id": case_id,
            "set": "unused_twenty",
            "topic": topic,
            "record_id_hash": identity,
            "body_sha256": body_sha256,
            "text": current["text"],
            "selection_reason": reason,
        })
        baseline.append({
            "case_id": case_id,
            "topic": topic,
            "record_id_hash": identity,
            "body_sha256": body_sha256,
            "current": saved["current"],
            "adoption_status": saved["adoption_status"],
            "adoption_basis": saved["adoption_basis"],
            "source": "editorial-adoption-current",
        })

    spec_sha = sha(SPEC)
    packet_core = {
        "schema_version": 1,
        "scope": "Policy stance mapping v3 validation only; no canonical, adoption-ledger, classification, aggregation, or public-page changes.",
        "spec_path": str(SPEC.relative_to(ROOT)),
        "spec_sha256": spec_sha,
        "counts_as_new_body_review": 0,
        "records": records,
        "allowed_values": {
            "decision_route": ["candidate", "context_needed", "criteria_needed"],
            "ai_use_position": ["support", "restrict", "mixed", "unexpressed", "unknown", None],
            "target_scope": ["whole_policy", "local_bid", "provision", "other", "unknown", None],
            "target_stance": ["support", "oppose", "mixed", "unexpressed", "unknown", None],
            "whole_policy_stance": ["法案賛成・推進", "法案反対", None],
            "aggregation_route": ["whole_policy", "scoped_only", "context_needed", "criteria_needed", None],
            "issues": {"ai-copyright": sorted(AI_ISSUES), "fukushuto": sorted(FUKUSHUTO_ISSUES)},
            "stances": {"ai-copyright": sorted(AI_STANCES), "fukushuto": sorted(x for x in FUKUSHUTO_STANCES if x is not None) + [None]},
        },
        "review_instructions": [
            "Read every body individually under policy-stance v3; do not infer from current or prior decisions.",
            "Return all four candidate fields. A null stance is allowed only for fukushuto scoped-only/context/criteria records and is not a production classification.",
            "For ai-copyright fill ai_use_position and leave fukushuto-only target fields null.",
            "For fukushuto fill stance_target, target_scope, target_stance, whole_policy_stance, and aggregation_route; leave ai_use_position null.",
            "If context or criteria are insufficient, preserve determinate fields and explain exactly what remains unresolved.",
        ],
    }
    packet_core["packet_fingerprint"] = fingerprint(packet_core)
    write(output / "review-input.private.json", packet_core)
    write(output / "baseline.private.json", {
        "spec_sha256": spec_sha,
        "packet_fingerprint": packet_core["packet_fingerprint"],
        "ledger_sha256": sha(LEDGER),
        "canonical_sha256": {topic: sha(path) for topic, path in CANONICAL.items()},
        "prior_packet_sha256": sha(PRIOR_PACKET),
        "recheck_packet_sha256": sha(RECHECK_PACKET),
        "baseline_counts": ledger["counts"],
        "reviewed_records": ledger["reviewed_records"],
        "records": baseline,
        "new_review_credit": 0,
        "canonical_changes": 0,
        "adoption_changes": 0,
        "public_changes": 0,
    })
    print(json.dumps({"records": len(records), "unused": 20, "known": 2, "new_review_credit": 0}, ensure_ascii=False))


def validate_review(packet: dict[str, Any], review: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if review.get("packet_fingerprint") != packet["packet_fingerprint"]:
        raise ValueError("review packet fingerprint mismatch")
    rows = review.get("records")
    if not isinstance(rows, list) or len(rows) != len(packet["records"]):
        raise ValueError("review must contain all 22 records")
    expected = {row["case_id"]: row for row in packet["records"]}
    found: dict[str, dict[str, Any]] = {}
    for row in rows:
        case_id = row.get("case_id")
        if case_id not in expected or case_id in found:
            raise ValueError(f"unknown or duplicate case: {case_id}")
        source = expected[case_id]
        for field in ("record_id_hash", "body_sha256"):
            if row.get(field) != source[field]:
                raise ValueError(f"identity mismatch: {case_id}/{field}")
        candidate = row.get("candidate")
        if not isinstance(candidate, dict) or set(candidate) != set(FIELDS):
            raise ValueError(f"four candidate fields required: {case_id}")
        if type(candidate["is_relevant"]) is not bool or type(candidate["is_opinion"]) is not bool:
            raise ValueError(f"boolean fields required: {case_id}")
        topic = source["topic"]
        issues = AI_ISSUES if topic == "ai-copyright" else FUKUSHUTO_ISSUES
        stances = AI_STANCES if topic == "ai-copyright" else FUKUSHUTO_STANCES
        if candidate["main_issue"] not in issues or candidate["stance"] not in stances:
            raise ValueError(f"invalid candidate labels: {case_id}")
        if row.get("decision_route") not in {"candidate", "context_needed", "criteria_needed"}:
            raise ValueError(f"invalid decision route: {case_id}")
        if not str(row.get("stance_target") or "").strip() or not str(row.get("reason") or "").strip():
            raise ValueError(f"target and reason required: {case_id}")
        if topic == "ai-copyright":
            if row.get("ai_use_position") not in {"support", "restrict", "mixed", "unexpressed", "unknown"}:
                raise ValueError(f"ai use position required: {case_id}")
            if any(row.get(field) is not None for field in ("target_scope", "target_stance", "whole_policy_stance", "aggregation_route")):
                raise ValueError(f"fukushuto fields must be null for AI: {case_id}")
        else:
            if row.get("ai_use_position") is not None:
                raise ValueError(f"ai field must be null for fukushuto: {case_id}")
            if row.get("target_scope") not in {"whole_policy", "local_bid", "provision", "other", "unknown"}:
                raise ValueError(f"target scope required: {case_id}")
            if row.get("target_stance") not in {"support", "oppose", "mixed", "unexpressed", "unknown"}:
                raise ValueError(f"target stance required: {case_id}")
            if row.get("whole_policy_stance") not in {"法案賛成・推進", "法案反対", None}:
                raise ValueError(f"whole policy stance invalid: {case_id}")
            if row.get("aggregation_route") not in {"whole_policy", "scoped_only", "context_needed", "criteria_needed"}:
                raise ValueError(f"aggregation route required: {case_id}")
        found[case_id] = row
    return found


def comparable(row: dict[str, Any], topic: str) -> dict[str, Any]:
    # stance_target is deliberately free-form evidence description. Compare the
    # structured mapping fields, not harmless wording differences.
    common = {"candidate": row["candidate"], "decision_route": row["decision_route"]}
    if topic == "ai-copyright":
        return common | {"ai_use_position": row["ai_use_position"]}
    return common | {field: row[field] for field in ("target_scope", "target_stance", "whole_policy_stance", "aggregation_route")}


def compare(packet_path: Path, review_a_path: Path, review_b_path: Path, public_path: Path, private_path: Path) -> None:
    packet = read(packet_path)
    review_a = read(review_a_path)
    review_b = read(review_b_path)
    if not review_a.get("reviewer") or not review_b.get("reviewer") or review_a["reviewer"] == review_b["reviewer"]:
        raise ValueError("two distinct reviewers are required")
    if "未参照" not in str(review_a.get("independence")) or "未参照" not in str(review_b.get("independence")):
        raise ValueError("independence attestations are required")
    a = validate_review(packet, review_a)
    b = validate_review(packet, review_b)
    counts = Counter()
    field_agreements = Counter()
    rows = []
    private_rows = []
    for source in packet["records"]:
        case_id, topic = source["case_id"], source["topic"]
        av, bv = comparable(a[case_id], topic), comparable(b[case_id], topic)
        different = [key for key in av if av[key] != bv[key]]
        if a[case_id]["candidate"] == b[case_id]["candidate"]:
            field_agreements["candidate_four_fields"] += 1
        if a[case_id]["decision_route"] == b[case_id]["decision_route"]:
            field_agreements["decision_route"] += 1
        if topic == "ai-copyright" and a[case_id]["ai_use_position"] == b[case_id]["ai_use_position"]:
            field_agreements["ai_use_position"] += 1
        if topic == "fukushuto":
            for field in ("target_scope", "target_stance", "whole_policy_stance", "aggregation_route"):
                if a[case_id][field] == b[case_id][field]:
                    field_agreements[f"fukushuto_{field}"] += 1
        outcome = "agreement" if not different else "disagreement"
        counts[outcome] += 1
        counts[f"{topic}_{outcome}"] += 1
        counts[f"{source['set']}_{outcome}"] += 1
        rows.append({
            "case_id": case_id,
            "set": source["set"],
            "topic": topic,
            "record_id_hash": source["record_id_hash"],
            "body_sha256": source["body_sha256"],
            "selection_reason": source["selection_reason"],
            "outcome": outcome,
            "different_fields": different,
            "reviewer_a": {k: v for k, v in a[case_id].items() if k not in {"reason", "evidence", "stance_target"}},
            "reviewer_b": {k: v for k, v in b[case_id].items() if k not in {"reason", "evidence", "stance_target"}},
        })
        private_rows.append({"source": source, "reviewer_a": a[case_id], "reviewer_b": b[case_id], "different_fields": different})

    known_expectations = {
        "known-ai-04": {
            "candidate": {"is_relevant": True, "is_opinion": True, "main_issue": "AI生成物の権利・創作性", "stance": "中立・情報"},
            "decision_route": "candidate",
            "ai_use_position": "unexpressed",
        },
        "known-fuku-18": {
            "candidate": {"is_relevant": True, "is_opinion": True, "main_issue": "費用・財源", "stance": None},
            "decision_route": "candidate",
            "target_scope": "local_bid",
            "target_stance": "oppose",
            "whole_policy_stance": None,
            "aggregation_route": "scoped_only",
        },
    }
    known_checks = {}
    for case_id, expected in known_expectations.items():
        topic = "ai-copyright" if case_id.startswith("known-ai") else "fukushuto"
        known_checks[case_id] = {
            "reviewer_a_matches_v3": all(comparable(a[case_id], topic).get(k) == v for k, v in expected.items()),
            "reviewer_b_matches_v3": all(comparable(b[case_id], topic).get(k) == v for k, v in expected.items()),
        }
    scope_counts = {
        name: dict(Counter(rows_by_id[source["case_id"]]["target_scope"] for source in packet["records"] if source["topic"] == "fukushuto"))
        for name, rows_by_id in (("reviewer_a", a), ("reviewer_b", b))
    }
    report = {
        "schema_version": 1,
        "scope": "Policy stance mapping v3 bounded validation; not an accuracy estimate or production application.",
        "spec_sha256": packet["spec_sha256"],
        "packet_fingerprint": packet["packet_fingerprint"],
        "counts": dict(counts),
        "field_agreements": dict(field_agreements),
        "field_denominators": {
            "candidate_four_fields": 22,
            "decision_route": 22,
            "ai_use_position": 11,
            "fukushuto_target_scope": 11,
            "fukushuto_target_stance": 11,
            "fukushuto_whole_policy_stance": 11,
            "fukushuto_aggregation_route": 11,
        },
        "comparison_definition": "Exact agreement compares structured fields only. Free-form stance_target, evidence, and reason wording are preserved privately but do not create false disagreements.",
        "known_boundary_checks": known_checks,
        "target_scope_counts": scope_counts,
        "records": rows,
        "reviewed_records_before": 4000,
        "reviewed_records_after": 4000,
        "new_review_credit": 0,
        "adoption_counts_unchanged": {"accepted": 2214, "hold": 1764, "pending_evidence": 22},
        "canonical_changes": 0,
        "adoption_changes": 0,
        "public_changes": 0,
    }
    write(public_path, report)
    write(private_path, report | {"private_records": private_rows, "reviewer_a": review_a, "reviewer_b": review_b})
    print(json.dumps({"counts": dict(counts), "known_boundary_checks": known_checks}, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_prepare = sub.add_parser("prepare")
    p_prepare.add_argument("--output", type=Path, required=True)
    p_compare = sub.add_parser("compare")
    p_compare.add_argument("--packet", type=Path, required=True)
    p_compare.add_argument("--review-a", type=Path, required=True)
    p_compare.add_argument("--review-b", type=Path, required=True)
    p_compare.add_argument("--public", type=Path, required=True)
    p_compare.add_argument("--private", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.output)
    else:
        compare(args.packet, args.review_a, args.review_b, args.public, args.private)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
