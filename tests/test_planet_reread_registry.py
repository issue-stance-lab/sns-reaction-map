"""共通再読台帳とページ生成の境界。原文・外付けディスクは不要。"""
import copy
import hashlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_planet_data as bpd


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class PlanetRereadRegistryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patch = patch.object(bpd, "ROOT", self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.path = self.root / "data/verification/reread/example.json"
        self.path.parent.mkdir(parents=True)
        self.source = self.root / "source.json"
        self.source.write_text("{}")
        self.record = {"post_key": digest("1"), "baseline_text_sha256": digest("original"),
                       "main_issue": "issue", "is_opinion": True,
                       "review": {"kind": "editorial_body_reread", "bucket": "A"}}
        self.manifest = {"topic": "example", "sources": {"source.json": digest("{}")},
                         "records": [self.record]}
        self.statuses = [{"post_key": digest("1"), "statuses": ["reviewed_legacy"]}]
        self.assess = Mock(side_effect=lambda *_: {"records": self.statuses})
        self.module = patch.dict(sys.modules, {"reread_registry": types.SimpleNamespace(assess=self.assess)})
        self.module.start()
        self.addCleanup(self.module.stop)

    def write_manifest(self):
        self.path.write_text(json.dumps(self.manifest))

    def load(self):
        self.write_manifest()
        return bpd.load_reread_registry("example", [])

    def test_not_migrated_theme_retains_existing_checks(self):
        self.assertIsNone(bpd.load_reread_registry("example", []))
        self.assess.assert_not_called()
        bpd.validate_registry_membership(None, [{"tweet_id": "1"}], "issue")

    def test_unchanged_review_loads_and_matches_bucket(self):
        manifest = self.load()
        bpd.validate_registry_membership(manifest, [{"tweet_id": "1", "bucket": "A"}], "issue")
        self.assess.assert_called_once_with(self.manifest, [])

    def test_new_registry_without_reviews_can_have_no_sources(self):
        self.manifest["records"][0]["review"] = None
        self.manifest["sources"] = {}
        self.assertEqual(self.load(), self.manifest)

    def test_source_change_or_missing_source_stops(self):
        for content in ["changed", None]:
            with self.subTest(content=content):
                if content is None:
                    self.source.unlink()
                else:
                    self.source.write_text(content)
                with self.assertRaises(SystemExit):
                    self.load()
        self.assess.assert_not_called()

    def test_wrong_theme_empty_sources_and_outside_path_stop(self):
        for change in [{"topic": "wrong"}, {"sources": {}},
                       {"sources": {"../outside.json": digest("{}")}}]:
            with self.subTest(change=change):
                original = copy.deepcopy(self.manifest)
                self.manifest.update(change)
                with self.assertRaises(SystemExit):
                    self.load()
                self.manifest = original

    def test_each_reviewed_delta_stops_even_if_not_currently_configured(self):
        for status in ["body_changed", "issue_changed", "opinion_changed", "removed"]:
            with self.subTest(status=status):
                self.statuses[0]["statuses"] = [status]
                with self.assertRaises(SystemExit):
                    self.load()

    def test_unreviewed_changes_and_new_targets_do_not_erase_valid_reviews(self):
        self.manifest["records"].append({"post_key": digest("2"), "review": None})
        self.statuses.extend([{"post_key": digest("2"), "statuses": ["body_changed", "unreviewed"]},
                              {"post_key": digest("3"), "statuses": ["added", "unreviewed"]}])
        self.assertEqual(self.load(), self.manifest)

    def test_membership_rejects_unknown_id_wrong_bucket_issue_and_nonopinion(self):
        for record, change in [({"tweet_id": "2", "bucket": "A"}, {}),
                               ({"tweet_id": "1", "bucket": "B"}, {}),
                               ({"tweet_id": "1", "bucket": "A"}, {"main_issue": "other"}),
                               ({"tweet_id": "1", "bucket": "A"}, {"is_opinion": False}),
                               ({"tweet_id": "1", "bucket": "A"}, {"review": None}),
                               ({"tweet_id": "1", "bucket": "A"},
                                {"review": {"kind": "automated_classification", "bucket": "A"}})]:
            with self.subTest(record=record, change=change):
                manifest = copy.deepcopy(self.manifest)
                manifest["records"][0].update(change)
                with self.assertRaises(SystemExit):
                    bpd.validate_registry_membership(manifest, [record], "issue")

    def test_invalid_core_manifest_stops_as_build_error(self):
        self.assess.side_effect = ValueError("invalid evidence")
        with self.assertRaisesRegex(SystemExit, "invalid evidence"):
            self.load()


if __name__ == "__main__":
    unittest.main()
