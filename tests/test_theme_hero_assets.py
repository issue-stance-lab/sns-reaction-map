import re
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "ai-copyright-reaction-map.html"
HERO = ROOT / "docs" / "images" / "topics" / "ai-copyright" / "ai-copyright-hero.webp"


class ThemeHeroAssetTests(unittest.TestCase):
    def test_ai_copyright_page_uses_the_canonical_hero(self):
        html = PAGE.read_text(encoding="utf-8")

        self.assertGreaterEqual(html.count("ai-copyright-hero.webp"), 2)
        self.assertNotIn("ai-copyright-hero-v2.webp", html)
        self.assertIn('content="https://issue-stance-lab.github.io/sns-reaction-map/ogp/ai-copyright.png"', html)
        self.assertIn("G-K10S4YCZFH", html)
        self.assertIn("ca-pub-2542211932832864", html)

    def test_ai_copyright_hero_has_web_sized_dimensions(self):
        self.assertTrue(HERO.exists())
        self.assertLess(HERO.stat().st_size, 200_000)

        with Image.open(HERO) as image:
            self.assertEqual(image.size, (1536, 1024))
            self.assertEqual(image.format, "WEBP")

    def test_existing_infographics_are_unchanged_in_the_page(self):
        html = PAGE.read_text(encoding="utf-8")
        infographic_sources = set(
            re.findall(r'images/topics/ai-copyright/ai-copyright-infographic-wide-[a-z]+\.webp', html)
        )
        self.assertEqual(len(infographic_sources), 6)


if __name__ == "__main__":
    unittest.main()
