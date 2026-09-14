#!/usr/bin/env python3
"""皇室典範の確認用入力を、外付けの非公開領域から復元する。公開昇格はしない。"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import yaml

ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=ROOT/'quality/candidates/koshitsu-tenpakai'
TOPIC='koshitsu-tenpakai'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def restore(private_dir: Path, stage: Path):
    private_dir=private_dir.resolve();stage=stage.resolve()
    if stage==ROOT or stage.is_relative_to(ROOT) or stage==private_dir:
        raise ValueError('復元先にはリポジトリ外の専用ディレクトリが必要です')
    manifest=json.loads((CANDIDATE/'manifest.json').read_text())
    if digest(private_dir/'candidate.private.json')!=manifest['private_candidate_sha256']:
        raise ValueError('非公開候補の版が保存時と一致しません')
    for relative,expected in manifest['inputs'].items():
        if digest(CANDIDATE/relative)!=expected:raise ValueError('候補入力の変更: '+relative)
    stage.mkdir(parents=True,exist_ok=True)
    # Never follow an existing directory symlink during copy/write operations.
    for name in ('scripts','configs','data','schemas'):
        if (stage/name).is_symlink():raise ValueError('復元先に書込み用シンボリックリンクがあります: '+name)
        shutil.copytree(ROOT/name,stage/name,dirs_exist_ok=True)
    for name in ('docs','quality','social-samples'):
        target=stage/name
        if not target.exists():target.symlink_to(ROOT/name,target_is_directory=True)
    shutil.copytree(CANDIDATE/'inputs',stage,dirs_exist_ok=True)
    taxonomy=json.loads((stage/'configs/public-data-taxonomy.json').read_text())
    taxonomy['themes'][TOPIC]=json.loads((CANDIDATE/'taxonomy.json').read_text())
    (stage/'configs/public-data-taxonomy.json').write_text(json.dumps(taxonomy,ensure_ascii=False,indent=2)+'\n')
    themes=yaml.safe_load((ROOT/'THEMES.yaml').read_text())
    themes['themes'][TOPIC]['sample_file']=str(private_dir/'candidate.private.json')
    (stage/'THEMES.yaml').write_text(yaml.safe_dump(themes,allow_unicode=True,sort_keys=False))
    # IDs are retained only in this private restore. The safe claim ledger is committed.
    claim_path=private_dir/'claim-posts.private.json'
    private_claims=json.loads(claim_path.read_text())
    anonymous=[{'claim':key,'record_id_hash':'sha256:'+hashlib.sha256(('tweet:'+str(tid)).encode()).hexdigest()} for key,ids in private_claims.items() for tid in ids]
    safe_claims=json.loads((stage/'data/verification/koshitsu-tenpakai-claims.json').read_text())
    if sorted(anonymous,key=str)!=sorted(safe_claims,key=str):raise ValueError('非公開の主張対応表が保存済み台帳と一致しません')
    shutil.copy(claim_path,stage/'data/koshitsu-tenpakai_claim_posts.json')
    print('候補入力の復元完了:',stage)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--private-dir',type=Path,required=True);p.add_argument('--stage-root',type=Path,required=True)
    a=p.parse_args();restore(a.private_dir,a.stage_root)
if __name__=='__main__':main()
