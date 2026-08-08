import unittest

from scripts.seo.apply_theme_trust import is_opinion


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


if __name__ == "__main__":
    unittest.main()
