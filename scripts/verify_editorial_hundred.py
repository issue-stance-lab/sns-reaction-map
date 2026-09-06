#!/usr/bin/env python3
"""5回×20件を集約し、支持された差分を1つの隔離コピーで生成検査する。"""
import argparse
from collections import Counter,defaultdict
import copy
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import yaml
try:
    from scripts.summarize_editorial_batch import summarize
    from scripts.prepare_editorial_review_packet import check_record
    from scripts.verify_editorial_candidate_pair import counts
except ModuleNotFoundError:
    from summarize_editorial_batch import summarize
    from prepare_editorial_review_packet import check_record
    from verify_editorial_candidate_pair import counts

ADAPTERS={'ai-copyright':'ai_copyright','bukatsu-chiiki':'bukatsu','constitutional-amendment':'constitutional',
          'consumption-tax-cut':'consumption_tax','elderly-license-revocation':'elderly','fukushuto':'fukushuto',
          'henoko-student-accident':'henoko','koshitsu-tenpakai':'koshitsu','school-nickname-ban':'nickname','takaichi':'takaichi'}
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')


def collect(run):
    run=Path(run);reservation=read(run/'reservation.json');batches=[];journal=[];source={};proofs={};seen=set()
    for n in range(1,6):
        d=run/f'batch-{n:02d}';packet=read(d/'packet.private.json')
        if sha(d/'packet.private.json')!=reservation['packet_hashes'][str((d/'packet.private.json').relative_to(run))]:raise ValueError('packet changed')
        if len(packet['records'])!=20:raise ValueError('batch size differs')
        result=summarize(packet,read(d/'editor.private.json'),read(d/'audit.private.json'))
        for row in result['journal']:
            raw=packet['records'][row['index']];key=(raw['topic'],raw['body_sha256'],raw['classification_sha256'])
            if key in seen:raise ValueError('duplicate review input across batches')
            seen.add(key);item={**row,'batch':n};journal.append(item);source[(n,row['index'])]=(raw,packet['criteria'][raw['topic']])
        batches.append({'batch':n,**{k:result[k] for k in ['records','independent_records','first_routes','routes']}})
        for f in ['packet.private.json','editor.private.json','audit.private.json']:proofs[str((d/f).relative_to(run))]=sha(d/f)
    if len(journal)!=100:raise ValueError('one hundred records required')
    return {'schema_version':1,'new_records':100,'batches':batches,'routes':dict(Counter(r['route'] for r in journal)),
            'independent_records':sum(b['independent_records'] for b in batches),'journal':journal,'proofs':proofs,
            'canonical_changes':0,'registered_reread_increment':0,'local_model_calls':0,'codex_tokens':'not_measured'},source


def verify(root,run,out,*,collected=None):
    root,run,out=map(Path,[root,run,out]);started=time.time()
    if out.exists() or out.resolve().is_relative_to(root.resolve()):raise ValueError('new external output directory required')
    aggregate,sources=collect(run) if collected is None else collected
    meta=yaml.safe_load((root/'THEMES.yaml').read_text())['themes']
    cache={};canon_hashes={};chosen=defaultdict(list)
    for row in aggregate['journal']:
        raw,c=sources[(row['batch'],row['index'])];t=row['topic']
        if sha(root/c['source'])!=c['source_sha256']:raise ValueError('criteria changed')
        if t not in cache:
            p=root/meta[t]['sample_file'];rows=read(p);cache[t]={str(r['tweet_id']):r for r in rows};canon_hashes[t]=sha(p)
            if len(cache[t])!=len(rows):raise ValueError('canonical duplicate IDs')
        check_record(raw,cache[t][raw['tweet_id']])
        if row['route']=='change_candidate':chosen[t].append(row)
    tree=out/'candidate';tree.mkdir(parents=True)
    paths=set(subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().strip('\0').split('\0'))
    paths|={str(p.relative_to(root)) for p in (root/'social-samples').rglob('*') if p.is_file()}
    before={p:sha(root/p) for p in paths if (root/p).is_file()}
    for rel in before:
        dest=tree/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/rel,dest)
    impacts=[]
    for t,changes in sorted(chosen.items()):
        path=tree/meta[t]['sample_file'];original=read(path);candidate=copy.deepcopy(original)
        byid={str(r['tweet_id']):r for r in candidate}
        for row in changes:
            raw,_=sources[(row['batch'],row['index'])];target=byid[raw['tweet_id']]
            check_record(raw,target)
            for field,value in row['changes'].items():
                if field in (target.get('classification') or {}):target['classification'][field]=value
                else:target[field]=value
        if sum(a!=b for a,b in zip(original,candidate))!=len(changes) or len(original)!=len(candidate):raise ValueError('unexpected changes')
        dump(path,candidate)
        impacts.append({'topic':t,'changed_records':len(changes),'before':counts(original),'after':counts(candidate),
                        'source_sha256':canon_hashes[t],'candidate_sha256':sha(path)})
    logs=[]
    def command(args):
        r=subprocess.run([sys.executable,*args],cwd=tree,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        logs.append({'args':args,'exit_code':r.returncode,'output':r.stdout});dump(out/'commands.private.json',logs)
        if r.returncode:raise RuntimeError('failed '+' '.join(args))
    sys.path.insert(0,str(root));sys.path.insert(0,str(root/'scripts'))
    adapters={t:importlib.import_module('scripts.refresh_adapters.'+ADAPTERS[t]) for t in chosen}
    def generate():
        command(['scripts/build_public_registry.py','--all'])
        for t,adapter in sorted(adapters.items()):
            page=tree/meta[t]['html'];canonical=tree/meta[t]['sample_file']
            if t=='bukatsu-chiiki':command(['scripts/build_bukatsu_arena.py'])
            else:
                args=[tree,canonical,page,page]
                if len(inspect.signature(adapter._run_builder).parameters)==5:args.append(tree/adapter.ARENA_DATA)
                # Adapter subprocess output stays private; no body text is placed in the report.
                import contextlib
                with (out/'adapter-output.private.log').open('a') as log:
                    with contextlib.redirect_stdout(log):adapter._run_builder(*args)
                if hasattr(adapter,'finalize'):adapter.finalize(tree,'2026-09-07')
            if meta[t].get('verification_file'):command(['scripts/verification_data.py','--input',meta[t]['sample_file'],'--output',meta[t]['verification_file']])
            command(['scripts/sync_issue_counts.py',t])
        command(['scripts/seo/apply_theme_trust.py']);command(['scripts/sync_portal_stats.py'])
    generate()
    first={str(p.relative_to(tree)):sha(p) for folder in ['docs','data/public'] for p in (tree/folder).rglob('*') if p.is_file()}
    generate()
    if first!={rel:sha(tree/rel) for rel in first}:raise ValueError('second generation differs')
    for t,adapter in sorted(adapters.items()):
        command(['scripts/verify_theme_page.py',t]);command(['scripts/verify_number_provenance.py',t])
        a=(root/meta[t]['html']).read_text();b=(tree/meta[t]['html']).read_text()
        if hasattr(adapter,'vote_fingerprint'):
            if adapter.vote_fingerprint(a)!=adapter.vote_fingerprint(b):raise ValueError('vote definition changed')
        else:
            from scripts.refresh_adapters.elderly import vote_fingerprint
            if vote_fingerprint(a)!=vote_fingerprint(b):raise ValueError('vote definition changed')
        for token in set(getattr(adapter,'PROTECTED',()))|{'G-K10S4YCZFH','ca-pub-2542211932832864','vote-store.js','property="og:image"','rel="canonical"'}:
            if a.count(token)!=b.count(token):raise ValueError('protected tag changed')
    command(['scripts/verify_top_page.py']);command(['scripts/verify_public_registry.py','--against-private'])
    if any(sha(root/rel)!=value for rel,value in before.items()):raise ValueError('source tree changed during generation')
    aggregate.update({'generation':{'impacts':impacts,'source_unchanged':True,'idempotent':True,'vote_and_protected_tags_unchanged':True,
                    'elapsed_seconds':round(time.time()-started,2),'checks':[{'args':r['args'],'exit_code':r['exit_code']} for r in logs],
                    'changed_hashes':{rel:value for rel,value in first.items() if not (root/rel).exists() or sha(root/rel)!=value}}})
    dump(out/'report.json',aggregate);return aggregate


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=verify(a.root,a.run,a.out);print(json.dumps({'routes':r['routes'],'independent_records':r['independent_records'],'generation':'passed'},ensure_ascii=False))
