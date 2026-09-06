import copy
import unittest
from scripts.summarize_editorial_batch import summarize,verified_reviews

class EditorialBatchTests(unittest.TestCase):
    def setUp(self):
        c={'is_relevant':True,'is_opinion':True,'main_issue':'a','stance':'neutral'}
        r={'topic':'t','record_id_hash':'id','body_sha256':'body','classification_sha256':'class','classification':c}
        self.packet={'records':[r],'criteria':{'t':{'issues':['a','b'],'stances':['neutral','pro']}}}
        self.editor={'reviews':[{'index':0,**{k:r[k] for k in ['record_id_hash','body_sha256','classification_sha256']},'classification':dict(c),'uncertain':False,'reason':'本文に沿った判断'}]}
    def test_changes_wait_for_independent_review(self):
        self.editor['reviews'][0]['classification']['stance']='pro'
        self.assertEqual(summarize(self.packet,self.editor)['routes'],{'independent_review_pending':1})
    def test_agreement_still_candidate_not_applied(self):
        self.editor['reviews'][0]['classification']['stance']='pro'
        r=summarize(self.packet,self.editor,copy.deepcopy(self.editor))
        self.assertEqual(r['routes'],{'change_candidate':1});self.assertEqual(r['canonical_changes'],0)
    def test_disagreement_becomes_hold(self):
        audit=copy.deepcopy(self.editor);audit['reviews'][0]['classification']['stance']='pro'
        self.assertEqual(summarize(self.packet,self.editor,audit)['routes'],{'hold':1})
    def test_initial_hold_not_overridden(self):
        audit=copy.deepcopy(self.editor);self.editor['reviews'][0]['uncertain']=True
        self.assertEqual(summarize(self.packet,self.editor,audit)['routes'],{'hold':1})
    def test_changed_reference_rejected(self):
        self.editor['reviews'][0]['body_sha256']='changed'
        with self.assertRaises(ValueError):summarize(self.packet,self.editor)
    def test_missing_review_rejected(self):
        with self.assertRaises(ValueError):verified_reviews(self.packet,{'reviews':[]},[0])

if __name__=='__main__':unittest.main()
