import json
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from scripts.build_consumption_tax_page import apply_search_entry


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "consumption-tax-cut-reaction-map.html"


class ConsumptionTaxSearchEntryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PAGE.read_text(encoding="utf-8")
        cls.soup = BeautifulSoup(cls.source, "html.parser")

    def test_search_intent_is_visible_in_title_and_description(self) -> None:
        self.assertIn("いつから", self.soup.title.string)
        description = self.soup.select_one('meta[name="description"]')["content"]
        for phrase in ("2027年4月", "1％", "法律成立前", "財源", "給付付き税額控除"):
            self.assertIn(phrase, description)

    def test_status_separates_cabinet_outline_from_law(self) -> None:
        stage = self.soup.select_one("#tax-brief-stage").get_text(" ", strip=True)
        self.assertIn("大綱を閣議決定", stage)
        self.assertIn("国会で成立", stage)
        caution = self.soup.select_one("#tax-brief .tax-desk__caution").get_text(" ", strip=True)
        self.assertIn("法律は未成立", caution)

    def test_four_keyboard_tabs_share_one_live_panel(self) -> None:
        tabs = self.soup.select("#tax-brief [role=tab]")
        self.assertEqual(len(tabs), 4)
        self.assertEqual({tab["data-tax-tab"] for tab in tabs}, {"food", "takeout", "eatin", "alcohol"})
        self.assertEqual(sum(tab["aria-selected"] == "true" for tab in tabs), 1)
        self.assertTrue(all(tab["aria-controls"] == "tax-case-panel" for tab in tabs))
        panel = self.soup.select_one("#tax-case-panel")
        self.assertEqual(panel["aria-live"], "polite")
        self.assertEqual(panel["aria-labelledby"], "tax-tab-food")

    def test_receipt_example_has_scope_warning(self) -> None:
        receipt = self.soup.select_one("#tax-brief .tax-receipt").get_text(" ", strip=True)
        self.assertIn("税率だけで比べた例", receipt)
        self.assertIn("1,080円", receipt)
        caution = self.soup.select_one("#tax-brief .tax-desk__caution").get_text(" ", strip=True)
        self.assertIn("実際の販売価格を保証しません", caution)

    def test_faq_uses_progressive_disclosure(self) -> None:
        questions = self.soup.select("#tax-faq details")
        self.assertEqual(len(questions), 5)
        text = self.soup.select_one("#tax-faq").get_text(" ", strip=True)
        for phrase in ("0％", "外食", "新聞", "財源", "給付付き税額控除"):
            self.assertIn(phrase, text)

    def test_styles_behavior_and_generator_are_idempotent(self) -> None:
        self.assertEqual(len(self.soup.select('link[href="consumption-tax-search-entry.css?v=3"]')), 1)
        self.assertEqual(len(self.soup.select('script[src="consumption-tax-search-entry.js?v=1"][defer]')), 1)
        css = (ROOT / "docs" / "consumption-tax-search-entry.css").read_text(encoding="utf-8")
        self.assertIn("max-width: 1180px", css)
        self.assertIn("width: calc(100% - 48px)", css)
        for filename in ("supermarket.webp", "takeout.webp", "dine-in.webp", "alcohol.webp"):
            self.assertIn(f"tabs/{filename}", css)
            self.assertTrue((ROOT / "docs" / "images" / "topics" / "consumption-tax-cut" / "tabs" / filename).is_file())
        self.assertTrue((ROOT / "docs" / "consumption-tax-search-entry.js").is_file())
        rebuilt = apply_search_entry(apply_search_entry(self.source, 4340), 4340)
        self.assertEqual(rebuilt.count("<!-- TAX_SEARCH_ENTRY_START -->"), 1)
        self.assertEqual(rebuilt.count("consumption-tax-search-entry.css?v=3"), 1)

    def test_article_metadata_matches_visible_heading(self) -> None:
        article = json.loads(self.soup.select_one('script[type="application/ld+json"]').string)
        self.assertIn("いつから", article["headline"])
        self.assertEqual(article["dateModified"], "2026-09-27")
        dates = self.soup.select(".article-trust-meta time")
        self.assertEqual([node["datetime"] for node in dates], ["2026-07-29", "2026-09-27"])


if __name__ == "__main__":
    unittest.main()
