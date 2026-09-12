import json
import unittest
from pathlib import Path
from scripts.build_henoko_arena import build_page, load_records, apply_public_counts
from scripts.verify_theme_page import _arena_points
from scripts.build_planet_page_preview import fix_henoko_vote_scroll

ROOT = Path(__file__).resolve().parents[1]
TOPIC = 'henoko-student-accident'

class HenokoPlanetTests(unittest.TestCase):
    def test_map_check_uses_visible_mountains_even_if_legacy_asset_exists(self):
        page = 'window.PLANET_DATA=' + json.dumps({'issues': [{'count': 7}, {'count': 9}]})
        self.assertEqual(_arena_points(ROOT, page, TOPIC), 16)

    def test_legacy_map_check_remains_supported(self):
        self.assertEqual(_arena_points(ROOT, 'const HENOKO_ARENA_RAW=[{"i":0},{"i":1}];', TOPIC), 2)

    def test_refresh_preserves_votes_and_does_not_restore_old_map(self):
        page = (ROOT / 'docs' / (TOPIC + '-reaction-map.html')).read_text()
        if (ROOT / 'social-samples/henoko/henoko_hermes_arena_classified.json').exists():
            records, opinions = load_records(None)
            self.assertEqual(build_page(page, records, opinions), fix_henoko_vote_scroll(page))
        self.assertEqual(apply_public_counts(page), fix_henoko_vote_scroll(page))
        self.assertNotIn('HENOKO_ARENA_RAW', page)
        self.assertIn('id="issue-arena-section"', page)
        self.assertIn("choiceIdx:selected*STANCES.length+index", page)

    def test_claim_and_common_concern_evidence_exists_in_current_opinions(self):
        records = json.loads((ROOT / 'data/verification' / (TOPIC + '.json')).read_text())
        indexed = {x['record_id_hash']: x['classification'] for x in records}
        claims = json.loads((ROOT / 'data/verification' / (TOPIC + '-claims.json')).read_text())
        for claim in claims:
            self.assertTrue(indexed[claim['record_id_hash']]['is_opinion'])
        veins = json.loads((ROOT / 'data/verification' / (TOPIC + '-veins.json')).read_text())
        for item in veins['items']:
            for side in item['sides']:
                for p in side['representative_posts']:
                    self.assertEqual(indexed[p['record_id_hash']]['stance'], side['stance_label'])
