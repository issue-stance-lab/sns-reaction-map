"""Release candidate invariants independent of production writes."""
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
from bs4 import BeautifulSoup
from scripts.build_bukatsu_redesign import build, finalize, fingerprint, ROOT, PAGE, PRINT_PAGE, RESOURCES

class RedesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        from scripts.bukatsu_layout import source_for_refresh
        cls.source_path = source_for_refresh(ROOT)
        cls.source = cls.source_path.read_text()
        cls.manifest = build(cls.source_path, cls.out)
        cls.page = (cls.out / PAGE).read_text()
        cls.s = BeautifulSoup(cls.page, "html.parser")
        build(cls.source_path, cls.out / "release", "release")
        cls.release = BeautifulSoup((cls.out / "release" / PAGE).read_text(), "html.parser")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_rebuild_deterministic(self):
        first = (self.out / PAGE).read_bytes()
        build(self.source_path, self.out)
        self.assertEqual(first, (self.out / PAGE).read_bytes())

    def test_issue_and_reason_data_preserved(self):
        old = BeautifulSoup(self.source, "html.parser")
        data = json.loads(old.select_one("#planet-data").get_text().split("=",1)[1].strip().rstrip(";"))
        new = json.loads(self.s.select_one("#public-data").get_text())
        self.assertEqual(data["totals"], new["totals"])
        self.assertEqual(data["modes"], new["modes"])
        for issue in data["issues"]:
            panel = self.s.find(id=issue["id"])
            for item in issue["sub"].get("items",[]):
                button = panel.select_one('[data-reason="'+item["id"]+'"]')
                self.assertEqual(button.b.get_text(), str(item["count"])+"件")

    def test_vote_mapping_and_storage_compatible(self):
        for text in (self.page, str(self.release)):
            self.assertIn("bukatsu-chiiki-issue-stance-v1", text)
            self.assertIn("choiceIdx:issueIdx*STANCES.length+stanceIdx", text)
            original = re.search(r"var VOTE_ISSUES=(.*?);", self.source, re.S).group(1)
            self.assertEqual(original, re.search(r"var VOTE_ISSUES=(.*?);", text, re.S).group(1))
            self.assertIn("window.SNS_REDESIGN_PRODUCTION?'sns_vote_':'sns_vote_preview_'",text)

    def test_config_guard_before_vote_client(self):
        scripts=self.s.select("script")
        config=next(i for i,x in enumerate(scripts) if x.get("src")=="vote-config.js")
        client=next(i for i,x in enumerate(scripts) if x.get("src")=="vote-store.js")
        self.assertEqual(config+2,client)
        self.assertIn("SNS_REDESIGN_PRODUCTION=false",scripts[config+1].get_text())
        self.assertIn("location.hostname==='sns-reaction-map.jp'",str(self.release))
        for name in ("vote-store.js","vote-config.js"):
            self.assertEqual((ROOT/"docs"/name).read_bytes(),(self.out/name).read_bytes())

    def test_metadata_and_integrations(self):
        self.assertEqual(len(self.s.select('meta[name="description"]')),1)
        self.assertIn("noindex",self.s.select_one('meta[name="robots"]')["content"])
        self.assertFalse(self.release.select('meta[name="robots"]'))
        self.assertTrue(self.release.select_one('script[src*="adsbygoogle"]'))
        self.assertFalse(self.s.select_one('script[src*="adsbygoogle"]'))
        for marker in ("GA_TAG_START","GA_TAG_END","ADSENSE_TAG_START","ADSENSE_TAG_END"):
            self.assertIn(marker,str(self.release))

    def test_read_progress_migrates_only_equivalent_topics(self):
        self.assertIn("isa-seen-bukatsu-chiiki",self.page)
        self.assertIn("isa-reading-bukatsu-chiiki-v2",self.page)
        self.assertIn("x.startsWith('i:')",self.page)

    def test_anchors_and_assets(self):
        ids=[x["id"] for x in self.s.select("[id]")]
        self.assertEqual(len(ids),len(set(ids)))
        for a in self.s.select('a[href^="#"]'):
            if a["href"]!="#":self.assertIn(a["href"][1:],ids)
        for image in self.s.select("img[src]"):
            self.assertTrue((self.out/image["src"]).is_file())
        page=BeautifulSoup((self.out/PRINT_PAGE).read_text(),"html.parser")
        for a in page.select('a[href^="'+PAGE+'#"]'):
            self.assertIn(a["href"].split("#")[1],ids)

    def test_embed_cap_and_content_parity(self):
        for group in self.s.select(".original-posts,.issue-examples"):
            self.assertLessEqual(len(group.select(".twitter-tweet")),2)
        for selector,count in (("#faq>details",6),(".issue-illustration",7),("[data-trend-download]",4)):
            self.assertEqual(len(self.s.select(selector)),count)

    def test_full_reading_without_javascript_preserves_all_reasons(self):
        from scripts.bukatsu_redesign_readable import READ_PAGE
        full=BeautifulSoup((self.out/READ_PAGE).read_text(),"html.parser")
        self.assertFalse(full.select('script,iframe'))
        self.assertFalse(full.select('.issue-panel[hidden],.reason-detail[hidden],details:not([open])'))
        self.assertEqual(len(full.select('.issue-panel')),7)
        self.assertEqual([n.get_text(" ",strip=True) for n in full.select('.reason-detail>h3')],
                         [n.get_text(" ",strip=True) for n in self.s.select('.reason-detail>h3')])
        self.assertEqual(len(full.select('.trend-table tbody tr')),len(self.s.select('.trend-table tbody tr')))
        self.assertTrue(full.select('.trend-table tbody tr'))
        self.assertIn(READ_PAGE,self.manifest['files'])
        ids={n['id'] for n in full.select('[id]')}
        for a in full.select('a[href^="#"]'):self.assertIn(a['href'][1:],ids)
        self.assertIn(READ_PAGE,str(self.s.select_one('noscript')))

    def test_changed_editorial_stops_without_overwrite(self):
        before=(self.out/PAGE).read_bytes()
        with patch("scripts.build_bukatsu_redesign.fingerprint",return_value="changed"):
            with self.assertRaisesRegex(ValueError,"参照本文"):
                build(self.source_path,self.out)
        self.assertEqual(before,(self.out/PAGE).read_bytes())

    def test_never_writes_docs(self):
        with self.assertRaisesRegex(ValueError,"公開先docs"):
            build(self.source_path,ROOT/"docs")

    def test_publication_validator_checks_rendered_counts(self):
        from scripts.verify_theme_page import _planet_data, verify_planet_breakdowns
        data = _planet_data(self.page)
        self.assertEqual(verify_planet_breakdowns("bukatsu-chiiki",self.page,data)[1],0)
        bad = BeautifulSoup(self.page,"html.parser")
        bad.select_one('.reason-choice b').string="999件"
        self.assertGreater(verify_planet_breakdowns("bukatsu-chiiki",str(bad),data)[1],0)

    def test_public_data_driving_ui_matches_contract(self):
        from scripts.verify_theme_page import _planet_data
        contract=_planet_data(self.page)
        ui=json.loads(self.s.select_one("#public-data").get_text())
        self.assertEqual(ui["modes"],contract["modes"])
        self.assertEqual(ui["stances"],contract["stances"])
        self.assertEqual(ui["issues"],[{k:i[k] for k in ("id","label","count","high_pct")} for i in contract["issues"]])

    def test_independent_reason_count_provenance(self):
        from scripts.bukatsu_redesign_provenance import verify_counts
        self.assertTrue(verify_counts(self.page,ROOT))
        bad=BeautifulSoup(self.page,"html.parser")
        bad.select_one(".reason-choice b").string="999件"
        with self.assertRaisesRegex(ValueError,"理由の件数"):
            verify_counts(str(bad),ROOT)

    def test_generated_scripts_parse(self):
        import subprocess
        for i,script in enumerate(self.s.select('script:not([src]):not([type="application/ld+json"]):not([type="application/json"])')):
            if not script.get_text().strip():continue
            path=self.out/f"script-{i}.js"
            path.write_text(script.get_text())
            subprocess.run(["node","--check",str(path)],check=True,capture_output=True)

if __name__=="__main__":
    unittest.main()
