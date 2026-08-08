import unittest

from scripts.refresh_bukatsu_pilot import (
    identity,
    previous_collection_date,
    previous_wave,
    unique,
    validate_candidate,
)
from scripts.verification_data import make_verification_records


def row(tweet_id, *, issue="費用・家庭負担", fetched_at=None):
    return {
        "tweet_id": tweet_id,
        "url": f"https://x.com/example/status/{tweet_id}",
        "text": tweet_id,
        **({"fetched_at": fetched_at} if fetched_at else {}),
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


class PreviousWaveTest(unittest.TestCase):
    """潮目の比較対象を正典から導く。以前は日付と件数のべた書きだった。"""

    def waves(self):
        return (
            [row(f"a{i}", fetched_at="2026-07-23T01:00:00.000Z") for i in range(3)]
            + [row(f"b{i}", fetched_at="2026-08-02T01:00:00.000Z") for i in range(2)]
            + [row(f"c{i}", fetched_at="2026-08-08T01:00:00.000Z") for i in range(4)]
        )

    def test_picks_latest_collection_before_today(self):
        self.assertEqual(previous_collection_date(self.waves(), "2026-08-15"), "2026-08-08")

    def test_skips_the_wave_being_added_now(self):
        # 今回分がすでに正典へ入っていても、前回はその1つ前になる。
        self.assertEqual(previous_collection_date(self.waves(), "2026-08-08"), "2026-08-02")

    def test_returns_the_rows_of_that_day_only(self):
        previous_date, wave = previous_wave(self.waves(), "2026-08-15")
        self.assertEqual(previous_date, "2026-08-08")
        self.assertEqual(len(wave), 4)
        self.assertTrue(all(r["fetched_at"].startswith("2026-08-08") for r in wave))

    def test_ignores_rows_without_a_usable_date(self):
        rows = self.waves() + [row("x"), row("y", fetched_at="unknown")]
        self.assertEqual(previous_collection_date(rows, "2026-08-15"), "2026-08-08")

    def test_raises_when_no_earlier_collection_exists(self):
        rows = [row("a", fetched_at="2026-08-08T01:00:00.000Z")]
        with self.assertRaises(ValueError):
            previous_wave(rows, "2026-08-08")


if __name__ == "__main__":
    unittest.main()
