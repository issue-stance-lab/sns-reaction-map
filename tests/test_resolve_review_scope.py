import copy
import unittest
from scripts.resolve_remaining_review_scope import build_resolution
from scripts.editorial_work_registry import fingerprint


class ScopeResolutionTests(unittest.TestCase):
    def setUp(self):
        self.criteria = {'topic': {'source_sha256': 'criteria'}}
        criteria_sha = fingerprint(self.criteria['topic'])
        def row(number, body=None, reason=None):
            value = {'topic': 'topic', 'record_id_hash': str(number),
                     'body_sha256': str(number if body is None else body),
                     'classification_sha256': 'classification'}
            if reason:
                value['exclusion_reasons'] = [reason]
            return value
        primary = row(1)
        legacy = row(2, reason='unfinished_legacy_pilot')
        invalid = row(3, reason='invalid_run_reserved_id')
        prior_alias = row(4, body=9, reason='same_input_as_existing_work_different_id')
        future_alias = row(5, body=1, reason='same_input_as_another_unconfirmed_id')
        self.inventory = {'raw_remaining': [primary, legacy, invalid, prior_alias, future_alias],
                          'eligible_inventory_only': [primary],
                          'excluded_unconfirmed': [legacy, invalid, prior_alias, future_alias]}
        self.work = {'records': [
            row(2) | {'state': 'attempted', 'work_key': 'old-2', 'criteria_sha256': criteria_sha},
            row(9) | {'state': 'hold', 'work_key': 'old-9', 'criteria_sha256': criteria_sha},
        ]}

    def run_resolution(self):
        return build_resolution(self.inventory, self.work, self.criteria)

    def test_all_routes_preserve_unconfirmed_without_adoption_transfer(self):
        before = copy.deepcopy(self.work)
        result = self.run_resolution()
        self.assertEqual(result['target_topic_post_records'], 5)
        self.assertEqual(result['primary_body_review_inputs'], 3)
        self.assertEqual(result['distinct_id_verification_records'], 2)
        self.assertEqual(len(result['route_counts']), 5)
        self.assertEqual(self.work, before)
        for row in result['records']:
            self.assertEqual(row['state'], 'unconfirmed')
            self.assertEqual(row['reservation_state'], 'not_reserved')
            self.assertEqual(row['body_review_credit'], 0)
            self.assertEqual(row['post_completion_credit'], 0)
            self.assertFalse(row['adoption_transfer_allowed'])
        future = result['records'][-1]
        self.assertEqual(future['dependency']['record_id_hash'], '1')

    def test_duplicate_post_rejected(self):
        self.inventory['raw_remaining'].append(self.inventory['raw_remaining'][0])
        with self.assertRaisesRegex(ValueError, 'duplicate unresolved'):
            self.run_resolution()

    def test_missing_partition_entry_rejected(self):
        self.inventory['excluded_unconfirmed'].pop()
        with self.assertRaisesRegex(ValueError, 'partition differs'):
            self.run_resolution()

    def test_changed_classification_rejected(self):
        self.inventory['excluded_unconfirmed'] = copy.deepcopy(self.inventory['excluded_unconfirmed'])
        self.inventory['excluded_unconfirmed'][0]['classification_sha256'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'classification changed'):
            self.run_resolution()

    def test_unfinished_source_never_reused_as_completed(self):
        self.work['records'][1]['state'] = 'attempted'
        with self.assertRaisesRegex(ValueError, 'completed source'):
            self.run_resolution()

    def test_completed_legacy_cannot_be_reopened(self):
        self.work['records'][0]['state'] = 'hold'
        with self.assertRaisesRegex(ValueError, 'no longer an unfinished'):
            self.run_resolution()

    def test_missing_alias_primary_rejected(self):
        self.inventory['raw_remaining'][-1]['body_sha256'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'primary review missing'):
            self.run_resolution()

    def test_changed_source_criteria_rejected(self):
        self.work['records'][1]['criteria_sha256'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'criteria version differs'):
            self.run_resolution()

    def test_ambiguous_exclusion_not_forced(self):
        self.inventory['excluded_unconfirmed'][0]['exclusion_reasons'].append('invalid_run_reserved_id')
        with self.assertRaisesRegex(ValueError, 'overlapping exclusion'):
            self.run_resolution()


if __name__ == '__main__':
    unittest.main()
