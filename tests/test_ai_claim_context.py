"""条件説明・程度評価を、誤りの採点や山の色へ読み替えない。"""
import copy
import json
import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from scripts.claim_assessment import validate_assessment
from scripts import build_planet_data as bpd
from scripts import public_registry_common as prc

ROOT = Path(__file__).resolve().parents[1]

class ClaimContextTests(unittest.TestCase):
    def test_null_requires_explicit_context_and_context_forbids_truth_verdict(self):
        for bad in [{"verdict":None}, {"verdict":"unknown"},
                    {"verdict":"gap","assessment_kind":"evaluation_context"},
                    {"verdict":None,"assessment_kind":"unknown"}]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_assessment(bad)
        for kind in ['conditional_explanation','evaluation_context']:
            validate_assessment({'verdict':None,'assessment_kind':kind})

    def test_context_never_colors_the_issue_as_fact_gap_or_miss(self):
        context={'id':'r','verdict':None,'assessment_kind':'evaluation_context','issue_ids':['x'],'matched_post_count':86}
        verdict,matched=bpd.issue_verdict('x',[context]);self.assertIsNone(verdict);self.assertEqual(matched,[context])
        zero={'id':'h','verdict':'gap','issue_ids':['x'],'matched_post_count':0}
        self.assertIsNone(bpd.issue_verdict('x',[context,zero],ignore_empty=True)[0])
        positive={**zero,'matched_post_count':8}
        self.assertEqual(bpd.issue_verdict('x',[context,positive],ignore_empty=True)[0],'gap')

    def test_schema_rejects_null_without_kind_or_false_truth_labels(self):
        schema=json.loads((ROOT/'schemas/public-theme.schema.json').read_text())
        claim=copy.deepcopy(prc.build_claim_verification('ai-copyright')['claims'][-1])
        def errors(value):
            return prc.validate_schema(value,schema['$defs']['claim'],schema)
        self.assertEqual(errors(claim),[])
        for change in [{'verdict':'gap'},{'assessment_kind':'unknown'}]:
            with self.subTest(change=change):
                self.assertTrue(errors({**claim,**change}))
        claim.pop('assessment_kind')
        self.assertTrue(errors(claim))

    def test_schema_one_of_rejects_overlap_and_keeps_sibling_constraints(self):
        schema={'type':'object','additionalProperties':False,'properties':{'x':{'type':'string'}},
                'oneOf':[{'type':'object','required':['x']},{'type':'object','required':['y']}]}
        self.assertEqual(prc.validate_schema({'x':'a'},schema),[])
        self.assertTrue(prc.validate_schema({'x':'a','y':'b'},schema))
        self.assertTrue(prc.validate_schema({'x':'a','z':'b'},schema))

    def test_release_page_preserves_counts_explanations_sources_and_zero_notes(self):
        public=json.loads((ROOT/'docs/data/themes/ai-copyright.json').read_text())
        soup=BeautifulSoup((ROOT/'docs/ai-copyright-reaction-map.html').read_text(),'html.parser')
        for c in public['claim_verification']['claims']:
            nodes=soup.select(f'.fr-claim[data-claim="{c["id"]}"]');self.assertTrue(nodes)
            for n in nodes:
                self.assertIn(c['claim'],n.get_text());self.assertIn(c['finding'],n.get_text());self.assertIn(c['source_summary'],n.get_text())
                self.assertIn(f"{c['matched_post_count']}件",n.get_text())
                for source in c['sources']:self.assertTrue(n.select(f'a[href="{source["url"]}"]'))
                if not c['matched_post_count']:self.assertIn('直接の表明は見つかりませんでした',n.get_text())
                if c['verdict'] is None:
                    self.assertNotIn('fr-verdict-gap',n.get('class',[]))
                    self.assertEqual(n.select_one('.fr-verdict').get_text(),bpd.claim_label(c))

if __name__=='__main__':unittest.main()
