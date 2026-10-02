import json
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from scripts.fukushuto_search_entry import ENTRY_TOPICS, FAQS, apply


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "fukushuto-reaction-map.html"


class FukushutoSearchEntryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PAGE.read_text(encoding="utf-8")
        cls.soup = BeautifulSoup(cls.source, "html.parser")

    def test_search_intent_is_visible_in_title_and_description(self) -> None:
        self.assertIn("副首都法とは", self.soup.title.string)
        self.assertIn("大阪は決定", self.soup.title.string)
        description = self.soup.select_one('meta[name="description"]')["content"]
        for phrase in ("候補地", "大阪", "メリット・デメリット", "費用"):
            self.assertIn(phrase, description)

    def test_progress_has_one_current_step_and_no_designation(self) -> None:
        steps = self.soup.select("#fukushuto-now .fuk-status li")
        self.assertEqual(len(steps), 3)
        self.assertEqual(len(self.soup.select('#fukushuto-now .fuk-status [aria-current="step"]')), 1)
        self.assertIn("指定前", steps[-1].get_text(" ", strip=True))

    def test_four_questions_are_keyboard_tabs_with_matching_panels(self) -> None:
        tabs = self.soup.select("#fuk-entry-switcher [role=tab]")
        panels = self.soup.select("#fuk-entry-switcher [role=tabpanel]")
        self.assertEqual(len(tabs), len(ENTRY_TOPICS))
        self.assertEqual(len(panels), len(ENTRY_TOPICS))
        self.assertEqual({tab["aria-controls"] for tab in tabs}, {panel["id"] for panel in panels})
        self.assertEqual(sum(tab["aria-selected"] == "true" for tab in tabs), 1)

    def test_each_answer_connects_to_a_real_mountain_issue(self) -> None:
        buttons = self.soup.select("#fuk-entry-switcher [data-fuk-mountain]")
        expected = {topic["issue_id"] for topic in ENTRY_TOPICS}
        self.assertEqual({button["data-fuk-mountain"] for button in buttons}, expected)
        for issue_id in expected:
            self.assertIsNotNone(self.soup.select_one("#fb-" + issue_id))

    def test_faq_visible_and_structured_data_match(self) -> None:
        details = self.soup.select("#fukushuto-faq details")
        self.assertEqual(len(details), len(FAQS))
        payload = json.loads(self.soup.select_one("#fukushuto-faq-json-ld").string)
        self.assertEqual(payload["@type"], "FAQPage")
        self.assertEqual(len(payload["mainEntity"]), len(FAQS))
        self.assertEqual(
            [item["name"] for item in payload["mainEntity"]],
            [question for question, _ in FAQS],
        )

    def test_assets_are_loaded_once(self) -> None:
        self.assertEqual(len(self.soup.select('link[href="fukushuto-search-entry.css?v=1"]')), 1)
        self.assertEqual(len(self.soup.select('script[src="fukushuto-search-entry.js?v=1"][defer]')), 1)

    def test_entry_refresh_is_idempotent_and_updates_count(self) -> None:
        updated = apply(self.source, 2345)
        block = updated.split("<!-- FUKUSHUTO_SEARCH_ENTRY_START -->", 1)[1].split(
            "<!-- FUKUSHUTO_SEARCH_ENTRY_END -->", 1
        )[0]
        self.assertEqual(
            block.count("<!-- FUKUSHUTO_SEARCH_OPINIONS -->2,345<!-- FUKUSHUTO_SEARCH_OPINIONS_END -->"),
            1,
        )
        self.assertEqual(apply(updated, 2345), updated)


if __name__ == "__main__":
    unittest.main()
