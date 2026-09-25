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


class ResyncSourceTests(unittest.TestCase):
    """継承元ファイルには post_key を直接持つ形式（henoko等）と tweet_id しか
    持たない形式（bukatsu-chiiki等）の2種類がある。resync-source はどちらでも
    投稿を照合できなければならない（post_key は一方向ハッシュのため、
    tweet_id 側からしか導出できない）。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rows = [{'tweet_id': '1', 'text': '本文', 'classification': {'main_issue': '論点', 'is_opinion': True}}]
        self.save('canonical.json', self.rows)
        (self.root / 'THEMES.yaml').write_text(yaml.safe_dump({'themes': {'t': {'sample_file': 'canonical.json'}}}))

    def save(self, name, value):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value, ensure_ascii=False))

    def config(self, source_file, path=('buckets',)):
        p = self.root / 'configs/planet/t.yaml'
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(yaml.safe_dump({'sub_issues': {'論点': {'file': source_file, 'path': list(path)}}}))

    def config_shared(self, source_file):
        """henoko等の実データと同じ形: 複数の論点が同じファイル・同じ items 配列を、
        item_issue_field（main_issue）で絞り込みながら共有する。"""
        p = self.root / 'configs/planet/t.yaml'
        p.parent.mkdir(parents=True, exist_ok=True)
        spec = {'file': source_file, 'items_path': ['items'], 'item_issue_field': 'main_issue'}
        p.write_text(yaml.safe_dump({'sub_issues': {
            '論点': {**spec, 'path': ['buckets', '論点']},
            '別論点': {**spec, 'path': ['buckets', '別論点']},
        }}))

    def record_one(self, bucket):
        manifest = manager.initialize(self.root, 't', '2026-09-06T12:00:00+00:00')
        pk = manager.key('1')
        target = manager.create_target(manifest, [pk])
        review = {
            'kind': 'editorial_body_reread', 'evidence_quality': 'verified',
            'read_at': '2026-09-24T00:00:00+00:00', 'reviewer_type': 'human', 'reviewer': 'tester',
            'method_version': 'v1', 'text_sha256': target['records'][0]['baseline_text_sha256'],
            'reason_sha256': manager.hashlib.sha256(b'reason').hexdigest(),
            'source_file': 'quality/reviews/test.json',
            'source_sha256': manager.hashlib.sha256(b'{}').hexdigest(), 'bucket': bucket,
        }
        return manager.record_reviews(manifest, target, [{'post_key': pk, 'review': review}]), pk

    def test_resync_accepts_post_key_only_source_items(self):
        manifest, pk = self.record_one('A')
        self.config('data/postkey.json')
        self.save('data/postkey.json', {'buckets': {'A': {'label': '内容', 'count': 1}},
                                         'items': [{'post_key': pk, 'bucket': 'A', 'main_issue': '論点'}]})
        result = manager.resync_source(self.root, 't', manifest, 'data/postkey.json')
        self.assertEqual(result['sources']['data/postkey.json'],
                          manager.digest(self.root / 'data/postkey.json'))

    def test_resync_still_accepts_tweet_id_only_source_items(self):
        manifest, _pk = self.record_one('A')
        self.config('data/tweetid.json')
        self.save('data/tweetid.json', {'buckets': {'A': {'label': '内容', 'count': 1}},
                                         'items': [{'tweet_id': '1', 'bucket': 'A', 'main_issue': '論点'}]})
        result = manager.resync_source(self.root, 't', manifest, 'data/tweetid.json')
        self.assertEqual(result['sources']['data/tweetid.json'],
                          manager.digest(self.root / 'data/tweetid.json'))

    def test_resync_rejects_post_key_mismatch(self):
        manifest, pk = self.record_one('A')
        self.config('data/postkey.json')
        self.save('data/postkey.json', {'buckets': {'A': {'label': '内容', 'count': 1}},
                                         'items': [{'post_key': pk, 'bucket': 'B', 'main_issue': '論点'}]})
        with self.assertRaises(ValueError):
            manager.resync_source(self.root, 't', manifest, 'data/postkey.json')

    def test_resync_filters_shared_items_by_issue_before_matching(self):
        """henokoの実データと同型: 2つの論点が同じ items 配列を共有する場合、
        item_issue_field で絞り込まずに突き合わせると、他の論点の投稿まで
        「一致しない」と誤検知していた（修正前に実データで再現したバグ）。"""
        self.rows = [
            {'tweet_id': '1', 'text': '本文1', 'classification': {'main_issue': '論点', 'is_opinion': True}},
            {'tweet_id': '2', 'text': '本文2', 'classification': {'main_issue': '別論点', 'is_opinion': True}},
        ]
        self.save('canonical.json', self.rows)
        manifest = manager.initialize(self.root, 't', '2026-09-06T12:00:00+00:00')
        pk1, pk2 = manager.key('1'), manager.key('2')
        target = manager.create_target(manifest, [pk1, pk2])
        by_key = {r['post_key']: r for r in target['records']}

        def review_for(pk, bucket):
            return {'post_key': pk, 'review': {
                'kind': 'editorial_body_reread', 'evidence_quality': 'verified',
                'read_at': '2026-09-24T00:00:00+00:00', 'reviewer_type': 'human', 'reviewer': 'tester',
                'method_version': 'v1', 'text_sha256': by_key[pk]['baseline_text_sha256'],
                'reason_sha256': manager.hashlib.sha256(b'reason').hexdigest(),
                'source_file': 'quality/reviews/test.json',
                'source_sha256': manager.hashlib.sha256(b'{}').hexdigest(), 'bucket': bucket}}

        manifest = manager.record_reviews(manifest, target, [review_for(pk1, 'A'), review_for(pk2, 'X')])
        self.config_shared('data/shared.json')
        self.save('data/shared.json', {
            'buckets': {'論点': {'A': {'label': '内容A', 'count': 1}},
                        '別論点': {'X': {'label': '内容X', 'count': 1}}},
            'items': [
                {'post_key': pk1, 'bucket': 'A', 'main_issue': '論点'},
                {'post_key': pk2, 'bucket': 'X', 'main_issue': '別論点'},
            ],
        })
        result = manager.resync_source(self.root, 't', manifest, 'data/shared.json')
        self.assertEqual(result['sources']['data/shared.json'],
                          manager.digest(self.root / 'data/shared.json'))

    def test_initialize_accepts_post_key_only_legacy_source(self):
        self.config('data/postkey.json')
        pk = manager.key('1')
        self.save('data/postkey.json', {'read_at': '2026-08-01', 'buckets': {'A': {'label': '内容', 'count': 1}},
                                         'items': [{'post_key': pk, 'bucket': 'A', 'body_reviewed': True}]})
        manifest = manager.initialize(self.root, 't', '2026-09-06T12:00:00+00:00')
        self.assertEqual(manifest['records'][0]['review']['bucket'], 'A')
        self.assertEqual(manifest['records'][0]['review']['evidence_quality'], 'legacy')


if __name__=='__main__':unittest.main()
