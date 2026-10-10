"""学校あだ名禁止テーマの課題77連動表示の接続・冪等性検査。"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import school_nickname_connected as connected  # noqa: E402


class SchoolNicknameConnectedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (ROOT / "docs/school-nickname-ban-reaction-map.html").read_text(encoding="utf-8")
        cls.page = connected.apply(cls.original, activate=True)

    def test_activation_is_explicit_and_other_themes_are_unchanged(self):
        inactive = self.original.replace(connected.START, "<!-- SCHOOL_NICKNAME_CONNECTED_DISABLED -->")
        self.assertEqual(connected.apply(inactive), inactive)
        other = (ROOT / "docs/ai-copyright-reaction-map.html").read_text(encoding="utf-8")
        self.assertEqual(connected.apply(other, activate=True, topic="ai-copyright"), other)

    def test_same_input_does_not_accumulate_assets_or_bridges(self):
        self.assertEqual(connected.apply(self.page), self.page)
        self.assertEqual(connected.validate(self.page), [])
        self.assertEqual(self.page.count(connected.START), 1)
        self.assertEqual(self.page.count(connected.BRIDGE_START), 1)
        self.assertEqual(self.page.count(connected.BRIDGE_END), 1)

    def test_all_issue_relationships_have_posts_and_data_connections(self):
        data = connected.planet_data(self.page)
        expected = connected.content_index(data)
        soup = BeautifulSoup(self.page, "html.parser")
        for issue in data["issues"]:
            iid = issue["id"]
            reading = soup.select_one("#school-nickname-ban-reading-" + iid)
            self.assertIsNotNone(reading)
            self.assertEqual(len(reading.select("[data-school-nickname-post-url]")), 2, iid)
            self.assertGreaterEqual(len(reading.select("[data-school-nickname-reason-post-url]")), 0)
            connection = expected["issues"][iid]
            for key, attr in (
                ("claim_ids", "data-school-nickname-claim"),
                ("source_only_ids", "data-school-nickname-source-only"),
                ("global_source_only_ids", "data-school-nickname-global-source-only"),
                ("shared_concern_ids", "data-school-nickname-concern"),
                ("timeline_ids", "data-school-nickname-timeline"),
                ("check_ids", "data-school-nickname-check"),
            ):
                self.assertEqual(
                    [node.get(attr) for node in reading.select("[" + attr + "]")],
                    connection[key],
                    iid + " " + key,
                )
        self.assertEqual(len(soup.select("[data-school-nickname-reason-post-url]")), 26)

    def test_background_checklist_and_timeline_are_connected_to_known_ids(self):
        data = connected.planet_data(self.page)
        expected = connected.content_index(data)
        issue_ids = set(expected["issues"])
        background = connected.background_data()
        self.assertEqual(len(background["timeline"]), 3)
        for check_id, issue_list in connected.CHECK_ISSUES.items():
            self.assertTrue(issue_list, check_id)
            self.assertTrue(set(issue_list) <= issue_ids, check_id)

    def test_search_entry_and_visible_faq_are_generated_once(self):
        soup = BeautifulSoup(self.page, "html.parser")
        self.assertEqual(len(soup.select('link[href="school-nickname-connected.css?v=4"]')), 1)
        self.assertNotIn("school-nickname-connected.css?v=3", self.page)
        self.assertEqual(len(soup.select('script[src="school-nickname-connected-page.js?v=2"][defer]')), 1)
        self.assertEqual(len(soup.select("#school-nickname-guide")), 1)
        tabs = soup.select("#school-nickname-guide [data-school-nickname-guide-tab]")
        panels = soup.select("#school-nickname-guide [data-school-nickname-guide-panel]")
        self.assertEqual(len(tabs), 3)
        self.assertEqual(len(panels), 3)
        self.assertEqual([tab.get("aria-controls") for tab in tabs], [panel.get("id") for panel in panels])
        self.assertEqual(
            {panel.get("data-school-nickname-issue-id") for panel in panels},
            {
                "school-nickname-ban-school-practice",
                "school-nickname-ban-psychological-safety",
                "school-nickname-ban-uniform-rule",
            },
        )
        self.assertEqual(len(soup.select("#school-nickname-guide [data-school-nickname-map-link]")), 3)
        self.assertEqual(len(soup.select("#school-nickname-faq details")), 10)
        self.assertLess(self.page.index("SCHOOL_NICKNAME_SEARCH_ENTRY_START"), self.page.index("STANCE_GLANCE_START"))
        self.assertLess(self.page.index("SCHOOL_NICKNAME_FAQ_START"), self.page.index('id="related-topics"'))
        payloads = [json.loads(node.string) for node in soup.select('script[type="application/ld+json"]')]
        faq = next(item for item in payloads if item.get("@type") == "FAQPage")
        article = next(item for item in payloads if item.get("@type") == "Article")
        self.assertEqual(len(faq["mainEntity"]), 10)
        self.assertEqual(article["headline"], "学校のあだ名禁止はなぜ？さん付け・いじめとの関係と賛否")
        self.assertEqual(
            soup.select_one("title").get_text(strip=True),
            "学校のあだ名禁止はなぜ？さん付け・いじめとの関係と賛否｜SNS反応まっぷ",
        )

    def test_progress_label_describes_recorded_actions_not_reading(self):
        soup = BeautifulSoup(self.page, "html.parser")
        progress = soup.select_one("#progress")
        self.assertIsNotNone(progress)
        self.assertEqual(progress.select_one("span").get_text(strip=True), "探ったところ")
        self.assertIn("記録対象の操作", progress.get_text(" ", strip=True))
        self.assertNotIn("読んだところ", progress.get_text(" ", strip=True))
        self.assertIn('localStorage.getItem("isa-seen-"+D.theme_id)', self.page)
        self.assertIn("const SPOTS = 2 + issues.length", self.page)

    def test_internal_process_copy_is_removed_without_changing_public_data(self):
        before = connected.planet_data(self.original)
        after = connected.planet_data(self.page)
        self.assertEqual(after, before)
        for phrase in connected.UNWANTED_PROCESS_COPY:
            self.assertNotIn(phrase, self.page)

        soup = BeautifulSoup(self.page, "html.parser")
        self.assertEqual(len(soup.select("[data-school-nickname-post-url]")), 12)
        self.assertEqual(len(soup.select("[data-school-nickname-reason-post-url]")), 26)
        self.assertEqual(len(after["issues"]), 6)
        self.assertEqual(sum(issue["count"] for issue in after["issues"]), after["totals"]["opinions"])
        # 未読が残るときだけ「まだ読み直していない分」の説明が出る（2026-10-10の追い読みで0件）
        if any(issue["sub"].get("unread_count") for issue in after["issues"]):
            self.assertIn("まだ読み直していない分", self.page)
        self.assertIn("SNS投稿の収集方法", self.page)
        self.assertIn("データの読み方:", self.page)
        self.assertIn('localStorage.getItem("isa-seen-"+D.theme_id)', self.page)

    def test_relationships_do_not_depend_on_issue_order_or_labels(self):
        data = connected.planet_data(self.page)
        expected = connected.content_index(data)
        changed = copy.deepcopy(data)
        changed["issues"] = list(reversed(changed["issues"]))
        for issue in changed["issues"]:
            issue["label"] = "表示名変更"
        self.assertEqual(connected.content_index(changed), expected)


if __name__ == "__main__":
    unittest.main()
