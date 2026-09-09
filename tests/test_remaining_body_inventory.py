"""Identity exclusions must not silently grant review credit to another ID."""
import unittest

from scripts.inventory_remaining_body_reviews import partition, post_key, input_key


def row(post, body='body', version='v1'):
    return {'topic': 'topic', 'record_id_hash': post,
            'body_sha256': body, 'classification_sha256': version}


class RemainingBodyInventoryTests(unittest.TestCase):
    def test_same_body_other_id_remains_unconfirmed(self):
        old, alias = row('1'), row('2')
        eligible, excluded = partition([alias], {}, {input_key(old)}, {post_key(old)})
        self.assertEqual(eligible, [])
        self.assertEqual(excluded[0]['record_id_hash'], '2')
        self.assertEqual(excluded[0]['exclusion_reasons'], ['same_input_as_existing_work_different_id'])

    def test_changed_classification_is_not_same_input(self):
        old, changed = row('1'), row('2', version='v2')
        eligible, excluded = partition([changed], {}, {input_key(old)})
        self.assertEqual(eligible, [changed])
        self.assertEqual(excluded, [])

    def test_unfinished_id_and_invalid_id_do_not_seed_fresh_group(self):
        attempted, invalid, fresh, alias = row('1', 'a'), row('2', 'b'), row('3', 'c'), row('4', 'c')
        reasons = {'unfinished': {post_key(attempted)}, 'invalid': {post_key(invalid)}}
        eligible, excluded = partition([alias, attempted, invalid, fresh], reasons,
                                       {input_key(attempted)}, {post_key(attempted)})
        self.assertEqual(eligible, [fresh])
        self.assertEqual([r['exclusion_reasons'] for r in excluded],
                         [['unfinished'], ['invalid'], ['same_input_as_another_unconfirmed_id']])


if __name__ == '__main__':
    unittest.main()
