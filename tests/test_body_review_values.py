import unittest
from scripts.trial_body_review_values import validate, schema

class ValueTrialTests(unittest.TestCase):
    def setUp(self):
        self.current = {'is_relevant': True, 'is_opinion': True, 'main_issue': 'a', 'stance': 'neutral'}
        self.criteria = {'issues': ['a', 'b'], 'stances': ['neutral', 'pro']}
        self.value = {'classification': dict(self.current), 'uncertain': False, 'reason': '本文から判断'}
    def test_no_change_calculated_without_candidate_status(self):
        result = validate(self.value, self.current, self.criteria)
        self.assertEqual(result['route'], 'no_change')
        self.assertEqual(result['changes'], {})
        self.assertFalse(result['counts_as_editorial_reread'])
    def test_only_changed_field_extracted(self):
        self.value['classification']['stance'] = 'pro'
        self.assertEqual(validate(self.value, self.current, self.criteria)['changes'], {'stance': 'pro'})
    def test_uncertain_change_never_becomes_clear_candidate(self):
        self.value['classification']['stance'] = 'pro'; self.value['uncertain'] = True
        self.assertEqual(validate(self.value, self.current, self.criteria)['route'], 'uncertain')
    def test_incomplete_values_rejected(self):
        del self.value['classification']['is_opinion']
        with self.assertRaises(ValueError):validate(self.value, self.current, self.criteria)
    def test_string_boolean_rejected(self):
        self.value['classification']['is_opinion'] = 'false'
        with self.assertRaises(ValueError):validate(self.value, self.current, self.criteria)
    def test_unknown_label_rejected(self):
        self.value['classification']['main_issue'] = 'unknown'
        with self.assertRaises(ValueError):validate(self.value, self.current, self.criteria)
    def test_all_fields_required_by_schema(self):
        self.assertEqual(set(schema(self.criteria)['properties']['classification']['required']), set(self.current))

if __name__ == '__main__':unittest.main()
