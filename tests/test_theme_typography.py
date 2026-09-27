import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
THEME_PAGES = sorted(DOCS.glob("*-reaction-map.html"))


class ThemeTypographyTests(unittest.TestCase):
    def test_all_theme_pages_load_display_and_body_fonts(self):
        self.assertEqual(10, len(THEME_PAGES))
        for page in THEME_PAGES:
            source = page.read_text(encoding="utf-8")
            with self.subTest(page=page.name):
                self.assertIn("family=Noto+Sans+JP:wght@400;700;900", source)
                self.assertIn("family=Noto+Serif+JP:wght@700;900", source)
                self.assertIn('site-tokens.css?v=3', source)
                self.assertIn('topic-modern.css?v=32', source)

    def test_shared_css_keeps_editorial_and_control_roles_separate(self):
        tokens = (DOCS / "site-tokens.css").read_text(encoding="utf-8")
        modern = (DOCS / "topic-modern.css").read_text(encoding="utf-8")
        self.assertIn('--font-body: "Noto Sans JP"', tokens)
        self.assertIn('--font-display: "Noto Serif JP"', tokens)
        for selector in (
            ".hero h1",
            ".panel-title h2",
            ".article-trust-heading h2",
            ".classroom-heading h2",
            ".stat:first-child strong",
        ):
            self.assertIn(selector, modern)
        self.assertRegex(modern, r"body\s*\{[^}]*font-family:\s*var\(--font-body")

    def test_base_builder_preserves_font_pair_on_regeneration(self):
        builder = (ROOT / "scripts" / "build_reaction_map.py").read_text(encoding="utf-8")
        self.assertIn("family=Noto+Sans+JP:wght@400;700;900", builder)
        self.assertIn("family=Noto+Serif+JP:wght@700;900", builder)

    def test_seo_updater_keeps_current_stylesheet_version(self):
        updater = (ROOT / "scripts" / "seo" / "apply_theme_trust.py").read_text(encoding="utf-8")
        self.assertIn('TOPIC_CSS_VERSION = "32"', updater)


if __name__ == "__main__":
    unittest.main()
