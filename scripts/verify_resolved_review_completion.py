"""Verify completed non-royal targets by ID without granting extra review credit."""
from collections import Counter
from pathlib import Path

from scripts.finalize_resolved_review_cycle import collect as collect_cycle
from scripts.short_resolved_review import collect as collect_short
from scripts.editorial_work_registry import load_registry
from scripts.resolve_remaining_review_scope import load_resolution
from scripts.verify_editorial_hundred import read, sha
from scripts.review_completion_identity_counts import identity_counts


def verify(root, private, shared, cycles, short_run):
    root, private, shared = (Path(p).resolve() for p in (root, private, shared))
    if len(cycles) != 4:
        raise ValueError('four completed ordinary cycles required')
    scope = load_resolution(read(root / 'data/verification/editorial-review-scope.json'), private)
    work = load_registry(root / 'data/verification/editorial-work.json', root, private)
    completed = {(r['topic'], r['record_id_hash']): r for r in work['records'] if r['state'] != 'attempted'}
    reports = []
    for run, report_path in cycles:
        saved = read(root / report_path)
        current = collect_cycle(root, private, Path(run), [Path(x['path']) for x in saved['supplements']])
        if saved != current:
            raise ValueError('saved cycle report differs from completed evidence')
        reports.append(current)
    short_run, short_report_path = short_run
    short = collect_short(root, Path(short_run))
    if short != read(root / short_report_path):
        raise ValueError('saved short report differs from completed evidence')
    reports.append(short)
    rows = [r for report in reports for r in report['journal']]
    by_id = {(r['topic'], r['record_id_hash']): r for r in rows}
    targets = {(r['topic'], r['record_id_hash']): r for r in scope['records'] if r['topic'] != 'koshitsu-tenpakai'}
    if len(rows) != 4352 or len(by_id) != 4352 or set(by_id) != set(targets):
        raise ValueError('completed ID set differs from all 4352 non-royal targets')
    for key, row in by_id.items():
        original, registered = targets[key], completed.get(key)
        if registered is None:
            raise ValueError('completed target lacks formal work registration')
        if any(original[k] != row[k] or row[k] != registered[k] for k in ('body_sha256', 'classification_sha256')):
            raise ValueError('target body/classification version changed')
        if original['criteria_sha256'] != registered['criteria_sha256']:
            raise ValueError('registered target criteria version changed')
        if row['adoption_status'] not in {'accepted', 'hold', 'pending_evidence'}:
            raise ValueError('unfinished adoption decision')
    remaining = [r for r in scope['records'] if (r['topic'], r['record_id_hash']) not in completed]
    if len(remaining) != 782 or {r['topic'] for r in remaining} != {'koshitsu-tenpakai'}:
        raise ValueError('remaining ID set is not exactly the 782 paused royal targets')
    protected_path = private / 'body-review-pilot/20260908-finish5134-handoff/protected-before.private.json'
    protected = read(protected_path)
    if any(not (shared / rel).is_file() or sha(shared / rel) != h for rel, h in protected.items()):
        raise ValueError('shared protected file changed')
    if any(not (root / rel).is_file() or sha(root / rel) != h for rel, h in protected.items()):
        raise ValueError('worktree protected file changed')
    aliases = [r for r in short['journal'] if r['scope_route'].startswith('verify_distinct_id_')]
    if len(aliases) != 127 or any(not r['independently_checked'] for r in aliases):
        raise ValueError('distinct-ID verification lacks independent completion')
    baseline_path = private / 'body-review-pilot/20260908-nonkoshitsu-cycle01/work-before.private.json'
    if sha(baseline_path) != scope['provenance']['work_registry_sha256']:
        raise ValueError('initial completed-work baseline changed')
    identities = identity_counts([r['journal'] for r in reports], scope, read(baseline_path))
    if any(identities['blocking'].values()):
        raise ValueError('duplicate completed post or input version')
    return {'schema_version': 1, 'completed_target_records': len(rows),
            'identity_counts': identities,
            'new_body_reviews': len(rows) - len(aliases), 'distinct_id_verifications': len(aliases),
            'independent_audits': sum(r['independent_records'] for r in reports),
            'supplemental_audits': sum(r.get('supplemental_audits', 0) for r in reports),
            'adoption_counts': dict(Counter(r['adoption_status'] for r in rows)),
            'remaining_public_opinion_records': len(remaining), 'remaining_non_royal_records': 0,
            'paused_royal_records': len(remaining), 'work_registry_records': len(work['records']),
            'remaining_ids': [{'topic': r['topic'], 'record_id_hash': r['record_id_hash'],
                               'body_sha256': r['body_sha256'], 'classification_sha256': r['classification_sha256']}
                              for r in remaining],
            'protected_files_unchanged': len(protected), 'canonical_changes': 0,
            'adoption_changes': 0, 'public_changes': 0}
