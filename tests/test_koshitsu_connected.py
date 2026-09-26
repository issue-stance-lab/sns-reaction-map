"""課題77・皇室典範テーマの接続表と読書面の検査。"""

import copy
import json
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from scripts import koshitsu_connected as connected


ROOT = Path(__file__).resolve().parents[1]


class KoshitsuConnectedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (ROOT / "docs/koshitsu-tenpakai-reaction-map.html").read_text(encoding="utf-8")
        cls.data = connected.planet_data(cls.page)
        cls.index = connected.content_index(cls.data)

    def test_published_candidate_is_valid_and_idempotent(self):
        self.assertEqual(connected.validate(self.page), [])
        self.assertEqual(connected.apply(self.page), self.page)
        self.assertEqual(connected.apply(self.page, activate=True), self.page)

    def test_disabled_page_is_left_untouched_without_activation(self):
        disabled = self.page.replace(connected.START, "<!-- KOSHITSU_CONNECTED_DISABLED -->", 1)
        self.assertEqual(connected.apply(disabled), disabled)

    def test_every_issue_has_a_reading_template_and_post_examples(self):
        soup = BeautifulSoup(self.page, "html.parser")
        for issue in self.data["issues"]:
            template = soup.select_one("#koshitsu-tenpakai-reading-" + issue["id"])
            self.assertIsNotNone(template, issue["id"])
            self.assertEqual(template.name, "template", issue["id"])
            self.assertTrue(template.select("[data-aic-post-url]"), issue["id"])

    def test_claim_connections_follow_the_issue_data(self):
        for issue in self.data["issues"]:
            iid = issue["id"]
            self.assertEqual(
                self.index["issues"][iid]["claim_ids"],
                [claim["id"] for claim in issue["claims"]],
                iid,
            )
            for claim in issue["claims"]:
                self.assertIn(iid, claim["issue_ids"], claim["id"])

    def test_all_source_only_items_are_tagged_once(self):
        sunk = self.data["ocean"]["sunk_continents"]
        self.assertTrue(sunk)
        self.assertTrue(all(item.get("nearest_issue_id") for item in sunk))
        linked = [
            source_id
            for issue in self.index["issues"].values()
            for source_id in issue["source_only_ids"]
        ]
        self.assertEqual(sorted(linked), sorted(item["id"] for item in sunk))

    def test_checklist_contract_has_expected_issue_links(self):
        expected = {
            "koshitsu-tenpakai-patrilineal-matrilineal": ["female-and-matrilineal-emperor"],
            "koshitsu-tenpakai-former-royal-adoption": ["adopted-child-and-descendants"],
            "koshitsu-tenpakai-legislative-process": [],
            "koshitsu-tenpakai-other": [],
            "koshitsu-tenpakai-princess-aiko": ["marriage-status"],
            "koshitsu-tenpakai-female-emperor": ["female-and-matrilineal-emperor"],
        }
        self.assertEqual(
            {iid: entry["check_ids"] for iid, entry in self.index["issues"].items()},
            expected,
        )

    def test_timeline_is_intentionally_unassigned_until_unique_tags_exist(self):
        self.assertTrue(self.data["issues"])
        self.assertTrue(connected.background_data()["timeline"])
        self.assertTrue(all(not event.get("issue_ids") for event in connected.background_data()["timeline"]))
        self.assertTrue(all(not entry["timeline_ids"] for entry in self.index["issues"].values()))

    def test_reordering_display_data_does_not_change_relationships(self):
        mutated = copy.deepcopy(self.data)
        mutated["issues"].reverse()
        for issue in mutated["issues"]:
            issue["label"] = "表示名変更"
        self.assertEqual(connected.content_index(mutated), self.index)

    def test_refresh_dispatcher_reapplies_the_same_candidate(self):
        from scripts.refresh_planet_section import _apply_connected_display

        self.assertEqual(_apply_connected_display("koshitsu-tenpakai", self.page), self.page)

    def test_connected_payload_is_embedded_once(self):
        soup = BeautifulSoup(self.page, "html.parser")
        payload = soup.select("#koshitsu-connected-data")
        self.assertEqual(len(payload), 1)
        self.assertEqual(json.loads(payload[0].string), self.index)


if __name__ == "__main__":
    unittest.main()
