import json
from pathlib import Path
import sys
import tempfile
import unittest
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import manage_reread_registry as manager
import verify_reread_registry as verifier

class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rows = [{'tweet_id':'1','text':'原投稿だけにあるテスト本文XYZ','classification':{'main_issue':'論点','is_opinion':True}}]
        self.source = {'read_at':'2026-08-24 / 2026-09-06', 'buckets':{'A':{'label':'内容','count':1}},
                       'items':[{'tweet_id':'1','bucket':'A'}]}
        self.save('canonical.json', self.rows)
        (self.root/'THEMES.yaml').write_text(yaml.safe_dump({'themes':{'t':{'sample_file':'canonical.json'}}}))
        self.save('data/old.json',self.source)
        path=self.root/'configs/planet/t.yaml';path.parent.mkdir(parents=True)
        path.write_text(yaml.safe_dump({'sub_issues':{'論点':{'file':'data/old.json','path':['buckets']}}}))

    def save(self,name,value):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False))

    def initialize(self):
        return manager.initialize(self.root,'t','2026-09-06T12:00:00+00:00')

    def test_migration_does_not_invent_historical_evidence(self):
        m=self.initialize();r=m['records'][0]['review']
        self.assertEqual(r['evidence_quality'],'legacy')
        self.assertEqual(r['reviewer_type'],'unspecified_editorial')
        self.assertIsNone(r['read_at']);self.assertIsNone(r['text_sha256'])
        self.assertEqual(m['source_date_labels']['data/old.json'],self.source['read_at'])
        self.assertNotIn('原投稿だけにあるテスト本文XYZ',json.dumps(m,ensure_ascii=False))
        self.assertNotIn('tweet_id',json.dumps(m))

    def test_automated_evidence_rejected(self):
        self.source['items'][0]['body_reviewed']=False;self.save('data/old.json',self.source)
        with self.assertRaises(ValueError):self.initialize()

    def test_wrong_issue_rejected(self):
        self.rows[0]['classification']['main_issue']='違う';self.save('canonical.json',self.rows)
        with self.assertRaises(ValueError):self.initialize()

    def test_duplicate_review_rejected(self):
        self.source['items']*=2;self.save('data/old.json',self.source)
        with self.assertRaises(ValueError):self.initialize()

    def test_required_registry_cannot_be_silently_removed(self):
        config=self.root/'configs/planet/t.yaml'
        data=yaml.safe_load(config.read_text());data['reread_registry']=True
        config.write_text(yaml.safe_dump(data))
        self.assertTrue(verifier.check(self.root))
        manager.write(manager.registry_path(self.root,'t'),self.initialize())
        self.assertEqual(verifier.check(self.root),[])

    def test_source_change_and_overwrite_are_not_silent(self):
        m=self.initialize();manager.check_sources(self.root,m)
        self.source['items'][0]['bucket']='B';self.save('data/old.json',self.source)
        with self.assertRaises(ValueError):manager.check_sources(self.root,m)
        out=self.root/'manifest.json';manager.write(out,m)
        with self.assertRaises(ValueError):manager.write(out,m)

if __name__=='__main__':unittest.main()
