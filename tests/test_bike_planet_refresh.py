"""山なみの外側に残る母数が、更新のたびに古いままにならないこと。"""
import sys
import copy
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from refresh_planet_section import _sync_bike_method_text
from build_bike_editorial_reread import apply_review_updates


class BikeMethodTextTests(unittest.TestCase):
    def test_real_page_updates_collected_and_opinions_separately(self):
        html = (ROOT / "docs/bike-blue-ticket-reaction-map.html").read_text()
        data = {"totals": {"collected": 504, "opinions": 392},
                "issues": [{"key": "その他", "count": 140}], "sample_period": "2026-06-27〜2026-09-12"}
        result = _sync_bike_method_text(html, data)
        self.assertIn("収集したSNS投稿504件のうち、分析対象の意見392件", result)
        self.assertIn("主要5論点252件に分類し、残る140件", result)
        self.assertIn("収集した504件のうち意見と判定した392件", result)
        self.assertEqual(result, _sync_bike_method_text(result, data))
        for marker in ("G-K10S4YCZFH", "ca-pub-2542211932832864", "supabase", "og:"):
            self.assertEqual(html.count(marker), result.count(marker))

    def test_missing_method_text_stops_instead_of_silent_stale_counts(self):
        with self.assertRaises(SystemExit):
            _sync_bike_method_text("<p>changed layout</p>", {
                "totals": {"collected": 504, "opinions": 392},
                "issues": [{"key": "その他", "count": 140}], "sample_period": "2026-06-27〜2026-09-12"})


class BikeCollectionReviewTests(unittest.TestCase):
    def setUp(self):
        self.data = {"population": {"その他": 1}, "sources": {}, "その他": {
            "items": [{"tweet_id": "old", "bucket": "abolish"}],
            "buckets": {"abolish": {"label": "制度そのものに反対", "count": 1}}}}
        self.rows = [{"tweet_id": "new", "text": "反対します", "is_opinion": True,
                      "classification": {"main_issue": "その他", "stance": "反対", "intensity": "high"}}]
        self.review = {"review_kind": "editorial_body_reread", "finalized_by": "editor",
            "read_at": "2026-09-12T12:00:00+00:00", "items": [{"tweet_id": "new",
            "body_reviewed": True, "review_kind": "editorial_body_reread", "independently_checked": True, "reviewer": "editor", "read_at": "2026-09-12T12:00:00+00:00", "reason_sha256": hashlib.sha256("明示的な反対".encode()).hexdigest(), "intensity": "high", "decision": "adopt", "text_sha256": hashlib.sha256("反対します".encode()).hexdigest(),
            "main_issue": "その他", "stance": "反対", "reason": "明示的な反対", "bucket": "abolish"}]}

    def test_update_survives_fresh_generation_and_keeps_old_record(self):
        first = apply_review_updates(copy.deepcopy(self.data), self.rows, {"wave.json": self.review})
        second = apply_review_updates(copy.deepcopy(self.data), self.rows, {"wave.json": self.review})
        self.assertEqual(first, second)
        self.assertEqual(first["population"]["その他"], 2)
        self.assertIn(self.data["その他"]["items"][0], first["その他"]["items"])

    def test_changed_body_duplicate_and_automatic_review_are_rejected(self):
        bad_body = copy.deepcopy(self.review)
        bad_body["items"][0]["text_sha256"] = "0" * 64
        duplicate = copy.deepcopy(self.review)
        duplicate["items"].append(copy.deepcopy(duplicate["items"][0]))
        automatic = {**self.review, "review_kind": "automated_classification"}
        unread = copy.deepcopy(self.review)
        unread["items"][0]["body_reviewed"] = False
        automated_item = copy.deepcopy(self.review)
        automated_item["items"][0]["review_kind"] = "automated_classification"
        for bad in (bad_body, duplicate, automatic, unread, automated_item):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                apply_review_updates(copy.deepcopy(self.data), self.rows, {"wave.json": bad})

    def test_held_post_in_candidate_is_rejected(self):
        held = copy.deepcopy(self.review)
        held["items"][0]["decision"] = "hold"
        with self.assertRaises(ValueError):
            apply_review_updates(copy.deepcopy(self.data), self.rows, {"wave.json": held})


class BikeVerificationTests(unittest.TestCase):
    def test_legacy_flags_and_nested_override_survive_without_raw_text(self):
        from build_bike_verification import build
        rows = [{"tweet_id": "1", "text": "private body", "is_opinion": True,
                 "classification": {"main_issue": "その他"}},
                {"tweet_id": "2", "text": "private body", "is_opinion": True,
                 "classification": {"is_opinion": False}}]
        original = copy.deepcopy(rows)
        safe = build(rows)
        self.assertEqual(sum(r["classification"]["is_opinion"] is True for r in safe), 1)
        self.assertEqual(rows, original)
        self.assertTrue(all(set(r) == {"record_id_hash", "classification"} for r in safe))
