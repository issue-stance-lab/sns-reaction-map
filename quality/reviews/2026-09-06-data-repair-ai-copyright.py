#!/usr/bin/env python3
"""Build private task 63-M1 candidates; never change a source or publish data."""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil

FIELDS = ('fetched_at', 'query', 'source')
CANONICAL = 'social-samples/ai-copyright_hermes_classified.json'
CORROBORATION = 'social-samples/ai-copyright_classified.json'
RAW = 'social-samples/ai-copyright_samples.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(text):
    # Only the known Yahoo highlight delimiters and whitespace are normalized.
    return ' '.join(text.replace('\tSTART\t', ' ').replace('\tEND\t', ' ').split())


def match(left, right):
    if left == right:
        return 'exact'
    if normalize(left) == normalize(right):
        return 'highlight_whitespace_only'
    if re.sub(r'\s+', '', normalize(left)) == re.sub(r'\s+', '', normalize(right)):
        return 'highlight_spacing_only_reviewed'
    return 'different'


def walk(value, pointer=''):
    if isinstance(value, list):
        for i, item in enumerate(value):
            yield from walk(item, f'{pointer}/{i}')
    elif isinstance(value, dict):
        if value.get('tweet_id'):
            yield pointer, value
        for key, item in value.items():
            if isinstance(item, (list, dict)):
                yield from walk(item, f'{pointer}/{key}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = root / CANONICAL
    rows = json.loads(source.read_text())
    by_id = {str(r['tweet_id']): r for r in rows}
    assert len(by_id) == len(rows), 'duplicate canonical IDs'
    target = {key: r for key, r in by_id.items() if any(not r.get(f) for f in FIELDS)}
    evidence = collections.defaultdict(list)
    manifest, scanned, unreadable = {}, 0, []
    for path in sorted((root / 'social-samples').rglob('*.json')):
        scanned += 1
        try:
            value = json.loads(path.read_text())
        except (ValueError, UnicodeError) as error:
            unreadable.append({'path': str(path.relative_to(root)), 'error_type': type(error).__name__})
            continue
        matches = [(ptr, r) for ptr, r in walk(value)
                   if str(r.get('tweet_id')) in target and any(r.get(f) for f in FIELDS)]
        if not matches:
            continue
        rel = str(path.relative_to(root))
        digest = sha(path)
        dest = out / 'sources' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        assert sha(dest) == digest
        manifest[rel] = {'sha256': digest, 'records': len(value) if isinstance(value, list) else None,
                         'target_observations': len(matches)}
        for pointer, observed in matches:
            canonical = target[str(observed['tweet_id'])]
            evidence[str(observed['tweet_id'])].append({
                'path': rel, 'sha256': digest, 'pointer': pointer,
                'values': {f: observed.get(f) for f in FIELDS},
                'text_match': match(canonical['text'], observed.get('text', '')),
                'canonical_text_sha256': hashlib.sha256(canonical['text'].encode()).hexdigest(),
                'observed_text_sha256': hashlib.sha256(observed.get('text', '').encode()).hexdigest(),
                'url_equal': canonical.get('url') == observed.get('url'),
                'synthetic_flagged': any(observed.get(k) for k in ('synthetic', 'is_synthetic')),
            })
    candidate = copy.deepcopy(rows)
    candidate_by_id = {str(r['tweet_id']): r for r in candidate}
    dispositions = []
    for key, row in target.items():
        obs = evidence[key]
        trusted = []
        for item in obs:
            if item['path'] != CORROBORATION or item['text_match'] != 'exact' or not item['url_equal'] or item['synthetic_flagged']:
                continue
            if not all(item['values'][f] for f in FIELDS):
                continue
            raw_matches = [o for o in obs if o['path'] == RAW and o['url_equal']
                           and o['text_match'] in ('exact', 'highlight_whitespace_only')
                           and o['values'] == item['values'] and not o['synthetic_flagged']]
            if raw_matches:
                trusted.append(item)
        unique = {json.dumps(o['values'], sort_keys=True) for o in trusted}
        selected = trusted[0] if len(unique) == 1 else None
        repaired = {}
        if selected:
            for field in FIELDS:
                if not row.get(field):
                    candidate_by_id[key][field] = selected['values'][field]
                    repaired[field] = selected['values'][field]
        dispositions.append({
            'tweet_id': key, 'missing_before': [f for f in FIELDS if not row.get(f)],
            'status': 'evidence_backed_candidate' if selected else 'held_text_difference',
            'adopted_values': repaired, 'selected_evidence': selected,
            'reason': ('Old classified text matches exactly; its observation tuple is corroborated by raw text after Yahoo highlight/whitespace normalization. This is a documented observation, not a proven first fetch or canonical adoption date.'
                       if selected else 'Canonical text is shorter by seven characters within the final URL. Raw and old classified texts agree, but canonical provenance of truncation is not proven. Keep all three missing fields and the existing text unchanged.'),
            'observations': obs,
            'distinct_observation_dates': sorted({o['values']['fetched_at'] for o in obs if o['values']['fetched_at']}),
        })
    assert len(dispositions) == len(target)
    assert [r['tweet_id'] for r in candidate] == [r['tweet_id'] for r in rows]
    for before, after in zip(rows, candidate):
        assert {k: v for k, v in before.items() if k not in FIELDS} == {k: v for k, v in after.items() if k not in FIELDS}
        for field in FIELDS:
            if before.get(field):
                assert before[field] == after[field]
    statuses = collections.Counter(d['status'] for d in dispositions)
    summary = {
        'canonical_path': CANONICAL, 'canonical_sha256': sha(source), 'records': len(rows),
        'missing_before': {f: sum(not r.get(f) for r in rows) for f in FIELDS},
        'missing_after': {f: sum(not r.get(f) for r in candidate) for f in FIELDS},
        'target_posts': len(target), 'statuses': dict(statuses), 'unprocessed': 0,
        'multiple_observation_dates': sum(len(d['distinct_observation_dates']) > 1 for d in dispositions),
        'scan_json_files': scanned, 'unreadable_files': unreadable,
        'observations': sum(len(d['observations']) for d in dispositions),
        'candidate_observed_date_min': min(r['fetched_at'][:10] for r in candidate if r.get('fetched_at')),
        'candidate_observed_date_max': max(r['fetched_at'][:10] for r in candidate if r.get('fetched_at')),
        'integrity_checks': {'unique_ids': True, 'same_id_order': True, 'all_non_fetch_fields_unchanged': True,
                             'existing_fetch_values_unchanged': True},
        'period_policy': 'Do not change sample_period or owner_confirmed. Observations do not prove original canonical adoption or true first collection.',
        'source_files': manifest,
    }
    shutil.copy2(source, out / 'original.json')
    for filename, data in [('candidate.json', candidate), ('dispositions.json', dispositions),
                           ('held.json', [d for d in dispositions if not d['adopted_values']]),
                           ('summary.json', summary)]:
        (out / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    assert sha(source) == sha(out / 'original.json')
    print(json.dumps({k:v for k,v in summary.items() if k != 'source_files'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
