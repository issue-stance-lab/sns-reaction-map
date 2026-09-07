import copy
import unittest
from unittest.mock import patch

from scripts.reassess_editorial_criteria import (
    EVENT, apply_history, digest, restore_baseline, verify_reassessment,
)


class ReassessmentHistoryTest(unittest.TestCase):
    def setUp(self):
        self.before = {'schema_version': 1, 'counts': {'pending_evidence': 59, 'hold': 1},
                       'records': [dict(topic='topic', record_id_hash=str(i),
                                        adoption_status='pending_evidence', adoption_basis='criteria_issue',
                                        route='retain_candidate', canonical_applied=False)
                                   for i in range(59)] +
                                  [dict(topic='other', record_id_hash='untouched',
                                        adoption_status='hold', adoption_basis='uncertain')],
                       'canonical_applied': 0}
        self.history = {'event': EVENT, 'baseline_sha256': digest(self.before),
                        'before_key_order': list(self.before),
                        'before_metadata': {k: copy.deepcopy(v) for k, v in self.before.items() if k != 'records'},
                        'records': [{'before': copy.deepcopy(r)} for r in self.before['records'][:59]]}

    def test_history_restores_exact_original_without_mutating_it(self):
        snapshot = copy.deepcopy(self.before)
        after = apply_history(self.before, self.history)
        self.assertEqual(self.before, snapshot)
        self.assertEqual(after['counts'], {'accepted': 59, 'hold': 1})
        self.assertEqual(after['records'][-1], self.before['records'][-1])
        self.assertEqual(restore_baseline(after, self.history), snapshot)
        self.assertTrue(all(not r['canonical_applied'] for r in after['records'][:59]))

    def test_duplicate_or_missing_history_rejected(self):
        for changes in (self.history['records'][:-1], self.history['records'][:-1] + [self.history['records'][0]]):
            history = {**self.history, 'records': changes}
            with self.assertRaises(ValueError):
                apply_history(self.before, history)

    def test_unrelated_row_change_is_detected(self):
        after = apply_history(self.before, self.history)
        after['records'][-1]['adoption_status'] = 'accepted'
        with self.assertRaises(ValueError):
            restore_baseline(after, self.history)

    def test_after_values_and_metadata_cannot_be_modified(self):
        for alter in (lambda d: d['records'][0].update(route='change_candidate'),
                      lambda d: d.update(canonical_applied=59),
                      lambda d: d.update(counts={'accepted': 60}),
                      lambda d: d['reassessment'].update(history_sha256='bad')):
            after = apply_history(self.before, self.history)
            alter(after)
            with self.assertRaises(ValueError):
                restore_baseline(after, self.history)

    def test_hold_cannot_be_promoted_by_history(self):
        before = copy.deepcopy(self.before)
        before['records'][0]['adoption_status'] = 'hold'
        history = copy.deepcopy(self.history)
        history['records'][0]['before'] = before['records'][0]
        with self.assertRaises(ValueError):
            apply_history(before, history)

    def test_double_application_is_rejected(self):
        after = apply_history(self.before, self.history)
        with self.assertRaises(ValueError):
            apply_history(after, self.history)

    def test_evidence_replay_mismatch_is_rejected(self):
        after = apply_history(self.before, self.history)
        with patch('scripts.reassess_editorial_criteria.read', side_effect=[after, self.history]), \
             patch('scripts.reassess_editorial_criteria.load_baseline', return_value=self.before), \
             patch('scripts.reassess_editorial_criteria.assess', return_value={'different': True}):
            with self.assertRaises(ValueError):
                verify_reassessment('.', '.')
