"""Synthetic metadata only: no raw posts or body judgments are read."""
import copy
import unittest

from scripts.review_completion_identity_counts import identity_counts


def row(topic, post, body='same-body', state='hold', route='new_body_review'):
    return dict(topic=topic, record_id_hash=post, body_sha256=body,
                classification_sha256='labels', criteria_sha256='criteria',
                state=state, route=route)


class IdentityCountsTests(unittest.TestCase):
    def inspect(self, rows, old=(), scope=None):
        return identity_counts([rows], {'records': rows if scope is None else scope}, {'records': list(old)})

    def test_legacy_attempts_and_distinct_id_aliases_do_not_block(self):
        old = [row('tax', f'legacy-{i}', state='attempted') for i in range(56)]
        old.append(row('tax', 'old-completed'))
        resumed = [row('tax', f'legacy-{i}', route='resume_unfinished_review') for i in range(56)]
        aliases = [row('tax', f'alias-{i}', route='verify_distinct_id_against_existing_review') for i in range(127)]
        result = self.inspect(resumed + aliases, old)
        self.assertFalse(any(result['blocking'].values()))
        self.assertEqual(result['records'], 183)
        self.assertEqual(result['reference']['resumed_attempted_version_rows'], 56)
        self.assertEqual(result['reference']['distinct_id_verification_rows'], 127)
        self.assertEqual(result['reference']['baseline_completed_records'], 1)

    def test_cross_theme_global_id_is_reference_only(self):
        result = self.inspect([row('tax', 'same-id')], [row('fuku', 'same-id')])
        self.assertFalse(any(result['blocking'].values()))
        self.assertEqual(result['reference']['global_id_reappears_in_baseline_completed_count'], 1)
        self.assertEqual(result['reference']['global_id_reappears_in_baseline_completed'][0]['baseline_topics'], ['fuku'])
        result = self.inspect([row('tax', 'same-id'), row('fuku', 'same-id')])
        self.assertFalse(any(result['blocking'].values()))
        self.assertEqual(len(result['reference']['global_id_across_theme_recurrences']), 1)

    def test_same_topic_id_repeat_counts_even_across_journals(self):
        original = row('tax', 'id')
        result = identity_counts([[original], [copy.deepcopy(original)]],
                                 {'records': [original]}, {'records': []})
        self.assertEqual(result['blocking']['topic_id_duplicate_excess_rows'], 1)
        self.assertEqual(result['blocking']['topic_id_body_classification_duplicate_excess_rows'], 1)
        self.assertEqual(result['blocking']['topic_id_body_classification_criteria_duplicate_excess_rows'], 1)

    def test_old_completed_id_cannot_be_hidden_by_changed_version(self):
        old = row('tax', 'id', body='old-body')
        result = self.inspect([row('tax', 'id', body='new-body')], [old])
        self.assertEqual(result['blocking']['previously_completed_topic_id_rows'], 1)
        self.assertEqual(result['blocking']['previously_completed_full_version_rows'], 0)
        result = self.inspect([old], [old])
        self.assertEqual(result['blocking']['previously_completed_full_version_rows'], 1)

    def test_scope_version_changes_are_rejected(self):
        original = row('tax', 'id')
        for field in ('body_sha256', 'classification_sha256', 'criteria_sha256'):
            with self.subTest(field=field):
                changed = {**original, field: 'changed'}
                with self.assertRaisesRegex(ValueError, 'differs from scope'):
                    self.inspect([changed], scope=[original])

    def test_journal_without_criteria_uses_validated_scope_version(self):
        original = row('tax', 'id')
        journal = {k: v for k, v in original.items() if k != 'criteria_sha256'}
        self.assertEqual(self.inspect([journal], [original], [original])['blocking']['previously_completed_full_version_rows'], 1)


if __name__ == '__main__':
    unittest.main()
