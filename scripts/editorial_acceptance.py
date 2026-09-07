"""Separate evidence-backed editorial adoption from canonical/public application."""
from collections import Counter
from scripts.summarize_editorial_batch import summarize, verified_reviews

POLICY = 'editorial-adoption-v2'


def decide(journal, editor, audit, gate):
    if type(gate.get('systemic_criteria_issue')) is not bool:
        raise ValueError('missing quality gate')
    conflicts = gate.get('reason_conflicts')
    if not isinstance(conflicts, list) or any(type(i) is not int for i in conflicts):
        raise ValueError('invalid reason conflicts')
    topics = set(gate.get('additional_audit_topics', []))
    # A failing retained sample blocks other unaudited retains in that topic.
    for row in journal:
        if row['first_route'] == 'no_change' and row['independently_checked'] and (row['route'] == 'hold' or editor[row['index']].get('evidence_sufficient') is not True or audit.get(row['index'],{}).get('evidence_sufficient') is not True or row['index'] in conflicts):
            topics.add(row['topic'])
    result = []
    for row in journal:
        i = row['index']; first = editor[i]; second = audit.get(i)
        if type(first.get('evidence_sufficient')) is not bool or (second and type(second.get('evidence_sufficient')) is not bool):
            raise ValueError('explicit evidence assessment required')
        status = 'accepted'; basis = 'independent' if second else 'sampled_batch'
        if row['route'] == 'hold': status = 'hold'; basis = 'uncertain_or_disagreement'
        elif row['route'] not in {'retain_candidate', 'change_candidate'}:
            raise ValueError('pending route cannot be adopted')
        elif not first['evidence_sufficient'] or (second and not second['evidence_sufficient']) or i in conflicts:
            status = 'pending_evidence'; basis = 'insufficient_or_conflicting_reason'
        elif gate['systemic_criteria_issue']:
            status = 'pending_evidence'; basis = 'criteria_issue'
        elif not second:
            samples = [r for r in journal if r['first_route'] == 'no_change' and r['independently_checked']]
            if row['route'] == 'change_candidate' or not samples or row['topic'] in topics:
                status = 'pending_audit'; basis = 'additional_audit_required'
        result.append({**row, 'adoption_status': status, 'adoption_basis': basis,
                       'policy_version': POLICY, 'canonical_applied': False,
                       'counts_as_registered_editorial_reread': False})
    return result


def assess_batch(packet, editor, audit, gate):
    summary = summarize(packet, editor, audit)
    first = verified_reviews(packet, editor, list(range(len(packet['records']))))
    second = verified_reviews(packet, audit, summary['audit_indices'])
    summary['journal'] = decide(summary['journal'], first, second, gate)
    summary['adoption_counts'] = dict(Counter(r['adoption_status'] for r in summary['journal']))
    return summary
