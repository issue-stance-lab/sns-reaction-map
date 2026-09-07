"""Rebuild 1,000 decisions from saved evidence and test all accepted corrections."""
import argparse
from collections import Counter
from pathlib import Path
from scripts.assess_prior_editorial import assess_prior
from scripts.verify_editorial_wave import collect_wave,verify_accepted
from scripts.verify_editorial_hundred import read,sha
from scripts.trial_body_review_values import validate


def collect_thousand(root,base):
    root,base=Path(root),Path(base);run=base/'20260907-to1000-v1';items=[assess_prior(root,base)]
    items += [collect_wave(root,run,(n-1)*5+1,min(n*5,38)) for n in range(1,9)]
    journal=[];sources={};proofs={}
    for group,(aggregate,raws) in enumerate(items):
        proofs[str(group)]=aggregate['proofs']
        for r in aggregate['journal']:
            b=r['batch']+group*1000;journal.append({**r,'batch':b});sources[(b,r['index'])]=raws[(r['batch'],r['index'])]
    bykey={(r['topic'],r['record_id_hash']):r for r in journal}
    if len(journal)!=1000 or len(bykey)!=1000:raise ValueError('1,000 unique decisions required')
    supplemental=0
    for name in ['first9','remaining']:
        p=run/f'supplement-{name}.private.json';ap=run/f'supplement-{name}-audit.private.json';packet=read(p);audit=read(ap)
        if audit['source_sha256']!=sha(p):raise ValueError('supplement changed')
        reviews=audit['reviews'];indices=[r['index'] for r in reviews]
        if any(type(i) is not int for i in indices) or sorted(indices)!=list(range(len(packet['records']))):raise ValueError('supplement coverage')
        second={r['index']:r for r in reviews}
        for original in packet['records']:
            row=bykey[(original['topic'],original['record_id_hash'])];review=second[original['index']];raw,criteria=sources[(row['batch'],row['index'])]
            if row['adoption_status']!='pending_audit':raise ValueError('supplement may only resolve pending audit')
            if original['classification']!=raw['classification'] or original['criteria']!=criteria:raise ValueError('supplement input version')
            for k in ['record_id_hash','body_sha256','classification_sha256']:
                if review[k]!=original[k] or original[k]!=row[k]:raise ValueError('supplement identity')
            validate({k:review[k] for k in ['classification','uncertain','reason']},raw['classification'],criteria)
            if type(review.get('evidence_sufficient')) is not bool:raise ValueError('missing supplement evidence assessment')
            supported=not review['uncertain'] and review['evidence_sufficient'] and review['classification']==row['proposed']
            row['adoption_status']='accepted' if supported else 'hold';row['adoption_basis']='supplemental_parent_review' if supported else 'supplemental_uncertainty';supplemental+=1
        proofs['supplement-'+name]={'packet':sha(p),'audit':sha(ap)}
    from scripts.reassess_editorial_criteria import verify_reassessment, BASIS, EVENT
    ledger, reassessment = verify_reassessment(root, run)
    if ledger['policy_sha256']!=sha(root/'scripts/editorial_acceptance.py'):raise ValueError('adoption policy changed')
    saved={(r['topic'],r['record_id_hash']):r for r in ledger['records']}
    if len(ledger['records'])!=1000 or set(saved)!=set(bykey):raise ValueError('adoption ledger coverage')
    for key,row in bykey.items():
        if any(saved[key].get(k)!=row.get(k) for k in ['body_sha256','classification_sha256','current','proposed','route','reason_sha256','adoption_status','adoption_basis']):raise ValueError('adoption ledger differs from evidence')
    if reassessment:
        for change in reassessment['records']:
            key=(change['before']['topic'],change['before']['record_id_hash'])
            bykey[key].update(adoption_status='accepted', adoption_basis=BASIS, reassessment_event=EVENT)
        proofs['reassessment'] = {'history': sha(root/'quality/reviews/2026-09-07-criteria-reassessment59.json')}
    return {'schema_version':1,'reviewed_records':1000,'new_records':760,'routes':dict(Counter(r['route'] for r in journal)),
            'adoption_counts':dict(Counter(r['adoption_status'] for r in journal)),'journal':journal,'proofs':proofs,'supplemental_reviews':supplemental,
            'canonical_changes':0,'registered_reread_increment':0,'policy_sha256':sha(root/'scripts/editorial_acceptance.py'),'ledger_sha256':sha(root/'data/verification/editorial-adoption.json')},sources


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['root','base','out']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=verify_accepted(a.root,a.base,a.out,collect_thousand(a.root,a.base));print(r['adoption_counts'])
