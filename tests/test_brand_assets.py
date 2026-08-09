import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as source:
        header = source.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"PNGではありません: {path}")
    return struct.unpack(">II", header[16:24])


class BrandAssetTests(unittest.TestCase):
    def test_selected_mark_is_used_by_shared_headers(self):
        expected = {
            "index.html": 'src="images/brand/mark.svg"',
            "usage.html": 'src="images/brand/mark.svg"',
            "ai-copyright-reaction-map.html": 'src="images/brand/mark.svg"',
        }
        for filename, marker in expected.items():
            with self.subTest(filename=filename):
                self.assertIn(marker, (DOCS / filename).read_text(encoding="utf-8"))

    def test_index_uses_person_free_brand_illustrations(self):
        source = (DOCS / "index.html").read_text(encoding="utf-8")
        expected = [
            "voices-map.svg",
            "organize-map.svg",
            "perspectives-map.svg",
            "vote-map.svg",
            "divider-routes.svg",
            "topics-landscape.svg",
            "footer-map.svg",
        ]
        for filename in expected:
            with self.subTest(filename=filename):
                self.assertIn(f"images/site-v2/{filename}", source)
                asset = DOCS / "images" / "site-v2" / filename
                self.assertTrue(asset.exists())
                self.assertNotIn("<text", asset.read_text(encoding="utf-8").lower())
        self.assertNotRegex(source, r"images/site/[1-7]\.(?:png|webp)")

    def test_social_and_icon_exports_have_required_sizes(self):
        expected = {
            DOCS / "ogp" / "default.png": (1200, 630),
            DOCS / "images" / "brand" / "x-header.png": (1500, 500),
            DOCS / "images" / "brand" / "x-avatar.png": (400, 400),
            DOCS / "apple-touch-icon.png": (180, 180),
        }
        for path, size in expected.items():
            with self.subTest(path=path.name):
                self.assertEqual(size, png_size(path))

    def test_top_page_keeps_measurement_and_social_metadata(self):
        source = (DOCS / "index.html").read_text(encoding="utf-8")
        for marker in (
            "G-K10S4YCZFH",
            "ca-pub-2542211932832864",
            "ogp/default.png",
            'rel="icon" href="favicon.svg"',
            'rel="apple-touch-icon" href="apple-touch-icon.png"',
        ):
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
