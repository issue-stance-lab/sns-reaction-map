import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "ai-copyright-reaction-map.html"
INDEX = ROOT / "docs" / "index.html"


class ReactionMapDesignPilotTests(unittest.TestCase):
    """ai-copyright だけに行った「question spine」2Dデザイン実験の回帰検査。

    課題54で本番が山なみ形式へ差し替え済み（オーナー承認済みの後継デザイン）。
    この実験自体が山なみに置き換えられて役目を終えたため、対応する旧マーカーが
    無いテストは山なみ形式では対象外にする（is_planet ガード）。トップページ側の
    論点アトラス（全10テーマ比較）は本テストの対象外で別物のため、山なみ移行の
    影響を受けない。
    """

    @classmethod
    def setUpClass(cls):
        cls.source = PAGE.read_text(encoding="utf-8")
        cls.index_source = INDEX.read_text(encoding="utf-8")
        cls.is_planet = "<!-- PLANET_SECTION_START -->" in cls.source

    def test_index_and_first_theme_have_scalable_atlas_overview(self):
        for marker in ('id="topic-atlas-overview"', 'id="topic-atlas-title"', 'topic-atlas-rows', '10テーマの論点アトラス'):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.index_source)
        if self.is_planet:
            self.skipTest("ai-copyright は山なみ形式へ差し替え済み。テーマページ側のテーマ別アトラスは実験ごと廃止された")
        for marker in ('id="theme-atlas-pilot"', 'theme-atlas-row', '生成AIと著作権 — 論点アトラス'):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.source)

    def test_pilot_uses_question_spine_layout(self):
        if self.is_planet:
            self.skipTest("ai-copyright は山なみ形式へ差し替え済み。question spine実験は山なみに置き換わった")
        for marker in (
            'id="arena-question-spine-pilot"',
            'class="arena-spine-layout"',
            'class="arena-spine-key"',
            "未解決の問い",
            "sideOf(p)",
            "const spread=side===0?",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.source)
        # 件数はビルダが生成するので、値ではなく形だけを検査する（データ更新で落とさない）
        self.assertRegex(self.source, r"問いから分かれる、[\d,]+件の意見")
        self.assertNotIn('media="not all"', self.source)
        self.assertEqual(self.source.count("7つの論点"), 0)
        self.assertIn("6つの論点とXの声", self.source)

    def test_pilot_encodes_stance_and_strength_without_polar_sectors(self):
        if self.is_planet:
            self.skipTest("ai-copyright は山なみ形式へ差し替え済み。極座標の代替だったspine実験は山なみに置き換わった")
        for marker in (
            "const voteDistance=44+voteStrength*(MAX_SPREAD-44)",
            "権利保護・規制",
            "AI活用・推進",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.source)
        self.assertNotIn("drawArenaSectorHighlight(ctx", self.source)

    def test_pilot_keeps_all_seven_issue_sectors_and_source_links(self):
        if self.is_planet:
            self.skipTest("ai-copyright は山なみ形式へ差し替え済み。旧アリーナのセクター描画は撤去済み（7論点は山なみ本体のissuesが引き継ぐ）")
        self.assertIn("ISSUES.forEach((iss,i)=>addBtn(iss.k,i,iss.n));", self.source)
        self.assertIn("const ISSUES=[", self.source)
        self.assertIn("{k:'その他',", self.source)
        self.assertIn("window.open(pt.p.u,'_blank','noopener')", self.source)

    def test_pilot_keeps_protected_site_features(self):
        for marker in (
            "G-K10S4YCZFH",
            "ca-pub-2542211932832864",
            "ogp/ai-copyright.png",
            "vote-store.js",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.source)


if __name__ == "__main__":
    unittest.main()
