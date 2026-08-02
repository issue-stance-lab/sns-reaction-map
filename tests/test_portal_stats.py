import json
import tempfile
import unittest
from datetime import date, timedelta
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
    def test_blank_yaml_scalar_does_not_consume_next_field(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "THEMES.yaml"
            registry.write_text(
                "themes:\n  blank:\n    title: Blank\n    refresh_at:\n"
                "    published_at: 2026-06-24\n",
                encoding="utf-8",
            )
            theme = parse_themes_yaml(registry)["blank"]
            self.assertIsNone(theme["refresh_at"])
            self.assertEqual(theme["published_at"], "2026-06-24")

    def test_all_published_themes_have_nonzero_canonical_samples(self):
        stats = compute_stats(parse_themes_yaml(), ROOT)

        self.assertEqual(stats["theme_count"], 11)
        self.assertEqual(len(stats["sample_counts"]), 11)
        self.assertTrue(all(count > 0 for count in stats["sample_counts"].values()))

    def test_top_page_matches_canonical_stats(self):
        _lines, failures = verify_top_page()

        self.assertEqual(failures, 0)

    def test_top_page_verification_fails_after_collect_deadline(self):
        # 予定日は運用で動くため、期待値は台帳から作る（日付をベタ書きすると
        # collect_at を動かすたびにこのテストが落ちる）。
        scheduled = {
            name: fields["collect_at"]
            for name, fields in parse_themes_yaml().items()
            if fields.get("collect_at")
        }
        self.assertTrue(scheduled, "collect_at を持つテーマが1つもない")
        latest = max(date.fromisoformat(value) for value in scheduled.values())

        lines, failures = verify_top_page(today=latest + timedelta(days=1))

        self.assertGreater(failures, 0)
        detail = ", ".join(f"{name}（{value}）" for name, value in scheduled.items())
        self.assertIn(f"NG  collect_at 期限超過: {detail}", lines)

    def test_unmanaged_topic_count_is_rejected(self):
        html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        html = html.replace(
            '<strong id="topic-count-ai-copyright">708</strong>',
            "708",
            1,
        )
        with tempfile.TemporaryDirectory() as directory:
            index_path = Path(directory) / "index.html"
            index_path.write_text(html, encoding="utf-8")

            lines, failures = verify_top_page(index_path=index_path)

        self.assertGreater(failures, 0)
        self.assertIn(
            "NG  ページ内の「○件」表示は全て id 付き: 708件",
            lines,
        )

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

    def test_all_past_refresh_dates_are_reported_as_overdue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "past.json").write_text(
                json.dumps([{"tweet_id": "real", "source": "yahoo_realtime"}]),
                encoding="utf-8",
            )
            theme = self._theme("past.json", "2026-07-31")

            stats = compute_stats({"past": theme}, root, today=date(2026, 8, 1))

            self.assertIsNone(stats["next_update"])
            self.assertEqual(stats["overdue_count"], 1)

    def test_past_collect_dates_are_reported_even_without_refresh_at(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "past.json").write_text(
                json.dumps([{"tweet_id": "real", "source": "yahoo_realtime"}]),
                encoding="utf-8",
            )
            theme = self._theme("past.json", None, collect_at="2026-07-31")

            stats = compute_stats({"past": theme}, root, today=date(2026, 8, 1))

            self.assertEqual(stats["overdue_collect"], {"past": date(2026, 7, 31)})
            self.assertEqual(stats["collect_at_missing"], [])

    def test_missing_collect_date_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "missing.json").write_text(
                json.dumps([{"tweet_id": "real", "source": "yahoo_realtime"}]),
                encoding="utf-8",
            )
            theme = self._theme("missing.json", None, collect_at=None)

            stats = compute_stats({"missing": theme}, root, today=date(2026, 8, 1))

            self.assertEqual(stats["overdue_collect"], {})
            self.assertEqual(stats["collect_at_missing"], ["missing"])

    def test_event_driven_theme_may_have_blank_collect_date(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "event.json").write_text(
                json.dumps([{"tweet_id": "real", "source": "yahoo_realtime"}]),
                encoding="utf-8",
            )
            theme = self._theme("event.json", None, collect_at=None)
            theme["collect_mode"] = "event-driven"

            stats = compute_stats({"event": theme}, root, today=date(2026, 8, 1))

            self.assertEqual(stats["collect_at_missing"], [])
            self.assertEqual(stats["collect_event_driven"], ["event"])

    @staticmethod
    def _theme(sample_file, refresh_at, *, collect_at="2026-08-02"):
        return {
            "title": "Test theme",
            "html": "docs/test.html",
            "published": True,
            "page_v3": True,
            "sample_file": sample_file,
            "sample_period": "unknown",
            "sample_source": "Yahooリアルタイム検索",
            "updated_at": "2026-07-29",
            "collect_at": collect_at,
            "collect_mode": "scheduled",
            "refresh_at": refresh_at,
        }


if __name__ == "__main__":
    unittest.main()
