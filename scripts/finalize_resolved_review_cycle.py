"""Register a resolved-scope cycle as work only, retaining baseline rows exactly."""
from collections import Counter
import hashlib
from pathlib import Path
import yaml

from scripts import editorial_cycle
from scripts.finalize_editorial_continuation import overlay_supplements
from scripts.editorial_work_registry import build_registry, load_registry
from scripts.resolve_remaining_review_scope import load_resolution
from scripts.verify_editorial_hundred import read, sha, dump
from scripts.verify_extra_held_audits import overlay as held_audit_overlay


def boundary_holds(result, wave):
    """Retain manual post-reading criteria flags without altering saved decisions."""
    rows={(r['batch'],r['index']):dict(r) for r in result['journal']}
    overlays=[]
    for path in sorted(wave.glob('editor-*-boundary-flags.private.json')):
        flags=read(path)
        if 'flags' in flags:
            if flags['new_review_credit'] != 0 or flags['preserves_saved_editor_results'] is not True:
                raise ValueError('boundary flags cannot grant credit or rewrite answers')
            items=flags['flags']
        else:
            items=[]
            for item in flags['rows']:
                if item['new_reading_credit'] != 0 or item['recommendation'] != 'criteria_scope_hold':
                    raise ValueError('invalid retrospective boundary recommendation')
                editor_path=wave/f"batch-{item['batch']:02d}"/'editor.private.json'
                if sha(editor_path) != item['editor_sha256']:
                    raise ValueError('boundary editor evidence changed')
                old=rows[(item['batch'],item['index'])]
                if any(old[k] != item[k] for k in ('record_id_hash','body_sha256')):
                    raise ValueError('boundary identity changed')
                items.append({**item,'route':'criteria_needed','uncertain':True,'evidence_sufficient':False})
        for flag in items:
            key=(flag['batch'],flag['index']);old=rows[key]
            actor=read(wave/f'batch-{key[0]:02d}'/'editor-actor.private.json')['actor']
            if actor != flags['actor'] or flag['route'] != 'criteria_needed' or not flag['uncertain'] or flag['evidence_sufficient']:
                raise ValueError('invalid manual boundary flag')
            new={**old,'adoption_status':'hold','adoption_basis':'manual_criteria_boundary_hold',
                 'boundary_flag_sha256':sha(path),'boundary_reason_sha256':hashlib.sha256(flag['reason'].encode()).hexdigest()}
            overlays.append({'source_key':list(key),'old':old,'new':new});rows[key]=new
    return {**result,'journal':[rows[(r['batch'],r['index'])] for r in result['journal']],
            'adoption_counts':dict(Counter(r['adoption_status'] for r in rows.values())),
            'boundary_hold_overlays':overlays}


def collect(root, private, run, supplements=()):
    root, private, run = map(Path, (root, private, run))
    top = read(run/'reservation.json')
    integrity=read(run/'decision-code-integrity.private.json')
    if any(sha(root/f)!=h for f,h in integrity['code_sha256'].items()):raise ValueError('decision code changed')
    if top['new_records'] != 1000 or set(top['waves']) != {'wave-01'}:
        raise ValueError('expected one frozen 1000-record cycle')
    for name in ('work','adoption'):
        if sha(run/f'{name}-before.private.json') != top[f'baseline_{name}_sha256']:
            raise ValueError('baseline snapshot changed')
    if sha(root/'data/verification/editorial-adoption-current.json') != top['baseline_adoption_sha256']:
        raise ValueError('adoption must remain unchanged')
    meta=yaml.safe_load((root/'THEMES.yaml').read_text())['themes']
    for topic,h in top['canonical_hashes'].items():
        if sha(root/meta[topic]['sample_file']) != h: raise ValueError('canonical changed')
    for name,h in top['policy_sha256'].items():
        if sha(run/name) != h or sha(root/'quality/designs/body-review'/name) != h:
            raise ValueError('review policy changed')
    wave=run/'wave-01';reservation=read(wave/'reservation.json')
    if sha(wave/'reservation.json') != top['waves']['wave-01'] or sha(root/'scripts/editorial_cycle.py') != reservation['cycle_writer_sha256']:
        raise ValueError('reservation or writer changed')
    result,_ = editorial_cycle.collect(root,wave)
    result=overlay_supplements(root,run,'wave-01',result,supplements)
    if result['adoption_counts'].get('pending_audit',0):raise ValueError('additional audits remain')
    result=boundary_holds(result,wave)
    result=held_audit_overlay(run,result)
    scope=load_resolution(read(root/'data/verification/editorial-review-scope.json'),private)
    scope_by_id={(r['topic'],r['record_id_hash']):r for r in scope['records']}
    for row in result['journal']:
        source=scope_by_id[(row['topic'],row['record_id_hash'])]
        if source['topic'] in {'koshitsu-tenpakai','takaichi'} or source['route'] != 'new_body_review':
            raise ValueError('ordinary cycle contains paused or special-route record')
        if any(source[k] != row[k] for k in ('body_sha256','classification_sha256')):
            raise ValueError('scope version changed')
    if len({(r['topic'],r['body_sha256'],r['classification_sha256']) for r in result['journal']}) != 1000:
        raise ValueError('duplicate input in cycle')
    return result


def register(root, private, run, report_prefix, supplements=()):
    root,private,run=(Path(p).resolve() for p in (root,private,run))
    workpath=root/'data/verification/editorial-work.json'
    result=collect(root,private,run,supplements)
    baseline=load_registry(run/'work-before.private.json',root,private)
    if sha(workpath) != sha(run/'work-before.private.json'):raise ValueError('work changed since reservation')
    sources=baseline['sources'][:]
    def add(path,kind):
        path=path.resolve();base=root if path.is_relative_to(root) else private
        entry={'storage':'repository' if base==root else 'private','path':str(path.relative_to(base)),'kind':kind,'sha256':sha(path)}
        old=next((s for s in sources if (s['storage'],s['path'])==(entry['storage'],entry['path'])),None)
        if old and old != entry:raise ValueError('source changed')
        if not old:sources.append(entry)
    report=root/'quality/reviews'/f'{report_prefix}-wave.json'
    if report.exists():
        if read(report)!=result:raise ValueError('never overwrite cycle report')
    else:dump(report,result)
    add(report,'journal')
    for path in run.rglob('*'):
        if path.is_file() and path.suffix=='.json':
            is_packet=path.name=='packet.private.json' and path.parent.parent==run/'wave-01'
            add(path,'packet' if is_packet else 'evidence')
    for supplement in result['supplements']:
        for rel in supplement['report']['proofs']:add(Path(supplement['path'])/rel,'evidence')
    updated=build_registry(sources,root,private)
    bykey={r['work_key']:r for r in updated['records']}
    if any(bykey.get(old['work_key']) != old for old in baseline['records']):
        raise ValueError('old work rows changed')
    if len(updated['records']) != len(baseline['records'])+1000:
        raise ValueError('work ID overlap or coverage mismatch')
    added=[r for r in updated['records'] if r['work_key'] not in {x['work_key'] for x in baseline['records']}]
    if any(r['state']=='attempted' for r in added):raise ValueError('new work lacks formal completion')
    summary={'schema_version':1,'scope':'Work registration only; no adoption or canonical application',
             'new_body_reviews':1000,'independent_audits':result['independent_records'],
             'supplemental_audits':result['supplemental_audits'],'adoption_counts':result['adoption_counts'],
             'work_registry_records':len(updated['records']),'old_work_rows_preserved':len(baseline['records']),
             'topic_counts':dict(Counter(r['topic'] for r in result['journal'])),
             'wave_report_sha256':sha(report),'baseline_work_sha256':sha(workpath),
             'canonical_changes':0,'adoption_changes':0,'public_changes':0}
    dump(root/'quality/reviews'/f'{report_prefix}-results.json',summary)
    if sha(workpath) != sha(run/'work-before.private.json'):raise ValueError('work changed during registration')
    dump(workpath,updated);load_registry(workpath,root,private)
    return summary
