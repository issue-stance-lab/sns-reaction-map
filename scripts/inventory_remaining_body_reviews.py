"""Read-only Task 63 inventory. Outputs are evidence, never work reservations.

Do not equate a duplicate body under another post ID with completed reading.
The ID remainder and the selector's unique-input remainder are separate values.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from scripts.prepare_body_review_pilot import inventory, fingerprint, sha
from scripts.editorial_work_registry import checked_packet, load_registry


def read(path):
    return json.loads(path.read_text())


def post_key(row):
    return row['topic'], row['record_id_hash']


def input_key(row):
    return row['topic'], row['body_sha256'], row['classification_sha256']


def global_id_counts(rows, previous):
    ids = {r['record_id_hash'] for r in rows}
    versions = {(r['record_id_hash'], r['body_sha256'], r['classification_sha256']) for r in rows}
    return {
        'topic_record_count': len(rows), 'global_post_id_unique': len(ids),
        'global_post_id_duplicate_excess': len(rows) - len(ids),
        'post_id_body_classification_unique': len(versions),
        'post_id_body_classification_duplicate_excess': len(rows) - len(versions),
        'previous_global_post_id_overlap': len(ids & {r['record_id_hash'] for r in previous}),
        'previous_post_id_body_classification_overlap': len(versions & {
            (r['record_id_hash'], r['body_sha256'], r['classification_sha256']) for r in previous}),
    }


def partition(rows, reasons, previously_seen_inputs, previously_seen_ids=()):
    """Retain all unresolved IDs even when their input cannot be reserved again."""
    seen = set(previously_seen_inputs)
    eligible, excluded = [], []
    for row in sorted(rows, key=post_key):
        why = [name for name, keys in reasons.items() if post_key(row) in keys]
        if input_key(row) in previously_seen_inputs and post_key(row) not in previously_seen_ids:
            why.append('same_input_as_existing_work_different_id')
        if not why and input_key(row) in seen:
            why.append('same_input_as_another_unconfirmed_id')
        if why:
            excluded.append({**row, 'exclusion_reasons': why})
        else:
            eligible.append(row)
            seen.add(input_key(row))
    return eligible, excluded


def inspect(root, canonical_root, private_root, run):
    report, queues = inventory(root, private_root)
    proofs = dict(report['source_fingerprints'])
    canonical = {}
    for topic, value in report['topics'].items():
        actual = sha(canonical_root / value['canonical_file'])
        if actual != value['canonical_sha256']:
            raise ValueError('authoritative canonical differs from inventory copy: ' + topic)
        canonical[topic] = actual
    reservation = read(run / 'reservation.json')
    for topic, expected in reservation['canonical_hashes'].items():
        if canonical[topic] != expected:
            raise ValueError('run canonical changed: ' + topic)
    for name, field in [('work-before.private.json', 'baseline_work_sha256'),
                        ('adoption-before.private.json', 'baseline_adoption_sha256')]:
        if sha(run / name) != reservation[field]:
            raise ValueError('baseline changed: ' + name)
    old = read(run / 'adoption-before.private.json')['records']
    work = load_registry(run / 'work-before.private.json', root, private_root)['records']
    valid_new = []
    for wave_name, expected in reservation['waves'].items():
        wave = run / wave_name
        if sha(wave / 'reservation.json') != expected:
            raise ValueError('wave reservation changed')
        for relative, expected_packet in read(wave / 'reservation.json')['packet_hashes'].items():
            path = wave / relative
            if sha(path) != expected_packet:
                raise ValueError('packet changed')
            packet = read(path)
            checked_packet(packet, root)
            if fingerprint(packet['records']) != packet['input_sha256']:
                raise ValueError('packet identity changed')
            valid_new.extend(packet['records'])
            proofs[str(path.relative_to(private_root))] = expected_packet
    candidates = [{**row, 'topic': topic} for topic, rows in queues.items()
                  if report['topics'][topic]['published'] for row in rows if row['opinion']]
    byid = {post_key(row): row for row in candidates}
    if len(byid) != len(candidates):
        raise ValueError('duplicate canonical topic/post ID')
    all_unconfirmed = {post_key({**row, 'topic': topic}): {**row, 'topic': topic}
                       for topic, rows in queues.items() for row in rows}
    for row in old + work + valid_new:
        current = all_unconfirmed.get(post_key(row))
        if current and input_key(current) != input_key(row):
            raise ValueError('existing work body/classification version changed')
    old_keys, new_keys = set(map(post_key, old)), set(map(post_key, valid_new))
    if old_keys & new_keys or len(new_keys) != len(valid_new):
        raise ValueError('duplicate valid review ID')
    raw_remaining = [r for r in candidates if post_key(r) not in old_keys | new_keys]
    raw_keys = set(map(post_key, raw_remaining))
    reasons = {'unfinished_legacy_pilot': set(map(post_key, work)) - old_keys}
    base = private_root / 'body-review-pilot'
    limited = set()
    for dirname, filename in [
        ('20260907-policy-stance-check-v1', 'packet.private.json'),
        ('20260907-policy-stance-recheck-v2', 'packet.private.json'),
        ('20260907-policy-stance-v3-validation', 'review-input.private.json'),
        ('20260907-sol-terra20-v1', 'packet.private.json'),
    ]:
        path = base / dirname / filename
        limited.update(map(post_key, read(path)['records']))
        proofs[str(path.relative_to(private_root))] = sha(path)
    reasons['past_limited_rechecks'] = limited
    invalid, invalid_saved, invalid_summary = set(), set(), {}
    for marker in sorted(base.glob('*/invalidated.private.json')):
        keys, saved = set(), set()
        for path in marker.parent.glob('wave-*/batch-*/packet.private.json'):
            batch_keys = set(map(post_key, read(path)['records']))
            keys |= batch_keys
            if (path.parent / 'editor.private.json').exists():
                saved |= batch_keys
            proofs[str(path.relative_to(private_root))] = sha(path)
        invalid |= keys
        invalid_saved |= saved
        invalid_summary[marker.parent.name] = {
            'reserved_ids': len(keys), 'saved_editor_ids': len(saved),
            'valid_review_overlap': len(keys & (old_keys | new_keys)),
            'remaining_ids': len(keys & raw_keys),
            'remaining_saved_editor_ids': len(saved & raw_keys),
        }
        proofs[str(marker.relative_to(private_root))] = sha(marker)
    reasons['invalid_run_reserved_id'] = invalid
    # Conservative reservation scan: every packet not in known completed/invalid
    # sets remains unavailable, regardless of a worker's self-reported status.
    other_reserved = set()
    for folder in sorted(p for p in base.iterdir() if p.is_dir()):
        if (folder / 'invalidated.private.json').exists():
            continue
        paths = list(folder.glob('wave-*/batch-*/packet.private.json'))
        paths += list(folder.glob('batch-*/packet.private.json'))
        if (folder / 'packet.private.json').exists():
            paths.append(folder / 'packet.private.json')
        for path in paths:
            packet = read(path)
            if all('record_id_hash' in r and 'topic' in r for r in packet.get('records', [])):
                other_reserved.update(map(post_key, packet.get('records', [])))
                proofs[str(path.relative_to(private_root))] = sha(path)
    reasons['other_existing_reservation'] = other_reserved - old_keys - new_keys - limited - invalid - set(map(post_key, work))
    prior_inputs = set(map(input_key, work + valid_new))
    previous_post_ids = set(map(post_key, work + valid_new))
    eligible, excluded = partition(raw_remaining, reasons, prior_inputs, previous_post_ids)
    sequential, remaining_keys = {}, set(raw_keys)
    for name, keys in reasons.items():
        removed = remaining_keys & keys
        remaining_keys -= removed
        sequential[name] = {'removed': len(removed), 'remaining': len(remaining_keys)}
    aliased_prior = {post_key(r) for r in raw_remaining
                     if input_key(r) in prior_inputs and post_key(r) not in previous_post_ids}
    removed = remaining_keys & aliased_prior
    remaining_keys -= removed
    sequential['same_input_as_existing_work_different_id'] = {'removed': len(removed), 'remaining': len(remaining_keys)}
    sequential['same_input_as_another_unconfirmed_id'] = {'removed': len(remaining_keys) - len(eligible), 'remaining': len(eligible)}
    public_opinion_keys = set(byid) | set()  # candidates already omit legacy reading
    overlap_sets = {name: keys & raw_keys for name, keys in reasons.items()}
    overlap_sets['same_input_as_existing_work_different_id'] = aliased_prior
    reason_combinations = Counter(tuple(name for name, keys in overlap_sets.items() if key in keys)
                                  for key in raw_keys)
    summary = {
        'schema_version': 1, 'purpose': 'Inventory evidence only; NOT A RESERVATION. No reading credit.',
        'published_opinions': report['totals']['published']['opinion'],
        'prior_editorial_opinions': report['totals']['published']['opinion_editorial_record'],
        'prior_limited_opinions': report['totals']['published']['opinion_limited_record'],
        'original_unconfirmed_ids': len(candidates),
        'previously_reviewed_public_opinion_ids': len(old_keys & public_opinion_keys),
        'current_run_public_opinion_ids': len(new_keys & public_opinion_keys),
        'current_run_total_ids': len(valid_new),
        'current_run_nonopinion_ids': sum(not r['opinion'] for r in valid_new),
        'current_run_unlisted_opinion_ids': sum(r['opinion'] and r['topic'] == 'takaichi' for r in valid_new),
        'raw_unconfirmed_id_remainder': len(raw_remaining),
        'raw_remainder_by_topic': dict(sorted(Counter(r['topic'] for r in raw_remaining).items())),
        'raw_remainder_unique_inputs': len(set(map(input_key, raw_remaining))),
        'all_reason_overlap_counts': {n: len(s) for n, s in overlap_sets.items()},
        'reason_combinations': [{'reasons': list(k), 'ids': v} for k, v in sorted(reason_combinations.items())],
        'sequential_exclusions': sequential,
        'eligible_unique_inputs': len(eligible),
        'eligible_by_topic': dict(sorted(Counter(r['topic'] for r in eligible).items())),
        'unconfirmed_but_ineligible_ids': len(excluded),
        'invalid_runs': invalid_summary,
        'global_identity_checks': {
            'raw_remaining': global_id_counts(raw_remaining, old + valid_new),
            'eligible_inventory_only': global_id_counts(eligible, old + valid_new),
            'previous_valid_reviews': global_id_counts(old + valid_new, []),
            'interpretation': 'Counts above use topic/post ID. Repeated global IDs differ in both body and classification; do not carry reading credit across those versions.',
        },
        'canonical_sha256': canonical,
        'criteria_source_sha256': {r['criteria_sha256'] for r in work},
        'new_body_reviews': 0, 'registered_work_records': 0, 'reservations_created': 0,
        'canonical_changes': 0, 'adoption_changes': 0, 'public_changes': 0,
        'required_action': 'Stop before reserving new work because exclusion-aware count differs from 5,134.',
    }
    summary['criteria_fingerprints'] = sorted(summary.pop('criteria_source_sha256'))
    evidence = {'purpose': summary['purpose'], 'raw_remaining': raw_remaining,
                'eligible_inventory_only': eligible, 'excluded_unconfirmed': excluded,
                'source_fingerprints': proofs, 'canonical_sha256': canonical}
    assert len(raw_remaining) == len(eligible) + len(excluded)
    assert not set(map(post_key, eligible)) & set(map(post_key, excluded))
    return summary, evidence


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'canonical-root', 'private-root', 'run', 'summary-out', 'private-out'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    if a.private_out.resolve().is_relative_to(a.root.resolve()):
        raise ValueError('ID/body evidence must remain outside the repository')
    if a.summary_out.exists() or a.private_out.exists():
        raise ValueError('never overwrite inventory evidence')
    summary, evidence = inspect(a.root.resolve(), a.canonical_root.resolve(), a.private_root.resolve(), a.run.resolve())
    for path, value in [(a.private_out, evidence), (a.summary_out, summary)]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
