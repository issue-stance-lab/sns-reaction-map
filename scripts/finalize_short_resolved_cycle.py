"""Register final short packets, preserving old attempts as explicit transitions."""
from collections import Counter
from pathlib import Path
import yaml

from scripts import short_resolved_review
from scripts.editorial_work_registry import build_registry,load_registry
from scripts.verify_editorial_hundred import read,sha,dump


def register(root,private,run,prefix):
    root,private,run=(Path(p).resolve() for p in (root,private,run));top=read(run/'reservation.json')
    result=short_resolved_review.collect(root,run)
    if result['new_records']!=352 or result['independent_records']!=352 or result['adoption_counts'].get('pending_audit',0):raise ValueError('incomplete short remainder')
    workpath=root/'data/verification/editorial-work.json'
    if sha(workpath)!=top['baseline_work_sha256'] or sha(run/'work-before.private.json')!=top['baseline_work_sha256']:raise ValueError('work baseline changed')
    if sha(root/'data/verification/editorial-adoption-current.json')!=top['baseline_adoption_sha256'] or sha(run/'adoption-before.private.json')!=top['baseline_adoption_sha256']:raise ValueError('adoption changed')
    meta=yaml.safe_load((root/'THEMES.yaml').read_text())['themes']
    for t,h in top['canonical_hashes'].items():
        if sha(root/meta[t]['sample_file'])!=h:raise ValueError('canonical changed')
    for name,h in top['policy_sha256'].items():
        if sha(run/name)!=h or sha(root/'quality/designs/body-review'/name)!=h:raise ValueError('policy changed')
    baseline=load_registry(workpath,root,private);sources=baseline['sources'][:]
    report=root/'quality/reviews'/f'{prefix}-wave.json'
    if report.exists():
        if read(report)!=result:raise ValueError('never overwrite short report')
    else:dump(report,result)
    def add(path,kind):
        path=path.resolve();base=root if path.is_relative_to(root) else private
        entry={'storage':'repository' if base==root else 'private','path':str(path.relative_to(base)),'sha256':sha(path),'kind':kind}
        if any((s['storage'],s['path'])==(entry['storage'],entry['path']) for s in sources):raise ValueError('duplicate evidence path')
        sources.append(entry)
    add(report,'journal')
    for path in run.rglob('*'):
        if path.is_file() and path.suffix=='.json':
            is_packet=path.name=='packet.private.json' and path.parent.parent==run
            add(path,'packet' if is_packet else 'evidence')
    updated=build_registry(sources,root,private);bykey={r['work_key']:r for r in updated['records']}
    resumed={(r['topic'],r['record_id_hash']) for r in result['journal'] if r['scope_route']=='resume_unfinished_review'}
    if len(resumed)!=56 or len(updated['records'])!=len(baseline['records'])+296:raise ValueError('short coverage differs')
    transitions=[]
    for old in baseline['records']:
        new=bykey[old['work_key']]
        if (old['topic'],old['record_id_hash']) in resumed:
            if old['state']!='attempted' or new['state']=='attempted' or not set(old['evidence'])<=set(new['evidence']) or old['scope_only_audits']!=new['scope_only_audits']:raise ValueError('old attempt history lost')
            if any(old[k]!=new[k] for k in ('body_sha256','classification_sha256','criteria_sha256','canonical_applied','counts_as_registered_editorial_reread')):raise ValueError('resumed identity or credit changed')
            transitions.append({'old':old,'new':new})
        elif old!=new:raise ValueError('unrelated baseline row changed')
    routes=Counter(r['scope_route'] for r in result['journal']);aliases=sum(n for route,n in routes.items() if route.startswith('verify_distinct_id_'))
    if aliases!=127:raise ValueError('alias ID verification coverage differs')
    summary={'schema_version':1,'new_body_reviews':352-aliases,'distinct_id_verifications':aliases,'completed_target_records':352,
             'independent_audits':352,'supplemental_audits':0,'adoption_counts':result['adoption_counts'],'route_counts':dict(routes),
             'work_registry_records':len(updated['records']),'old_attempt_transitions':transitions,'canonical_changes':0,'adoption_changes':0,'public_changes':0}
    dump(root/'quality/reviews'/f'{prefix}-results.json',summary)
    if sha(workpath)!=top['baseline_work_sha256']:raise ValueError('work changed during registration')
    dump(workpath,updated);load_registry(workpath,root,private)
    return summary
