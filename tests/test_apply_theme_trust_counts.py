import unittest
import json
import re
from pathlib import Path
from unittest import mock

from scripts.seo import apply_theme_trust
from scripts.seo.apply_theme_trust import is_opinion, observations_html, resolve_counts, trust_block
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
    def test_ai_process_section_is_disabled_only_for_themes_that_opt_out(self):
        root = Path(__file__).resolve().parents[1]
        config = json.loads((root / "configs/theme-seo.json").read_text(encoding="utf-8"))
        themes = {theme["id"]: theme for theme in config["themes"]}
        organization = config["organization"]
        bike_theme = dict(themes["bike-blue-ticket"])
        bike_theme["collection"] = bike_theme["collection"].replace("{total}", "585").replace("{opinions}", "415")
        ai_theme = dict(themes["ai-copyright"])
        ai_theme["collection"] = ai_theme["collection"].replace("{total}", "4734").replace("{opinions}", "3146")
        other_theme = dict(themes["consumption-tax-cut"])
        other_theme["collection"] = other_theme["collection"].replace("{total}", "5459").replace("{opinions}", "4823")
        bike = trust_block(bike_theme, organization)
        ai_copyright = trust_block(ai_theme, organization)
        other = trust_block(other_theme, organization)
        self.assertNotIn("AIを使用した工程", bike)
        self.assertNotIn("AIを使用した工程", ai_copyright)
        self.assertIn("AIを使用した工程", other)
        self.assertIn("世論調査ではなく", bike)

    def test_review_note_visibility_follows_ai_process_theme_setting(self):
        root = Path(__file__).resolve().parents[1]
        config = json.loads((root / "configs/theme-seo.json").read_text(encoding="utf-8"))
        themes = {theme["id"]: theme for theme in config["themes"]}
        self.assertFalse(should_show_review_note(themes["bike-blue-ticket"]))
        self.assertFalse(should_show_review_note(themes["ai-copyright"]))
        self.assertTrue(should_show_review_note({}))

    def test_review_note_suppression_removes_only_the_display_annotation(self):
        source = '条件／<span class="review-note">AI分類。代表投稿は編集部が選定</span>）'
        self.assertEqual(suppress_review_note(source), "条件）")


ROOT = Path(__file__).resolve().parents[1]
ELDERLY = "elderly-license-revocation"
ELDERLY_CANONICAL = ROOT / "social-samples/elderly-license_2d_classified.json"


def _elderly_theme() -> dict:
    config = json.loads((ROOT / "configs/theme-seo.json").read_text(encoding="utf-8"))
    return next(theme for theme in config["themes"] if theme["id"] == ELDERLY)


class IssueCountPlaceholderTests(unittest.TestCase):
    """分析メモの論点別件数は、書き手が数字を打たず公開データJSONから差し込む。

    高齢者テーマで「地方の足・移動権 29件／義務化・事故防止 221件」が設定にべた書きされ、
    2026-09-04 までの途中経過のまま残っていた。更新のたびに apply_theme_trust.py が
    この古い数字でページを作り直し、正しい 39／283 を打ち消した（2026-09-30 に発生、
    手で戻したが今回また再発）。数字を書かずに差し込めば、どの順で何度実行しても
    公開データJSON（＝論点カードと同じ数）に揃う。
    """

    def test_論点名の件数が公開データJSONの値で差し込まれる(self) -> None:
        counts = {"地方の足・移動権": 41, "義務化・事故防止": 1283}
        with mock.patch.object(apply_theme_trust, "count_by_issue_from_public_json", return_value=counts):
            text = resolve_counts(
                "A{issue_count:地方の足・移動権}件、B（{issue_count:義務化・事故防止}件）", ELDERLY
            )
        self.assertEqual(text, "A41件、B（1,283件）")

    def test_公開データJSONが変われば文中の数字も変わる(self) -> None:
        sentence = "{issue_count:地方の足・移動権}件"
        with mock.patch.object(
            apply_theme_trust, "count_by_issue_from_public_json", return_value={"地方の足・移動権": 39}
        ):
            before = resolve_counts(sentence, ELDERLY)
        with mock.patch.object(
            apply_theme_trust, "count_by_issue_from_public_json", return_value={"地方の足・移動権": 47}
        ):
            after = resolve_counts(sentence, ELDERLY)
        self.assertEqual((before, after), ("39件", "47件"))

    def test_公開データJSONに無い論点名は黙って通さず止まる(self) -> None:
        with mock.patch.object(
            apply_theme_trust, "count_by_issue_from_public_json", return_value={"義務化・事故防止": 283}
        ):
            with self.assertRaisesRegex(ValueError, "地方の足"):
                resolve_counts("{issue_count:地方の足・移動権}件", ELDERLY)

    def test_公開データJSONが正典と食い違っていれば止まる(self) -> None:
        error = apply_theme_trust.IssueCountError("source_sha256が不一致")
        with mock.patch.object(apply_theme_trust, "count_by_issue_from_public_json", side_effect=error):
            with self.assertRaisesRegex(ValueError, "不一致"):
                resolve_counts("{issue_count:地方の足・移動権}件", ELDERLY)

    def test_差し込みの無い文は公開データJSONを読まない(self) -> None:
        with mock.patch.object(
            apply_theme_trust, "count_by_issue_from_public_json", side_effect=AssertionError("読んではいけない")
        ):
            self.assertEqual(resolve_counts("検索語は10個です。", ELDERLY), "検索語は10個です。")


class ElderlyObservationCountTests(unittest.TestCase):
    """次回の高齢者テーマ更新で、論点比較の文に古い数字が出ないことを固定する。"""

    SENTENCE_HEAD = "「地方の足・移動権」を論点とする投稿は"

    def _comparison_item(self) -> str:
        items = [item for item in _elderly_theme()["observations"] if self.SENTENCE_HEAD in item]
        self.assertEqual(len(items), 1, "論点比較の文が設定に1つだけあること")
        return items[0]

    def test_設定に論点別の件数がべた書きされていない(self) -> None:
        item = self._comparison_item()
        self.assertNotRegex(item, r"\d[\d,]*件", "件数は {issue_count:論点名} で差し込む")
        self.assertIn("{issue_count:地方の足・移動権}", item)
        self.assertIn("{issue_count:義務化・事故防止}", item)

    def test_ページに出る数字は公開データJSONの論点件数と同じ(self) -> None:
        public = json.loads((ROOT / f"data/public/themes/{ELDERLY}.json").read_text(encoding="utf-8"))
        counts = {issue["label"]: issue["count"] for issue in public["issues"]}
        rendered = observations_html(_elderly_theme())
        expected = (
            f"{self.SENTENCE_HEAD}{counts['地方の足・移動権']:,}件で、"
            f"義務化・事故防止（{counts['義務化・事故防止']:,}件）に比べると"
        )
        self.assertIn(expected, rendered)

    def test_ページに出る数字は正典の意見の件数と同じ(self) -> None:
        """公開データJSONを経由せず、正典（非公開）を数え直して突き合わせる。"""
        if not ELDERLY_CANONICAL.is_file():
            self.skipTest("非公開の正典が無い環境では数え直せない")
        counts: dict[str, int] = {}
        for row in json.loads(ELDERLY_CANONICAL.read_text(encoding="utf-8")):
            classification = row.get("classification") or {}
            if classification.get("is_relevant") and classification.get("is_opinion"):
                issue = classification.get("main_issue")
                counts[issue] = counts.get(issue, 0) + 1
        rendered = observations_html(_elderly_theme())
        expected = (
            f"{self.SENTENCE_HEAD}{counts['地方の足・移動権']:,}件で、"
            f"義務化・事故防止（{counts['義務化・事故防止']:,}件）に比べると"
        )
        self.assertIn(expected, rendered)


if __name__ == "__main__":
    unittest.main()
