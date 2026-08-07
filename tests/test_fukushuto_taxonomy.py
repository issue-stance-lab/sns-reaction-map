"""副首都テーマの論点体系が、分類器・カード定義・ページ・Edge Function で一致することを見る。

2026-07-26 に新設した Hermes 分類器が公開ページの論点定義を参照せず、切り口ごと分岐した
（公開側7論点・分類器5論点）。件数の検査は両方とも通ってしまうため、ラベルと並びを別に見る。
"""

import json
import re
import unittest

from scripts import classify_fukushuto_arena_hermes as classifier
from scripts import fukushuto_taxonomy as taxonomy


def read(*parts):
    return (taxonomy.ROOT.joinpath(*parts)).read_text(encoding="utf-8")


class FukushutoTaxonomyTest(unittest.TestCase):
    def setUp(self):
        self.html = read("docs", "fukushuto-reaction-map.html")

    def test_classifier_uses_the_shared_definition(self):
        self.assertEqual(classifier.ISSUES, taxonomy.ISSUES)
        self.assertEqual(classifier.STANCES, taxonomy.STANCES)

    def test_issue_defs_cover_every_issue_exactly_once(self):
        names = [name for name, _ in taxonomy.ISSUE_DEFS]
        self.assertEqual(sorted(names), sorted(taxonomy.ISSUE_ORDER))
        self.assertEqual(sorted(taxonomy.VOTE_ISSUE_ORDER), sorted(taxonomy.ISSUE_ORDER))
        self.assertEqual(names[-1], taxonomy.OTHER, "「その他」は説明順の最後に置く")
        stance_names = [name for name, _ in taxonomy.STANCE_DEFS]
        self.assertEqual(sorted(stance_names), sorted(taxonomy.STANCE_ORDER))

    def test_prompt_menu_is_generated_from_the_definition(self):
        prompt = classifier.prompt_for([{"text": "副首都の定義が法案に書いていない"}])
        for name, description in taxonomy.ISSUE_DEFS:
            self.assertIn(f"{name} ─ {description}", prompt)
        for name, description in taxonomy.STANCE_DEFS:
            self.assertIn(f"{name} ─ {description}", prompt)
        self.assertIn(f"main_issue（完全一致{len(taxonomy.ISSUE_ORDER)}択）", prompt)
        example = json.loads(re.search(r'\{"id":0,.*?"risk":"low"\}', prompt).group(0))
        self.assertIn(example["main_issue"], taxonomy.ISSUES)
        self.assertIn(example["stance"], taxonomy.STANCES)

    def test_published_arena_sectors_match_the_issue_order(self):
        block = re.search(r"const ISSUES = \[(.*?)\];", self.html, re.DOTALL)
        self.assertIsNotNone(block)
        published = re.findall(r"\{k:'([^']+)'", block.group(1))
        self.assertEqual(published, list(taxonomy.ISSUE_ORDER))

    def test_published_vote_choices_match_the_vote_order(self):
        self.assertIn(f"var TOPIC='{taxonomy.TOPIC_ID}'", self.html)
        issue_block = re.search(r"var VOTE_ISSUES=\[(.*?)\];", self.html, re.DOTALL)
        stance_block = re.search(r"var STANCES=\[(.*?)\];", self.html, re.DOTALL)
        self.assertIsNotNone(issue_block)
        self.assertIsNotNone(stance_block)
        published_issues = re.findall(r"\{k:'([^']+)'", issue_block.group(1))
        published_stances = re.findall(r"\{k:'([^']+)'", stance_block.group(1))
        self.assertEqual(
            published_issues,
            [taxonomy.VOTE_ISSUE_LABELS[name] for name in taxonomy.VOTE_ISSUE_ORDER],
        )
        self.assertEqual(
            published_stances,
            [taxonomy.VOTE_STANCE_LABELS[name] for name in taxonomy.STANCE_ORDER],
        )

    def test_published_vote_to_arena_mapping_matches(self):
        published = re.search(r"var V2I=\[([\d,]+)\];", self.html)
        self.assertIsNotNone(published)
        self.assertEqual(
            [int(value) for value in published.group(1).split(",")],
            list(taxonomy.VOTE_ISSUE_TO_ARENA_INDEX),
        )

    def test_edge_function_choice_count_matches_the_vote_grid(self):
        expected = len(taxonomy.VOTE_ISSUE_ORDER) * len(taxonomy.STANCE_ORDER)
        self.assertEqual(expected, 21)
        edge = read("supabase", "functions", "cast-vote", "index.ts")
        self.assertRegex(edge, rf'"{re.escape(taxonomy.TOPIC_ID)}":\s*{expected}')
        self.assertEqual(taxonomy.vote_choice_index(taxonomy.VOTE_ISSUE_ORDER[0], taxonomy.STANCE_ORDER[0]), 0)
        self.assertEqual(
            taxonomy.vote_choice_index(taxonomy.VOTE_ISSUE_ORDER[-1], taxonomy.STANCE_ORDER[-1]),
            expected - 1,
        )

    def test_issue_cards_reference_only_known_issues(self):
        config = json.loads(read("configs", "fukushuto-reaction-map.json"))
        cards = config["issue_counts"]["cards"]
        referenced = [name for card in cards for name in card["main_issue"]]
        self.assertEqual(sorted(referenced), sorted(set(taxonomy.ISSUE_ORDER) - {taxonomy.OTHER}))

    def test_canonical_labels_stay_inside_the_definition(self):
        theme = re.search(r"\n  fukushuto:\n(.*?)\n  \w", read("THEMES.yaml"), re.DOTALL)
        self.assertIsNotNone(theme)
        sample_file = re.search(r"sample_file: (\S+)", theme.group(1)).group(1)
        rows = json.loads(read(*sample_file.split("/")))
        labels = {row.get("main_issue") for row in rows if row.get("main_issue")}
        self.assertTrue(labels)
        self.assertEqual(labels - taxonomy.ISSUES, set())

    def test_arena_coordinates_stay_inside_the_published_range(self):
        for stance in taxonomy.STANCE_ORDER:
            for intensity in sorted(taxonomy.INTENSITIES):
                x = taxonomy.arena_x(stance, intensity)
                e = taxonomy.arena_e(intensity)
                self.assertLessEqual(abs(x), taxonomy.COORD_LIMIT)
                self.assertLessEqual(abs(e), taxonomy.COORD_LIMIT)
                # ページの colorOf() は ±0.5 を境に赤／青／灰へ塗り分ける。
                if stance == taxonomy.NEUTRAL_STANCE:
                    self.assertLess(abs(x), taxonomy.COLOR_THRESHOLD)
                elif stance == "法案反対":
                    self.assertLessEqual(x, -taxonomy.COLOR_THRESHOLD)
                else:
                    self.assertGreaterEqual(x, taxonomy.COLOR_THRESHOLD)

    def test_page_color_thresholds_have_not_moved(self):
        color = re.search(r"function colorOf\(p\)\{return ([^}]+)\}", self.html)
        self.assertIsNotNone(color)
        self.assertIn(f"p.x>={taxonomy.COLOR_THRESHOLD}", color.group(1))
        self.assertIn(f"p.x<=-{taxonomy.COLOR_THRESHOLD}", color.group(1))


if __name__ == "__main__":
    unittest.main()
