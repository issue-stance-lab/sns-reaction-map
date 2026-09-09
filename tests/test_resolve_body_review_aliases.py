import copy
import unittest
from scripts.resolve_body_review_aliases import link_aliases, stored_user_comparison, EXISTING, REMAINING


class AliasLinksTests(unittest.TestCase):
    def setUp(self):
        self.alias = dict(topic='t', record_id_hash='alias', body_sha256='body', classification_sha256='class', exclusion_reasons=[EXISTING])
        self.source = dict(topic='t', record_id_hash='source', body_sha256='body', classification_sha256='class', criteria_sha256='criterion', work_key='work', state='hold', evidence=['packet'])
        self.inv = {'excluded_unconfirmed': [self.alias], 'eligible_inventory_only': []}
        self.decision = {('t', 'source'): {**self.source, 'adoption_status': 'pending_evidence', '_evidence': 'final'}}

    def run_links(self, work=None):
        return link_aliases(self.inv, [self.source] if work is None else work, {'t': 'criterion'}, self.decision)

    def test_empty_and_placeholder_metadata_not_equal_author(self):
        for a, b, status in [(None, None, 'metadata_missing'), ('', '', 'metadata_missing'), ('unknown', 'unknown', 'metadata_placeholder'), ('null', 'null', 'metadata_placeholder'), ('0', '0', 'metadata_placeholder')]:
            self.assertEqual(stored_user_comparison(a, b), status)
        self.assertEqual(stored_user_comparison('account1', 'account1'), 'metadata_equal')
        self.assertEqual(stored_user_comparison('account1', 'account2'), 'metadata_different')

    def test_hold_or_evidence_source_never_grants_alias_credit(self):
        result = self.run_links()[0]
        self.assertEqual(result['source']['final_status'], 'pending_evidence')
        self.assertTrue(result['source']['formal_body_review_complete'])
        self.assertFalse(result['body_review_complete'])
        self.assertFalse(result['attribution_verified'])
        self.assertEqual(result['automatic_inherited_credit'], 0)

    def test_final_status_must_not_be_inferred_from_route(self):
        self.source['state'] = 'retain_candidate'
        self.assertEqual(self.run_links()[0]['source']['final_status'], 'pending_evidence')

    def test_missing_final_decision_stops(self):
        self.decision.clear()
        with self.assertRaisesRegex(ValueError, 'lacks exact decision'):
            self.run_links()

    def test_changed_body_in_decision_stops(self):
        self.decision[('t', 'source')]['body_sha256'] = 'different'
        with self.assertRaisesRegex(ValueError, 'lacks exact decision'):
            self.run_links()

    def test_changed_criteria_stops(self):
        self.source['criteria_sha256'] = 'old'
        with self.assertRaisesRegex(ValueError, 'criterion mismatch'):
            self.run_links()

    def test_cross_theme_body_match_is_not_source(self):
        self.source['topic'] = 'other'
        with self.assertRaisesRegex(ValueError, 'exactly one source'):
            self.run_links()

    def test_multiple_source_ids_are_not_arbitrarily_chosen(self):
        second = {**self.source, 'record_id_hash': 'source2'}
        with self.assertRaisesRegex(ValueError, 'exactly one source'):
            self.run_links([self.source, second])

    def test_same_id_is_not_alias(self):
        self.source['record_id_hash'] = self.alias['record_id_hash']
        with self.assertRaisesRegex(ValueError, 'same ID'):
            self.run_links()

    def test_duplicate_alias_id_stops(self):
        self.inv['excluded_unconfirmed'].append(copy.deepcopy(self.alias))
        with self.assertRaisesRegex(ValueError, 'duplicate alias'):
            self.run_links()

    def test_pending_audit_cannot_be_completed_source(self):
        self.decision[('t', 'source')]['adoption_status'] = 'pending_audit'
        with self.assertRaisesRegex(ValueError, 'not resolved'):
            self.run_links()

    def test_multiple_aliases_share_representative_without_credit(self):
        self.alias['exclusion_reasons'] = [REMAINING]
        self.inv['excluded_unconfirmed'].append({**self.alias, 'record_id_hash': 'alias2'})
        self.inv['eligible_inventory_only'] = [self.source]
        self.decision.clear()
        rows = self.run_links([])
        self.assertEqual(len(rows), 2)
        self.assertEqual(len({r['input_group_key'] for r in rows}), 1)
        self.assertTrue(all(r['depends_on_source_completion'] for r in rows))
        self.assertTrue(all(not r['body_review_complete'] for r in rows))

    def test_legacy_attempt_not_promoted(self):
        self.source['state'] = 'attempted'
        self.decision.clear()
        r = self.run_links()[0]
        self.assertTrue(r['depends_on_source_completion'])
        self.assertTrue(r['source']['legacy_unfinished_dependency'])
        self.assertFalse(r['source']['formal_body_review_complete'])


if __name__ == '__main__':
    unittest.main()
