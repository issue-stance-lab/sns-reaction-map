import json
from pathlib import Path
import tempfile
import unittest
from scripts.build_adoption_registry import (load_sources, validate_evidence,
    validate_public_membership, write_snapshot, digest)
from scripts.public_registry_common import source_sha256
from scripts.verification_data import make_verification_records


class AdoptionBuilderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'configs').mkdir()
        (self.root/'configs/adoption-sources.yaml').write_text('legacy: []\nexternal: []\n')
        self.rows = [{'tweet_id':'12345', 'text':'fixture', 'classification':{
            'is_opinion':True,'is_relevant':True,'main_issue':'issue','stance':'pro'}}]

    def put(self,path,value):
        p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(value));return p

    def test_missing_private_wave_stays_body_unavailable(self):
        self.put('data/verification/updates/topic/2026-09-01/classified.json',make_verification_records(self.rows))
        sources,metadata=load_sources(self.root,self.root/'external','topic')
        self.assertEqual(sources[0]['kind'],'verification')
        self.assertFalse(metadata[1]['body_available'])
        self.assertTrue(metadata[0]['missing'])

    def test_private_and_summary_disagreement_stops(self):
        self.put('social-samples/updates/topic/2026-09-01/classified.json',self.rows)
        safe=make_verification_records(self.rows)
        safe[0]['classification']['stance']='con'
        self.put('data/verification/updates/topic/2026-09-01/classified.json',safe)
        with self.assertRaisesRegex(ValueError,'一致しません'):
            load_sources(self.root,self.root/'external','topic')

    def test_private_only_wave_is_not_dropped(self):
        self.put('social-samples/updates/topic/2026-09-01/raw.json',self.rows)
        sources,metadata=load_sources(self.root,self.root/'external','topic')
        self.assertEqual(len(sources),1)
        self.assertEqual(sources[0]['kind'],'raw')
        self.assertTrue(metadata[1]['missing'])

    def test_public_count_change_with_same_source_hash_stops(self):
        public={'source_sha256':source_sha256(self.rows),'collected_count':1,'opinion_count':1}
        validate_public_membership('topic',self.rows,public)
        public['opinion_count']=0
        with self.assertRaisesRegex(ValueError,'母数'):
            validate_public_membership('topic',self.rows,public)

    def test_public_and_private_evidence_changes_stop(self):
        private=self.put('external/proof.json',{'old':'decision'})
        public=self.put('quality/proof.json',{'safe':'summary'})
        seed={'evidence_sources':{'proof.json':digest(private)},'decisions':{'topic':{'hash':{
            'evidence_file':'quality/proof.json','evidence_sha256':digest(public)}}}}
        validate_evidence(self.root,self.root/'external',seed)
        old=private.read_bytes();private.write_text('{}')
        with self.assertRaisesRegex(ValueError,'非公開'):
            validate_evidence(self.root,self.root/'external',seed)
        private.write_bytes(old);public.write_text('{}')
        with self.assertRaisesRegex(ValueError,'公開'):
            validate_evidence(self.root,self.root/'external',seed)

    def test_snapshot_atomic_roundtrip(self):
        value={'topics':{'topic':{'records':[{'record_id_hash':'sha256:example','decision':None}]}}}
        target=self.root/'out/report.json'
        write_snapshot(target,value)
        self.assertEqual(json.loads(target.read_text()),value)
        self.assertEqual(list(target.parent.iterdir()),[target])

if __name__=='__main__':unittest.main()
