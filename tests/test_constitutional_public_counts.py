import json
import re
import unittest
from pathlib import Path

from scripts.build_constitutional_arena import apply_public_counts


ROOT = Path(__file__).resolve().parents[1]


class ConstitutionalPublicCountsTests(unittest.TestCase):
    def test_public_json_drives_page_level_counts(self):
        public_path = ROOT / "data/public/themes/constitutional-amendment.json"
        public = json.loads(public_path.read_text(encoding="utf-8"))
        page = apply_public_counts(
            (ROOT / "docs/constitutional-amendment-reaction-map.html").read_text(encoding="utf-8"),
            public_path,
        )
        self.assertIn(f'公開投稿{public["collected_count"]}件のうち、意見と判定した{public["opinion_count"]}件', page)
        self.assertIn(f'意見{public["opinion_count"]}件 | セクター=main_issue', page)
        self.assertRegex(page, rf'<td style="font-weight:900">{public["opinion_count"]}</td>')

