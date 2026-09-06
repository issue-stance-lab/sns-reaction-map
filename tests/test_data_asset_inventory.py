import json
from pathlib import Path
import tempfile
import unittest
from scripts.data_asset_inventory import coverage,safe_path
from scripts.verify_data_assets import validate_receipt
from scripts import backup_adoption_evidence as bundle
from unittest.mock import patch

class DataAssetsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.row={'path':'saved.json','sha256':'a'*64,'bytes':4}

    def test_missing_and_changed_backup_not_green(self):
        path=self.root/'receipt.json'
        self.assertEqual(coverage([self.row],path)['status'],'missing')
        path.write_text(json.dumps({'restore_verified':True,'files':[dict(self.row,sha256='b'*64)]}))
        self.assertEqual(coverage([self.row],path)['status'],'stale')
        path.write_text(json.dumps({'restore_verified':True,'files':[self.row]}))
        self.assertEqual(coverage([self.row],path)['status'],'verified')

    def test_new_file_requires_new_backup(self):
        path=self.root/'receipt.json';path.write_text(json.dumps({'restore_verified':True,'files':[self.row]}))
        result=coverage([self.row,dict(self.row,path='new.json')],path)
        self.assertEqual(result['missing'],['new.json']);self.assertEqual(result['status'],'stale')

    def test_unverified_receipt_is_rejected(self):
        path=self.root/'receipt.json';path.write_text(json.dumps({'restore_verified':False,'files':[self.row]}))
        with self.assertRaises(ValueError):coverage([self.row],path)

    def test_no_receipt_raw_fields(self):
        receipt={'schema_version':1,'verified_at':'2026-09-06T00:00:00+00:00','git_commit':'a'*40,
          'archive_name':'safe.tar.gz','archive_sha256':'b'*64,'file_count':1,'total_bytes':4,
          'files':[dict(self.row,records=None)],'restore_verified':True}
        validate_receipt(receipt)
        receipt['files'][0]['text']='private'
        with self.assertRaises(ValueError):validate_receipt(receipt)

    def test_external_mismatch_preserves_previous_receipt(self):
        root=self.root/'repo';root.mkdir();evidence=self.root/'evidence';evidence.mkdir()
        (evidence/'saved.json').write_text('new data')
        receipt=root/'receipt.json';receipt.write_text('previous')
        with patch.object(bundle,'external_requirements',return_value={'saved.json':'a'*64}):
            with self.assertRaises(ValueError):bundle.bundle(root,evidence,self.root/'archive',receipt)
        self.assertEqual(receipt.read_text(),'previous');self.assertFalse((self.root/'archive').exists())

    def test_paths_cannot_escape(self):
        for p in ['../outside','/private/file','a\\b']:
            with self.assertRaises(ValueError):safe_path(p)

if __name__=='__main__':unittest.main()
