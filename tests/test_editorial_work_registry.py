import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.editorial_work_registry import build_registry, load_registry, current_attempts, fingerprint, sha, checked_packet
from scripts.prepare_next_editorial_batch import select_batch


class EditorialWorkRegistryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'criteria.py').write_text('criteria v1')
        self.criteria = {'topic': {'source': 'criteria.py', 'source_sha256': sha(self.root/'criteria.py'), 'text': 'criteria'}}
        self.rows = []
        for i in range(4):
            text = 'test text ' + str(i)
            classification = {'stance': str(i)}
            self.rows.append({'topic': 'topic', 'record_id_hash': 'sha256:' + hashlib.sha256(str(i).encode()).hexdigest(), 'text': text, 'body_sha256': hashlib.sha256(text.encode()).hexdigest(), 'classification': classification, 'classification_sha256': fingerprint(classification), 'sample_id': 'sample' + str(i)})
        self.packet = {'records': self.rows, 'criteria': self.criteria, 'input_sha256': fingerprint(self.rows)}
        journal = [{**r, 'route': route} for r, route in zip(self.rows, ['retain_candidate', 'change_candidate', 'hold'])]
        self.sources = []
        for name, kind, value in [('packet.json', 'packet', self.packet), ('journal.json', 'journal', {'journal': journal}), ('audit.json', 'scope_audit', {'consistent': ['sample3']})]:
            (self.root/name).write_text(json.dumps(value))
            self.sources.append({'storage': 'private', 'path': name, 'sha256': sha(self.root/name), 'kind': kind})

    def build(self):
        return build_registry(self.sources, self.root, self.root)

    def test_counts_candidates_hold_scope_and_no_credit(self):
        ledger = self.build()
        self.assertEqual(ledger['counts'], dict(attempted=1, retain_candidate=1, change_candidate=1, hold=1))
        self.assertTrue(all(not r['canonical_applied'] and not r['counts_as_registered_editorial_reread'] for r in ledger['records']))
        row = next(r for r in ledger['records'] if r['state'] == 'attempted')
        self.assertEqual(len(row['scope_only_audits']), 1)
        self.assertEqual(ledger['automatic_reread_credit'], 0)

    def test_excludes_all_states_and_same_topic_duplicates(self):
        ledger = self.build()
        attempts = current_attempts(ledger, self.criteria)
        duplicate = {**self.rows[0], 'record_id_hash': 'different'}
        self.assertEqual(select_batch({'topic': self.rows + [duplicate]}, attempts), [])
        self.assertEqual(len(select_batch({'other': [duplicate]}, attempts)), 1)
        self.assertEqual(len(select_batch({'topic': [duplicate, duplicate]}, [])), 1)

    def test_body_and_label_change_requeue(self):
        attempts = current_attempts(self.build(), self.criteria)
        for field in ['body_sha256', 'classification_sha256']:
            row = {**self.rows[0], field: 'new-version'}
            self.assertEqual(len(select_batch({'topic': [row]}, attempts)), 1)

    def test_criteria_changes_stop(self):
        ledger = self.build()
        changed = copy.deepcopy(self.criteria)
        changed['topic']['text'] = 'new'
        with self.assertRaises(ValueError): current_attempts(ledger, changed)
        (self.root/'criteria.py').write_text('criteria v2')
        with self.assertRaises(ValueError): self.build()

    def test_missing_and_tampered_evidence_stop(self):
        p = self.root/'audit.json'
        saved = p.read_bytes()
        p.write_text('{}')
        with self.assertRaises(ValueError): self.build()
        p.unlink()
        with self.assertRaises(ValueError): self.build()
        p.write_bytes(saved)
        ledger = self.build()
        ledger['records'][0]['state'] = 'attempted'
        ledger['records'][0]['canonical_applied'] = True
        (self.root/'registry.json').write_text(json.dumps(ledger))
        with self.assertRaises(ValueError): load_registry(self.root/'registry.json', self.root, self.root)

    def test_reservation_packet_checks_content_and_criteria(self):
        self.assertEqual(len(checked_packet(self.packet, self.root)), 4)
        self.packet['records'][0]['classification']['stance'] = 'tampered'
        with self.assertRaises(ValueError): checked_packet(self.packet, self.root)

    def test_committed_summary_and_body_free(self):
        p = Path(__file__).resolve().parents[1]/'data/verification/editorial-work.json'
        ledger = json.loads(p.read_text())
        self.assertEqual(len(ledger['records']), 4080)
        self.assertEqual(sum(ledger['counts'].values()), 4080)
        current = json.loads((p.parent/'editorial-adoption-current.json').read_text())
        self.assertIn(current['reviewed_records'], [2000, 3000, 4000])
        self.assertEqual(ledger['counts']['attempted'], 4080-current['reviewed_records'])
        self.assertEqual(len({(r['topic'], r['record_id_hash']) for r in ledger['records']}), 4080)
        self.assertEqual(sum(bool(r['scope_only_audits']) for r in ledger['records']), 10)
        for row in ledger['records']:
            self.assertFalse({'text', 'tweet_id', 'reason'} & row.keys())
        self.assertTrue(all(not Path(s['path']).is_absolute() for s in ledger['sources']))


if __name__ == '__main__': unittest.main()
