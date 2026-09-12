import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.build_constitutional_arena import apply_public_counts, IssueCountError
from scripts.refresh_adapters.constitutional import vote_fingerprint
from scripts.verify_theme_page import _arena_points

ROOT = Path(__file__).resolve().parents[1]

class ConstitutionalPlanetRefreshTests(unittest.TestCase):
    def test_refresh_preserves_vote_contract_and_is_idempotent(self):
        page = (ROOT / 'docs/constitutional-amendment-reaction-map.html').read_text()
        updated = apply_public_counts(page)
        self.assertEqual(vote_fingerprint(updated), vote_fingerprint(page))
        self.assertEqual(vote_fingerprint(updated)[3], 24)
        self.assertEqual(apply_public_counts(updated), updated)
        self.assertEqual(updated.count('<!-- PLANET_SECTION_START -->'), 1)
        self.assertNotIn('id="stance-map-section"', updated)
        self.assertNotIn('id="claim-audit"', updated)

    def test_failed_reread_gate_stops_refresh(self):
        page = (ROOT / 'docs/constitutional-amendment-reaction-map.html').read_text()
        with patch('scripts.build_planet_page_preview.bpd.independence_gate', return_value=['unreviewed record']):
            with self.assertRaisesRegex(IssueCountError, 'unreviewed record'):
                apply_public_counts(page)

    def test_planet_denominator_uses_visible_issue_counts_not_old_points(self):
        data = {'issues': [{'count': 4}, {'count': 3}]}
        page = 'window.PLANET_DATA=' + json.dumps(data) + '; const SM_RAW = [{},{},{}];'
        self.assertEqual(_arena_points(ROOT, page, 'constitutional-amendment'), 7)
