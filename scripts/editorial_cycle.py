"""Frozen two-wave editorial cycle; original review helpers remain unchanged."""
import argparse
from collections import Counter
from pathlib import Path
import time
from scripts import continuous_editorial_review as review
from scripts.verify_editorial_hundred import read, sha, dump
from scripts.editorial_work_registry import checked_packet
from scripts.editorial_acceptance import assess_batch


def binding(run,batch,role,actor):
    run=Path(run); assignment=read(run/'reservation.json')['assignments']
    if batch not in assignment[role].get(actor,[]): raise ValueError('actor is not assigned this batch')
    expected=Path(read(run/'reservation.json')['worktrees'][actor]).resolve()
    if Path.cwd().resolve()!=expected: raise ValueError('wrong assigned worktree')
    p=review.batch_dir(run,batch)/(role+'-actor.private.json')
    value={'actor':actor,'worktree':str(expected),'reservation_sha256':sha(run/'reservation.json')}
    if p.exists():
        if read(p)!=value:raise ValueError('actor binding changed')
    else:dump(p,value)


def show(run,batch,role,actor,with_criteria=True):
    binding(run,batch,role,actor)
    return review.show(run,batch,role,with_criteria)


def save(run,batch,role,actor,values,**kwargs):
    binding(run,batch,role,actor)
    return review.save(run,batch,role,values,**kwargs)


def comparison(run,batch,actor):
    binding(run,batch,'audit',actor)
    return review.comparison(run,batch)


def gate(run,batch,actor,**kwargs):
    binding(run,batch,'audit',actor)
    return review.gate(run,batch,**kwargs)


def collect(root,run):
    root,run=Path(root),Path(run); reservation=read(run/'reservation.json')
    if reservation['writer_sha256']!=sha(root/'scripts/continuous_editorial_review.py'):
        raise ValueError('original writer changed')
    assignments=reservation['assignments'];n=reservation['new_records']//20
    if n!=50:raise ValueError('expected frozen 1000-record wave')
    for role in ['editor','audit']:
        if sorted(i for v in assignments[role].values() for i in v)!=list(range(1,n+1)):
            raise ValueError('incomplete assignments')
    for actor,bs in assignments['editor'].items():
        if set(bs)&set(assignments['audit'].get(actor,[])):raise ValueError('self audit')
    journal=[];sources={};proofs={'reservation.json':sha(run/'reservation.json')};independent=0
    for b in range(1,n+1):
        d=review.batch_dir(run,b);packet=review.packet_for(run,b);checked_packet(packet,root)
        editor=read(d/'editor.private.json');audit=read(d/'audit.private.json');g=read(d/'quality_gate.private.json')
        for role,result in [('editor',editor),('audit',audit)]:
            actor=next(a for a,v in assignments[role].items() if b in v)
            bound=read(d/(role+'-actor.private.json'))
            if bound!={'actor':actor,'worktree':reservation['worktrees'][actor],'reservation_sha256':sha(run/'reservation.json')}:
                raise ValueError('actor binding mismatch')
            started=read(d/(role+'-start.private.json'));draft=read(d/(role+'-draft.private.json'))
            if result['packet_sha256']!=sha(d/'packet.private.json') or started['packet_sha256']!=result['packet_sha256']:
                raise ValueError('packet identity mismatch')
            if started['started_epoch']!=result['started_epoch'] or not result['started_epoch']<=draft['recorded_epoch']<=result['finished_epoch']:
                raise ValueError('invalid timing')
            compact=[[r['index'],*[r['classification'][k] for k in ['is_relevant','is_opinion','main_issue','stance']],r['uncertain'],r['evidence_sufficient'],r['reason']] for r in result['reviews']]
            if compact!=draft['values']:raise ValueError('raw response mismatch')
        if read(d/'editor-flags.private.json')['systemic_criteria_issue'] and not g['systemic_criteria_issue']:
            raise ValueError('criteria issue dropped')
        result=assess_batch(packet,editor,audit,g);independent+=result['independent_records']
        for row in result['journal']:
            journal.append({**row,'batch':b});raw=packet['records'][row['index']]
            sources[(b,row['index'])]=(raw,packet['criteria'][raw['topic']])
        for p in d.glob('*.private.json'):proofs[str(p.relative_to(run))]=sha(p)
    if len({(r['topic'],r['record_id_hash']) for r in journal})!=1000:raise ValueError('duplicate records')
    return {'schema_version':1,'new_records':1000,'journal':journal,'independent_records':independent,'adoption_counts':dict(Counter(r['adoption_status'] for r in journal)),
            'proofs':proofs,'canonical_changes':0,'registered_reread_increment':0,'codex_tokens':None,
            'actor_evidence_scope':'Assignment pinned before work; writer checks assigned worktree and actor binding. This is operational attribution, not cryptographic agent authentication.'},sources


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['show','compare','ready']);p.add_argument('--run',type=Path,required=True);p.add_argument('--batch',type=int);p.add_argument('--role',default='editor');p.add_argument('--actor',required=True)
    a=p.parse_args();result=review.ready(a.run) if a.action=='ready' else comparison(a.run,a.batch,a.actor) if a.action=='compare' else show(a.run,a.batch,a.role,a.actor)
    import json
    print(json.dumps(result,ensure_ascii=False))
