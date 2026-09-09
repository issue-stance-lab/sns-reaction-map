"""Exercise final-verifier integration using synthetic 8080-row baseline only."""
import copy
import unittest

from tests import test_resolved_completion_integrity as fixtures
from scripts.verify_editorial_hundred import dump, sha


class FinalIdentityIntegrationTests(fixtures.CompletionIntegrityTests):
    def setUp(self):
        super().setUp()
        for row in self.scope['records']:
            row['route'] = row.get('scope_route', 'new_body_review')
        self.baseline_path = self.private / 'body-review-pilot/20260908-nonkoshitsu-cycle01/work-before.private.json'
        self.baseline = {'records': [dict(topic='old-topic', record_id_hash=f'old-{i}',
                                        body_sha256=f'old-body-{i}', classification_sha256='old-labels',
                                        criteria_sha256='criteria', state='hold' if i < 8000 else 'attempted')
                                     for i in range(8080)]}
        self.pin_baseline()

    def pin_baseline(self):
        dump(self.baseline_path, self.baseline)
        self.scope['provenance'] = {'work_registry_sha256': sha(self.baseline_path)}

    def test_baseline_hash_pin_rejects_valid_json_with_changed_content(self):
        self.verify()
        dump(self.baseline_path, {'records': []})
        with self.assertRaisesRegex(ValueError, 'initial completed-work baseline changed'):
            self.verify()

    def test_integrated_global_exact_version_overlap_blocks(self):
        self.baseline['records'][0] = {**self.rows[0], 'topic': 'different-topic', 'state': 'hold'}
        self.pin_baseline()
        with self.assertRaisesRegex(ValueError, 'duplicate completed post or input version'):
            self.verify()

    def test_integrated_bare_global_id_reference_does_not_block(self):
        self.baseline['records'][0]['record_id_hash'] = self.rows[0]['record_id_hash']
        self.pin_baseline()
        result = self.verify()['identity_counts']
        self.assertFalse(any(result['blocking'].values()))
        self.assertEqual(result['reference']['global_id_reappears_in_baseline_completed_count'], 1)
        self.assertEqual(result['reference']['baseline_completed_records'], 8000)
        self.assertEqual(result['reference']['baseline_attempted_records'], 80)

    def test_integrated_old_unfinished_version_is_not_formal_duplicate(self):
        self.baseline['records'][-1] = {**self.rows[0], 'state': 'attempted'}
        self.pin_baseline()
        counts = self.verify()['identity_counts']
        self.assertFalse(any(counts['blocking'].values()))
        self.assertEqual(counts['reference']['resumed_attempted_version_rows'], 1)


if __name__ == '__main__':
    unittest.main()
