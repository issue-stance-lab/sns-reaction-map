"""生成AIと著作権の論点定義が、公開ページ・投票・Edge Function と一致していること。

2026-07-26 に新設した分類器が公開ページの論点を参照せずに書かれ、
ページ側7論点・分類器5〜6論点の二重状態が2週間続いた。同じことを繰り返さないための検査。
"""

import json
import re
import unittest
from pathlib import Path

from scripts import ai_copyright_taxonomy as tx

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "ai-copyright-reaction-map.html"


class AiCopyrightTaxonomyTest(unittest.TestCase):
    def setUp(self):
        self.html = PAGE.read_text(encoding="utf-8")

    def test_arena_sectors_match_taxonomy(self):
        block = re.search(r"const ISSUES=\[(.*?)\];", self.html, re.S)
        self.assertIsNotNone(block)
        sectors = tuple(re.findall(r"['\"]([^'\"]{2,30})['\"]", block.group(1)))
        self.assertEqual(sectors, tuple(tx.ARENA_LABELS[name] for name in tx.ISSUE_ORDER))

    def test_vote_definition_matches_taxonomy_and_edge_function(self):
        self.assertIn(f"var TOPIC='{tx.TOPIC_ID}'", self.html)
        issues = re.search(r"var VOTE_ISSUES=\[(.*?)\];", self.html, re.S)
        stances = re.search(r"var STANCES=\[(.*?)\];", self.html, re.S)
        issue_keys = re.findall(r"\bk:'([^']+)'", issues.group(1))
        stance_keys = re.findall(r"\bk:'([^']+)'", stances.group(1))

        # 投票の並びはアリーナと別（投票は独自の順序）。集合と数で照合する
        self.assertEqual(set(issue_keys), {tx.VOTE_ISSUE_LABELS[name] for name in tx.ISSUE_ORDER})
        self.assertEqual(set(stance_keys), {tx.VOTE_STANCE_LABELS[name] for name in tx.STANCE_ORDER})
        self.assertEqual(len(issue_keys), len(tx.ISSUE_ORDER))

        edge = (ROOT / "supabase" / "functions" / "cast-vote" / "index.ts").read_text(encoding="utf-8")
        self.assertRegex(edge, rf'"{re.escape(tx.TOPIC_ID)}":\s*{len(issue_keys) * len(stance_keys)}')

    def test_cards_reference_taxonomy_labels(self):
        config = json.loads((ROOT / "configs" / "ai-copyright-reaction-map.json").read_text(encoding="utf-8"))
        labels = {label for card in config["issue_counts"]["cards"] for label in card["main_issue"]}
        self.assertTrue(labels <= set(tx.ISSUE_ORDER), f"taxonomy 外のカード: {sorted(labels - set(tx.ISSUE_ORDER))}")
        self.assertEqual(config["issue_counts"]["basis"], "opinion")

    def test_page_has_no_labels_outside_taxonomy(self):
        """旧分類器の5論点が潮目ウィジェットなどに残っていないこと。"""
        retired = ["学習データ無断利用", "法制度整備", "利用者モラル・AI生成物"]
        found = [label for label in retired if label in self.html]
        self.assertEqual(found, [], f"旧taxonomyのラベルが残っている: {found}")


if __name__ == "__main__":
    unittest.main()
