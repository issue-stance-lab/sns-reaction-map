"""部活動の連動表示（工程2: 土台／工程3: 読書面）の接続・冪等性検査。"""
import copy
import json
import re
import unittest
import unittest.mock
from pathlib import Path

from bs4 import BeautifulSoup

from scripts import bukatsu_connected as connected
from scripts import bukatsu_connected_content as content
from scripts import bukatsu_taxonomy

ROOT = Path(__file__).resolve().parents[1]


class BukatsuConnectedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (ROOT / "docs/bukatsu-chiiki-reaction-map.html").read_text(encoding="utf-8")
        cls.page = connected.apply(cls.original, activate=True)

    def test_activation_is_explicit_and_other_themes_are_unchanged(self):
        inactive = self.page.replace(connected.START, "<!-- BUKATSU_CONNECTED_DISABLED -->")
        self.assertEqual(connected.apply(inactive), inactive)
        # 現行の公開HTMLは、まだこの工程では有効化しない（マーカー未挿入）。
        self.assertEqual(connected.apply(self.original), self.original)
        for path in (ROOT / "docs").glob("*-reaction-map.html"):
            if path.stem == "bukatsu-chiiki-reaction-map":
                continue
            text = path.read_text(encoding="utf-8")
            self.assertEqual(connected.apply(text, activate=True, topic=path.stem), text)

    def test_same_input_does_not_accumulate_assets_or_bridges(self):
        self.assertEqual(connected.apply(self.page), self.page)
        self.assertEqual(self.page.count(connected.START), 1)
        self.assertEqual(self.page.count(connected.END), 1)
        self.assertEqual(self.page.count(connected.BRIDGE_START), 1)
        self.assertEqual(self.page.count(connected.BRIDGE_END), 1)
        self.assertEqual(self.page.count('bukatsu-connected.css?v=2'), 1)
        self.assertEqual(self.page.count('bukatsu-connected.js?v=1'), 1)
        self.assertEqual(self.page.count('bukatsu-connected-page.js?v=1'), 1)
        self.assertEqual(connected.validate(self.page), [])

    def test_reapplying_to_an_already_enabled_page_replaces_the_block_in_place(self):
        twice = connected.apply(self.page, activate=True)
        self.assertEqual(twice, self.page)

    def test_claim_ids_match_each_issues_own_claims_and_are_self_consistent(self):
        # data["claims"]（クイズ用の一覧）にはissue_idsが無く、論点へ埋め込まれた
        # issue["claims"]側にだけissue_idsが残る。ここでは論点の埋め込みをそのまま
        # 転記しているか（直接の正しさ）と、埋め込まれた側の自己申告
        # （claim["issue_ids"]に自分の論点idが入っているか）の両方を確認する。
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

    def test_source_only_ids_follow_nearest_issue_id_and_untagged_items_are_dropped(self):
        data = connected.planet_data(self.page)
        index = connected.content_index(data)
        tagged = [sc for sc in data["ocean"]["sunk_continents"] if sc.get("nearest_issue_id")]
        untagged = [sc for sc in data["ocean"]["sunk_continents"] if not sc.get("nearest_issue_id")]
        self.assertTrue(untagged, "この検査は未タグの語られていない争点が残っている前提です")
        all_linked = {sid for entry in index["issues"].values() for sid in entry["source_only_ids"]}
        for sc in tagged:
            self.assertIn(sc["id"], index["issues"][sc["nearest_issue_id"]]["source_only_ids"])
        for sc in untagged:
            self.assertNotIn(sc["id"], all_linked)

    def test_timeline_ids_match_the_owner_confirmed_tagging_and_untagged_issues_stay_empty(self):
        # 工程4でオーナーに確認した年表6件のタグ付け（configs/prompts...計画書の対話で決定）を、
        # data/verification/bukatsu-chiiki-background.jsonへ反映した結果がそのまま出ているかを見る。
        # 地域格差・その他は年表6件のどれにも該当しない前提（無理に割り当てていないことの確認）。
        data = connected.planet_data(self.page)
        index = connected.content_index(data)
        expected = {
            "bukatsu-chiiki-kyoin": ["shidouin", "budget2026"],
            "bukatsu-chiiki-seido": ["guideline2022", "period", "chutairen", "guideline2025"],
            "bukatsu-chiiki-kyoiku": ["chutairen"],
            "bukatsu-chiiki-ukezara": ["shidouin"],
            "bukatsu-chiiki-hiyo": ["budget2026"],
            "bukatsu-chiiki-sonota": [],
            "bukatsu-chiiki-kakusa": [],
        }
        self.assertEqual({iid: v["timeline_ids"] for iid, v in index["issues"].items()}, expected)

    def test_timeline_entry_without_issue_ids_is_rejected(self):
        data = connected.planet_data(self.page)
        broken = {
            "checked_on": "2026-09-05",
            "timeline": [{"id": "shidouin", "issue_ids": [], "when": "x", "era": "x", "text": "x", "sources": []}],
        }
        with unittest.mock.patch.object(connected, "background_data", return_value=broken):
            with self.assertRaises(ValueError):
                connected.content_index(data)

    def test_relationships_do_not_depend_on_rank_or_display_labels(self):
        data = connected.planet_data(self.page)
        expected = connected.content_index(data)
        changed = copy.deepcopy(data)
        changed["issues"].reverse()
        for issue in changed["issues"]:
            issue["label"] = "表示名を変更"
        self.assertEqual(connected.content_index(changed), expected)

    def test_display_adapts_to_changed_counts_while_vote_payload_stays_fixed(self):
        # 工程5「入力が変わる場合」: 隔離した検証データで件数・順位を変えても表示は追従し、
        # 投票番号と関連資料は変わらないことを確認する。次回の実データ更新で件数分布が
        # 変わっても、山なみ側の並び替えが投票の保存先へ波及しないことを保証する検査。
        data = connected.planet_data(self.original)
        mutated = copy.deepcopy(data)
        # 現在最多(教員の働き方)と最少(地域格差)の件数を入れ替え、山の並び順が変わる状況を再現する。
        by_id = {i["id"]: i for i in mutated["issues"]}
        top, bottom = "bukatsu-chiiki-kyoin", "bukatsu-chiiki-kakusa"
        by_id[top]["count"], by_id[bottom]["count"] = by_id[bottom]["count"], by_id[top]["count"]
        for mode in mutated["modes"]:
            mode["counts"][top], mode["counts"][bottom] = mode["counts"].get(bottom, 0), mode["counts"].get(top, 0)

        source = self.original
        mutated_json = json.dumps(mutated, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
        mutated_source = connected.DATA_PATTERN.sub(lambda m: m[1] + mutated_json + m[3], source, count=1)
        mutated_page = connected.apply(mutated_source, activate=True)
        self.assertEqual(connected.validate(mutated_page), [])

        # 表示側（読書面）は7論点分そろったまま追従する。
        mutated_index = connected.content_index(mutated)
        self.assertEqual(set(mutated_index["issues"]), set(by_id))

        # 投票（VOTE_ISSUES/STANCES/choiceIdx式）はPLANET_DATAを一切参照しないため、
        # 件数・順位が変わっても出力バイト列が変わらないことを直接比較する。
        # var VOTE_ISSUES= を含む<script>...</script>だけを切り出す（vote-section内には
        # window.voteMsg等の別のscriptも先にあるため、VOTE_ISSUESの位置から前後へ辿る）。
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
            '"schema":1,"theme_id":"bukatsu-chiiki"',
            '"schema":2,"theme_id":"bukatsu-chiiki"',
            1,
        )
        problems = connected.validate(broken)
        self.assertTrue(any("接続表" in p for p in problems))

    def test_reading_templates_cover_all_seven_issues_with_matching_reason_and_post_counts(self):
        data = connected.planet_data(self.page)
        soup = BeautifulSoup(self.page, "html.parser")
        by_id = {i["id"]: i for i in data["issues"]}
        expected_pilots = {
            "bukatsu-chiiki-kyoin": {"reasons": 16, "posts": 2, "claims": 1, "veins": 1, "timeline": 2},
            "bukatsu-chiiki-ukezara": {"reasons": 7, "posts": 2, "claims": 2, "veins": 2, "timeline": 1},
            "bukatsu-chiiki-sonota": {"reasons": 0, "posts": 2, "claims": 0, "veins": 0, "timeline": 0},
        }
        for issue in data["issues"]:
            iid = issue["id"]
            tpl = soup.select_one("#bukatsu-reading-" + iid)
            self.assertIsNotNone(tpl, iid)
            reading = BeautifulSoup(tpl.decode_contents(), "html.parser")
            self.assertEqual(len(reading.select("[data-bkt-post-url]")), 2, iid)
            if iid in expected_pilots:
                exp = expected_pilots[iid]
                self.assertEqual(len(reading.select("[data-bkt-reason]")), exp["reasons"], iid)
                self.assertEqual(len(reading.select("[data-bkt-claim]")), exp["claims"], iid)
                self.assertEqual(len(reading.select("[data-bkt-concern]")), exp["veins"], iid)
                self.assertEqual(len(reading.select("[data-bkt-timeline]")), exp["timeline"], iid)
                self.assertEqual("年表のどこが関係する？" in str(reading), exp["timeline"] > 0, iid)

    def test_coverage_note_is_suppressed_when_show_coverage_note_is_false(self):
        data = connected.planet_data(self.page)
        reread = next(i for i in data["issues"] if i["sub"]["status"] == "reread")
        self.assertIs(reread["sub"].get("show_coverage_note"), False, "この検査は現行データがshow_coverage_note=falseである前提です")
        html = content.reasons(reread, True)
        self.assertNotIn(reread["sub"]["coverage_note"], html)
        forced_on = copy.deepcopy(reread)
        forced_on["sub"]["show_coverage_note"] = True
        self.assertIn(forced_on["sub"]["coverage_note"], content.reasons(forced_on, True))

    def test_unreviewed_note_respects_the_theme_wide_flag(self):
        data = connected.planet_data(self.page)
        unreviewed = next(i for i in data["issues"] if i["sub"]["status"] == "not_reviewed")
        self.assertIs(data.get("show_unreviewed_note"), False, "この検査は現行データがshow_unreviewed_note=falseである前提です")
        suppressed = content.reasons(unreviewed, False)
        self.assertNotIn("AIが自動でつけた区分", suppressed)
        shown = content.reasons(unreviewed, True)
        self.assertIn("AIが自動でつけた区分", shown)

    def test_metrics_placeholders_exist_for_runtime_fill_including_the_zero_state(self):
        # 件数・割合は実行時にJS（fillMetrics）が埋める。0件（立場を絞ると0になる論点が
        # 実データに存在する。例: kakusaは「移行支持」で0件）でも不正な割合を出さないための
        # data-bkt-zero placeholderが、静的な読書面テンプレート側に用意されていることを確認する。
        data = connected.planet_data(self.page)
        has_zero_case = any(
            s["counts"].get(i["id"]) == 0
            for s in data["modes"] if s["id"] != "all"
            for i in data["issues"]
        )
        self.assertTrue(has_zero_case, "この検査は0件になる組合せが実データに存在する前提です")
        soup = BeautifulSoup(self.page, "html.parser")
        tpl = soup.select_one("#bukatsu-reading-bukatsu-chiiki-kakusa")
        reading = BeautifulSoup(tpl.decode_contents(), "html.parser")
        self.assertIsNotNone(reading.select_one("[data-bkt-count]"))
        self.assertIsNotNone(reading.select_one("[data-bkt-ratio]"))
        self.assertIsNotNone(reading.select_one("[data-bkt-zero]"))

    def test_vote_registry_is_unaffected_by_the_connected_layout(self):
        # 投票は今回の工程では独立のまま。連動表示の適用前後でVOTE_ISSUES/STANCESの
        # 個数・意味・保存式（choiceIdx=issueIdx*3+stanceIdx）が変わらないことを確認する。
        for html, label in ((self.original, "適用前"), (self.page, "適用後")):
            issue_block = re.search(r"var VOTE_ISSUES=\[(.*?)\];", html, re.DOTALL)
            stance_block = re.search(r"var STANCES=\[(.*?)\];", html, re.DOTALL)
            self.assertIsNotNone(issue_block, label)
            self.assertIsNotNone(stance_block, label)
            published_issues = re.findall(r"k:'([^']+)'", issue_block[1])
            published_stances = re.findall(r"k:'([^']+)'", stance_block[1])
            self.assertEqual(len(published_issues), 7, label)
            self.assertEqual(len(published_stances), 3, label)
            self.assertEqual(len(published_issues) * len(published_stances), 21, label)
            self.assertIn("choiceIdx:issueIdx*STANCES.length+stanceIdx", html.replace(" ", ""))
        self.assertEqual(bukatsu_taxonomy.TOPIC_ID, "bukatsu-chiiki-issue-stance-v1")


if __name__ == "__main__":
    unittest.main()
