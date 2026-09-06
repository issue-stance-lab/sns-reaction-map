import hashlib
import unittest
from scripts.prepare_editorial_review_packet import check_record
from scripts.run_body_review_pilot import fingerprint

class EditorialVersionTests(unittest.TestCase):
    def setUp(self):
        fields = {'is_relevant': True, 'is_opinion': False, 'main_issue': 'other', 'stance': 'neutral'}
        self.current = {'tweet_id': '123', 'text': '保存本文', 'classification': fields}
        self.saved = {'tweet_id': '123', 'body_sha256': hashlib.sha256('保存本文'.encode()).hexdigest(), 'classification_sha256': fingerprint(fields)}
    def test_identical_record_reuses_evidence(self):
        self.assertEqual(check_record(self.saved, self.current), self.current['classification'])
    def test_changed_body_stops_reuse(self):
        self.current['text'] += '変更'
        with self.assertRaisesRegex(ValueError, 'identity/body'):check_record(self.saved, self.current)
    def test_changed_classification_stops_reuse(self):
        self.current['classification']['is_opinion'] = True
        with self.assertRaisesRegex(ValueError, 'classification changed'):check_record(self.saved, self.current)
    def test_same_body_different_id_stops_reuse(self):
        self.current['tweet_id'] = '124'
        with self.assertRaises(ValueError):check_record(self.saved, self.current)

if __name__ == '__main__':unittest.main()
