"""生成AIと著作権の連動表示（工程2: 土台）の接続・冪等性検査。

読書面（`<template>`生成・#panel差し替え）は工程3で追加するため、ここでは
data/verification/ai-copyright-background.jsonとの接続表・バー↔山の状態共有・
冪等性だけを見る。bukatsu-chiikiのtest_bukatsu_connected.pyと同じ観点だが、
論点を選んだときの読書面に関する検査は含まない（content.pyがまだ無い）。
"""
import copy
import json
import re
import unittest
import unittest.mock
from pathlib import Path

from bs4 import BeautifulSoup

from scripts import ai_copyright_connected as connected

ROOT = Path(__file__).resolve().parents[1]


class AiCopyrightConnectedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (ROOT / "docs/ai-copyright-reaction-map.html").read_text(encoding="utf-8")
        cls.page = connected.apply(cls.original, activate=True)

    def test_activation_is_explicit_and_other_themes_are_unchanged(self):
        inactive = self.page.replace(connected.START, "<!-- AI_COPYRIGHT_CONNECTED_DISABLED -->")
        self.assertEqual(connected.apply(inactive), inactive)
        # 現行の公開HTMLは、まだこの工程では有効化しない（マーカー未挿入）。
        self.assertEqual(connected.apply(self.original), self.original)
        for path in (ROOT / "docs").glob("*-reaction-map.html"):
            if path.stem == "ai-copyright-reaction-map":
                continue
            text = path.read_text(encoding="utf-8")
            self.assertEqual(connected.apply(text, activate=True, topic=path.stem), text)

    def test_same_input_does_not_accumulate_assets_or_bridges(self):
        self.assertEqual(connected.apply(self.page), self.page)
        self.assertEqual(self.page.count(connected.START), 1)
        self.assertEqual(self.page.count(connected.END), 1)
        self.assertEqual(self.page.count(connected.BRIDGE_START), 1)
        self.assertEqual(self.page.count(connected.BRIDGE_END), 1)
        self.assertEqual(self.page.count(connected.CSS_HREF), 1)
        self.assertEqual(connected.validate(self.page), [])

    def test_reapplying_to_an_already_enabled_page_replaces_the_block_in_place(self):
        twice = connected.apply(self.page, activate=True)
        self.assertEqual(twice, self.page)

    def test_claim_ids_match_each_issues_own_claims_and_are_self_consistent(self):
        # data["claims"]（クイズ用の一覧）にはissue_idsを持つが、ここでは論点へ
        # 埋め込まれたissue["claims"]をそのまま転記しているか（直接の正しさ）と、
        # 埋め込まれた側の自己申告（claim["issue_ids"]に自分の論点idが入っているか）
        # の両方を確認する。
        data = connected.planet_data(self.page)
        index = connected.content_index(data)
        has_any_claim = False
        for issue in data["issues"]:
            expected = [c["id"] for c in issue["claims"]]
            self.assertEqual(index["issues"][issue["id"]]["claim_ids"], expected, issue["id"])
            for claim in issue["claims"]:
                has_any_claim = True
                self.assertIn(issue["id"], claim["issue_ids"], claim["id"])
        self.assertTrue(has_any_claim, "この検査は資料照合が1件以上ある前提です")

    def test_source_only_ids_are_fully_tagged_with_no_orphans(self):
        # ai-copyrightは工程1確認のとおり、沈んだ大陸4件がすべてnearest_issue_idを
        # 持つ（bukatsu-chiikiと違い編集部推定の補完が不要）。全件がどこか1論点に
        # 割り当たり、取りこぼしが無いことを確認する。
        data = connected.planet_data(self.page)
        index = connected.content_index(data)
        sunk = data["ocean"]["sunk_continents"]
        self.assertTrue(sunk)
        untagged = [sc for sc in sunk if not sc.get("nearest_issue_id")]
        self.assertEqual(untagged, [], "この検査は沈んだ大陸が全件タグ済みである前提です")
        all_linked = [sid for entry in index["issues"].values() for sid in entry["source_only_ids"]]
        self.assertEqual(sorted(all_linked), sorted(sc["id"] for sc in sunk))
        for sc in sunk:
            self.assertIn(sc["id"], index["issues"][sc["nearest_issue_id"]]["source_only_ids"])

    def test_check_ids_match_the_content_contract_tagging(self):
        # 工程1の内容確定書のドラフト案どおり、本工程でdata/verification/
        # ai-copyright-background.jsonのchecklist.items[]へissue_idsを追加した結果。
        data = connected.planet_data(self.page)
        index = connected.content_index(data)
        expected = {
            "ai-copyright-learning-data": ["gakushu", "kaiji"],
            "ai-copyright-user-ethics": [],
            "ai-copyright-legal-framework": ["kaiji", "hokaisei"],
            "ai-copyright-creator-rights": ["sakufu"],
            "ai-copyright-other": [],
            "ai-copyright-generated-work-rights": [],
            "ai-copyright-tech-promotion": [],
        }
        self.assertEqual({iid: v["check_ids"] for iid, v in index["issues"].items()}, expected)

    def test_check_entry_without_issue_ids_is_rejected(self):
        data = connected.planet_data(self.page)
        broken = {
            "checked_on": "2026-09-05",
            "timeline": [],
            "checklist": {"items": [{"id": "gakushu", "issue_ids": [], "label": "x", "ask": "x", "found": "x", "sources": []}]},
        }
        with unittest.mock.patch.object(connected, "background_data", return_value=broken):
            with self.assertRaises(ValueError):
                connected.content_index(data)

    def test_timeline_ids_are_empty_pending_future_tagging(self):
        # 年表6件は工程1確認のとおり無タグ（真のギャップ、V01の要件は日付切替のみで
        # 論点連動は必須ではない）。タグが増えれば自動で反映される作りであることを
        # 空配列の現状で確認しておく。
        data = connected.planet_data(self.page)
        index = connected.content_index(data)
        background = connected.background_data()
        self.assertTrue(background["timeline"])
        self.assertTrue(all(not t.get("issue_ids") for t in background["timeline"]))
        for entry in index["issues"].values():
            self.assertEqual(entry["timeline_ids"], [])

    def test_relationships_do_not_depend_on_rank_or_display_labels(self):
        data = connected.planet_data(self.page)
        expected = connected.content_index(data)
        changed = copy.deepcopy(data)
        changed["issues"].reverse()
        for issue in changed["issues"]:
            issue["label"] = "表示名を変更"
        self.assertEqual(connected.content_index(changed), expected)

    def test_display_adapts_to_changed_counts_while_vote_payload_stays_fixed(self):
        # 次回の実データ更新で件数分布が変わっても、山なみ側の並び替えが投票の
        # 保存先へ波及しないことを保証する検査。
        data = connected.planet_data(self.original)
        mutated = copy.deepcopy(data)
        by_id = {i["id"]: i for i in mutated["issues"]}
        top, bottom = "ai-copyright-learning-data", "ai-copyright-tech-promotion"
        by_id[top]["count"], by_id[bottom]["count"] = by_id[bottom]["count"], by_id[top]["count"]
        for mode in mutated["modes"]:
            mode["counts"][top], mode["counts"][bottom] = mode["counts"].get(bottom, 0), mode["counts"].get(top, 0)

        source = self.original
        mutated_json = json.dumps(mutated, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
        mutated_source = connected.DATA_PATTERN.sub(lambda m: m[1] + mutated_json + m[3], source, count=1)
        mutated_page = connected.apply(mutated_source, activate=True)
        self.assertEqual(connected.validate(mutated_page), [])

        mutated_index = connected.content_index(mutated)
        self.assertEqual(set(mutated_index["issues"]), set(by_id))

        # 投票（VOTE_ISSUES/STANCES/choiceIdx式）はPLANET_DATAを一切参照しないため、
        # 件数・順位が変わっても出力バイト列が変わらないことを直接比較する。
        def vote_script(html):
            anchor = html.index("var VOTE_ISSUES=")
            start = html.rindex("<script>", 0, anchor)
            end = html.index("</script>", anchor) + len("</script>")
            script = html[start:end]
            self.assertIn("choiceIdx", script)
            return script

        self.assertEqual(vote_script(mutated_page), vote_script(self.page))

    def test_stance_mode_mismatch_is_rejected(self):
        data = connected.planet_data(self.page)
        broken = copy.deepcopy(data)
        broken["modes"][1]["id"] = "存在しない立場"
        with self.assertRaises(ValueError):
            connected.content_index(broken)

    def test_connected_data_mismatch_is_rejected(self):
        broken = self.page.replace(
            '"schema":1,"theme_id":"ai-copyright"',
            '"schema":2,"theme_id":"ai-copyright"',
            1,
        )
        problems = connected.validate(broken)
        self.assertTrue(any("接続表" in p for p in problems))

    def test_vote_registry_is_unaffected_by_the_connected_layout(self):
        # 投票は今回の工程では独立のまま。連動表示の適用前後でVOTE_ISSUES/STANCESの
        # 個数・意味・保存式（choiceIdx=selIssue*STANCES.length+stanceIdx）が
        # 変わらないことを確認する。
        import sys
        sys.path.insert(0, str(ROOT))
        from scripts.refresh_adapters.ai_copyright import VOTE_CHOICES, VOTE_TOPIC

        for html, label in ((self.original, "適用前"), (self.page, "適用後")):
            topic = re.search(r"var TOPIC='([^']+)'", html)
            issue_block = re.search(r"var VOTE_ISSUES=\[(.*?)\];", html, re.DOTALL)
            stance_block = re.search(r"var STANCES=\[(.*?)\];", html, re.DOTALL)
            self.assertIsNotNone(topic, label)
            self.assertIsNotNone(issue_block, label)
            self.assertIsNotNone(stance_block, label)
            self.assertEqual(topic[1], VOTE_TOPIC, label)
            published_issues = re.findall(r"k:'([^']+)'", issue_block[1])
            published_stances = re.findall(r"k:'([^']+)'", stance_block[1])
            self.assertEqual(len(published_issues), 7, label)
            self.assertEqual(len(published_stances), 3, label)
            self.assertEqual(len(published_issues) * len(published_stances), VOTE_CHOICES, label)
            self.assertIn("choiceIdx:selIssue*STANCES.length+stanceIdx", html.replace(" ", ""), label)


if __name__ == "__main__":
    unittest.main()
