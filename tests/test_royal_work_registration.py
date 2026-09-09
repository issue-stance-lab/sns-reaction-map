"""Synthetic end-to-end work registration and interruption recovery."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts import royal_body_review as review
from tests import test_royal_body_review as fixtures

rewrite = fixtures.rewrite


class RoyalWorkRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.RoyalBodyReviewTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        values = f.make_run(2)
        self.root = f.base / 'repository'
        self.root.mkdir()
        self.private = f.base / 'private'
        self.run = f.run
        (self.root / 'taxonomy.py').write_text('# Synthetic source taxonomy')
        criterion = {'source': 'taxonomy.py', 'source_sha256': review.sha(self.root / 'taxonomy.py')}
        packet = review.read(f.folder / 'packet.private.json')
        classification = {'is_relevant': True, 'is_opinion': True, 'main_issue': 'synthetic', 'stance': 'old'}
        for row in packet['records']:
            row['classification_sha256'] = review.fingerprint(classification)
        f.reseal(packet=packet)
        raw = [dict(r, classification=classification) for r in packet['records']]
        self.targets = [{k: r[k] for k in review.KEYS} for r in raw]
        machine = {'records': raw, 'input_sha256': review.fingerprint(raw), 'criteria': {review.TOPIC: criterion}}
        rewrite(f.folder / 'registry-packet.private.json', machine)
        old_packet = dict(machine, records=raw[:1], input_sha256=review.fingerprint(raw[:1]))
        old_path = self.private / 'legacy-packet.json'
        review.write_new(old_path, old_packet)
        sources = [{'path': old_path.name, 'storage': 'private', 'kind': 'packet', 'sha256': review.sha(old_path)}]
        self.before = review.build_registry(sources, self.root, self.private)
        self.work_path = self.root / 'data/verification/editorial-work.json'
        review.write_new(self.work_path, self.before)
        (self.run / 'work-before.private.json').write_bytes(self.work_path.read_bytes())
        for rel in ('THEMES.yaml', 'data/verification/editorial-adoption-current.json',
                    'data/verification/editorial-review-scope.json', 'canonical.json'):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{}')
        baseline = {
            'work_before_sha256': review.sha(self.work_path),
            'canonical': {'canonical.json': review.sha(self.root / 'canonical.json')},
            'THEMES.yaml': review.sha(self.root / 'THEMES.yaml'),
            'adoption_sha256': review.sha(self.root / 'data/verification/editorial-adoption-current.json'),
            'scope_summary_sha256': review.sha(self.root / 'data/verification/editorial-review-scope.json'),
        }
        rewrite(self.run / 'baseline.private.json', baseline)
        reservation = review.read(self.run / 'reservation.json')
        reservation['baseline_sha256'] = review.sha(self.run / 'baseline.private.json')
        reservation['batches'][0]['registry_packet_sha256'] = review.sha(f.folder / 'registry-packet.private.json')
        f.reseal(reservation=reservation)
        previous = self.private / 'body-review-pilot/20260909-nonkoshitsu4352-handoff/final-results.private.json'
        review.write_new(previous, {'remaining_ids': self.targets})
        f.finish(values)
        queue = [dict(r, opinion=True) for r in raw]
        report = {'topics': {review.TOPIC: {'published': True}}}
        self.inventory = patch.object(review, 'inventory', return_value=(report, {review.TOPIC: queue}))
        self.inventory.start()
        self.addCleanup(self.inventory.stop)

    def test_registers_completed_ids_and_preserves_attempt_history(self):
        result = review.register_completed(self.root, self.private, self.run)
        self.assertEqual((result['completed_ids'], result['legacy_attempts_completed'], result['work_records']), (2, 1, 2))
        self.assertEqual(result['remaining_public_opinions'], 0)
        self.assertEqual(result['adoption_candidates'], 0)
        work = review.load_registry(self.work_path, self.root, self.private)
        old = self.before['records'][0]
        current = next(r for r in work['records'] if r['work_key'] == old['work_key'])
        self.assertEqual(current['state'], 'hold')
        self.assertTrue(set(old['evidence']) <= set(current['evidence']))
        self.assertTrue(all(not r['canonical_applied'] for r in work['records']))

    def test_interrupted_atomic_replace_recovers_from_saved_intent(self):
        before_sha = review.sha(self.work_path)
        with patch.object(review, 'replace_work', side_effect=RuntimeError('simulated interruption')):
            with self.assertRaises(RuntimeError):
                review.register_completed(self.root, self.private, self.run)
        self.assertEqual(review.sha(self.work_path), before_sha)
        self.assertTrue((self.run / 'registration-001.private.json').exists())
        result = review.register_completed(self.root, self.private, self.run)
        self.assertEqual(result['remaining_public_opinions'], 0)
        self.assertEqual(len(review.load_registry(self.work_path, self.root, self.private)['records']), 2)

    def test_remainder_mismatch_stops_before_ledger_replacement(self):
        before_sha = review.sha(self.work_path)
        extra = copy.deepcopy(self.targets[0]); extra['record_id_hash'] = 'unexpected'
        report = {'topics': {review.TOPIC: {'published': True}}}
        with patch.object(review, 'inventory', return_value=(report, {review.TOPIC: [dict(extra, opinion=True)]})):
            with self.assertRaisesRegex(ValueError, 'public remainder differs'):
                review.register_completed(self.root, self.private, self.run)
        self.assertEqual(review.sha(self.work_path), before_sha)
        self.assertFalse(list(self.run.glob('registration-*.private.json')))

    def test_changed_canonical_prevents_any_registration(self):
        before_sha = review.sha(self.work_path)
        (self.root / 'canonical.json').write_text('{"changed": true}')
        with self.assertRaisesRegex(ValueError, 'canonical source changed'):
            review.register_completed(self.root, self.private, self.run)
        self.assertEqual(review.sha(self.work_path), before_sha)


if __name__ == '__main__':
    unittest.main()
