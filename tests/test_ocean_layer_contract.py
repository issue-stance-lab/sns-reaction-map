"""公開データ契約に載せた海面下（沈んだ大陸・地下水脈）の検査。

課題54 段階7-B。それまで海面下は `data/verification/` の確認台帳にしか無く、
惑星の生成器が台帳を直接読んでいた。台帳には投稿ID・機械一致の作業記録が入っており、
そのまま惑星データと試作HTMLへ埋め込まれていた。公開契約を通す形へ変えたので、
「人が一次資料を読んで確定したことだけが画面へ出る」を検査で固定する。
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import public_registry_common as prc

PUBLIC = Path(prc.ROOT) / "data" / "public" / "themes"


def theme_json(theme_id: str) -> dict:
    return json.loads((PUBLIC / f"{theme_id}.json").read_text(encoding="utf-8"))


class OceanLayerContractTest(unittest.TestCase):
    def test_all_ten_themes_have_an_explicit_status(self) -> None:
        # 空欄と未実施を区別する（設計書14章）。読み手が「まだやっていない」を機械判定できる
        seen = 0
        for path in sorted(PUBLIC.glob("*.json")):
            ocean = json.loads(path.read_text(encoding="utf-8"))["ocean_layer"]
            self.assertIn(ocean["status"], {"complete", "not_started"}, path.stem)
            seen += 1
        self.assertEqual(seen, 10)

    def test_bukatsu_chiiki_is_complete_and_read_by_people(self) -> None:
        ocean = theme_json("bukatsu-chiiki")["ocean_layer"]
        self.assertEqual(ocean["status"], "complete")
        self.assertEqual(ocean["reviewer_type"], "editorial_review")
        self.assertEqual(len(ocean["sunk_continents"]), 4)
        self.assertEqual(len(ocean["veins"]), 2)

    def test_post_ids_and_bodies_never_reach_the_public_contract(self) -> None:
        # 台帳の match_rule.machine_hits / representative_posts[].tweet_id が漏れていないこと
        for path in sorted(PUBLIC.glob("*.json")):
            ocean = json.loads(path.read_text(encoding="utf-8"))["ocean_layer"]
            leaked = prc._forbidden_keys_in(ocean)
            self.assertEqual(leaked, set(), f"{path.stem}: {leaked}")
            text = json.dumps(ocean, ensure_ascii=False)
            self.assertNotIn("tweet_id", text, path.stem)

    def test_veins_carry_counts_not_post_ids(self) -> None:
        # 段階6・指摘2と同じ扱い。件数だけを公開し、投稿IDの正典は台帳側に残す
        for vein in theme_json("bukatsu-chiiki")["ocean_layer"]["veins"]:
            self.assertGreaterEqual(len(vein["sides"]), 2, vein["id"])
            for side in vein["sides"]:
                self.assertEqual(set(side), {"stance_label", "post_count"})
                self.assertGreaterEqual(side["post_count"], 2, vein["id"])

    def test_sunk_continents_have_primary_sources_and_a_denominator(self) -> None:
        for item in theme_json("bukatsu-chiiki")["ocean_layer"]["sunk_continents"]:
            self.assertTrue(item["sources"], item["id"])
            for src in item["sources"]:
                self.assertTrue(src["url"].startswith("https://"), item["id"])
                self.assertTrue(src["location"], item["id"])
            # 件数0件も「0件」と母数つきで出す（設計書3.3.2）
            self.assertLessEqual(item["sns_count"], item["sns_base"], item["id"])

    def test_links_point_at_real_issues_and_never_at_other(self) -> None:
        data = theme_json("bukatsu-chiiki")
        known = {i["id"] for i in data["issues"]}
        other = {i["id"] for i in data["issues"] if i["kind"] == "other"}
        ocean = data["ocean_layer"]
        for item in ocean["sunk_continents"]:
            if item["nearest_issue_id"] is not None:
                self.assertIn(item["nearest_issue_id"], known, item["id"])
        for vein in ocean["veins"]:
            self.assertTrue(vein["issue_ids"], vein["id"])
            for issue_id in vein["issue_ids"]:
                self.assertIn(issue_id, known, vein["id"])
                self.assertNotIn(issue_id, other, vein["id"])

    def test_unread_theme_stays_empty_instead_of_being_guessed(self) -> None:
        # 台帳が無いテーマは推測で埋めない（設計書3.3）
        ocean = prc.build_ocean_layer("takaichi")
        self.assertEqual(ocean["status"], "not_started")
        self.assertEqual(ocean["sunk_continents"], [])
        self.assertEqual(ocean["veins"], [])
        self.assertIsNone(ocean["checked_on"])

    def test_reviewer_type_follows_the_weakest_item(self) -> None:
        # 1件でもAIの下読みが混じれば、全体は editorial_review と名乗らない（設計書3.3）
        reviewers = [x["reviewer_type"] for x in
                     theme_json("bukatsu-chiiki")["ocean_layer"]["sunk_continents"]]
        overall = theme_json("bukatsu-chiiki")["ocean_layer"]["reviewer_type"]
        if "ai_assisted" in reviewers:
            self.assertEqual(overall, "ai_assisted")
        else:
            self.assertEqual(overall, "editorial_review")

    def test_a_count_above_its_denominator_is_stopped(self) -> None:
        errors = prc.check_ocean_invariants(
            {"theme_id": "t", "ocean_layer": {
                "status": "complete", "checked_on": "2026-09-02",
                "reviewer_type": "editorial_review", "veins": [],
                "sunk_continents": [{"id": "x", "sns_count": 5, "sns_base": 1,
                                     "nearest_issue_id": None}]}},
            set(), set())
        self.assertTrue(any("母数を超え" in e for e in errors), errors)
