"""Prepare the final non-koshitsu remainder only after four registered cycles."""
from collections import Counter,defaultdict
from pathlib import Path
import shutil
import time
import yaml

from scripts.resolve_remaining_review_scope import load_resolution
from scripts.prepare_editorial_continuation import build_criteria
from scripts.editorial_work_registry import load_registry,checked_packet,fingerprint
from scripts.verify_editorial_hundred import read,sha,dump


def prepare(root,private,run,worktrees,prior_runs):
    root,private,run=(Path(p).resolve() for p in (root,private,run))
    worktrees={actor:str(Path(path).resolve()) for actor,path in worktrees.items()}
    if run.exists() or not run.is_relative_to(private) or run.is_relative_to(root):raise ValueError('new private run required')
    if set(worktrees) != {'editor_a','editor_b','auditor'} or len(set(worktrees.values())) != 3 or any(not Path(p).is_dir() for p in worktrees.values()):raise ValueError('separate existing worktrees required')
    scope_summary=read(root/'data/verification/editorial-review-scope.json');scope=load_resolution(scope_summary,private)
    work=load_registry(root/'data/verification/editorial-work.json',root,private)
    complete={(r['topic'],r['record_id_hash']):r for r in work['records'] if r['state']!='attempted'}
    remaining=[r for r in scope['records'] if r['topic']!='koshitsu-tenpakai' and (r['topic'],r['record_id_hash']) not in complete]
    if len(remaining) != 352:raise ValueError('expected unresolved final 352; do not force count')
    prior_ids=set();prior_hashes={}
    if len(prior_runs)!=4:raise ValueError('four prior cycles required')
    for prev in map(Path,prior_runs):
        top=read(prev/'reservation.json');prior_hashes[str(prev.relative_to(private))]=sha(prev/'reservation.json')
        for name,digest in top['waves'].items():
            if sha(prev/name/'reservation.json')!=digest:raise ValueError('prior wave changed')
            for rel,h in read(prev/name/'reservation.json')['packet_hashes'].items():
                path=prev/name/rel
                if sha(path)!=h:raise ValueError('prior packet changed')
                for x in read(path)['records']:
                    key=(x['topic'],x['record_id_hash'])
                    if key in prior_ids or key not in complete:raise ValueError('prior cycles overlap or lack work completion')
                    prior_ids.add(key)
    if len(prior_ids)!=4000:raise ValueError('prior cycle coverage differs')
    inv=private/'body-review-inventory/20260908-finish5134/inventory.private.json'
    if sha(inv)!=scope['provenance']['inventory_sha256']:raise ValueError('inventory changed')
    raws={(r['topic'],r['record_id_hash']):r for r in read(inv)['raw_remaining']}
    meta=yaml.safe_load((root/'THEMES.yaml').read_text())['themes'];criteria=build_criteria(root)
    for t,h in scope['provenance']['canonical_sha256'].items():
        if sha(root/meta[t]['sample_file'])!=h:raise ValueError('canonical changed')
    grouped=defaultdict(list)
    for r in remaining:
        t=r['topic'];raw=raws[(t,r['record_id_hash'])]
        if t=='takaichi' or meta[t]['published']!='done':raise ValueError('nonpublic topic')
        if any(raw[k]!=r[k] for k in ('body_sha256','classification_sha256')) or fingerprint(criteria[t])!=r['criteria_sha256']:raise ValueError('input version changed')
        if r['route'].startswith('verify_distinct_id_'):
            dep=r['dependency'];key=(dep['topic'],dep['record_id_hash'])
            if key not in complete or key==(t,r['record_id_hash']) or any(complete[key][k]!=dep[k] for k in ('body_sha256','classification_sha256')) or complete[key]['criteria_sha256']!=r['criteria_sha256']:
                raise ValueError('alias requires distinct completed source with exact version')
        grouped[(t,r['route'])].append({**raw,'scope_route':r['route'],'scope_dependency':r['dependency'],'scope_input_job_key':r['input_job_key'],'prior_attempt_preserved':r['prior_attempt_preserved']})
    run.mkdir(parents=True)
    for name,rel in [('work','editorial-work'),('adoption','editorial-adoption-current')]:shutil.copy2(root/f'data/verification/{rel}.json',run/f'{name}-before.private.json')
    policy={}
    for name in ('CYCLE_2000_RUNBOOK.md','POLICY_STANCE_MAPPING_V3.md'):
        f=root/'quality/designs/body-review'/name;shutil.copy2(f,run/name);policy[name]=sha(f)
    packets={};b=0
    for (t,route),rows in sorted(grouped.items()):
        for start in range(0,len(rows),20):
            b+=1;part=rows[start:start+20]
            packet={'schema_version':1,'records':part,'criteria':{t:criteria[t]},'input_sha256':fingerprint(part),'automatic_reread_credit':0,
                    'instructions':'Every ID requires its own body/attribution/context judgment and independent audit. Never inherit a same-body source judgment. Paused koshitsu is absent.'}
            checked_packet(packet,root);path=run/f'batch-{b:02d}'/'packet.private.json';dump(path,packet);packets[str(path.relative_to(run))]=sha(path)
    top={'schema_version':1,'prepared_epoch':time.time(),'new_records':len(remaining),'batch_count':b,'packet_hashes':packets,
         'assignments':{'editor':{'editor_a':list(range(1,b+1,2)),'editor_b':list(range(2,b+1,2))},'audit':{'auditor':list(range(1,b+1))}},
         'worktrees':worktrees,'writer_sha256':sha(root/'scripts/short_resolved_review.py'),'prior_runs':prior_hashes,
         'scope_resolution_sha256':scope_summary['resolution_sha256'],'route_counts':dict(Counter(r['route'] for r in remaining)),
         'baseline_work_sha256':sha(run/'work-before.private.json'),'baseline_adoption_sha256':sha(run/'adoption-before.private.json'),
         'canonical_hashes':scope['provenance']['canonical_sha256'],'policy_sha256':policy,'all_ids_independently_audited':True,
         'koshitsu_paused':782,'new_body_review_credit':0}
    top['decision_code_sha256']={'scripts/'+f:sha(root/'scripts'/f) for f in ('short_resolved_review.py','summarize_editorial_batch.py','editorial_acceptance.py','trial_body_review_values.py','editorial_work_registry.py')}
    dump(run/'reservation.json',top);return top
