import unittest
from scripts.prepare_resolved_review_cycle import select_ordinary
from scripts.editorial_work_registry import fingerprint


class ResolvedCycleTests(unittest.TestCase):
    def setUp(self):
        self.criteria={'topic':{'version':1}}
        self.rows=[{'topic':'topic','record_id_hash':str(i),'body_sha256':str(i),
                    'classification_sha256':'classification','criteria_sha256':fingerprint(self.criteria['topic']),
                    'input_job_key':str(i),'route':'new_body_review'} for i in range(5)]
        self.raw={('topic',r['record_id_hash']):dict(r) for r in self.rows}

    def select(self, used=(),count=2):
        return select_ordinary({'records':self.rows},self.raw,self.criteria,set(used),{'topic':count})

    def test_completed_or_reserved_ids_are_skipped(self):
        self.assertEqual([r['record_id_hash'] for r in self.select([('topic','0'),('topic','1')])],['2','3'])

    def test_special_routes_cannot_silently_enter_ordinary_cycle(self):
        self.rows[0]['route']='resume_unfinished_review'
        self.rows[1]['route']='verify_distinct_id_against_existing_review'
        self.assertEqual([r['record_id_hash'] for r in self.select()],['2','3'])
        with self.assertRaisesRegex(ValueError,'not enough'):self.select(count=4)

    def test_paused_topic_rejected(self):
        with self.assertRaisesRegex(ValueError,'paused'):
            select_ordinary({'records':[]},{},{},set(),{'koshitsu-tenpakai':1})

    def test_changed_input_and_criteria_are_rejected(self):
        self.raw[('topic','0')]['body_sha256']='different'
        with self.assertRaisesRegex(ValueError,'changed'):self.select()
        self.raw[('topic','0')]['body_sha256']='0'
        self.criteria['topic']['version']=2
        with self.assertRaisesRegex(ValueError,'changed'):self.select()

    def test_duplicate_input_cannot_receive_two_jobs(self):
        self.rows[1]['input_job_key']='0'
        with self.assertRaisesRegex(ValueError,'duplicate'):self.select()
