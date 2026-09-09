"""Rebuild unread public opinions from canonical inputs without exposing bodies.

No reservation, judgment, ledger, or source file is written. A saved THEMES hash
can replace git at restore time. All returned paths are archive source entries.
"""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

from scripts.prepare_body_review_pilot import inventory
from scripts.editorial_work_registry import load_registry, resolve_source
from scripts.verify_editorial_hundred import read, sha

BASELINE = 'aaadb234bc473999b603a93d8a104f8f1d70f824'
IDENTITY = ('topic', 'record_id_hash', 'body_sha256', 'classification_sha256')


def identity(row):
    return tuple(row[k] for k in IDENTITY)


def match_completion(report, queues, work):
    """Only exact post/body/label versions with formal decisions are read.

    Holds (including evidence-pending decisions) are formal body readings.
    Attempt-only rows and a different ID with the same body are not readings.
    """
    initial = {}
    for topic, rows in queues.items():
        if not report['topics'][topic]['published']:
            continue
        for raw in rows:
            if not raw['opinion']:
                continue
            row = {**{k: raw[k] for k in IDENTITY[1:]}, 'topic': topic}
            key = identity(row)
            if key in initial:
                raise ValueError('duplicate initial versioned identity')
            initial[key] = row
    if len({k[:2] for k in initial}) != len(initial):
        raise ValueError('multiple current versions for a public post')
    completed = set()
    attempted = set()
    states = Counter()
    for row in work['records']:
        if row['state'] not in {'attempted', 'hold', 'retain_candidate', 'change_candidate'}:
            raise ValueError('unknown work state')
        key = identity(row)
        if row['state'] == 'attempted':
            attempted.add(key)
        else:
            completed.add(key)
            if key in initial:
                states[row['state']] += 1
    remaining = sorted(set(initial) - completed)
    return {
        'initial_unreviewed_public_opinions': len(initial),
        'formally_reviewed_public_opinions': len(set(initial) & completed),
        'unreviewed_public_opinions': len(remaining),
        'unreviewed_by_topic': dict(sorted(Counter(k[0] for k in remaining).items())),
        'matched_formal_states': dict(sorted(states.items())),
        'attempt_only_remaining': len((attempted - completed) & set(remaining)),
        'remaining': [initial[k] for k in remaining],
    }


def recompute(root, private, shared, *, expected_themes_sha256=None,
              expected_initial=10620, expected_public_themes=10,
              expected_canonical_files=11):
    root, private, shared = (Path(p).resolve() for p in (root, private, shared))
    if expected_themes_sha256 is None:
        baseline_bytes = subprocess.check_output(
            ['git', 'show', BASELINE + ':THEMES.yaml'], cwd=root)
        expected_themes_sha256 = hashlib.sha256(baseline_bytes).hexdigest()
    if len(expected_themes_sha256) != 64:
        raise ValueError('expected THEMES hash required')
    sources = {}

    def pin(storage, relative, expected=None):
        base = root if storage == 'repository' else private
        rel = Path(relative)
        if storage not in {'repository', 'private'} or rel.is_absolute() or '..' in rel.parts:
            raise ValueError('invalid source location')
        path = base / rel
        if not path.resolve().is_relative_to(base) or not path.is_file():
            raise ValueError('missing source: ' + str(path))
        value = sha(path)
        if expected is not None and value != expected:
            raise ValueError('source hash mismatch: ' + str(path))
        key = (storage, rel.as_posix())
        if key in sources and sources[key]['sha256'] != value:
            raise ValueError('source changed during recomputation')
        sources[key] = {'storage': storage, 'path': rel.as_posix(), 'sha256': value}
        return path

    themes = pin('repository', 'THEMES.yaml', expected_themes_sha256)
    if not (shared / 'THEMES.yaml').is_file() or sha(shared / 'THEMES.yaml') != sha(themes):
        raise ValueError('shared THEMES missing or different')
    scope_path = pin('repository', 'data/verification/editorial-review-scope.json')
    scope = read(scope_path)
    scope_resolution = pin('private', scope['resolution_path'], scope['resolution_sha256'])
    ledger_path = pin('repository', 'data/verification/editorial-work.json')
    work = load_registry(ledger_path, root, private)
    for source in work['sources']:
        resolve_source(source, root, private)
        pin(source['storage'], source['path'], source['sha256'])
    report, queues = inventory(root, private)
    if len(report['topics']) != expected_canonical_files:
        raise ValueError('canonical topic count changed')
    published = sorted(t for t, m in report['topics'].items() if m['published'])
    if len(published) != expected_public_themes or 'takaichi' in published:
        raise ValueError('public theme set changed')
    for topic, meta in report['topics'].items():
        canonical = pin('repository', meta['canonical_file'], meta['canonical_sha256'])
        if scope['provenance']['canonical_sha256'].get(topic) != sha(canonical):
            raise ValueError('canonical differs from initial scope snapshot')
        peer = shared / meta['canonical_file']
        if not peer.is_file() or sha(peer) != sha(canonical):
            raise ValueError('shared canonical missing or different: ' + topic)
    inventory_sources = []
    for rel, expected in report['source_fingerprints'].items():
        matches = [s for s, base in [('repository', root), ('private', private)]
                   if (base / rel).is_file() and sha(base / rel) == expected]
        if len(matches) != 1:
            raise ValueError('missing or ambiguous inventory source: ' + rel)
        storage = matches[0]
        path = pin(storage, rel, expected)
        inventory_sources.append((storage, rel))
        # inventory validates these via check_sources but does not return their
        # hashes. They must also survive archive extraction.
        if storage == 'repository' and rel.startswith('data/verification/reread/'):
            for dep, value in read(path).get('sources', {}).items():
                pin('repository', dep, value)
                inventory_sources.append(('repository', dep))
    # Pin local Python imports needed by inventory and ledger reconstruction.
    pending = ['recompute_public_unreviewed', 'prepare_body_review_pilot', 'editorial_work_registry', 'verify_editorial_hundred']
    visited = set()
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        file = pin('repository', 'scripts/' + name.replace('.', '/') + '.py')
        for node in ast.walk(ast.parse(file.read_text())):
            imports = ([a.name for a in node.names] if isinstance(node, ast.Import)
                       else [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            for module in imports:
                local = module.removeprefix('scripts.')
                if (root / 'scripts' / (local.replace('.', '/') + '.py')).is_file():
                    pending.append(local)
    result = match_completion(report, queues, work)
    if result['initial_unreviewed_public_opinions'] != expected_initial:
        raise ValueError('initial unread public opinion count changed: ' + str(result['initial_unreviewed_public_opinions']))
    scope_rows = read(scope_resolution)['records']
    scope_keys = {identity(row) for row in scope_rows}
    remaining_keys = {identity(row) for row in result['remaining']}
    if not remaining_keys <= scope_keys:
        raise ValueError('remaining versioned IDs are outside resolved scope')
    royal_keys = {identity(row) for row in scope_rows if row['topic'] == 'koshitsu-tenpakai'}
    result.update({
        'published_topics': published,
        'canonical_file_count': len(report['topics']),
        'initial_excluded_editorial_opinions': report['totals']['published']['opinion_editorial_record'],
        'initial_excluded_limited_opinions': report['totals']['published']['opinion_limited_record'],
        'expected_themes_sha256': expected_themes_sha256,
        'baseline_git_ref': BASELINE,
        'remaining_is_exactly_paused_scope': remaining_keys == royal_keys,
        'paused_scope_records': len(royal_keys),
        'inventory_exclusion_sources': [sources[k] for k in sorted(set(inventory_sources))],
        'source_fingerprints': [sources[k] for k in sorted(sources)],
        'holds_count_as_read': True, 'body_reviews_added': 0,
        'canonical_changes': 0, 'work_ledger_changes': 0,
    })
    # Recheck every captured source, including the ledger and THEMES, to detect
    # registration or input changes during the read-only calculation.
    for source in result['source_fingerprints']:
        resolve_source(source, root, private)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--shared-root', type=Path, required=True)
    parser.add_argument('--expected-themes-sha256')
    args = parser.parse_args()
    print(json.dumps(recompute(args.root, args.private_root, args.shared_root,
                              expected_themes_sha256=args.expected_themes_sha256),
                     ensure_ascii=False, indent=2))
