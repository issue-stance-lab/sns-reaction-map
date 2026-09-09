#!/usr/bin/env python3
"""部活動の265件確定・145件未解決という中間成果を証拠から照合する。

分類判定や台帳変更はしない。後日別の判定を加えた台帳をこの固定記録と混同しない。
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def check(root, private):
    sys.path.insert(0, str(root))
    from scripts.verification_data import record_id_hash
    from scripts.run_body_review_pilot import FIELDS, fingerprint

    original = read(private / 'adoption-before.private.json')
    current = read(root / 'data/verification/editorial-adoption-current.json')
    c1 = read(root / 'quality/reviews/2026-09-10-bukatsu-c1-decisions.json')
    c1_ids = {r['record_id_hash'] for r in c1['records']}
    untouched = lambda rows: [r for r in rows if r['topic'] != 'bukatsu-chiiki' or r['record_id_hash'] not in c1_ids]
    assert untouched(current['records'][:4000]) == untouched(original['records'])
    assert len(untouched(original['records'])) == 3977
    assert len(original['records']) == 4000 and len(current['records']) == 4224
    assert current['counts'] == dict(collections.Counter(r['adoption_status'] for r in current['records']))
    identities = [(r['topic'], r['record_id_hash']) for r in current['records']]
    assert len(identities) == len(set(identities))
    for source in current['sources']:
        assert sha(root / source['path']) == source['sha256'], source['path']

    raw_path = root / 'social-samples/bukatsu-chiiki_hermes_classified.json'
    assert sha(raw_path) == sha(private / 'canonical-before.private.json')
    raw = read(raw_path)
    by_hash = {record_id_hash(r): r for r in raw}
    assert len(raw) == len(by_hash) == 1395
    assert sum(bool(r['classification'].get('is_opinion')) for r in raw) == 1139
    added = current['records'][4000:]
    assert len(added) == 224 and all(r['topic'] == 'bukatsu-chiiki' for r in added)
    reviewed = added + [r for r in current['records'][:4000] if r['topic'] == 'bukatsu-chiiki' and r['record_id_hash'] in c1_ids]
    assert len(reviewed) == 247
    for r in reviewed:
        canonical = by_hash[r['record_id_hash']]
        assert hashlib.sha256(canonical['text'].encode()).hexdigest() == r['body_sha256']
        assert fingerprint({f: canonical['classification'].get(f) for f in FIELDS}) == r['classification_sha256']
        assert not r['canonical_applied'] and not r['counts_as_registered_editorial_reread']
        if r['adoption_status'] == 'accepted':
            assert r['independently_checked'] and r['proposed'] == r['independent_proposed']
            assert not r['remaining_uncertainty']

    before = read(root / 'quality/reviews/2026-09-09-bukatsu-triage-current.json')
    unresolved_ids = {r['record_id_hash'] for r in before['records']}
    assert len(unresolved_ids) == 305
    now_accepted = {r['record_id_hash'] for r in reviewed if r['adoption_status'] == 'accepted'}
    assert now_accepted <= unresolved_ids and len(now_accepted) == 160
    remaining = unresolved_ids - now_accepted
    assert len(remaining) == 145

    audited_ids = set()
    for number in range(1, 6):
        packet_path = private / f'b1-missing-audit-{number:02d}-packet.private.json'
        packet = read(packet_path)
        result = read(private / f'b1-missing-audit-{number:02d}-independent.private.json')
        assert len(packet['rows']) <= 20 and result['input_sha256'] == sha(packet_path)
        inputs = {r['record_id_hash']: r for r in packet['rows']}
        assert set(inputs) == {r['record_id_hash'] for r in result['rows']}
        assert not (set(inputs) & audited_ids)
        audited_ids |= set(inputs)
        for r in result['rows']:
            assert r['body_sha256'] == inputs[r['record_id_hash']]['body_sha256']
    assert len(audited_ids) == 83
    c1_confirmed = 0
    c1_seen = set()
    for number in range(1, 7):
        packet_path = private / f'c1-approved-rules-{number:02d}-packet.private.json'
        packet = read(packet_path)
        parent = read(private / f'c1-approved-rules-{number:02d}-parent.private.json')
        independent = read(private / f'c1-approved-rules-{number:02d}-independent.private.json')
        assert len(packet['rows']) <= 20
        assert parent['input_sha256'] == independent['input_sha256'] == sha(packet_path)
        inputs = {r['record_id_hash']: r for r in packet['rows']}
        others = {r['record_id_hash']: r for r in independent['rows']}
        assert set(inputs) == set(others) == {r['record_id_hash'] for r in parent['rows']}
        assert not (set(inputs) & c1_seen)
        c1_seen |= set(inputs)
        for r in parent['rows']:
            a = others[r['record_id_hash']]
            assert r['body_sha256'] == a['body_sha256'] == inputs[r['record_id_hash']]['body_sha256']
            c1_confirmed += bool(r['classification'] == a['classification'] and not r['uncertain'] and not a['uncertain'] and r['evidence_sufficient'] and a['evidence_sufficient'])
    assert len(c1_seen) == 110 and c1_confirmed == 58
    assert all(r['returncode'] == 0 for r in read(private / 'a6-final-generation-and-checks.private.json'))
    candidate = read(private / 'a6-candidate-files.private.json')
    for rel, digest in candidate['files'].items():
        assert sha(private / 'candidate-repo' / rel) == digest, rel
    assert read(private / 'a6-idempotence.private.json')['status'] == 'pass'
    for screen in read(private / 'a6-browser-check.private.json'):
        assert screen['width'] == screen['scrollWidth'] and screen['mountain']
        assert screen['has1143'] and not screen['errors']
    return {'status': 'pass', 'raw_records': 1395, 'canonical_opinions': 1139,
            'judgment_records': 410, 'resolved': 265, 'unresolved': 145,
            'resolved_this_work': 160, 'old_non_target_adoption_rows_preserved': 3977,
            'additional_independent_body_reviews': 193,
            'additional_parent_body_reviews': 133,
            'candidate_applied_records': 4, 'candidate_opinions': 1143,
            'canonical_applied': 0, 'published': False,
            'adoption_sha256': sha(root / 'data/verification/editorial-adoption-current.json')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--private-run', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.root.resolve(), args.private_run.resolve()), ensure_ascii=False, indent=2))
