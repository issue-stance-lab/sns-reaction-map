import unittest
from scripts.prepare_next_editorial_batch import select_batch

class NextBatchTests(unittest.TestCase):
    def row(self,n,body=None,classification='v1'):
        return {'record_id_hash':str(n),'body_sha256':body or str(n),'classification_sha256':classification}
    def test_attempted_and_same_input_different_id_not_resent(self):
        old=dict(self.row(1),topic='a')
        rows=select_batch({'a':[self.row(1),self.row(9,body='1'),self.row(2)]},[old])
        self.assertEqual([r['record_id_hash'] for r in rows],['2'])
    def test_same_body_different_classification_is_new_work(self):
        rows=select_batch({'a':[self.row(1,classification='v2')]},[dict(self.row(1),topic='a')])
        self.assertEqual(len(rows),1)
    def test_topic_boundary_preserved(self):
        rows=select_batch({'b':[self.row(1)]},[dict(self.row(1),topic='a')])
        self.assertEqual(len(rows),1)
    def test_hard_cap_and_deterministic_selection(self):
        q={'a':[self.row(i) for i in range(30)],'b':[self.row(i) for i in range(30)]}
        self.assertEqual(select_batch(q,[]),select_batch(q,[]))
        self.assertEqual(len(select_batch(q,[])),20)
        with self.assertRaises(ValueError):select_batch(q,[],21)
    def test_reserved_packet_excluded_next_time(self):
        q={'a':[self.row(i) for i in range(30)]};first=select_batch(q,[])
        second=select_batch(q,first)
        self.assertEqual(len(second),10)
        self.assertFalse({r['record_id_hash'] for r in first}&{r['record_id_hash'] for r in second})

if __name__=='__main__':unittest.main()
