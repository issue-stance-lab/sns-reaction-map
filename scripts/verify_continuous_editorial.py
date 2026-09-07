"""Replay a frozen 1,000-record Sol run and combine it with prior adoption."""
import argparse
from collections import Counter
from pathlib import Path
from scripts.continuous_editorial_review import packet_for, batch_dir
from scripts.editorial_acceptance import assess_batch
from scripts.editorial_work_registry import checked_packet
from scripts.verify_editorial_hundred import read, sha, dump
from scripts.verify_editorial_thousand import collect_thousand
from scripts.verify_editorial_wave import verify_accepted


def collect_run(root, run):
    root, run = Path(root), Path(run)
    reservation = read(run / 'reservation.json')
    if reservation['new_records'] != 1000 or len(reservation['packet_hashes']) != 50:
        raise ValueError('expected 50 reserved packets')
    if reservation['prior_adoption_sha256'] != sha(root / 'data/verification/editorial-adoption.json'):
        raise ValueError('prior adoption changed')
    if reservation['writer_sha256'] != sha(root / 'scripts/continuous_editorial_review.py'):
        raise ValueError('identity writer changed')
    assignments = read(run / 'assignment-change.json')
    for role in ['editors', 'auditors']:
        assigned = [n for batches in assignments[role].values() for n in batches]
        if sorted(assigned) != list(range(1, 51)):
            raise ValueError('assignments must cover each batch exactly once')
    for actor, batches in assignments['editors'].items():
        if set(batches) & set(assignments['auditors'].get(actor, [])):
            raise ValueError('self audit assignment')
    def strings(value):
        if isinstance(value, dict):
            return set().union(set(value), *(strings(v) for v in value.values()))
        if isinstance(value, list):
            return set().union(*(strings(v) for v in value))
        return {value} if isinstance(value, str) else set()
    for actor, name in [('continuous_auditor', 'auditor'), ('continuous_editor_a', 'editor-a'), ('continuous_editor_b', 'editor-b')]:
        attestation = strings(read(run / (name + '-attestation.private.json')))
        if '/root/' + actor not in attestation:
            raise ValueError('attestation actor missing')
        for role, file_names in [('editors', ['editor.private.json']), ('auditors', ['audit.private.json', 'quality_gate.private.json'])]:
            for n in assignments[role].get(actor, []):
                if any(sha(batch_dir(run, n) / file_name) not in attestation for file_name in file_names):
                    raise ValueError('attested evidence does not match saved outputs')
    journal = []; sources = {}; proofs = {name: sha(run / name) for name in ['reservation.json', 'assignment-change.json', 'auditor-attestation.private.json', 'editor-a-attestation.private.json', 'editor-b-attestation.private.json']}; seen = set()
    times = {'editor_packet_interval_sum_seconds': 0, 'audit_packet_interval_sum_seconds': 0}; independent = 0; last_saved = reservation['prepared_epoch']
    for n in range(1, 51):
        d = batch_dir(run, n); packet = packet_for(run, n); checked_packet(packet, root)
        if len(packet['records']) != 20 or len({r['topic'] for r in packet['records']}) != 1:
            raise ValueError('expected a homogeneous 20-record packet')
        editor = read(d / 'editor.private.json'); audit = read(d / 'audit.private.json'); gate = read(d / 'quality_gate.private.json')
        for role, result in [('editor', editor), ('audit', audit)]:
            start = read(d / (role + '-start.private.json'))
            if result['packet_sha256'] != sha(d / 'packet.private.json') or start['packet_sha256'] != result['packet_sha256']:
                raise ValueError('review packet identity mismatch')
            if result['started_epoch'] != start['started_epoch'] or result['finished_epoch'] < result['started_epoch']:
                raise ValueError('review timing mismatch')
            last_saved = max(last_saved, result['finished_epoch'])
            times[role + '_packet_interval_sum_seconds'] += result['finished_epoch'] - result['started_epoch']
            draft = read(d / (role + '-draft.private.json'))
            compact = [[r['index'], r['classification']['is_relevant'], r['classification']['is_opinion'],
                        r['classification']['main_issue'], r['classification']['stance'],
                        r['uncertain'], r['evidence_sufficient'], r['reason']] for r in result['reviews']]
            if compact != draft['values'] or not result['started_epoch'] <= draft['recorded_epoch'] <= result['finished_epoch']:
                raise ValueError('saved review differs from original response')
        if read(d / 'editor-flags.private.json')['systemic_criteria_issue'] and not gate['systemic_criteria_issue']:
            raise ValueError('editor criteria flag was dropped')
        result = assess_batch(packet, editor, audit, gate); independent += result['independent_records']
        for r in result['journal']:
            raw = packet['records'][r['index']]; key = (r['topic'], r['body_sha256'], r['classification_sha256'])
            if key in seen: raise ValueError('duplicate input')
            seen.add(key); journal.append({**r, 'batch': n}); sources[(n, r['index'])] = (raw, packet['criteria'][r['topic']])
        for name in ['packet.private.json', 'editor.private.json', 'audit.private.json', 'quality_gate.private.json', 'editor-flags.private.json', 'editor-start.private.json', 'audit-start.private.json', 'editor-draft.private.json', 'audit-draft.private.json']:
            proofs[str((d / name).relative_to(run))] = sha(d / name)
    return {'schema_version': 1, 'reviewed_records': 1000, 'new_records': 1000,
            'scope': 'five published themes, all inputs opinions; candidate adoption only',
            'journal': journal, 'adoption_counts': dict(Counter(r['adoption_status'] for r in journal)),
            'routes': dict(Counter(r['route'] for r in journal)), 'independent_records': independent,
            'proofs': proofs, 'policy_sha256': sha(root / 'scripts/editorial_acceptance.py'),
            'times': {k: round(v, 2) for k, v in times.items()},
            'reservation_to_last_review_save_seconds': round(last_saved - reservation['prepared_epoch'], 2),
            'timing_scope': 'Summed per-packet read-to-save intervals may overlap; not wall time or token/cost measurement. Audit comparison and gate time excluded.',
            'actor_evidence_scope': 'Orchestration assignment and retrospective actor attestations; saved review files do not authenticate the executing agent.',
            'canonical_changes': 0, 'registered_reread_increment': 0, 'codex_tokens': None}, sources


def combine(root, base, run):
    previous, previous_sources = collect_thousand(root, base)
    current, current_sources = collect_run(root, run)
    journal = previous['journal'] + [{**r, 'batch': r['batch'] + 100000} for r in current['journal']]
    sources = {**previous_sources, **{(b + 100000, i): v for (b, i), v in current_sources.items()}}
    if len(journal) != 2000 or len({(r['topic'], r['record_id_hash']) for r in journal}) != 2000:
        raise ValueError('expected 2,000 unique reviewed records')
    if len({(r['topic'], r['body_sha256'], r['classification_sha256']) for r in journal}) != 2000:
        raise ValueError('repeated review input')
    return {'schema_version': 1, 'reviewed_records': 2000, 'new_records': 1000,
            'journal': journal, 'adoption_counts': dict(Counter(r['adoption_status'] for r in journal)),
            'proofs': {'prior': previous['proofs'], 'new': current['proofs']},
            'independent_new_records': current['independent_records'], 'new_times': current['times'],
            'canonical_changes': 0, 'registered_reread_increment': 0, 'codex_tokens': None}, sources


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['root', 'base', 'run', 'out']:
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    result = verify_accepted(a.root, a.run, a.out, combine(a.root, a.base, a.run))
    print(result['adoption_counts'])
