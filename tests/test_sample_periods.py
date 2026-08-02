import json
import unittest

from scripts.sync_portal_stats import ROOT
from scripts.verify_sample_periods import EVIDENCE, expected_period, verify


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
