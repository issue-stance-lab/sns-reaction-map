import re
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "ai-copyright-reaction-map.html"
HERO = ROOT / "docs" / "images" / "topics" / "ai-copyright" / "ai-copyright-hero.webp"
BIKE_PAGE = ROOT / "docs" / "bike-blue-ticket-reaction-map.html"
BIKE_HERO = ROOT / "docs" / "images" / "topics" / "bike-blue-ticket" / "bike-blue-ticket-hero.webp"
BUKATSU_PAGE = ROOT / "docs" / "bukatsu-chiiki-reaction-map.html"
BUKATSU_HERO = ROOT / "docs" / "images" / "topics" / "bukatsu-chiiki" / "bukatsu-hero.webp"

REMAINING_HEROES = {
    "constitutional-amendment": {
        "page": "constitutional-amendment-reaction-map.html", "asset": "constitutional-hero.webp",
        "path": ("constitutional-amendment", "constitutional-hero.webp"), "size": (1807, 870),
        "ogp": "ogp/constitutional-amendment.png",
    },
    "elderly-license-revocation": {
        "page": "elderly-license-revocation-reaction-map.html", "asset": "elderly-license-revocation-hero.webp",
        "path": ("elderly-license-revocation", "elderly-license-revocation-hero.webp"), "size": (1725, 912),
        "ogp": "ogp/elderly-license-revocation.png",
    },
    "school-nickname-ban": {
        "page": "school-nickname-ban-reaction-map.html", "asset": "school-nickname-hero.webp",
        "path": ("school-nickname-ban", "school-nickname-hero.webp"), "size": (1726, 911),
        "ogp": "ogp/school-nickname-ban.png",
    },
    "henoko-student-accident": {
        "page": "henoko-student-accident-reaction-map.html", "asset": "henoko-hero.webp",
        "path": ("henoko-student-accident", "henoko-hero.webp"), "size": (1726, 911),
        "ogp": "ogp/henoko-student-accident.png",
    },
    "takaichi": {
        "page": "takaichi-reaction-map-standard.html", "asset": "takaichi-hero.webp",
        "path": ("takaichi", "takaichi-hero.webp"), "size": (1718, 916), "ogp": "ogp/takaichi.png",
    },
    "fukushuto": {
        "page": "fukushuto-reaction-map.html", "asset": "fukushuto-hero.webp",
        "path": ("fukushuto", "fukushuto-hero.webp"), "size": (1727, 910),
        "ogp": "images/topics/fukushuto/fukushuto-hero.webp",
    },
    "koshitsu-tenpakai": {
        "page": "koshitsu-tenpakai-reaction-map.html", "asset": "koshitsu-hero.webp",
        "path": ("koshitsu-tenpakai", "koshitsu-hero.webp"), "size": (1726, 911),
        "ogp": "images/topics/koshitsu-tenpakai/koshitsu-hero.webp",
    },
    "consumption-tax-cut": {
        "page": "consumption-tax-cut-reaction-map.html", "asset": "consumption-tax-cut-hero.webp",
        "path": ("consumption-tax-cut", "consumption-tax-cut-hero.webp"), "size": (1729, 910),
        "ogp": "images/topics/consumption-tax-cut/consumption-tax-cut-hero.webp",
    },
}


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

    def test_bike_page_uses_the_canonical_hero_and_keeps_protected_features(self):
        html = BIKE_PAGE.read_text(encoding="utf-8")

        self.assertGreaterEqual(html.count("bike-blue-ticket-hero.webp"), 2)
        self.assertNotIn("bike-blue-ticket-hero-v2.webp", html)
        self.assertIn('content="https://issue-stance-lab.github.io/sns-reaction-map/ogp/bike-blue-ticket.png"', html)
        self.assertIn("G-K10S4YCZFH", html)
        self.assertIn("ca-pub-2542211932832864", html)

    def test_bike_hero_has_web_sized_dimensions(self):
        self.assertTrue(BIKE_HERO.exists())
        self.assertLess(BIKE_HERO.stat().st_size, 200_000)

        with Image.open(BIKE_HERO) as image:
            self.assertEqual(image.size, (1536, 1024))
            self.assertEqual(image.format, "WEBP")

    def test_bukatsu_page_uses_the_canonical_hero_and_keeps_protected_features(self):
        html = BUKATSU_PAGE.read_text(encoding="utf-8")

        self.assertGreaterEqual(html.count("bukatsu-hero.webp"), 2)
        self.assertNotIn("bukatsu-hero-v2.webp", html)
        self.assertIn('content="https://issue-stance-lab.github.io/sns-reaction-map/ogp/bukatsu-chiiki.png"', html)
        self.assertIn("G-K10S4YCZFH", html)
        self.assertIn("ca-pub-2542211932832864", html)

    def test_bukatsu_hero_has_web_sized_dimensions(self):
        self.assertTrue(BUKATSU_HERO.exists())
        self.assertLess(BUKATSU_HERO.stat().st_size, 200_000)

        with Image.open(BUKATSU_HERO) as image:
            self.assertEqual(image.size, (1672, 941))
            self.assertEqual(image.format, "WEBP")

    def test_remaining_theme_heroes_use_canonical_assets(self):
        for slug, spec in REMAINING_HEROES.items():
            with self.subTest(theme=slug):
                page = ROOT / "docs" / spec["page"]
                html = page.read_text(encoding="utf-8")

                self.assertGreaterEqual(html.count(spec["asset"]), 2)
                self.assertNotIn("-hero-v2.webp", html)
                self.assertIn(spec["ogp"], html)
                self.assertIn("G-K10S4YCZFH", html)
                self.assertIn("ca-pub-2542211932832864", html)

                folder, filename = spec["path"]
                hero = ROOT / "docs" / "images" / "topics" / folder / filename
                self.assertTrue(hero.exists())
                self.assertLess(hero.stat().st_size, 200_000)

                with Image.open(hero) as image:
                    self.assertEqual(image.size, spec["size"])
                    self.assertEqual(image.format, "WEBP")


if __name__ == "__main__":
    unittest.main()
