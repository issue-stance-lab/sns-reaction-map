#!/usr/bin/env python3
"""保存済み独立判断20件を編集候補へ整理。本文/分類/基準が変われば停止する。"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import yaml
try:
    from scripts.run_body_review_pilot import FIELDS, fingerprint, validate
except ModuleNotFoundError:
    from run_body_review_pilot import FIELDS, fingerprint, validate


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_record(saved, current):
    fields = {f: (current.get('classification') or {}).get(f, current.get(f)) for f in FIELDS}
    if str(current['tweet_id']) != saved['tweet_id'] or hashlib.sha256(current['text'].encode()).hexdigest() != saved['body_sha256']:
        raise ValueError('canonical identity/body changed')
    if fingerprint(fields) != saved['classification_sha256']:
        raise ValueError('canonical classification changed')
    return fields


def build(root, directory):
    root, directory = Path(root), Path(directory)
    source = json.loads((directory / 'pilot-input.json').read_text())
    reference = json.loads((directory / 'reference-20.json').read_text())
    if fingerprint(source['records']) != source['input_sha256']:
        raise ValueError('pilot input changed')
    saved = {r['sample_id']: r for r in source['records']}
    refs = reference['reviews']
    if len(refs) != 20 or len({r['sample_id'] for r in refs}) != 20:
        raise ValueError('twenty unique reviews required')
    metadata = yaml.safe_load((root / 'THEMES.yaml').read_text())['themes']
    canon, versions, journal, private = {}, {}, [], []
    for ref in refs:
        row = saved[ref['sample_id']]; topic = row['topic']; criteria = source['criteria'][topic]
        if sha(root / criteria['source']) != criteria['source_sha256']:
            raise ValueError('classification criteria changed')
        if topic not in canon:
            path = root / metadata[topic]['sample_file']
            data = json.loads(path.read_text()); canon[topic] = {str(r['tweet_id']): r for r in data}
            if len(canon[topic]) != len(data):
                raise ValueError('duplicate canonical ID')
            versions[topic] = {'canonical_sha256': sha(path), 'criteria_sha256': criteria['source_sha256']}
        current = check_record(row, canon[topic][row['tweet_id']])
        if ref['body_sha256'] != row['body_sha256'] or ref['classification_sha256'] != row['classification_sha256']:
            raise ValueError('reference version mismatch')
        validate([{'id': 0, **{k: ref[k] for k in ['status', 'fields', 'suggested', 'reason']}}], [row], criteria)
        proposed = {**current, **ref['suggested']}
        result = {'sample_id': row['sample_id'], 'topic': topic, 'record_id_hash': row['record_id_hash'],
                  'body_sha256': row['body_sha256'], 'classification_sha256': row['classification_sha256'],
                  'route': {'ok': 'retain_candidate', 'candidate': 'change_candidate', 'uncertain': 'hold'}[ref['status']],
                  'current': current, 'suggested_changes': ref['suggested'], 'proposed': proposed,
                  'reason_sha256': hashlib.sha256(ref['reason'].encode()).hexdigest(),
                  'disposition': 'pending_editorial_decision', 'counts_as_editorial_reread': False}
        journal.append(result)
        private.append({**result, 'text': row['text'], 'tweet_id': row['tweet_id'], 'reason': ref['reason'],
                        'criteria': criteria['text']})
    packet = {'schema_version': 1, 'method': 'reuse_independent_twenty_v1',
              'source_sha256': {name: sha(directory / name) for name in ['pilot-input.json', 'reference-20.json']},
              'versions': versions, 'reviewer': reference['reviewer'], 'unique_records': 20,
              'routes': dict(Counter(r['route'] for r in journal)), 'additional_local_model_calls': 0,
              'codex_conversation_tokens': 'not_measured', 'canonical_changes': 0, 'automatic_editorial_credit': 0,
              'approval': 'not_approved', 'journal': sorted(journal, key=lambda r: r['sample_id'])}
    return packet, private


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True); p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--private-out', type=Path, required=True); p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    if a.private_out.resolve().is_relative_to(a.root.resolve()) or a.private_out.resolve().is_relative_to(Path(__file__).resolve().parents[1]):
        raise ValueError('private packet must be outside repository')
    if a.private_out.exists():
        raise ValueError('do not overwrite private evidence')
    public, private = build(a.root, a.directory)
    a.private_out.parent.mkdir(parents=True, exist_ok=True)
    a.private_out.write_text(json.dumps({'packet': public, 'reviews': private}, ensure_ascii=False, indent=2) + '\n')
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(public, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(public['routes'], ensure_ascii=False))
