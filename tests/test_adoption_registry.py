import copy
import unittest
from scripts.adoption_registry import build_topic
from scripts.verification_data import record_id_hash


def row(identifier="1", body="original", **classification):
    return {"tweet_id": identifier, "text": body, "classification": {
        "main_issue": "roads", "stance": "support", "is_opinion": True,
        "is_relevant": True, **classification}}


def source(rows, kind="classified", name="wave1"):
    return {"source_id": name, "kind": kind, "rows": rows}


def decision(status="pending_review"):
    return {"status": status, "reason_code": "needs_editorial_review",
            "evidence_file": "quality/review.json", "evidence_sha256": "a" * 64}


class AdoptionRegistryTests(unittest.TestCase):
    def test_presence_is_id_not_body_or_classification(self):
        old = row(body="old", stance="oppose")
        result = build_topic("bike", [row()], [source([old])], {})
        record = result["records"][0]
        self.assertEqual(record["adoption_status"], "in_canonical")
        self.assertEqual(record["observations"][0]["body_relation"], "different")
        self.assertEqual(record["observations"][0]["classification_relation"], "different")
        self.assertIsNone(record["public_opinion_presence"])

    def test_same_id_across_waves_is_one_record_many_observations(self):
        result = build_topic("bike", [row()], [source([row()]), source([row()], name="wave2")], {})
        self.assertEqual(result["summary"]["unique_records"], 1)
        self.assertEqual(result["summary"]["observations"], 2)
        self.assertEqual(result["records"][0]["observations"][0]["classification_relation"], "same")

    def test_duplicates_within_source_and_duplicate_source_id_fail(self):
        for sources in ([source([row(), row()])], [source([row()]), source([row()])]):
            with self.assertRaises(ValueError):
                build_topic("bike", [], sources, {})
        with self.assertRaises(ValueError):
            build_topic("bike", [row(), row()], [], {})

    def test_supplied_hash_must_match_real_identity(self):
        bad = row()
        bad["record_id_hash"] = record_id_hash(row("2"))
        with self.assertRaises(ValueError):
            build_topic("bike", [], [source([bad])], {})
        bad["record_id_hash"] = "sha256:invalid"
        with self.assertRaises(ValueError):
            build_topic("bike", [], [source([bad])], {})

    def test_synthetic_and_text_only_identity_rejected(self):
        for bad in (row("synthetic-1"), {**row(), "source": "synthetic"}, {"text": "no stable ID"}):
            with self.assertRaises(ValueError):
                build_topic("bike", [], [source([bad])], {})

    def test_raw_only_is_unresolved_without_inferred_classification(self):
        raw = {"tweet_id": "1", "text": "original"}
        result = build_topic("bike", [], [source([raw], "raw")], {})
        record = result["records"][0]
        self.assertEqual(record["adoption_status"], "unresolved")
        self.assertIsNone(record["canonical_opinion"])
        self.assertEqual(record["observations"][0]["classification_relation"], "unavailable")

    def test_verification_only_cannot_claim_body_match(self):
        verification = {"record_id_hash": record_id_hash(row()), "classification": row()["classification"]}
        result = build_topic("bike", [row()], [source([verification], "verification")], {})
        obs = result["records"][0]["observations"][0]
        self.assertEqual(obs["body_relation"], "unavailable")
        self.assertEqual(obs["classification_relation"], "same")
        absent = build_topic("bike", [], [source([verification], "verification")], {})
        self.assertEqual(absent["summary"]["unresolved"], 1)

    def test_documented_decisions_retained_and_superseded_when_present(self):
        for status in ("pending_review", "decision_unknown", "excluded_confirmed"):
            with self.subTest(status=status):
                d = {record_id_hash(row()): decision(status)}
                result = build_topic("bike", [], [source([row()])], d)
                self.assertEqual(result["records"][0]["adoption_status"], status)
                self.assertFalse(result["records"][0]["decision_superseded_by_presence"])
                adopted = build_topic("bike", [row()], [source([row()])], d)["records"][0]
                self.assertEqual(adopted["adoption_status"], "in_canonical")
                self.assertEqual(adopted["decision"], decision(status))
                self.assertTrue(adopted["decision_superseded_by_presence"])

    def test_public_is_independent_of_canonical_and_public_only_is_visible(self):
        keys = {record_id_hash(row("2"))}
        result = build_topic("bike", [row()], [], {}, keys)
        by_key = {r["record_id_hash"]: r for r in result["records"]}
        self.assertFalse(by_key[record_id_hash(row())]["public_opinion_presence"])
        self.assertTrue(by_key[record_id_hash(row("2"))]["public_opinion_presence"])
        self.assertFalse(by_key[record_id_hash(row("2"))]["canonical_presence"])
        result = build_topic("bike", [row()], [], {}, published=False)
        self.assertFalse(result["records"][0]["public_opinion_presence"])

    def test_missing_flags_are_not_false_and_top_level_fallback_works(self):
        current = {"tweet_id": "1", "text": "original", "classification": {"main_issue": "roads"}}
        result = build_topic("bike", [current], [source([row()])], {})
        self.assertIsNone(result["records"][0]["canonical_opinion"])
        self.assertEqual(result["records"][0]["observations"][0]["classification_relation"], "unavailable")
        current["is_opinion"] = True
        self.assertTrue(build_topic("bike", [current], [], {})["records"][0]["canonical_opinion"])
        current["classification"]["is_opinion"] = False
        self.assertFalse(build_topic("bike", [current], [], {})["records"][0]["canonical_opinion"])
        current["classification"]["is_opinion"] = "false"
        with self.assertRaises(ValueError):
            build_topic("bike", [current], [], {})

    def test_decision_rejects_body_fields_and_unobserved_id(self):
        bad = decision()
        bad["reason"] = "private text"
        with self.assertRaises(ValueError):
            build_topic("bike", [], [source([row()])], {record_id_hash(row()): bad})
        with self.assertRaises(ValueError):
            build_topic("bike", [], [], {record_id_hash(row()): decision()})

    def test_output_is_body_free_deterministic_and_inputs_unchanged(self):
        canonical = [row("2"), row()]
        sources = [source([row("3"), row()]), source([row("2")], name="wave2")]
        snapshot = copy.deepcopy((canonical, sources))
        first = build_topic("bike", canonical, sources, {})
        second = build_topic("bike", list(reversed(canonical)), list(reversed(sources)), {})
        self.assertEqual(first, second)
        self.assertEqual((canonical, sources), snapshot)
        for record in first["records"]:
            self.assertEqual(set(record), {"record_id_hash", "canonical_presence", "canonical_opinion",
                "public_opinion_presence", "adoption_status", "decision", "decision_superseded_by_presence", "observations"})


if __name__ == "__main__":
    unittest.main()
