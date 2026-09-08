"""Freeze unresolved-ID routes without granting reading credit or reserving work.

An input job is shared by byte-identical bodies under the same topic, source
classification, and criteria version. Every distinct post ID still needs its
own completion evidence; an alias link alone never completes an ID.
"""
from collections import Counter, defaultdict
from pathlib import Path
import argparse
import json

from scripts.editorial_work_registry import fingerprint, load_registry
from scripts.inventory_remaining_body_reviews import input_key, post_key, inspect
from scripts.prepare_editorial_continuation import build_criteria
from scripts.verify_editorial_hundred import sha


ROUTES = {
    'unfinished_legacy_pilot': 'resume_unfinished_review',
    'invalid_run_reserved_id': 'restart_invalid_reservation',
    'same_input_as_existing_work_different_id': 'verify_distinct_id_against_existing_review',
    'same_input_as_another_unconfirmed_id': 'verify_distinct_id_after_primary_review',
}
IDENTITY = ('topic', 'record_id_hash', 'body_sha256', 'classification_sha256')


def identity(row):
    return {k: row[k] for k in IDENTITY}


def build_resolution(inventory, work, criteria):
    raw = inventory['raw_remaining']
    by_id = {post_key(r): r for r in raw}
    if len(by_id) != len(raw):
        raise ValueError('duplicate unresolved topic/post ID')
    eligible = {post_key(r): r for r in inventory['eligible_inventory_only']}
    excluded = {post_key(r): r for r in inventory['excluded_unconfirmed']}
    if (len(eligible) != len(inventory['eligible_inventory_only']) or
            len(excluded) != len(inventory['excluded_unconfirmed']) or
            set(eligible) & set(excluded) or set(eligible) | set(excluded) != set(by_id)):
        raise ValueError('inventory partition differs from unresolved IDs')
    work_by_input = defaultdict(list)
    work_by_id = {}
    for row in work['records']:
        key = post_key(row)
        if key in work_by_id:
            raise ValueError('multiple work versions require explicit reconciliation')
        work_by_id[key] = row
        work_by_input[input_key(row)].append(row)
    primary_by_input = {input_key(r): r for r in eligible.values()}
    if len(primary_by_input) != len(eligible):
        raise ValueError('duplicate ordinary input jobs')
    entries = []
    for key, raw_row in sorted(by_id.items()):
        item = eligible.get(key, excluded.get(key))
        if identity(item) != identity(raw_row):
            raise ValueError('partition body or classification changed')
        source, predecessor = None, None
        reasons = item.get('exclusion_reasons', [])
        if key in excluded and not reasons:
            raise ValueError('excluded record lacks its original reason')
        if not reasons:
            route = 'new_body_review'
            if input_key(item) in work_by_input:
                raise ValueError('ordinary input already in work registry')
        else:
            if len(reasons) != 1 or reasons[0] not in ROUTES:
                raise ValueError('unknown or overlapping exclusion requires review')
            route = ROUTES[reasons[0]]
        criteria_sha = fingerprint(criteria[item['topic']])
        if route == 'resume_unfinished_review':
            predecessor = work_by_id.get(key)
            if not predecessor or predecessor['state'] != 'attempted':
                raise ValueError('legacy record no longer an unfinished attempt')
            source = predecessor
        elif route == 'restart_invalid_reservation':
            if key in work_by_id or input_key(item) in work_by_input:
                raise ValueError('invalid reservation now has registered work')
        elif route == 'verify_distinct_id_against_existing_review':
            candidates = work_by_input.get(input_key(item), [])
            if len(candidates) != 1 or candidates[0]['state'] == 'attempted':
                raise ValueError('alias needs one completed source review')
            source = candidates[0]
            if post_key(source) == key:
                raise ValueError('alias cannot reference its own post ID')
        elif route == 'verify_distinct_id_after_primary_review':
            source = primary_by_input.get(input_key(item))
            if not source or post_key(source) == key:
                raise ValueError('alias primary review missing')
        if source:
            if input_key(source) != input_key(item):
                raise ValueError('dependency input version differs')
            if source.get('criteria_sha256', criteria_sha) != criteria_sha:
                raise ValueError('dependency criteria version differs')
        gates = ['fresh_source_and_assignment_check', 'separate_editor_and_independent_auditor',
                 'post_specific_body_attribution_and_context_evidence']
        if route.startswith('verify_distinct_id_'):
            gates.append('independent_verification_of_every_alias_id_before_any_completion_credit')
        if item['topic'] == 'koshitsu-tenpakai':
            gates.append('koshitsu_separate_axes_v2_independent_validation')
        entries.append({
            **identity(item), 'criteria_sha256': criteria_sha,
            'route': route, 'original_exclusion_reasons': reasons,
            'state': 'unconfirmed', 'reservation_state': 'not_reserved',
            'input_job_key': fingerprint([*input_key(item), criteria_sha]),
            'dependency': identity(source) if source else None,
            'dependency_work_key': source.get('work_key') if source else None,
            'prior_attempt_preserved': predecessor['work_key'] if predecessor else None,
            'required_gates': gates, 'body_review_credit': 0,
            'post_completion_credit': 0, 'adoption_transfer_allowed': False,
        })
    routes = Counter(r['route'] for r in entries)
    primary_routes = {'new_body_review', 'resume_unfinished_review', 'restart_invalid_reservation'}
    primary = [r for r in entries if r['route'] in primary_routes]
    if len({r['input_job_key'] for r in primary}) != len(primary):
        raise ValueError('reopened input collides with another primary job')
    return {
        'schema_version': 1, 'scope': 'Resolved routing only; not execution reservations or reading evidence.',
        'target_topic_post_records': len(entries),
        'target_global_post_ids': len({r['record_id_hash'] for r in entries}),
        'route_counts': dict(sorted(routes.items())),
        'primary_body_review_inputs': len(primary),
        'distinct_id_verification_records': len(entries) - len(primary),
        'total_distinct_input_versions': len({r['input_job_key'] for r in entries}),
        'koshitsu_gated_records': sum(r['topic'] == 'koshitsu-tenpakai' for r in entries),
        'new_body_reviews': 0, 'completed_post_ids': 0, 'reservations_created': 0,
        'execution_constraints': {
            'cycle_records_max': 1000, 'body_packet_records_max': 20,
            'one_topic_per_packet': True, 'last_134_topic_homogeneous_packets_max_20': True,
            'completed_source_review_is_not_alias_id_completion': True,
            'old_attempts_and_invalid_reservations_preserved': True,
            'new_execution_reservations_require_fresh_checks': True,
        },
        'records': entries,
    }


def freeze(root, canonical_root, private_root, run, inventory_path, out):
    root, canonical_root, private_root, run, inventory_path, out = map(
        lambda p: Path(p).resolve(), (root, canonical_root, private_root, run, inventory_path, out))
    if out.exists() or out.is_relative_to(root):
        raise ValueError('new private evidence directory required')
    old_inventory = json.loads(inventory_path.read_text())
    summary, current = inspect(root, canonical_root, private_root, run)
    for key in ('raw_remaining', 'eligible_inventory_only', 'excluded_unconfirmed', 'canonical_sha256'):
        if current[key] != old_inventory[key]:
            raise ValueError('inventory changed since discrepancy was reported: ' + key)
    if summary['raw_unconfirmed_id_remainder'] != 5134 or summary['eligible_unique_inputs'] != 4769:
        raise ValueError('target counts changed; do not force the previous scope')
    work_path = root / 'data/verification/editorial-work.json'
    final_audit = json.loads((root / 'quality/reviews/2026-09-08-task63-final-work-audit.json').read_text())
    if sha(work_path) != final_audit['work_registry_sha256']:
        raise ValueError('finalized 8080-record work registry changed')
    work = load_registry(work_path, root, private_root)
    resolution = build_resolution(current, work, build_criteria(root))
    resolution['provenance'] = {
        'inventory_sha256': sha(inventory_path), 'work_registry_sha256': sha(work_path),
        'run_reservation_sha256': sha(run / 'reservation.json'),
        'canonical_sha256': current['canonical_sha256'],
        'authorization': 'Owner requested discrepancy-resolution work after the 365-record difference report.',
    }
    out.mkdir(parents=True)
    path = out / 'scope-resolution.private.json'
    path.write_text(json.dumps(resolution, ensure_ascii=False, indent=2) + '\n')
    return {k: v for k, v in resolution.items() if k != 'records'} | {
        'resolution_path': str(path.relative_to(private_root)), 'resolution_sha256': sha(path)}


def load_resolution(summary, private_root):
    """Read a committed routing summary; never returns a completed-work ledger."""
    private_root = Path(private_root).resolve()
    path = (private_root / summary['resolution_path']).resolve()
    if not path.is_relative_to(private_root) or sha(path) != summary['resolution_sha256']:
        raise ValueError('resolution evidence missing or changed')
    result = json.loads(path.read_text())
    if {k: v for k, v in result.items() if k != 'records'} != {
            k: v for k, v in summary.items() if k not in {'resolution_path', 'resolution_sha256'}}:
        raise ValueError('summary differs from routing evidence')
    if any(r['state'] != 'unconfirmed' or r['post_completion_credit'] or
           r['body_review_credit'] or r['adoption_transfer_allowed'] for r in result['records']):
        raise ValueError('routing evidence cannot grant completion or adoption')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'canonical-root', 'private-root', 'run', 'inventory', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.root, args.canonical_root, args.private_root, args.run,
                            args.inventory, args.out), ensure_ascii=False, indent=2))
