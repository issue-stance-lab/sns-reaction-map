import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from admin_dashboard import data_restore

class RestoreCardTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name);(self.root/'company').mkdir()
        self.today=dt.date(2026,9,6)
        self.inventory={'files':[{'path':'original','sha256':'a'*64}]}
        self.record={'schema_version':1,'verified_at':'2026-09-06T00:00:00Z','git_commit':'b'*40,
                     'method':'same_machine_clean_git_clone_and_two_archives','physical_other_machine':False,
                     'asset_content_sha256':hashlib.sha256(json.dumps(self.inventory['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                     'private_archive_sha256':'c'*64,'external_archive_sha256':'d'*64,
                     'checks':[{'check':c,'passed':True} for c in sorted(data_restore.REQUIRED_CHECKS)],
                     'restore_and_rebuild_verified':True}
        self.write('data-assets.json',self.inventory)
        for name,digest in [('data-backup-status.json','c'*64),('data-evidence-backup-status.json','d'*64)]:
            self.write(name,{'archive_sha256':digest,'restore_verified':True})
    def write(self,name,obj):
        (self.root/'company'/name).write_text(json.dumps(obj))
    def collect(self):
        self.write('data-restore-status.json',self.record)
        return data_restore.collect(self.today,self.root)
    def test_missing_is_unknown(self):
        self.assertIn('未確認',data_restore.collect(self.today,self.root)['status'])
    def test_success_and_other_machine_limit(self):
        self.assertEqual(self.collect()['checks'],6)
        self.assertIn('別マシンでの復元は未実施',data_restore.render_card(self.today,self.root))
    def test_changed_inventory_is_not_success(self):
        self.inventory['files'].append({'path':'new'})
        self.write('data-assets.json',self.inventory)
        self.assertIn('検査失敗',self.collect()['status'])
    def test_failed_check_is_not_success(self):
        self.record['checks'][0]['passed']=False
        self.assertIn('検査失敗',self.collect()['status'])
    def test_stale_and_future_are_marked(self):
        self.record['verified_at']='2026-08-01T00:00:00Z'
        self.assertIn('7日超',self.collect()['status'])
        self.record['verified_at']='2026-09-07T00:00:00Z'
        self.assertIn('未来',self.collect()['status'])
    def test_changed_archive_is_not_success(self):
        self.record['private_archive_sha256']='e'*64
        self.assertIn('検査失敗',self.collect()['status'])

if __name__ == '__main__': unittest.main()
