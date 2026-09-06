#!/usr/bin/env python3
"""Verify the body-free adoption snapshot using repository-tracked evidence only."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

import yaml

try:
    from .adoption_registry import KEY, DIGEST, STATUSES, _decision
except ImportError:
    from adoption_registry import KEY, DIGEST, STATUSES, _decision

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = "data/verification/adoption/registry.json"
TOPIC_FIELDS = {"topic", "records", "summary", "canonical_file", "canonical_sha256", "public_file",
                "public_sha256", "published_state", "sources", "saved_unique_records", "saved_outside_canonical"}
RECORD_FIELDS = {"record_id_hash", "canonical_presence", "canonical_opinion", "public_opinion_presence",
                 "adoption_status", "decision", "decision_superseded_by_presence", "observations"}
SOURCE_FIELDS = {"source_id", "file", "external", "sha256", "kind", "count", "body_available"}
SOURCE_OPTIONAL = {"verification_file", "verification_sha256", "report_file", "report_sha256", "run_id", "saved_status"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def fields(value, required, optional=frozenset()):
    require(isinstance(value, dict) and required <= set(value) <= required | optional, "unexpected or missing schema fields")


def safe_path(value):
    require(isinstance(value, str) and value and not PurePosixPath(value).is_absolute()
            and ".." not in PurePosixPath(value).parts and ":" not in value and "\\" not in value,
            "unsafe evidence path")
    return value


def sha(value):
    require(isinstance(value, str) and DIGEST.fullmatch(value), "invalid SHA256")


def key(value):
    require(isinstance(value, str) and KEY.fullmatch(value), "invalid identity hash")


def count(value):
    require(type(value) is int and value >= 0, "invalid count")


def verify(root=ROOT, registry_path=REGISTRY, tracked_files=None):
    root = Path(root)
    if tracked_files is None:
        tracked_files = set(subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0"))
    else:
        tracked_files = set(tracked_files)
    checked = set()

    def read(path):
        return json.loads((root / safe_path(path)).read_text())

    def check_file(path, digest, mandatory=False):
        safe_path(path); sha(digest)
        if mandatory:
            require(path in tracked_files, f"required evidence is not tracked: {path}")
        if path in tracked_files:
            require((root / path).is_file(), f"tracked evidence missing: {path}")
            require(hashlib.sha256((root / path).read_bytes()).hexdigest() == digest,
                    f"snapshot fingerprint changed: {path}")
            checked.add(path)

    registry = read(registry_path)
    fields(registry, {"schema_version", "snapshot_at", "scope", "scope_config", "decision_seed", "topics", "cohorts"})
    require(type(registry["schema_version"]) is int and registry["schema_version"] == 1, "unsupported schema")
    stamp = registry["snapshot_at"]
    require(isinstance(stamp, str) and "T" in stamp and datetime.fromisoformat(stamp.replace("Z", "+00:00")).tzinfo is not None,
            "invalid snapshot timestamp")
    require(registry["scope"] == "saved_updates_and_declared_legacy_waves", "unsupported scope")
    for name in ("scope_config", "decision_seed"):
        fields(registry[name], {"file", "sha256"})
        check_file(registry[name]["file"], registry[name]["sha256"], True)
    require(registry["scope_config"]["file"] == "configs/adoption-sources.yaml", "unexpected scope config")
    require(registry["decision_seed"]["file"] == "data/verification/adoption/decision-evidence.json", "unexpected decision seed")
    seed = read(registry["decision_seed"]["file"])
    fields(seed, {"schema_version", "cohorts", "decisions", "evidence_sources"})
    require(type(seed["schema_version"]) is int and seed["schema_version"] == 1, "unsupported decision schema")
    for path, digest in seed["evidence_sources"].items():
        safe_path(path); sha(digest)  # external private evidence: format only, no invented verification
    config = yaml.safe_load((root / registry["scope_config"]["file"]).read_text())
    themes = yaml.safe_load((root / "THEMES.yaml").read_text())["themes"]
    require(set(registry["topics"]) == set(themes), "theme coverage changed")
    require(set(seed["decisions"]) <= set(themes), "decision topic unknown")
    all_records = {}
    for topic, data in registry["topics"].items():
        fields(data, TOPIC_FIELDS)
        require(data["topic"] == topic and data["canonical_file"] == themes[topic]["sample_file"], "canonical reference changed")
        require(data["published_state"] == themes[topic]["published"], "published state changed")
        check_file(data["canonical_file"], data["canonical_sha256"])
        expected_public = f"data/public/themes/{topic}.json"
        require((data["public_file"] == expected_public) == (expected_public in tracked_files), "public snapshot coverage changed")
        public_data = None
        if data["public_file"] is not None:
            check_file(data["public_file"], data["public_sha256"], True)
            public_data = read(data["public_file"])
            for field in ("collected_count", "opinion_count"):
                count(public_data.get(field))
        else:
            require(data["public_sha256"] is None, "unexpected public digest")
        source_map = {}
        verification_members = {}
        require(isinstance(data["sources"], list), "sources must be list")
        for source in data["sources"]:
            if source.get("missing") is True:
                fields(source, {"source_id", "missing"})
            else:
                fields(source, SOURCE_FIELDS, SOURCE_OPTIONAL)
                require(source["kind"] in {"classified", "raw", "verification"}, "invalid source kind")
                require(type(source["external"]) is bool and type(source["body_available"]) is bool, "invalid source flags")
                count(source["count"]); safe_path(source["file"]); sha(source["sha256"])
                for label in ("run_id", "saved_status"):
                    if label in source:
                        require(source[label] is None or (isinstance(source[label], str) and
                                re.fullmatch(r"[A-Za-z0-9_.:-]+", source[label])), "invalid source label")
                if not source["external"]:
                    check_file(source["file"], source["sha256"])
                for prefix in ("verification", "report"):
                    require((prefix + "_file" in source) == (prefix + "_sha256" in source), "incomplete file fingerprint")
                    if prefix + "_file" in source:
                        check_file(source[prefix + "_file"], source[prefix + "_sha256"], prefix == "verification")
                path = source.get("verification_file")
                if path is None and source["kind"] == "verification" and not source["external"]:
                    path = source["file"]
                if path is not None:
                    members = [row["record_id_hash"] for row in read(path)]
                    for member in members: key(member)
                    require(len(members) == len(set(members)) == source["count"], "source verification duplicate/count mismatch")
                    verification_members[source["source_id"]] = set(members)
            safe_path(source["source_id"])
            require(source["source_id"] not in source_map, "duplicate source_id")
            source_map[source["source_id"]] = source
        for section in ("legacy", "external"):
            for entry in config.get(section, []):
                if entry["topic"] == topic:
                    sid = f'{section}/{entry["path"]}'
                    require(sid in source_map and source_map[sid].get("file") == entry["path"]
                            and source_map[sid].get("kind") == entry["kind"], "declared source omitted/changed")
        # New tracked waves must not quietly pass against an old snapshot.
        prefix = f"data/verification/updates/{topic}/"
        for path in tracked_files:
            if path.startswith(prefix) and Path(path).name in {"raw.json", "classified.json"}:
                rest = path[len("data/verification/"):].removesuffix(".json")
                require(rest in source_map and not source_map[rest].get("missing"), "new verification wave is outside snapshot")
                meta = source_map[rest]
                require(meta.get("verification_file", meta.get("file")) == path, "verification wave fingerprint missing")
        by_key = {}; observed = {sid: set() for sid in source_map}
        require(isinstance(data["records"], list), "records must be list")
        for record in data["records"]:
            fields(record, RECORD_FIELDS)
            rid = record["record_id_hash"]; key(rid)
            require(rid not in by_key, "duplicate record identity")
            by_key[rid] = record
            require(type(record["canonical_presence"]) is bool and type(record["decision_superseded_by_presence"]) is bool, "invalid presence flags")
            for flag in ("canonical_opinion", "public_opinion_presence"):
                require(record[flag] is None or type(record[flag]) is bool, "invalid opinion presence")
            if not record["canonical_presence"]:
                require(record["canonical_opinion"] is None, "absent canonical cannot have opinion state")
            if data["published_state"] != "done":
                require(record["public_opinion_presence"] is False, "unpublished topic cannot be public")
            elif public_data is not None:
                # Current public generation treats a missing opinion flag as false.
                # The ledger must retain None as unknown, without promoting it to True.
                expected_public_presence = record["canonical_presence"] and record["canonical_opinion"] is True
                require(record["public_opinion_presence"] is expected_public_presence,
                        "public membership disagrees with canonical opinion state")
            else:
                require(record["public_opinion_presence"] is None, "public membership lacks public evidence")
            expected_decision = seed["decisions"].get(topic, {}).get(rid)
            require(record["decision"] == expected_decision, "decision differs from evidence seed")
            if expected_decision is not None:
                _decision(expected_decision)
                check_file(expected_decision["evidence_file"], expected_decision["evidence_sha256"], True)
            expected_status = "in_canonical" if record["canonical_presence"] else expected_decision["status"] if expected_decision else "unresolved"
            require(record["adoption_status"] == expected_status, "adoption status disagrees with presence/decision")
            require(record["decision_superseded_by_presence"] == bool(record["canonical_presence"] and expected_decision), "invalid superseded decision")
            require(isinstance(record["observations"], list), "observations must be list")
            seen = set()
            for obs in record["observations"]:
                fields(obs, {"source_id", "kind", "body_relation", "classification_relation"})
                sid = obs["source_id"]
                require(sid in source_map and sid not in seen and not source_map[sid].get("missing"), "invalid observation source")
                seen.add(sid); observed[sid].add(rid)
                require(obs["kind"] == source_map[sid]["kind"], "observation kind mismatch")
                for relation in ("body_relation", "classification_relation"):
                    require(obs[relation] in {"same", "different", "unavailable"}, "invalid relation")
                require(obs["kind"] != "raw" or obs["classification_relation"] == "unavailable", "raw source has no classification proof")
                require(obs["kind"] != "verification" or obs["body_relation"] == "unavailable", "verification source has no body proof")
                if not record["canonical_presence"]:
                    require(obs["body_relation"] == obs["classification_relation"] == "unavailable", "comparison without canonical")
        if public_data is not None:
            require(public_data["collected_count"] == sum(r["canonical_presence"] for r in by_key.values()),
                    "public collected count disagrees with canonical membership count")
            require(public_data["opinion_count"] == sum(r["canonical_opinion"] is True for r in by_key.values()),
                    "public opinion count disagrees with canonical opinion count")
        # Public aggregate JSON has no full private ID list: these checks do not
        # prove exact private canonical identity membership in a clean clone.
        require(list(by_key) == sorted(by_key), "record order is not deterministic")
        require(set(seed["decisions"].get(topic, {})) <= set(by_key), "decision identity missing")
        for sid, source in source_map.items():
            require(len(observed[sid]) == source.get("count", 0), "source observation count mismatch")
            if sid in verification_members:
                require(observed[sid] == verification_members[sid], "source observation identities differ from verification")
        summary = Counter({status: 0 for status in STATUSES})
        summary.update(record["adoption_status"] for record in by_key.values())
        expected_summary = {**dict(summary), "unique_records": len(by_key),
                            "observations": sum(len(r["observations"]) for r in by_key.values()),
                            "sources": sum(not s.get("missing", False) for s in source_map.values())}
        require(isinstance(data["summary"], dict), "summary must be object")
        for value in data["summary"].values(): count(value)
        count(data["saved_unique_records"]); count(data["saved_outside_canonical"])
        require(data["summary"] == expected_summary, "summary mismatch")
        require(data["saved_unique_records"] == sum(bool(r["observations"]) for r in by_key.values()), "saved unique count mismatch")
        require(data["saved_outside_canonical"] == sum(bool(r["observations"]) and not r["canonical_presence"] for r in by_key.values()), "outside canonical count mismatch")
        all_records[topic] = by_key
    expected_cohorts = {}
    for name, topics in seed["cohorts"].items():
        detail = {}
        for topic, members in topics.items():
            require(topic in all_records and len(members) == len(set(members)), "invalid cohort")
            require(all(member in all_records[topic] for member in members), "cohort identity missing")
            selected = [all_records[topic][member] for member in members]
            detail[topic] = {"total": len(members), "in_canonical": sum(r["canonical_presence"] for r in selected),
                             "statuses": dict(Counter(r["adoption_status"] for r in selected))}
        expected_cohorts[name] = detail
    require(registry["cohorts"] == expected_cohorts, "cohort summary mismatch")
    return {"topics": len(all_records), "records": sum(len(r) for r in all_records.values()), "checked_files": len(checked)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        result = verify(args.root)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        raise SystemExit(f"NG 採用台帳: {exc}") from exc
    print("OK 採用台帳（公開証拠・構造・集計）", result)


if __name__ == "__main__":
    main()
