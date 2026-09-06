#!/usr/bin/env python3
"""Reproduce private 63-M3 candidate from frozen raw evidence; no source writes or AI calls."""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import shutil
import contextlib
import io
import subprocess
import sys

FIELDS = ('fetched_at', 'query', 'source')
CANONICAL = 'social-samples/takaichi_hermes_arena_classified.json'
RAW = 'social-samples/takaichi_realtime_samples.json'
OLD = 'social-samples/takaichi_realtime_ollama_batch_classified.json'
WAVE = 'social-samples/updates/takaichi/2026-08-29'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def walk(value, pointer=''):
    if isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, f'{pointer}/{i}')
    elif isinstance(value, dict):
        if value.get('tweet_id'):
            yield pointer, value
        for k, v in value.items():
            if isinstance(v, (list, dict)):
                yield from walk(v, f'{pointer}/{k}')


def clean(text):
    # Only Yahoo's literal highlight delimiters; no prose or whitespace rewriting.
    return text.replace('\tSTART\t', '').replace('\tEND\t', '')


def stats(rows):
    opinion = [r for r in rows if r.get('classification', {}).get('is_relevant')
               and r.get('classification', {}).get('is_opinion')]
    return {'records': len(rows),
            'relevant': sum(bool(r.get('classification', {}).get('is_relevant')) for r in rows),
            'opinions': len(opinion),
            'issues': dict(collections.Counter(r['classification'].get('main_issue') for r in opinion)),
            'stances': dict(collections.Counter(r['classification'].get('stance') for r in opinion))}


def verify(root, out):
    """Run local, theme-only checks against the candidate; restore original bytes even on failure."""
    sys.path.insert(0, str(root / 'scripts'))
    import verify_sample_periods as periods
    import refresh_topic
    candidate = json.loads((out / 'candidate.json').read_text())
    wave = json.loads((out / 'sources' / WAVE / 'classified.json').read_text())
    raw = json.loads((out / 'sources' / WAVE / 'raw.json').read_text())
    classifier = root / 'scripts/classify_takaichi_arena_hermes.py'
    results = {'candidate_labels': refresh_topic.validate_classified(candidate, classifier),
               'wave_labels': refresh_topic.validate_classified(wave, classifier),
               'wave_sets': refresh_topic.validate_sets(candidate, raw, wave, wave)}
    theme = periods.parse_themes_yaml()['takaichi']
    periods.parse_themes_yaml = lambda: {'takaichi': theme}
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        code = periods.verify({'takaichi': periods.summarize(candidate)})
    results['sample_periods_theme_only'] = {'exit_code': code, 'output': log.getvalue(),
        'reason': 'Expected mismatch: all dates restored but registry unknown intentionally retained pending period review; verifier not weakened.'}
    path = root / CANONICAL
    original = path.read_bytes()
    try:
        path.write_bytes((out / 'candidate.json').read_bytes())
        for script in ('verify_theme_page.py', 'verify_number_provenance.py'):
            completed = subprocess.run([sys.executable, str(root / 'scripts' / script), 'takaichi'], cwd=root, text=True, capture_output=True)
            results[script] = {'exit_code': completed.returncode, 'output': completed.stdout + completed.stderr}
    finally:
        path.write_bytes(original)
    assert path.read_bytes() == original
    results['canonical_restored'] = True
    results['new_page_reread_check'] = 'Not run: configs/planet/takaichi.yaml absent; no new page or reread changed.'
    write(out / 'verification.json', results)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--session-evidence', type=Path, required=True)
    p.add_argument('--verify', action='store_true', help='Use a dedicated worktree only; temporarily swaps its canonical file and restores it.')
    args = p.parse_args()
    root, out = args.root.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    rows = json.loads((root / CANONICAL).read_text())
    by_id = {str(r['tweet_id']): r for r in rows}
    assert len(rows) == len(by_id)
    targets = {k: r for k, r in by_id.items() if any(not r.get(f) for f in FIELDS)}
    evidence = collections.defaultdict(list)
    manifest = {}

    def preserve(path):
        rel = str(path.relative_to(root))
        dest = out / 'sources' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        assert sha(path) == sha(dest)
        manifest[rel] = {'sha256': sha(path)}
        return rel

    preserve(root / CANONICAL)
    scanned, unreadable = 0, []
    for path in sorted((root / 'social-samples').rglob('*.json')):
        scanned += 1
        try:
            data = json.loads(path.read_text())
        except (ValueError, UnicodeError):
            unreadable.append(str(path.relative_to(root)))
            continue
        matches = [(ptr, r) for ptr, r in walk(data)
                   if str(r.get('tweet_id')) in targets and any(r.get(f) for f in FIELDS)]
        if not matches:
            continue
        rel = preserve(path)
        for pointer, r in matches:
            original = targets[str(r['tweet_id'])]
            evidence[str(r['tweet_id'])].append({
                'path': rel, 'sha256': sha(path), 'pointer': pointer,
                'values': {f: r.get(f) for f in FIELDS},
                'text_match': ('exact' if r.get('text') == original['text'] else
                               'highlight_only' if clean(r.get('text', '')) == original['text'] else 'different'),
                'text_sha256': hashlib.sha256(r.get('text', '').encode()).hexdigest(),
                'url_equal': r.get('url') == original.get('url'),
                'synthetic_flagged': any(r.get(k) for k in ('synthetic', 'is_synthetic')),
            })
    candidate = copy.deepcopy(rows)
    cb = {str(r['tweet_id']): r for r in candidate}
    dispositions = []
    for key, row in targets.items():
        obs = evidence[key]
        trusted = []
        for o in obs:
            if o['path'] != RAW or o['text_match'] not in ('exact', 'highlight_only'):
                continue
            if not o['url_equal'] or o['synthetic_flagged'] or not all(o['values'].values()):
                continue
            corroboration = [v for v in obs if v['path'] == OLD and v['text_match'] == 'exact'
                             and v['url_equal'] and not v['synthetic_flagged'] and v['values'] == o['values']]
            if corroboration:
                trusted.append((o, corroboration))
        unique = {json.dumps(o['values'], sort_keys=True) for o, _ in trusted}
        chosen = trusted[0] if len(unique) == 1 else None
        adopted = {}
        if chosen:
            for field in FIELDS:
                if not row.get(field):
                    cb[key][field] = chosen[0]['values'][field]
                    adopted[field] = cb[key][field]
        dispositions.append({
            'tweet_id': key, 'status': 'evidence_backed_candidate' if chosen else 'held',
            'missing_before': [f for f in FIELDS if not row.get(f)],
            'adopted_values': adopted, 'selected_evidence': chosen,
            'reason': 'Use unique original raw observation tuple corroborated by exact classified text. Later observations remain in evidence; this is not a claim of true first fetch or canonical adoption date.' if chosen else 'No unique corroborated raw tuple.',
            'observations': obs,
            'observation_dates': sorted({o['values']['fetched_at'][:10] for o in obs if o['values']['fetched_at']}),
        })
    session = out / 'session-context.json'
    shutil.copy2(args.session_evidence, session)
    wave_raw_path, wave_class_path, report_path = (root / WAVE / f for f in ('raw.json', 'classified.json', 'report.json'))
    for path in (wave_raw_path, wave_class_path, report_path):
        preserve(path)
    raw = json.loads(wave_raw_path.read_text())
    classified = json.loads(wave_class_path.read_text())
    report = json.loads(report_path.read_text())
    raw_by = {str(r['tweet_id']): r for r in raw}
    wave_by = {str(r['tweet_id']): r for r in classified}
    assert len(raw_by) == len(raw) and len(wave_by) == len(classified)
    assert set(wave_by) == set(raw_by) - set(by_id)
    assert (len(raw), len(raw_by.keys() & by_id.keys()), len(classified)) == (report['raw'], report['duplicates'], report['new'])
    assert report['status'] == 'validated' and all(report['checks'].values())
    assert stats(classified)['opinions'] == report['opinions']
    assert stats(classified)['relevant'] == report['relevant']
    for key, r in wave_by.items():
        assert clean(raw_by[key]['text']) == clean(r['text'])
        assert all(raw_by[key].get(f) == r.get(f) for f in FIELDS)
    adoption = [{
        'tweet_id': key, 'status': 'intentional_hold',
        'reason': 'Original collection instruction explicitly prohibited cumulative-canonical and HTML updates; saved wave validated, adoption was not authorized. No evidence of per-post editorial exclusion.',
        'session_evidence': {'path': session.name, 'sha256': sha(session)},
        'wave_source': {'path': WAVE + '/classified.json', 'sha256': sha(wave_class_path)},
        'already_adopted': key in by_id, 'semantic_reread_performed': False,
        'future_review': 'Before any proposed adoption, review relevance, opinion status, issue/stance fit and downstream editorial evidence.'}
        for key in wave_by]
    assert [r['tweet_id'] for r in rows] == [r['tweet_id'] for r in candidate]
    for before, after in zip(rows, candidate):
        assert {k: v for k, v in before.items() if k not in FIELDS} == {k: v for k, v in after.items() if k not in FIELDS}
        for f in FIELDS:
            if before.get(f):
                assert before[f] == after[f]
    assert stats(rows) == stats(candidate)
    summary = {
        'canonical_path': CANONICAL, 'canonical_sha256': sha(root / CANONICAL),
        'before': stats(rows), 'after': stats(candidate), 'wave': stats(classified),
        'missing_before': {f: sum(not r.get(f) for r in rows) for f in FIELDS},
        'missing_after': {f: sum(not r.get(f) for r in candidate) for f in FIELDS},
        'repair_statuses': dict(collections.Counter(d['status'] for d in dispositions)),
        'multiple_observation_dates': sum(len(d['observation_dates']) > 1 for d in dispositions),
        'unprocessed_repairs': len(targets) - len(dispositions),
        'adoption_statuses': dict(collections.Counter(d['status'] for d in adoption)),
        'unprocessed_wave': len(classified) - len(adoption),
        'added_posts': 0, 'classification_changes': 0, 'text_changes': 0,
        'candidate_date_min': min(r['fetched_at'][:10] for r in candidate if r.get('fetched_at')),
        'candidate_date_max': max(r['fetched_at'][:10] for r in candidate if r.get('fetched_at')),
        'scan_files': scanned, 'unreadable': unreadable, 'sources': manifest,
        'checks': {'unique_ids': True, 'id_order_unchanged': True, 'all_other_fields_unchanged': True,
                   'existing_metadata_unchanged': True, 'wave_equals_raw_minus_canonical': True,
                   'wave_raw_classified_text_and_metadata_match': True},
        'policy': 'Keep sample_period unknown, published unlisted and noindex. No general publication or canonical replacement.',
    }
    shutil.copy2(root / CANONICAL, out / 'original.json')
    for filename, data in [('candidate.json', candidate), ('fetch-dispositions.json', dispositions),
                           ('adoption-dispositions.json', adoption), ('held.json', adoption),
                           ('summary.json', summary)]:
        write(out / filename, data)
    if args.verify:
        verify(root, out)
    print(json.dumps({k: v for k, v in summary.items() if k != 'sources'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
