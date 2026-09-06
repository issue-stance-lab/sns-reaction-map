import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from admin_dashboard import data_assets, render

TODAY = dt.date(2026,9,6)

class AssetDashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'THEMES.yaml').write_text(yaml.safe_dump({'themes': {'a': {'title':'<script>sample</script>', 'published':'done'}, 'b':{'title':'非掲載', 'published':'hold'}}}))
    def write(self, name, obj):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj))
    def collect(self):
        return data_assets.collect_data_assets(TODAY,self.root)
    def test_missing_evidence_is_unknown_not_zero(self):
        result=self.collect()
        self.assertIsNone(result['themes'][0]['canonical'])
        self.assertEqual(result['themes'][0]['reread_status'],'共通台帳未管理')
        self.assertIn('検査失敗',result['adoption_status'])
        html=render.section_data_assets({'data_assets':result})
        self.assertNotIn('<script>sample',html)
        self.assertIn('&lt;script&gt;sample',html)
        self.assertIn('別マシンでの復元は未実施',html)
    @patch.object(data_assets, 'verify')
    def test_membership_statuses_and_stale_snapshot(self, _):
        record=lambda status: {'canonical_presence':status=='in_canonical','adoption_status':status}
        item={'canonical_file':'missing.json','canonical_sha256':'a'*64,'saved_unique_records':5,'records':[record(s) for s in ['in_canonical','pending_review','decision_unknown','unresolved','excluded_confirmed']]}
        self.write('data/verification/adoption/registry.json',{'snapshot_at':'2026-08-01T00:00:00Z','topics':{'a':item,'b':item}})
        result=self.collect();row=result['themes'][0]
        self.assertEqual([row[k] for k in ('canonical','pending','unknown','unresolved','excluded')],[1]*5)
        self.assertIn('7日超',result['adoption_status'])
        self.assertFalse(result['themes'][1]['published'])
    def test_failed_restore_and_overdue_operation(self):
        self.write('company/data-backup-status.json',{'schema_version':1,'restore_verified':False})
        p=self.root/'company/data-operations.yaml'
        p.write_text(yaml.safe_dump({'schema_version':1,'operations':[{'id':'a','title':'保全','owner':'担当AI','due_at':'2026-09-05','status':'pending','task':'課題63','next_action':'確認する'}]}))
        result=self.collect()
        self.assertIn('検査失敗',result['backup']['status'])
        self.assertTrue(result['operations'][0]['overdue'])
        self.assertIn('期限超過',render.section_data_assets({'data_assets':result}))
    def test_stale_receipt(self):
        self.write('company/data-backup-status.json',{'schema_version':1,'restore_verified':True,'verified_at':'2026-08-01T00:00:00Z','archive_name':'safe.tar.gz','archive_sha256':'a'*64,'git_commit':'b'*40,'file_count':1,'total_bytes':3,'files':[{'path':'safe','bytes':3,'sha256':'c'*64}]})
        self.assertIn('7日超',self.collect()['backup']['status'])
    def test_inventory_coverage_failure_visible(self):
        self.write('company/data-assets.json',{'schema_version':1,'snapshot_at':'2026-09-06T00:00:00Z','files':[{'storage':'private_backup'}],'summary':{'git':0,'private_backup':1,'external_evidence':0},'backup':{'private':{'status':'missing','missing':['original.json'],'changed':[]}}})
        html=render.section_data_assets({'data_assets':self.collect()})
        self.assertIn('欠落あり',html)
        self.assertNotIn('original.json',html)

if __name__ == '__main__': unittest.main()
