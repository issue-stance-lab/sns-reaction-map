"""Private review lifecycle tests using synthetic bodies and temporary runs."""
from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import royal_body_review as review
from tests.test_royal_review_schema import decision


@contextmanager
def cwd(path):
    before = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(before)


def rewrite(path, data):
    """Deliberate test corruption only; production writer uses exclusive create."""
    path.write_text(json.dumps(data, ensure_ascii=False))


class RoyalBodyReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.run = self.base / 'private/run'
        self.root = Path(review.__file__).resolve().parents[1]
        self.worktrees = {r: self.base / r for r in ('editor_a', 'editor_b', 'audit')}
        for path in self.worktrees.values():
            path.mkdir()
        self.assignments = {r: {'actor': r, 'worktree': str(path)}
                            for r, path in self.worktrees.items()}
        self.versions = {p: review.sha(self.root / p)
                         for p in (review.CRITERIA, review.SCHEMA, review.WRITER)}

    def make_run(self, count=2):
        """Small sealed run fixture; 782-population selection is tested separately."""
        self.run.mkdir(parents=True)
        self.folder = self.run / 'batch-01'
        self.folder.mkdir()
        rows = []
        for i in range(count):
            body = f'Synthetic body {i}: storage testing only.'
            rows.append({'index': i, 'topic': review.TOPIC,
                         'record_id_hash': hashlib.sha256(str(i).encode()).hexdigest(),
                         'body_sha256': hashlib.sha256(body.encode()).hexdigest(),
                         'classification_sha256': 'c' * 64, 'text': body,
                         'scope_route': 'new_body_review', 'dependency': None})
        packet = {'schema_version': review.SCHEMA_VERSION, 'versions': self.versions,
                  'topic': review.TOPIC, 'records': rows}
        review.write_new(self.folder / 'packet.private.json', packet)
        review.write_new(self.folder / 'registry-packet.private.json', {'records': rows})
        review.write_new(self.run / 'work-before.private.json', {'records': [], 'sources': []})
        review.write_new(self.run / 'baseline.private.json', {
            'work_before_sha256': review.sha(self.run / 'work-before.private.json')})
        review.write_new(self.run / 'implementation-review.private.json', {
            'status': 'pass', 'versions': self.versions})
        (self.run / 'criteria.md').write_bytes((self.root / review.CRITERIA).read_bytes())
        reservation = {'schema_version': review.SCHEMA_VERSION,
                       'assignments': self.assignments, 'versions': self.versions,
                       'baseline_sha256': review.sha(self.run / 'baseline.private.json'),
                       'implementation_review_sha256': review.sha(self.run / 'implementation-review.private.json'),
                       'batches': [{'batch': 1, 'count': count, 'editor': 'editor_a',
                                    'packet_sha256': review.sha(self.folder / 'packet.private.json'),
                                    'registry_packet_sha256': review.sha(self.folder / 'registry-packet.private.json')}],
                       'target_count': count, 'legacy_adoption_allowed': False}
        review.write_new(self.run / 'reservation.json', reservation)
        review.write_new(self.run / 'reservation-seal.json', {'sha256': review.sha(self.run / 'reservation.json')})
        return [dict(decision(), index=i) for i in range(count)]

    def reseal(self, packet=None, reservation=None):
        # This simulates malformed trusted input, in addition to ordinary
        # corruption tests which deliberately do not recompute seals.
        if reservation is None:
            reservation = review.read(self.run / 'reservation.json')
        if packet is not None:
            rewrite(self.folder / 'packet.private.json', packet)
            reservation['batches'][0]['packet_sha256'] = review.sha(self.folder / 'packet.private.json')
        rewrite(self.run / 'reservation.json', reservation)
        rewrite(self.run / 'reservation-seal.json', {'sha256': review.sha(self.run / 'reservation.json')})

    def save_role(self, role, values):
        actor = 'editor_a' if role == 'editor' else 'audit'
        with cwd(self.worktrees[actor]):
            review.show(self.run, 1, role, actor)
            review.save(self.run, 1, role, actor, values)

    def checks(self, count):
        return [{'index': i, 'semantic_agreement': True, 'reason_sufficient': True,
                 'criteria_issue': False, 'reason': 'Synthetic individual comparison.'}
                for i in range(count)]

    def finish(self, values):
        self.save_role('audit', values)  # Independent values can precede editor.
        self.save_role('editor', values)
        with cwd(self.worktrees['audit']):
            review.comparison(self.run, 1, 'audit')
            review.save_gate(self.run, 1, 'audit', self.checks(len(values)))

    def test_single_two_and_twenty_finish_without_adoption(self):
        for count in (1, 2, 20):
            with self.subTest(count=count):
                self.run = self.base / f'private/run-{count}'
                values = self.make_run(count)
                self.finish(values)
                actual = review.status(self.run)
                self.assertEqual((actual['editor'], actual['audit'], actual['gated']), (count,) * 3)
                self.assertEqual(actual['remaining_to_gate'], 0)
                self.assertEqual(actual['hold'], count)
                self.assertEqual(actual['adoption_candidates'], 0)
                self.assertTrue(all(r['canonical_applied'] is False for r in review.collect_batch(self.run, 1)))

    def test_zero_or_twenty_one_rows_are_rejected(self):
        for count in (0, 21):
            with self.subTest(count=count):
                self.run = self.base / f'private/run-{count}'
                self.make_run(count)
                with self.assertRaises(ValueError):
                    review.packet_for(self.run, 1)

    def test_wrong_theme_duplicate_identity_and_index_are_rejected(self):
        self.make_run()
        original = review.read(self.folder / 'packet.private.json')
        for mutation in ('theme', 'duplicate', 'index', 'hash'):
            packet = copy.deepcopy(original)
            if mutation == 'theme':
                packet['records'][1]['topic'] = 'ai-copyright'
            elif mutation == 'duplicate':
                packet['records'][1] = dict(packet['records'][0], index=1)
            elif mutation == 'index':
                packet['records'][1]['index'] = 0
            else:
                packet['records'][1]['body_sha256'] = '0' * 64
            self.reseal(packet=packet)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                review.packet_for(self.run, 1)

    def test_packet_envelope_pins_topic_schema_and_versions(self):
        self.make_run()
        original = review.read(self.folder / 'packet.private.json')
        for key, value in (('topic', 'ai-copyright'), ('schema_version', 'old'), ('versions', {})):
            packet = dict(original, **{key: value})
            self.reseal(packet=packet)
            with self.subTest(key=key), self.assertRaises(ValueError):
                review.packet_for(self.run, 1)

    def test_batch_number_requires_reserved_integer(self):
        self.make_run()
        for value in (True, None, 1.0, '1', 0, 2):
            with self.subTest(value=value), self.assertRaises(ValueError):
                review.packet_for(self.run, value)

    def test_wrong_actor_and_worktree_cannot_start(self):
        self.make_run()
        with cwd(self.worktrees['editor_b']), self.assertRaises(ValueError):
            review.show(self.run, 1, 'editor', 'editor_a')
        with cwd(self.worktrees['editor_a']), self.assertRaises(ValueError):
            review.show(self.run, 1, 'editor', 'editor_b')
        self.assertFalse((self.folder / 'editor-start.private.json').exists())

    def test_input_criteria_baseline_and_reservation_corruption_stop(self):
        for name in ('criteria.md', 'baseline.private.json', 'reservation.json',
                     'work-before.private.json', 'implementation-review.private.json',
                     'batch-01/packet.private.json'):
            self.run = self.base / ('private/' + name.replace('/', '-').replace('.', '-'))
            self.make_run()
            path = self.run / name
            path.write_bytes(path.read_bytes() + b' ')
            with self.subTest(name=name), self.assertRaises(ValueError):
                review.packet_for(self.run, 1)

    def test_changed_runtime_version_stops_without_editing_real_code(self):
        self.make_run()
        reservation = review.read(self.run / 'reservation.json')
        reservation['versions'][review.WRITER] = '0' * 64
        self.reseal(reservation=reservation)
        with self.assertRaises(ValueError):
            review.checked_run(self.run)

    def test_final_and_draft_are_immutable(self):
        values = self.make_run()
        self.save_role('editor', values)
        with cwd(self.worktrees['editor_a']), self.assertRaises(ValueError):
            review.save(self.run, 1, 'editor', 'editor_a', values)
        values[0]['reason'] = 'Different synthetic reason.'
        with cwd(self.worktrees['audit']):
            review.show(self.run, 1, 'audit', 'audit')
            review.write_new(self.folder / 'audit-draft.private.json', {
                'records': [dict(v, reason='Earlier synthetic draft.') for v in values], 'recorded_epoch': 0})
            with self.assertRaises(ValueError):
                review.save(self.run, 1, 'audit', 'audit', values)
        self.assertFalse((self.folder / 'audit.private.json').exists())

    def test_save_requires_every_ordered_decision_and_valid_schema(self):
        values = self.make_run()
        with cwd(self.worktrees['editor_a']):
            review.show(self.run, 1, 'editor', 'editor_a')
            for invalid in (values[:1], list(reversed(values)), [values[0], values[0]], [None, values[1]],
                            [dict(values[0], stance='support'), values[1]]):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    review.save(self.run, 1, 'editor', 'editor_a', invalid)
        self.assertFalse((self.folder / 'editor-draft.private.json').exists())

    def test_independent_save_is_required_before_comparison(self):
        values = self.make_run()
        self.save_role('editor', values)
        with cwd(self.worktrees['audit']), self.assertRaises((ValueError, FileNotFoundError)):
            review.comparison(self.run, 1, 'audit')
        self.assertFalse((self.folder / 'comparison-start.private.json').exists())
        self.save_role('audit', values)
        with cwd(self.worktrees['audit']):
            paired = review.comparison(self.run, 1, 'audit')
        self.assertEqual(len(paired), 2)

    def test_self_audit_rejected_even_if_reservation_is_resealed(self):
        values = self.make_run()
        reservation = review.read(self.run / 'reservation.json')
        reservation['assignments']['audit'] = reservation['assignments']['editor_a']
        self.reseal(reservation=reservation)
        self.save_role('editor', values)
        with cwd(self.worktrees['editor_a']):
            review.show(self.run, 1, 'audit', 'editor_a')
            review.save(self.run, 1, 'audit', 'editor_a', values)
        with self.assertRaises(ValueError):
            review.verified_pair(self.run, 1)

    def test_early_comparison_cannot_be_gated(self):
        values = self.make_run()
        self.save_role('editor', values)
        self.save_role('audit', values)
        with cwd(self.worktrees['audit']):
            review.comparison(self.run, 1, 'audit')
            path = self.folder / 'comparison-start.private.json'
            rewrite(path, dict(review.read(path), compared_epoch=0))
            with self.assertRaises(ValueError):
                review.save_gate(self.run, 1, 'audit', self.checks(2))

    def test_draft_mismatch_and_invalid_decisions_cannot_enter_progress_counts(self):
        values = self.make_run()
        self.save_role('audit', values)
        final_path = self.folder / 'audit.private.json'
        draft_path = self.folder / 'audit-draft.private.json'
        original = review.read(final_path)
        wrong = copy.deepcopy(original)
        wrong['records'][0]['reason'] = 'Altered saved final.'
        rewrite(final_path, wrong)
        with self.assertRaises(ValueError):
            review.status(self.run)
        wrong['records'][0]['stance'] = 'support'
        rewrite(final_path, wrong)
        rewrite(draft_path, dict(review.read(draft_path), records=wrong['records']))
        with self.assertRaises(ValueError):
            review.status(self.run)

    def test_start_and_draft_only_are_reported_without_completed_credit(self):
        values = self.make_run()
        with cwd(self.worktrees['editor_a']):
            review.show(self.run, 1, 'editor', 'editor_a')
        state = review.status(self.run)
        self.assertEqual(state.get('editor', 0), 0)
        self.assertEqual(state['incomplete'], [{'batch': 1, 'role': 'editor', 'stage': 'start'}])
        review.write_new(self.folder / 'editor-draft.private.json', {'records': values, 'recorded_epoch': 0})
        state = review.status(self.run)
        self.assertEqual(state.get('editor', 0), 0)
        self.assertEqual(state.get('gated', 0), 0)
        self.assertEqual(state['remaining_to_gate'], 2)
        self.assertEqual(state['incomplete'][0]['stage'], 'draft')

    def test_orphan_draft_is_visible_but_not_complete(self):
        values = self.make_run()
        review.write_new(self.folder / 'audit-draft.private.json', {'records': values, 'recorded_epoch': 0})
        state = review.status(self.run)
        self.assertEqual(state.get('audit', 0), 0)
        self.assertEqual(state.get('gated', 0), 0)
        self.assertEqual(state['incomplete'], [{'batch': 1, 'role': 'audit', 'stage': 'draft'}])

    def test_gate_requires_exact_typed_individual_checks(self):
        checks = self.checks(2)
        variants = [None, checks[:1], list(reversed(checks)), [None, checks[1]],
                    [dict(checks[0], index=True), checks[1]],
                    [dict(checks[0], semantic_agreement=1), checks[1]],
                    [dict(checks[0], reason=' \t'), checks[1]],
                    [dict(checks[0], extra=True), checks[1]]]
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                review.validate_checks(variant, 2)

    def test_gate_cannot_be_resaved_and_source_change_is_rejected(self):
        values = self.make_run()
        self.finish(values)
        with cwd(self.worktrees['audit']), self.assertRaises(FileExistsError):
            review.save_gate(self.run, 1, 'audit', self.checks(2))
        path = self.folder / 'comparison-start.private.json'
        rewrite(path, dict(review.read(path), actor='other'))
        with self.assertRaises(ValueError):
            review.collect_batch(self.run, 1)

    def test_gate_actor_version_shape_and_chronology_tampering_rejected(self):
        values = self.make_run()
        self.finish(values)
        path = self.folder / 'quality_gate.private.json'
        original = review.read(path)
        for key, value in (('actor', 'other'), ('versions', {}), ('checks', []), ('finished_epoch', 0),
                           ('audit_sha256', '0' * 64)):
            rewrite(path, dict(original, **{key: value}))
            with self.subTest(key=key), self.assertRaises(ValueError):
                review.collect_batch(self.run, 1)

    def test_disagreement_and_weak_evidence_are_not_candidates(self):
        values = self.make_run()
        self.save_role('editor', values)
        other = copy.deepcopy(values)
        other[0]['is_opinion'] = False
        self.save_role('audit', other)
        checks = self.checks(2)
        checks[1]['reason_sufficient'] = False
        with cwd(self.worktrees['audit']):
            review.comparison(self.run, 1, 'audit')
            review.save_gate(self.run, 1, 'audit', checks)
        rows = review.collect_batch(self.run, 1)
        self.assertFalse(rows[0]['three_domain_agreement'])
        self.assertEqual(rows[1]['adoption_status'], 'pending_evidence')
        self.assertTrue(all(r['route'] == 'hold' for r in rows))

    def test_exclusive_writer_never_overwrites_saved_file(self):
        path = self.base / 'saved.json'
        review.write_new(path, {'original': True})
        before = path.read_bytes()
        with self.assertRaises(FileExistsError):
            review.write_new(path, {'replacement': True})
        self.assertEqual(path.read_bytes(), before)

    def test_freeze_rejects_shared_actor_or_worktree_before_reading_inputs(self):
        for field in ('actor', 'worktree'):
            assignments = copy.deepcopy(self.assignments)
            assignments['audit'][field] = assignments['editor_a'][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                review.freeze(self.root, self.base, self.base / 'new-run', assignments, self.base / 'absent.json')

    def freeze_fixture(self, count=782):
        private = self.base / 'freeze-private'
        previous_path = private / 'body-review-pilot/20260909-nonkoshitsu4352-handoff/final-results.private.json'
        rows = []
        for index in range(count):
            text = f'Synthetic reservation fixture {index}.'
            rows.append({'topic': review.TOPIC, 'record_id_hash': str(index),
                         'body_sha256': hashlib.sha256(text.encode()).hexdigest(),
                         'classification_sha256': 'c' * 64, 'text': text})
        review.write_new(previous_path, {'remaining_ids': rows})
        work = {'sources': [], 'records': [{'topic': review.TOPIC,
                                          'criteria_sha256': review.fingerprint({'synthetic': True})}]}
        scope = {'records': [dict(row, route='new_body_review', dependency=None) for row in rows]}
        approved = self.base / 'freeze-approval.json'
        review.write_new(approved, {'status': 'pass', 'versions': self.versions})
        return private, rows, work, scope, approved

    def freeze_with(self, private, rows, work, scope, approval):
        with patch.object(review, 'current_remaining', return_value=(rows, work, {'topics': {}})), \
             patch.object(review, 'load_resolution', return_value=scope), \
             patch.object(review, 'build_criteria', return_value={review.TOPIC: {'synthetic': True}}):
            return review.freeze(self.root, private, private / 'new-run', self.assignments, approval)

    def test_freeze_exact_782_is_split_into_single_theme_batches(self):
        private, rows, work, scope, approval = self.freeze_fixture()
        result = self.freeze_with(private, rows, work, scope, approval)
        self.assertEqual(result['target_count'], 782)
        self.assertEqual([m['count'] for m in result['batches']], [20] * 39 + [2])
        identities = []
        for meta in result['batches']:
            _, _, _, packet = review.packet_for(private / 'new-run', meta['batch'])
            identities.extend(map(review.key, packet['records']))
        self.assertEqual(len(identities), len(set(identities)))

    def test_freeze_count_mismatch_stops_without_creating_reservation(self):
        private, rows, work, scope, approval = self.freeze_fixture(781)
        with self.assertRaises(ValueError):
            self.freeze_with(private, rows, work, scope, approval)
        self.assertFalse((private / 'new-run').exists())

    def test_freeze_same_count_changed_id_or_classification_stops(self):
        private, rows, work, scope, approval = self.freeze_fixture()
        original = copy.deepcopy(rows)
        for field in ('record_id_hash', 'body_sha256', 'classification_sha256'):
            changed = copy.deepcopy(original)
            changed[0][field] = 'different'
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.freeze_with(private, changed, work, scope, approval)
        self.assertFalse((private / 'new-run').exists())

    def test_freeze_active_target_is_not_freed_by_gate_file_alone(self):
        private, rows, work, scope, approval = self.freeze_fixture()
        active = private / 'body-review-pilot/other-run/batch-01'
        review.write_new(active / 'packet.private.json', {'records': [rows[0]]})
        review.write_new(active / 'quality_gate.private.json', {'synthetic': 'not registered'})
        with self.assertRaises(ValueError):
            self.freeze_with(private, rows, work, scope, approval)
        self.assertFalse((private / 'new-run').exists())


if __name__ == '__main__':
    unittest.main()
