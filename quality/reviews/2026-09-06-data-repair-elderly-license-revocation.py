#!/usr/bin/env python3
"""Reproduce the private elderly provenance candidate; never edits canonical files."""
import argparse
import collections
import contextlib
import io
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

FIELDS = ('fetched_at', 'query', 'source')
SLUG = 'elderly-license-revocation'
CANON = 'social-samples/elderly-license_2d_classified.json'
REREAD = 'data/elderly-license_issues-reread.json'
CLASSIFIED = 'social-samples/elderly-license-revocation_classified.json'
RAW = 'social-samples/elderly-license-revocation_samples.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def verify_candidate(root, out):
    """Temporarily use the candidate and restore all tracked inputs in finally."""
    sys.path.insert(0, str(root / 'scripts'))
    from scripts import verify_sample_periods as periods
    from public_registry_common import build_theme_json, dumps_theme_json, validate_public_theme, check_theme_invariants
    canon_path = root / CANON
    public_path = root / 'data/public/themes' / (SLUG + '.json')
    original, public_original = canon_path.read_bytes(), public_path.read_bytes()
    results = []
    old_loader = periods.parse_themes_yaml
    try:
        canon_path.write_bytes((out / 'candidate.json').read_bytes())
        theme = old_loader()[SLUG]
        periods.parse_themes_yaml = lambda: {SLUG: theme}
        log = io.StringIO()
        with contextlib.redirect_stdout(log):
            rc = periods.verify({SLUG: periods.summarize(json.loads(canon_path.read_text()))})
        results.append({'check': 'verify_sample_periods.verify target only, fresh candidate summary', 'exit_code': rc, 'log': log.getvalue()})
        generated = build_theme_json(SLUG)
        errors = validate_public_theme(generated) + check_theme_invariants(generated)
        assert not errors, errors
        # Compare regenerated public structure; only provenance may change.
        old_public = json.loads(public_original)
        diffs = []
        def compare(a, b, path=''):
            if isinstance(a, dict) and isinstance(b, dict):
                for key in sorted(a.keys() | b.keys()):
                    compare(a.get(key), b.get(key), path + '/' + key)
            elif a != b:
                diffs.append(path)
        compare(old_public, generated)
        dump(out / 'public-registry-diff-paths.json', diffs)
        public_candidate = dumps_theme_json(generated)
        (out / 'public-theme-candidate.json').write_bytes(public_candidate)
        public_path.write_bytes(public_candidate)
        for script in ('verify_theme_page.py', 'verify_number_provenance.py'):
            proc = subprocess.run([sys.executable, str(root / 'scripts' / script), SLUG], cwd=root, capture_output=True, text=True)
            results.append({'check': script, 'exit_code': proc.returncode, 'log': proc.stdout + proc.stderr})
    finally:
        canon_path.write_bytes(original)
        public_path.write_bytes(public_original)
        periods.parse_themes_yaml = old_loader
    dump(out / 'candidate-checks.json', results)
    assert all(r['exit_code'] == 0 for r in results), 'See private candidate-checks.json'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path.cwd())
    ap.add_argument('--shared', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root, shared, out = args.root.resolve(), args.shared.resolve(), args.out.resolve()
    if out.exists():
        raise SystemExit('Output already exists; choose a new run directory.')
    out.mkdir(parents=True)
    sys.path.insert(0, str(root))
    from scripts.merge_reaction_samples import normalized_text
    from scripts.build_planet_data import split_unread, latest_read_date
    from scripts.verify_sample_periods import summarize
    canonical = json.loads((root / CANON).read_text())
    reread = json.loads((root / REREAD).read_text())
    ids = [str(r['tweet_id']) for r in canonical]
    assert len(ids) == len(set(ids))
    targets = {str(r['tweet_id']): r for r in canonical if any(not r.get(k) for k in FIELDS)}
    classified = {str(r['tweet_id']): r for r in json.loads((root / CLASSIFIED).read_text())}
    raw = {str(r['tweet_id']): r for r in json.loads((root / RAW).read_text())}
    evidence, inventory, parse_errors = collections.defaultdict(list), [], []
    for p in sorted((root / 'social-samples').rglob('*.json')):
        try:
            data = json.loads(p.read_text())
        except (ValueError, UnicodeError):
            parse_errors.append(str(p.relative_to(root)))
            continue
        rows = data if isinstance(data, list) else data.get('samples', data.get('posts', [])) if isinstance(data, dict) else []
        matches = [(i, r) for i, r in enumerate(rows) if isinstance(r, dict) and str(r.get('tweet_id')) in targets and r.get('fetched_at')]
        if not matches:
            continue
        rel = str(p.relative_to(root))
        digest = sha(p)
        shared_path = shared / rel
        assert shared_path.exists() and sha(shared_path) == digest, rel
        item = {'path': rel, 'sha256': digest, 'rows': len(rows), 'shared_sha256': sha(shared_path)}
        inventory.append(item)
        dest = out / 'evidence-files' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        for i, r in matches:
            target = targets[str(r['tweet_id'])]
            evidence[str(r['tweet_id'])].append({
                'file': rel, 'file_sha256': digest, 'row_index': i,
                'values': {k: r.get(k) for k in FIELDS},
                'text_sha256': hashlib.sha256(r.get('text', '').encode()).hexdigest(),
                'text_exact': r.get('text') == target['text'],
                'text_normalized_equal': normalized_text(r.get('text')) == normalized_text(target['text']),
                'normalization': 'scripts/merge_reaction_samples.py:normalized_text',
                'eligible': rel == CLASSIFIED or p.name.startswith('elderly-license-revocation_samples'),
            })
    candidate, decisions = copy.deepcopy(canonical), []
    for r in candidate:
        tid = str(r['tweet_id'])
        if tid not in targets:
            continue
        base, observation = classified.get(tid), raw.get(tid)
        supported = (base is not None and observation is not None
                     and base.get('text') == r['text']
                     and normalized_text(observation.get('text')) == normalized_text(r['text'])
                     and all(base.get(k) and base[k] == observation.get(k) for k in FIELDS))
        adopted = {k: base[k] for k in FIELDS if not r.get(k)} if supported else {}
        r.update(adopted)
        history = evidence[tid]
        decisions.append({'tweet_id': tid, 'missing_fields': [k for k in FIELDS if not targets[tid].get(k)],
            'status': 'repaired' if supported else 'held', 'adopted': adopted,
            'reason': ('Recovered the original 2026-06-28 observation tuple: exact-text classified predecessor '
                       'and normalized-text raw observation agree on all three fields. The old 2D converter '
                       'copied text/ID but omitted acquisition fields. This is a documented observation, '
                       'not a claim about the true first acquisition or canonical adoption date.') if supported else 'Original cohort lacks corroboration.',
            'observed_dates': sorted({e['values']['fetched_at'][:10] for e in history if e['eligible']}),
            'observations': history})
    for before, after in zip(canonical, candidate):
        assert {k:v for k,v in before.items() if k not in FIELDS} == {k:v for k,v in after.items() if k not in FIELDS}
        for k in FIELDS:
            if before.get(k):
                assert before[k] == after[k]
    assert [r['tweet_id'] for r in candidate] == [r['tweet_id'] for r in canonical]
    read_ids = {str(r['tweet_id']) for r in reread['items']}
    assert len(read_ids) == len(reread['items']) == 250 and read_ids <= set(ids)
    read_date = latest_read_date(reread['read_at'])
    coverage = {}
    for issue in reread['buckets']:
        relevant = {str(r['tweet_id']) for r in canonical if r.get('classification', {}).get('is_relevant') and r.get('classification', {}).get('is_opinion') and r['classification'].get('main_issue') == issue}
        issue_read = {str(r['tweet_id']) for r in reread['items'] if r['main_issue'] == issue}
        assert relevant == issue_read
        coverage[issue] = {'population': len(relevant), 'read': len(issue_read),
            'before_skipped_grown': split_unread(canonical, issue, read_ids, read_date),
            'after_skipped_grown': split_unread(candidate, issue, read_ids, read_date)}
    # A stored canonical snapshot immediately preceding the reread proves membership;
    # acquisition timestamps alone do not prove adoption.
    snapshot = subprocess.check_output(['git', 'show', '5da3a48:' + CANON], cwd=root)
    assert json.loads(snapshot) == canonical
    (out / 'canonical-before-reread-5da3a48.json').write_bytes(snapshot)
    for rel in (CANON, REREAD):
        assert sha(root / rel) == sha(shared / rel)
        dest = out / 'original' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rel, dest)
    dump(out / 'candidate.json', candidate)
    dump(out / 'decisions.json', decisions)
    dump(out / 'evidence-inventory.json', inventory)
    opinion = lambda rows: sum(bool(r.get('classification', {}).get('is_relevant') and r.get('classification', {}).get('is_opinion')) for r in rows)
    summary = {'theme': SLUG, 'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
        'canonical_sha256': sha(root / CANON), 'candidate_sha256': sha(out / 'candidate.json'),
        'reread_sha256': sha(root / REREAD), 'target_records': len(targets),
        'repaired': sum(d['status']=='repaired' for d in decisions), 'held': sum(d['status']=='held' for d in decisions),
        'unprocessed': len(targets)-len(decisions), 'multiple_observed_dates': sum(len(d['observed_dates'])>1 for d in decisions),
        'before': summarize(canonical), 'after': summarize(candidate), 'opinion_before': opinion(canonical), 'opinion_after': opinion(candidate),
        'missing_after': {k: sum(not r.get(k) for r in candidate) for k in FIELDS},
        'reread_coverage': coverage, 'reread_unchanged': True, 'canonical_before_reread_equal': True,
        'reread_target_repaired': len(read_ids & targets.keys()), 'scan_parse_errors': parse_errors,
        'id_order_text_existing_classification_unchanged': True,
        'period_note': 'Keep owner_confirmed period 2026-06-27〜2026-09-04 unchanged. Recovered observations start 2026-06-28; they do not establish the entire survey boundary.'}
    dump(out / 'summary.json', summary)
    verify_candidate(root, out)
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
