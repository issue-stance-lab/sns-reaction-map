import json
from pathlib import Path
import re
import unittest
from bs4 import BeautifulSoup
from scripts.apply_theme_design import THEMES, transform

ROOT=Path(__file__).resolve().parents[1]
class ThemeDesignTests(unittest.TestCase):
    def test_layer_preserves_content_data_and_identifiers(self):
        for slug in THEMES:
            with self.subTest(slug=slug):
                text=(ROOT/'docs'/f'{slug}-reaction-map.html').read_text()
                result=transform(text,slug)
                self.assertEqual(result,transform(result,slug))
                old=BeautifulSoup(text,'html.parser');new=BeautifulSoup(result,'html.parser')
                self.assertEqual(old.get_text(),new.get_text())
                self.assertEqual([e.get('id') for e in old.select('[id]')],[e.get('id') for e in new.select('[id]')])
                self.assertEqual(old.select_one('#planet-data').string,new.select_one('#planet-data').string)
                self.assertEqual([(e.get('src'),e.string) for e in old.select('script')],[(e.get('src'),e.string) for e in new.select('script')])
    def test_koshitsu_tide_uses_current_classification(self):
        from scripts.inject_tide_widget import THEMES as tide_themes,generate_tide_section
        config=next(t for t in tide_themes if t['slug']=='koshitsu-tenpakai')
        rows=[{'stance':s,'main_issue':'男系vs女系'} for s in config['stance_labels']]
        html=generate_tide_section(config,rows,rows)
        self.assertNotIn('前回収集分0件',html)
        self.assertIn('今回案全体を支持',html)
        self.assertNotIn('改正反対（男系維持）',html)
