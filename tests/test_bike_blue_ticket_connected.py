"""自転車青切符の課題77連動表示の接続・冪等性検査。"""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import bike_blue_ticket_connected as connected  # noqa: E402


class BikeBlueTicketConnectedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (ROOT / "docs/bike-blue-ticket-reaction-map.html").read_text(encoding="utf-8")
        cls.page = connected.apply(cls.original, activate=True)

    def test_activation_is_explicit_and_other_themes_are_unchanged(self):
        inactive = self.page.replace(connected.START, "<!-- BIKE_CONNECTED_DISABLED -->")
        self.assertEqual(connected.apply(inactive), inactive)
        other = (ROOT / "docs/ai-copyright-reaction-map.html").read_text(encoding="utf-8")
        self.assertEqual(connected.apply(other, activate=True, topic="ai-copyright"), other)

    def test_same_input_does_not_accumulate_assets_or_bridges(self):
        self.assertEqual(connected.apply(self.page), self.page)
        self.assertEqual(connected.validate(self.page), [])
        self.assertEqual(self.page.count(connected.START), 1)
        self.assertEqual(self.page.count(connected.BRIDGE_START), 1)
        self.assertEqual(self.page.count(connected.BRIDGE_END), 1)

    def test_all_issue_relationships_have_two_representative_posts(self):
        data = connected.planet_data(self.page)
        expected = connected.content_index(data)
        soup = BeautifulSoup(self.page, "html.parser")
        for issue in data["issues"]:
            iid = issue["id"]
            reading = soup.select_one("#bike-blue-ticket-reading-" + iid)
            self.assertIsNotNone(reading)
            self.assertEqual(len(reading.select("[data-bike-post-url]")), 2, iid)
            connection = expected["issues"][iid]
            for key, attr in (
                ("claim_ids", "data-bike-claim"),
                ("source_only_ids", "data-bike-source-only"),
                ("global_source_only_ids", "data-bike-global-source-only"),
                ("check_ids", "data-bike-check"),
            ):
                self.assertEqual(
                    [node.get(attr) for node in reading.select("[" + attr + "]")],
                    connection[key],
                    iid + " " + key,
                )

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
        private_sample = ROOT / "social-samples/bike-blue-ticket_2d_classified.json"
        if not private_sample.is_file():
            self.skipTest("自転車の非公開正典がない環境では再生成検査を省略")
        from scripts.refresh_planet_section import refresh

        _old, rebuilt, _failures = refresh("bike-blue-ticket", source=self.page)
        self.assertEqual(connected.validate(rebuilt), [])
        self.assertIn(connected.CSS_HREF, rebuilt)


if __name__ == "__main__":
    unittest.main()
