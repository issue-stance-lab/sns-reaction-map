import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from fukushuto_target_data import aggregate_targets, validate_targets


class TargetDataTest(unittest.TestCase):
    def rows(self):
        return [dict(decision='include', main_issue='候補地', concept='肯定',
                     law='未表明', law_scope='未表明',
                     locations=[dict(name='大阪', stance='否定'),
                                dict(name='福岡', stance='肯定')]),
                dict(decision='include', main_issue='防災・災害', concept='未表明',
                     law='肯定', law_scope='別案・追加提案', locations=[])]

    def test_multi_target_is_one_post_per_issue_and_target(self):
        d = aggregate_targets(self.rows())
        self.assertEqual(d['opinion_count'], 2)
        osaka = next(x for x in d['targets'] if x['label'] == '大阪')
        self.assertEqual(osaka['counts']['否定'], 1)
        self.assertEqual(osaka['counts']['未表明'], 1)
        self.assertEqual(osaka['evaluated_count'], 1)
        self.assertEqual(next(x for x in osaka['issues'] if x['issue'] == '候補地')['counts']['否定'], 1)
        bill = next(x for x in d['targets'] if x['id'] == 'law-0')
        self.assertEqual(bill['evaluated_count'], 0)
        self.assertEqual(bill['counts']['未表明'], 2)

    def test_hold_and_partial_unknown_do_not_become_votes(self):
        rows = self.rows()
        held = copy.deepcopy(rows[0]); held['decision'] = 'hold'; rows.append(held)
        rows[0]['locations'][0]['stance'] = '判定保留'
        d = aggregate_targets(rows)
        osaka = next(x for x in d['targets'] if x['label'] == '大阪')
        self.assertEqual(d['opinion_count'], 2)
        self.assertEqual(osaka['counts']['判定保留'], 1)
        self.assertEqual(osaka['counts']['否定'], 0)

    def test_location_id_does_not_shift_when_a_place_is_added(self):
        rows = self.rows(); before = aggregate_targets(rows)
        rows[0]['locations'].append(dict(name='京都', stance='条件付き'))
        after = aggregate_targets(rows)
        self.assertEqual(next(x['id'] for x in before['targets'] if x['label'] == '大阪'),
                         next(x['id'] for x in after['targets'] if x['label'] == '大阪'))

    def test_corrupted_cross_counts_are_rejected(self):
        d = aggregate_targets(self.rows())
        d['targets'][0]['issues'][0]['counts']['肯定'] += 1
        with self.assertRaises(ValueError): validate_targets(d)

    def test_real_snapshot_matches_approved_totals_and_contains_no_posts(self):
        r = json.loads((ROOT / 'quality/reviews/2026-09-13-fukushuto-target-review.json').read_text())
        d = aggregate_targets(r['records'])
        self.assertEqual(d['opinion_count'], 1497)
        self.assertEqual(d['targets'][0]['counts'], r['concept'])
        for s, counts in r['law_by_scope'].items():
            actual = next(x for x in d['targets'] if x['kind'] == 'law' and x['label'] == s)
            for k in counts:
                if k != '未表明': self.assertEqual(actual['counts'][k], counts[k])
        for loc in r['locations']:
            actual = next(x for x in d['targets'] if x['kind'] == 'location' and x['label'] == loc['name'])
            self.assertEqual(actual['evaluated_count'], loc['posts'])
        serialized = json.dumps(d)
        for private in ('tweet_id', 'post_key', 'text_sha256', 'reason', 'records'):
            self.assertNotIn('"'+private+'"', serialized)


if __name__ == '__main__': unittest.main()
