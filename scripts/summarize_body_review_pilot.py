#!/usr/bin/env python3
"""補助レビュー試行の消費量と独立比較を集計する。精度や読了率へ読み替えない。"""
from collections import Counter
from datetime import datetime,timezone
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def summarize(directory):
    directory=Path(directory);source=read(directory/'pilot-input.json')
    reference=read(directory/'reference-20.json');records={r['sample_id']:r for r in source['records']}
    batches=[read(p) for p in sorted((directory/'batches').glob('*.json'))]
    attempts=[read(p) for p in sorted((directory/'attempts').glob('*.json'))]
    reviews={};errors={};covered=set()
    for b in batches:
        target={sid for sid,r in records.items() if r['topic']==b['request']['topic'] and r['phase']==b['request']['phase']}
        if b['request']['input_sha256']!=source['input_sha256']:raise ValueError('mixed pilot input')
        if b['status'] not in {'complete','partial','invalid'}:raise ValueError('unfinished batch')
        covered|=target
        for r in b.get('reviews',[]):
            sid=r['sample_id']
            if sid not in target or sid in reviews or r['body_sha256']!=records[sid]['body_sha256'] or r['classification_sha256']!=records[sid]['classification_sha256']:raise ValueError('review scope mismatch')
            reviews[sid]=r
        for r in b.get('errors',[]):errors[r['sample_id']]=r['error']
        if b['status']=='invalid':
            for sid in target:errors[sid]=b.get('error','invalid output')
    if covered!=records.keys():raise ValueError('100件すべての呼出しが完了していません')
    if reviews.keys()&errors.keys() or reviews.keys()|errors.keys()!=records.keys():raise ValueError('output partition mismatch')
    usage={k:sum((b.get('usage',{}).get(k) or 0) for b in batches+attempts) for k in ['prompt_eval_count','eval_count','total_duration','load_duration']}
    usage['observed_input_plus_output_tokens']=usage['prompt_eval_count']+usage['eval_count']
    usage['requests']=len(batches)+len(attempts)
    usage['missing_token_counters']=sum(any(b.get('usage',{}).get(k) is None for k in ['prompt_eval_count','eval_count']) for b in batches+attempts)
    usage['scope']='Local Ollama API counters, including failed attempts; excludes parent/child Codex conversation and setup work.'
    comparison=[];confusion=Counter()
    for r in reference['reviews']:
        sid=r['sample_id']
        if r['body_sha256']!=records[sid]['body_sha256'] or r['classification_sha256']!=records[sid]['classification_sha256']:raise ValueError('reference version mismatch')
        local=reviews[sid]['status'] if sid in reviews else 'format_error'
        confusion[r['status']+' -> '+local]+=1
        comparison.append({'sample_id':sid,'independent_status':r['status'],'local_status':local,
                           'same_status':r['status']==local,
                           'same_suggestion':r['status']==local and r['suggested']==reviews.get(sid,{}).get('suggested')})
    if len(comparison)!=20 or len({r['sample_id'] for r in comparison})!=20:raise ValueError('independent sample must be 20 unique records')
    statuses=dict(Counter([r['status'] for r in reviews.values()]+['format_error']*len(errors)))
    false_clear=sum(r['local_status']=='ok' and r['independent_status']!='ok' for r in comparison)
    output={'schema_version':1,'completed_at':datetime.now(timezone.utc).isoformat(),'sampling':source['sampling'],'unique_records':len(records),
            'model':batches[0]['request']['model'],'model_digest':batches[0]['request']['model_digest'],
            'statuses':statuses,'usage':usage,'independent_comparison':{'records':20,'status_matches':sum(r['same_status'] for r in comparison),
            'local_ok_needing_independent_review':false_clear,'confusion':dict(confusion),'details':comparison},
            'automatic_editorial_credit':0,'canonical_changes':0,'production_rollout_allowed':False,
            'limitations':['Stratified small sample, not representative population accuracy.','Independent AI reference is not human ground truth or fact checking.','ok is a local model judgement, not proof of correctness.'],
            'private_evidence':{p.name:sha(p) for p in [directory/'pilot-input.json',directory/'reference-20.json',directory/'smoke-gate.json']},
            'per_phase':{phase:{'requests':len([b for b in batches if b['request']['phase']==phase]),
              'prompt_tokens':sum(b['usage']['prompt_eval_count'] for b in batches if b['request']['phase']==phase),
              'output_tokens':sum(b['usage']['eval_count'] for b in batches if b['request']['phase']==phase)} for phase in ['smoke','pilot']}}
    reference_byid={r['sample_id']:r for r in reference['reviews']}
    journal=[]
    for sid,row in sorted(records.items()):
        ref=reference_byid.get(sid)
        journal.append({'sample_id':sid,'record_id_hash':row['record_id_hash'],'body_sha256':row['body_sha256'],
            'classification_sha256':row['classification_sha256'],'local_status':reviews[sid]['status'] if sid in reviews else 'format_error',
            'independent_reference_status':ref['status'] if ref else None,
            'independent_reason_sha256':hashlib.sha256(ref['reason'].encode()).hexdigest() if ref else None,
            'disposition':'pilot_only_pending_editorial_decision','counts_as_editorial_reread':False})
    output['journal']=journal
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,required=True);a=p.parse_args();out=summarize(a.directory)
    (ROOT/'quality/reviews/2026-09-06-body-review-pilot-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ['unique_records','statuses','usage','production_rollout_allowed']},ensure_ascii=False))
