import hashlib
import tempfile
import unittest
from pathlib import Path
from scripts.continuous_editorial_review import show, save, gate, comparison
from scripts.verify_editorial_hundred import read, sha, dump
from scripts.editorial_work_registry import fingerprint


class ContinuousReviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.run = Path(self.tmp.name); self.d = self.run / 'batch-01'
        current = {'is_relevant': True, 'is_opinion': True, 'main_issue': 'issue', 'stance': 'yes'}
        self.packet = {'records': [{'topic': 'topic', 'record_id_hash': str(i), 'text': str(i),
                                   'body_sha256': hashlib.sha256(str(i).encode()).hexdigest(),
                                   'classification_sha256': fingerprint(current), 'classification': current}
                                  for i in range(20)],
                       'criteria': {'topic': {'issues': ['issue'], 'stances': ['yes', 'no']}}}
        dump(self.d / 'packet.private.json', self.packet)
        dump(self.run / 'reservation.json', {'packet_hashes': {'batch-01/packet.private.json': sha(self.d / 'packet.private.json')}})
        self.values = [[i, True, True, 'issue', 'yes', False, True, 'explicit evaluation'] for i in range(20)]

    def test_identity_and_actual_clock_are_supplied_by_program(self):
        show(self.run, 1, 'editor')
        started = read(self.d / 'editor-start.private.json')
        show(self.run, 1, 'editor')
        self.assertEqual(read(self.d / 'editor-start.private.json'), started)
        save(self.run, 1, 'editor', self.values)
        result = read(self.d / 'editor.private.json')
        self.assertGreaterEqual(result['finished_epoch'], result['started_epoch'])
        for row, raw in zip(result['reviews'], self.packet['records']):
            for k in ['record_id_hash', 'body_sha256', 'classification_sha256']:
                self.assertEqual(row[k], raw[k])
        with self.assertRaises(ValueError): save(self.run, 1, 'editor', self.values)

    def test_invalid_attempt_is_retained_not_silently_repaired(self):
        show(self.run, 1, 'editor'); self.values[0][3] = 'invalid issue'
        with self.assertRaises(ValueError): save(self.run, 1, 'editor', self.values)
        self.assertTrue((self.d / 'editor-draft.private.json').exists())
        self.assertFalse((self.d / 'editor.private.json').exists())
        self.values[0][3] = 'issue'
        with self.assertRaises(ValueError): save(self.run, 1, 'editor', self.values)

    def test_audit_sees_current_input_not_editor_proposal(self):
        show(self.run, 1, 'editor'); self.values[7][4] = 'no'
        save(self.run, 1, 'editor', self.values)
        view = show(self.run, 1, 'audit')
        self.assertEqual([r['index'] for r in view['records']], [0, 1, 7])
        self.assertEqual(view['records'][-1]['current']['stance'], 'yes')
        self.assertTrue(all(set(r) == {'index', 'topic', 'text', 'current'} for r in view['records']))
        with self.assertRaises(FileNotFoundError): comparison(self.run, 1)

    def test_gate_keeps_independent_disagreement(self):
        show(self.run, 1, 'editor'); save(self.run, 1, 'editor', self.values)
        show(self.run, 1, 'audit'); audit = [self.values[0][:], self.values[1][:]]; audit[0][4] = 'no'
        save(self.run, 1, 'audit', audit)
        gate(self.run, 1, reason_conflicts=[], systemic_criteria_issue=False, notes='disagreement')
        result = comparison(self.run, 1)
        self.assertNotEqual(result['rows'][0]['editor']['classification'], result['rows'][0]['audit']['classification'])
        with self.assertRaises(ValueError): gate(self.run, 1, reason_conflicts=[], systemic_criteria_issue=False, notes='')

    def test_modified_packet_stops_before_reading(self):
        self.packet['records'][0]['text'] = 'modified'
        dump(self.d / 'packet.private.json', self.packet)
        with self.assertRaises(ValueError): show(self.run, 1, 'editor')
        self.assertFalse((self.d / 'editor-start.private.json').exists())
