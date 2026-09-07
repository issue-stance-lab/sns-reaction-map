import unittest
from scripts.editorial_acceptance import decide

class AcceptanceTest(unittest.TestCase):
    def row(self, i=0, route='retain_candidate', checked=True, first='no_change', topic='a'):
        return dict(index=i, route=route, first_route=first, independently_checked=checked, topic=topic)
    def gate(self, **kw):
        return dict(systemic_criteria_issue=False, reason_conflicts=[], **kw)
    def test_agreement_without_evidence_is_not_enough(self):
        r=decide([self.row()],{0:dict(evidence_sufficient=False)},{0:dict(evidence_sufficient=True)},self.gate())
        self.assertEqual(r[0]['adoption_status'],'pending_evidence')
    def test_hold_never_promoted(self):
        r=decide([self.row(route='hold')],{0:dict(evidence_sufficient=True)},{0:dict(evidence_sufficient=True)},self.gate())
        self.assertEqual(r[0]['adoption_status'],'hold')
    def test_failed_sample_blocks_same_topic_not_other(self):
        rows=[self.row(route='hold'),self.row(1,checked=False),self.row(2,checked=False,topic='b')]
        r=decide(rows,{i:dict(evidence_sufficient=True) for i in range(3)},{0:dict(evidence_sufficient=True)},self.gate())
        self.assertEqual([x['adoption_status'] for x in r],['hold','pending_audit','accepted'])
    def test_insufficient_or_conflicting_sample_blocks_other_retains(self):
        rows=[self.row(),self.row(1,checked=False)]
        for insufficient in [True,False]:
            gate=self.gate();gate['reason_conflicts']=[] if insufficient else [0]
            r=decide(rows,{0:dict(evidence_sufficient=not insufficient),1:dict(evidence_sufficient=True)},{0:dict(evidence_sufficient=True)},gate)
            self.assertEqual([x['adoption_status'] for x in r],['pending_evidence','pending_audit'])
    def test_change_requires_independent_review(self):
        r=decide([self.row(route='change_candidate',checked=False,first='candidate')],{0:dict(evidence_sufficient=True)},{},self.gate())
        self.assertEqual(r[0]['adoption_status'],'pending_audit')
    def test_boolean_must_not_be_truthy_string(self):
        with self.assertRaises(ValueError):decide([self.row()],{0:dict(evidence_sufficient='true')},{},self.gate())
    def test_accepted_does_not_apply_or_credit(self):
        r=decide([self.row()],{0:dict(evidence_sufficient=True)},{0:dict(evidence_sufficient=True)},self.gate())[0]
        self.assertEqual(r['adoption_status'],'accepted');self.assertFalse(r['canonical_applied']);self.assertFalse(r['counts_as_registered_editorial_reread'])

class AcceptedGenerationTest(unittest.TestCase):
    def test_only_accepted_changes_enter_generation_and_journal_is_preserved(self):
        from unittest.mock import patch
        from pathlib import Path
        from scripts.verify_editorial_wave import verify_accepted
        rows=[dict(index=0,route='change_candidate',adoption_status='accepted'),dict(index=1,route='change_candidate',adoption_status='pending_evidence')]
        def fake(root,run,out,*,collected,prepare_candidate):
            self.assertEqual([r['route'] for r in collected[0]['journal']],['change_candidate','hold'])
            return {'generation':{'passed':True}}
        with patch('scripts.verify_editorial_wave.verify',side_effect=fake),patch('scripts.verify_editorial_wave.dump'):
            result=verify_accepted(Path('.'),Path('.'),Path('unused'),({'journal':rows},{}))
        self.assertEqual(result['journal'],rows)
        self.assertEqual(result['journal'][1]['route'],'change_candidate')
