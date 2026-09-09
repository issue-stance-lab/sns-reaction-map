"""Inspect old unfinished work without reserving IDs or granting reading credit.

This is evidence collection for Task 63, not an editorial decision writer.
Every output is new; original work, auxiliary replies and invalid runs stay intact.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import yaml

from scripts.editorial_work_registry import checked_packet, fingerprint, load_registry, sha
from scripts.prepare_body_review_pilot import FIELDS
from scripts.verification_data import record_id_hash


def read(path):
    return json.loads(path.read_text())


def key(row):
    return row['topic'], row['record_id_hash']


def inspect(root, canonical_root, private_root, inventory_path, activity_path):
    proofs = {}

    def proof(path):
        path = path.resolve()
        digest = sha(path)
        proofs[str(path)] = digest
        for storage, base in (('repository', root), ('private', private_root), ('repository', canonical_root)):
            if path.is_relative_to(base):
                return {'storage': storage, 'path': str(path.relative_to(base)), 'sha256': digest}
        return {'storage': 'external', 'path': str(path), 'sha256': digest}

    inv = read(inventory_path)
    proof(inventory_path)
    activity = read(activity_path)
    proof(activity_path)
    if activity['old_workers_active'] or activity['new_body_review_assignments']:
        raise ValueError('active or newly assigned work cannot be proposed for resumption')
    work_path = root / 'data/verification/editorial-work.json'
    work = load_registry(work_path, root, private_root)
    proof(work_path)
    by_work = {key(r): r for r in work['records']}
    if len(by_work) != len(work['records']):
        raise ValueError('multiple existing work versions need explicit resolution')
    adoption_path = root / 'data/verification/editorial-adoption-current.json'
    adoption = read(adoption_path)
    proof(adoption_path)
    adopted_keys = {key(r) for r in adoption['records']}
    reasons = {'unfinished_legacy_pilot', 'invalid_run_reserved_id'}
    selected = [r for r in inv['excluded_unconfirmed'] if reasons & set(r['exclusion_reasons'])]
    if len(selected) != 93 or len(set(map(key, selected))) != 93:
        raise ValueError('expected exact 93 topic/post IDs')
    if Counter(r['exclusion_reasons'][0] for r in selected) != {
            'unfinished_legacy_pilot': 63, 'invalid_run_reserved_id': 30}:
        raise ValueError('legacy/invalid scope changed')
    selected_keys = set(map(key, selected))
    metadata_path = root / 'THEMES.yaml'
    metadata = yaml.safe_load(metadata_path.read_text())['themes']
    proof(metadata_path)
    current = {}
    for topic in sorted({r['topic'] for r in selected}):
        path = canonical_root / metadata[topic]['sample_file']
        if sha(path) != inv['canonical_sha256'][topic] or metadata[topic]['published'] != 'done':
            raise ValueError('current public canonical changed: ' + topic)
        proof(path)
        for row in read(path):
            rid = record_id_hash(row)
            if (topic, rid) in selected_keys:
                labels = {f: (row.get('classification') or {}).get(f, row.get(f)) for f in FIELDS}
                current[(topic, rid)] = (sha_text(row['text']), fingerprint(labels))

    base = private_root / 'body-review-pilot'
    pilot_path = base / '20260906-v1/pilot-input.json'
    pilot = read(pilot_path)
    pilot_checked = {key(r): r for r in checked_packet(pilot, root)}
    pilot_rows = {key(r): r for r in pilot['records']}
    pilot_ref = proof(pilot_path)
    histories = defaultdict(list)
    invalid_names = ('20260907-cycle-next4000-v1', '20260907-cycle-next4000-v2')
    invalid_counts = {}
    for name in invalid_names:
        run = base / name
        marker = read(run / 'invalidated.private.json')
        if marker['status'] != 'invalid_do_not_count' or marker['new_valid_reviews'] != 0:
            raise ValueError('invalid-run status changed')
        marker_ref = proof(run / 'invalidated.private.json')
        reservation = read(run / 'reservation.json')
        reservation_ref = proof(run / 'reservation.json')
        hit_count = 0
        for wave_name, expected in reservation['waves'].items():
            wave_path = run / wave_name / 'reservation.json'
            if sha(wave_path) != expected:
                raise ValueError('wave reservation changed')
            wave = read(wave_path)
            wave_ref = proof(wave_path)
            for rel, expected_packet in wave['packet_hashes'].items():
                path = wave_path.parent / rel
                packet = read(path)
                hits = [r for r in packet['records'] if key(r) in selected_keys]
                if not hits:
                    continue
                if sha(path) != expected_packet:
                    raise ValueError('invalid reservation packet changed')
                checked = {key(r): r for r in checked_packet(packet, root)}
                number = int(path.parent.name.split('-')[-1])
                assigned = {role: [worker for worker, batches in workers.items() if number in batches]
                            for role, workers in wave['assignments'].items()}
                files = sorted(p.name for p in path.parent.iterdir())
                # All 30 were unstarted reservations. A new file requires investigation.
                if files != ['packet.private.json']:
                    raise ValueError('invalid reserved ID now has other saved work: ' + str(path.parent))
                for row in hits:
                    hit_count += 1
                    histories[key(row)].append({
                        'kind': 'invalid_reservation_only', 'run': name,
                        'packet': proof(path), 'packet_row': checked[key(row)],
                        'invalid_marker': marker_ref, 'reservation': reservation_ref,
                        'wave_reservation': wave_ref, 'assigned_workers': assigned,
                        'worktrees': wave.get('worktrees', {}),
                        'observed_batch_files': files,
                        'editor_saved': False, 'audit_saved': False, 'quality_gate_saved': False,
                        'start_or_draft_saved': False,
                    })
        invalid_counts[name] = hit_count
    if set(invalid_counts.values()) != {30}:
        raise ValueError('invalid reserved scope not reproduced')

    results = []
    for row in sorted(selected, key=key):
        ident = key(row)
        if current.get(ident) != (row['body_sha256'], row['classification_sha256']):
            raise ValueError('current body/classification mismatch')
        if ident in adopted_keys:
            raise ValueError('formal adoption decision already exists')
        history = histories[ident]
        state = row['exclusion_reasons'][0]
        if state == 'unfinished_legacy_pilot':
            old = by_work[ident]
            if old['state'] != 'attempted':
                raise ValueError('legacy work now has formal decision')
            if history or old['evidence'] != ['body-review-pilot/20260906-v1/pilot-input.json']:
                raise ValueError('unexpected legacy work history')
            raw = pilot_rows[ident]
            checked = pilot_checked[ident]
            if any(old[f] != checked[f] for f in checked):
                raise ValueError('legacy version mismatch')
            path = pilot_path.parent / 'batches' / (raw['phase'] + '-' + row['topic'] + '.json')
            aux = read(path)
            if aux['kind'] != 'automated_auxiliary_check' or aux['counts_as_editorial_reread'] is not False:
                raise ValueError('auxiliary scope changed')
            if aux['request']['input_sha256'] != pilot['input_sha256']:
                raise ValueError('auxiliary input provenance changed')
            phase_rows = [r for r in pilot['records'] if r['topic'] == row['topic'] and r['phase'] == raw['phase']]
            index = next(i for i, r in enumerate(phase_rows) if key(r) == ident)
            response = json.loads(aux['raw_response'])
            raw_matches = [r for r in response if r.get('id') == index]
            saved = [r for r in aux['reviews'] if r['sample_id'] == raw['sample_id']]
            errors = [r['error'] for r in aux['errors'] if r['sample_id'] == raw['sample_id']]
            if len(raw_matches) != 1 or len(saved) + len(errors) != 1:
                raise ValueError('auxiliary reply cannot be linked to exact old sample')
            limited = []
            for scope in old['scope_only_audits']:
                audit_path = root / scope['evidence']
                audit = read(audit_path)
                if raw['sample_id'] not in audit[scope['finding']] or audit['automatic_editorial_credit'] != 0:
                    raise ValueError('limited audit linkage changed')
                value_path = base / '20260906-values-v2' / (raw['sample_id'].replace(':', '-') + '.json')
                value = read(value_path)
                if value['counts_as_editorial_reread'] is not False or any(value[f] != row[f] for f in ('body_sha256', 'classification_sha256')):
                    raise ValueError('limited auxiliary version mismatch')
                limited.append({'finding': scope['finding'], 'audit': proof(audit_path),
                                'auxiliary_value_file': proof(value_path), 'reading_credit': 0})
            history.append({
                'kind': 'auxiliary_only_not_formal_editorial', 'packet': pilot_ref,
                'packet_row': checked, 'sample_id': raw['sample_id'],
                'old_work_key': old['work_key'], 'old_work_state': old['state'],
                'saved_auxiliary_file': proof(path), 'raw_response_index': index,
                'raw_auxiliary_reply_saved': True, 'validated_auxiliary_reply_saved': bool(saved),
                'saved_auxiliary_validation_errors': errors,
                'auxiliary_kind': aux['kind'], 'auxiliary_model': aux['request']['model'],
                'auxiliary_completed_at': aux['completed_at'],
                'counts_as_editorial_reread': False, 'formal_editorial_decision_saved': False,
                'scope_only_audits': limited,
            })
        elif ident in by_work or len(history) != 2:
            raise ValueError('invalid-only ID unexpectedly has registered work or missing history')
        for h in history:
            checked = h['packet_row']
            if (checked['body_sha256'], checked['classification_sha256']) != current[ident]:
                raise ValueError('historical body/classification mismatch')
        criteria = pilot['criteria'][row['topic']]
        proof(root / criteria['source'])
        current_criteria = fingerprint(criteria)
        if any(h['packet_row']['criteria_sha256'] != current_criteria for h in history):
            raise ValueError('historical classifier criteria mismatch')
        results.append({
            **{f: row[f] for f in ('topic', 'record_id_hash', 'body_sha256', 'classification_sha256')},
            'criteria_sha256': current_criteria, 'tweet_id': row['tweet_id'],
            'source_exclusion_reason': state, 'proposed_state': 'resume_required',
            'resolution_kind': 'formal_review_still_required', 'history': history,
            'active_assignment': False, 'activity_evidence': proof(activity_path),
            'new_reading_credit': 0, 'reservation_created': False,
            'criteria_gate_required': row['topic'] == 'koshitsu-tenpakai',
        })
    for name in ('CYCLE_2000_RUNBOOK.md', 'POLICY_STANCE_MAPPING_V3.md'):
        proof(root / 'quality/designs/body-review' / name)
    # Recheck pinned files after the full scan to catch concurrent changes.
    for name, digest in proofs.items():
        if sha(Path(name)) != digest:
            raise ValueError('evidence changed during investigation: ' + name)
    summary = {
        'schema_version': 1, 'purpose': 'Resolution proposal only, NOT A RESERVATION. No reading credit.',
        'inspected_at': datetime.now(timezone.utc).isoformat(),
        'inspected_ids': len(results), 'remaining_to_inspect': 0,
        'resume_required': len(results), 'legacy_auxiliary_only': 63, 'invalid_reservation_only': 30,
        'invalid_run_id_counts': invalid_counts,
        'legacy_validated_auxiliary_replies': sum(h.get('validated_auxiliary_reply_saved', False) for r in results for h in r['history']),
        'legacy_auxiliary_validation_failures': sum(bool(h.get('saved_auxiliary_validation_errors')) for r in results for h in r['history']),
        'legacy_ids_with_limited_audit_history': sum(any(h.get('scope_only_audits') for h in r['history']) for r in results),
        'legacy_limited_audit_findings': sum(len(h.get('scope_only_audits', [])) for r in results for h in r['history']),
        'by_topic': dict(sorted(Counter(r['topic'] for r in results).items())),
        'current_body_classification_and_classifier_criteria_match': 93,
        'formal_review_decisions_found': 0, 'old_active_assignments_found': 0,
        'new_body_reviews': 0, 'independent_body_audits': 0, 'supplemental_body_audits': 0,
        'reading_credit': 0, 'reservations_created': 0, 'registered_work_changes': 0,
        'adoption_changes': 0, 'canonical_changes': 0, 'public_changes': 0,
        'unconfirmed_public_opinion_remainder': 5134,
        'koshitsu_criteria_gated_ids': 7,
        'identity_set_sha256': fingerprint([{k: r[k] for k in ('topic', 'record_id_hash', 'body_sha256', 'classification_sha256', 'criteria_sha256')} for r in results]),
        'activity_evidence': activity,
    }
    stable_proofs = [proof(Path(name)) for name in sorted(proofs)]
    return summary, {'summary': summary, 'records': results, 'source_fingerprints': stable_proofs}


def sha_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ('root', 'canonical-root', 'private-root', 'inventory', 'activity', 'summary-out', 'private-out'):
        p.add_argument('--' + arg, type=Path, required=True)
    a = p.parse_args()
    if a.private_out.resolve().is_relative_to(a.root.resolve()):
        raise ValueError('ID evidence must stay outside repository')
    if a.summary_out.exists() or a.private_out.exists():
        raise ValueError('do not overwrite previous investigation')
    summary, evidence = inspect(a.root.resolve(), a.canonical_root.resolve(), a.private_root.resolve(), a.inventory.resolve(), a.activity.resolve())
    for path, value in ((a.summary_out, summary), (a.private_out, evidence)):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
