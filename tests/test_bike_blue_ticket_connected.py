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

    def test_process_copy_is_absent_from_rendered_fallbacks_and_templates_data_is_preserved(self):
        data = connected.planet_data(self.page)
        soup = BeautifulSoup(self.page, "html.parser")
        for node in soup.select("script, style"):
            node.decompose()
        rendered = soup.get_text(" ", strip=True)
        rendered += " " + " ".join(
            BeautifulSoup(node.decode_contents(), "html.parser").get_text(" ", strip=True)
            for node in BeautifulSoup(self.page, "html.parser").select("template")
        )
        for phrase in (
            "AIを使用した工程",
            "AIで整理し",
            "AI分類。代表投稿は編集部が選定",
            "Powered by Yahooリアルタイム検索 + AI分類",
            "理由の区分と個別投稿IDを結ぶ公開台帳はない",
            "この論点に対応する資料照合は、まだ登録されていません。",
            "AIが自動でつけた区分",
            "人が読んだ結果だけをまとめにします",
            "AIの下読みを含む",
            "編集部が本文を読んで分けたもの",
            "今回新たに採用した",
        ):
            self.assertNotIn(phrase, rendered)
        # 表示上の工程文を除いても、再読・調査ログを含む保存データは保持する。
        self.assertEqual(len(data["ocean"]["sunk_continents"]), 4)
        self.assertTrue(all("今回新たに採用した" in row["sns_note"] for row in data["ocean"]["sunk_continents"]))
        self.assertEqual([issue["sub"]["status"] for issue in data["issues"]], ["reread"] * 6)

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
        import copy
        from unittest.mock import patch

        from scripts import refresh_planet_section
        from scripts.refresh_planet_section import refresh

        snapshot = connected.planet_data(self.page)
        with patch.object(
            refresh_planet_section.bpd,
            "build",
            side_effect=lambda topic: copy.deepcopy(snapshot) if topic == "bike-blue-ticket" else None,
        ):
            _old, rebuilt, failures = refresh("bike-blue-ticket", source=self.page)
            _old_again, rebuilt_again, failures_again = refresh("bike-blue-ticket", source=rebuilt)
        self.assertEqual(failures, [])
        self.assertEqual(failures_again, [])
        self.assertEqual(rebuilt, rebuilt_again)
        self.assertEqual(connected.validate(rebuilt), [])
        self.assertIn(connected.CSS_HREF, rebuilt)


if __name__ == "__main__":
    unittest.main()
