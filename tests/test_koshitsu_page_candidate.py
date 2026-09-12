import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_koshitsu_page_candidate import prepare_template
from refresh_adapters.koshitsu import vote_fingerprint
from public_registry_common import validate_public_theme,check_theme_invariants
from reread_registry import validate_manifest

class KoshitsuCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=ROOT/'quality/candidates/koshitsu-tenpakai'
        cls.public=json.loads((cls.base/'inputs/data/public/themes/koshitsu-tenpakai.json').read_text())
        cls.original=(ROOT/'docs/koshitsu-tenpakai-reaction-map.html').read_text()
        cls.preview=(ROOT/'quality/prototypes/koshitsu-tenpakai-page-preview.html').read_text()

    def test_issue_media_and_destinations(self):
        from bs4 import BeautifulSoup
        page=BeautifulSoup(self.preview, 'html.parser')
        for issue in self.public['issues']:
            iid=issue['id']
            card=page.find(id='issue-'+iid)
            self.assertIsNotNone(card)
            image=card.find('img')
            self.assertTrue((ROOT/'quality/prototypes'/image['src']).resolve().is_file())
            self.assertEqual(len(card.select('blockquote.twitter-tweet a')),2)
            self.assertIsNotNone(page.find(id='fb-'+iid).find('a',href='#issue-'+iid))
        self.assertIn('href="#issue-\'+it.id',self.preview)
        self.assertEqual(len(page.select('#issue-cards article')),6)

    def test_public_contract_and_complete_cross_table(self):
        self.assertEqual(validate_public_theme(self.public)+check_theme_invariants(self.public),[])
        self.assertEqual(sum(i['count'] for i in self.public['issues']),self.public['opinion_count'])
        for issue in self.public['issues']:
            self.assertEqual(sum(x['count'] for x in issue['stances']),issue['count'])
            self.assertTrue(all('-package-' in x['id'] for x in issue['stances']))

    def test_review_membership_and_saved_fingerprints(self):
        meta=json.loads((self.base/'manifest.json').read_text())
        for relative,expected in meta['inputs'].items():
            self.assertEqual(hashlib.sha256((self.base/relative).read_bytes()).hexdigest(),expected,relative)
        registry=json.loads((self.base/'inputs/data/verification/reread/koshitsu-tenpakai.json').read_text())
        validate_manifest(registry)
        reviews=[r for r in registry['records'] if r['review']]
        self.assertEqual(len(reviews),self.public['opinion_count'])
        self.assertTrue(all(r['is_opinion'] for r in reviews))
        self.assertEqual(len(registry['records']),self.public['collected_count'])

    def test_vote_contract_is_preserved_and_preview_is_local(self):
        self.assertEqual(vote_fingerprint(self.original),vote_fingerprint(self.preview))
        self.assertEqual(vote_fingerprint(self.preview)[3],24)
        self.assertIn('window.SNS_VOTE_CONFIG={}',self.preview)
        self.assertNotRegex(self.preview,r'<script[^>]*src="[^"]*vote-config\.js')
        self.assertIn("var STORAGE_KEY='sns_preview_vote_'",self.preview)
        self.assertRegex(self.preview,r'<meta[^>]+name="robots"[^>]+noindex')

    def test_legacy_graph_and_source_findings_do_not_return(self):
        template=prepare_template(self.original,self.public)
        for token in ['const SM_RAW','id="koshitsu-audit"','class="update-dashboard"','改正賛成（女系容認）','改正反対（男系維持）']:
            self.assertNotIn(token,template)
            self.assertNotIn(token,self.preview)
        self.assertIn('未表明は、中立や無関心の意味ではありません',self.preview)
        claims={x['id']:x for x in self.public['claim_verification']['claims']}
        self.assertEqual(claims['claim_3_養子継承資格']['verdict'],'fact')
        self.assertEqual(claims['claim_5_継承資格者3名']['verdict'],'gap')
        self.assertEqual(claims['claim_6_第二条継承順序']['matched_post_count'],1)

    def test_no_raw_post_identity_or_body_in_safe_inputs(self):
        for p in (self.base/'inputs').rglob('*.json'):
            t=p.read_text()
            self.assertNotRegex(t,r'https://(?:x|twitter)\.com/[^\s"]+/status/\d+',str(p))
            self.assertNotRegex(t,r'"tweet_id"\s*:',str(p))
            self.assertNotIn('\\tSTART\\t',t,str(p))

    def test_nojs_height_matches_interactive_raw_percentage(self):
        for issue in self.public['issues']:
            high=next(x['count'] for x in issue['intensities'] if x['id']=='high')
            expected=round(100*high/issue['count'],1)
            match=re.search(r'<section[^>]+id="fb-'+re.escape(issue['id'])+r'".*?山の高さ：強い表現([0-9.]+)%',self.preview,re.S)
            self.assertIsNotNone(match)
            self.assertEqual(float(match[1]),expected)
