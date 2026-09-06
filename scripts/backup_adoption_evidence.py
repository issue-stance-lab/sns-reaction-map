#!/usr/bin/env python3
"""段階Dが参照する外付け原資料を、既存の復元検査で確かめた可搬アーカイブへ保存する。"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
try:
    from . import backup_private_data as backup
    from .data_asset_inventory import ROOT,EVIDENCE,EXTERNAL_RECEIPT,external_requirements,sha,contained_file
except ImportError:
    import backup_private_data as backup
    from data_asset_inventory import ROOT,EVIDENCE,EXTERNAL_RECEIPT,external_requirements,sha,contained_file


def bundle(root,evidence_root,dest,receipt):
    root=Path(root);evidence_root=Path(evidence_root);dest=Path(dest)
    if dest.resolve().is_relative_to(root.resolve()):raise ValueError('保存先はリポジトリ外にしてください')
    requirements=external_requirements(root)
    if not requirements:raise ValueError('根拠ファイルがありません')
    files=[]
    for path,expected in sorted(requirements.items()):
        p=contained_file(evidence_root,path)
        if sha(p)!=expected:raise ValueError('採否根拠の指紋不一致: '+path)
        files.append({'path':path,'bytes':p.stat().st_size,'sha256':expected,'records':backup.record_count(p)})
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    stamp=datetime.now(timezone.utc).isoformat()
    manifest={'created_at':stamp,'git_commit':commit,'files':files}
    dest.mkdir(parents=True,exist_ok=True)
    archive=dest/('adoption-evidence-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.tar.gz')
    with tempfile.TemporaryDirectory(dir=dest) as tmp:
        temporary=Path(tmp);mp=temporary/'manifest.json';mp.write_text(json.dumps(manifest))
        partial=temporary/'archive.tar.gz'
        with tarfile.open(partial,'w:gz') as tar:
            tar.add(mp,arcname='manifest.json')
            for row in files:tar.add(evidence_root/row['path'],arcname=row['path'],recursive=False)
        if backup.verify(partial,quiet=True):raise ValueError('根拠アーカイブの復元検査に失敗')
        partial.replace(archive)
    status={'schema_version':1,'verified_at':stamp,'git_commit':commit,'archive_name':archive.name,
            'archive_sha256':sha(archive),'file_count':len(files),'total_bytes':sum(r['bytes'] for r in files),
            'files':files,'restore_verified':True}
    receipt=Path(receipt);receipt.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',dir=receipt.parent,delete=False,encoding='utf-8') as out:
        out.write(json.dumps(status,ensure_ascii=False,indent=2)+'\n');temporary=Path(out.name)
    temporary.replace(receipt)
    return status


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence-root',type=Path,default=EVIDENCE)
    p.add_argument('--dest',type=Path,required=True);args=p.parse_args()
    result=bundle(ROOT,args.evidence_root,args.dest,ROOT/EXTERNAL_RECEIPT)
    print('OK 採否根拠の復元確認:',result['file_count'],'ファイル',result['archive_name'])

if __name__=='__main__':main()
