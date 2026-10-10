import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from bs4 import BeautifulSoup
from scripts import bukatsu_layout as layout
from scripts.build_bukatsu_redesign import ROOT, REVIEW_INPUTS, RESOURCES

class LayoutTests(unittest.TestCase):
    def test_disabled_has_no_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(layout.finish(Path(temp)),{})

    def test_new_page_without_source_stops(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"docs").mkdir()
            (root/layout.PAGE).write_text('<meta name="bukatsu-layout">')
            (root/"configs").mkdir()
            (root/layout.CONFIG).write_text('{"enabled":true}')
            with self.assertRaisesRegex(ValueError,"更新元HTML"):
                layout.source_for_refresh(root)
            (root/layout.CONFIG).write_text('{"enabled":false}')
            with self.assertRaisesRegex(ValueError,"更新設定が無効"):
                layout.source_for_refresh(root)

    def test_pipeline_rebuild_keeps_design_and_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"docs").mkdir()
            source=layout.source_for_refresh(ROOT).read_text()
            (root/layout.PAGE).write_text(source)
            for name in ("vote-store.js","vote-config.js"):
                shutil.copy2(ROOT/"docs"/name,root/"docs"/name)
            soup=BeautifulSoup(source,"html.parser")
            # All images potentially imported by parity, including download-only assets.
            for n in soup.select("img[src],a[href]"):
                path=n.get("src",n.get("href","")).removeprefix("https://sns-reaction-map.jp/")
                if path.startswith("images/") and (ROOT/"docs"/path).is_file():
                    target=root/"docs"/path;target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(ROOT/"docs"/path,target)
            for name in REVIEW_INPUTS:
                target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(ROOT/name,target)
            shutil.copytree(RESOURCES,root/"scripts/bukatsu_redesign")
            (root/"configs").mkdir()
            (root/layout.CONFIG).write_text('{"enabled":true}')
            targets=layout.finish(root)
            self.assertIn(layout.SOURCE,targets)
            self.assertIn(Path("docs/bukatsu-chiiki-classroom.html"),targets)
            first=(root/layout.PAGE).read_bytes()
            self.assertIn(b'bukatsu-layout',first)
            self.assertEqual(source,(root/layout.SOURCE).read_text())
            self.assertEqual(layout.source_for_refresh(root),root/layout.SOURCE)
            # Existing update/SEO passes receive legacy source; layout is always the last pass.
            shutil.copy2(layout.source_for_refresh(root),root/layout.PAGE)
            layout.finish(root)
            self.assertEqual(first,(root/layout.PAGE).read_bytes())
            with self.assertRaisesRegex(ValueError,"再入力"):
                layout.finish(root)

if __name__=="__main__":
    unittest.main()
