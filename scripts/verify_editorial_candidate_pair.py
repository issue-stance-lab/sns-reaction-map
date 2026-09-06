#!/usr/bin/env python3
"""支持済み2件だけを隔離コピーで生成検査。共有正典と公開物は変更しない。"""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import yaml
try:
    from scripts.prepare_editorial_review_packet import build, check_record
    from scripts.public_registry_common import is_opinion_record
except ModuleNotFoundError:
    from prepare_editorial_review_packet import build, check_record
    from public_registry_common import is_opinion_record


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def counts(rows):
    opinions=[r for r in rows if is_opinion_record(r)]
    return {'collected':len(rows),'opinions':len(opinions),'issues':dict(Counter((r.get('classification') or {}).get('main_issue',r.get('main_issue')) for r in opinions)),
            'stances':dict(Counter((r.get('classification') or {}).get('stance',r.get('stance')) for r in opinions))}

def run(root,source,out,decisions):
    root,source,out,decisions=map(Path,[root,source,out,decisions])
    if out.exists() or out.resolve().is_relative_to(root.resolve()):raise ValueError('new external output directory required')
    packet=json.loads(decisions.read_text());fresh,_=build(root,source)
    if fresh['versions']!=packet['versions'] or fresh['source_sha256']!=packet['source_sha256']:raise ValueError('candidate evidence stale')
    chosen=[r for r in packet['journal'] if r['route']=='change_candidate' and r.get('independent_candidate_audit')=='support']
    if len(chosen)!=2:raise ValueError('exactly two supported changes required')
    saved={r['sample_id']:r for r in json.loads((source/'pilot-input.json').read_text())['records']}
    meta=yaml.safe_load((root/'THEMES.yaml').read_text())['themes']
    tree=out/'candidate';tree.mkdir(parents=True)
    paths=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
    paths=set(p for p in paths if p)|{str(p.relative_to(root)) for p in (root/'social-samples').rglob('*') if p.is_file()}
    before={p:sha(root/p) for p in paths if (root/p).is_file()}
    for rel in before:
        dest=tree/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/rel,dest)
    changes=[]
    for row in chosen:
        topic=row['topic'];path=tree/meta[topic]['sample_file'];original=json.loads(path.read_text());candidate=copy.deepcopy(original)
        hits=[r for r in candidate if str(r['tweet_id'])==saved[row['sample_id']]['tweet_id']]
        if len(hits)!=1:raise ValueError('target missing/duplicate')
        check_record(saved[row['sample_id']],hits[0])
        for key,value in row['suggested_changes'].items():
            if key in (hits[0].get('classification') or {}):hits[0]['classification'][key]=value
            else:hits[0][key]=value
        changed=[i for i,(a,b) in enumerate(zip(original,candidate)) if a!=b]
        if len(changed)!=1 or len(original)!=len(candidate):raise ValueError('unexpected mutation')
        dump(path,candidate)
        changes.append({'topic':topic,'sample_id':row['sample_id'],'before':counts(original),'after':counts(candidate),
                        'canonical_before_sha256':before[meta[topic]['sample_file']],'candidate_sha256':sha(path),'changed_records':1})
    logs=[]
    def command(args):
        result=subprocess.run([sys.executable,*args],cwd=tree,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        logs.append({'args':args,'exit_code':result.returncode,'output':result.stdout})
        dump(out/'commands.private.json',logs)
        if result.returncode:raise RuntimeError('candidate check failed: '+' '.join(args))
    names={'elderly-license-revocation':'elderly','koshitsu-tenpakai':'koshitsu'}
    def generate():
        for row in chosen:
            topic=row['topic'];command(['scripts/build_'+names[topic]+'_arena.py'])
            if meta[topic].get('verification_file'):command(['scripts/verification_data.py','--input',meta[topic]['sample_file'],'--output',meta[topic]['verification_file']])
        command(['scripts/build_public_registry.py','--all'])
        for row in chosen:
            topic=row['topic'];command(['scripts/build_'+names[topic]+'_arena.py','--public-counts-only'])
            command(['scripts/sync_issue_counts.py',topic])
        command(['scripts/seo/apply_theme_trust.py']);command(['scripts/sync_portal_stats.py'])
    generate()
    first={str(p.relative_to(tree)):sha(p) for folder in ['docs','data/public'] for p in (tree/folder).rglob('*') if p.is_file()}
    generate()
    second={rel:sha(tree/rel) for rel in first}
    if first!=second:raise ValueError('second generation differs')
    for row in chosen:
        topic=row['topic'];command(['scripts/verify_theme_page.py',topic]);command(['scripts/verify_number_provenance.py',topic])
    command(['scripts/verify_top_page.py']);command(['scripts/verify_public_registry.py','--against-private'])
    if any(sha(root/rel)!=digest for rel,digest in before.items()):raise ValueError('source tree changed during trial')
    report={'schema_version':1,'scope':'isolated two-record data/page generation trial; not public release',
            'decisions_sha256':sha(decisions),'topics':changes,'idempotent':True,'source_unchanged':True,
            'canonical_promoted':False,'additional_model_calls':0,'checks':[{'args':x['args'],'exit_code':x['exit_code']} for x in logs],
            'generated_hashes':first}
    dump(out/'report.json',report)
    print(json.dumps({'topics':changes,'idempotent':True,'source_unchanged':True},ensure_ascii=False))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ['root','source','out','decisions']:p.add_argument('--'+flag,type=Path,required=True)
    a=p.parse_args();run(a.root,a.source,a.out,a.decisions)
