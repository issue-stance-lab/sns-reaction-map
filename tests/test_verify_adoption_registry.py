import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.adoption_registry import build_topic
from scripts.verification_data import make_verification_records, record_id_hash
from scripts.verify_adoption_registry import verify


class VerifyAdoptionRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.tracked = set()
        self.write("THEMES.yaml", 'themes:\n  bike:\n    sample_file: social-samples/private.json\n    published: done\n')
        config = "configs/adoption-sources.yaml"
        self.write(config, "legacy: []\nexternal: []\n")
        self.public = "data/public/themes/bike.json"
        self.write(self.public, {"collected_count": 1, "opinion_count": 1})
        self.evidence = "quality/reviews/decision.md"
        self.write(self.evidence, "Review decision")
        current = {"tweet_id": "1", "text": "private original", "classification": {
            "main_issue": "road", "stance": "support", "is_opinion": True, "is_relevant": True}}
        absent = {**current, "tweet_id": "2"}
        rid = record_id_hash(absent)
        self.seed_path = "data/verification/adoption/decision-evidence.json"
        self.seed = {"schema_version": 1, "decisions": {"bike": {rid: {
            "status": "pending_review", "reason_code": "pending_read",
            "evidence_file": self.evidence, "evidence_sha256": self.digest(self.evidence)}}},
            "cohorts": {"initial": {"bike": [rid]}}, "evidence_sources": {"private/decision.json": "a" * 64}}
        self.write(self.seed_path, self.seed)
        self.verification = "data/verification/updates/bike/2026-09-06/classified.json"
        self.write(self.verification, make_verification_records([current, absent]))
        sid = "updates/bike/2026-09-06/classified"
        data = build_topic("bike", [current], [{"source_id": sid, "kind": "classified", "rows": [current, absent]}],
                           self.seed["decisions"]["bike"], {record_id_hash(current)})
        data.update(canonical_file="social-samples/private.json", canonical_sha256="b" * 64,
                    public_file=self.public, public_sha256=self.digest(self.public), published_state="done",
                    sources=[{"source_id": sid, "file": "social-samples/updates/bike/2026-09-06/classified.json",
                              "external": False, "sha256": "c" * 64, "kind": "classified", "count": 2,
                              "body_available": True, "verification_file": self.verification,
                              "verification_sha256": self.digest(self.verification)}],
                    saved_unique_records=2, saved_outside_canonical=1)
        self.registry = {"schema_version": 1, "snapshot_at": "2026-09-06T15:00:00+09:00",
                         "scope": "saved_updates_and_declared_legacy_waves",
                         "scope_config": {"file": config, "sha256": self.digest(config)},
                         "decision_seed": {"file": self.seed_path, "sha256": self.digest(self.seed_path)},
                         "topics": {"bike": data}, "cohorts": {"initial": {"bike": {
                             "total": 1, "in_canonical": 0, "statuses": {"pending_review": 1}}}}}

    def write(self, path, value):
        dest = self.root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(value if isinstance(value, str) else json.dumps(value))
        self.tracked.add(path)

    def digest(self, path):
        return hashlib.sha256((self.root / path).read_bytes()).hexdigest()

    def check(self):
        self.write("data/verification/adoption/registry.json", self.registry)
        return verify(self.root, tracked_files=self.tracked)

    def test_clean_clone_needs_no_original_or_external_evidence(self):
        self.assertFalse((self.root / "social-samples").exists())
        self.assertEqual(self.check()["records"], 2)

    def test_changed_public_snapshot_and_public_decision_evidence_stop(self):
        for path in (self.public, self.evidence, self.seed_path, "configs/adoption-sources.yaml", self.verification):
            with self.subTest(path=path):
                original = (self.root / path).read_bytes()
                (self.root / path).write_bytes(original + b" ")
                with self.assertRaisesRegex(ValueError, "fingerprint changed"):
                    self.check()
                (self.root / path).write_bytes(original)

    def test_tracked_canonical_changes_are_detected(self):
        self.write("social-samples/private.json", "changed tracked canonical")
        with self.assertRaisesRegex(ValueError, "fingerprint changed"):
            self.check()

    def test_new_verification_wave_cannot_pass_old_snapshot(self):
        self.write("data/verification/updates/bike/2026-09-07/raw.json", [])
        with self.assertRaisesRegex(ValueError, "new verification wave"):
            self.check()

    def test_counts_cohorts_and_decisions_are_recomputed(self):
        original = copy.deepcopy(self.registry)
        mutations = [lambda r: r["topics"]["bike"]["summary"].update(unresolved=1),
                     lambda r: r["topics"]["bike"].update(saved_outside_canonical=0),
                     lambda r: r["cohorts"]["initial"]["bike"].update(total=0),
                     lambda r: r["topics"]["bike"]["records"][0].update(decision=None)]
        # Ensure decision mutation selects the record that actually has evidence.
        mutations[-1] = lambda r: next(x for x in r["topics"]["bike"]["records"] if x["decision"]).update(decision=None)
        for mutation in mutations:
            self.registry = copy.deepcopy(original)
            mutation(self.registry)
            with self.assertRaises(ValueError):
                self.check()

    def test_duplicate_id_and_unknown_source_fail(self):
        original = copy.deepcopy(self.registry)
        self.registry["topics"]["bike"]["records"].append(self.registry["topics"]["bike"]["records"][0])
        with self.assertRaisesRegex(ValueError, "duplicate record"):
            self.check()
        self.registry = original
        self.registry["topics"]["bike"]["records"][0]["observations"][0]["source_id"] = "unknown"
        with self.assertRaisesRegex(ValueError, "invalid observation source"):
            self.check()

    def test_private_fields_are_rejected_at_each_output_level(self):
        original = copy.deepcopy(self.registry)
        for target in (lambda r: r, lambda r: r["topics"]["bike"],
                       lambda r: r["topics"]["bike"]["records"][0],
                       lambda r: r["topics"]["bike"]["sources"][0],
                       lambda r: r["topics"]["bike"]["records"][0]["observations"][0]):
            self.registry = copy.deepcopy(original)
            target(self.registry)["text"] = "private content"
            with self.assertRaisesRegex(ValueError, "schema fields"):
                self.check()

    def test_verification_membership_detects_changed_identity_even_if_counts_match(self):
        data = json.loads((self.root / self.verification).read_text())
        data[0]["record_id_hash"] = "sha256:" + "f" * 64
        self.write(self.verification, data)
        self.registry["topics"]["bike"]["sources"][0]["verification_sha256"] = self.digest(self.verification)
        with self.assertRaisesRegex(ValueError, "identities differ"):
            self.check()

    def test_scope_declared_source_cannot_be_omitted(self):
        path = "configs/adoption-sources.yaml"
        self.write(path, "legacy:\n  - {topic: bike, path: social-samples/old.json, kind: classified}\nexternal: []\n")
        self.registry["scope_config"]["sha256"] = self.digest(path)
        with self.assertRaisesRegex(ValueError, "declared source"):
            self.check()

    def test_public_presence_mutation_cannot_hide_an_opinion(self):
        present = next(r for r in self.registry["topics"]["bike"]["records"] if r["canonical_presence"])
        present["public_opinion_presence"] = False
        with self.assertRaisesRegex(ValueError, "public membership"):
            self.check()

    def test_public_presence_cannot_include_saved_only_record(self):
        absent = next(r for r in self.registry["topics"]["bike"]["records"] if not r["canonical_presence"])
        absent["public_opinion_presence"] = True
        with self.assertRaisesRegex(ValueError, "public membership"):
            self.check()

    def test_public_aggregate_mismatch_stops_even_with_updated_fingerprint(self):
        for counts in ({"collected_count": 2, "opinion_count": 1},
                       {"collected_count": 1, "opinion_count": 0}):
            self.write(self.public, counts)
            self.registry["topics"]["bike"]["public_sha256"] = self.digest(self.public)
            with self.assertRaisesRegex(ValueError, "public .* count disagrees"):
                self.check()

    def test_unknown_opinion_remains_unknown_and_is_not_public(self):
        present = next(r for r in self.registry["topics"]["bike"]["records"] if r["canonical_presence"])
        present["canonical_opinion"] = None
        present["public_opinion_presence"] = False
        self.write(self.public, {"collected_count": 1, "opinion_count": 0})
        self.registry["topics"]["bike"]["public_sha256"] = self.digest(self.public)
        self.assertEqual(self.check()["records"], 2)

    def test_unknown_fields_and_schema_boolean_are_not_accepted(self):
        self.registry["schema_version"] = True
        with self.assertRaises(ValueError):
            self.check()


if __name__ == "__main__":
    unittest.main()
