#!/usr/bin/env python3
"""既存20+新20+新100の支持16件を、原証拠を照合して1候補へ統合する。"""
import argparse
from collections import Counter
from pathlib import Path
try:
    from scripts.verify_editorial_hundred import collect, verify, read, sha
    from scripts.prepare_editorial_review_packet import build
    from scripts.summarize_editorial_batch import summarize
except ModuleNotFoundError:
    from verify_editorial_hundred import collect, verify, read, sha
    from prepare_editorial_review_packet import build
    from summarize_editorial_batch import summarize


def validate_integrated(journal):
    identities={(r['topic'],r['record_id_hash']) for r in journal}
    routes=dict(Counter(r['route'] for r in journal))
    if len(journal)!=140 or len(identities)!=140 or routes!={'retain_candidate':69,'change_candidate':16,'hold':55}:
        raise ValueError('unexpected integrated population')
    if any(r['independently_checked'] is not True for r in journal if r['route']=='change_candidate'):
        raise ValueError('unsupported correction')
    return routes


def assemble(root,base):
    root,base=Path(root),Path(base);journal=[];sources={};proofs={}
    original_path=root/'quality/reviews/2026-09-07-editorial-review-packet.json'
    final=read(root/'quality/reviews/2026-09-07-editorial-review-decisions.json')
    fresh,_=build(root,base/'20260906-v1')
    if fresh!=read(original_path):raise ValueError('initial packet is stale or changed')
    audit_path=base/'20260907-editorial-v1/candidate-audit.private.json';audit=read(audit_path)
    if sha(audit_path)!=final['candidate_audit_sha256'] or sha(original_path)!=audit['source_packet_sha256']:raise ValueError('initial audit proof mismatch')
    decisions={r['sample_id']:r for r in audit['decisions']}
    candidates={r['sample_id'] for r in fresh['journal'] if r['route']=='change_candidate'}
    if set(decisions)!=candidates or len(audit['decisions'])!=3:raise ValueError('initial audit coverage mismatch')
    final_rows={r['sample_id']:r for r in final['journal']}
    if len(final_rows)!=20 or len(final['journal'])!=20:raise ValueError('initial final coverage mismatch')
    input1=read(base/'20260906-v1/pilot-input.json');raws={r['sample_id']:r for r in input1['records']}
    for i,old in enumerate(fresh['journal']):
        row=final_rows[old['sample_id']];raw=raws[old['sample_id']];decision=decisions.get(old['sample_id'])
        for field in ['record_id_hash','body_sha256','classification_sha256','current','proposed','suggested_changes']:
            if row[field]!=old[field]:raise ValueError('initial candidate content changed')
        route=old['route']
        if decision:
            if decision['decision'] not in {'support','hold'}:raise ValueError('invalid audit decision')
            if any(decision[k]!=row[k] for k in ['body_sha256','classification_sha256']):raise ValueError('audit version mismatch')
            if decision['decision']=='hold':route='hold'
        if row['route']!=route:raise ValueError('audit disposition changed')
        journal.append({**row,'batch':0,'index':i,'changes':row['suggested_changes'],
                        'independently_checked':bool(decision),'canonical_applied':False})
        sources[(0,i)]=(raw,input1['criteria'][row['topic']])
    for p in [original_path,root/'quality/reviews/2026-09-07-editorial-review-decisions.json']:
        proofs[str(p.relative_to(root))]=sha(p)
    proofs[str(audit_path.relative_to(base))]=sha(audit_path)
    packet_path=base/'20260907-next20/packet.private.json';packet=read(packet_path)
    editor_path=base/'20260907-next20-review-v1/editor.private.json';audit_path2=base/'20260907-next20-review-v1/audit.private.json'
    next20=summarize(packet,read(editor_path),read(audit_path2))
    saved=read(root/'quality/reviews/2026-09-07-next20-editorial-results.json')
    if next20['journal']!=saved['journal']:raise ValueError('next20 final decisions changed')
    for row in next20['journal']:
        journal.append({**row,'batch':1});raw=packet['records'][row['index']]
        sources[(1,row['index'])]=(raw,packet['criteria'][row['topic']])
    for p in [packet_path,editor_path,audit_path2]:proofs[str(p.relative_to(base))]=sha(p)
    hundred,hundred_sources=collect(base/'20260907-hundred-v1')
    for row in hundred['journal']:
        journal.append({**row,'batch':row['batch']+1})
        sources[(row['batch']+1,row['index'])]=hundred_sources[(row['batch'],row['index'])]
    proofs.update({'20260907-hundred-v1/'+k:v for k,v in hundred['proofs'].items()})
    routes=validate_integrated(journal)
    return {'schema_version':1,'scope':'integration of existing 140 editorial records; no new body review',
            'reviewed_records':140,'new_records':0,'routes':routes,'journal':journal,'proofs':proofs,
            'canonical_changes':0,'registered_reread_increment':0,'local_model_calls':0,'codex_tokens':'not_measured'},sources


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();result=verify(a.root,a.base,a.out,collected=assemble(a.root,a.base))
    print(result['routes'])
