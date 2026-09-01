from __future__ import annotations

import json
import unittest

from scripts import public_registry_common as prc


class ClaimVerificationContractTest(unittest.TestCase):
    def test_completed_and_not_started_are_distinguished(self) -> None:
        complete = prc.build_claim_verification("constitutional-amendment")
        self.assertEqual(complete["status"], "complete")
        self.assertEqual(len(complete["claims"]), 10)
        self.assertEqual({item["verdict"] for item in complete["claims"]}, {"fact", "gap", "miss"})
        self.assertTrue(all(item["matched_post_count"] > 0 for item in complete["claims"]))
        self.assertNotIn("tweet_id", json.dumps(complete, ensure_ascii=False))

        pending = prc.build_claim_verification("bukatsu-chiiki")
        self.assertEqual(pending, {"status": "not_started", "checked_on": None, "reviewer_type": None, "claims": []})

    def test_all_ten_themes_have_an_explicit_status(self) -> None:
        complete = {theme for theme in prc.CLAIM_AUDIT_SOURCES if prc.build_claim_verification(theme)["status"] == "complete"}
        self.assertEqual(complete, set(prc.CLAIM_AUDIT_SOURCES))
        self.assertEqual(
            {theme for theme in prc.QUESTIONS if prc.build_claim_verification(theme)["status"] == "not_started"},
            {"ai-copyright", "bukatsu-chiiki", "henoko-student-accident", "school-nickname-ban"},
        )
