import json
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
NEW_ORIGIN = "https://sns-reaction-map.jp"
NEW_HOST = "sns-reaction-map.jp"
OLD_HOST = "issue-stance-lab.github.io"
OLD_SITE_BASE = "https://issue-stance-lab.github.io/sns-reaction-map/"


class DomainMigrationTests(unittest.TestCase):
    def test_sitemap_only_contains_new_domain(self):
        tree = ElementTree.parse(DOCS / "sitemap.xml")
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [node.text for node in tree.findall("sm:url/sm:loc", namespace)]
        self.assertGreater(len(urls), 0)
        self.assertTrue(all(url and url.startswith(f"{NEW_ORIGIN}/") for url in urls))

    def test_every_sitemap_page_has_new_canonical_and_og_url(self):
        tree = ElementTree.parse(DOCS / "sitemap.xml")
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for node in tree.findall("sm:url/sm:loc", namespace):
            url = node.text or ""
            relative = url.removeprefix(f"{NEW_ORIGIN}/")
            page = DOCS / relative
            html = page.read_text(encoding="utf-8")
            expected = NEW_ORIGIN + "/" if relative == "index.html" else url
            with self.subTest(page=relative):
                self.assertRegex(
                    html,
                    rf'<link rel="canonical" href="{re.escape(expected)}">',
                )
                self.assertRegex(
                    html,
                    rf'<meta property="og:url" content="{re.escape(expected)}">',
                )

    def test_robots_points_to_new_sitemap(self):
        robots = (DOCS / "robots.txt").read_text(encoding="utf-8")
        self.assertIn(f"Sitemap: {NEW_ORIGIN}/sitemap.xml", robots)
        self.assertNotIn("issue-stance-lab.github.io", robots)

    def test_active_public_assets_do_not_reference_old_site_base(self):
        checked = [DOCS, ROOT / "configs"]
        for directory in checked:
            for path in directory.rglob("*"):
                if not path.is_file():
                    continue
                if "prompts" in path.parts:
                    continue
                if path.suffix.lower() not in {".html", ".xml", ".txt", ".json", ".md"}:
                    continue
                with self.subTest(path=path.relative_to(ROOT)):
                    self.assertNotIn(OLD_SITE_BASE, path.read_text(encoding="utf-8"))

    def test_vote_service_allows_new_and_legacy_origins_during_transition(self):
        source = (ROOT / "supabase" / "functions" / "cast-vote" / "index.ts").read_text(
            encoding="utf-8"
        )
        self.assertIn("https://sns-reaction-map.jp", source)
        self.assertIn("https://issue-stance-lab.github.io", source)

    def test_published_pages_gate_analytics_to_new_host(self):
        pages = [p for p in DOCS.glob("*.html") if "allowedHosts" in p.read_text(encoding="utf-8")]
        self.assertGreater(len(pages), 0)
        for page in pages:
            html = page.read_text(encoding="utf-8")
            with self.subTest(page=page.relative_to(ROOT)):
                match = re.search(r"var allowedHosts = (\[[^\]]*\]);", html)
                self.assertIsNotNone(match, "allowedHosts の配列が見つからない")
                hosts = json.loads(match.group(1))
                self.assertIn(NEW_HOST, hosts)
                self.assertNotIn(OLD_HOST, hosts)

    def test_cname_file_matches_custom_domain(self):
        cname = DOCS / "CNAME"
        self.assertTrue(cname.exists(), "docs/CNAME が無い。カスタムドメイン設定がデプロイで外れる")
        self.assertEqual(cname.read_text(encoding="utf-8").strip(), NEW_HOST)

    def test_scripts_have_no_old_origin_url_constants(self):
        for path in (ROOT / "scripts").rglob("*.py"):
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotIn(OLD_HOST, path.read_text(encoding="utf-8"))

    def test_ads_txt_exists(self):
        ads = DOCS / "ads.txt"
        self.assertTrue(ads.exists(), "docs/ads.txt が無い。AdSense収益化に必要")
        self.assertIn("pub-2542211932832864", ads.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
