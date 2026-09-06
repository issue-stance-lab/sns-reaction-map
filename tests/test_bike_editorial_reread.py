"""自動分類を本文再読に見せた過大計上の回帰検査。"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_bike_editorial_reread import build
from build_bike_process_sections import write_provenance_records


def post(tid, issue, stance="反対（インフラ・制度優先）"):
    return {"tweet_id": tid, "is_opinion": True, "text": "fixture",
            "classification": {"main_issue": issue, "stance": stance,
                               "article_usable": True, "risk": "low"}}


class BikeEditorialRereadTests(unittest.TestCase):
    def setUp(self):
        self.samples = [post("opposition", "その他"), post("addition", "ルール曖昧・不信"),
                        post("automatic", "取締り強化賛成", "賛成（取締り強化支持）")]
        self.opposition = {"assigned_at": "2026-08-17", "buckets": {"place": ["opposition"]}}
        self.supplement = {"review_kind": "editorial_body_reread", "read_at": "2026-09-06",
                           "source_ref": "source-fixture", "items": [{"tweet_id": "addition", "bucket": "distrust"}]}

    def test_automatic_support_is_not_promoted_and_other_issue_is_connected(self):
        data = build(self.samples, self.opposition, self.supplement)
        self.assertEqual(data["population"], {"その他": 1, "ルール曖昧・不信": 1, "取締り強化賛成": 0})
        self.assertEqual(data["その他"]["items"][0]["source_id"], "opposition")
        self.assertEqual(data["ルール曖昧・不信"]["items"][0]["source_id"], "supplement")
        self.assertNotIn("summary", data["その他"]["items"][0])

    def test_source_kind_and_duplicate_ids_cannot_inflate_reread_count(self):
        wrong_kind = copy.deepcopy(self.supplement)
        wrong_kind["review_kind"] = "automated_classification"
        with self.assertRaises(ValueError):
            build(self.samples, self.opposition, wrong_kind)
        duplicate = copy.deepcopy(self.supplement)
        duplicate["items"][0]["tweet_id"] = "opposition"
        with self.assertRaises(ValueError):
            build(self.samples, self.opposition, duplicate)

    def test_outside_canonical_and_nonopinion_are_rejected(self):
        outside = copy.deepcopy(self.supplement)
        outside["items"][0]["tweet_id"] = "missing"
        with self.assertRaises(ValueError):
            build(self.samples, self.opposition, outside)
        samples = copy.deepcopy(self.samples)
        samples[1]["is_opinion"] = False
        with self.assertRaises(ValueError):
            build(samples, self.opposition, self.supplement)

    def test_number_provenance_retains_automatic_counts_but_marks_no_body_review(self):
        with tempfile.TemporaryDirectory() as d:
            write_provenance_records(self.samples, self.opposition, {"claims": {}}, Path(d))
            rows = json.loads((Path(d) / "bike-blue-ticket-reread.json").read_text())
        rows = {r["tweet_id"]: r for r in rows}
        self.assertEqual(set(rows), {"opposition", "automatic"})
        self.assertFalse(rows["automatic"]["body_reviewed"])
        self.assertEqual(rows["automatic"]["review_kind"], "automated_classification")
        self.assertTrue(rows["opposition"]["body_reviewed"])
        self.assertEqual(rows["opposition"]["review_kind"], "editorial_body_reread")

    def test_checked_in_ledger_is_reproducible_from_editorial_sources(self):
        load = lambda p: json.loads((ROOT / p).read_text())
        data = build(load("social-samples/bike-blue-ticket_2d_classified.json"),
                     load("data/bike-blue-ticket_opposition_reread.json"),
                     load("data/bike-blue-ticket_editorial-supplement.json"))
        saved = load("data/bike-blue-ticket_issues-reread.json")
        saved.pop("input_sha256")
        self.assertEqual(data, saved)


if __name__ == "__main__":
    unittest.main()
