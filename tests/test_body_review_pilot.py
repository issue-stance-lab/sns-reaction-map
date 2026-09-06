import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import run_body_review_pilot as runner

class ReviewPilotTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{'classification':{'is_relevant':True,'is_opinion':True,'main_issue':'issue','stance':'neutral'}}]
        self.criteria={'issues':['issue','other'],'stances':['neutral','pro']}
        self.valid={'id':0,'status':'ok','fields':[],'suggested':{},'reason':'明確な修正理由なし'}
    def test_invalid_label_cannot_pass(self):
        item=dict(self.valid,status='candidate',fields=['main_issue'],suggested={'main_issue':'invented'})
        with self.assertRaisesRegex(ValueError,'invalid issue'):runner.validate([item],self.rows,self.criteria)
    def test_duplicate_and_missing_results_stop(self):
        with self.assertRaises(ValueError):runner.validate([self.valid,self.valid],self.rows,self.criteria)
        with self.assertRaises(ValueError):runner.validate([],self.rows,self.criteria)
    def test_ok_cannot_hide_suggestion(self):
        item=dict(self.valid,fields=['stance'],suggested={'stance':'pro'})
        with self.assertRaisesRegex(ValueError,'disagreement'):runner.validate([item],self.rows,self.criteria)
    def test_no_change_is_not_a_correction(self):
        item=dict(self.valid,status='candidate',fields=['stance'],suggested={'stance':'neutral'})
        with self.assertRaisesRegex(ValueError,'nothing'):runner.validate([item],self.rows,self.criteria)
    def test_string_boolean_rejected(self):
        item=dict(self.valid,status='candidate',fields=['is_opinion'],suggested={'is_opinion':'false'})
        with self.assertRaisesRegex(ValueError,'boolean'):runner.validate([item],self.rows,self.criteria)
    def test_schema_bounds_to_theme(self):
        schema=runner.output_schema(self.criteria,9)
        self.assertEqual(schema['maxItems'],9)
        self.assertEqual(schema['items']['properties']['suggested']['properties']['main_issue']['enum'],['issue','other'])
    def test_bad_suggestion_routes_only_that_record_to_review(self):
        rows=[dict(self.rows[0],sample_id='a'),dict(self.rows[0],sample_id='b')]
        invalid=dict(self.valid,id=1,status='candidate',fields=['stance'],suggested={'stance':'neutral'})
        valid,errors=runner.decode(json.dumps([self.valid,invalid]),rows,self.criteria)
        self.assertEqual(len(valid),1)
        self.assertEqual(errors[0]['sample_id'],'b')
    def test_duplicate_batch_id_is_not_repaired(self):
        with self.assertRaisesRegex(ValueError,'IDs'):
            runner.decode(json.dumps([self.valid,self.valid]),self.rows*2,self.criteria)
    def test_pilot_without_smoke_gate_stops_before_model_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);records=[]
            (root/'pilot-input.json').write_text(json.dumps({'input_sha256':runner.fingerprint(records),'records':records,'criteria':{}}))
            with patch.object(runner,'request',return_value={'models':[{'name':runner.MODEL,'digest':'fixed'}]}) as request:
                with self.assertRaises(FileNotFoundError):runner.run(root,'pilot')
            self.assertEqual(request.call_count,1)
            self.assertEqual(request.call_args.args[0],'tags')

if __name__=='__main__':unittest.main()
