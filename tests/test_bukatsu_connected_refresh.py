"""refresh_planet_section.refresh()が、bukatsu-chiikiの連動表示を再適用することを確認する。

課題77工程5で発覚したバグの再発防止検査。refresh_planet_section.pyの仕上げ処理は
以前 consumption_tax_connected だけを無条件に呼んでおり、他テーマ（bukatsu-chiiki含む）は
その関数自身のtopicガードで無変更のまま素通りしていた。エラーにはならないため、
bukatsu-chiikiの連動表示は「公開後の通常データ更新のどこからも再適用されない」まま
気づかれずに残っていた。ここでは公開データ（docs/のPLANET_DATA）をbpd.build()の
戻り値として差し替え、非公開正典なしで実際のrefresh()経路を通す。
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from scripts import bukatsu_connected as connected
from refresh_planet_section import refresh, _apply_connected_display


class BukatsuConnectedRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (ROOT / "docs/bukatsu-chiiki-reaction-map.html").read_text(encoding="utf-8")
        cls.enabled_page = connected.apply(cls.original, activate=True)
        cls.data = connected.planet_data(cls.enabled_page)

    def test_dispatcher_reapplies_when_already_enabled_and_stays_idempotent(self):
        out = _apply_connected_display("bukatsu-chiiki", self.enabled_page)
        self.assertEqual(connected.validate(out), [])
        self.assertEqual(out, self.enabled_page, "再適用のたびに差分が出る（冪等性が崩れている）")

    def test_dispatcher_does_not_activate_a_page_that_never_opted_in(self):
        out = _apply_connected_display("bukatsu-chiiki", self.original)
        self.assertEqual(out, self.original, "工程6の前に勝手に有効化している")

    def test_dispatcher_leaves_other_topics_untouched(self):
        # bikeなど、bukatsu-chiikiでも消費税でもないテーマは無変更のまま。
        other = (ROOT / "docs/bike-blue-ticket-reaction-map.html").read_text(encoding="utf-8")
        self.assertEqual(_apply_connected_display("bike-blue-ticket", other), other)

    def test_real_refresh_entry_point_keeps_the_connection_alive(self):
        # bpd.build()を実データ（公開済みdocsのPLANET_DATA）に差し替え、
        # 非公開正典を要さずにrefresh()の実経路を通す。
        with patch("refresh_planet_section.bpd.build", return_value=self.data):
            _, page, failures = refresh("bukatsu-chiiki", source=self.enabled_page)
        self.assertEqual(failures, [])
        self.assertEqual(connected.validate(page), [], "refresh()後に連動表示の検査が通らない")
        self.assertIn("BUKATSU_CONNECTED_CONTENT_START", page, "読書面テンプレートが失われている")

    def test_real_refresh_is_idempotent_across_two_runs(self):
        with patch("refresh_planet_section.bpd.build", return_value=self.data):
            _, first, failures1 = refresh("bukatsu-chiiki", source=self.enabled_page)
            self.assertEqual(failures1, [])
            _, second, failures2 = refresh("bukatsu-chiiki", source=first)
        self.assertEqual(failures2, [])
        self.assertEqual(first, second, "2回目のrefresh()で差分が出る")


if __name__ == "__main__":
    unittest.main()
