import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.sync_portal_stats import (
    ROOT,
    PortalStatsError,
    compute_stats,
    count_sample_records,
    parse_themes_yaml,
    update_html,
)
from scripts.verify_top_page import verify_top_page


class PortalStatsTest(unittest.TestCase):
    def test_all_published_themes_have_nonzero_canonical_samples(self):
        stats = compute_stats(parse_themes_yaml(), ROOT)

        self.assertEqual(stats["theme_count"], 11)
        self.assertEqual(len(stats["sample_counts"]), 11)
        self.assertTrue(all(count > 0 for count in stats["sample_counts"].values()))

    def test_top_page_matches_canonical_stats(self):
        _lines, failures = verify_top_page()

        self.assertEqual(failures, 0)

    def test_zero_record_sample_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "empty.json"
            sample.write_text(json.dumps([]), encoding="utf-8")

            with self.assertRaisesRegex(PortalStatsError, "0件"):
                count_sample_records(root, "empty-theme", "empty.json")

    def test_empty_replacement_is_rejected(self):
        stats = compute_stats(parse_themes_yaml(), ROOT)

        with self.assertRaisesRegex(PortalStatsError, "置換が0件"):
            update_html("<html></html>", stats)

    def test_synthetic_sample_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample = root / "synthetic.json"
            sample.write_text(
                json.dumps([{"tweet_id": "synthetic_0001", "source": "synthetic"}]),
                encoding="utf-8",
            )
            theme = self._theme("synthetic.json", "2026-08-02")

            with self.assertRaisesRegex(PortalStatsError, "synthetic"):
                compute_stats({"theme": theme}, root, today=date(2026, 8, 1))

    def test_blank_refresh_at_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for filename in ("blank.json", "future.json"):
                (root / filename).write_text(
                    json.dumps([{"tweet_id": filename, "source": "yahoo_realtime"}]),
                    encoding="utf-8",
                )
            themes = {
                "blank": self._theme("blank.json", None),
                "future": self._theme("future.json", "2026-08-02"),
            }

            stats = compute_stats(themes, root, today=date(2026, 8, 1))

            self.assertEqual(stats["next_update"], date(2026, 8, 2))
            self.assertEqual(stats["refresh_at_missing"], ["blank"])

    def test_all_past_refresh_dates_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "past.json").write_text(
                json.dumps([{"tweet_id": "real", "source": "yahoo_realtime"}]),
                encoding="utf-8",
            )
            theme = self._theme("past.json", "2026-07-31")

            with self.assertRaisesRegex(PortalStatsError, "今日.*以降"):
                compute_stats({"past": theme}, root, today=date(2026, 8, 1))

    @staticmethod
    def _theme(sample_file, refresh_at):
        return {
            "published": True,
            "page_v3": True,
            "sample_file": sample_file,
            "sample_period": "unknown",
            "sample_source": "Yahooリアルタイム検索",
            "updated_at": "2026-07-29",
            "refresh_at": refresh_at,
        }


if __name__ == "__main__":
    unittest.main()
