import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from scripts.verify_editorial_hundred import dump, sha
from scripts.editorial_work_registry import fingerprint

from scripts.finalize_editorial_continuation import (
    combine_journals, overlay_supplements, register_work_only, RESULT_PREFIX,
)


def journal(record, status='accepted', route='retain_candidate'):
    return {
        'topic': 'topic',
        'record_id_hash': f'id-{record}',
        'body_sha256': f'body-{record}',
        'classification_sha256': f'class-{record}',
        'adoption_status': status,
        'route': route,
        'batch': record,
    }


class FinalizeEditorialContinuationTest(unittest.TestCase):
    def test_combines_without_applying_baseline(self):
        baseline = [journal(0, 'hold', 'hold')]
        waves = [
            {'journal': [journal(1)], 'independent_records': 1},
            {'journal': [journal(2, 'pending_evidence', 'change_candidate')], 'independent_records': 1},
        ]
        result = combine_journals(baseline, waves, expected_new=2)
        self.assertEqual(result['baseline_records'], 1)
        self.assertEqual(result['new_records'], 2)
        self.assertEqual(result['reviewed_records_if_adoption_is_applied'], 3)
        self.assertEqual(result['new_adoption_counts'], {'accepted': 1, 'pending_evidence': 1})
        self.assertEqual(result['cumulative_adoption_counts_if_applied'], {'accepted': 1, 'hold': 1, 'pending_evidence': 1})

    def test_rejects_unfinished_audit(self):
        wave = {'journal': [journal(1, 'pending_audit')], 'independent_records': 0}
        with self.assertRaisesRegex(ValueError, 'supplemental audit'):
            combine_journals([], [wave], expected_new=1)

    def test_rejects_duplicate_baseline_identity(self):
        wave = {'journal': [journal(1)], 'independent_records': 0}
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            combine_journals([journal(1)], [wave], expected_new=1)


class SupplementOverlayTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.run = self.root / 'run'
        self.folder = self.root / 'supplement'
        self.row = {**journal(1, 'pending_audit'), 'index': 0,
                    'proposed': {}, 'current': {}, 'changes': {}}
        dump(self.run / 'reservation.json', {'version': 1})
        dump(self.run / 'wave-01/reservation.json', {'version': 1})
        dump(self.run / 'wave-01/batch-01/editor-actor.private.json', {'actor': 'editor'})
        dump(self.folder / 'batch-01/audit.private.json', {'actor': 'auditor'})
        provenance = {
            'source_run': str(self.run.resolve()),
            'source_top_reservation_sha256': sha(self.run / 'reservation.json'),
            'source_wave': 'wave-01',
            'source_wave_reservation_sha256': sha(self.run / 'wave-01/reservation.json'),
            'source_batches': [1],
        }
        dump(self.folder / 'reservation.json', {'source_provenance': provenance})
        dump(self.folder / 'baseline.private.json', {
            'source_provenance': provenance,
            'source_journal_sha256': fingerprint([self.row]),
            'records': [{'supplemental_batch': 1, 'source_key': [1, 0]}],
        })
        self.report = {'overlay': [{'source_key': [1, 0], 'old': self.row,
                                   'new': {**self.row, 'adoption_status': 'hold'}}],
                       'supplemental_audits': 1}

    def call(self, folders=None):
        with patch('scripts.finalize_editorial_continuation.supplemental_editorial_audit.collect', return_value=self.report):
            return overlay_supplements(self.root, self.run, 'wave-01',
                                       {'journal': [self.row]}, folders or [self.folder])

    def test_replays_hold_without_changing_proposal(self):
        result = self.call()
        self.assertEqual(result['adoption_counts'], {'hold': 1})
        self.assertEqual(self.row['adoption_status'], 'pending_audit')
        self.assertEqual(result['supplemental_audits'], 1)

    def test_rejects_duplicate_supplement(self):
        with self.assertRaisesRegex(ValueError, 'overlay does not match'):
            self.call([self.folder, self.folder])

    def test_rejects_self_audit(self):
        dump(self.folder / 'batch-01/audit.private.json', {'actor': 'editor'})
        with self.assertRaisesRegex(ValueError, 'self audit'):
            self.call()

    def test_rejects_changed_source(self):
        dump(self.run / 'reservation.json', {'version': 2})
        with self.assertRaisesRegex(ValueError, 'another source wave or version'):
            self.call()


class WorkRegistrationFailureTest(unittest.TestCase):
    def test_conflicting_report_does_not_write_work_registry(self):
        with tempfile.TemporaryDirectory() as temp:
            root, private = Path(temp) / 'root', Path(temp) / 'private'
            run = private / 'run'
            work_path = root / 'data/verification/editorial-work.json'
            old = {'sources': [], 'records': []}
            dump(work_path, old)
            before = work_path.read_bytes()
            dump(run / 'work-before.private.json', old)
            dump(run / 'adoption-before.private.json', {})
            dump(run / 'reservation.json', {
                'baseline_work_records': 0, 'topic_counts': {}, 'opinion_counts': {},
            })
            for n in range(1, 5):
                dump(run / f'wave-{n:02d}/reservation.json', {})
            dump(root / 'quality/reviews' / f'{RESULT_PREFIX}-results.json', {'conflict': True})
            combined = {'new_records': 1, 'baseline_records': 0,
                        'reviewed_records_if_adoption_is_applied': 1,
                        'new_adoption_counts': {}, 'cumulative_adoption_counts_if_applied': {},
                        'new_routes': {}, 'independent_new_records': 0}
            with patch('scripts.finalize_editorial_continuation.verify_and_collect', return_value=(combined, [])), \
                 patch('scripts.finalize_editorial_continuation.load_registry', return_value=old), \
                 patch('scripts.finalize_editorial_continuation.build_registry', return_value={'records': [{}]}), \
                 patch('scripts.finalize_editorial_continuation.validate_work_lineage'):
                with self.assertRaisesRegex(ValueError, 'different result report'):
                    register_work_only(root, private, run)
            self.assertEqual(work_path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
