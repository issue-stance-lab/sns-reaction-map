#!/usr/bin/env python3
"""Independently resolve frozen pending-audit editorial decisions.

The run is private and append-only.  It produces an overlay for the source
journal; it never edits that journal, canonical samples, or public files.
"""
import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import json
from pathlib import Path
import time

from scripts.editorial_work_registry import checked_packet, fingerprint
from scripts.trial_body_review_values import validate
from scripts.verify_editorial_hundred import dump, read, sha


WRITER = 'supplemental_editorial_audit.save'
BASELINE = 'baseline.private.json'
RESERVATION = 'reservation.json'


def _run(out):
    return Path(out)


def _batch_dir(out, batch):
    if type(batch) is not int or batch < 1:
        raise ValueError('batch must be a positive integer')
    return _run(out) / f'batch-{batch:02d}'


def _compact(review):
    classification = review['classification']
    return [review['index'], classification['is_relevant'], classification['is_opinion'],
            classification['main_issue'], classification['stance'], review['uncertain'],
            review['evidence_sufficient'], review['reason']]


def _reservation(out):
    out = _run(out)
    reservation = read(out / RESERVATION)
    baseline_path = out / BASELINE
    if sha(baseline_path) != reservation['baseline_sha256']:
        raise ValueError('pinned baseline changed')
    if reservation.get('batch_count') != len(reservation.get('packet_hashes', {})):
        raise ValueError('invalid reservation')
    if reservation.get('batch_count') != len(reservation.get('original_hashes', {})):
        raise ValueError('invalid original review reservation')
    return reservation, read(baseline_path)


def _packet(out, batch):
    reservation, baseline = _reservation(out)
    path = _batch_dir(out, batch) / 'packet.private.json'
    rel = str(path.relative_to(_run(out)))
    if rel not in reservation['packet_hashes'] or sha(path) != reservation['packet_hashes'][rel]:
        raise ValueError('reserved packet changed')
    original_path = _batch_dir(out, batch) / 'original.private.json'
    original_rel = str(original_path.relative_to(_run(out)))
    if original_rel not in reservation['original_hashes'] or sha(original_path) != reservation['original_hashes'][original_rel]:
        raise ValueError('reserved initial editor review changed')
    packet = read(path)
    expected = [r for r in baseline['records'] if r['supplemental_batch'] == batch]
    if len(packet['records']) != len(expected) or not 1 <= len(expected) <= 20:
        raise ValueError('packet coverage differs from baseline')
    if len({r['topic'] for r in packet['records']}) != 1:
        raise ValueError('supplemental packet must contain one topic')
    for i, item in enumerate(expected):
        raw = packet['records'][i]
        if item['supplemental_index'] != i or any(raw[k] != item[k] for k in
                ['topic', 'record_id_hash', 'body_sha256', 'classification_sha256']):
            raise ValueError('packet identity differs from baseline')
    return packet, expected


def prepare(root, out, journal, sources, editor_reviews=None):
    """Freeze pending-audit retains into homogeneous packets of at most 20."""
    root, out = Path(root), Path(out)
    if out.exists() or out.resolve().is_relative_to(root.resolve()):
        raise ValueError('new private output outside the repository required')
    rows = journal['journal'] if isinstance(journal, dict) else journal
    if not isinstance(rows, list) or not isinstance(sources, dict) or editor_reviews is not None and not isinstance(editor_reviews, dict):
        raise ValueError('journal and sources are required')
    selected = []
    seen = set()
    for row in rows:
        if row.get('adoption_status') != 'pending_audit':
            continue
        source_key = (row.get('batch'), row.get('index'))
        if source_key in seen or source_key not in sources:
            raise ValueError('missing or duplicate source key')
        seen.add(source_key)
        raw, criteria = sources[source_key]
        if row.get('route') != 'retain_candidate' or row.get('first_route') != 'no_change' or row.get('changes') != {}:
            raise ValueError('supplemental audit only accepts pending retain candidates')
        if row.get('current') != row.get('proposed') or raw.get('classification') != row.get('current'):
            raise ValueError('pending retain input differs')
        for key in ['topic', 'record_id_hash', 'body_sha256', 'classification_sha256']:
            if row.get(key) != raw.get(key):
                raise ValueError('journal and raw identity differ')
        selected.append((copy.deepcopy(row), copy.deepcopy(raw), copy.deepcopy(criteria), source_key))
    if not selected:
        raise ValueError('no pending-audit records')
    if editor_reviews is not None and set(editor_reviews) != seen:
        raise ValueError('initial editor review coverage differs')

    grouped = defaultdict(list)
    for item in selected:
        grouped[item[0]['topic']].append(item)
    out.mkdir(parents=True)
    baseline_records = []
    packets = []
    originals_paths = []
    batch = 0
    for topic in sorted(grouped):
        for start in range(0, len(grouped[topic]), 20):
            batch += 1
            items = grouped[topic][start:start + 20]
            packet = {'schema_version': 1, 'records': [item[1] for item in items],
                      'criteria': {topic: items[0][2]}}
            if any(item[2] != items[0][2] for item in items):
                raise ValueError('mixed criteria versions within one topic')
            checked_packet(packet, root)
            d = _batch_dir(out, batch)
            dump(d / 'packet.private.json', packet)
            originals = []
            for index, (row, raw, _criteria, source_key) in enumerate(items):
                prior = editor_reviews.get(source_key) if editor_reviews is not None else None
                if prior is not None:
                    if any(prior.get(k) != raw[k] for k in ['record_id_hash', 'body_sha256', 'classification_sha256']):
                        raise ValueError('initial editor identity differs')
                    if prior.get('classification') != row['proposed'] or prior.get('uncertain') is not False:
                        raise ValueError('initial editor decision differs from journal')
                    if type(prior.get('evidence_sufficient')) is not bool or not isinstance(prior.get('reason'), str):
                        raise ValueError('incomplete initial editor review')
                    if hashlib.sha256(prior['reason'].encode()).hexdigest() != row.get('reason_sha256'):
                        raise ValueError('initial editor reason differs from journal')
                    validate({k: prior[k] for k in ['classification', 'uncertain', 'reason']},
                             raw['classification'], items[0][2])
                    reason, evidence, evidence_source = prior['reason'], prior['evidence_sufficient'], 'editor_review'
                else:
                    reason, evidence, evidence_source = None, True, 'pending_audit_policy_inference'
                original = {'index': index, 'classification': row['proposed'],
                            'uncertain': False, 'evidence_sufficient': evidence,
                            'reason': reason, 'reason_sha256': row.get('reason_sha256'),
                            'evidence_source': evidence_source}
                originals.append(original)
                baseline_records.append({**copy.deepcopy(row), 'source_key': list(source_key),
                                         'supplemental_batch': batch, 'supplemental_index': index})
            dump(d / 'original.private.json', {'records': originals})
            originals_paths.append(d / 'original.private.json')
            packets.append(d / 'packet.private.json')
    baseline = {'schema_version': 1, 'records': baseline_records,
                'source_journal_sha256': fingerprint(rows), 'pending_audit_records': len(selected),
                'canonical_changes': 0, 'registered_reread_increment': 0}
    dump(out / BASELINE, baseline)
    reservation = {'schema_version': 1, 'prepared_epoch': time.time(), 'batch_count': batch,
                   'pending_audit_records': len(selected), 'baseline_sha256': sha(out / BASELINE),
                   'policy_sha256': sha(root / 'scripts/editorial_acceptance.py'),
                   'packet_hashes': {str(p.relative_to(out)): sha(p) for p in packets},
                   'original_hashes': {str(p.relative_to(out)): sha(p) for p in originals_paths}}
    dump(out / RESERVATION, reservation)
    return {'batches': batch, 'records': len(selected), 'topics': dict(Counter(r[0]['topic'] for r in selected)),
            'canonical_changes': 0, 'registered_reread_increment': 0}


def show(out, batch):
    packet, _ = _packet(out, batch)
    d = _batch_dir(out, batch)
    marker = d / 'audit-start.private.json'
    if not marker.exists():
        dump(marker, {'started_epoch': time.time(), 'packet_sha256': sha(d / 'packet.private.json')})
    return {'records': [{'index': i, 'body': raw['text'], 'current': raw['classification'],
                         'criteria': packet['criteria'][raw['topic']]}
                        for i, raw in enumerate(packet['records'])]}


def save(out, batch, values, actor):
    """Save [index, relevant, opinion, issue, stance, uncertain, evidence, reason]."""
    packet, _ = _packet(out, batch)
    d = _batch_dir(out, batch)
    path, draft = d / 'audit.private.json', d / 'audit-draft.private.json'
    if path.exists() or draft.exists():
        raise ValueError('never overwrite a saved attempt')
    if not isinstance(actor, str) or not actor.strip() or not isinstance(values, list):
        raise ValueError('actor and values are required')
    started = read(d / 'audit-start.private.json')
    dump(draft, {'values': values, 'actor': actor, 'recorded_epoch': time.time()})
    reviews = []
    for value in values:
        if not isinstance(value, list) or len(value) != 8 or type(value[0]) is not int:
            raise ValueError('invalid compact response')
        i, relevant, opinion, issue, stance, uncertain, evidence, reason = value
        if not 0 <= i < len(packet['records']) or any(type(v) is not bool for v in
                [relevant, opinion, uncertain, evidence]):
            raise ValueError('invalid compact response')
        raw = packet['records'][i]
        classification = {'is_relevant': relevant, 'is_opinion': opinion,
                          'main_issue': issue, 'stance': stance}
        validate({'classification': classification, 'uncertain': uncertain, 'reason': reason},
                 raw['classification'], packet['criteria'][raw['topic']])
        reviews.append({'index': i, 'record_id_hash': raw['record_id_hash'],
                        'body_sha256': raw['body_sha256'],
                        'classification_sha256': raw['classification_sha256'],
                        'classification': classification, 'uncertain': uncertain,
                        'evidence_sufficient': evidence, 'reason': reason})
    if sorted(r['index'] for r in reviews) != list(range(len(packet['records']))):
        raise ValueError('review coverage mismatch')
    if [r['index'] for r in reviews] != list(range(len(packet['records']))):
        raise ValueError('reviews must be in packet order')
    finished = time.time()
    result = {'packet_sha256': started['packet_sha256'], 'started_epoch': started['started_epoch'],
              'finished_epoch': finished, 'reviews': reviews, 'actor': actor,
              'identity_writer': WRITER}
    dump(path, result)
    return {'batch': batch, 'saved': len(reviews)}


def compare(out, batch):
    packet, _ = _packet(out, batch)
    d = _batch_dir(out, batch)
    audit = read(d / 'audit.private.json')
    originals = read(d / 'original.private.json')['records']
    _verified_audit(packet, audit)
    if len(originals) != len(packet['records']):
        raise ValueError('original coverage mismatch')
    return {'batch': batch, 'rows': [{'index': i, 'initial': originals[i], 'audit': audit['reviews'][i]}
                                     for i in range(len(originals))]}


def _verified_audit(packet, audit):
    reviews = audit['reviews']
    if audit.get('identity_writer') != WRITER or not isinstance(audit.get('actor'), str) or not audit['actor'].strip():
        raise ValueError('audit writer or actor mismatch')
    if sorted(r.get('index') for r in reviews) != list(range(len(packet['records']))):
        raise ValueError('audit coverage or writer mismatch')
    for review in reviews:
        raw = packet['records'][review['index']]
        if any(review.get(k) != raw[k] for k in ['record_id_hash', 'body_sha256', 'classification_sha256']):
            raise ValueError('audit identity differs')
        validate({k: review[k] for k in ['classification', 'uncertain', 'reason']},
                 raw['classification'], packet['criteria'][raw['topic']])
        if type(review.get('evidence_sufficient')) is not bool:
            raise ValueError('explicit evidence assessment required')
    return reviews


def _resolutions(initial, audit, reason_conflicts):
    resolutions = []
    for i, second in enumerate(audit):
        first = initial[i]
        if first['uncertain'] or second['uncertain'] or first['classification'] != second['classification']:
            status, basis = 'hold', 'supplemental_disagreement_or_uncertainty'
        elif first['evidence_sufficient'] is True and second['evidence_sufficient'] is True and i not in reason_conflicts:
            status, basis = 'accepted', 'supplemental_independent_audit'
        else:
            status, basis = 'pending_evidence', 'supplemental_insufficient_or_conflicting_evidence'
        resolutions.append({'index': i, 'adoption_status': status, 'adoption_basis': basis})
    return resolutions


def finish(out, batch, reason_conflicts, notes):
    packet, _ = _packet(out, batch)
    d = _batch_dir(out, batch)
    path = d / 'resolution.private.json'
    if path.exists():
        raise ValueError('resolution already saved')
    if not isinstance(reason_conflicts, list) or len(set(reason_conflicts)) != len(reason_conflicts) or any(
            type(i) is not int or not 0 <= i < len(packet['records']) for i in reason_conflicts):
        raise ValueError('invalid reason conflicts')
    if not isinstance(notes, str):
        raise ValueError('notes must be a string')
    audit = _verified_audit(packet, read(d / 'audit.private.json'))
    initial = read(d / 'original.private.json')['records']
    resolutions = _resolutions(initial, audit, reason_conflicts)
    result = {'reason_conflicts': reason_conflicts, 'notes': notes, 'resolutions': resolutions,
              'finished_epoch': time.time()}
    dump(path, result)
    return {'batch': batch, 'counts': dict(Counter(r['adoption_status'] for r in resolutions))}


def collect(root, out):
    root, out = Path(root), Path(out)
    reservation, baseline = _reservation(out)
    if sha(root / 'scripts/editorial_acceptance.py') != reservation['policy_sha256']:
        raise ValueError('editorial acceptance policy changed')
    overlays, proofs = [], {RESERVATION: sha(out / RESERVATION), BASELINE: sha(out / BASELINE)}
    seen = set()
    for batch in range(1, reservation['batch_count'] + 1):
        packet, expected = _packet(out, batch)
        checked_packet(packet, root)
        d = _batch_dir(out, batch)
        original_path, draft_path = d / 'original.private.json', d / 'audit-draft.private.json'
        audit_path, start_path, resolution_path = d / 'audit.private.json', d / 'audit-start.private.json', d / 'resolution.private.json'
        originals, draft, audit = read(original_path)['records'], read(draft_path), read(audit_path)
        start, resolution = read(start_path), read(resolution_path)
        reviews = _verified_audit(packet, audit)
        if start['packet_sha256'] != sha(d / 'packet.private.json') or audit['packet_sha256'] != start['packet_sha256']:
            raise ValueError('audit packet identity mismatch')
        if audit['started_epoch'] != start['started_epoch'] or not audit['started_epoch'] <= draft['recorded_epoch'] <= audit['finished_epoch']:
            raise ValueError('audit timing mismatch')
        if draft.get('actor') != audit.get('actor') or draft.get('values') != [_compact(r) for r in reviews]:
            raise ValueError('saved audit differs from draft')
        conflicts = resolution.get('reason_conflicts')
        if not isinstance(conflicts, list) or len(set(conflicts)) != len(conflicts) or any(
                type(i) is not int or not 0 <= i < len(expected) for i in conflicts):
            raise ValueError('invalid saved reason conflicts')
        recomputed = _resolutions(originals, reviews, conflicts)
        if len(originals) != len(expected) or resolution.get('resolutions') != recomputed:
            raise ValueError('supplemental coverage mismatch')
        by_index = {r['index']: r for r in recomputed}
        if set(by_index) != set(range(len(expected))):
            raise ValueError('resolution coverage mismatch')
        for i, source in enumerate(expected):
            source_key = tuple(source['source_key'])
            if source_key in seen or source.get('adoption_status') != 'pending_audit':
                raise ValueError('baseline source is not a unique pending audit')
            seen.add(source_key)
            if originals[i]['classification'] != source['proposed'] or originals[i]['reason_sha256'] != source.get('reason_sha256'):
                raise ValueError('initial decision differs from baseline')
            decision = by_index[i]
            new = {**{k: v for k, v in source.items() if k not in ['source_key', 'supplemental_batch', 'supplemental_index']},
                   'adoption_status': decision['adoption_status'], 'adoption_basis': decision['adoption_basis'],
                   'canonical_applied': False,
                   'counts_as_registered_editorial_reread': False,
                   'supplemental_audit_sha256': sha(audit_path),
                   'supplemental_reason_sha256': hashlib.sha256(reviews[i]['reason'].encode()).hexdigest()}
            old = {k: v for k, v in source.items() if k not in ['source_key', 'supplemental_batch', 'supplemental_index']}
            overlays.append({'source_key': list(source_key), 'old': old, 'new': new})
        for path in [d / 'packet.private.json', original_path, start_path, draft_path, audit_path, resolution_path]:
            proofs[str(path.relative_to(out))] = sha(path)
    if len(overlays) != baseline['pending_audit_records']:
        raise ValueError('incomplete supplemental audit')
    return {'schema_version': 1, 'overlay': overlays,
            'counts': dict(Counter(item['new']['adoption_status'] for item in overlays)),
            'supplemental_audits': len(overlays), 'new_records': 0,
            'canonical_changes': 0, 'registered_reread_increment': 0, 'proofs': proofs}


def ready(out):
    reservation, _ = _reservation(out)
    pending, comparable, finished = [], [], []
    for batch in range(1, reservation['batch_count'] + 1):
        d = _batch_dir(out, batch)
        (finished if (d / 'resolution.private.json').exists() else comparable if (d / 'audit.private.json').exists() else pending).append(batch)
    return {'pending_batches': pending, 'comparable_batches': comparable, 'finished_batches': finished}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['show', 'compare', 'ready'])
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--batch', type=int)
    args = parser.parse_args()
    result = ready(args.out) if args.action == 'ready' else compare(args.out, args.batch) if args.action == 'compare' else show(args.out, args.batch)
    print(json.dumps(result, ensure_ascii=False))
