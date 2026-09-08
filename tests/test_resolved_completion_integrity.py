"""Independent completion regressions using only temporary synthetic evidence.

The final verifier's upstream collectors are stubbed; report equality, ID/version
accounting and protected files remain real. Short-review tests use real packet
validation, actor binding, show/save, gate and collection without such stubs.
"""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import short_resolved_review as short
from scripts import verify_resolved_review_completion as final
from scripts.editorial_work_registry import fingerprint
from scripts.verify_editorial_hundred import dump, read, sha


class CompletionIntegrityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root, self.private, self.shared = [self.base / p for p in ('repo', 'private', 'shared')]
        for base in (self.root, self.private, self.shared):
            base.mkdir()
        self.protected = 'docs/index.html'
        for base in (self.root, self.shared):
            path = base / self.protected
            path.parent.mkdir()
            path.write_text('Synthetic unchanged public page\n')
        dump(self.private / 'body-review-pilot/20260908-finish5134-handoff/protected-before.private.json',
             {self.protected: sha(self.root / self.protected)})
        self.rows = [dict(topic='topic', record_id_hash=str(i), body_sha256=f'body-{i}',
                          classification_sha256='labels', criteria_sha256='criteria',
                          adoption_status='hold', independently_checked=True,
                          scope_route='new_body_review' if i < 4225 else
                          'verify_distinct_id_against_existing_review') for i in range(4352)]
        paused = [dict(topic='koshitsu-tenpakai', record_id_hash=str(i),
                       body_sha256=f'royal-body-{i}', classification_sha256='labels',
                       criteria_sha256='criteria') for i in range(782)]
        self.scope = {'records': copy.deepcopy(self.rows + paused)}
        self.work = {'records': [{**r, 'state': 'hold'} for r in copy.deepcopy(self.rows)]}
        dump(self.root / 'data/verification/editorial-review-scope.json', {})
        self.cycles = [(self.private / f'cycle-{i}', f'reports/cycle-{i}.json') for i in range(4)]
        self.short_run = (self.private / 'short', 'reports/short.json')

    def verify(self):
        reports = {run: {'journal': self.rows[i*1000:(i+1)*1000],
                         'supplements': [], 'independent_records': 1000}
                   for i, (run, _) in enumerate(self.cycles)}
        for run, path in self.cycles:
            dump(self.root / path, reports[run])
        short_report = {'journal': self.rows[4000:], 'independent_records': 352}
        dump(self.root / self.short_run[1], short_report)
        with patch.object(final, 'load_resolution', return_value=self.scope), \
             patch.object(final, 'load_registry', return_value=self.work), \
             patch.object(final, 'collect_cycle', side_effect=lambda root, private, run, supplements: reports[run]), \
             patch.object(final, 'collect_short', return_value=short_report):
            return final.verify(self.root, self.private, self.shared, self.cycles, self.short_run)

    def test_complete_identity_set_preserves_royal_pause_and_separate_credit(self):
        result = self.verify()
        self.assertEqual(result['completed_target_records'], 4352)
        self.assertEqual(result['new_body_reviews'], 4225)
        self.assertEqual(result['distinct_id_verifications'], 127)
        self.assertEqual(result['remaining_public_opinion_records'], 782)
        self.assertEqual(result['remaining_non_royal_records'], 0)
        self.assertEqual(result['protected_files_unchanged'], 1)

    def test_missing_parent_protected_file_cannot_be_counted_unchanged(self):
        self.verify()  # Prove fixture is complete before deleting one file.
        (self.root / self.protected).unlink()
        with self.assertRaisesRegex(ValueError, 'worktree protected file changed'):
            self.verify()

    def test_missing_shared_protected_file_stops(self):
        (self.shared / self.protected).unlink()
        with self.assertRaisesRegex(ValueError, 'shared protected file changed'):
            self.verify()

    def test_changed_protected_bytes_stop_in_both_trees(self):
        for base, message in ((self.root, 'worktree'), (self.shared, 'shared')):
            path = base / self.protected
            original = path.read_bytes()
            with self.subTest(tree=message):
                path.write_bytes(original + b'changed')
                try:
                    with self.assertRaisesRegex(ValueError, message + ' protected file changed'):
                        self.verify()
                finally:
                    path.write_bytes(original)

    def test_duplicate_id_cannot_replace_an_unreviewed_target(self):
        self.rows[1] = copy.deepcopy(self.rows[0])
        with self.assertRaisesRegex(ValueError, 'completed ID set differs'):
            self.verify()

    def test_body_classification_and_registered_criteria_versions_stop(self):
        for field in ('body_sha256', 'classification_sha256', 'criteria_sha256'):
            row = self.work['records'][0]
            original = row[field]
            with self.subTest(field=field):
                row[field] = 'changed'
                try:
                    with self.assertRaisesRegex(ValueError, 'version changed'):
                        self.verify()
                finally:
                    row[field] = original

    def test_attempt_only_registration_is_not_completion(self):
        self.work['records'][0]['state'] = 'attempted'
        with self.assertRaisesRegex(ValueError, 'lacks formal work registration'):
            self.verify()

    def test_pending_audit_is_not_completion(self):
        self.rows[0]['adoption_status'] = 'pending_audit'
        with self.assertRaisesRegex(ValueError, 'unfinished adoption decision'):
            self.verify()

    def test_every_distinct_id_requires_independent_completion(self):
        self.rows[-1]['independently_checked'] = False
        with self.assertRaisesRegex(ValueError, 'lacks independent completion'):
            self.verify()


class ShortSaveIntegrityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root, self.run = self.base / 'repo', self.base / 'run'
        scripts = self.root / 'scripts'
        scripts.mkdir(parents=True)
        writer = scripts / 'short_resolved_review.py'
        writer.write_bytes(Path(short.__file__).read_bytes())
        criteria_source = scripts / 'synthetic_criteria.py'
        criteria_source.write_text('# Synthetic criteria only\n')
        self.worktrees = {a: str(self.base / a) for a in ('editor_a', 'auditor')}
        for path in self.worktrees.values():
            Path(path).mkdir()
        label = dict(is_relevant=True, is_opinion=True, main_issue='issue', stance='neutral')
        body = 'Synthetic opinion with explicit policy position.'
        records = [dict(topic='topic', record_id_hash='synthetic-id', text=body,
                        body_sha256=hashlib.sha256(body.encode()).hexdigest(),
                        classification=label, classification_sha256=fingerprint(label),
                        scope_route='new_body_review')]
        packet = {'records': records, 'input_sha256': fingerprint(records), 'criteria': {
            'topic': {'source': 'scripts/synthetic_criteria.py', 'source_sha256': sha(criteria_source),
                      'issues': ['issue'], 'stances': ['neutral', 'support']}}}
        self.batch = self.run / 'batch-01'
        dump(self.batch / 'packet.private.json', packet)
        dump(self.run / 'reservation.json', {
            'batch_count': 1, 'new_records': 1,
            'packet_hashes': {'batch-01/packet.private.json': sha(self.batch / 'packet.private.json')},
            'worktrees': self.worktrees,
            'assignments': {'editor': {'editor_a': [1]}, 'audit': {'auditor': [1]}},
            'writer_sha256': sha(writer),
            'decision_code_sha256': {'scripts/short_resolved_review.py': sha(writer)}})
        for role, actor, start, finish in (('editor', 'editor_a', 10, 20), ('audit', 'auditor', 30, 40)):
            with patch.object(Path, 'cwd', return_value=Path(self.worktrees[actor])):
                with patch.object(short.time, 'time', return_value=start):
                    short.show(self.run, 1, role, actor)
                with patch.object(short.time, 'time', return_value=finish):
                    short.save(self.run, 1, role, actor, [
                        [0, True, True, 'issue', 'neutral', False, True,
                         f'Synthetic {role}: explicit opinion supports this test position.']])
        with patch.object(Path, 'cwd', return_value=Path(self.worktrees['auditor'])):
            short.gate(self.run, 1, 'auditor', [], 'Synthetic independent gate')
        self.assertEqual(short.collect(self.root, self.run)['independent_records'], 1)

    def test_saved_writers_are_required_for_each_role(self):
        for role in ('editor', 'audit'):
            path = self.batch / f'{role}.private.json'
            original = read(path)
            for invalid in (None, 'unrecognized.manual.writer'):
                changed = copy.deepcopy(original)
                if invalid is None:
                    del changed['identity_writer']
                else:
                    changed['identity_writer'] = invalid
                with self.subTest(role=role, writer=invalid):
                    dump(path, changed)
                    try:
                        with self.assertRaisesRegex(ValueError, 'unrecognized decision writer'):
                            short.collect(self.root, self.run)
                    finally:
                        dump(path, original)

    def set_audit_start(self, epoch):
        # Both markers agree and each role's local time order remains valid.
        for name in ('audit-start.private.json', 'audit.private.json'):
            path = self.batch / name
            value = read(path)
            value['started_epoch'] = epoch
            dump(path, value)

    def test_audit_start_before_editor_finish_is_rejected(self):
        self.set_audit_start(15)
        with self.assertRaisesRegex(ValueError, 'audit began before editor completion'):
            short.collect(self.root, self.run)

    def test_audit_start_equal_to_editor_finish_is_allowed(self):
        self.set_audit_start(20)
        self.assertEqual(short.collect(self.root, self.run)['new_records'], 1)

    def test_missing_gate_cannot_be_counted_complete(self):
        (self.batch / 'quality_gate.private.json').unlink()
        with self.assertRaises(FileNotFoundError):
            short.collect(self.root, self.run)


if __name__ == '__main__':
    unittest.main()
