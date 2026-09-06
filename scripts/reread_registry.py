"""Body-free editorial reread evidence and fixed-target validation.

A migration snapshot is NOT evidence that its text was historically read.
This module never creates editorial evidence from classification results.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import re

try:
    from .public_registry_common import is_opinion_record
except ImportError:
    from public_registry_common import is_opinion_record

HASH = re.compile(r"^[0-9a-f]{64}$")
BASE_FIELDS = {"post_key", "baseline_text_sha256", "main_issue", "is_opinion"}
REVIEW_FIELDS = {"kind", "evidence_quality", "read_at", "reviewer_type", "reviewer",
                 "method_version", "text_sha256", "reason_sha256", "source_file",
                 "source_sha256", "bucket"}
STATUSES = ("added", "removed", "body_changed", "issue_changed", "opinion_changed",
            "unreviewed", "reviewed_legacy", "reviewed_verified")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _hash(value):
    return isinstance(value, str) and bool(HASH.fullmatch(value))


def _string(value):
    return isinstance(value, str) and bool(value.strip())


def _timestamp(value):
    if not _string(value):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return "T" in value and parsed.tzinfo is not None
    except ValueError:
        return False


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def snapshot_records(canonical_rows):
    """Capture current body/classification baseline, without implying rereading."""
    records = []
    seen = set()
    for row in canonical_rows:
        identifier = row.get("tweet_id")
        _require(identifier is not None and str(identifier).strip(), "missing tweet_id")
        key = hashlib.sha256(str(identifier).encode()).hexdigest()
        _require(key not in seen, "duplicate canonical tweet_id")
        seen.add(key)
        body = row.get("text")
        _require(isinstance(body, str), "canonical text must be a string")
        issue = (row.get("classification") or {}).get("main_issue")
        _require(issue is None or isinstance(issue, str), "invalid main_issue")
        records.append({"post_key": key, "baseline_text_sha256": hashlib.sha256(body.encode()).hexdigest(),
                        "main_issue": issue, "is_opinion": is_opinion_record(row), "review": None})
    return sorted(records, key=lambda row: row["post_key"])


def _validate_review(review):
    _require(isinstance(review, dict) and set(review) == REVIEW_FIELDS, "invalid review fields")
    _require(review["kind"] == "editorial_body_reread", "automated classification is not editorial rereading")
    _require(review["reviewer_type"] in {"editorial_ai", "human"}, "invalid editorial reviewer_type")
    _require(review["evidence_quality"] in {"legacy", "verified"}, "invalid evidence_quality")
    _require(_string(review["source_file"]) and _hash(review["source_sha256"]), "missing source evidence")
    _require(_string(review["bucket"]), "missing editorial bucket")
    for name in ("reviewer", "method_version"):
        _require(review[name] is None or _string(review[name]), f"invalid {name}")
    for name in ("text_sha256", "reason_sha256"):
        _require(review[name] is None or _hash(review[name]), f"invalid {name}")
    _require(review["read_at"] is None or _timestamp(review["read_at"]), "invalid read_at timestamp")
    if review["evidence_quality"] == "verified":
        _require(all(review[name] is not None for name in
                     ("read_at", "reviewer", "method_version", "text_sha256", "reason_sha256")),
                 "verified review lacks historical evidence")


def validate_manifest(manifest):
    _require(isinstance(manifest, dict) and set(manifest) ==
             {"schema_version", "topic", "snapshot_at", "canonical_sha256", "records"}, "invalid manifest fields")
    _require(type(manifest["schema_version"]) is int and manifest["schema_version"] == 1, "unsupported schema_version")
    _require(_string(manifest["topic"]), "missing topic")
    _require(_timestamp(manifest["snapshot_at"]), "invalid snapshot_at timestamp")
    _require(_hash(manifest["canonical_sha256"]), "invalid canonical_sha256")
    _require(isinstance(manifest["records"], list), "records must be list")
    seen = set()
    for row in manifest["records"]:
        _require(isinstance(row, dict) and set(row) == BASE_FIELDS | {"review"}, "invalid record fields")
        _require(_hash(row["post_key"]) and _hash(row["baseline_text_sha256"]), "invalid record hashes")
        _require(row["post_key"] not in seen, "duplicate post_key")
        seen.add(row["post_key"])
        _require(type(row["is_opinion"]) is bool, "is_opinion must be bool")
        _require(row["main_issue"] is None or isinstance(row["main_issue"], str), "invalid main_issue")
        if row["review"] is not None:
            _validate_review(row["review"])
    _require([r["post_key"] for r in manifest["records"]] == sorted(seen), "records must be sorted")
    return manifest


def assess(manifest, current_rows):
    """Return overlapping change flags and one review status per current record."""
    validate_manifest(manifest)
    baseline = {row["post_key"]: row for row in manifest["records"]}
    current = {row["post_key"]: row for row in snapshot_records(current_rows)}
    output = []
    counts = Counter({name: 0 for name in STATUSES})
    for key in sorted(baseline.keys() | current.keys()):
        statuses = []
        if key not in current:
            statuses.append("removed")
        elif key not in baseline:
            statuses.extend(["added", "unreviewed"])
        else:
            old, now = baseline[key], current[key]
            for field, flag in (("baseline_text_sha256", "body_changed"),
                                ("main_issue", "issue_changed"), ("is_opinion", "opinion_changed")):
                if old[field] != now[field]:
                    statuses.append(flag)
            review = old["review"]
            if (review is None or "body_changed" in statuses or
                    (review["text_sha256"] is not None and review["text_sha256"] != now["baseline_text_sha256"])):
                statuses.append("unreviewed")
            else:
                statuses.append("reviewed_" + review["evidence_quality"])
        counts.update(statuses)
        output.append({"post_key": key, "statuses": statuses})
    return {"records": output, "summary": dict(counts)}


def create_target(manifest, selected_keys, current_rows=None):
    """Freeze selected baseline records; the caller must separately preserve bodies."""
    validate_manifest(manifest)
    selected = list(selected_keys)
    _require(selected and len(selected) == len(set(selected)), "empty or duplicate target keys")
    rows = {row["post_key"]: row for row in (snapshot_records(current_rows) if current_rows is not None else manifest["records"])}
    _require(set(selected) <= rows.keys(), "unknown target keys")
    target = {"schema_version": 1, "topic": manifest["topic"], "manifest_sha256": fingerprint(manifest), "records":
              [{field: rows[key][field] for field in sorted(BASE_FIELDS)} for key in sorted(selected)]}
    target["target_sha256"] = fingerprint(target)
    return target


def record_reviews(manifest, target, review_records, current_rows=None):
    """Accept complete genuine editorial evidence for exactly the frozen target."""
    validate_manifest(manifest)
    _require(isinstance(target, dict) and set(target) ==
             {"schema_version", "topic", "manifest_sha256", "records", "target_sha256"}, "invalid target fields")
    _require(isinstance(target["records"], list), "invalid target records")
    _require(all(isinstance(row, dict) and set(row) == BASE_FIELDS for row in target["records"]), "invalid target row")
    keys = [row["post_key"] for row in target["records"]]
    _require(target == create_target(manifest, keys, current_rows), "target changed or fingerprint mismatch")
    _require(isinstance(review_records, list), "review_records must be list")
    incoming = {}
    for entry in review_records:
        _require(isinstance(entry, dict) and set(entry) == {"post_key", "review"}, "invalid submitted fields")
        key = entry["post_key"]
        _require(key in keys and key not in incoming, "unknown or duplicate submitted post_key")
        _validate_review(entry["review"])
        _require(entry["review"]["evidence_quality"] == "verified", "new review requires verified evidence")
        incoming[key] = entry["review"]
    _require(set(incoming) == set(keys), "missing target reviews")
    result = deepcopy(manifest)
    updated = {row["post_key"]: row for row in result["records"]}
    for row in target["records"]:
        review = incoming[row["post_key"]]
        _require(review["text_sha256"] == row["baseline_text_sha256"], "review body does not match fixed target")
        updated[row["post_key"]] = {**deepcopy(row), "review": deepcopy(review)}
    result["records"] = [updated[key] for key in sorted(updated)]
    return result
