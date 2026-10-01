import unittest
import json
from pathlib import Path

from scripts.seo.apply_theme_trust import is_opinion, trust_block
from scripts.seo.apply_review_note import should_show_review_note, suppress_review_note


class IsOpinionTests(unittest.TestCase):
    """収集方法の {opinions} が数える対象を固定する。

    テーマによって is_opinion の置き場所が違う。`classification` があれば必ず
    そちらを見る書き方だと、自転車の青切符のように `classification` はあるが
    その中に is_opinion が無いテーマで常に0件になる（2026-08-08 に
    「意見と判定した0件」を公開しかけた）。
    """

    def test_classification配下の値を読む(self) -> None:
        self.assertTrue(is_opinion({"classification": {"is_opinion": True}}))
        self.assertFalse(is_opinion({"classification": {"is_opinion": False}}))

    def test_レコード直下の値を読む(self) -> None:
        self.assertTrue(is_opinion({"is_opinion": True}))
        self.assertFalse(is_opinion({"is_opinion": False}))

    def test_classificationにキーが無ければ直下へ落ちる(self) -> None:
        """自転車の青切符の形。直下の値へ落ちる。"""
        row = {"is_opinion": True, "classification": {"main_issue": "取締り強化賛成"}}
        self.assertTrue(is_opinion(row))

    def test_classification配下が直下より優先される(self) -> None:
        row = {"is_opinion": True, "classification": {"is_opinion": False}}
        self.assertFalse(is_opinion(row))

    def test_どちらにも無ければ意見ではない(self) -> None:
        self.assertFalse(is_opinion({"text": "本文だけ"}))
        self.assertFalse(is_opinion({"classification": {}}))


class ThemeTrustCopyTests(unittest.TestCase):
    def test_ai_process_section_is_disabled_only_for_bike(self):
        root = Path(__file__).resolve().parents[1]
        config = json.loads((root / "configs/theme-seo.json").read_text(encoding="utf-8"))
        themes = {theme["id"]: theme for theme in config["themes"]}
        organization = config["organization"]
        bike_theme = dict(themes["bike-blue-ticket"])
        bike_theme["collection"] = bike_theme["collection"].replace("{total}", "585").replace("{opinions}", "415")
        other_theme = dict(themes["ai-copyright"])
        other_theme["collection"] = other_theme["collection"].replace("{total}", "1").replace("{opinions}", "1")
        bike = trust_block(bike_theme, organization)
        other = trust_block(other_theme, organization)
        self.assertNotIn("AIを使用した工程", bike)
        self.assertIn("AIを使用した工程", other)
        self.assertIn("世論調査ではなく", bike)

    def test_review_note_visibility_follows_ai_process_theme_setting(self):
        root = Path(__file__).resolve().parents[1]
        config = json.loads((root / "configs/theme-seo.json").read_text(encoding="utf-8"))
        themes = {theme["id"]: theme for theme in config["themes"]}
        self.assertFalse(should_show_review_note(themes["bike-blue-ticket"]))
        self.assertTrue(should_show_review_note(themes["ai-copyright"]))
        self.assertTrue(should_show_review_note({}))

    def test_review_note_suppression_removes_only_the_display_annotation(self):
        source = '条件／<span class="review-note">AI分類。代表投稿は編集部が選定</span>）'
        self.assertEqual(suppress_review_note(source), "条件）")


if __name__ == "__main__":
    unittest.main()
