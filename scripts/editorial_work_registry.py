#!/usr/bin/env python3
"""Body-free attempted-work ledger; never grants reread credit or applies labels.

Sources are explicit, root-relative, SHA-pinned manifest entries. Verification
rebuilds the ledger from those sources and checks criteria against current code.
Missing evidence or changed criteria stops selection; changed body/labels requeue.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

STATES = {'attempted', 'retain_candidate', 'change_candidate', 'hold'}
IDENTITY = ('topic', 'record_id_hash', 'body_sha256', 'classification_sha256', 'criteria_sha256')


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_source(source, root, private_root):
    if source['storage'] not in {'repository', 'private'}:
        raise ValueError('unknown source storage')
    base = Path(root if source['storage'] == 'repository' else private_root).resolve()
    rel = Path(source['path'])
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('source must be relative')
    path = base / rel
    if not path.resolve().is_relative_to(base):
        raise ValueError('source escapes evidence root')
    if not path.is_file() or sha(path) != source['sha256']:
        raise ValueError('evidence missing or changed: ' + source['path'])
    return path


def checked_packet(packet, root):
    rows = packet['records']
    if 'input_sha256' in packet and fingerprint(rows) != packet['input_sha256']:
        raise ValueError('packet input changed')
    criteria = {}
    for topic, value in packet['criteria'].items():
        path = Path(value['source'])
        if path.is_absolute() or '..' in path.parts or sha(Path(root) / path) != value['source_sha256']:
            raise ValueError('criteria changed')
        criteria[topic] = fingerprint(value)
    result = []
    for row in rows:
        if hashlib.sha256(row['text'].encode()).hexdigest() != row['body_sha256'] or fingerprint(row['classification']) != row['classification_sha256']:
            raise ValueError('packet body or classification changed')
        result.append({**{key: row[key] for key in IDENTITY[:-1]}, 'criteria_sha256': criteria[row['topic']]})
    return result


def build_registry(sources, root, private_root):
    loaded = [(s, json.loads(resolve_source(s, root, private_root).read_text())) for s in sources]
    records = {}; samples = {}; criteria = {}
    for source, data in loaded:
        if source['kind'] != 'packet':
            continue
        for raw, row in zip(data['records'], checked_packet(data, root)):
            key = fingerprint([row[k] for k in IDENTITY])
            topic = row['topic']
            if topic in criteria and criteria[topic] != row['criteria_sha256']:
                raise ValueError('mixed criteria versions require separate migration')
            criteria[topic] = row['criteria_sha256']
            if key not in records:
                records[key] = {**row, 'work_key': key, 'state': 'attempted', 'scope_only_audits': [], 'evidence': [], 'canonical_applied': False, 'counts_as_registered_editorial_reread': False}
            records[key]['evidence'].append(source['path'])
            if 'sample_id' in raw:
                samples[raw['sample_id']] = key
    for source, data in loaded:
        if source['kind'] == 'journal':
            for raw in data['journal']:
                row = {**{k: raw[k] for k in IDENTITY[:-1]}, 'criteria_sha256': criteria[raw['topic']]}
                key = fingerprint([row[k] for k in IDENTITY])
                if key not in records:
                    raise ValueError('decision lacks matching versioned packet')
                if raw['route'] not in STATES - {'attempted'}:
                    raise ValueError('unknown editorial route')
                if records[key]['state'] != 'attempted' and records[key]['state'] != raw['route']:
                    raise ValueError('conflicting decisions')
                if raw.get('canonical_applied') or raw.get('counts_as_registered_editorial_reread') or raw.get('counts_as_editorial_reread'):
                    raise ValueError('candidate ledger cannot import applied or credited records')
                records[key]['state'] = raw['route']
                records[key]['evidence'].append(source['path'])
        elif source['kind'] == 'scope_audit':
            for label in ('consistent', 'needs_review', 'direct_reason_value_conflict'):
                for sample in data.get(label, []):
                    if sample not in samples:
                        raise ValueError('scope audit lacks packet')
                    records[samples[sample]]['scope_only_audits'].append({'evidence': source['path'], 'finding': label})
        elif source['kind'] not in {'packet', 'evidence'}:
            raise ValueError('unknown source kind')
    rows = sorted(records.values(), key=lambda r: r['work_key'])
    return {'schema_version': 1, 'purpose': 'Prevent repeated work; candidate decisions and limited audits are not canonical changes or registered reread credit.', 'sources': sources, 'records': rows, 'counts': dict(sorted(Counter(r['state'] for r in rows).items())), 'automatic_reread_credit': 0, 'canonical_changes': 0}


def load_registry(path, root, private_root):
    value = json.loads(Path(path).read_text())
    if value != build_registry(value['sources'], root, private_root):
        raise ValueError('registry does not match pinned evidence')
    return value


def current_attempts(registry, packet_criteria):
    """Criteria changes stop; exact body/label versions are filtered by selector."""
    current = {topic: fingerprint(value) for topic, value in packet_criteria.items()}
    for row in registry['records']:
        if row['state'] not in STATES or current.get(row['topic']) != row['criteria_sha256']:
            raise ValueError('registry state or criteria changed')
    return registry['records']


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--private-root', type=Path, required=True)
    p.add_argument('--registry', type=Path, required=True)
    p.add_argument('--source-manifest', type=Path, help='Explicit SHA-pinned source list, creates a new ledger')
    args = p.parse_args()
    if args.source_manifest:
        if args.registry.exists():
            raise ValueError('refusing to overwrite ledger; create and review a new version')
        result = build_registry(json.loads(args.source_manifest.read_text()), args.root, args.private_root)
        args.registry.parent.mkdir(parents=True, exist_ok=True)
        args.registry.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    else:
        result = load_registry(args.registry, args.root, args.private_root)
    print(json.dumps({'records': len(result['records']), 'counts': result['counts'], 'automatic_reread_credit': 0}))
