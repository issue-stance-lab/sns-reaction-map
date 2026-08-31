import json
import unittest
from pathlib import Path

from scripts.build_henoko_arena import apply_public_counts
from scripts.verify_theme_page import verify_theme_page


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/henoko-student-accident-reaction-map.html"
PUBLIC = ROOT / "data/public/themes/henoko-student-accident.json"


class HenokoPublicCountsTests(unittest.TestCase):
    def test_public_counts_replace_page_aggregates(self) -> None:
        data = json.loads(PUBLIC.read_text(encoding="utf-8"))
        page = apply_public_counts(PAGE.read_text(encoding="utf-8"), PUBLIC)
        self.assertIn(f"公開投稿{data['collected_count']}件", page)
        self.assertIn(f">{data['opinion_count']}件 | Hermes再分類", page)

    def test_zero_count_other_matches_verification_data(self) -> None:
        _lines, failures = verify_theme_page("henoko-student-accident")
        self.assertEqual(failures, 0)


if __name__ == "__main__":
    unittest.main()
