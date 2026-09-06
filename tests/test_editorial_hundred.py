import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from scripts.verify_editorial_hundred import collect

class HundredTests(unittest.TestCase):
    def make_run(self,root,duplicate=False):
        proofs={}
        for b in range(1,6):
            d=root/f'batch-{b:02d}';d.mkdir();records=[];reviews=[]
            for i in range(20):
                n=(b-1)*20+i
                if duplicate and b==2 and i==0:n=0
                c={'is_relevant':True,'is_opinion':True,'main_issue':'a','stance':'n'}
                r={'topic':'t','record_id_hash':f'id{n}','body_sha256':f'body{n}','classification_sha256':'class','classification':c}
                records.append(r);reviews.append({'index':i,**{k:r[k] for k in ['record_id_hash','body_sha256','classification_sha256']},'classification':c,'uncertain':False,'reason':'検査用'})
            packet={'records':records,'criteria':{'t':{'issues':['a'],'stances':['n']}}}
            p=d/'packet.private.json';p.write_text(json.dumps(packet));proofs[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
            (d/'editor.private.json').write_text(json.dumps({'reviews':reviews}))
            (d/'audit.private.json').write_text(json.dumps({'reviews':copy.deepcopy(reviews[:2])}))
        (root/'reservation.json').write_text(json.dumps({'packet_hashes':proofs}))
    def test_exact_100_and_no_automatic_application(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.make_run(root);result,sources=collect(root)
            self.assertEqual(result['routes'],{'retain_candidate':100});self.assertEqual(len(sources),100)
            self.assertEqual(result['canonical_changes'],0)
    def test_packet_tamper_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.make_run(root);p=root/'batch-01/packet.private.json';p.write_text(p.read_text()+' ')
            with self.assertRaisesRegex(ValueError,'packet changed'):collect(root)
    def test_repeated_input_across_batches_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.make_run(root,True)
            with self.assertRaisesRegex(ValueError,'duplicate review input'):collect(root)
    def test_missing_audit_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.make_run(root);(root/'batch-05/audit.private.json').unlink()
            with self.assertRaises(FileNotFoundError):collect(root)

if __name__=='__main__':unittest.main()
