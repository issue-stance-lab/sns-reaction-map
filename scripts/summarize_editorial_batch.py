#!/usr/bin/env python3
"""小口編集確認の対象・版・判断を検査し、独立確認を必要な差分へ限定する。"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
try:
    from scripts.trial_body_review_values import validate
except ModuleNotFoundError:
    from trial_body_review_values import validate


def verified_reviews(packet, result, expected):
    reviews=result['reviews']
    if len(reviews)!=len(expected) or any(type(r.get('index')) is not int for r in reviews) or sorted(r['index'] for r in reviews)!=sorted(expected):
        raise ValueError('review coverage mismatch')
    verified={}
    for review in reviews:
        i=review['index'];source=packet['records'][i]
        for key in ['record_id_hash','body_sha256','classification_sha256']:
            if review[key]!=source[key]:raise ValueError('review identity/version mismatch')
        value={k:review[k] for k in ['classification','uncertain','reason']}
        verified[i]={**review,**validate(value,source['classification'],packet['criteria'][source['topic']])}
    return verified


def select_audit(verified):
    changed=[i for i,r in sorted(verified.items()) if r['route']=='candidate']
    retained=[i for i,r in sorted(verified.items()) if r['route']=='no_change'][:2]
    held=[i for i,r in sorted(verified.items()) if r['route']=='uncertain'][:1]
    return sorted(set(changed+retained+held))


def summarize(packet, editor, audit=None):
    if not 1<=len(packet['records'])<=20:raise ValueError('batch size must be 1..20')
    first=verified_reviews(packet,editor,list(range(len(packet['records']))))
    targets=select_audit(first);second=verified_reviews(packet,audit,targets) if audit else {}
    journal=[]
    for i,r in sorted(first.items()):
        source=packet['records'][i];other=second.get(i)
        if r['route']=='uncertain':route='hold'
        elif i in targets and not other:route='independent_review_pending'
        elif other and (other['uncertain'] or other['classification']!=r['classification']):route='hold'
        else:route='change_candidate' if r['changes'] else 'retain_candidate'
        journal.append({'index':i,'topic':source['topic'],'record_id_hash':source['record_id_hash'],
            'body_sha256':source['body_sha256'],'classification_sha256':source['classification_sha256'],
            'current':source['classification'],'proposed':r['classification'],'changes':r['changes'],
            'route':route,'first_route':r['route'],'independently_checked':other is not None,
            'independent_proposed':other['classification'] if other else None,
            'reason_sha256':hashlib.sha256(r['reason'].encode()).hexdigest(),
            'independent_reason_sha256':hashlib.sha256(other['reason'].encode()).hexdigest() if other else None,
            'counts_as_registered_editorial_reread':False,'canonical_applied':False})
    return {'schema_version':1,'records':len(first),'audit_indices':targets,'independent_records':len(second),
            'first_routes':dict(Counter(r['route'] for r in first.values())),
            'routes':dict(Counter(r['route'] for r in journal)),
            'additional_local_model_calls':0,'codex_tokens':'not_measured',
            'classification_quality_scope':'AI editorial candidates, not accuracy or public approval',
            'canonical_changes':0,'registered_reread_increment':0,'journal':journal}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packet',type=Path,required=True);p.add_argument('--editor',type=Path,required=True)
    p.add_argument('--audit',type=Path);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();read=lambda f:json.loads(f.read_text())
    result=summarize(read(a.packet),read(a.editor),read(a.audit) if a.audit else None)
    result['proofs']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [a.packet,a.editor,*([a.audit] if a.audit else [])]}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['records','audit_indices','first_routes','routes']},ensure_ascii=False))
