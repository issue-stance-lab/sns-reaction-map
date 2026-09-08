#!/usr/bin/env python3
"""既存の本文確認記録を再利用し、未確認100件だけの補助レビュー試行を固定する。"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parent))
from public_registry_common import is_opinion_record
from verification_data import record_id_hash
from reread_registry import validate_manifest
from manage_reread_registry import check_sources
ROOT=Path(__file__).resolve().parents[1]
EXTERNAL=Path('/Volumes/HD-LE-B/issue-stance-private-backups/data-repairs')
FIELDS=('is_relevant','is_opinion','main_issue','stance')
CLASSIFIERS=dict(zip(['ai-copyright','bukatsu-chiiki','constitutional-amendment','elderly-license-revocation','school-nickname-ban','henoko-student-accident','takaichi','fukushuto','koshitsu-tenpakai','consumption-tax-cut'],['aicopyright','bukatsu','constitutional','elderly','nickname','henoko','takaichi','fukushuto','koshitsu','consumption_tax']))

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprint(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def text_hash(text):return hashlib.sha256(text.encode()).hexdigest()
def write(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def ids(value):
    if isinstance(value,dict):
        for v in value.values():yield from ids(v)
    elif isinstance(value,list):
        for v in value:yield from ids(v)
    elif isinstance(value,str) and re.fullmatch(r'\d{15,22}',value):yield value


def resolve_legacy_source(value,root,external):
    """Resolve old evidence references only inside the supplied restore roots."""
    root=Path(root).resolve();external=Path(external).resolve()
    path=Path(value)
    if path.is_absolute():
        if path.is_relative_to(EXTERNAL):
            base=external;relative=path.relative_to(EXTERNAL)
        elif path.is_relative_to(external):
            base=external;relative=path.relative_to(external)
        elif path.is_relative_to(root):
            base=root;relative=path.relative_to(root)
        elif '/issue-stance-aggregator/' in value:
            base=root;relative=Path(value.split('/issue-stance-aggregator/',1)[1])
        else:raise ValueError('限定確認の出所が指定ルート外: '+value)
    else:base=root;relative=path
    resolved=(base/relative).resolve()
    if '..' in relative.parts or not resolved.is_relative_to(base):
        raise ValueError('限定確認の出所が指定ルート外: '+value)
    return resolved


def inventory(root,external):
    root=Path(root).resolve();external=Path(external).resolve()
    metadata=yaml.safe_load((root/'THEMES.yaml').read_text())['themes']
    report={'schema_version':1,'snapshot_at':datetime.now(timezone.utc).isoformat(),'topics':{},'totals':{},
            'measurement_stage':'before_low_token_pilot','meaning':'Existing additional reading records by scope, not full four-field classification correctness, human approval or proof of comprehension.'}
    queues={};source_fingerprints={}
    for topic,meta in metadata.items():
        path=root/meta['sample_file'];rows=read(path);byid={str(r['tweet_id']):r for r in rows}
        if len(byid)!=len(rows):raise ValueError('duplicate canonical ID')
        editorial={};limited=set();legacy=external/'reread-inventory/20260906-v1'/f'{topic}.json'
        current_hash=sha(path)
        old=read(legacy) if legacy.exists() else None
        if old and topic!='bike-blue-ticket':
            if old['baseline_sha256']!=current_hash:raise ValueError('旧棚卸しの正典版不一致: '+topic)
            limited.update(map(str,old.get('focused_body_review_ids',[])))
            limited.update(map(str,old.get('classification_review_ids',[])))
            source_fingerprints[str(legacy.relative_to(external))]=sha(legacy)
            # Revalidate reading evidence files, not stale source scripts/old configuration references.
            for source in old['sources']:
                if source.get('kind') not in {'focused_body_review','classification_review','classification_body_review'}:continue
                p=resolve_legacy_source(source['path'],root,external)
                if not p.is_file() or sha(p)!=source['sha256']:raise ValueError('限定確認の出所が欠落・変化: '+source['path'])
                source_ref=str(p.relative_to(external)) if p.is_relative_to(external) else str(p.relative_to(root))
                source_fingerprints[source_ref]=sha(p)
        ledger=root/'data/verification/reread'/f'{topic}.json'
        if ledger.exists():
            data=read(ledger);validate_manifest(data);check_sources(root,data)
            if data['canonical_sha256']!=current_hash:raise ValueError('共通再読台帳が古い: '+topic)
            source_fingerprints[str(ledger.relative_to(root))]=sha(ledger)
            keyed={hashlib.sha256(k.encode()).hexdigest():k for k in byid}
            for row in data['records']:
                if row['review'] is not None:editorial[keyed[row['post_key']]]=row['review']['evidence_quality']
        # Recover non-opinion records omitted from the previous opinion-only report.
        if topic in {'constitutional-amendment','fukushuto','koshitsu-tenpakai','consumption-tax-cut','elderly-license-revocation'}:
            p=root/'data'/f'{topic}_claim_posts.json';limited.update(set(ids(read(p)))&byid.keys());source_fingerprints[str(p.relative_to(root))]=sha(p)
        if topic=='elderly-license-revocation':
            p=root/'social-samples/updates/elderly-license-revocation/2026-08-20/classified.json'
            limited.update(str(r['tweet_id']) for r in read(p));source_fingerprints[str(p.relative_to(root))]=sha(p)
        if topic in {'school-nickname-ban','henoko-student-accident'}:
            folder='school-nickname-ban/20260906-u2' if topic=='school-nickname-ban' else 'henoko-student-accident/20260906-u3'
            p=external/folder/'decisions.json';source_fingerprints[str(p.relative_to(external))]=sha(p)
            for record in read(p):
                key=str(record.get('tweet_id'))
                if key not in byid:continue
                if not (record.get('reviewer') or record.get('reviewer_type')):continue
                if record.get('text_sha256')!=text_hash(byid[key]['text']):raise ValueError('修復本文確認の版が変化: '+topic)
                limited.add(key)
        if not limited<=byid.keys():raise ValueError('限定記録が正典外')
        stats=Counter();queue=[]
        for key,row in byid.items():
            opinion=is_opinion_record(row);group='opinion' if opinion else 'nonopinion'
            status='editorial_record' if key in editorial else 'limited_record' if key in limited else 'record_unconfirmed'
            stats['canonical']+=1;stats[group]+=1;stats[status]+=1;stats[group+'_'+status]+=1
            if key in editorial:stats['editorial_'+editorial[key]]+=1
            if status=='record_unconfirmed':
                classification={f:(row.get('classification') or {}).get(f,row.get(f)) for f in FIELDS}
                queue.append({'record_id_hash':record_id_hash(row),'tweet_id':key,'text':row['text'],'body_sha256':text_hash(row['text']),
                              'classification':classification,'classification_sha256':fingerprint(classification),'opinion':opinion})
        for f in ['opinion','nonopinion','editorial_record','limited_record','record_unconfirmed','editorial_verified','editorial_legacy']:
            stats.setdefault(f,0)
        for g in ['opinion','nonopinion']:
            for s in ['editorial_record','limited_record','record_unconfirmed']:stats.setdefault(g+'_'+s,0)
        stats['unique_unconfirmed_bodies']=len({r['body_sha256'] for r in queue})
        stats['unique_review_inputs']=len({(r['body_sha256'],r['classification_sha256']) for r in queue})
        report['topics'][topic]={'title':meta['title'],'published':meta['published']=='done','canonical_file':meta['sample_file'],'canonical_sha256':current_hash,'counts':dict(stats)}
        queues[topic]=sorted(queue,key=lambda r:r['record_id_hash'])
    for label,predicate in [('all',lambda t:True),('published',lambda t:t['published'])]:
        total=Counter()
        for t in report['topics'].values():
            if predicate(t):total.update(t['counts'])
        report['totals'][label]=dict(total)
    report['source_fingerprints']=source_fingerprints
    return report,queues


def select(queues,report):
    picked=[];criteria={}
    for topic,queue in sorted(queues.items()):
        if not queue:continue
        if topic not in CLASSIFIERS:raise ValueError('基準未指定: '+topic)
        module=importlib.import_module('classify_'+CLASSIFIERS[topic]+'_arena_hermes')
        prompt=module.prompt_for([])
        criteria[topic]={'text':prompt.split('JSON配列')[0].strip(),'source':'scripts/classify_'+CLASSIFIERS[topic]+'_arena_hermes.py',
                         'source_sha256':sha(Path(module.__file__)),'issues':sorted(module.ISSUES),'stances':sorted(module.STANCES),'title':report['topics'][topic]['title']}
        used=set();chosen=[]
        for opinion,wanted in [(True,8),(False,2)]:
            candidates=[r for r in queue if r['opinion']==opinion]
            # Rotate issue/stance groups for coverage; this is a stratified pilot, not a random accuracy estimate.
            strata=defaultdict(list)
            for row in candidates:strata[(row['classification']['main_issue'],row['classification']['stance'])].append(row)
            while len([r for r in chosen if r['opinion']==opinion])<wanted and any(strata.values()):
                for key in sorted(strata,key=str):
                    if not strata[key]:continue
                    row=strata[key].pop(0);identity=(row['body_sha256'],row['classification_sha256'])
                    if identity in used:continue
                    used.add(identity);chosen.append(row)
                    if len([r for r in chosen if r['opinion']==opinion])>=wanted:break
            if len([r for r in chosen if r['opinion']==opinion])!=wanted:raise ValueError('試行母数不足: '+topic)
        for n,row in enumerate(chosen):picked.append({**row,'topic':topic,'sample_id':topic+':'+str(n+1),'phase':'smoke' if n==0 else 'pilot'})
    if len(picked)!=100:raise ValueError('100件の層化試行になっていません')
    return {'schema_version':1,'sampling':'10 themes, 8 opinions and 2 non-opinions each; deterministic issue/stance stratification; no claim of random population accuracy',
            'input_sha256':fingerprint(picked),'records':picked,'criteria':criteria}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    if args.out.resolve().is_relative_to(ROOT.resolve()):raise SystemExit('本文付き試行は非公開のリポジトリ外へ保存')
    if (args.out/'pilot-input.json').exists():raise SystemExit('既存試行を上書きしません')
    report,queues=inventory(ROOT,EXTERNAL);sample=select(queues,report)
    write(args.out/'inventory.json',report);write(args.out/'queues.private.json',queues);write(args.out/'pilot-input.json',sample)
    write(ROOT/'quality/reviews/2026-09-06-body-review-current-inventory.json',report)
    print(json.dumps(report['totals'],ensure_ascii=False));print('固定試行100件（最初10件）の準備完了')
