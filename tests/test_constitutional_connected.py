import re
import sys
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import constitutional_connected as connected  # noqa: E402
from scripts.constitutional_count_provenance import verified_selectors  # noqa: E402
from scripts.build_constitutional_arena import apply_public_counts  # noqa: E402
from scripts.refresh_adapters.constitutional import vote_fingerprint  # noqa: E402
from scripts.refresh_planet_section import _apply_connected_display  # noqa: E402


class ConstitutionalConnectedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (ROOT / 'docs/constitutional-amendment-reaction-map.html').read_text(encoding='utf-8')
        cls.page = connected.apply(cls.original, activate=True)

    def test_apply_is_idempotent_and_validates(self):
        self.assertEqual(connected.validate(self.page), [])
        self.assertEqual(connected.apply(self.page), self.page)
        self.assertEqual(self.page.count(connected.START), 1)
        self.assertEqual(self.page.count(connected.BRIDGE_START), 1)
        self.assertEqual(self.page.count('constitutional-connected.css?v=3'), 1)

    def test_other_theme_and_unactivated_page_are_unchanged(self):
        self.assertEqual(connected.apply(self.original), self.original)
        other = (ROOT / 'docs/bike-blue-ticket-reaction-map.html').read_text(encoding='utf-8')
        self.assertEqual(connected.apply(other, activate=True, topic='bike-blue-ticket'), other)

    def test_all_issues_have_templates_and_unknown_post_data_is_explicit(self):
        data = connected.planet_data(self.page)
        soup = BeautifulSoup(self.page, 'html.parser')
        for issue in data['issues']:
            template = soup.select_one('#constitutional-amendment-reading-' + issue['id'])
            self.assertIsNotNone(template, issue['id'])
        self.assertEqual(soup.select('[data-ca-post-url]') .__len__(), 12)
        other = soup.select_one('#constitutional-amendment-reading-constitutional-amendment-other')
        self.assertIn('代表投稿が登録されていません', other.decode_contents())

    def test_relationships_use_ids_not_guessed_issue_labels(self):
        data = connected.planet_data(self.page)
        index = connected.content_index(data)
        self.assertEqual(index['issues']['constitutional-amendment-procedure']['source_only_ids'], ['constitutional-amendment-sc-3'])
        self.assertEqual(index['issues']['constitutional-amendment-referendum']['source_only_ids'], ['constitutional-amendment-sc-4'])
        self.assertEqual(
            sorted(item['id'] for item in data['ocean']['sunk_continents']),
            ['constitutional-amendment-challenge', 'constitutional-amendment-emergency-review', 'constitutional-amendment-sc-3', 'constitutional-amendment-sc-4'],
        )
        self.assertIn('constitutional-amendment-challenge', self.page)
        self.assertIn('constitutional-amendment-emergency-review', self.page)

    def test_background_tags_and_untagged_timeline_are_fixed(self):
        background = connected.background_data()
        self.assertEqual(
            {item['id']: item['issue_ids'] for item in background['checklist']['items']},
            {
                'document': ['constitutional-amendment-general', 'constitutional-amendment-article9', 'constitutional-amendment-emergency', 'constitutional-amendment-referendum', 'constitutional-amendment-procedure'],
                'decision': ['constitutional-amendment-procedure', 'constitutional-amendment-referendum'],
                'emergency': ['constitutional-amendment-emergency'],
                'rights': ['constitutional-amendment-general', 'constitutional-amendment-article9', 'constitutional-amendment-emergency'],
            },
        )
        self.assertEqual(len(background['timeline']), 11)
        self.assertTrue(all(not item.get('issue_ids') for item in background['timeline']))

    def test_provenance_checks_reason_concern_and_source_numbers(self):
        result = verified_selectors(self.page, ROOT)
        self.assertGreaterEqual(len(result), 72)

    def test_vote_contract_is_unchanged(self):
        before = vote_fingerprint(self.original)
        after = vote_fingerprint(self.page)
        self.assertEqual(before, after)
        self.assertEqual(after[0], 'constitutional-amendment-issue-stance-v1')
        self.assertEqual(after[3], 24)

    def test_refresh_dispatcher_reapplies_only_an_existing_connection(self):
        self.assertEqual(_apply_connected_display('constitutional-amendment', self.original), self.original)
        refreshed = _apply_connected_display('constitutional-amendment', self.page)
        self.assertEqual(refreshed, self.page)
        self.assertEqual(connected.validate(refreshed), [])

    @unittest.skipUnless(
        (ROOT / 'social-samples/constitutional_amendment_hermes_arena_classified.json').is_file(),
        'private constitutional source is not available; checked locally before publication',
    )
    def test_public_count_refresh_keeps_connection_and_is_idempotent(self):
        updated = apply_public_counts(self.page)
        self.assertEqual(connected.validate(updated), [])
        self.assertEqual(apply_public_counts(updated), updated)
        self.assertEqual(vote_fingerprint(updated), vote_fingerprint(self.page))


if __name__ == '__main__':
    unittest.main()
