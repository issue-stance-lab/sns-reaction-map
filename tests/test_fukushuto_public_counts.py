import json
import unittest
from pathlib import Path

from scripts.build_fukushuto_arena import apply_public_counts


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/fukushuto-reaction-map.html"
PUBLIC = ROOT / "data/public/themes/fukushuto.json"


class FukushutoPublicCountsTests(unittest.TestCase):
    def test_public_counts_replace_page_aggregates(self) -> None:
        data = json.loads(PUBLIC.read_text(encoding="utf-8"))
        page = apply_public_counts(PAGE.read_text(encoding="utf-8"), PUBLIC)
        self.assertIn(f"公開投稿{data['collected_count']}件", page)
        self.assertIn(f"意見{data['opinion_count']}件 | セクター=論点", page)


if __name__ == "__main__":
    unittest.main()
