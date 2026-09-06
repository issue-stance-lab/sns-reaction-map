#!/usr/bin/env python3
"""未確認入力から既処理を除き最大20件を準備。保留・失敗の自動再送なし。"""
import argparse
from collections import deque
import json
from pathlib import Path
try:
    from scripts.prepare_body_review_pilot import inventory, EXTERNAL, fingerprint
    from scripts.editorial_work_registry import load_registry, current_attempts, checked_packet
except ModuleNotFoundError:
    from prepare_body_review_pilot import inventory, EXTERNAL, fingerprint
    from editorial_work_registry import load_registry, current_attempts, checked_packet


def select_batch(queues, attempted, limit=20):
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError('limit must be 1..20')
    seen={(r['topic'],r['body_sha256'],r['classification_sha256']) for r in attempted}
    buckets={k:deque(v) for k,v in sorted(queues.items())};chosen=[]
    while len(chosen)<limit and any(buckets.values()):
        for topic,queue in buckets.items():
            while queue:
                row=queue.popleft();key=(topic,row['body_sha256'],row['classification_sha256'])
                if key in seen:continue
                seen.add(key);chosen.append({**row,'topic':topic});break
            if len(chosen)==limit:break
    return chosen


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--registry',type=Path,help='本文なし作業台帳。既定は root/data/verification/editorial-work.json')
    p.add_argument('--private-root',type=Path,default=EXTERNAL)
    p.add_argument('--exclude-packet',type=Path,action='append',default=[],help='追加の処理済み/担当中packet。複数指定可')
    a=p.parse_args()
    if a.out.exists() or a.out.resolve().is_relative_to(a.root.resolve()) or a.out.resolve().is_relative_to(Path(__file__).resolve().parents[1]):raise ValueError('new private external file required')
    source=json.loads((a.source/'pilot-input.json').read_text())
    if fingerprint(source['records'])!=source['input_sha256']:raise ValueError('attempt source changed')
    old=json.loads((a.source/'inventory.json').read_text());current,queues=inventory(a.root,EXTERNAL)
    # 原本のどこかが変わった場合は、旧試行を再利用する前に差分監査する。
    for topic in old['topics']:
        if old['topics'][topic]['canonical_sha256']!=current['topics'][topic]['canonical_sha256']:raise ValueError('canonical snapshot changed')
    for criteria in source['criteria'].values():
        import hashlib
        if hashlib.sha256((a.root/criteria['source']).read_bytes()).hexdigest()!=criteria['source_sha256']:raise ValueError('criteria changed')
    registry=load_registry(a.registry or a.root/'data/verification/editorial-work.json',a.root,a.private_root)
    attempted=list(current_attempts(registry,source['criteria']))
    for path in a.exclude_packet:
        extra=json.loads(path.read_text())
        if any(fingerprint(value)!=fingerprint(source['criteria'].get(topic)) for topic,value in extra['criteria'].items()):raise ValueError('reservation criteria changed')
        attempted.extend(checked_packet(extra,a.root))
    rows=select_batch(queues,attempted)
    value={'schema_version':1,'state':'prepared_not_reviewed','records':rows,'criteria':{t:source['criteria'][t] for t in sorted({r['topic'] for r in rows})},
           'excluded_or_reserved_records':len(attempted),'input_sha256':fingerprint(rows),'automatic_reread_credit':0,'additional_model_calls':0,
           'measurement_template':{'new_decisions':None,'reused_decisions':None,'held':None,'elapsed_seconds':None,'observed_tokens':None,'token_scope':None},
           'instructions':'Read only these records and criteria. Return all four values, uncertainty and a brief reason. Preserve uncertainty; do not publish or mutate canonical. Independent reviewer checks change candidates and reason conflicts. No agents receive full thread history.'}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print('PREPARED',len(rows),'new unique inputs; no model call')
