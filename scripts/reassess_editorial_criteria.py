"""Reassess the independently scoped 59 records, preserving the original ledger."""
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

from scripts.verify_editorial_hundred import read, sha, dump

HISTORY = 'quality/reviews/2026-09-07-criteria-reassessment59.json'
SCOPE = 'quality/reviews/2026-09-07-criteria-scope65.json'
LEDGER = 'data/verification/editorial-adoption.json'
EVENT = 'criteria-scope65-reassessment59-v1'
BASIS = 'scoped_criteria_reassessment'


def digest(value):
    return hashlib.sha256((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()).hexdigest()


def identity(row):
    return row['topic'], row['record_id_hash']


def restore_baseline(current, history):
    """Verify the exact after-state, then reconstruct the byte-identical before-state."""
    marker = {'event': EVENT, 'history': HISTORY, 'history_sha256': digest(history)}
    if current.get('reassessment') != marker or history.get('event') != EVENT:
        raise ValueError('reassessment history changed')
    changes = history['records']
    if len(changes) != 59 or len({identity(c['before']) for c in changes}) != 59:
        raise ValueError('59 unique reassessments required')
    rows = {identity(r): r for r in current['records']}
    if len(rows) != len(current['records']):
        raise ValueError('duplicate ledger identities')
    baseline = copy.deepcopy(history['before_metadata'])
    baseline['records'] = copy.deepcopy(current['records'])
    restored = {identity(r): r for r in baseline['records']}
    for change in changes:
        before = change['before']
        if before['adoption_status'] != 'pending_evidence' or before['adoption_basis'] != 'criteria_issue':
            raise ValueError('only criteria-blocked records may be reassessed')
        expected = {**before, 'adoption_status': 'accepted', 'adoption_basis': BASIS,
                    'reassessment_event': EVENT}
        if rows.get(identity(before)) != expected:
            raise ValueError('reassessment after-state changed')
        restored[identity(before)].clear()
        restored[identity(before)].update(before)
    # Preserve the original top-level ordering for the saved byte hash.
    baseline = {k: baseline[k] for k in history['before_key_order']}
    if digest(baseline) != history['baseline_sha256']:
        raise ValueError('original ledger cannot be reconstructed')
    expected_metadata = {k: v for k, v in baseline.items() if k != 'records'}
    expected_metadata['counts'] = dict(Counter(r['adoption_status'] for r in current['records']))
    expected_metadata['reassessment'] = marker
    if {k: v for k, v in current.items() if k != 'records'} != expected_metadata:
        raise ValueError('unexpected current ledger metadata')
    return baseline


def load_baseline(root):
    current = read(Path(root) / LEDGER)
    if 'reassessment' not in current:
        return current
    return restore_baseline(current, read(Path(root) / HISTORY))


def assess(root, run, baseline):
    from scripts.scope_editorial_criteria import build
    root, run = Path(root), Path(run)
    saved_scope = read(root / SCOPE)
    if saved_scope != build(root, run, ledger=baseline):
        raise ValueError('scope or source evidence changed; repeat scope review')
    targets = [r for r in saved_scope['records'] if r['queue'] == 'reassessment_ready']
    if len(targets) != 59:
        raise ValueError('expected 59 independently scoped candidates')
    rows = {identity(r): r for r in baseline['records']}
    changes = []
    for target in targets:
        before = rows[identity(target)]
        if before['adoption_status'] != 'pending_evidence' or before['adoption_basis'] != 'criteria_issue':
            raise ValueError('unexpected prior adoption')
        if before['route'] == 'change_candidate' and before['independently_checked'] is not True:
            raise ValueError('correction lacks independent audit')
        changes.append({'before': copy.deepcopy(before)})
    return {'schema_version': 1, 'event': EVENT, 'baseline_sha256': digest(baseline),
            'scope_sha256': sha(root / SCOPE),
            'before_key_order': list(baseline),
            'before_metadata': {k: copy.deepcopy(v) for k, v in baseline.items() if k != 'records'},
            'reason': 'Independently reviewed topic scope excludes these records; original evidence, conflicts and sample audit conditions replayed successfully.',
            'records': changes, 'new_body_reviews': 0, 'canonical_changes': 0,
            'registered_reread_increment': 0}


def apply_history(baseline, history):
    result = copy.deepcopy(baseline)
    bykey = {identity(r): r for r in result['records']}
    for change in history['records']:
        r = bykey[identity(change['before'])]
        if r != change['before']:
            raise ValueError('history before-state mismatch')
        r.update(adoption_status='accepted', adoption_basis=BASIS, reassessment_event=EVENT)
    result['counts'] = dict(Counter(r['adoption_status'] for r in result['records']))
    result['reassessment'] = {'event': EVENT, 'history': HISTORY, 'history_sha256': digest(history)}
    if restore_baseline(result, history) != baseline:
        raise ValueError('history round trip failed')
    return result


def verify_reassessment(root, run):
    root = Path(root)
    current = read(root / LEDGER)
    baseline = load_baseline(root)
    if 'reassessment' not in current:
        return baseline, None
    history = read(root / HISTORY)
    if history != assess(root, run, baseline) or current != apply_history(baseline, history):
        raise ValueError('reassessment differs from saved evidence')
    return baseline, history


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--run', type=Path, required=True)
    a = p.parse_args()
    current = read(a.root / LEDGER)
    baseline = load_baseline(a.root)
    history = assess(a.root, a.run, baseline)
    updated = apply_history(baseline, history)
    if 'reassessment' in current:
        verify_reassessment(a.root, a.run)
    else:
        if (a.root / HISTORY).exists() and read(a.root / HISTORY) != history:
            raise ValueError('existing history must not be overwritten')
        dump(a.root / HISTORY, history)
        temp = (a.root / LEDGER).with_suffix('.json.tmp')
        dump(temp, updated)
        temp.replace(a.root / LEDGER)
    print(json.dumps(updated['counts'], ensure_ascii=False))
