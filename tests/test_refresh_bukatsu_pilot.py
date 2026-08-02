import unittest

from scripts.refresh_bukatsu_pilot import identity, unique, validate_candidate
from scripts.verification_data import make_verification_records


def row(tweet_id, *, issue="費用・家庭負担"):
    return {
        "tweet_id": tweet_id,
        "url": f"https://x.com/example/status/{tweet_id}",
        "text": tweet_id,
        "classification": {
            "main_issue": issue,
            "stance": "移行支持",
            "is_relevant": True,
            "is_opinion": True,
            "confidence": 0.9,
        },
    }


class RefreshBukatsuPilotTest(unittest.TestCase):
    def test_verification_history_preserves_wave_without_post_data(self):
        safe = make_verification_records([row("123")])
        self.assertEqual(len(safe), 1)
        self.assertNotIn("123", str(safe))
        self.assertNotIn("https://", str(safe))

    def test_identity_prefers_tweet_id(self):
        self.assertEqual(identity({"tweet_id": "123", "url": "https://invalid"}), "tweet:123")

    def test_unique_is_idempotent(self):
        rows = [row("1"), row("1"), row("2")]
        self.assertEqual([item["tweet_id"] for item in unique(rows)], ["1", "2"])
        self.assertEqual(unique(unique(rows)), unique(rows))

    def test_candidate_invariants(self):
        current = [row("1")]
        raw = [row("1"), row("2")]
        new = [row("2")]
        classified = [row("2")]
        candidate = current + classified
        from scripts.refresh_bukatsu_pilot import PAGE
        page = PAGE.read_text(encoding="utf-8")
        report = validate_candidate(current, raw, new, classified, candidate, page)
        self.assertEqual(report["duplicates"], 1)
        self.assertEqual(report["new"], 1)
        self.assertTrue(all(report["checks"].values()))


if __name__ == "__main__":
    unittest.main()
