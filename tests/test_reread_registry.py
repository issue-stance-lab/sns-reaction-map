import copy
import hashlib
import unittest
from scripts.reread_registry import (snapshot_records, assess, create_target,
                                    record_reviews, validate_manifest)


def rows():
    return [{"tweet_id": str(i), "text": f"body {i}",
             "classification": {"main_issue": "roads", "is_opinion": True}} for i in range(3)]


def manifest():
    return {"schema_version": 1, "topic": "bike", "snapshot_at": "2026-09-06T12:00:00+09:00",
            "canonical_sha256": "a" * 64, "records": snapshot_records(rows())}


def evidence(record, quality="verified"):
    return {"kind": "editorial_body_reread", "evidence_quality": quality,
            "read_at": "2026-09-06T11:00:00+09:00" if quality == "verified" else None,
            "reviewer_type": "editorial_ai", "reviewer": "reviewer-a" if quality == "verified" else None,
            "method_version": "body-review-v1" if quality == "verified" else None,
            "text_sha256": record["baseline_text_sha256"] if quality == "verified" else None,
            "reason_sha256": "b" * 64 if quality == "verified" else None,
            "source_file": "quality/private-evidence.json", "source_sha256": "c" * 64,
            "bucket": "road-rules"}


class RereadRegistryTests(unittest.TestCase):
    def test_snapshot_has_no_body_and_no_claim_of_reading(self):
        snap = snapshot_records(rows())
        self.assertEqual(snap, snapshot_records(list(reversed(rows()))))
        self.assertEqual(set(snap[0]), {"post_key", "baseline_text_sha256", "main_issue", "is_opinion", "review"})
        self.assertTrue(all(row["review"] is None for row in snap))
        self.assertEqual(assess(manifest(), rows())["summary"]["unreviewed"], 3)

    def test_duplicate_id_normalizes_strings_and_numbers(self):
        data = rows()
        data.append({**data[0], "tweet_id": 0})
        with self.assertRaisesRegex(ValueError, "duplicate"):
            snapshot_records(data)

    def test_legacy_is_not_upgraded_by_snapshot_hash(self):
        m = manifest()
        m["records"][0]["review"] = evidence(m["records"][0], "legacy")
        result = assess(m, rows())["summary"]
        self.assertEqual(result["reviewed_legacy"], 1)
        self.assertEqual(result["reviewed_verified"], 0)

    def test_missing_verified_evidence_is_rejected(self):
        for field in ("read_at", "reviewer", "method_version", "text_sha256", "reason_sha256"):
            with self.subTest(field=field):
                m = manifest()
                m["records"][0]["review"] = evidence(m["records"][0])
                m["records"][0]["review"][field] = None
                with self.assertRaises(ValueError):
                    validate_manifest(m)

    def test_body_issue_opinion_and_population_deltas(self):
        m = manifest()
        for row in m["records"]:
            row["review"] = evidence(row)
        data = rows()
        data[0]["text"] = "changed"
        data[1]["classification"] = {"main_issue": "other", "is_opinion": False}
        data.pop()
        data.append({"tweet_id": "new", "text": "new", "classification": {"is_opinion": False}})
        summary = assess(m, data)["summary"]
        self.assertEqual(summary, {"added": 1, "removed": 1, "body_changed": 1,
                                  "issue_changed": 1, "opinion_changed": 1,
                                  "unreviewed": 2, "reviewed_legacy": 0, "reviewed_verified": 1})

    def test_old_review_body_cannot_be_counted_verified(self):
        m = manifest()
        m["records"][0]["review"] = evidence(m["records"][0])
        m["records"][0]["review"]["text_sha256"] = "d" * 64
        self.assertEqual(assess(m, rows())["summary"]["reviewed_verified"], 0)
        self.assertEqual(assess(m, rows())["summary"]["body_changed"], 1)

    def test_record_exact_target_and_preserve_input(self):
        m = manifest()
        key = m["records"][0]["post_key"]
        target = create_target(m, [key])
        new = record_reviews(m, target, [{"post_key": key, "review": evidence(m["records"][0])}])
        self.assertIsNone(m["records"][0]["review"])
        self.assertEqual(assess(new, rows())["summary"]["reviewed_verified"], 1)

    def test_incomplete_duplicate_and_extra_reviews_fail(self):
        m = manifest()
        target = create_target(m, [r["post_key"] for r in m["records"][:2]])
        entries = [{"post_key": r["post_key"], "review": evidence(r)} for r in m["records"]]
        for batch in (entries[:1], entries[:2] + entries[:1], entries):
            with self.assertRaises(ValueError):
                record_reviews(m, target, batch)

    def test_target_fingerprint_and_concurrent_manifest_edits_fail(self):
        m = manifest()
        target = create_target(m, [m["records"][0]["post_key"]])
        batch = [{"post_key": m["records"][0]["post_key"], "review": evidence(m["records"][0])}]
        tampered = copy.deepcopy(target)
        tampered["records"][0]["main_issue"] = "wrong"
        with self.assertRaises(ValueError):
            record_reviews(m, tampered, batch)
        m["records"][1]["main_issue"] = "changed by other session"
        with self.assertRaises(ValueError):
            record_reviews(m, target, batch)

    def test_automated_legacy_mismatched_new_evidence_fails(self):
        m = manifest()
        row = m["records"][0]
        target = create_target(m, [row["post_key"]])
        for field, value in (("kind", "automated"), ("reviewer_type", "classifier"),
                             ("evidence_quality", "legacy"), ("text_sha256", "d" * 64),
                             ("read_at", "2026-09-06")):
            with self.subTest(field=field):
                review = evidence(row)
                review[field] = value
                with self.assertRaises(ValueError):
                    record_reviews(m, target, [{"post_key": row["post_key"], "review": review}])

    def test_delta_review_targets_current_bodies_and_added_ids(self):
        m = manifest()
        current = rows()
        current[0]["text"] = "new version"
        current[1]["text"] = "unread different version"
        current.append({"tweet_id": "new", "text": "new", "classification": {"is_opinion": False}})
        selected = [r for r in snapshot_records(current) if r["post_key"] in
                    {hashlib.sha256(b"0").hexdigest(), hashlib.sha256(b"new").hexdigest()}]
        target = create_target(m, [r["post_key"] for r in selected], current)
        accepted = record_reviews(m, target, [{"post_key": r["post_key"], "review": evidence(r)} for r in selected], current)
        summary = assess(accepted, current)["summary"]
        self.assertEqual(summary["reviewed_verified"], 2)
        self.assertEqual(summary["body_changed"], 1)
        self.assertEqual(summary["added"], 0)
        current[0]["text"] = "changed after target prepared"
        with self.assertRaises(ValueError):
            record_reviews(m, target, [{"post_key": r["post_key"], "review": evidence(r)} for r in selected], current)

    def test_optional_migration_sources_preserve_historical_date_labels(self):
        m = manifest()
        m.update(sources={"quality/old.json": "a" * 64},
                 source_date_labels={"quality/old.json": "2026-08-10"},
                 migration_note="Snapshot hashes do not prove historical body versions.")
        self.assertIs(validate_manifest(m), m)
        m["sources"]["quality/old.json"] = "invalid"
        with self.assertRaises(ValueError):
            validate_manifest(m)

    def test_unknown_legacy_reviewer_is_not_inferred(self):
        for reviewer_type in ("unspecified_editorial", "ai_or_unspecified_editorial"):
            m = manifest()
            review = evidence(m["records"][0], "legacy")
            review["reviewer_type"] = reviewer_type
            m["records"][0]["review"] = review
            self.assertEqual(assess(m, rows())["summary"]["reviewed_legacy"], 1)
            review.update(evidence(m["records"][0]))
            review["reviewer_type"] = reviewer_type
            with self.assertRaises(ValueError):
                validate_manifest(m)

    def test_missing_and_invalid_opinion_flags_do_not_become_false(self):
        for bad in (None, "false", 0):
            data = rows()
            data[0]["classification"]["is_opinion"] = bad
            with self.assertRaises(ValueError):
                snapshot_records(data)
        data = rows()
        del data[0]["classification"]["is_opinion"]
        with self.assertRaises(ValueError):
            snapshot_records(data)
        data[0]["is_opinion"] = False
        self.assertFalse(next(r for r in snapshot_records(data)
                              if r["post_key"] == hashlib.sha256(b"0").hexdigest())["is_opinion"])

    def test_manifest_rejects_private_fields_duplicate_keys_and_bad_schema(self):
        for mutation in (lambda m: m.update(schema_version=True),
                         lambda m: m["records"][0].update(text="private"),
                         lambda m: m["records"].append(m["records"][0])):
            m = manifest()
            mutation(m)
            with self.assertRaises(ValueError):
                validate_manifest(m)


if __name__ == "__main__":
    unittest.main()
