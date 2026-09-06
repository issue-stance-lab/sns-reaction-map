import copy
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from scripts.verify_data_asset_restore import restore
from scripts import verify_data_assets as verifier
from scripts.data_asset_inventory import sha,ROOT,OUT

class RestoreSafetyTests(unittest.TestCase):
    def test_restore_parent_link_is_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);dest=root/'clone';dest.mkdir();outside=root/'outside';outside.mkdir()
            (dest/'linked').symlink_to(outside,target_is_directory=True)
            payload=b'[]';digest=__import__('hashlib').sha256(payload).hexdigest()
            rows=[{'path':p,'sha256':digest,'bytes':2,'records':0} for p in ['safe.json','linked/new.json']]
            archive=root/'backup.tar.gz'
            with tarfile.open(archive,'w:gz') as tar:
                contents={'manifest.json':json.dumps({'files':rows}).encode(),**{r['path']:payload for r in rows}}
                for name,body in contents.items():
                    info=tarfile.TarInfo(name);info.size=len(body);tar.addfile(info,io.BytesIO(body))
            receipt={'archive_sha256':sha(archive),'files':rows}
            with self.assertRaisesRegex(ValueError,'リンク'):restore(archive,receipt,dest)
            self.assertFalse((dest/'safe.json').exists())
            self.assertEqual(list(outside.iterdir()),[])

    def test_persona_cannot_be_removed_from_inventory(self):
        original=verifier.read
        mutated=copy.deepcopy(original(ROOT/OUT))
        mutated['files']=[r for r in mutated['files'] if r['path']!='configs/persona.private.json']
        mutated['summary']['private_backup']-=1
        def reader(path):return mutated if path==ROOT/OUT else original(path)
        with patch.object(verifier,'read',side_effect=reader):
            with self.assertRaisesRegex(ValueError,'ペルソナ'):verifier.verify(ROOT)

if __name__=='__main__':unittest.main()
