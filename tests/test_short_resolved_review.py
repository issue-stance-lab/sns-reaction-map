import copy
import unittest

from scripts.short_resolved_review import assess_all


class ShortAllAuditTests(unittest.TestCase):
    def setUp(self):
        label={'is_relevant':True,'is_opinion':True,'main_issue':'issue','stance':'neutral'}
        self.packet={'criteria':{'topic':{'issues':['issue'],'stances':['neutral','support']}},
                     'records':[{'topic':'topic','record_id_hash':str(i),'body_sha256':str(i),'classification_sha256':'labels','classification':label} for i in range(3)]}
        self.editor={'reviews':[{**{k:r[k] for k in ('record_id_hash','body_sha256','classification_sha256')},'index':i,'classification':dict(label),'uncertain':False,'evidence_sufficient':True,'reason':'fixture judgment'} for i,r in enumerate(self.packet['records'])]}
        self.audit=copy.deepcopy(self.editor)
        self.gate={'systemic_criteria_issue':False,'reason_conflicts':[],'additional_audit_topics':[]}

    def test_all_retains_have_independent_evidence(self):
        result=assess_all(self.packet,self.editor,self.audit,self.gate)
        self.assertEqual(result['independent_records'],3)
        self.assertTrue(all(r['independently_checked'] for r in result['journal']))

    def test_missing_alias_audit_is_rejected_even_when_retains_match(self):
        self.audit['reviews'].pop()
        with self.assertRaisesRegex(ValueError,'coverage'):assess_all(self.packet,self.editor,self.audit,self.gate)

    def test_disagreement_and_insufficient_reason_are_not_accepted(self):
        self.audit['reviews'][0]['classification']['stance']='support'
        self.audit['reviews'][1]['evidence_sufficient']=False
        result=assess_all(self.packet,self.editor,self.audit,self.gate)
        self.assertEqual([r['adoption_status'] for r in result['journal']],['hold','pending_evidence','accepted'])

    def test_wrong_post_version_is_rejected(self):
        self.audit['reviews'][2]['body_sha256']='different'
        with self.assertRaisesRegex(ValueError,'identity/version'):assess_all(self.packet,self.editor,self.audit,self.gate)
