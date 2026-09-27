"""部活動ページの検索回答入口と一次資料本文の同期を確認する。"""

import json
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from scripts import build_bukatsu_arena as arena


ROOT = Path(__file__).resolve().parents[1]


class BukatsuSearchEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (ROOT / "docs/bukatsu-chiiki-reaction-map.html").read_text(encoding="utf-8")
        cls.page = arena.apply_bukatsu_search_entry(cls.original)

    def test_entry_is_first_main_section_and_idempotent(self):
        soup = BeautifulSoup(self.page, "html.parser")
        main = soup.find("main")
        first_section = main.find("section", recursive=False)
        self.assertIn("bukatsu-search-entry", first_section.get("class", []))
        self.assertEqual(arena.apply_bukatsu_search_entry(self.page), self.page)
        self.assertEqual(self.page.count(arena.SEARCH_ENTRY_START), 1)
        self.assertEqual(self.page.count(arena.SEARCH_CSS_START), 1)
        self.assertEqual(self.page.count(arena.SEARCH_FAQ_START), 1)

    def test_visible_faq_and_jsonld_have_the_same_questions(self):
        soup = BeautifulSoup(self.page, "html.parser")
        visible = [node.get_text(" ", strip=True) for node in soup.select(".bukatsu-search-faq summary")]
        schemas = [json.loads(node.string) for node in soup.select('script[type="application/ld+json"]')]
        faq = next(schema for schema in schemas if schema.get("@type") == "FAQPage")
        structured = [item["name"] for item in faq["mainEntity"]]
        self.assertEqual(visible, structured)

    def test_entry_links_target_existing_unique_sections(self):
        soup = BeautifulSoup(self.page, "html.parser")
        for link in soup.select(".bukatsu-search-entry__links a[href^='#']"):
            target = link["href"][1:]
            self.assertEqual(len(soup.select(f"#{target}")), 1, target)

    def test_four_role_views_are_accessible_and_not_a_vote(self):
        soup = BeautifulSoup(self.page, "html.parser")
        tabs = soup.select(".bukatsu-role-tab[role='tab']")
        self.assertEqual([tab.get_text(" ", strip=True) for tab in tabs], ["家 保護者", "学 生徒", "校 教員", "地 地域指導者"])
        self.assertEqual(sum(tab.get("aria-selected") == "true" for tab in tabs), 1)
        note = soup.select_one(".bukatsu-role-guide__note").get_text(" ", strip=True)
        self.assertIn("投票ではありません", note)
        self.assertIn("属性で分類する操作でもありません", note)

    def test_four_role_views_use_generated_background_images(self):
        filenames = [
            "bukatsu-role-parent-v1.webp",
            "bukatsu-role-student-v1.webp",
            "bukatsu-role-teacher-v1.webp",
            "bukatsu-role-community-v1.webp",
        ]
        for filename in filenames:
            self.assertIn(filename, self.page)
            self.assertTrue((ROOT / "docs/images/topics/bukatsu-chiiki" / filename).is_file())

    def test_search_entry_does_not_replace_the_existing_reaction_map(self):
        def planet(page):
            start = page.index("<!-- PLANET_SECTION_START -->")
            end = page.index("<!-- PLANET_SECTION_END -->") + len("<!-- PLANET_SECTION_END -->")
            return page[start:end]

        self.assertEqual(planet(self.page), planet(self.original))

    def test_background_refresh_uses_current_ledger(self):
        updated = arena.apply_bukatsu_background(self.original)
        self.assertIn("2026〜2031年度を改革実行期間", updated)
        self.assertNotIn("新版との突き合わせはまだ済んでいません", updated)

    def test_local_check_restores_questions_copy_and_status_actions(self):
        updated = arena.apply_bukatsu_background(self.original)
        soup = BeautifulSoup(updated, "html.parser")
        checks = soup.select("#bukatsu-check [data-local-check]")
        self.assertEqual(len(checks), 6)
        self.assertEqual(sum(node.get("aria-pressed") == "true" for node in checks), 1)
        self.assertIsNotNone(soup.select_one("#bukatsu-check [data-local-copy]"))
        self.assertEqual(len(soup.select("#bukatsu-check [data-local-mark]")), 2)
        self.assertIn("質問文をコピーしました", updated)
        self.assertIn("bukatsu_question_copy", updated)


if __name__ == "__main__":
    unittest.main()
