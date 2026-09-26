"""副首都テーマの課題77連動表示の接続・冪等性検査。"""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import fukushuto_connected as connected  # noqa: E402


class FukushutoConnectedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (ROOT / "docs/fukushuto-reaction-map.html").read_text(encoding="utf-8")
        cls.page = connected.apply(cls.original, activate=True)

    def test_activation_is_explicit_and_other_themes_are_unchanged(self):
        inactive = self.page.replace(connected.START, "<!-- FUKUSHUTO_CONNECTED_DISABLED -->")
        self.assertEqual(connected.apply(inactive), inactive)
        other = (ROOT / "docs/ai-copyright-reaction-map.html").read_text(encoding="utf-8")
        self.assertEqual(connected.apply(other, activate=True, topic="ai-copyright"), other)

    def test_same_input_does_not_accumulate_assets_or_bridges(self):
        self.assertEqual(connected.apply(self.page), self.page)
        self.assertEqual(connected.validate(self.page), [])
        self.assertEqual(self.page.count(connected.START), 1)
        self.assertEqual(self.page.count(connected.BRIDGE_START), 1)
        self.assertEqual(self.page.count(connected.BRIDGE_END), 1)
        self.assertIn("FukushutoConnectedMap", self.page)
        self.assertNotIn("BikeBlueTicketConnectedMap", self.page)

    def test_all_issue_relationships_have_two_representative_posts(self):
        data = connected.planet_data(self.page)
        expected = connected.content_index(data)
        soup = BeautifulSoup(self.page, "html.parser")
        for issue in data["issues"]:
            iid = issue["id"]
            reading = soup.select_one("#fukushuto-reading-" + iid)
            self.assertIsNotNone(reading)
            self.assertEqual(len(reading.select("[data-fuk-post-url]")), 2, iid)
            connection = expected["issues"][iid]
            for key, attr in (("claim_ids", "data-fuk-claim"), ("source_only_ids", "data-fuk-source-only"), ("check_ids", "data-fuk-check")):
                self.assertEqual([node.get(attr) for node in reading.select("[" + attr + "]")], connection[key], iid + " " + key)

    def test_background_checklist_is_tagged_to_existing_issue_ids(self):
        background = connected.background_data()
        issue_ids = set(connected.content_index(connected.planet_data(self.page))["issues"])
        for item in background["checklist"]["items"]:
            self.assertTrue(item.get("issue_ids"), item["id"])
            self.assertTrue(set(item["issue_ids"]) <= issue_ids, item["id"])

    def test_relationships_do_not_depend_on_issue_order_or_labels(self):
        data = connected.planet_data(self.page)
        expected = connected.content_index(data)
        changed = copy.deepcopy(data)
        changed["issues"] = list(reversed(changed["issues"]))
        for issue in changed["issues"]:
            issue["label"] = "表示名変更"
        self.assertEqual(connected.content_index(changed), expected)

    def test_refresh_planet_section_reapplies_the_candidate(self):
        if not (ROOT / "social-samples/fukushuto_hermes_classified.json").is_file():
            self.skipTest("非公開の副首都正典がないCI環境では再生成経路を省略")
        from scripts.refresh_planet_section import refresh

        _old, rebuilt, _failures = refresh("fukushuto", source=self.page)
        self.assertEqual(connected.validate(rebuilt), [])
        self.assertIn(connected.CSS_HREF, rebuilt)
        self.assertIn("fukushuto-infographic-wide-tokoso-v2.webp", rebuilt)


if __name__ == "__main__":
    unittest.main()
