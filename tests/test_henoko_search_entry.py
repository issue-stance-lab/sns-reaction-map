import json
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from scripts.build_henoko_arena import apply_search_entry_counts


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "henoko-student-accident-reaction-map.html"


class HenokoSearchEntryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PAGE.read_text(encoding="utf-8")
        cls.soup = BeautifulSoup(cls.source, "html.parser")

    def test_search_intent_is_visible_in_metadata_and_heading(self) -> None:
        self.assertIn("辺野古沖転覆事故", self.soup.title.string)
        self.assertIn("原因・報告書・安全管理", self.soup.title.string)
        description = self.soup.select_one('meta[name="description"]')["content"]
        for phrase in ("同志社国際高校", "確認済み", "未決定事項", "SNS上の意見"):
            self.assertIn(phrase, description)
        self.assertIn("辺野古沖転覆事故", self.soup.select_one("h1").get_text())

    def test_entry_separates_three_information_layers(self) -> None:
        layers = self.soup.select("#henoko-entry .henoko-layer")
        self.assertEqual(len(layers), 3)
        text = self.soup.select_one("#henoko-entry").get_text(" ", strip=True)
        for phrase in ("公表資料で確認済み", "このページでは確定できない", "世論調査ではなく反応サンプル"):
            self.assertIn(phrase, text)

    def test_routes_join_existing_page_sections(self) -> None:
        hrefs = {link["href"] for link in self.soup.select("#henoko-entry .henoko-entry__routes a")}
        self.assertEqual(hrefs, {"#bukatsu-background", "#bukatsu-check", "#henoko-faq", "#planet-block"})
        for href in hrefs:
            self.assertIsNotNone(self.soup.select_one(href))

    def test_faq_and_structured_data_match(self) -> None:
        questions = self.soup.select("#henoko-faq details")
        self.assertEqual(len(questions), 6)
        self.assertTrue(all(question.select_one("summary") for question in questions))
        schemas = [json.loads(node.string) for node in self.soup.select('script[type="application/ld+json"]')]
        faq = next(schema for schema in schemas if schema.get("@type") == "FAQPage")
        self.assertEqual(len(faq["mainEntity"]), 6)
        self.assertIn("ダンプカーと警備員", self.soup.select_one("#henoko-faq").get_text())

    def test_search_entry_styles_are_loaded_once(self) -> None:
        self.assertEqual(len(self.soup.select('link[href="henoko-search-entry.css?v=2"]')), 1)
        self.assertEqual(len(self.soup.select('script[src="henoko-search-entry.js?v=1"]')), 1)
        self.assertTrue((ROOT / "docs" / "henoko-search-entry.css").is_file())
        self.assertTrue((ROOT / "docs" / "henoko-search-entry.js").is_file())

    def test_issue_picker_controls_the_three_layers_and_mountain(self) -> None:
        tabs = self.soup.select('#henoko-entry [role="tab"][data-entry-issue]')
        self.assertEqual(len(tabs), 6)
        self.assertEqual(sum(tab.get("aria-selected") == "true" for tab in tabs), 1)
        self.assertEqual({tab["aria-controls"] for tab in tabs}, {"henoko-entry-layers"})
        layers = self.soup.select_one("#henoko-entry-layers")
        self.assertEqual(layers.get("role"), "tabpanel")
        bridge = self.soup.select_one("#henoko-entry-open-map[data-entry-issue]")
        self.assertIsNotNone(bridge)
        self.assertIn("この論点の山を見る", bridge.get_text(" ", strip=True))

    def test_opinion_count_follows_refresh_and_is_idempotent(self) -> None:
        updated = apply_search_entry_counts(self.source, 1234)
        block = updated.split("<!-- HENOKO_SEARCH_ENTRY_START -->", 1)[1].split(
            "<!-- HENOKO_SEARCH_ENTRY_END -->", 1
        )[0]
        self.assertIn("<!-- HENOKO_SEARCH_OPINIONS -->1,234<!-- HENOKO_SEARCH_OPINIONS_END -->", block)
        self.assertEqual(apply_search_entry_counts(updated, 1234), updated)


if __name__ == "__main__":
    unittest.main()
