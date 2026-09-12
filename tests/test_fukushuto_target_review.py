import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_fukushuto_target_review import compile_review, digest, render_preview

class TargetReviewTest(unittest.TestCase):
    def fixture(self):
        baseline=[{'tweet_id':'a','text':'構想はよいが大阪は違う','classification':{'is_opinion':True,'is_relevant':True,'main_issue':'候補地','stance':'法案反対'}}]
        r={'index':0,'post_key':digest(b'a'),'text_sha256':digest(baseline[0]['text'].encode()),'read_at':'2026-09-13T00:00:00Z','reason':'構想支持と地域批判を分ける','decision':'include','main_issue':'候補地','concept':'肯定','law':'未表明','law_scope':'未表明','locations':[{'name':'大阪','stance':'否定'},{'name':'福岡','stance':'肯定'}]}
        return baseline,{'records':[r]}

    def test_targets_do_not_become_bill_votes_or_extra_posts(self):
        b,r=self.fixture();d=compile_review(b,r)
        self.assertEqual(d['candidate_opinions'],1)
        self.assertEqual(d['location_evaluating_posts'],1)
        self.assertEqual(len(d['locations']),2)
        self.assertEqual(d['law_unexpressed'],1)
        self.assertEqual(sum(sum(c.values()) for c in d['law_by_scope'].values()),0)
        self.assertFalse(d['can_publish'])
        self.assertNotIn('text',d['records'][0])
        self.assertNotIn('tweet_id',d['records'][0])

    def test_partial_and_wrong_evidence_are_rejected(self):
        b,r=self.fixture()
        with self.assertRaises(ValueError):compile_review(b,{'records':[]})
        bad=copy.deepcopy(r);bad['records'][0]['text_sha256']='stale'
        with self.assertRaises(ValueError):compile_review(b,bad)
        bad=copy.deepcopy(r);bad['records'][0]['index']=1
        with self.assertRaises(ValueError):compile_review(b,bad)

    def test_alternative_is_not_added_to_bill_scope(self):
        b,r=self.fixture();r['records'][0].update(law='肯定',law_scope='別案・追加提案')
        d=compile_review(b,r)
        self.assertEqual(d['law_by_scope']['別案・追加提案']['肯定'],1)
        self.assertEqual(d['law_by_scope']['法案・成立法（版未確定）']['肯定'],0)

    def test_held_post_has_no_effect_on_stance_or_issue_counts(self):
        b,r=self.fixture();r['records'][0]['decision']='hold'
        d=compile_review(b,r)
        self.assertEqual(d['candidate_opinions'],0)
        self.assertEqual(d['pending_posts'],1)
        self.assertEqual(sum(d['concept'].values()),0)
        self.assertEqual(sum(x['after'] for x in d['issues']),0)

    def test_invalid_exclusion_or_duplicate_city_is_rejected(self):
        b,r=self.fixture();r['records'][0]['decision']='exclude'
        with self.assertRaises(ValueError):compile_review(b,r)
        b,r=self.fixture();r['records'][0]['locations']*=2
        with self.assertRaises(ValueError):compile_review(b,r)

    def test_preview_embedded_data_cannot_close_script(self):
        b,r=self.fixture();r['records'][0]['locations'][0]['name']='</script><img src=x>'
        d=compile_review(b,r)
        out=render_preview(d,[], '<script>__DATA__</script>__STATIC_TABLES__')
        self.assertEqual(out.count('</script>'),1)
        payload=out.split('<script>',1)[1].split('</script>',1)[0]
        self.assertIn('</script><img src=x>',[x['name'] for x in json.loads(payload)['locations']])

    def test_committed_review_matches_twenty_accepted_examples(self):
        d=json.loads((ROOT/'quality/reviews/2026-09-13-fukushuto-target-review.json').read_text())
        by_key={r['post_key']:r for r in d['records']}
        examples=json.loads((ROOT/'quality/reviews/2026-09-12-fukushuto-20-comparison.json').read_text())['items']
        for x in examples:
            r=by_key[x['post_key']];self.assertEqual(r['text_sha256'],x['text_sha256'])
            self.assertTrue(x['proposal']['concept'].startswith(r['concept']))
            self.assertTrue(x['proposal']['law_and_design'].startswith(r['law']))
            decision=x['proposal']['opinion_decision']
            self.assertEqual(r['decision'],'hold' if '保留' in decision else 'exclude' if '外す' in decision else 'include')
        self.assertEqual(sum(d['decisions'].values()),d['original_total'])
        self.assertEqual(sum(x['after'] for x in d['issues']),d['candidate_opinions'])
        self.assertEqual(sum(d['concept'].values()),d['candidate_opinions'])
        self.assertEqual(d['law_unexpressed']+sum(sum(c.values()) for c in d['law_by_scope'].values()),d['candidate_opinions'])

if __name__=='__main__':unittest.main()
