#!/usr/bin/env python3
"""Reproduce the two-theme period proposal from the preserved, private input bundle.

No collection, AI calls, canonical writes, or publication. Output must not exist.
Usage: python3 quality/reviews/2026-09-06-period-review.py INPUT_BUNDLE NEW_OUTPUT
"""
from __future__ import annotations
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import verify_sample_periods as periods

EXPECTED = {
    'ai-copyright/original.json': '5878c17bcfe347643f24238b4f2f8dfba2019f394f5b0da0cbe77921590d86f8',
    'ai-copyright/candidate.json': '7874e74c64a3e142ebb700ac95c3f8968c20c217d091d6b66590c2c4e6d4a786',
    'ai-copyright/ai-copyright_classified.json': '585fcc623540c2e43ec1931001056790b155bfbcaacfcd09ae5054838d88cfb5',
    'ai-copyright/ai-copyright_samples.json': '81a6866796eea13791c268da425097822d34eaa024325e4fd1346372966d6766',
    'takaichi/original.json': 'cdad5a2196712c81650df45bad105f2bf1a8c983c2ddd101852e5f2dfa90fddb',
    'takaichi/candidate.json': 'aee97f77330a187e3264a31a35ce9736c953cbfaae73979972bb0e96e39e0d74',
    'takaichi/takaichi_realtime_samples.json': 'd3321e174a0549c6b045a3e8cad13129e58b33617109327f3bd5dd882e79ad69',
    'takaichi/takaichi_realtime_ollama_batch_classified.json': '104a022de11263e61b8488c62ac5ae6b7fc45286f4e9f49fc6b326b51e58392e',
    'old-2d.json': '0a6cb95929f6e899c22236213e3e299023131f8075067b94ee70156fa250770d',
}
FIELDS = ('fetched_at', 'query', 'source')
JST = timezone(timedelta(hours=9))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def clean(text):
    return re.sub(r'\s+', '', text.replace('\tSTART\t', '').replace('\tEND\t', ''))

def profile(rows):
    values = [row['fetched_at'] for row in rows]
    dates = [datetime.fromisoformat(value.replace('Z', '+00:00')) for value in values]
    assert all(x.tzinfo is not None and x.utcoffset() == timedelta(0) for x in dates)
    assert not any(re.fullmatch(r'\d{4}-\d{2}-\d{2}', value) for value in values)
    return {
        'records': len(rows), 'full_utc_timestamp_records': len(dates),
        'date_only_records': 0, 'naive_timestamp_records': 0,
        'timestamp_suffix_counts': dict(Counter('Z' if v.endswith('Z') else '+00:00' for v in values)),
        'utc_min': min(dates).isoformat(), 'utc_max': max(dates).isoformat(),
        'jst_min': min(dates).astimezone(JST).isoformat(),
        'jst_max': max(dates).astimezone(JST).isoformat(),
        'utc_date_counts': dict(sorted(Counter(str(d.date()) for d in dates).items())),
        'jst_date_counts': dict(sorted(Counter(str(d.astimezone(JST).date()) for d in dates).items())),
        'utc_vs_jst_date_changed_records': sum(d.date() != d.astimezone(JST).date() for d in dates),
    }

def main():
    inputs, out = map(Path, sys.argv[1:])
    for name, expected in EXPECTED.items():
        assert sha(inputs / name) == expected, f'input drift: {name}'
    out.mkdir(parents=True, exist_ok=False)
    read = lambda name: json.loads((inputs / name).read_text())
    ai = read('ai-copyright/candidate.json')
    held = read('ai-copyright/held.json')
    assert len(held) == 1
    tweet_id = held[0]['tweet_id']
    target = next(row for row in ai if row['tweet_id'] == tweet_id)
    raw = next(row for row in read('ai-copyright/ai-copyright_samples.json') if row['tweet_id'] == tweet_id)
    old_rows = read('old-2d.json')
    old_lookup = {row['tweet_id']: row for row in old_rows}
    classified = {row['tweet_id']: row for row in read('ai-copyright/ai-copyright_classified.json')}
    previous = classified[tweet_id]
    assert len(old_rows) == 339
    assert all(row['text'] == classified[row['tweet_id']]['text'][:200] for row in old_rows)
    assert all(row['url'] == classified[row['tweet_id']]['url'] for row in old_rows)
    assert sum(len(row['text']) == 200 for row in old_rows) == 1
    assert target['text'] == old_lookup[tweet_id]['text'] == previous['text'][:200]
    assert len(previous['text']) == 207 and len(target['text']) == 200
    assert clean(raw['text']) == clean(previous['text'])
    assert target['url'] == raw['url'] == previous['url']
    assert old_lookup[tweet_id]['original_category'] == previous['classification']['category']
    assert old_lookup[tweet_id]['original_stance'] == previous['classification']['stance']
    code = (inputs / 'old-classifier.py').read_text()
    assert '"text": text[:200]' in code and '"ai-copyright_classified.json"' in code
    assert '"ai-copyright_2d_classified.json"' in code
    for field in FIELDS:
        assert not target.get(field) and raw[field] == previous[field]
        target[field] = raw[field]
    proof = {
        'tweet_id': tweet_id, 'disposition': 'recovered_metadata_only',
        'raw_values': {field: raw[field] for field in FIELDS},
        'old_classified_text_length': 207, 'canonical_text_length': 200,
        'old_2d_records': 339, 'matching_text_200_prefix': 339, 'matching_url': 339,
        'exact_200_character_records': 1, 'raw_to_old_classified_normalization': 'Yahoo START/END markers and whitespace',
        'canonical_text_changed': False, 'source_code_reference': '1b72277:scripts/classify_2d_opencodego.py:206',
        'earliest_saved_2d_reference': 'dd94fba:social-samples/ai-copyright_2d_classified.json',
        'limit': 'Exact original execution command is not recovered. Historical output, input and committed transformation agree for all 339 rows.',
    }
    write(out / 'held-resolution.json', proof)
    takaichi = read('takaichi/candidate.json')
    candidates = {'ai-copyright': ai, 'takaichi': takaichi}
    evidence, checks, profiles = {}, {}, {}
    proposals = {}
    current = periods.parse_themes_yaml()
    for slug, rows in candidates.items():
        original = read(f'{slug}/original.json')
        assert len(original) == len(rows)
        changed = 0
        for before, after in zip(original, rows):
            assert {k: v for k, v in before.items() if k not in FIELDS} == {k: v for k, v in after.items() if k not in FIELDS}
            for field in FIELDS:
                if before.get(field): assert before[field] == after[field]
                assert after[field]
            changed += before != after
        assert changed == (339 if slug == 'ai-copyright' else 140)
        write(out / f'{slug}-candidate.json', rows)
        evidence[slug] = periods.summarize(rows)
        profiles[slug] = profile(rows)
        proposed = periods.expected_period(evidence[slug])
        assert proposed == ('2026-06-22〜2026-09-05' if slug == 'ai-copyright' else '2026-06-13〜2026-08-19')
        proposals[slug] = {
            'previous': {key: current[slug].get(key) for key in ('sample_period','sample_period_source')},
            'candidate_fields': {'sample_period': proposed, 'sample_period_source': 'recovered_fetched_at_utc'},
            'source': 'saved full UTC fetched_at timestamps; reconstructed observations, not first collection/adoption dates',
            'display_note': '保存された取得日時のUTC日付に基づく範囲です。' + ('日本時間では2026年6月14日〜8月20日です。' if slug == 'takaichi' else ''),
            'status': 'preview_proposal_only',
            'owner_history_preserved': slug == 'ai-copyright',
        }
        checks[slug] = {'records': len(rows), 'metadata_repaired': changed, 'missing_each_field': {f: sum(not r.get(f) for r in rows) for f in FIELDS}, 'text_and_classification_preserved': True, 'existing_metadata_preserved': True, 'id_order_and_set_preserved': True, 'candidate_sha256': sha(out / f'{slug}-candidate.json')}
    proposed_themes = {slug: {**current[slug], **proposals[slug]['candidate_fields']} for slug in candidates}
    original_parser = periods.parse_themes_yaml
    try:
        periods.parse_themes_yaml = lambda: proposed_themes
        with contextlib.redirect_stdout(io.StringIO()) as result:
            exit_code = periods.verify(evidence)
        assert exit_code == 0
    finally:
        periods.parse_themes_yaml = original_parser
    checks['candidate_period_verification'] = {'exit_code': exit_code, 'stdout': result.getvalue(), 'implementation': 'unchanged scripts/verify_sample_periods.py'}
    write(out / 'checks.json', checks)
    write(out / 'sample-periods.json', evidence)
    write(out / 'timestamp-profiles.json', profiles)
    write(out / 'theme-period-proposals.json', proposals)
    write(out / 'input-fingerprints.json', {str(p.relative_to(inputs)): sha(p) for p in sorted(inputs.rglob('*')) if p.is_file()})
    print(json.dumps(checks, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
