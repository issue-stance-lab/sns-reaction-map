import json
import unittest
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "elderly-license-revocation-reaction-map.html"


class ElderlySearchEntryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PAGE.read_text(encoding="utf-8")
        cls.soup = BeautifulSoup(cls.source, "html.parser")

    def test_search_intent_is_visible_in_metadata_and_heading(self) -> None:
        self.assertIn("免許返納は何歳から", self.soup.title.string)
        self.assertIn("免許返納は何歳から", self.soup.select_one("h1").get_text())
        description = self.soup.select_one('meta[name="description"]')["content"]
        for phrase in ("全国一律", "70歳", "75歳", "メリットとデメリット"):
            self.assertIn(phrase, description)

    def test_age_rules_are_not_presented_as_mandatory_return(self) -> None:
        guide = self.soup.select_one("#return-age-guide").get_text(" ", strip=True)
        self.assertIn("全国一律の答えはありません", guide)
        self.assertIn("70歳以上", guide)
        self.assertIn("高齢者講習", guide)
        self.assertIn("75歳以上", guide)
        self.assertIn("認知機能検査", guide)

    def test_decision_check_has_four_steps(self) -> None:
        steps = self.soup.select("#return-age-guide .decision-check li")
        self.assertEqual(len(steps), 4)
        self.assertEqual(
            [step.select_one("strong").get_text(strip=True) for step in steps],
            ["運転の変化", "健康と検査", "返納後の生活の足", "続ける条件とやめる条件"],
        )

    def test_faq_is_visible_and_uses_progressive_disclosure(self) -> None:
        questions = self.soup.select("#elderly-license-faq details")
        self.assertEqual(len(questions), 6)
        self.assertTrue(all(question.select_one("summary") for question in questions))
        self.assertIn("全国共通ではありません", questions[-1].get_text())

    def test_primary_sources_are_linked(self) -> None:
        hrefs = {link["href"] for link in self.soup.select("#elderly-license-faq a[href]")}
        self.assertIn(
            "https://www.npa.go.jp/policies/application/license_renewal/jishuhennou.html",
            hrefs,
        )
        self.assertIn(
            "https://www.npa.go.jp/policies/application/license_renewal/ninchi.html",
            hrefs,
        )

    def test_styles_are_loaded_once(self) -> None:
        self.assertEqual(len(self.soup.select('link[href="elderly-search-entry.css?v=1"]')), 1)
        self.assertTrue((ROOT / "docs" / "elderly-search-entry.css").is_file())

    def test_article_metadata_matches_visible_heading(self) -> None:
        article = json.loads(self.soup.select_one('script[type="application/ld+json"]').string)
        self.assertEqual(article["headline"], self.soup.select_one("h1").get_text(strip=True))
        self.assertEqual(article["dateModified"], "2026-09-20")


if __name__ == "__main__":
    unittest.main()
