#!/usr/bin/env python3
"""Git＋2種の保全アーカイブだけを新しいフォルダに復元し、再生成を検査する。"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
try:
    from . import backup_private_data as backup
    from .data_asset_inventory import ROOT,OUT,PRIVATE_RECEIPT,EXTERNAL_RECEIPT,sha,read
except ImportError:
    import backup_private_data as backup
    from data_asset_inventory import ROOT,OUT,PRIVATE_RECEIPT,EXTERNAL_RECEIPT,sha,read


def content_hash(inventory):
    return hashlib.sha256(json.dumps(inventory['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()


def restore(archive,receipt,dest):
    if sha(archive)!=receipt['archive_sha256'] or backup.verify(archive,quiet=True):
        raise ValueError('アーカイブが復元成功記録と一致しません')
    with tarfile.open(archive,'r:gz') as tar:
        manifest,members=backup.validated_manifest(tar)
        expected={r['path']:(r['sha256'],r['bytes'],r['records']) for r in receipt['files']}
        actual={r['path']:(r['sha256'],r['bytes'],r['records']) for r in manifest['files']}
        if actual!=expected:raise ValueError('復元するファイルの範囲が記録と不一致')
        for path in expected:
            target=dest/path
            if target.exists():raise ValueError('復元先に同名ファイルがあります')
            target.parent.mkdir(parents=True,exist_ok=True)
            with tar.extractfile(members[path]) as source:target.write_bytes(source.read())


def run(root,backup_root,report):
    root=Path(root);backup_root=Path(backup_root)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    private=read(root/PRIVATE_RECEIPT);external=read(root/EXTERNAL_RECEIPT);inventory=read(root/OUT)
    results=[]
    with tempfile.TemporaryDirectory(prefix='isa-assets-restore-') as tmp:
        tmp=Path(tmp);checkout=tmp/'repo';evidence=tmp/'evidence';evidence.mkdir()
        subprocess.run(['git','clone','--quiet','--no-hardlinks',str(root),str(checkout)],check=True)
        subprocess.run(['git','checkout','--quiet','--detach',commit],cwd=checkout,check=True)
        # Clone must provide exactly the receipts being tested; uncommitted proof is not portable.
        for path in [PRIVATE_RECEIPT,EXTERNAL_RECEIPT,OUT]:
            if (root/path).read_bytes()!=(checkout/path).read_bytes():raise ValueError('復元記録を先にコミットしてください')
        restore(backup_root/private['archive_name'],private,checkout)
        restore(backup_root/external['archive_name'],external,evidence)
        commands=[['scripts/data_asset_inventory.py','--check','--evidence-root',str(evidence)],
                  ['scripts/build_adoption_registry.py','--check','--evidence-root',str(evidence)],
                  ['scripts/verify_public_registry.py','--against-private'],
                  ['scripts/verify_reread_registry.py'],
                  ['scripts/verify_builder_rebuildability.py'],
                  ['scripts/verify_data_assets.py']]
        for args in commands:
            p=subprocess.run([sys.executable,*args],cwd=checkout,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            label=args[0]
            if p.returncode:
                print(p.stdout[-3000:]);raise ValueError('復元後の検査失敗: '+label)
            print('OK 復元後:',label,flush=True);results.append({'check':label,'passed':True})
    result={'schema_version':1,'verified_at':datetime.now(timezone.utc).isoformat(),'git_commit':commit,
            'method':'same_machine_clean_git_clone_and_two_archives','physical_other_machine':False,
            'asset_content_sha256':content_hash(inventory),'private_archive_sha256':private['archive_sha256'],
            'external_archive_sha256':external['archive_sha256'],'checks':results,'restore_and_rebuild_verified':True}
    Path(report).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--backup-root',type=Path,required=True)
    args=p.parse_args();run(ROOT,args.backup_root,ROOT/'company/data-restore-status.json')
    print('OK Git＋原本＋採否根拠からの復元・再生成（同じマシン）')
