import json
import unittest

from scripts.sync_portal_stats import ROOT
from scripts.verify_sample_periods import EVIDENCE, expected_period, stale_owner_period, verify


class OwnerConfirmedPeriodTests(unittest.TestCase):
    """オーナーが期間を確定させるテーマは、--promote で期間が自動更新されない。

    直し忘れると、ページの取得期間が半月前のまま公開される
    （2026-08-17 の自転車青切符で実際に起きた）。
    """

    def test_range_ending_before_the_last_update_is_rejected(self):
        reason = stale_owner_period(
            "2026-06-27〜2026-07-26", {"updated_at": "2026-08-17"}
        )
        self.assertIn("2026-06-27〜2026-07-26", reason)
        self.assertIn("2026-08-17", reason)

    def test_range_ending_on_the_last_update_is_accepted(self):
        self.assertEqual(
            stale_owner_period("2026-06-27〜2026-08-17", {"updated_at": "2026-08-17"}), ""
        )

    def test_single_date_is_out_of_scope(self):
        """開始日だけの表記は範囲を持たないので、この検査の対象にしない。"""
        self.assertEqual(stale_owner_period("2026-06-27", {"updated_at": "2026-08-16"}), "")

    def test_missing_updated_at_is_out_of_scope(self):
        self.assertEqual(stale_owner_period("2026-06-27〜2026-07-26", {}), "")


class SamplePeriodTests(unittest.TestCase):
    def test_partial_dates_require_unknown(self):
        self.assertEqual(
            expected_period({"records": 2, "dated_records": 1, "missing_records": 1, "min": "2026-01-01", "max": "2026-01-01"}),
            "unknown",
        )

    def test_registry_matches_committed_evidence(self):
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(verify(evidence), 0)


if __name__ == "__main__":
    unittest.main()
