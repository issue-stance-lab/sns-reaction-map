import tempfile
import unittest
from pathlib import Path

from scripts import sync_public_site


class PublicSiteSyncTests(unittest.TestCase):
    def test_sync_copies_site_and_generates_legacy_redirects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "docs"
            target = root / "public"
            source.mkdir()
            (source / "index.html").write_text("<h1>home</h1>", encoding="utf-8")
            (source / "topic.html").write_text("<h1>topic</h1>", encoding="utf-8")
            (source / "asset.png").write_bytes(b"png")

            count = sync_public_site.sync(source, target)

            self.assertEqual(count, 7)
            self.assertEqual((target / "index.html").read_text(encoding="utf-8"), "<h1>home</h1>")
            self.assertEqual((target / "asset.png").read_bytes(), b"png")
            self.assertEqual((target / "CNAME").read_text(encoding="utf-8"), "sns-reaction-map.jp\n")
            redirect = (target / "sns-reaction-map" / "topic.html").read_text(encoding="utf-8")
            self.assertIn("https://sns-reaction-map.jp/topic.html", redirect)
            self.assertIn('name="robots" content="noindex,follow"', redirect)
            self.assertEqual(sync_public_site.differences(source, target), [])

    def test_check_detects_changed_and_stale_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "docs"
            target = root / "public"
            source.mkdir()
            (source / "index.html").write_text("first", encoding="utf-8")
            sync_public_site.sync(source, target)

            (source / "index.html").write_text("second", encoding="utf-8")
            errors = sync_public_site.differences(source, target)
            self.assertIn("different: index.html", errors)
            self.assertNotIn("different: sns-reaction-map/index.html", errors)


if __name__ == "__main__":
    unittest.main()
