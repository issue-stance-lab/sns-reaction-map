"""verify_theme_page.verify_page_count_spans が「意見の推移」の節だけを対象外にすること。"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_theme_page import verify_page_count_spans  # noqa: E402


class PageCountSpansTest(unittest.TestCase):
    TREND = '<section class="trend-card" id="x"><p>投稿は<span id="t">1315件</span>ありました。</p></section>'

    def test_stray_count_outside_the_trend_section_is_rejected(self) -> None:
        lines, failures = verify_page_count_spans("consumption-tax-cut", '<p><span>12件</span></p>')
        self.assertEqual(failures, 1)
        self.assertIn("管理対象外の件数", lines[0])

    def test_count_inside_the_trend_section_is_exempt(self) -> None:
        _, failures = verify_page_count_spans("consumption-tax-cut", self.TREND)
        self.assertEqual(failures, 0)

    def test_only_the_trend_section_is_exempt_not_the_whole_page(self) -> None:
        page = self.TREND + '<p><span>12件</span></p>'
        lines, failures = verify_page_count_spans("consumption-tax-cut", page)
        self.assertEqual(failures, 1)
        self.assertIn("12件", lines[0])
        self.assertNotIn("1315件", lines[0])


if __name__ == "__main__":
    unittest.main()
