"""再読の過大計上と、取得日不明を後日増分へ流す誤りを防ぐ。"""
import copy
import hashlib
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_planet_data as bpd


class RereadEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.posts = [
            {'tweet_id': 'a', 'classification': {'main_issue': '論点', 'is_opinion': True,
                                              'is_relevant': True}, 'fetched_at': '2026-08-01'},
            {'tweet_id': 'b', 'classification': {'main_issue': '論点'},
             'is_opinion': True, 'fetched_at': '2026-09-02'},
            {'tweet_id': 'c', 'classification': {'main_issue': '論点'}, 'is_opinion': True},
            {'tweet_id': 'd', 'classification': {'main_issue': '論点', 'is_opinion': False}},
        ]
        self.records = [{'tweet_id': 'a', 'bucket': 'A'}]
        self.buckets = {'A': {'label': '理由', 'count': 1}}

    def test_legacy_and_nested_flags_use_the_public_contract(self):
        self.assertEqual(bpd.unread_breakdown(self.posts, '論点', set(), date(2026, 9, 1)),
                         (1, 1, 1))

    def test_invalid_date_is_unknown_and_never_growth(self):
        self.posts[0]['fetched_at'] = '不明'
        self.assertEqual(bpd.unread_breakdown(self.posts, '論点', set(), date(2026, 9, 1)),
                         (0, 1, 2))

    def test_uncertain_read_date_never_certifies_growth(self):
        self.assertEqual(bpd.unread_breakdown(self.posts, '論点', {'a'}, date(2026, 9, 1),
                                             review_date_uncertain=True), (0, 0, 2))

    def test_legacy_two_way_call_stops_on_unknown(self):
        with self.assertRaises(SystemExit):
            bpd.split_unread(self.posts, '論点', set(), date(2026, 9, 1))

    def test_current_opinion_membership_and_counts(self):
        self.assertEqual(bpd.validate_reread_records(self.records, self.buckets,
                                                    self.posts, '論点', 3), {'a'})

    def test_duplicate_missing_wrong_issue_and_nonopinion_ids_stop(self):
        variants = [self.records * 2, [{'bucket': 'A'}],
                    [{'tweet_id': 'outside', 'bucket': 'A'}],
                    [{'tweet_id': 'd', 'bucket': 'A'}]]
        for records in variants:
            with self.subTest(records=records), self.assertRaises(SystemExit):
                bpd.validate_reread_records(records, self.buckets, self.posts, '論点', 3)

    def test_aggregate_count_cannot_mask_wrong_bucket(self):
        records = [{'tweet_id': 'a', 'bucket': 'B'}]
        with self.assertRaises(SystemExit):
            bpd.validate_reread_records(records, self.buckets, self.posts, '論点', 3)

    def test_automated_classification_cannot_count_as_body_review(self):
        for flag in [{'body_reviewed': False}, {'review_kind': 'automated_classification'}]:
            records = [dict(self.records[0], **flag)]
            with self.subTest(flag=flag), self.assertRaises(SystemExit):
                bpd.validate_reread_records(records, self.buckets, self.posts, '論点', 3)

    def test_public_count_drift_and_duplicate_canonical_stop(self):
        for posts, expected in [(self.posts, 4), (self.posts + [self.posts[0]], 4)]:
            with self.subTest(expected=expected), self.assertRaises(SystemExit):
                bpd.validate_reread_records(self.records, self.buckets, posts, '論点', expected)

    def test_body_change_is_detected_when_review_has_fingerprint(self):
        self.posts[0]["text"] = "before"
        self.records[0]["text_sha256"] = hashlib.sha256(b"before").hexdigest()
        bpd.validate_reread_records(self.records, self.buckets, self.posts, '論点', 3)
        self.posts[0]["text"] = "after"
        with self.assertRaises(SystemExit):
            bpd.validate_reread_records(self.records, self.buckets, self.posts, '論点', 3)

    def test_unknown_timing_blocks_gate(self):
        data = {'theme_id': 'bukatsu-chiiki', 'totals': {'opinions': 3},
                'issues': [{'count': 3, 'label': '論点', 'sub': {'status': 'reread',
                            'reread_count': 1, 'skipped_count': 0, 'grown_count': 0,
                            'unknown_timing_count': 2}}], 'ocean': {'sunk_continents': []}}
        failures = bpd.independence_gate(data, {'question': '問い'})
        self.assertTrue(any('時' in f and '不明' in f for f in failures))


class ConnectedThemeRegressionTest(unittest.TestCase):
    def test_bike_completed_reading_still_blocks_unresolved_classification(self):
        data = bpd.build("bike-blue-ticket")
        self.assertEqual(data["reread_summary"]["connected_editorial_count"], 468)
        self.assertEqual(data["reread_summary"]["not_connected_opinion_count"], 0)
        self.assertEqual(sum(i["sub"]["unknown_timing_count"] for i in data["issues"]), 0)
        cfg = bpd.yaml.safe_load((bpd.ROOT / "configs/planet/bike-blue-ticket.yaml").read_text())
        self.assertTrue(bpd.independence_gate(data, cfg))
        self.assertEqual(sum(i["sub"].get("classification_review_pending", 0) for i in data["issues"]), 95)
        self.assertTrue(all("分類" in x for x in bpd.independence_gate(data, cfg)))
        rendered = bpd.static_fallback(data)
        self.assertNotIn("enforcement_support", rendered)
        self.assertIn("賛成（取締り強化）", rendered)
        self.assertEqual(data["modes"][1]["label"], cfg["stances"][0]["label"])
        self.assertEqual(data["modes"][1]["id"], cfg["stances"][0]["key"])

    def test_elderly_flat_items_filter_each_issue_without_duplication(self):
        data = bpd.build("elderly-license-revocation")
        self.assertEqual(data["reread_summary"]["connected_editorial_count"], 250)
        reviewed = [i for i in data["issues"] if i["sub"]["status"] == "reread"]
        self.assertEqual(sorted(i["sub"]["reread_count"] for i in reviewed), [29, 221])
        self.assertTrue(all(i["sub"]["unread_count"] == 0 for i in reviewed))


if __name__ == '__main__':
    unittest.main()
