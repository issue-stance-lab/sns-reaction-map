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

    def test_planet_is_copied_from_source(self):
        """「意見の全体像」は、元HTMLの対話式の山なみ（PLANET_SECTION）をそのまま写す（2026-10-11 に app.js の図から戻した）。"""
        page=str(self.release)
        src=BeautifulSoup(re.search(r"<!-- PLANET_SECTION_START -->(.*?)<!-- PLANET_SECTION_END -->",self.source,re.S).group(1),"html.parser")
        # 山なみのスクリプト・見た目・PLANET_DATA は1文字も変えない
        src_script=[x for x in src.find_all("script",recursive=False) if x.get("id")!="planet-data"][0].string
        for text in (self.page,(self.out/"release"/PAGE).read_text()):
            self.assertEqual(text.count(src_script),1)
            self.assertEqual(text.count(src.select_one("section.planet-panel > style").string),1)
            self.assertEqual(text.count("window.PLANET_DATA="),1)
        # 山なみは #map の中。app.js が描いていた図・論点ボタン・立場の切り替え・読み方は無い
        planet=self.release.select_one("#map section.planet-panel #planet-block")
        self.assertIsNotNone(planet)
        self.assertEqual(self.release.select("#mountains,#mobile-issues,#map-filters,#map-explain,#global-stances,.map-shell,.overview"),[])
        for sel in ("#modes",".stage","#dotbox","#list","#meta",".floor-note",".hint"):
            self.assertEqual(str(planet.select_one(sel)),str(src.select_one("#planet-block "+sel)),sel)
        # JSなしの論点一覧は読書面の各論点（#issue-{論点ID}）へ
        data=json.loads(self.release.select_one("#public-data").get_text())
        hrefs=[a["href"] for a in planet.select("#fallback-nav a")]
        self.assertEqual(sorted(hrefs),sorted("#issue-"+i["id"] for i in data["issues"]))
        for href in hrefs:
            self.assertIsNotNone(self.release.find(id=href[1:]),href)
        # 新デザインで出さない部分は外し、予想・クイズ・進捗は受け皿だけ
        self.assertEqual(planet.select("section.landing-panel, #ocean, #editorial"),[])
        for receiver in ("#guesses","#quiz"):
            node=planet.select_one(receiver)
            self.assertTrue(node.has_attr("hidden") and not node.get_text(strip=True),receiver)
        self.assertTrue(self.release.select_one("#progress").has_attr("hidden"))
        # 調査条件は山なみの中で RESEARCH_CONDITIONS に囲まれている
        self.assertEqual(len(self.release.select("#caution")),1)
        self.assertIsNotNone(planet.select_one("#research-conditions > #caution"))
        block=page[page.index("<!-- RESEARCH_CONDITIONS_START -->"):page.index("<!-- RESEARCH_CONDITIONS_END -->")]
        self.assertIn('id="caution"',block)
        # 論点IDは PLANET_DATA・公開データ・読書面で同じ。読み込み時のURLを山なみより先に控え、橋渡しは app.js の後
        contract=json.loads(re.search(r"window\.PLANET_DATA=(\{.*?\});?</script>",page,re.S).group(1))
        self.assertEqual([i["id"] for i in contract["issues"]],[i["id"] for i in data["issues"]])
        for issue in data["issues"]:
            self.assertIsNotNone(self.release.select_one(f'section.issue-panel#{issue["id"]}'),issue["id"])
        self.assertLess(page.index("window.BUKATSU_LOAD_HASH"),page.index(src_script))
        self.assertLess(page.index("window.BukatsuReading"),page.index("function goReading"))
        self.assertIsNotNone(self.release.select_one("style#bukatsu-planet-style"))
        for name in ("bukatsu-connected.js","bukatsu-connected-page.js","bukatsu-connected.css"):
            self.assertNotIn(f'="{name}',page)
        self.assertNotIn('"planet-block"',page[page.rindex("const aliases="):])
        # 全文・印刷版では山なみ（スクリプトが要る）を外し、調査条件だけ残す
        from scripts.bukatsu_redesign_readable import READ_PAGE
        full=BeautifulSoup((self.out/READ_PAGE).read_text(),"html.parser")
        self.assertFalse(full.select("section.planet-panel,#planet-block,#progress"))
        self.assertEqual(len(full.select("#research-conditions #caution")),1)

    def test_planet_follows_source_updates(self):
        """定期更新で元HTMLの山なみが変われば、新ページにもそのまま載る。部品が欠けたら止まる。"""
        changed=self.source.replace("このページの見かた","このページの見かた（更新確認）",1)
        self.assertNotEqual(changed,self.source)
        page=finalize(self._markup(),changed,"release")
        self.assertIn("このページの見かた（更新確認）",page)
        broken=re.sub(r'<div class="dotbox" id="dotbox".*?<div class="waffle" id="waffle"></div>',"",self.source,count=1,flags=re.S)
        self.assertNotEqual(broken,self.source)
        with self.assertRaisesRegex(ValueError,"山なみの部品"):
            finalize(self._markup(),broken,"release")

    def _markup(self):
        import os,shutil,subprocess,sys
        if not hasattr(type(self),"_raw"):
            with tempfile.TemporaryDirectory() as temp:
                stage=Path(temp);shutil.copytree(RESOURCES,stage/".build",ignore=shutil.ignore_patterns("__pycache__"))
                (stage/"evidence").mkdir()
                env=dict(os.environ,BUKATSU_BUILD_ROOT=str(stage),BUKATSU_REPO_ROOT=str(ROOT))
                subprocess.run([sys.executable,str(stage/".build/build.py"),"--source-page",str(self.source_path)],check=True,env=env,cwd=ROOT,capture_output=True)
                type(self)._raw=(stage/"index.html").read_text()
        return self._raw

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
