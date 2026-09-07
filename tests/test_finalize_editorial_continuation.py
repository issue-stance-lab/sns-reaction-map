import unittest

from scripts.finalize_editorial_continuation import combine_journals


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


if __name__ == '__main__':
    unittest.main()
