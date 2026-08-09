import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "ai-copyright-reaction-map.html"
INDEX = ROOT / "docs" / "index.html"


class ReactionMapDesignPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PAGE.read_text(encoding="utf-8")
        cls.index_source = INDEX.read_text(encoding="utf-8")

    def test_index_and_first_theme_have_scalable_atlas_overview(self):
        for source, markers in (
            (self.index_source, ('id="topic-atlas-overview"', 'id="topic-atlas-title"', 'topic-atlas-rows', '11テーマの論点アトラス')),
            (self.source, ('id="theme-atlas-pilot"', 'theme-atlas-row', '生成AIと著作権 — 論点アトラス')),
        ):
            for marker in markers:
                with self.subTest(marker=marker):
                    self.assertIn(marker, source)

    def test_pilot_uses_question_spine_layout(self):
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
        for marker in (
            "const voteDistance=44+voteStrength*(MAX_SPREAD-44)",
            "権利保護・規制",
            "AI活用・推進",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.source)
        self.assertNotIn("drawArenaSectorHighlight(ctx", self.source)

    def test_pilot_keeps_all_seven_issue_sectors_and_source_links(self):
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
