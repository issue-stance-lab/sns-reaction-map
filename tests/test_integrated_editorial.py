import unittest
from scripts.verify_integrated_editorial_candidates import validate_integrated

class IntegratedEditorialTests(unittest.TestCase):
    def rows(self):
        routes=['retain_candidate']*69+['change_candidate']*16+['hold']*55
        return [{'topic':'t','record_id_hash':str(i),'route':route,'independently_checked':route=='change_candidate'} for i,route in enumerate(routes)]
    def test_expected_partition(self):
        self.assertEqual(validate_integrated(self.rows()),{'retain_candidate':69,'change_candidate':16,'hold':55})
    def test_duplicate_record_cannot_be_counted_twice(self):
        rows=self.rows();rows[1]['record_id_hash']=rows[0]['record_id_hash']
        with self.assertRaises(ValueError):validate_integrated(rows)
    def test_unsupported_correction_stops(self):
        rows=self.rows();rows[70]['independently_checked']='false'
        with self.assertRaisesRegex(ValueError,'unsupported'):validate_integrated(rows)
    def test_hold_not_silently_promoted(self):
        rows=self.rows();rows[-1]['route']='change_candidate';rows[-1]['independently_checked']=True
        with self.assertRaises(ValueError):validate_integrated(rows)

if __name__=='__main__':unittest.main()
