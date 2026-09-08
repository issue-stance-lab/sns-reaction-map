"""Single-topic short packets with every post independently audited.

Used for the resolved final remainder, including distinct-ID verifications.
It never inherits an author's judgment from a same-body post.
"""
from collections import Counter
import hashlib
from pathlib import Path
import time

from scripts.verify_editorial_hundred import read,sha,dump
from scripts.summarize_editorial_batch import verified_reviews
from scripts.editorial_acceptance import decide
from scripts.editorial_work_registry import checked_packet


def packet(run,batch):
    run=Path(run);reservation=read(run/'reservation.json')
    if type(batch) is not int or not 1 <= batch <= reservation['batch_count']:
        raise ValueError('unreserved batch')
    path=run/f'batch-{batch:02d}'/'packet.private.json'
    if sha(path) != reservation['packet_hashes'][str(path.relative_to(run))]:
        raise ValueError('packet changed')
    value=read(path)
    if not 1 <= len(value['records']) <= 20 or len({r['topic'] for r in value['records']}) != 1:
        raise ValueError('short single-topic packet required')
    if any(r['topic'] in {'koshitsu-tenpakai','takaichi'} for r in value['records']):
        raise ValueError('paused or private theme forbidden')
    return value


def bind(run,batch,role,actor):
    run=Path(run);r=read(run/'reservation.json')
    if batch not in r['assignments'][role].get(actor,[]):raise ValueError('not assigned')
    if Path.cwd().resolve() != Path(r['worktrees'][actor]).resolve():raise ValueError('wrong worktree')
    value={'actor':actor,'worktree':str(Path.cwd().resolve()),'reservation_sha256':sha(run/'reservation.json')}
    path=run/f'batch-{batch:02d}'/(role+'-actor.private.json')
    if path.exists():
        if read(path) != value:raise ValueError('actor changed')
    else:dump(path,value)


def show(run,batch,role,actor):
    run=Path(run);p=packet(run,batch);bind(run,batch,role,actor)
    if role=='audit' and not (run/f'batch-{batch:02d}'/'editor.private.json').exists():
        raise ValueError('editor not yet saved')
    marker=run/f'batch-{batch:02d}'/(role+'-start.private.json')
    if not marker.exists():dump(marker,{'started_epoch':time.time(),'packet_sha256':sha(marker.parent/'packet.private.json')})
    return {'records':[{'index':i,'topic':r['topic'],'text':r['text']} for i,r in enumerate(p['records'])],
            'criteria':p['criteria'],'all_records_require_independent_audit':True}


def save(run,batch,role,actor,values):
    run=Path(run);p=packet(run,batch);bind(run,batch,role,actor);d=run/f'batch-{batch:02d}'
    final=d/(role+'.private.json');draft=d/(role+'-draft.private.json')
    if final.exists() or draft.exists():raise ValueError('never overwrite saved attempt')
    start=read(d/(role+'-start.private.json'));dump(draft,{'values':values,'recorded_epoch':time.time()})
    rows=[]
    for v in values:
        if len(v)!=8:raise ValueError('eight explicit fields required')
        i,relevant,opinion,issue,stance,uncertain,evidence,reason=v
        if type(i) is not int or not 0 <= i < len(p['records']) or type(evidence) is not bool:
            raise ValueError('invalid index or evidence assessment')
        raw=p['records'][i]
        rows.append({**{k:raw[k] for k in ('record_id_hash','body_sha256','classification_sha256')},'index':i,
                     'classification':dict(is_relevant=relevant,is_opinion=opinion,main_issue=issue,stance=stance),
                     'uncertain':uncertain,'evidence_sufficient':evidence,'reason':reason})
    result={**start,'finished_epoch':time.time(),'reviews':rows,'identity_writer':'short_resolved_review.save'}
    verified_reviews(p,result,list(range(len(p['records']))));dump(final,result)
    return len(rows)


def assess_all(p,editor,audit,gate):
    expected=list(range(len(p['records'])))
    first=verified_reviews(p,editor,expected);second=verified_reviews(p,audit,expected);journal=[]
    for i,raw in enumerate(p['records']):
        e,a=first[i],second[i]
        route='hold' if e['uncertain'] or a['uncertain'] or e['classification']!=a['classification'] else 'change_candidate' if e['changes'] else 'retain_candidate'
        journal.append({**{k:raw[k] for k in ('topic','record_id_hash','body_sha256','classification_sha256')},
                        'index':i,'current':raw['classification'],'proposed':e['classification'],'changes':e['changes'],
                        'route':route,'first_route':e['route'],'independently_checked':True,'independent_proposed':a['classification'],
                        'reason_sha256':hashlib.sha256(e['reason'].encode()).hexdigest(),
                        'independent_reason_sha256':hashlib.sha256(a['reason'].encode()).hexdigest(),
                        'canonical_applied':False,'counts_as_registered_editorial_reread':False})
    rows=decide(journal,first,second,gate)
    return {'schema_version':1,'records':len(expected),'independent_records':len(expected),'journal':rows,
            'adoption_counts':dict(Counter(r['adoption_status'] for r in rows))}


def comparison(run,batch,actor):
    run=Path(run);bind(run,batch,'audit',actor);d=run/f'batch-{batch:02d}';p=packet(run,batch)
    e=read(d/'editor.private.json');a=read(d/'audit.private.json');expected=list(range(len(p['records'])))
    first=verified_reviews(p,e,expected);second=verified_reviews(p,a,expected)
    return {'rows':[{'index':i,'editor':first[i],'audit':second[i]} for i in expected]}


def gate(run,batch,actor,reason_conflicts,notes):
    run=Path(run);bind(run,batch,'audit',actor);d=run/f'batch-{batch:02d}'
    if (d/'quality_gate.private.json').exists():raise ValueError('gate already saved')
    p=packet(run,batch)
    if len(set(reason_conflicts)) != len(reason_conflicts) or any(type(i) is not int or not 0 <= i < len(p['records']) for i in reason_conflicts):
        raise ValueError('invalid conflicts')
    value={'reason_conflicts':reason_conflicts,'systemic_criteria_issue':False,'additional_audit_topics':[],'notes':notes}
    result=assess_all(p,read(d/'editor.private.json'),read(d/'audit.private.json'),value)
    dump(d/'quality_gate.private.json',value);return result['adoption_counts']


def collect(root,run):
    root,run=map(Path,(root,run));r=read(run/'reservation.json')
    if sha(root/'scripts/short_resolved_review.py') != r['writer_sha256']:raise ValueError('writer changed')
    if any(sha(root/f)!=h for f,h in r['decision_code_sha256'].items()):raise ValueError('decision dependency changed')
    n=r['batch_count'];journal=[];proofs={'reservation.json':sha(run/'reservation.json')}
    for role in ('editor','audit'):
        if sorted(b for bs in r['assignments'][role].values() for b in bs) != list(range(1,n+1)):
            raise ValueError('assignment coverage mismatch')
    for actor,bs in r['assignments']['editor'].items():
        if set(bs)&set(r['assignments']['audit'].get(actor,[])):raise ValueError('self audit')
    for b in range(1,n+1):
        p=packet(run,b);checked_packet(p,root);d=run/f'batch-{b:02d}'
        for role in ('editor','audit'):
            value=read(d/(role+'.private.json'));start=read(d/(role+'-start.private.json'));draft=read(d/(role+'-draft.private.json'))
            actor=next(a for a,bs in r['assignments'][role].items() if b in bs)
            if read(d/(role+'-actor.private.json')) != {'actor':actor,'worktree':r['worktrees'][actor],'reservation_sha256':sha(run/'reservation.json')}:raise ValueError('actor binding mismatch')
            if value['packet_sha256'] != sha(d/'packet.private.json') or value['packet_sha256'] != start['packet_sha256'] or value['started_epoch'] != start['started_epoch'] or not value['started_epoch'] <= draft['recorded_epoch'] <= value['finished_epoch']:raise ValueError('timing or packet mismatch')
            compact=[[x['index'],*[x['classification'][k] for k in ('is_relevant','is_opinion','main_issue','stance')],x['uncertain'],x['evidence_sufficient'],x['reason']] for x in value['reviews']]
            if compact != draft['values']:raise ValueError('draft mismatch')
        result=assess_all(p,read(d/'editor.private.json'),read(d/'audit.private.json'),read(d/'quality_gate.private.json'))
        for row,raw in zip(result['journal'],p['records']):journal.append({**row,'batch':b,'scope_route':raw['scope_route'],'scope_dependency':raw.get('scope_dependency')})
        for f in d.glob('*.private.json'):proofs[str(f.relative_to(run))]=sha(f)
    if len(journal) != r['new_records'] or len({(x['topic'],x['record_id_hash']) for x in journal}) != len(journal):raise ValueError('coverage or duplicate ID')
    return {'schema_version':1,'new_records':len(journal),'independent_records':len(journal),'journal':journal,
            'adoption_counts':dict(Counter(x['adoption_status'] for x in journal)),'proofs':proofs}
