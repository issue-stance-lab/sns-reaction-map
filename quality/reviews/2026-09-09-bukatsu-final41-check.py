"""Read-only reproduction of the 41-record decision and hypothetical counts.

Run with --root (authoritative repository) and --run (private evidence directory).
Prints a body-free report; never changes source data or adoption ledgers.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def totals(rows):
    opinions = [r for r in rows if r['is_relevant'] and r['is_opinion']]
    return {'raw': len(rows), 'relevant': sum(r['is_relevant'] for r in rows),
            'opinions': len(opinions),
            'issues': dict(sorted(Counter(r['main_issue'] for r in opinions).items())),
            'stances': dict(sorted(Counter(r['stance'] for r in opinions).items()))}


def verify(root, run):
    packet = read(run / 'packet.private.json')
    parents = read(run / 'parent-review.private.json')
    auditors = read(run / 'independent-review.private.json')
    followup = read(run / 'independent-followup.private.json')
    final = read(run / 'final-decisions.private.json')
    rationale = {r['id']: r for r in read(run / 'final-rationale.private.json')}
    baseline = read(run / 'baseline.private.json')
    assert sha(run / 'canonical-before.private.json') == baseline['social-samples/bukatsu-chiiki_hermes_classified.json']
    rows = packet['records']
    assert len(rows) == 41 and len({r['record_id_hash'] for r in rows}) == 41
    assert {r['id'] for r in rows} == set(range(1, 42))
    byid = {r['id']: r for r in rows}
    for review in (parents, auditors, final):
        assert len(review['records']) == 41
        assert {r['id'] for r in review['records']} == set(byid)
        for r in review['records']:
            assert r['record_id_hash'] == byid[r['id']]['record_id_hash']
            assert r['body_sha256'] == byid[r['id']]['body_sha256']
    audit = {r['id']: r for r in auditors['records']}
    for r in followup['records']:
        assert r['record_id_hash'] == byid[r['id']]['record_id_hash']
        assert r['body_sha256'] == byid[r['id']]['body_sha256']
        audit[r['id']] = r
    fields = ('is_relevant', 'is_opinion', 'main_issue', 'stance')
    raw = read(run / 'canonical-before.private.json')
    current = [{f: r['classification'][f] for f in fields} for r in raw]
    # Use snapshot ID hash implementation from the frozen source version.
    import sys
    sys.path.insert(0, str(root / 'scripts'))
    from verification_data import record_id_hash
    indices = {record_id_hash(r): i for i, r in enumerate(raw)}
    assert len(indices) == len(raw)
    candidate = [dict(c) for c in current]
    changes = Counter()
    for r in final['records']:
        original = byid[r['id']]
        index = indices[r['record_id_hash']]
        assert hashlib.sha256(raw[index]['text'].encode()).hexdigest() == r['body_sha256']
        assert fingerprint(current[index]) == original['classification_sha256']
        assert r['classification_sha256'] == original['classification_sha256']
        assert r['reason_sha256'] == hashlib.sha256(rationale[r['id']]['parent_final_reason'].encode()).hexdigest()
        assert r['independent_reason_sha256'] == hashlib.sha256(audit[r['id']]['reason'].encode()).hexdigest()
        assert rationale[r['id']]['independent_reason'] == audit[r['id']]['reason']
        assert r['pending_fields'] == [k for k, v in r['proposed'].items() if v is None]
        assert r['apply_candidate'] == (r['decision'] in {'accept_proposal', 'alternative'})
        assert original['saved_decision']['adoption_status'] == 'accepted'
        assert original['saved_proposed'] != current[index]
        if r['decision'] == 'hold':
            assert r['apply_candidate'] is False and r['pending_fields']
            continue
        assert not r['pending_fields']
        assert not audit[r['id']]['unresolved_fields']
        assert r['proposed'] == audit[r['id']]['proposed'], 'independent support missing'
        assert set(r['proposed']) == set(fields)
        assert type(r['proposed']['is_relevant']) is bool
        assert type(r['proposed']['is_opinion']) is bool
        assert r['proposed']['main_issue'] in {x['label'] for x in packet['criteria']['issues']}
        assert r['proposed']['stance'] in {x['label'] for x in packet['criteria']['stances']}
        if r['decision'] == 'accept_proposal':
            assert r['proposed'] == original['saved_proposed']
        elif r['decision'] == 'retain_current':
            assert r['proposed'] == current[index]
        else:
            assert r['decision'] == 'alternative'
            assert r['proposed'] != original['saved_proposed']
            assert r['proposed'] != current[index]
        candidate[index] = r['proposed']
        for f in fields:
            changes[f] += current[index][f] != candidate[index][f]
    mismatches = [name for name, expected in baseline.items() if sha(root / name) != expected]
    assert not mismatches, f'protected files changed: {mismatches}'
    reasons = read(run / 'saved-reasons.private.json')
    assert not reasons['missing'] and len(reasons['matched']) == 82
    for name, expected in reasons['source_hashes'].items():
        assert sha(Path(name)) == expected
    for r in rows:
        assert sha(Path(r['source']['path'])) == r['source']['sha256']
        source = read(Path(r['source']['path']))
        assert r['saved_decision'] in source.get('records', source.get('journal', []))
    return {'target': 41, 'decisions': dict(Counter(r['decision'] for r in final['records'])),
            'current': totals(current), 'hypothetical': totals(candidate),
            'changed_fields_overlapping': dict(changes),
            'protected_files_unchanged': len(baseline), 'saved_reasons_verified': 82,
            'new_reread_credit': 0, 'canonical_changes': 0, 'adoption_ledger_changes': 0,
            'public_changes': 0, 'records': final['records'],
            'evidence_hashes': {p.name: sha(p) for p in sorted(run.glob('*.json'))
                                if not p.name.startswith('2026-09-09-bukatsu-final41-')}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.root.resolve(), args.run.resolve()), ensure_ascii=False, indent=2))
