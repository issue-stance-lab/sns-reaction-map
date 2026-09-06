#!/usr/bin/env python3
"""保存回と正典・公開集計・採否根拠を照合する。追加・削除・再分類は行わない。"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import os
import tempfile
import yaml
try:
    from .adoption_registry import build_topic
    from .public_registry_common import is_opinion_record, source_sha256
    from .verification_data import record_id_hash, make_verification_records
except ImportError:
    from adoption_registry import build_topic
    from public_registry_common import is_opinion_record, source_sha256
    from verification_data import record_id_hash, make_verification_records

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=Path('/Volumes/HD-LE-B/issue-stance-private-backups/data-repairs')
OUTPUT='data/verification/adoption/registry.json'
DECISIONS='data/verification/adoption/decision-evidence.json'


def read(path):return json.loads(path.read_text())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_evidence(root,evidence_root,seed):
    for file,expected in seed.get('evidence_sources',{}).items():
        if digest(evidence_root/file)!=expected:
            raise ValueError(f'非公開の判断根拠が変わっています: {file}')
    checked=set()
    for decisions in seed.get('decisions',{}).values():
        for decision in decisions.values():
            pair=(decision['evidence_file'],decision['evidence_sha256'])
            if pair not in checked and digest(root/pair[0])!=pair[1]:
                raise ValueError(f'公開の判断根拠が変わっています: {pair[0]}')
            checked.add(pair)


def validate_public_membership(topic,rows,public):
    if public is None:return
    if public['source_sha256']!=source_sha256(rows):
        raise ValueError(f'{topic}: 公開データの原本版と現在正典が一致しません')
    if public['collected_count']!=len(rows) or public['opinion_count']!=sum(is_opinion_record(r) for r in rows):
        raise ValueError(f'{topic}: 公開集計の母数と現在正典が一致しません')


def write_snapshot(path, result):
    # One record per line keeps review diffs bounded without hiding individual records.
    def encode(value):
        if isinstance(value,dict) and 'record_id_hash' in value:
            return json.dumps(value,ensure_ascii=False,separators=(',', ':'))
        if isinstance(value,dict):
            return '{\n'+',\n'.join(json.dumps(k)+':'+encode(v) for k,v in value.items())+'\n}'
        if isinstance(value,list):return '[\n'+',\n'.join(encode(v) for v in value)+'\n]'
        return json.dumps(value,ensure_ascii=False)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd, temporary=tempfile.mkstemp(prefix=path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as out:out.write(encode(result)+'\n')
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)


def load_sources(root, evidence_root, topic):
    sources=[];metadata=[]
    def append(source_id,path,kind,*,external=False,items_key=None,verification=None,report=None):
        rows=read(path)
        if items_key:rows=rows[items_key]
        if not isinstance(rows,list):raise ValueError(f'保存回が配列ではありません: {source_id}')
        sources.append({'source_id':source_id,'kind':kind,'rows':rows})
        meta={'source_id':source_id,'file':str(path.relative_to(evidence_root if external else root)),
              'external':external,'sha256':digest(path),'kind':kind,'count':len(rows),
              'body_available':any(isinstance(r.get('text'),str) for r in rows)}
        if verification and verification.is_file():
            if make_verification_records(rows)!=read(verification):
                raise ValueError(f'保存回と検証用サマリが一致しません: {source_id}')
            meta['verification_file']=str(verification.relative_to(root));meta['verification_sha256']=digest(verification)
        if report and report.is_file():
            rep=read(report);meta['report_file']=str(report.relative_to(root));meta['report_sha256']=digest(report)
            meta['run_id']=rep.get('run_id');meta['saved_status']=rep.get('status')
        metadata.append(meta)
    private=root/'social-samples/updates'/topic;public=root/'data/verification/updates'/topic
    dates=sorted({p.name for base in (private,public) if base.exists() for p in base.iterdir() if p.is_dir()})
    for date in dates:
        for name in ('raw','classified'):
            original=private/date/(name+'.json');verification=public/date/(name+'.json')
            if original.is_file():
                append(f'updates/{topic}/{date}/{name}',original,'raw' if name=='raw' else 'classified',
                       verification=verification,report=private/date/'report.json')
            elif verification.is_file():
                append(f'updates/{topic}/{date}/{name}',verification,'verification',report=public/date/'report.json')
            else:
                # A half-saved update is visible, not silently omitted from the inventory.
                metadata.append({'source_id':f'updates/{topic}/{date}/{name}','missing':True})
    config=yaml.safe_load((root/'configs/adoption-sources.yaml').read_text())
    for section,base in [('legacy',root),('external',evidence_root)]:
        for entry in config.get(section,[]):
            if entry['topic']==topic:
                path=base/entry['path']
                append(f'{section}/{entry["path"]}',path,entry['kind'],external=section=='external',items_key=entry.get('items_key'))
    return sources,metadata


def build(root=ROOT,evidence_root=EVIDENCE,snapshot_at=None):
    themes=yaml.safe_load((root/'THEMES.yaml').read_text())['themes']
    seed=read(root/DECISIONS)
    validate_evidence(root,evidence_root,seed)
    result={'schema_version':1,'snapshot_at':snapshot_at or datetime.now(timezone.utc).isoformat(),
            'scope':'saved_updates_and_declared_legacy_waves',
            'scope_config':{'file':'configs/adoption-sources.yaml','sha256':digest(root/'configs/adoption-sources.yaml')},
            'decision_seed':{'file':DECISIONS,'sha256':digest(root/DECISIONS)},'topics':{}}
    for topic,theme in sorted(themes.items()):
        canonical_path=root/theme['sample_file'];rows=read(canonical_path)
        public_path=root/'data/public/themes'/f'{topic}.json'
        public=read(public_path) if public_path.exists() else None
        validate_public_membership(topic,rows,public)
        public_keys={record_id_hash(r) for r in rows if is_opinion_record(r)} if public else None
        sources,metadata=load_sources(root,evidence_root,topic)
        data=build_topic(topic,rows,sources,seed.get('decisions',{}).get(topic,{}),
                         public_keys=public_keys,published=theme['published']=='done')
        data['canonical_file']=theme['sample_file'];data['canonical_sha256']=digest(canonical_path)
        data['public_file']=str(public_path.relative_to(root)) if public else None
        data['public_sha256']=digest(public_path) if public else None
        data['published_state']=theme['published'];data['sources']=metadata
        data['saved_unique_records']=sum(bool(r['observations']) for r in data['records'])
        data['saved_outside_canonical']=sum(bool(r['observations']) and not r['canonical_presence'] for r in data['records'])
        result['topics'][topic]=data
    result['cohorts']={}
    for name,topics in seed.get('cohorts',{}).items():
        detail={}
        for topic,keys in topics.items():
            byid={r['record_id_hash']:r for r in result['topics'][topic]['records']}
            if len(keys)!=len(set(keys)) or any(k not in byid for k in keys):raise ValueError(f'追跡集合が保存回にありません: {name}/{topic}')
            detail[topic]={'total':len(keys),'in_canonical':sum(byid[k]['canonical_presence'] for k in keys),
                           'statuses':dict(Counter(byid[k]['adoption_status'] for k in keys))}
        result['cohorts'][name]=detail
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence-root',type=Path,default=EVIDENCE)
    p.add_argument('--out',type=Path,default=ROOT/OUTPUT)
    p.add_argument('--snapshot-at')
    p.add_argument('--check',action='store_true')
    args=p.parse_args()
    existing=read(args.out) if args.out.exists() else None
    result=build(evidence_root=args.evidence_root,snapshot_at=args.snapshot_at or (existing or {}).get('snapshot_at'))
    if args.check:
        if existing!=result:raise SystemExit('NG 採用台帳と現在の原本・保存回・判断根拠に差分があります')
        print('OK 採用台帳を原本から再生成して一致')
    else:
        write_snapshot(args.out,result)
        print('採用台帳を作成しました（原本・公開ページは変更しません）')
    print(json.dumps({t:{'saved':d['saved_unique_records'],'outside':d['saved_outside_canonical']} for t,d in result['topics'].items()},ensure_ascii=False))

if __name__=='__main__':main()
