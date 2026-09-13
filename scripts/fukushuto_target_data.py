"""Aggregate reviewed targets without turning them into a single bill vote.

The result contains counts only. Editorial rereading and publication approval
are deliberately not inferred from classification evidence.
"""
from collections import Counter
from hashlib import sha256

from build_fukushuto_target_review import LABELS, ISSUES, SCOPES


def aggregate_targets(records):
    rows = [r for r in records if r['decision'] == 'include']
    locations = sorted({x['name'] for r in rows for x in r['locations']})
    definitions = [('concept', '構想', 'concept', None)]
    definitions += [('law-' + str(i), s, 'law', s) for i, s in enumerate(SCOPES)]
    definitions += [('location-' + sha256(name.encode()).hexdigest()[:16], name, 'location', name)
                    for name in locations]
    targets = []
    for target_id, label, kind, scope in definitions:
        cross = {issue: Counter() for issue in ISSUES}
        for row in rows:
            stance = '未表明'
            if kind == 'concept':
                stance = row['concept']
            elif kind == 'law' and row['law_scope'] == scope:
                stance = row['law']
            elif kind == 'location':
                stance = next((x['stance'] for x in row['locations']
                               if x['name'] == scope), '未表明')
            cross[row['main_issue']][stance] += 1
        by_issue = [{
            'issue': issue,
            'population': sum(cross[issue].values()),
            'counts': {stance: cross[issue][stance] for stance in LABELS},
        } for issue in ISSUES]
        counts = {s: sum(x['counts'][s] for x in by_issue) for s in LABELS}
        targets.append({'id': target_id, 'label': label, 'kind': kind,
                        'population': len(rows), 'counts': counts,
                        'evaluated_count': len(rows) - counts['未表明'],
                        'issues': by_issue})
    result = {'schema': 'fukushuto-target-counts-v1', 'opinion_count': len(rows),
              'targets': targets}
    validate_targets(result)
    return result


def validate_targets(data):
    """Reject dropped/doubled posts, unknown labels and malformed counts."""
    if data['schema'] != 'fukushuto-target-counts-v1':
        raise ValueError('対象別データの形式が不正')
    n = data['opinion_count']
    if type(n) is not int or n < 0:
        raise ValueError('意見母数が不正')
    ids = set()
    for target in data['targets']:
        if target['id'] in ids:
            raise ValueError('対象IDが重複')
        ids.add(target['id'])
        if target['population'] != n or set(target['counts']) != set(LABELS):
            raise ValueError('対象の母数・評価が不正')
        if [x['issue'] for x in target['issues']] != list(ISSUES):
            raise ValueError('論点が欠落・重複')
        for item in [target, *target['issues']]:
            if set(item['counts']) != set(LABELS) or any(
                    type(v) is not int or v < 0 for v in item['counts'].values()):
                raise ValueError('評価件数が不正')
            if sum(item['counts'].values()) != item['population']:
                raise ValueError('評価件数と母数が不一致')
        if sum(x['population'] for x in target['issues']) != n:
            raise ValueError('論点母数の合計が不一致')
        if any(sum(x['counts'][s] for x in target['issues']) != target['counts'][s]
               for s in LABELS):
            raise ValueError('対象集計と論点別集計が不一致')
        if target['evaluated_count'] != n - target['counts']['未表明']:
            raise ValueError('評価記録件数が不一致')
    if 'concept' not in ids:
        raise ValueError('構想の対象が欠落')
    return data
