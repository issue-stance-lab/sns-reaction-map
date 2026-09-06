import copy
import unittest
from scripts.recover_body_review_pilot import recover

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.current = {'is_relevant': True, 'is_opinion': True, 'main_issue': 'a', 'stance': 'neutral'}
        self.criteria = {'issues': ['a', 'b'], 'stances': ['neutral', 'pro']}
        self.value = {'id': 0, 'status': 'candidate', 'fields': ['main_issue', 'stance'],
                      'suggested': {'main_issue': 'a', 'stance': 'pro'}, 'reason': '変更案'}
    def test_mixed_proposal_retains_only_real_difference_without_approval(self):
        before = copy.deepcopy(self.value)
        result = recover(self.value, self.current, self.criteria)
        self.assertEqual(result['changes'], {'stance': 'pro'})
        self.assertEqual(result['unchanged_fields'], ['main_issue'])
        self.assertEqual(result['route'], 'candidate_pending_review')
        self.assertFalse(result['automatic_approval'])
        self.assertFalse(result['counts_as_editorial_reread'])
        self.assertEqual(self.value, before)
    def test_no_op_never_becomes_ok(self):
        self.value['suggested']['stance'] = 'neutral'
        self.assertEqual(recover(self.value, self.current, self.criteria)['route'], 'contradictory_candidate')
    def test_invalid_label_not_salvaged(self):
        self.value['suggested']['stance'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'invalid stance'):
            recover(self.value, self.current, self.criteria)
    def test_uncertain_with_hidden_suggestion_stays_invalid(self):
        self.value['status'] = 'uncertain'; self.value['fields'] = []
        with self.assertRaisesRegex(ValueError, 'invalid suggestions'):
            recover(self.value, self.current, self.criteria)
    def test_string_bool_not_normalized(self):
        self.value['fields'] = ['is_opinion']; self.value['suggested'] = {'is_opinion': 'false'}
        with self.assertRaisesRegex(ValueError, 'invalid boolean'):
            recover(self.value, self.current, self.criteria)
    def test_duplicate_field_not_silently_removed(self):
        self.value['fields'].append('stance')
        with self.assertRaisesRegex(ValueError, 'invalid suggestions'):
            recover(self.value, self.current, self.criteria)
    def test_ok_still_pending(self):
        self.value.update(status='ok', fields=[], suggested={})
        self.assertEqual(recover(self.value, self.current, self.criteria)['route'], 'ok_pending_review')

if __name__ == '__main__':
    unittest.main()
