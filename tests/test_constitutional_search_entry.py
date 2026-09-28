import json
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from scripts.build_constitutional_arena import apply_search_entry_counts


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "constitutional-amendment-reaction-map.html"


class ConstitutionalSearchEntryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PAGE.read_text(encoding="utf-8")
        cls.soup = BeautifulSoup(cls.source, "html.parser")

    def test_search_intent_is_visible_in_title_and_description(self) -> None:
        self.assertIn("何が変わる", self.soup.title.string)
        description = self.soup.select_one('meta[name="description"]')["content"]
        for phrase in ("9条", "緊急事態条項", "国民投票", "賛成・反対"):
            self.assertIn(phrase, description)

    def test_change_lens_has_four_keyboard_tabs_and_matching_panels(self) -> None:
        tabs = self.soup.select("#change-lens [role=tab]")
        panels = self.soup.select("#change-lens [role=tabpanel]")
        self.assertEqual(len(tabs), 4)
        self.assertEqual(len(panels), 4)
        self.assertEqual(
            {tab["aria-controls"] for tab in tabs},
            {panel["id"] for panel in panels},
        )
        self.assertEqual(sum(tab["aria-selected"] == "true" for tab in tabs), 1)

    def test_current_rules_and_proposals_are_labeled_separately(self) -> None:
        labels = {node.get_text(" ", strip=True) for node in self.soup.select("#change-lens .status-chip")}
        self.assertEqual(labels, {"政党の提案", "国会で議論中", "現行の手続き", "SNS反応サンプル"})
        self.assertIn("最低投票率の規定はありません", self.soup.select_one("#lens-panel-referendum").get_text())

    def test_styles_and_behavior_are_loaded_once(self) -> None:
        self.assertEqual(len(self.soup.select('link[href="constitutional-search-entry.css?v=2"]')), 1)
        self.assertEqual(len(self.soup.select('script[src="constitutional-search-entry.js?v=2"][defer]')), 1)
        self.assertTrue((ROOT / "docs" / "constitutional-search-entry.css").is_file())
        self.assertTrue((ROOT / "docs" / "constitutional-search-entry.js").is_file())

    def test_tab_switch_does_not_request_automatic_scrolling(self) -> None:
        script = (ROOT / "docs" / "constitutional-search-entry.js").read_text(encoding="utf-8")
        self.assertNotIn("scrollIntoView", script)
        self.assertIn("focus({ preventScroll: true })", script)

    def test_entry_background_uses_the_same_centered_page_width(self) -> None:
        css = (ROOT / "docs" / "constitutional-search-entry.css").read_text(encoding="utf-8")
        self.assertIn("width:100%", css)
        self.assertIn("max-width:1180px", css)
        self.assertIn("margin-left:auto", css)
        self.assertIn("margin-right:auto", css)

    def test_article_metadata_matches_visible_heading(self) -> None:
        article = json.loads(self.soup.select_one('script[type="application/ld+json"]').string)
        self.assertIn("何が変わる", article["headline"])
        self.assertEqual(article["dateModified"], "2026-09-26")

    def test_faq_uses_progressive_disclosure(self) -> None:
        questions = self.soup.select("#constitutional-faq details")
        self.assertEqual(len(questions), 5)
        self.assertTrue(all(question.select_one("summary") for question in questions))
        self.assertIn("最低投票率", self.soup.select_one("#constitutional-faq").get_text())

    def test_opinion_count_follows_canonical_refresh_and_is_idempotent(self) -> None:
        updated = apply_search_entry_counts(self.source, 2345)
        block = updated.split("<!-- SEARCH_ENTRY_START -->", 1)[1].split("<!-- SEARCH_ENTRY_END -->", 1)[0]
        self.assertEqual(block.count("<!-- SEARCH_OPINIONS -->2,345<!-- SEARCH_OPINIONS_END -->"), 2)
        self.assertNotIn("1,756", block)
        self.assertEqual(apply_search_entry_counts(updated, 2345), updated)


if __name__ == "__main__":
    unittest.main()
