"""Frozen 20-record editorial packets with programmatic identity and timing."""
import argparse
import json
import time
from pathlib import Path
from scripts.verify_editorial_hundred import read, sha, dump
from scripts.summarize_editorial_batch import verified_reviews, select_audit
from scripts.editorial_acceptance import assess_batch


def batch_dir(run, batch):
    if type(batch) is not int or not 1 <= batch <= 50:
        raise ValueError('batch must be 1..50')
    return Path(run) / f'batch-{batch:02d}'


def packet_for(run, batch):
    d = batch_dir(run, batch); packet = read(d / 'packet.private.json')
    reservation = read(Path(run) / 'reservation.json')
    if sha(d / 'packet.private.json') != reservation['packet_hashes'][str((d / 'packet.private.json').relative_to(run))]:
        raise ValueError('reserved packet changed')
    return packet


def targets(run, batch, role):
    packet = packet_for(run, batch)
    if role == 'editor':
        return list(range(20))
    if role != 'audit':
        raise ValueError('unknown role')
    first = verified_reviews(packet, read(batch_dir(run, batch) / 'editor.private.json'), list(range(20)))
    return select_audit(first)


def show(run, batch, role, with_criteria=False):
    packet = packet_for(run, batch); indices = targets(run, batch, role)
    marker = batch_dir(run, batch) / (role + '-start.private.json')
    if not marker.exists():
        dump(marker, {'started_epoch': time.time(), 'packet_sha256': sha(batch_dir(run, batch) / 'packet.private.json')})
    result = {'batch': batch, 'role': role, 'records': [
        {'index': i, 'topic': packet['records'][i]['topic'], 'text': packet['records'][i]['text'],
         'current': packet['records'][i]['classification']} for i in indices]}
    if with_criteria:
        result['criteria'] = packet['criteria']
    return result


def save(run, batch, role, values, *, systemic_criteria_issue=False, notes=''):
    """Values: [index, relevant, opinion, issue, stance, uncertain, evidence, reason]."""
    d = batch_dir(run, batch); packet = packet_for(run, batch)
    path = d / (role + '.private.json'); draft = d / (role + '-draft.private.json')
    if path.exists() or draft.exists():
        raise ValueError('never overwrite a saved attempt')
    started = read(d / (role + '-start.private.json'))
    dump(draft, {'values': values, 'recorded_epoch': time.time()})
    reviews = []
    for value in values:
        if len(value) != 8 or type(value[0]) is not int or not 0 <= value[0] < 20:
            raise ValueError('invalid compact response')
        i, relevant, opinion, issue, stance, uncertain, evidence, reason = value
        raw = packet['records'][i]
        reviews.append({k: raw[k] for k in ['record_id_hash', 'body_sha256', 'classification_sha256']} |
                       {'index': i, 'classification': {'is_relevant': relevant, 'is_opinion': opinion,
                        'main_issue': issue, 'stance': stance}, 'uncertain': uncertain,
                        'evidence_sufficient': evidence, 'reason': reason})
        if type(evidence) is not bool:
            raise ValueError('evidence assessment must be boolean')
    output = {'packet_sha256': started['packet_sha256'], 'started_epoch': started['started_epoch'],
              'finished_epoch': time.time(), 'reviews': reviews, 'identity_writer': 'continuous_editorial_review.save'}
    verified_reviews(packet, output, targets(run, batch, role))
    if type(systemic_criteria_issue) is not bool:
        raise ValueError('explicit systemic assessment required')
    dump(path, output)
    if role == 'editor':
        dump(d / 'editor-flags.private.json', {'systemic_criteria_issue': systemic_criteria_issue, 'notes': notes})
    print('SAVED', batch, role, len(reviews), flush=True)


def comparison(run, batch):
    d = batch_dir(run, batch); packet = packet_for(run, batch)
    first = verified_reviews(packet, read(d / 'editor.private.json'), list(range(20)))
    second = verified_reviews(packet, read(d / 'audit.private.json'), targets(run, batch, 'audit'))
    return {'batch': batch, 'editor_flags': read(d / 'editor-flags.private.json'), 'rows': [
        {'index': i, 'editor': {k: first[i][k] for k in ['classification', 'uncertain', 'evidence_sufficient', 'reason']},
         'audit': {k: second[i][k] for k in ['classification', 'uncertain', 'evidence_sufficient', 'reason']}}
        for i in second]}


def gate(run, batch, *, reason_conflicts, systemic_criteria_issue, notes):
    d = batch_dir(run, batch)
    if (d / 'quality_gate.private.json').exists():
        raise ValueError('gate already saved')
    if type(systemic_criteria_issue) is not bool or any(type(i) is not int or not 0 <= i < 20 for i in reason_conflicts):
        raise ValueError('invalid quality gate')
    g = {'reason_conflicts': reason_conflicts,
         'systemic_criteria_issue': systemic_criteria_issue or read(d / 'editor-flags.private.json')['systemic_criteria_issue'],
         'additional_audit_topics': [], 'notes': notes}
    result = assess_batch(packet_for(run, batch), read(d / 'editor.private.json'), read(d / 'audit.private.json'), g)
    dump(d / 'quality_gate.private.json', g)
    print('GATED', batch, result['adoption_counts'], flush=True)


def ready(run):
    batches = []
    for batch in range(1, 51):
        d = batch_dir(run, batch)
        if (d / 'editor.private.json').exists() and (d / 'editor-flags.private.json').exists() and not (d / 'quality_gate.private.json').exists():
            batches.append(batch)
    return {'ready_batches': batches, 'gated': sum((batch_dir(run, n) / 'quality_gate.private.json').exists() for n in range(1, 51))}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['show', 'compare', 'ready'])
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--batch', type=int)
    p.add_argument('--role', choices=['editor', 'audit'], default='editor')
    p.add_argument('--with-criteria', action='store_true')
    a = p.parse_args()
    value = ready(a.run) if a.action == 'ready' else comparison(a.run, a.batch) if a.action == 'compare' else show(a.run, a.batch, a.role, a.with_criteria)
    print(json.dumps(value, ensure_ascii=False))
