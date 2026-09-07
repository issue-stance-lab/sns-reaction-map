"""Summarize a frozen 20-record model trial without changing adoption."""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from scripts.summarize_editorial_batch import verified_reviews
from scripts.verify_editorial_hundred import read, sha, dump


def summary(root, run):
    root, run = Path(root), Path(run)
    plan = read(run / 'plan.json')
    packet = read(run / 'packet.private.json')
    if sha(run / 'packet.private.json') != plan['packet_sha256']:
        raise ValueError('comparison packet changed')
    if sha(root / 'data/verification/editorial-adoption.json') != plan['ledger_sha256']:
        raise ValueError('adoption changed during comparison')
    if sha(run / 'historical-reference.private.json') != plan['historical_reference_sha256']:
        raise ValueError('historical reference changed')
    if len(packet['records']) != 20 or len({r['record_id_hash'] for r in packet['records']}) != 20:
        raise ValueError('20 unique records required')
    parent = read(run / 'parent-before-results.private.json')
    parent_rows = verified_reviews(packet, parent, list(range(20)))
    historical = {r['index']: r for r in read(run / 'historical-reference.private.json')['records']}
    output = {}; results = {}; fingerprints = {}
    for name in ['sol', 'terra']:
        path = run / f'{name}.private.json'; result = read(path)
        if result['packet_sha256'] != plan['packet_sha256']:
            raise ValueError('model input hash mismatch')
        reviews = result['reviews']
        if len(reviews) != 20 or any(type(r.get('index')) is not int for r in reviews) or sorted(r['index'] for r in reviews) != list(range(20)):
            raise ValueError('unusable model coverage')
        rows = {}; errors = []
        for review in reviews:
            i = review['index']
            try:
                verified = verified_reviews(packet, {'reviews': [review]}, [i])[i]
                if type(verified.get('evidence_sufficient')) is not bool:
                    raise ValueError('missing evidence assessment')
                rows[i] = verified
            except (ValueError, KeyError, TypeError) as error:
                errors.append({'index': i, 'error': str(error)})
        times = [result['started_epoch'], result['finished_epoch']]
        if any(type(t) not in (int, float) or not math.isfinite(t) for t in times) or times[1] < times[0]:
            raise ValueError('invalid model timing')
        output[name] = {
            'requested_model': 'gpt-5.6-' + name, 'reasoning_effort': plan['reasoning_effort'],
            'format_valid': len(rows), 'validation_errors': errors, 'routes': dict(Counter(r['route'] for r in rows.values())),
            'recorded_elapsed_seconds': round(times[1] - times[0], 2), 'tokens': None,
            'four_values_match_parent': sum(r['classification'] == parent_rows[i]['classification'] for i, r in rows.items()),
            'uncertainty_match_parent': sum(r['uncertain'] == parent_rows[i]['uncertain'] for i, r in rows.items()),
            'previously_accepted_same_values_and_not_uncertain': sum(
                historical[i]['adoption_status'] == 'accepted' and not r['uncertain'] and
                r['classification'] == historical[i]['proposed'] for i, r in rows.items()),
            'previously_unresolved_not_uncertain': sum(historical[i]['adoption_status'] != 'accepted' and not r['uncertain'] for i, r in rows.items()),
        }
        results[name] = rows; fingerprints[path.name] = sha(path)
    pair = [{'index': i, 'topic': packet['records'][i]['topic'],
             'record_id_hash': packet['records'][i]['record_id_hash'],
             'same_four_values': (results['sol'][i]['classification'] == results['terra'][i]['classification']) if i in results['sol'] and i in results['terra'] else None,
             'same_uncertainty': (results['sol'][i]['uncertain'] == results['terra'][i]['uncertain']) if i in results['sol'] and i in results['terra'] else None,
             'models': {n: {k: rs[i][k] for k in ['classification', 'uncertain', 'evidence_sufficient', 'route']}
                        for n, rs in results.items() if i in rs}}
            for i in range(20)]
    measurements = read(run / 'measurement-notes.json')
    for name in output:
        output[name]['timing_scope'] = measurements[name]['scope']
        output[name]['timing_comparable'] = False
    fingerprints['measurement-notes.json'] = sha(run / 'measurement-notes.json')
    fingerprints.update({name: sha(run / name) for name in ['plan.json', 'packet.private.json',
                        'parent-before-results.private.json', 'historical-reference.private.json']})
    mapping = read(run / 'blind-map.private.json')
    if set(mapping) != {'A', 'B'} or set(mapping.values()) != {'sol', 'terra'}:
        raise ValueError('invalid blind assignment')
    audit_input = read(run / 'audit-four.private.json')
    audit = read(run / 'audit-four-result.private.json')
    if sorted(r['index'] for r in audit['reviews']) != [5, 11, 17, 19]:
        raise ValueError('four-case audit coverage')
    for r in audit_input['records']:
        i = r['input']['index']
        if r['input'] != packet['records'][i]:
            raise ValueError('audit input differs')
        for label, name in mapping.items():
            if r['answers'][label] != {k: results[name][i][k] for k in ['classification', 'uncertain', 'reason', 'evidence_sufficient']}:
                raise ValueError('audit answer differs')
    audit_public = []
    for r in audit['reviews']:
        for label in mapping:
            if r['assessment_' + label] not in {'supported', 'needs_review', 'undetermined'}:
                raise ValueError('invalid audit assessment')
        audit_public.append({'index': r['index'], 'assessment': {name: r['assessment_' + label] for label, name in mapping.items()},
                             'common_criteria_issue': r['common_criteria_issue']})
    for name in ['blind-map.private.json', 'audit-four.private.json', 'audit-four-result.private.json', 'audit-clarification.json', 'parent-blinded-assessment.private.json']:
        fingerprints[name] = sha(run / name)
    return {'schema_version': 1, 'sampling': plan['selection'], 'records': 20,
            'models': output, 'valid_pairs': sum(r['same_four_values'] is not None for r in pair),
            'pair_four_values_match': sum(r['same_four_values'] is True for r in pair),
            'pair_uncertainty_match': sum(r['same_uncertainty'] is True for r in pair),
            'records_compared': pair, 'proofs': fingerprints,
            'measurement_notes': measurements, 'independent_audit': audit_public,
            'audit_clarification': read(run / 'audit-clarification.json'),
            'interpretation': 'Agreement is not accuracy. Historical and parent judgments are fallible. Timings include agent work and tool overhead; token usage not measured.',
            'canonical_changes': 0, 'adoption_changes': 0, 'new_review_credit': 0}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['root', 'run', 'report']:
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); result = summary(a.root, a.run); dump(a.report, result)
    print(json.dumps({'models': result['models'], 'pair_four_values_match': result['pair_four_values_match'],
                      'pair_uncertainty_match': result['pair_uncertainty_match']}, ensure_ascii=False))
