"""Compare saved observations with canonical/public identity sets without adopting data.

A differing body is a version difference, never proof of corruption or data loss.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import re

try:
    from .verification_data import record_id_hash, record_identity
except ImportError:
    from verification_data import record_id_hash, record_identity

KEY = re.compile(r"^sha256:[0-9a-f]{64}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
CODE = re.compile(r"^[a-z][a-z0-9_-]*$")
STATUSES = ("in_canonical", "pending_review", "decision_unknown", "excluded_confirmed", "unresolved")
FIELDS = ("main_issue", "stance", "is_opinion", "is_relevant")


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _key(row):
    _require(isinstance(row, dict), "record must be object")
    supplied = row.get("record_id_hash")
    if supplied is not None:
        _require(isinstance(supplied, str) and KEY.fullmatch(supplied), "invalid record_id_hash")
    raw = {key: value for key, value in row.items() if key != "record_id_hash"}
    identity = None
    try:
        identity = record_identity(raw)
    except ValueError:
        _require(supplied is not None, "record has no stable identity")
    _require("synthetic" not in str(row.get("source", "")).lower()
             and "synthetic" not in str(identity).lower() and not row.get("synthetic"),
             "synthetic record is not an observation")
    # Text-only fallback cannot establish a stable post identity across versions.
    if identity is not None:
        _require(identity.startswith("tweet:"), "tweet identity required")
        computed = record_id_hash(raw)
        _require(supplied is None or supplied == computed, "record_id_hash disagrees with tweet identity")
        return computed
    return supplied


def _index(rows):
    _require(isinstance(rows, list), "rows must be list")
    result = {}
    for row in rows:
        key = _key(row)
        _require(key not in result, "duplicate record identity within source")
        result[key] = row
    return result


def _classification(row):
    nested = row.get("classification")
    _require(nested is None or isinstance(nested, dict), "classification must be object")
    nested = nested or {}
    values = {field: nested[field] if field in nested else row.get(field) for field in FIELDS}
    for field in ("is_opinion", "is_relevant"):
        _require(values[field] is None or type(values[field]) is bool, "invalid classification flag")
    for field in ("main_issue", "stance"):
        _require(values[field] is None or isinstance(values[field], str), "invalid semantic classification")
    return values


def _opinion(row):
    values = _classification(row)
    if values["is_opinion"] is None:
        return None
    if values["is_relevant"] is False:
        return False
    return values["is_opinion"]


def _classification_relation(old, canonical, kind):
    if canonical is None or kind == "raw":
        return "unavailable"
    left, right = _classification(old), _classification(canonical)
    # A known disagreement is detectable even when another field is missing.
    if any(left[field] is not None and right[field] is not None and left[field] != right[field]
           for field in FIELDS):
        return "different"
    if any(left[field] is None or right[field] is None for field in FIELDS):
        return "unavailable"
    return "same"


def _body_relation(old, canonical, kind):
    if canonical is None or kind == "verification":
        return "unavailable"
    left, right = old.get("text"), canonical.get("text")
    if not isinstance(left, str) or not isinstance(right, str):
        return "unavailable"
    return "same" if left == right else "different"


def _decision(decision):
    _require(isinstance(decision, dict) and set(decision) ==
             {"status", "reason_code", "evidence_file", "evidence_sha256"}, "invalid decision fields")
    _require(decision["status"] in STATUSES[1:4], "invalid decision status")
    _require(isinstance(decision["reason_code"], str) and CODE.fullmatch(decision["reason_code"]), "invalid reason_code")
    _require(isinstance(decision["evidence_file"], str) and decision["evidence_file"].strip()
             and not decision["evidence_file"].startswith(("http://", "https://")), "evidence file required")
    _require(isinstance(decision["evidence_sha256"], str) and DIGEST.fullmatch(decision["evidence_sha256"]), "invalid evidence digest")
    return deepcopy(decision)


def build_topic(topic, canonical_rows, sources, decisions, public_keys=None, published=True):
    """Build one body-free row per unique saved/canonical identity.

    Status describes presence or documented decisions, not inferred adoption intent.
    Public membership is independently supplied; None means it was not measured.
    """
    _require(isinstance(topic, str) and CODE.fullmatch(topic), "invalid topic")
    _require(type(published) is bool, "published must be bool")
    canonical = _index(canonical_rows)
    for row in canonical.values():
        _classification(row)
    _require(isinstance(sources, list), "sources must be list")
    observations = {}
    source_ids = set()
    for source in sources:
        _require(isinstance(source, dict) and set(source) == {"source_id", "kind", "rows"}, "invalid source fields")
        source_id, kind = source["source_id"], source["kind"]
        _require(isinstance(source_id, str) and source_id.strip() and source_id not in source_ids, "invalid or duplicate source_id")
        _require(kind in {"classified", "raw", "verification"}, "invalid source kind")
        source_ids.add(source_id)
        for key, row in _index(source["rows"]).items():
            if kind != "raw":
                _classification(row)
            observations.setdefault(key, []).append({"source_id": source_id, "kind": kind,
                "body_relation": _body_relation(row, canonical.get(key), kind),
                "classification_relation": _classification_relation(row, canonical.get(key), kind)})
    keys = canonical.keys() | observations.keys()
    _require(isinstance(decisions, dict), "decisions must be object")
    _require(set(decisions) <= keys, "decision refers to an unobserved identity")
    decision_map = {key: _decision(value) for key, value in decisions.items()}
    if public_keys is not None:
        _require(isinstance(public_keys, (set, frozenset)) and
                 all(isinstance(key, str) and KEY.fullmatch(key) for key in public_keys), "invalid public_keys")
        # Public-only IDs must remain visible even when absent from saved/canonical data.
        keys |= public_keys
    records = []
    counts = Counter({status: 0 for status in STATUSES})
    for key in sorted(keys):
        present = key in canonical
        decision = decision_map.get(key)
        status = "in_canonical" if present else decision["status"] if decision else "unresolved"
        counts[status] += 1
        records.append({"record_id_hash": key, "canonical_presence": present,
                        "canonical_opinion": _opinion(canonical[key]) if present else None,
                        "public_opinion_presence": False if not published else None if public_keys is None else key in public_keys,
                        "adoption_status": status, "decision": decision,
                        "decision_superseded_by_presence": bool(present and decision),
                        "observations": sorted(observations.get(key, []), key=lambda item: item["source_id"])})
    return {"topic": topic, "records": records, "summary": {**dict(counts),
            "unique_records": len(records), "observations": sum(len(r["observations"]) for r in records),
            "sources": len(sources)}}
