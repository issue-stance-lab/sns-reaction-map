#!/usr/bin/env python3
"""訂正結果を再現・照合する。本文を表示せず、判定・原本・公開物へ書き込まない。"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

TOPIC = 'bukatsu-chiiki'
PREFIX = 'quality/reviews/2026-09-09-bukatsu-'
RUN = 'body-review-pilot/20260909-bukatsu-triage-fix'
FIELDS = ('is_relevant', 'is_opinion', 'main_issue', 'stance')


def read(path):
    return json.loads(path.read_text())


def sha(value):
    return hashlib.sha256(value).hexdigest()


def fingerprint(value):
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())


def build(root, raw_root, private):
    sys.path.insert(0, str(root / 'scripts'))
    from verification_data import record_id_hash
    from prepare_body_review_pilot import resolve_legacy_source
    from manage_reread_registry import check_sources
    from reread_registry import validate_manifest
    import classify_bukatsu_arena_hermes as classifier

    raw_path = raw_root / 'social-samples/bukatsu-chiiki_hermes_classified.json'
    raw = read(raw_path)
    current = {record_id_hash(r): r for r in raw}
    assert len(raw) == len(current) == 1395
    work = read(root / 'data/verification/editorial-work.json')
    work = {r['record_id_hash']: r for r in work['records'] if r['topic'] == TOPIC}
    assert len(work) == 411
    for key, r in work.items():
        canonical = current[key]
        fields = {f: canonical['classification'][f] for f in FIELDS}
        assert r['body_sha256'] == sha(canonical['text'].encode()), key
        assert r['classification_sha256'] == fingerprint(fields), key

    ledger = read(root / 'data/verification/reread/bukatsu-chiiki.json')
    validate_manifest(ledger)
    check_sources(raw_root, ledger)
    assert ledger['canonical_sha256'] == sha(raw_path.read_bytes())
    by_post_key = {sha(str(r['tweet_id']).encode()): record_id_hash(r) for r in raw}
    legacy = {by_post_key[r['post_key']] for r in ledger['records'] if r['review']}
    assert len(legacy) == 966 and not legacy.intersection(work)
    inventory_path = private / 'reread-inventory/20260906-v1/bukatsu-chiiki.json'
    inventory = read(inventory_path)
    assert inventory['baseline_sha256'] == sha(raw_path.read_bytes())
    limited = {record_id_hash({'tweet_id': i}) for i in inventory['focused_body_review_ids'] + inventory['classification_review_ids']}
    limited_sources = []
    for source in inventory['sources']:
        if source['kind'] not in {'focused_body_review', 'classification_review', 'classification_body_review'}:
            continue
        path = resolve_legacy_source(source['path'], raw_root, private)
        assert sha(path.read_bytes()) == source['sha256']
        limited_sources.append({'path': source['path'], 'sha256': source['sha256']})
    outside = sorted(current.keys() - work.keys() - legacy)
    assert len(outside) == 18 and len(set(outside) & limited) == 5
    outside_rows = []
    for key in outside:
        r = current[key]
        outside_rows.append({'record_id_hash': key, 'body_sha256': sha(r['text'].encode()),
                             'classification_sha256': fingerprint({f: r['classification'][f] for f in FIELDS}),
                             'in_current_opinions': bool(r['classification']['is_relevant'] and r['classification']['is_opinion']),
                             'limited_review_evidence': key in limited})
    assert sum(r['in_current_opinions'] for r in outside_rows) == 5

    spec = importlib.util.spec_from_file_location('triage312', root / (PREFIX + 'triage312.py'))
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    _, rows = old.build(root, private)
    assert len(rows) == 312
    original_c1b = {r['record_id_hash'] for r in rows if r['group'] == 'C1b'}
    routing = read(root / (PREFIX + 'reasons27.json'))['records']
    route_by_key = {r['record_id_hash']: r for r in routing}
    assert len(routing) == len(route_by_key) == 27 and route_by_key.keys() == original_c1b
    saved = read(private / RUN / 'saved-reasons27.private.json')
    for path, expected in saved['source_hashes'].items():
        assert sha((private / path).read_bytes()) == expected, path
    saved_by_key = {r['record_id_hash']: r for r in saved['records']}
    adoption = {r['record_id_hash']: r for r in read(root / 'data/verification/editorial-adoption-current.json')['records'] if r['topic'] == TOPIC}
    for r in routing:
        key = r['record_id_hash']
        evidence = saved_by_key[key]
        journal = next(x for x in read(root / r['source_journal'])['journal'] if x['record_id_hash'] == key)
        effective = adoption.get(key, journal)
        assert r['proposed'] == effective['proposed'] == effective['independent_proposed']
        assert effective['adoption_status'] == r['adoption_status'] == 'hold'
        assert r['classification_sha256'] == work[key]['classification_sha256']
        assert r['body_sha256'] == work[key]['body_sha256']
        assert r['review_flags'] == evidence['review_flags']
        for field, digest in [('reason', 'reason_sha256'), ('independent_reason', 'independent_reason_sha256')]:
            assert r[digest] == effective[digest]
            assert evidence[field] and all(sha(x['text'].encode()) == r[digest] for x in evidence[field])
        if r['bucket'] == 'A':
            assert all(f['evidence_sufficient'] is True for f in r['review_flags'].values())
    assert Counter(r['bucket'] for r in routing) == {'A': 6, 'B': 4, 'C': 17}

    rules11 = read(root / (PREFIX + 'rules11-results.json'))['records']
    resolved = {r['record_id_hash'] for r in rules11 if r['decision'] == 'resolved_by_rule'}
    held = {r['record_id_hash'] for r in rules11 if r['decision'] == 'hold'}
    assert len(resolved) == 7 and len(held) == 4
    result_rows = []
    for r in rows:
        key = r['record_id_hash']
        if key in resolved:
            continue
        r = dict(r)
        r['classification_sha256'] = work[key]['classification_sha256']
        if key in held:
            r.update(bucket='C', group='C_rules11_hold')
        if key in route_by_key:
            route = route_by_key[key]
            r.update(bucket=route['bucket'], group=route['bucket'] + '_saved_reason27', reason_review_id=route['id'])
        result_rows.append(r)
    result_rows.sort(key=lambda r: (r['bucket'], r['group'], r['record_id_hash']))
    assert len(result_rows) == len({r['record_id_hash'] for r in result_rows}) == 305

    config_path = 'configs/bukatsu-chiiki-reaction-map.json'
    classifier_path = 'scripts/classify_bukatsu_arena_hermes.py'
    baseline_ref = '9b9ca3b'
    old_config_bytes = subprocess.check_output(['git', 'show', baseline_ref + ':' + config_path], cwd=root)
    old_classifier = subprocess.check_output(['git', 'show', baseline_ref + ':' + classifier_path], cwd=root)
    assert old_classifier == (root / classifier_path).read_bytes()
    prompt_now = classifier.prompt_for([])
    old_config = json.loads(old_config_bytes)['arena_taxonomy']
    defs, stances = classifier.ISSUE_DEFS, classifier.STANCES
    try:
        classifier.ISSUE_DEFS = old_config['issues']
        classifier.STANCES = [r['label'] for r in old_config['stances']]
        prompt_before = classifier.prompt_for([])
    finally:
        classifier.ISSUE_DEFS, classifier.STANCES = defs, stances
    dependencies = [classifier_path, 'scripts/bukatsu_taxonomy.py', config_path,
                    'quality/designs/2026-09-09-bukatsu-classification-rules.md']
    criteria = {
        'schema_version': 1, 'topic': TOPIC, 'baseline_ref': baseline_ref,
        'method': 'prompt_for([]), UTF-8, exact whitespace; no model invocation. Baseline uses identical classifier with baseline config.',
        'dependencies_sha256': {p: sha((root / p).read_bytes()) for p in dependencies},
        'baseline_config_sha256': sha(old_config_bytes),
        'baseline_rendered_prompt_sha256': sha(prompt_before.encode()),
        'current_rendered_prompt_sha256': sha(prompt_now.encode()),
        'baseline_review_criteria_text_sha256': sha(prompt_before.split('JSON配列')[0].strip().encode()),
        'current_review_criteria_text_sha256': sha(prompt_now.split('JSON配列')[0].strip().encode()),
        'approval_ids': ['approval-20260909-002', 'approval-20260909-003'],
        'supplement_rules': ['1', '2', '3', '4', '5', '6', '7', '7-b'],
        'usage': 'Attach this version and the rules to subsequent judgments. Do not overwrite historical criteria hashes. This snapshot does not implement migration or update the production pipeline.',
    }
    criteria['effective_review_version_sha256'] = fingerprint(criteria)
    counts = dict(sorted(Counter(r['bucket'] for r in result_rows).items()))
    assert counts == {'A': 6, 'B': 135, 'C': 164}
    report = {
        'schema_version': 1, 'topic': TOPIC,
        'meaning': 'Routing snapshot after rules11 and saved-reason review. A is a final-judgment candidate, still held. Resolved means decisions available, not canonical application.',
        'raw_records': 1395, 'current_opinions': sum(bool(r['classification']['is_relevant'] and r['classification']['is_opinion']) for r in raw),
        'partition': {'work_registry': 411, 'legacy_review': 966, 'outside_both': 18},
        'judgment_records': 410, 'attempted_without_judgment': 1,
        'resolved_decisions': 105, 'unresolved_including_A_candidates': 305,
        'bucket_counts': counts, 'reason27_counts': {'A': 6, 'B': 4, 'C': 17},
        'outside_records': outside_rows, 'limited_evidence_sources': limited_sources,
        'limited_inventory_sha256': sha(inventory_path.read_bytes()),
        'saved_reason_evidence_sha256': sha((private / RUN / 'saved-reasons27.private.json').read_bytes()),
        'effective_review_version_sha256': criteria['effective_review_version_sha256'],
        'new_body_reviews': 0, 'new_adoption_decisions': 0, 'canonical_changes': 0, 'public_changes': 0,
        'records': result_rows,
    }
    assert report['current_opinions'] == 1139
    return {'triage-current.json': report, 'criteria-version.json': criteria}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--raw-root', type=Path, required=True)
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--write', action='store_true', help='訂正結果のJSON 2本のみ書く。省略時は保存値を照合')
    args = parser.parse_args()
    results = build(args.root.resolve(), args.raw_root.resolve(), args.private_root.resolve())
    for name, value in results.items():
        path = args.root / (PREFIX + name)
        if args.write:
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        else:
            assert read(path) == value, '保存結果との不一致: ' + name
    report = results['triage-current.json']
    print(json.dumps({k: report[k] for k in ['partition', 'resolved_decisions', 'unresolved_including_A_candidates', 'bucket_counts', 'reason27_counts']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
