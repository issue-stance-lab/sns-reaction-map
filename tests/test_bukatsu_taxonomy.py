import json
import re
import unittest

from scripts import bukatsu_taxonomy
from scripts import classify_bukatsu_arena_hermes
from scripts import update_bukatsu_tide


class BukatsuTaxonomyTest(unittest.TestCase):
    def test_all_data_processors_share_taxonomy(self):
        self.assertEqual(classify_bukatsu_arena_hermes.ISSUES, bukatsu_taxonomy.ISSUES)
        self.assertEqual(classify_bukatsu_arena_hermes.STANCES, bukatsu_taxonomy.STANCES)
        self.assertEqual(update_bukatsu_tide.ISSUES, bukatsu_taxonomy.ISSUES)
        self.assertEqual(update_bukatsu_tide.STANCES, bukatsu_taxonomy.STANCES)

    def test_published_vote_mapping_remains_v1_with_21_choices(self):
        html = (bukatsu_taxonomy.ROOT / "docs" / "bukatsu-chiiki-reaction-map.html").read_text(encoding="utf-8")
        self.assertIn(f"var TOPIC='{bukatsu_taxonomy.TOPIC_ID}'", html)
        issue_block = re.search(r"var VOTE_ISSUES=\[(.*?)\];", html, re.DOTALL)
        stance_block = re.search(r"var STANCES=\[(.*?)\];", html, re.DOTALL)
        self.assertIsNotNone(issue_block)
        self.assertIsNotNone(stance_block)
        published_issues = re.findall(r"\{k:'([^']+)'", issue_block.group(1))
        published_stances = re.findall(r"\{k:'([^']+)'", stance_block.group(1))
        configured_issues = [item.get("vote_label", item["label"]) for item in bukatsu_taxonomy.VOTE_ISSUES]
        configured_stances = [item["label"] for item in bukatsu_taxonomy.VOTE_STANCES]
        self.assertEqual(published_issues, configured_issues)
        self.assertEqual(published_stances, configured_stances)
        self.assertEqual(len(published_issues) * len(published_stances), 21)

        edge = (bukatsu_taxonomy.ROOT / "supabase" / "functions" / "cast-vote" / "index.ts").read_text(encoding="utf-8")
        self.assertRegex(edge, rf'"{re.escape(bukatsu_taxonomy.TOPIC_ID)}":\s*21')

    def test_refresh_config_has_ten_queries(self):
        themes = (bukatsu_taxonomy.ROOT / "THEMES.yaml").read_text(encoding="utf-8")
        self.assertIn("refresh_config: configs/topics/bukatsu-chiiki-v2.yaml", themes)
        config = (bukatsu_taxonomy.ROOT / "configs" / "topics" / "bukatsu-chiiki-v2.yaml").read_text(encoding="utf-8")
        queries = re.search(r"fetch_queries:\n((?:  - .*\n)+)", config)
        self.assertIsNotNone(queries)
        self.assertEqual(len(re.findall(r"^  - ", queries.group(1), re.MULTILINE)), 10)


if __name__ == "__main__":
    unittest.main()
