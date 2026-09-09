"""Independent regression coverage for reservation and evidence review findings.

All posts and judgments are synthetic; this suite never reads live review evidence.
"""
from contextlib import ExitStack
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import prepare_resolved_review_cycle as ordinary
from scripts import prepare_short_resolved_cycle as short_prepare
from scripts import short_resolved_review as short
from scripts.editorial_work_registry import fingerprint
from scripts.verify_editorial_hundred import dump, read, sha


DEPENDENCIES = (
    'short_resolved_review.py', 'summarize_editorial_batch.py',
    'editorial_acceptance.py', 'trial_body_review_values.py',
    'editorial_work_registry.py',
)


class ResolvedReviewAuditRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'repo'
        self.private = self.base / 'private'
        self.root.mkdir()
        self.private.mkdir()
        self.worktrees = {}
        for actor in ('editor_a', 'editor_b', 'auditor'):
            path = self.base / actor
            path.mkdir()
            self.worktrees[actor] = str(path)

    def test_comparison_matches_identity_after_reversed_save_order(self):
        run = self.private / 'comparison'
        packet_path = run / 'batch-01/packet.private.json'
        label = dict(is_relevant=True, is_opinion=True,
                     main_issue='issue', stance='neutral')
        records = [dict(topic='topic', record_id_hash=f'post-{i}',
                        text=f'Synthetic opinion {i}',
                        body_sha256=f'body-{i}', classification_sha256='labels',
                        classification=copy.deepcopy(label)) for i in range(3)]
        dump(packet_path, {'records': records, 'criteria': {
            'topic': {'issues': ['issue'], 'stances': ['neutral', 'support']}}})
        dump(run / 'reservation.json', {
            'batch_count': 1, 'packet_hashes': {
                'batch-01/packet.private.json': sha(packet_path)},
            'worktrees': self.worktrees,
            'assignments': {'editor': {'editor_a': [1]}, 'audit': {'auditor': [1]}}})
        for role, actor, order in (
                ('editor', 'editor_a', [1, 2, 0]),
                ('audit', 'auditor', [2, 0, 1])):
            with patch.object(Path, 'cwd', return_value=Path(self.worktrees[actor])):
                short.show(run, 1, role, actor)
                values = [[i, True, True, 'issue', 'neutral', False, True,
                           f'Synthetic {role} judgment for post {i}'] for i in order]
                self.assertEqual(short.save(run, 1, role, actor, values), 3)
            self.assertEqual([r['index'] for r in read(
                run / f'batch-01/{role}.private.json')['reviews']], order)
        with patch.object(Path, 'cwd', return_value=Path(self.worktrees['auditor'])):
            rows = short.comparison(run, 1, 'auditor')['rows']
        self.assertEqual([r['index'] for r in rows], [0, 1, 2])
        for row in rows:
            i = row['index']
            for role in ('editor', 'audit'):
                self.assertEqual(row[role]['index'], i)
                self.assertEqual(row[role]['record_id_hash'], f'post-{i}')
                self.assertEqual(row[role]['reason'],
                                 f'Synthetic {role} judgment for post {i}')

    def test_both_preparers_reject_same_worktree_with_dot_or_symlink(self):
        alias = self.base / 'editor-alias'
        alias.symlink_to(self.worktrees['editor_a'], target_is_directory=True)
        for spelling in (self.worktrees['editor_a'] + '/.', str(alias)):
            worktrees = {**self.worktrees, 'auditor': spelling}
            for module in (ordinary, short_prepare):
                with self.subTest(module=module.__name__, spelling=spelling):
                    run = self.private / 'must-not-reserve'
                    with self.assertRaisesRegex(ValueError, 'separate'):
                        if module is ordinary:
                            module.prepare(self.root, self.private, run,
                                           {'topic': 1000}, worktrees)
                        else:
                            module.prepare(self.root, self.private, run, worktrees, [])
                    self.assertFalse(run.exists())

    def short_fixture(self, source_criteria_matches=True):
        """352 synthetic remaining IDs and four completed 1000-ID reservations."""
        criteria = {'topic': {'issues': ['issue'], 'stances': ['neutral']}}
        criteria_hash = fingerprint(criteria['topic'])
        completed = [dict(topic='topic', record_id_hash=f'old-{i}', state='reviewed',
                          body_sha256=f'body-{i}', classification_sha256='labels',
                          criteria_sha256=criteria_hash) for i in range(4000)]
        if not source_criteria_matches:
            completed[0]['criteria_sha256'] = 'obsolete-criteria'
        dependency = {k: completed[0][k] for k in (
            'topic', 'record_id_hash', 'body_sha256', 'classification_sha256')}
        remaining = [dict(topic='topic', record_id_hash=f'new-{i}',
                          body_sha256='body-0' if i >= 225 else f'new-body-{i}',
                          classification_sha256='labels', criteria_sha256=criteria_hash,
                          route='new_body_review' if i < 225 else
                          'verify_distinct_id_against_existing_review',
                          input_job_key=f'new-job-{i}', prior_attempt_preserved=False,
                          dependency=None if i < 225 else dependency)
                     for i in range(352)]
        inventory = self.private / 'body-review-inventory/20260908-finish5134/inventory.private.json'
        dump(inventory, {'raw_remaining': remaining})
        dump(self.root / 'data/verification/editorial-review-scope.json',
             {'resolution_sha256': 'synthetic-resolution'})
        dump(self.root / 'data/verification/editorial-work.json', {'records': completed})
        dump(self.root / 'data/verification/editorial-adoption-current.json', {'records': []})
        (self.root / 'THEMES.yaml').write_text(
            'themes:\n  topic:\n    published: done\n    sample_file: sample.json\n')
        dump(self.root / 'sample.json', [])
        for name in ('CYCLE_2000_RUNBOOK.md', 'POLICY_STANCE_MAPPING_V3.md'):
            path = self.root / 'quality/designs/body-review' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Synthetic frozen policy\n')
        for name in DEPENDENCIES:
            path = self.root / 'scripts' / name
            path.parent.mkdir(exist_ok=True)
            path.write_text(f'# Synthetic decision dependency: {name}\n')
        prior_runs = []
        for n in range(4):
            previous = self.private / f'prior-{n}'
            packet_hashes = {}
            for batch in range(50):
                relative = f'batch-{batch+1:02d}/packet.private.json'
                packet_path = previous / 'wave-01' / relative
                start = n*1000 + batch*20
                dump(packet_path, {'records': completed[start:start+20]})
                packet_hashes[relative] = sha(packet_path)
            reservation = previous / 'wave-01/reservation.json'
            dump(reservation, {'packet_hashes': packet_hashes})
            dump(previous / 'reservation.json', {'waves': {'wave-01': sha(reservation)}})
            prior_runs.append(previous)
        scope = {'records': remaining, 'provenance': {
            'inventory_sha256': sha(inventory),
            'canonical_sha256': {'topic': sha(self.root / 'sample.json')}}}
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(short_prepare, 'load_resolution', return_value=scope))
        stack.enter_context(patch.object(short_prepare, 'load_registry',
                                         return_value={'records': completed}))
        stack.enter_context(patch.object(short_prepare, 'build_criteria', return_value=criteria))
        # Canonical packet validation has separate coverage. Only upstream loading
        # is stubbed here; reservation version checks, hashes and writes stay real.
        stack.enter_context(patch.object(short_prepare, 'checked_packet'))
        return prior_runs

    def test_short_reservation_freezes_and_rejects_each_changed_dependency(self):
        priors = self.short_fixture()
        run = self.private / 'short-cycle'
        reservation = short_prepare.prepare(self.root, self.private, run,
                                             self.worktrees, priors)
        self.assertEqual(set(reservation['decision_code_sha256']),
                         {'scripts/' + name for name in DEPENDENCIES})
        # An intact dependency set reaches packet collection; changed code must
        # fail before any review evidence is consumed or credited.
        with patch.object(short, 'packet', side_effect=RuntimeError('packet boundary')):
            with self.assertRaisesRegex(RuntimeError, 'packet boundary'):
                short.collect(self.root, run)
            for name in DEPENDENCIES:
                path = self.root / 'scripts' / name
                original = path.read_bytes()
                with self.subTest(dependency=name):
                    path.write_bytes(original + b'# changed decision code\n')
                    try:
                        expected = 'writer changed' if name == 'short_resolved_review.py' else 'decision dependency changed'
                        with self.assertRaisesRegex(ValueError, expected):
                            short.collect(self.root, run)
                    finally:
                        path.write_bytes(original)

    def test_alias_rejects_completed_source_with_different_criteria_version(self):
        priors = self.short_fixture(source_criteria_matches=False)
        run = self.private / 'must-not-reserve-alias'
        with self.assertRaisesRegex(ValueError, 'alias requires distinct completed source with exact version'):
            short_prepare.prepare(self.root, self.private, run, self.worktrees, priors)
        self.assertFalse(run.exists())


if __name__ == '__main__':
    unittest.main()
