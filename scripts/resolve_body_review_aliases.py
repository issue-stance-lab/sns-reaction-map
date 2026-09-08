"""Resolve same-input/different-ID inventory links without granting reading credit.

Metadata/hash inspection only. Every alias remains pending an ID-specific author,
quotation and context check; source decisions must never be copied automatically.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import yaml

from scripts.editorial_work_registry import load_registry, sha, fingerprint
from scripts.prepare_body_review_pilot import FIELDS
from scripts.verification_data import record_id_hash

EXISTING = 'same_input_as_existing_work_different_id'
REMAINING = 'same_input_as_another_unconfirmed_id'
IDENTITY = ('topic', 'record_id_hash', 'body_sha256', 'classification_sha256', 'criteria_sha256')


def read(path):
    return json.loads(path.read_text())


def input_key(row):
    return tuple(row[k] for k in ('topic', 'body_sha256', 'classification_sha256'))


def post_key(row):
    return row['topic'], row['record_id_hash']


def stored_user_comparison(a, b):
    """Compare stored fields only, excluding empty and placeholder metadata."""
    placeholders = {'unknown', 'none', 'null', 'undefined', 'n/a', 'na', '0', '-', '匿名', '不明'}
    if a is None or b is None or not str(a).strip() or not str(b).strip():
        return 'metadata_missing'
    if str(a).strip().casefold() in placeholders or str(b).strip().casefold() in placeholders:
        return 'metadata_placeholder'
    return 'metadata_equal' if str(a) == str(b) else 'metadata_different'


def link_aliases(inventory, work, criteria, decisions):
    """Require a unique exact source and complete decision; never assign credit."""
    prior, remaining = defaultdict(list), defaultdict(list)
    for row in work:
        prior[input_key(row)].append(row)
    for row in inventory['eligible_inventory_only']:
        remaining[input_key(row)].append(row)
    result = []
    for alias in inventory['excluded_unconfirmed']:
        reasons = set(alias['exclusion_reasons'])
        if not reasons & {EXISTING, REMAINING}:
            continue
        if reasons not in ({EXISTING}, {REMAINING}):
            raise ValueError('overlapping alias exclusion reasons require investigation')
        kind = 'existing_work' if EXISTING in reasons else 'remaining_representative'
        sources = (prior if kind == 'existing_work' else remaining)[input_key(alias)]
        if len(sources) != 1:
            raise ValueError('alias must resolve to exactly one source')
        source = sources[0]
        if post_key(source) == post_key(alias):
            raise ValueError('alias source is the same ID')
        criterion = criteria[alias['topic']]
        if source.get('criteria_sha256', criterion) != criterion:
            raise ValueError('source criterion mismatch')
        decision = decisions.get(post_key(source))
        attempted = source.get('state') == 'attempted'
        if kind == 'existing_work' and not attempted:
            if not decision or input_key(decision) != input_key(source):
                raise ValueError('completed source lacks exact decision')
            if decision['adoption_status'] not in {'accepted', 'hold', 'pending_evidence'}:
                raise ValueError('source final status not resolved')
        result.append({
            **{k: alias[k] for k in IDENTITY[:-1]}, 'criteria_sha256': criterion,
            'alias_work_key': fingerprint([alias[k] for k in IDENTITY[:-1]] + [criterion]),
            'input_group_key': fingerprint(list(input_key(alias)) + [criterion]),
            'source_kind': kind,
            'source': {**{k: source[k] for k in IDENTITY[:-1]}, 'criteria_sha256': criterion,
                       'work_key': source.get('work_key'), 'work_state': source.get('state'),
                       'formal_body_review_complete': kind == 'existing_work' and not attempted,
                       'final_status': decision['adoption_status'] if decision else 'unconfirmed',
                       'final_decision_evidence': decision.get('_evidence') if decision else None,
                       'work_evidence': source.get('evidence', []),
                       'legacy_unfinished_dependency': attempted},
            'route': 'alias_identity_attribution_check_pending',
            'attribution_verified': False, 'body_review_complete': False,
            'new_body_review_credit': 0, 'automatic_inherited_credit': 0,
            'depends_on_source_completion': kind == 'remaining_representative' or attempted,
        })
    if len({post_key(r) for r in result}) != len(result):
        raise ValueError('duplicate alias ID')
    return sorted(result, key=post_key)


def inspect(root, canonical_root, private_root, inventory_path):
    inv = read(inventory_path)
    registry_path = root / 'data/verification/editorial-work.json'
    registry = load_registry(registry_path, root, private_root)
    def reference(path, storage, base):
        return {'storage': storage, 'path': str(path.relative_to(base)), 'sha256': sha(path)}
    proofs = [reference(inventory_path, 'private', private_root),
              reference(registry_path, 'repository', root)]
    work_evidence = {s['path']: {k: s[k] for k in ('storage', 'path', 'sha256')}
                     for s in registry['sources']}
    criteria = {}
    for row in registry['records']:
        topic = row['topic']
        if criteria.setdefault(topic, row['criteria_sha256']) != row['criteria_sha256']:
            raise ValueError('multiple current criteria')
    # Old 4,000 final decisions are preserved in the adoption snapshot, while the
    # latest 4,000 are in final wave journals; the work route alone is insufficient.
    decision_paths = [root / 'data/verification/editorial-adoption-current.json']
    decision_paths += [root / f'quality/reviews/2026-09-08-cycle-next4000-final-wave-{n:02}.json' for n in range(1, 5)]
    decisions = {}
    for path in decision_paths:
        data = read(path)
        ref = reference(path, 'repository', root)
        proofs.append(ref)
        for row in data.get('records', data.get('journal', [])):
            if post_key(row) in decisions:
                raise ValueError('duplicate final decision')
            decisions[post_key(row)] = {**row, '_evidence': ref}
    aliases = link_aliases(inv, registry['records'], criteria, decisions)
    meta = yaml.safe_load((root / 'THEMES.yaml').read_text())['themes']
    canonical = {}
    for topic, expected in inv['canonical_sha256'].items():
        path = canonical_root / meta[topic]['sample_file']
        if sha(path) != expected:
            raise ValueError('canonical changed: ' + topic)
        proofs.append(reference(path, 'canonical_repository', canonical_root))
        rows = read(path)
        for raw in rows:
            key = (topic, record_id_hash(raw))
            if key in canonical:
                raise ValueError('duplicate canonical ID')
            canonical[key] = raw
    for alias in aliases:
        alias['source']['work_evidence'] = [work_evidence[p] for p in alias['source']['work_evidence']]
        raw_alias, raw_source = canonical[post_key(alias)], canonical[post_key(alias['source'])]
        for expected, raw in [(alias, raw_alias), (alias['source'], raw_source)]:
            classification = {k: (raw.get('classification') or {}).get(k, raw.get(k)) for k in FIELDS}
            if hashlib.sha256(raw['text'].encode()).hexdigest() != expected['body_sha256'] or fingerprint(classification) != expected['classification_sha256']:
                raise ValueError('canonical identity mismatch')
        alias['tweet_id'] = str(raw_alias['tweet_id'])
        alias['source']['tweet_id'] = str(raw_source['tweet_id'])
        # These values describe stored metadata only, never who voiced an opinion.
        a, b = raw_alias.get('user_id'), raw_source.get('user_id')
        alias['stored_user_id_comparison'] = stored_user_comparison(a, b)
        alias['identity_hash_checks'] = {'topic': True, 'distinct_post_ids': True, 'body': True, 'classification': True, 'criteria': True, 'canonical_version': True}
    summary = {
        'schema_version': 2, 'purpose': 'Resolve duplicate-input dependencies only; not a reservation or reading result.',
        'alias_ids': len(aliases),
        'by_source_kind': dict(Counter(r['source_kind'] for r in aliases)),
        'existing_source_final_status': dict(Counter(r['source']['final_status'] for r in aliases if r['source_kind'] == 'existing_work')),
        'existing_unique_source_ids': len({post_key(r['source']) for r in aliases if r['source_kind'] == 'existing_work'}),
        'remaining_unique_representative_ids': len({post_key(r['source']) for r in aliases if r['source_kind'] == 'remaining_representative'}),
        'legacy_unfinished_dependency_ids': sum(r['source']['legacy_unfinished_dependency'] for r in aliases),
        'alias_input_groups': len({r['input_group_key'] for r in aliases}),
        'by_topic': dict(sorted(Counter(r['topic'] for r in aliases).items())),
        'stored_user_id_comparison': dict(Counter(r['stored_user_id_comparison'] for r in aliases)),
        'complete_hash_identity_links': sum(all(r['identity_hash_checks'].values()) for r in aliases),
        'attribution_verified': 0, 'body_review_completed': 0, 'new_body_reviews': 0,
        'new_reservations': 0, 'registered_work_changes': 0, 'automatic_inherited_credit': 0,
        'remaining_public_opinion_ids': len(inv['raw_remaining']),
        'work_registry_records_verified': len(registry['records']),
        'work_registry_source_files_verified': len(registry['sources']),
        'canonical_changes': 0, 'adoption_changes': 0, 'public_changes': 0,
        'input_evidence': proofs,
    }
    return summary, {'summary': summary, 'aliases': aliases}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'canonical-root', 'private-root', 'inventory', 'summary-out', 'private-out'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    if a.private_out.resolve().is_relative_to(a.root.resolve()):
        raise ValueError('private ID links must stay outside repository')
    if a.summary_out.exists() or a.private_out.exists():
        raise ValueError('never overwrite evidence')
    summary, evidence = inspect(a.root.resolve(), a.canonical_root.resolve(), a.private_root.resolve(), a.inventory.resolve())
    for path, data in [(a.summary_out, summary), (a.private_out, evidence)]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'input_evidence'}, ensure_ascii=False, indent=2))
