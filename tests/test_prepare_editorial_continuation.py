import unittest
from collections import deque

from scripts.prepare_editorial_continuation import (
    alternating_assignments,
    select_records,
    select_topic_homogeneous_records,
)


def row(name, *, opinion=True):
    return {
        'body_sha256': 'body-' + name,
        'classification_sha256': 'class-' + name,
        'opinion': opinion,
    }


class PrepareEditorialContinuationTest(unittest.TestCase):
    def test_round_robin_skips_registered_identities(self):
        queues = {
            'a': [row('a1'), row('a2'), row('a2'), row('a3')],
            'b': [row('b1'), row('b2')],
        }
        attempted = [{**row('a1'), 'topic': 'a'}]
        result = select_records(queues, attempted, 4)
        self.assertEqual(
            [(value['topic'], value['body_sha256']) for value in result],
            [('a', 'body-a2'), ('b', 'body-b1'), ('a', 'body-a3'), ('b', 'body-b2')],
        )

    def test_selection_requires_full_nonduplicate_limit(self):
        with self.assertRaisesRegex(ValueError, 'only 1'):
            select_records({'a': [row('a1')]}, [], 2)

    def test_topic_quota_selection_keeps_twenty_record_blocks_homogeneous(self):
        queues = {
            'a': [row(f'a{i}') for i in range(21)],
            'b': [row(f'b{i}') for i in range(20)],
        }
        attempted = [{**row('a0'), 'topic': 'a'}]
        result = select_topic_homogeneous_records(queues, attempted, {'a': 20, 'b': 20})
        self.assertEqual([value['topic'] for value in result[:20]], ['a'] * 20)
        self.assertEqual([value['topic'] for value in result[20:]], ['b'] * 20)

    def test_topic_quotas_must_be_twenty_aligned(self):
        with self.assertRaisesRegex(ValueError, 'multiple of 20'):
            select_topic_homogeneous_records({'a': [row('a1')]}, [], {'a': 1})

    def test_cross_audit_has_no_self_audit(self):
        assignments = alternating_assignments('/root/a', '/root/b')
        self.assertEqual(
            sorted(n for values in assignments['editor'].values() for n in values),
            list(range(1, 51)),
        )
        self.assertEqual(
            sorted(n for values in assignments['audit'].values() for n in values),
            list(range(1, 51)),
        )
        for actor in assignments['editor']:
            self.assertFalse(set(assignments['editor'][actor]) & set(assignments['audit'][actor]))


if __name__ == '__main__':
    unittest.main()
