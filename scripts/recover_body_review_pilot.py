#!/usr/bin/env python3
"""保存応答の提案を差分へ分解する。AI呼出し・自動承認・元記録の変更なし。"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
try:
    from scripts.run_body_review_pilot import FIELDS, fingerprint
except ModuleNotFoundError:
    from run_body_review_pilot import FIELDS, fingerprint


def recover(value, current, criteria):
    """変更のない項目を別記し、有効な差分もあくまで審査候補として保持する。"""
    if not isinstance(value, dict) or set(value) != {'id', 'status', 'fields', 'suggested', 'reason'}:
        raise ValueError('unexpected response fields')
    status = value['status']
    if status not in {'ok', 'candidate', 'uncertain'}:
        raise ValueError('invalid status')
    if not isinstance(value['reason'], str) or not value['reason'].strip() or len(value['reason']) > 150:
        raise ValueError('invalid reason')
    fields, proposed = value['fields'], value['suggested']
    if not isinstance(fields, list) or any(not isinstance(f, str) for f in fields):
        raise ValueError('invalid fields')
    if len(fields) != len(set(fields)) or not set(fields) <= FIELDS or not isinstance(proposed, dict) or set(fields) != set(proposed):
        raise ValueError('invalid suggestions')
    if (status == 'candidate') != bool(fields):
        raise ValueError('status/suggestion disagreement')
    for field, label in proposed.items():
        if field in {'is_relevant', 'is_opinion'} and type(label) is not bool:
            raise ValueError('invalid boolean')
        if field == 'main_issue' and label not in criteria['issues']:
            raise ValueError('invalid issue')
        if field == 'stance' and label not in criteria['stances']:
            raise ValueError('invalid stance')
    changes = {k: v for k, v in proposed.items() if v != current[k]}
    unchanged = sorted(k for k, v in proposed.items() if v == current[k])
    route = ('candidate_pending_review' if changes else 'contradictory_candidate') if status == 'candidate' else status + '_pending_review'
    return {'route': route, 'changes': changes, 'unchanged_fields': unchanged,
            'counts_as_editorial_reread': False, 'automatic_approval': False}


def build(directory):
    directory = Path(directory)
    source = json.loads((directory / 'pilot-input.json').read_text())
    if fingerprint(source['records']) != source['input_sha256']:
        raise ValueError('input fingerprint mismatch')
    refs = {r['sample_id']: r for r in json.loads((directory / 'reference-20.json').read_text())['reviews']}
    journal, proofs, seen = [], {}, set()
    for path in sorted((directory / 'batches').glob('*.json')):
        batch = json.loads(path.read_text())
        if batch['request']['input_sha256'] != source['input_sha256']:
            raise ValueError('batch input mismatch')
        rows = [r for r in source['records'] if r['topic'] == batch['request']['topic'] and r['phase'] == batch['request']['phase']]
        raw = batch['raw_response'].strip()
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[1].rsplit('```', 1)[0].strip()
        values = json.loads(raw)
        if not isinstance(values, list) or any(not isinstance(v, dict) or type(v.get('id')) is not int for v in values):
            raise ValueError('invalid batch')
        if sorted(v['id'] for v in values) != list(range(len(rows))):
            raise ValueError('duplicate/missing ID')
        proofs[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        for value in values:
            row = rows[value['id']]; sid = row['sample_id']
            if sid in seen:
                raise ValueError('duplicate sample')
            seen.add(sid)
            try:
                recovered = recover(value, row['classification'], source['criteria'][row['topic']])
            except (ValueError, TypeError, KeyError) as error:
                recovered = {'route': 'invalid_pending_review', 'error': str(error), 'changes': {}, 'unchanged_fields': [],
                             'counts_as_editorial_reread': False, 'automatic_approval': False}
            ref = refs.get(sid)
            if ref and (ref['body_sha256'] != row['body_sha256'] or ref['classification_sha256'] != row['classification_sha256']):
                raise ValueError('reference fingerprint mismatch')
            journal.append({'sample_id': sid, 'record_id_hash': row['record_id_hash'],
                            'body_sha256': row['body_sha256'], 'classification_sha256': row['classification_sha256'],
                            'original_status': value['status'], **recovered,
                            'reference_status': ref['status'] if ref else None,
                            'reference_changes': ref['suggested'] if ref else None,
                            'priority': 'independent_disagreement' if ref and value['status'] == 'ok' and ref['status'] != 'ok' else 'ordinary'})
    if seen != {r['sample_id'] for r in source['records']}:
        raise ValueError('incomplete coverage')
    return {'schema_version': 1, 'method': 'offline_saved_response_diff_v1',
            'input_sha256': source['input_sha256'], 'criteria_sha256': fingerprint(source['criteria']),
            'reference_sha256': hashlib.sha256((directory / 'reference-20.json').read_bytes()).hexdigest(),
            'source_batches': proofs, 'unique_records': len(journal), 'additional_model_calls': 0,
            'additional_local_model_tokens': 0, 'codex_conversation_tokens': 'not_measured',
            'automatic_editorial_credit': 0, 'canonical_changes': 0, 'production_rollout_allowed': False,
            'routes': dict(Counter(r['route'] for r in journal)),
            'mixed_proposals_recovered': sum(bool(r['changes']) and bool(r['unchanged_fields']) for r in journal),
            'priority_records': sum(r['priority'] == 'independent_disagreement' for r in journal),
            'journal': sorted(journal, key=lambda r: r['sample_id'])}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    result = build(args.directory)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['routes', 'mixed_proposals_recovered', 'priority_records', 'additional_model_calls']}, ensure_ascii=False))
