"""Independent synthetic evidence tests; never read actual edited posts."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

from scripts import verify_extra_held_audits as held
from scripts.editorial_work_registry import fingerprint
from scripts.verify_editorial_hundred import dump, read, sha


class ExtraHeldAuditIntegrityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.run = Path(temp.name).resolve() / 'run'
        self.source = self.run / 'wave-01/batch-01'
        self.folder = self.run / 'extra-held-audit-01'
        self.label = dict(is_relevant=True, is_opinion=True, main_issue='issue', stance='neutral')
        text = 'Synthetic statement only.'
        self.raw = dict(topic='topic', record_id_hash='synthetic-post', text=text,
                        body_sha256=hashlib.sha256(text.encode()).hexdigest(),
                        classification_sha256=fingerprint(self.label), classification=self.label)
        packet = {'records': [self.raw], 'criteria': {
            'topic': {'issues': ['issue'], 'stances': ['neutral', 'support']}}}
        dump(self.source / 'packet.private.json', packet)
        dump(self.source / 'editor.private.json', {'finished_epoch': 20})
        dump(self.source / 'editor-actor.private.json', {
            'actor': 'editor_a', 'worktree': str(self.run.parent / 'editor')})
        dump(self.folder / 'packet.private.json', packet)
        self.start = {
            'source_batch': 1, 'source_index': 0, 'actor': 'other_auditor',
            'worktree': str(self.run.parent / 'independent'),
            'source_editor_sha256': sha(self.source / 'editor.private.json'),
            'source_packet_sha256': sha(self.source / 'packet.private.json'),
            'packet_sha256': sha(self.folder / 'packet.private.json'),
            'started_epoch': 30, 'new_body_review_credit': 0}
        decision = {**{k: self.raw[k] for k in ('record_id_hash', 'body_sha256', 'classification_sha256')},
                    'index': 0, 'classification': self.label, 'uncertain': False,
                    'evidence_sufficient': True, 'reason': 'Synthetic independent assessment of the stated position.'}
        self.audit = {**self.start, 'identity_writer': 'manual_held_audit.v1',
                      'finished_epoch': 50, 'reviews': [decision]}
        dump(self.folder / 'audit-draft.private.json', {'recorded_epoch': 40, 'values': [
            [0, True, True, 'issue', 'neutral', False, True, decision['reason']]]})
        self.gate = dict(source_status='hold', result_status='hold',
                         compared_after_independent_save=True, recorded_epoch=60)
        self.flush()
        self.result = {'journal': [{**{k: self.raw[k] for k in ('topic', 'record_id_hash', 'body_sha256', 'classification_sha256')},
                                   'batch': 1, 'index': 0, 'adoption_status': 'hold',
                                   'independently_checked': False, 'canonical_applied': False,
                                   'counts_as_registered_editorial_reread': False}],
                       'supplemental_audits': 7, 'new_records': 1000,
                       'independent_records': 600, 'adoption_counts': {'hold': 1}}

    def flush(self):
        dump(self.folder / 'audit-start.private.json', self.start)
        dump(self.folder / 'audit.private.json', self.audit)
        dump(self.folder / 'quality_gate.private.json', {
            **self.gate, 'audit_sha256': sha(self.folder / 'audit.private.json')})

    def test_independent_audit_adds_only_supplemental_count_and_keeps_hold(self):
        original = copy.deepcopy(self.result)
        output = held.overlay(self.run, self.result)
        self.assertEqual(self.result, original)
        self.assertEqual(output['supplemental_audits'], 8)
        self.assertEqual(output['new_records'], 1000)
        self.assertEqual(output['independent_records'], 600)
        self.assertEqual(output['adoption_counts'], {'hold': 1})
        self.assertTrue(output['journal'][0]['independently_checked'])
        self.assertEqual(output['journal'][0]['adoption_status'], 'hold')
        self.assertFalse(output['journal'][0]['canonical_applied'])
        self.assertFalse(output['journal'][0]['counts_as_registered_editorial_reread'])

    def test_earlier_cycles_without_extra_folder_return_identical_result(self):
        for name in ('cycle01', 'cycle02'):
            with self.subTest(cycle=name):
                self.assertIs(held.overlay(self.run.parent / name, self.result), self.result)

    def test_changed_source_hashes_stop(self):
        for name in ('editor.private.json', 'packet.private.json'):
            path = self.source / name
            original = path.read_bytes()
            with self.subTest(source=name):
                path.write_bytes(original + b' ')
                try:
                    with self.assertRaisesRegex(ValueError, 'source changed'):
                        held.overlay(self.run, self.result)
                finally:
                    path.write_bytes(original)

    def test_same_actor_or_same_resolved_worktree_stops(self):
        original_start, original_audit = copy.deepcopy(self.start), copy.deepcopy(self.audit)
        for field, value in (('actor', 'editor_a'), ('worktree', str(self.run.parent / 'editor') + '/.')):
            with self.subTest(field=field):
                self.start[field] = self.audit[field] = value
                self.flush()
                with self.assertRaisesRegex(ValueError, 'self audit'):
                    held.overlay(self.run, self.result)
                self.start, self.audit = copy.deepcopy(original_start), copy.deepcopy(original_audit)

    def test_cross_actor_and_comparison_time_order_are_required(self):
        for field, value in (('started_epoch', 19), ('finished_epoch', 39), ('gate_epoch', 49)):
            with self.subTest(field=field):
                old = copy.deepcopy((self.start, self.audit, self.gate))
                if field == 'started_epoch':
                    self.start[field] = self.audit[field] = value
                elif field == 'gate_epoch':
                    self.gate['recorded_epoch'] = value
                else:
                    self.audit[field] = value
                self.flush()
                with self.assertRaisesRegex(ValueError, 'timing differs'):
                    held.overlay(self.run, self.result)
                self.start, self.audit, self.gate = old

    def test_draft_mismatch_stops(self):
        path = self.folder / 'audit-draft.private.json'
        value = read(path)
        value['values'][0][-1] = 'A different independently saved reason.'
        dump(path, value)
        with self.assertRaisesRegex(ValueError, 'draft differs'):
            held.overlay(self.run, self.result)

    def test_gate_cannot_release_hold_or_skip_post_save_comparison(self):
        for field, value in (('result_status', 'accepted'), ('source_status', 'accepted'),
                             ('compared_after_independent_save', False)):
            with self.subTest(field=field):
                original = copy.deepcopy(self.gate)
                self.gate[field] = value
                self.flush()
                with self.assertRaisesRegex(ValueError, 'cannot release a hold'):
                    held.overlay(self.run, self.result)
                self.gate = original

    def test_already_audited_or_nonheld_rows_cannot_gain_duplicate_audit(self):
        for field, value in (('independently_checked', True), ('adoption_status', 'accepted')):
            with self.subTest(field=field):
                result = copy.deepcopy(self.result)
                result['journal'][0][field] = value
                with self.assertRaisesRegex(ValueError, 'unaudited held row'):
                    held.overlay(self.run, result)

    def test_second_folder_for_same_target_cannot_double_count(self):
        import shutil
        shutil.copytree(self.folder, self.run / 'extra-held-audit-02')
        with self.assertRaisesRegex(ValueError, 'duplicate held audit'):
            held.overlay(self.run, self.result)

    def test_nonzero_new_body_credit_and_unrecognized_writer_stop(self):
        self.start['new_body_review_credit'] = self.audit['new_body_review_credit'] = 1
        self.flush()
        with self.assertRaisesRegex(ValueError, 'identity or credit differs'):
            held.overlay(self.run, self.result)
        self.start['new_body_review_credit'] = self.audit['new_body_review_credit'] = 0
        self.audit['identity_writer'] = 'other_writer'
        self.flush()
        with self.assertRaisesRegex(ValueError, 'identity or credit differs'):
            held.overlay(self.run, self.result)


if __name__ == '__main__':
    unittest.main()
