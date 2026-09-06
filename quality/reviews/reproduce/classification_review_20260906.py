#!/usr/bin/env python3
"""Rebuild reviewed candidates from immutable private sources and per-ID decisions.
No collection, classification API, canonical writes, or publication.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def index(rows):
    result = {r['tweet_id']: r for r in rows}
    assert len(result) == len(rows), 'duplicate IDs'
    return result


def run(bundle, output):
    output.mkdir(parents=True, exist_ok=False)
    decisions = read(bundle / 'review-decisions.json')
    result = {}
    for topic, cfg in decisions['topics'].items():
        base = bundle / 'sources' / cfg['source_folder']
        manifest = read(base / 'manifest.json')
        files = manifest.get('files', manifest)
        for name, item in files.items():
            expected = item['sha256'] if isinstance(item, dict) else item
            assert digest(base / name) == expected, (topic, name)
        canon = read(base / cfg['canon'])
        wave = read(base / cfg['wave'])
        proposal = read(base / cfg['proposal'])
        old, historic, previous = index(canon), index(wave), index(proposal)
        rows = list(canon)
        applied = []
        held = []
        review = {r['tweet_id']: r for r in cfg['reviews']}
        assert len(review) == cfg['review_count']
        for post in proposal:
            tid = post['tweet_id']
            if tid in old:
                assert post == old[tid], (topic, tid, 'prior candidate changed existing row')
                continue
            assert tid in historic
            assert {k:v for k,v in post.items() if k != 'classification'} == {k:v for k,v in historic[tid].items() if k != 'classification'}
            decision = review.get(tid)
            if decision:
                assert hashlib.sha256(post['text'].encode()).hexdigest() == decision['text_sha256']
                if decision['disposition'] == 'hold':
                    held.append(tid)
                    continue
                row = dict(post)
                row['classification'] = dict(decision['recommended_classification'])
                applied.append(tid)
            else:
                assert topic == 'school-nickname-ban', 'unread addition'
                row = post
            rows.append(row)
        actual = index(rows)
        assert all(actual[k] == v for k,v in old.items()), 'existing fields changed'
        assert set(actual) - set(old) == set(historic) - set(old) - set(held)
        for tid in set(actual) - set(old):
            assert {k:v for k,v in actual[tid].items() if k != 'classification'} == {k:v for k,v in historic[tid].items() if k != 'classification'}
            c = actual[tid]['classification']
            assert type(c['is_relevant']) is bool and type(c['is_opinion']) is bool
            assert c['main_issue'] in cfg['allowed_issues'] and c['stance'] in cfg['allowed_stances']
            assert c['risk'] in ['low','medium','high']
            if not c['is_relevant'] or c['main_issue'] == 'その他':
                assert not c['is_opinion'] and not c['article_usable']
        target = output / (topic + '-candidate.json')
        write(target, rows)
        opinions = [r for r in rows if r['classification']['is_relevant'] and r['classification']['is_opinion']]
        changed = {tid: {k: {'before': previous[tid]['classification'].get(k), 'after': v} for k,v in actual[tid]['classification'].items() if v != previous[tid]['classification'].get(k)} for tid in applied}
        changed = {k:v for k,v in changed.items() if v}
        result[topic] = dict(total=len(rows), relevant=sum(r['classification']['is_relevant'] for r in rows), opinions=len(opinions), additional=len(rows)-len(canon), held=held, reviewed=len(review), existing_unchanged=len(canon), issue_counts=dict(collections.Counter(r['classification']['main_issue'] for r in opinions)), stance_counts=dict(collections.Counter(r['classification']['stance'] for r in opinions)), changes_from_prior=changed, sha256=digest(target))
        assert (len(rows),len(opinions)) == tuple(cfg['expected_total_opinions'])
    write(output / 'validation.json', result)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True,help='new output directory; existing path rejected')
    a=p.parse_args()
    run(a.bundle,a.output)
