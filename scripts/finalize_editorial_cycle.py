"""Replay new waves plus supplemental overlays, retaining every prior decision."""
import argparse
import yaml
from collections import Counter
from pathlib import Path
from scripts import editorial_cycle as cycle_review
from scripts import supplemental_editorial_audit as supplemental
from scripts.verify_continuous_editorial import combine as previous_combine
from scripts.verify_editorial_hundred import read,sha,dump
from scripts.editorial_work_registry import fingerprint,load_registry,build_registry


def apply_overlay(journal,report):
    bykey={(r['batch'],r['index']):r for r in journal}
    if len(bykey)!=len(journal):raise ValueError('duplicate source keys')
    seen=set()
    for change in report['overlay']:
        key=tuple(change['source_key'])
        if key in seen or key not in bykey or bykey[key]!=change['old']:raise ValueError('overlay does not match original decision')
        seen.add(key)
        new=change['new']
        if change['old']['adoption_status']!='pending_audit' or (new['batch'],new['index'])!=key:raise ValueError('invalid overlay identity or source state')
        for field in ['topic','record_id_hash','body_sha256','classification_sha256','proposed','current','changes','route']:
            if new[field]!=change['old'][field]:raise ValueError('supplement cannot alter prior proposal or identity')
        bykey[key]=new
    return [bykey[(r['batch'],r['index'])] for r in journal]


def collect(root,base,run,waves=2,require_supplements=True):
    root,base,run=map(Path,[root,base,run]);reservation=read(run/'reservation.json')
    if reservation!=read(root/'quality/reviews/2026-09-07-cycle-next2000-reservation-v2.json'):raise ValueError('top-level reservation differs from registered manifest')
    metadata=yaml.safe_load((root/'THEMES.yaml').read_text())['themes']
    if any(sha(root/metadata[t]['sample_file'])!=h for t,h in reservation['canonical_hashes'].items()):raise ValueError('canonical snapshot changed')
    invalidation=base.parent/reservation['retry_of']/'invalidated.private.json'
    if sha(invalidation)!=reservation['invalid_attempt_sha256']:raise ValueError('invalid-attempt history changed')
    baseline=read(run/'adoption-before.private.json')
    if sha(run/'adoption-before.private.json')!=reservation['baseline_adoption_sha256']:raise ValueError('baseline changed')
    prior,sources=previous_combine(root,base,base/'20260907-next1000-sol-v1')
    if prior['journal']!=baseline['records']:raise ValueError('baseline does not replay')
    journal=prior['journal'];reports={};proofs={'reservation':sha(run/'reservation.json'),'baseline':sha(run/'adoption-before.private.json')}
    def supplement_if_ready(name,rows,batches=None):
        projection=rows if batches is None else [r for r in rows if r['batch'] in batches]
        folder=run/name
        if not folder.exists():
            if not any(r['adoption_status']=='pending_audit' for r in projection):return rows
            if require_supplements:raise ValueError('required supplement missing: '+name)
            return rows
        ready=supplemental.ready(folder)
        if ready['pending_batches'] or ready['comparable_batches']:
            if require_supplements:raise ValueError('supplement unfinished: '+name)
            return rows
        if read(folder/'baseline.private.json')['source_journal_sha256']!=fingerprint(projection):raise ValueError('supplement source journal changed')
        result=supplemental.collect(root,folder);reports[name]=result
        return apply_overlay(rows,result)
    journal=supplement_if_ready('supplement-baseline',journal)
    independent=0
    for n in range(1,waves+1):
        name=f'wave-{n:02d}';folder=run/name
        if sha(folder/'reservation.json')!=reservation['waves'][name]:raise ValueError('wave reservation changed')
        if sha(root/'scripts/editorial_cycle.py')!=read(folder/'reservation.json')['cycle_writer_sha256']:raise ValueError('cycle writer changed')
        result,raws=cycle_review.collect(root,folder);reports[name]=result;independent+=result['independent_records']
        rows=result['journal']
        for part,batches in enumerate([range(1,21),range(21,41),range(41,51)],1):
            rows=supplement_if_ready('supplement-'+name+f'-part-{part:02d}',rows,batches)
        if require_supplements and any(r['adoption_status']=='pending_audit' for r in rows):raise ValueError('wave still needs supplemental audit')
        offset=n*100000+100000
        journal += [{**r,'batch':r['batch']+offset} for r in rows]
        sources.update({(b+offset,i):v for (b,i),v in raws.items()})
    expected=2000+waves*1000
    if len(journal)!=expected or len({(r['topic'],r['record_id_hash']) for r in journal})!=expected:raise ValueError('duplicate records')
    if len({(r['topic'],r['body_sha256'],r['classification_sha256']) for r in journal})!=expected:raise ValueError('duplicate input')
    result={'schema_version':1,'reviewed_records':expected,'new_records':waves*1000,'journal':journal,'adoption_counts':dict(Counter(r['adoption_status'] for r in journal)),
            'independent_new_records':independent,'supplemental_audits':sum(v['supplemental_audits'] for k,v in reports.items() if k.startswith('supplement-')),
            'accepted_routes':dict(Counter(r['route'] for r in journal if r['adoption_status']=='accepted')),
            'proofs':proofs,'canonical_changes':0,'registered_reread_increment':0,'codex_tokens':None}
    return result,sources,reports


def register(root,base,run,waves=2):
    root,base,run=map(Path,[root,base,run]);result,_,reports=collect(root,base,run,waves)
    private=base.parent;workpath=root/'data/verification/editorial-work.json';work=load_registry(workpath,root,private);sources=work['sources'][:]
    def add(path,storage,kind):
        entry={'path':str(path.relative_to(root if storage=='repository' else private)),'storage':storage,'kind':kind,'sha256':sha(path)}
        existing=next((s for s in sources if (s['path'],s['storage'])==(entry['path'],entry['storage'])),None)
        if existing is not None and existing!=entry:raise ValueError('registered evidence changed')
        if existing is None:sources.append(entry)
    add(private/read(run/'reservation.json')['retry_of']/'invalidated.private.json','private','evidence')
    report_refs=[]
    for name,report in reports.items():
        path=root/'quality/reviews'/('2026-09-07-cycle-'+name+'.json')
        if path.exists() and read(path)!=report:raise ValueError('never overwrite registered report')
        dump(path,report);add(path,'repository','journal' if name.startswith('wave-') else 'evidence')
        report_refs.append({'path':str(path.relative_to(root)),'sha256':sha(path)})
        for p in (run/name).rglob('*.json'):add(p,'private','evidence')
    updated=build_registry(sources,root,private)
    if len(updated['records'])!=4080 or updated['counts'].get('attempted',0)!=80+(2-waves)*1000:raise ValueError('work coverage mismatch')
    view={'schema_version':1,'scope':'Current editorial adoption; supplemental changes preserve original proposals and history; no canonical application.',
          'reviewed_records':result['reviewed_records'],'counts':result['adoption_counts'],'sources':report_refs,
          'baseline_sha256':sha(run/'adoption-before.private.json'),'records':result['journal'],'canonical_applied':0,'registered_reread_increment':0}
    dump(workpath,updated);dump(root/'data/verification/editorial-adoption-current.json',view)
    load_registry(workpath,root,private)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['root','base','run']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--waves',type=int,choices=[1,2],default=2);a=p.parse_args();r=register(a.root,a.base,a.run,a.waves);print(r['reviewed_records'],r['adoption_counts'])
