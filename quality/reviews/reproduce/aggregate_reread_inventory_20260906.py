#!/usr/bin/env python3
"""Reconcile ten inventories against current canonical IDs; emit public counts.

Never read source text into the report. Private per-ID work queues stay outside
the repository. This inventories recorded work, not actual comprehension.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--private', type=Path, required=True)
    ap.add_argument('--public-out', type=Path, required=True)
    args = ap.parse_args()
    root, private = args.root.resolve(), args.private.resolve()
    assert root not in private.parents
    sys.path.insert(0, str(root / 'scripts'))
    from public_registry_common import is_opinion_record
    metadata = yaml.safe_load((root / 'THEMES.yaml').read_text())['themes']
    catalog = json.loads((root / 'data/public/catalog.json').read_text())
    topics = sorted(json.loads(p.read_text())['theme_id']
                    for p in (root / 'data/public/themes').glob('*.json'))
    assert len(topics) == 10 and 'takaichi' not in topics
    public = {'scope': 'Ten publicly listed themes; units are (theme, post ID), opinion records only',
              'baseline_commit': '565e76bb2590bdcab29c79098780b9e8fd4233b7',
              'meaning': 'Recorded additional reading after initial AI classification, not proof of comprehension or source truth',
              'themes': {}, 'totals': {}}
    queues = {}
    numeric = ['opinions', 'editorial_main', 'editorial_all', 'editorial_branch_only',
               'connected_main_qualified', 'connected_any_qualified',
               'editorial_not_connected_any', 'editorial_not_connected_main',
               'focused_or_classification_only', 'confirmed_body_review',
               'body_review_record_unconfirmed', 'connected_claim_without_editorial_evidence']
    for topic in topics:
        p = private / (topic + '.json')
        data = json.loads(p.read_text())
        canonical = root / metadata[topic]['sample_file']
        assert digest(canonical) == data['baseline_sha256'], topic
        rows = json.loads(canonical.read_text())
        ids = {str(r['tweet_id']) for r in rows if is_opinion_record(r)}
        document = json.loads((root / 'data/public/themes' / (topic + '.json')).read_text())
        assert len(ids) == document['opinion_count']
        sets = {}
        for key in ['opinion_ids', 'editorial_main_ids', 'editorial_all_ids',
                    'planet_connected_main_ids', 'planet_connected_any_ids',
                    'focused_body_review_ids', 'classification_review_ids', 'claim_mapping_ids']:
            value = list(map(str, data.get(key, [])))
            assert len(value) == len(set(value)), (topic, key, 'duplicates')
            sets[key] = set(value)
            assert sets[key] <= ids, (topic, key, 'outside opinion population')
        assert sets['opinion_ids'] == ids, topic
        main, editorial = sets['editorial_main_ids'], sets['editorial_all_ids']
        assert main <= editorial
        focused = sets['focused_body_review_ids'] | sets['classification_review_ids']
        confirmed = editorial | focused
        conn_main = sets['planet_connected_main_ids'] & editorial
        conn_any = sets['planet_connected_any_ids'] & editorial
        assert conn_main <= conn_any
        partitions = [editorial, focused-editorial, ids-confirmed]
        assert set.union(*partitions) == ids
        assert sum(map(len, partitions)) == len(ids)
        expected = data.get('confirmed_body_review_ids')
        if expected is not None:
            assert set(expected) == confirmed, topic
        stats = dict(zip(numeric, map(len, [
            ids, main, editorial, editorial-main, conn_main, conn_any,
            editorial-conn_any, editorial-conn_main, focused-editorial,
            confirmed, ids-confirmed, sets['planet_connected_any_ids']-editorial])))
        stats['collected'] = len(rows)
        stats['title'] = document['title']
        stats['canonical_sha256'] = digest(canonical)
        stats['inventory_sha256'] = digest(p)
        stats['body_review_record_percent'] = round(100*len(confirmed)/len(ids), 2)
        stats['sources'] = [{k: v for k, v in source.items()
                             if k in ['path', 'git_ref', 'sha256', 'kind', 'reader', 'method', 'notes']}
                            for source in data['sources']]
        stats['caveats'] = data['caveats']
        # Generate issue-level queues from the canonical population, not file totals.
        issue_groups = {}
        for row in rows:
            key = str(row['tweet_id'])
            if key not in ids:
                continue
            issue = row['classification']['main_issue']
            issue_groups.setdefault(issue, set()).add(key)
        stats['issues'] = {issue: {'opinions': len(group), 'editorial': len(group & editorial),
                                  'focused_only': len((group & focused)-editorial),
                                  'body_review_record_unconfirmed': len(group-confirmed)}
                           for issue, group in issue_groups.items()}
        assert sum(v['opinions'] for v in stats['issues'].values()) == len(ids)
        public['themes'][topic] = stats
        queues[topic] = {
            'canonical_sha256': digest(canonical),
            'merge_existing_editorial_ids': sorted(editorial-main),
            'connect_existing_editorial_ids': sorted(editorial-conn_any),
            'unconfirmed_body_review_ids': sorted(ids-confirmed),
            'focused_review_only_ids': sorted(focused-editorial),
            'new_page_editorial_record_missing_ids': sorted(ids-editorial),
            'connected_without_editorial_evidence_ids': sorted(sets['planet_connected_any_ids']-editorial),
        }
    for key in numeric + ['collected']:
        public['totals'][key] = sum(t[key] for t in public['themes'].values())
    assert public['totals']['opinions'] == 12495
    assert public['totals']['collected'] == 15779
    public['historical_rough_estimate'] = {'old_nine_theme_half_sum': 5659,
        'current_nine_theme_half_sum': sum((t['opinions']+1)//2 for k,t in public['themes'].items() if k != 'bukatsu-chiiki'),
        'is_remaining_reading_count': False,
        'reason': 'Half of all opinions is not a selected issue population and did not subtract or validate prior evidence.'}
    public['caveats'] = [
        'Initial automated classification is excluded; absence of reread evidence is not proof nobody has read a post.',
        'Focused claim/classification checks are not issue-level editorial decomposition or a complete fact check.',
        'Branch connection means a prototype/configuration link, not merged/publicly deployed new-page content.',
        'Some old evidence lacks per-post read-time body hashes; evidence strength differs by source.',
        'Current strict input hashes must be rechecked before merging, connecting, or rereading queued IDs.',
        'No new reading, production data changes, threshold changes, or public page changes performed.']
    write(private / 'work-queues.json', queues)
    write(args.public_out, public)
    print(json.dumps(public['totals'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
