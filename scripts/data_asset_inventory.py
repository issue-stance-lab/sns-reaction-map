#!/usr/bin/env python3
"""Xデータの保存境界とバックアップの内容一致を本文なしで確認する。"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import yaml

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=Path('/Volumes/HD-LE-B/issue-stance-private-backups/data-repairs')
OUT='company/data-assets.json'
PRIVATE_RECEIPT='company/data-backup-status.json'
EXTERNAL_RECEIPT='company/data-evidence-backup-status.json'


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def git_paths(root,*args):
    return set(filter(None,subprocess.check_output(['git','ls-files','-z',*args],cwd=root).decode().split('\0')))
def safe_path(path):
    p=Path(path)
    if not path or p.is_absolute() or '..' in p.parts or '\\' in path or ':' in path or str(p)!=path:raise ValueError('不正な資産パス')
    return path


def contained_file(root,path):
    safe_path(path);p=root/path
    if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):
        raise ValueError('資産の欠落または保管境界外のリンク: '+path)
    return p


def external_requirements(root):
    """段階Dが現に参照する根拠の和集合。参照されない資料は削除せず対象外。"""
    seed=read(root/'data/verification/adoption/decision-evidence.json')
    requirements=dict(seed['evidence_sources'])
    registry=read(root/'data/verification/adoption/registry.json')
    for topic in registry['topics'].values():
        for source in topic['sources']:
            if source.get('external'):
                path=source['file'];digest=source['sha256']
                if path in requirements and requirements[path]!=digest:raise ValueError('外付け根拠の参照指紋が競合')
                requirements[path]=digest
    for path in requirements:safe_path(path)
    return requirements


def coverage(files, receipt_path):
    if not receipt_path.is_file():return {'status':'missing','missing':[r['path'] for r in files],'changed':[]}
    receipt=read(receipt_path)
    if receipt.get('restore_verified') is not True:raise ValueError('復元成功のないバックアップ記録')
    saved={r['path']:r for r in receipt['files']}
    if len(saved)!=len(receipt['files']):raise ValueError('バックアップ記録に重複')
    missing=[r['path'] for r in files if r['path'] not in saved]
    changed=[r['path'] for r in files if r['path'] in saved and
             (r['sha256']!=saved[r['path']]['sha256'] or r['bytes']!=saved[r['path']]['bytes'])]
    return {'status':'stale' if missing or changed else 'verified','missing':missing,'changed':changed}


def build(root=ROOT,evidence_root=EVIDENCE,snapshot_at=None):
    root=Path(root);evidence_root=Path(evidence_root)
    tracked=git_paths(root)
    changed=subprocess.run(['git','diff','--quiet','HEAD','--','social-samples'],cwd=root)
    if changed.returncode:raise ValueError('Git保管のXデータに未コミット変更があります')
    ignored=git_paths(root,'--others','--ignored','--exclude-standard','--','social-samples')
    untracked=git_paths(root,'--others','--exclude-standard','--','social-samples')
    if untracked:raise ValueError('保管先が未定の未追跡Xデータがあります: '+', '.join(sorted(untracked)))
    themes=yaml.safe_load((root/'THEMES.yaml').read_text())['themes']
    canonical={t:d['sample_file'] for t,d in themes.items()}
    paths={p for p in tracked if p.startswith('social-samples/')}|ignored|set(canonical.values())|{'configs/persona.private.json'}
    files=[]
    for path in sorted(paths):
        p=contained_file(root,path)
        roles=['canonical'] if path in canonical.values() else ['saved_update' if path.startswith('social-samples/updates/') else 'legacy_or_support']
        if path=='configs/persona.private.json':roles=['private_persona']
        files.append({'path':path,'storage':'git' if path in tracked else 'private_backup','sha256':sha(p),'bytes':p.stat().st_size,'roles':roles})
    for path,expected in sorted(external_requirements(root).items()):
        p=contained_file(evidence_root,path)
        if sha(p)!=expected:raise ValueError('外付け根拠の欠落または不一致: '+path)
        files.append({'path':path,'storage':'external_evidence','sha256':expected,'bytes':p.stat().st_size,'roles':['adoption_evidence']})
    bypath={r['path']:r for r in files}
    return {'schema_version':1,'snapshot_at':snapshot_at or datetime.now(timezone.utc).isoformat(),
            'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
            'scope':'all_social_samples_plus_persona_and_active_adoption_evidence',
            'files':files,'summary':dict(Counter(r['storage'] for r in files)),
            'canonical':{t:{'path':p,'storage':bypath[p]['storage']} for t,p in canonical.items()},
            'backup':{'private':coverage([r for r in files if r['storage']=='private_backup'],root/PRIVATE_RECEIPT),
                      'external':coverage([r for r in files if r['storage']=='external_evidence'],root/EXTERNAL_RECEIPT)}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-root',type=Path,default=EVIDENCE)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    old=read(ROOT/OUT) if (ROOT/OUT).is_file() else None
    data=build(evidence_root=args.evidence_root,snapshot_at=(old or {}).get('snapshot_at'))
    if args.check:
        if old is None:raise SystemExit('NG 資産台帳が未作成')
        # Git commit points to the observed checkout; ordinary later code commits do not stale data.
        comparable=dict(data);comparable['git_commit']=old['git_commit']
        if comparable!=old:raise SystemExit('NG 資産台帳と現在の入力・保全に差分があります')
    else:(ROOT/OUT).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print('OK 資産一覧',data['summary'],'保全', {k:v['status'] for k,v in data['backup'].items()})
    if any(v['status']!='verified' for v in data['backup'].values()):raise SystemExit(1)

if __name__=='__main__':main()
