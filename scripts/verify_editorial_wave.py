"""Collect a reserved 20..100-record wave, assess adoption, test accepted changes."""
import argparse
from collections import Counter
from pathlib import Path
from scripts.editorial_acceptance import assess_batch
from scripts.prepare_editorial_candidate_text import prepare_conclusion
from scripts.verify_editorial_hundred import read, sha, dump, verify


def collect_wave(root, run, start, stop):
    root,run=Path(root),Path(run)
    if not 1<=start<=stop<=38 or stop-start>=5:raise ValueError('wave must contain 1..5 reserved batches')
    reservation=read(run/'reservation.json');journal=[];sources={};proofs={};seen=set();batches=[]
    for n in range(start,stop+1):
        d=run/f'batch-{n:02d}';packet=read(d/'packet.private.json')
        if sha(d/'packet.private.json')!=reservation['packet_hashes'][str((d/'packet.private.json').relative_to(run))]:raise ValueError('reservation changed')
        if len(packet['records'])!=20:raise ValueError('batch size changed')
        result=assess_batch(packet,read(d/'editor.private.json'),read(d/'audit.private.json'),read(d/'quality_gate.private.json'))
        for row in result['journal']:
            raw=packet['records'][row['index']];key=(row['topic'],row['body_sha256'],row['classification_sha256'])
            if key in seen:raise ValueError('duplicate input')
            seen.add(key);journal.append({**row,'batch':n});sources[(n,row['index'])]=(raw,packet['criteria'][row['topic']])
        batches.append({'batch':n,**{k:result[k] for k in ['records','independent_records','routes','adoption_counts']}})
        for f in ['packet.private.json','editor.private.json','audit.private.json','quality_gate.private.json']:proofs[str((d/f).relative_to(run))]=sha(d/f)
    aggregate={'schema_version':1,'new_records':len(journal),'batches':batches,'journal':journal,'routes':dict(Counter(r['route'] for r in journal)),
               'adoption_counts':dict(Counter(r['adoption_status'] for r in journal)),'independent_records':sum(b['independent_records'] for b in batches),
               'proofs':proofs,'policy_sha256':sha(root/'scripts/editorial_acceptance.py'),'canonical_changes':0,'registered_reread_increment':0,'codex_tokens':None,'local_model_calls':0}
    return aggregate,sources


def verify_accepted(root, run, out, collected):
    aggregate,sources=collected
    # Preserve the editorial journal; only accepted changes enter the candidate.
    candidate={**aggregate,'journal':[{**r,'route':r['route'] if r['adoption_status']=='accepted' else 'hold'} for r in aggregate['journal']]}
    tested=verify(root,run,out,collected=(candidate,sources),prepare_candidate=prepare_conclusion)
    result={**aggregate,'generation':tested['generation']}
    dump(Path(out)/'report.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['root','run','out']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--start',type=int,required=True);p.add_argument('--stop',type=int,required=True)
    a=p.parse_args();r=verify_accepted(a.root,a.run,a.out,collect_wave(a.root,a.run,a.start,a.stop));print(r['adoption_counts'])
