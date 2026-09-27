"""高齢者免許返納の課題77連動表示の接続・冪等性検査。"""

from __future__ import annotations

import copy
import re
import unittest
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup

from scripts import elderly_connected as connected

ROOT = Path(__file__).resolve().parents[1]


class ElderlyConnectedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = (ROOT / "docs/elderly-license-revocation-reaction-map.html").read_text(encoding="utf-8")
        # 候補ページから連動表示の静的ブロックだけを外し、工程6の明示的な有効化を検査する。
        cls.base = re.sub(
            re.escape(connected.START) + r".*?" + re.escape(connected.END) + r"\n?",
            "",
            cls.current,
            flags=re.S,
        )
        cls.base = re.sub(
            r"/\* ELDERLY_CONNECTED_BRIDGE_START \*/.*?/\* ELDERLY_CONNECTED_BRIDGE_END \*/\n?",
            "",
            cls.base,
            flags=re.S,
        )
        from scripts.elderly_connected_content import END as CONTENT_END
        from scripts.elderly_connected_content import START as CONTENT_START

        cls.base = re.sub(re.escape(CONTENT_START) + r".*?" + re.escape(CONTENT_END) + r"\n?", "", cls.base, flags=re.S)
        cls.page = connected.apply(cls.base, activate=True)

    def test_activation_is_explicit_and_other_themes_are_unchanged(self):
        self.assertEqual(connected.apply(self.base), self.base)
        self.assertEqual(connected.apply(self.page), self.page)
        other = (ROOT / "docs/bike-blue-ticket-reaction-map.html").read_text(encoding="utf-8")
        self.assertEqual(connected.apply(other, activate=True, topic="bike-blue-ticket"), other)

    def test_assets_and_markers_are_unique(self):
        from scripts.elderly_connected_content import END as CONTENT_END
        from scripts.elderly_connected_content import START as CONTENT_START

        self.assertEqual(self.page.count(connected.START), 1)
        self.assertEqual(self.page.count(connected.END), 1)
        self.assertEqual(self.page.count(connected.BRIDGE_START), 1)
        self.assertEqual(self.page.count(connected.BRIDGE_END), 1)
        self.assertEqual(self.page.count(CONTENT_START), 1)
        self.assertEqual(self.page.count(CONTENT_END), 1)
        self.assertEqual(self.page.count(connected.CSS_HREF), 1)
        self.assertEqual(self.page.count(connected.JS_SRC), 1)
        self.assertEqual(self.page.count(connected.PAGE_JS_SRC), 1)
        self.assertEqual(connected.validate(self.page), [])

    def test_generated_ids_are_unique_even_for_shared_claims(self):
        soup = BeautifulSoup(self.page, "html.parser")
        ids = [node.get("id") for node in soup.select("[id]")]
        self.assertEqual(len(ids), len(set(ids)), "論点横断で再利用する主張もHTML idを重複させない")

    def test_connections_match_planet_data_and_every_issue_has_a_template(self):
        soup = BeautifulSoup(self.page, "html.parser")
        data = connected.planet_data(self.page)
        index = connected.content_index(data)
        self.assertEqual(len(soup.select("template[id^='elderly-license-revocation-reading-']")), len(data["issues"]))
        self.assertEqual(
            sorted(sid for entry in index["issues"].values() for sid in entry["source_only_ids"]),
            sorted(item["id"] for item in data["ocean"]["sunk_continents"]),
        )
        for issue in data["issues"]:
            iid = issue["id"]
            reading = soup.select_one("#elderly-license-revocation-reading-" + iid)
            self.assertIsNotNone(reading, iid)
            connection = index["issues"][iid]
            for key, attr in (
                ("claim_ids", "data-elc-claim"),
                ("source_only_ids", "data-elc-source-only"),
                ("shared_concern_ids", "data-elc-concern"),
                ("timeline_ids", "data-elc-timeline"),
                ("check_ids", "data-elc-check"),
                ("reason_ids", "data-elc-reason-posts"),
            ):
                self.assertEqual([node.get(attr) for node in reading.select("[" + attr + "]")], connection[key], iid + " " + key)

    def test_reasons_only_show_source_registered_posts_and_unreviewed_are_explicitly_empty(self):
        soup = BeautifulSoup(self.page, "html.parser")
        data = connected.planet_data(self.page)
        by_id = {issue["id"]: issue for issue in data["issues"]}
        for iid in ("elderly-license-revocation-safety", "elderly-license-revocation-mobility-rights"):
            issue = by_id[iid]
            reading = soup.select_one("#elderly-license-revocation-reading-" + iid)
            expected = [str(item["id"]) for item in issue["sub"]["items"] if not item.get("unread")]
            self.assertEqual([node["data-elc-reason-posts"] for node in reading.select("[data-elc-reason-posts]")], expected)
            self.assertEqual(len(reading.select("[data-elc-reason-posts] [data-elc-post-url]")), len(expected))
        for iid in (
            "elderly-license-revocation-assessment",
            "elderly-license-revocation-other",
            "elderly-license-revocation-alternative-transport",
            "elderly-license-revocation-voluntary-return",
        ):
            reading = soup.select_one("#elderly-license-revocation-reading-" + iid)
            self.assertIsNotNone(reading.select_one(".elc-empty"), iid)
            self.assertIsNone(reading.select_one(".elc-reasons"), iid)

    def test_vote_contract_is_unchanged(self):
        from scripts.refresh_adapters.elderly import VOTE_CHOICES, VOTE_TOPIC, vote_fingerprint

        before = vote_fingerprint(self.base)
        after = vote_fingerprint(self.page)
        self.assertEqual(before, after)
        self.assertEqual(after[0], VOTE_TOPIC)
        self.assertEqual(after[3], VOTE_CHOICES)

    def test_relationships_do_not_depend_on_issue_order_or_labels(self):
        data = connected.planet_data(self.page)
        expected = connected.content_index(data)
        changed = copy.deepcopy(data)
        changed["issues"].reverse()
        for issue in changed["issues"]:
            issue["label"] = "表示名を変更"
        self.assertEqual(connected.content_index(changed), expected)

    def test_refresh_dispatcher_reapplies_only_an_existing_connection(self):
        from scripts.refresh_planet_section import _apply_connected_display, refresh

        self.assertEqual(_apply_connected_display("elderly-license-revocation", self.base), self.base)
        self.assertEqual(_apply_connected_display("elderly-license-revocation", self.page), self.page)
        data = connected.planet_data(self.page)
        with patch("scripts.refresh_planet_section.bpd.build", return_value=data):
            _, rebuilt, failures = refresh("elderly-license-revocation", source=self.page)
        self.assertEqual(failures, [])
        self.assertEqual(connected.validate(rebuilt), [])
        with patch("scripts.refresh_planet_section.bpd.build", return_value=data):
            _, twice, failures = refresh("elderly-license-revocation", source=rebuilt)
        self.assertEqual(failures, [])
        self.assertEqual(rebuilt, twice)


if __name__ == "__main__":
    unittest.main()
