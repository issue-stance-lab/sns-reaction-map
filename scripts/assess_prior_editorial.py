"""Reuse prior 240 review records and explicit parent evidence assessment."""
from collections import Counter,defaultdict
from pathlib import Path
from scripts.verify_integrated_editorial_candidates import assemble
from scripts.verify_editorial_hundred import collect,read,sha
from scripts.editorial_acceptance import decide


def assess_prior(root, base):
    root,base=Path(root),Path(base);a,s=assemble(root,base);b,t=collect(base/'20260907-parallel100-v1')
    proof=base/'20260907-to1000-v1/prior147.private.json';assessment_path=base/'20260907-to1000-v1/prior147-assessment.private.json';assessment=read(assessment_path)
    if assessment['source_sha256']!=sha(proof):raise ValueError('parent evidence assessment changed')
    originals=read(proof)['records'];assessments=assessment['reviews']
    if len(originals)!=147 or len(assessments)!=147 or [r['ordinal'] for r in assessments]!=list(range(147)):raise ValueError('assessment coverage')
    evidence={}
    for original,decision in zip(originals,assessments):
        if original['record_id_hash']!=decision['record_id_hash'] or type(decision['evidence_sufficient']) is not bool:raise ValueError('assessment identity')
        evidence[(original['topic'],original['record_id_hash'])]=(original,decision)
    journal=[];sources={};offset=0
    for aggregate,raws in [(a,s),(b,t)]:
        grouped=defaultdict(list)
        for row in aggregate['journal']:
            row={**row,'first_route':row.get('first_route','candidate' if row['changes'] else 'no_change')}
            grouped[row['batch']].append(row)
        for batch,rows in sorted(grouped.items()):
            editor={};audit={}
            for r in rows:
                key=(r['topic'],r['record_id_hash']);sufficient=False
                if r['route']!='hold':
                    original,decision=evidence[key]
                    if any(original[k]!=r[k] for k in ['body_sha256','classification_sha256']) or original['classification']!=r['proposed']:raise ValueError('prior classification changed')
                    sufficient=decision['evidence_sufficient']
                editor[r['index']]={'evidence_sufficient':sufficient}
                if r['independently_checked']:audit[r['index']]={'evidence_sufficient':sufficient}
            decisions=decide(rows,editor,audit,{'systemic_criteria_issue':False,'reason_conflicts':[]})
            for r in decisions:
                journal.append({**r,'batch':batch+offset});sources[(batch+offset,r['index'])]=raws[(batch,r['index'])]
        offset=100
    return {'schema_version':1,'new_records':0,'reviewed_records':240,'journal':journal,'routes':dict(Counter(r['route'] for r in journal)),
            'adoption_counts':dict(Counter(r['adoption_status'] for r in journal)),
            'proofs':{'prior147.private.json':sha(proof),'prior147-assessment.private.json':sha(assessment_path)},
            'canonical_changes':0,'registered_reread_increment':0,'policy_sha256':sha(root/'scripts/editorial_acceptance.py')},sources
