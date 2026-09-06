"""今回の棚卸しを再実行する読み取り専用スクリプト。本文・投稿IDは出力しない。"""
import collections
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
import tarfile

import yaml

root = pathlib.Path(sys.argv[1]).resolve()
themes = yaml.safe_load((root / 'THEMES.yaml').read_text())['themes']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field(row, key):
    return row.get('classification', {}).get(key, row.get(key))


def identity(row):
    # 今回の正典は全行 tweet_id あり。欠落時は黙って件数を確定しない。
    assert row.get('tweet_id')
    return str(row['tweet_id'])


tracked = set(subprocess.check_output(['git', 'ls-files'], cwd=root, text=True).splitlines())
missing_rows = {}
out = {'audited_at': datetime.datetime.now().astimezone().isoformat(),
       'source_root': str(root),
       'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
       'themes_sha256': digest(root / 'THEMES.yaml'), 'themes': {}}
for topic, cfg in themes.items():
    path = root / cfg['sample_file']
    rows = json.loads(path.read_text())
    ids = {identity(r) for r in rows}
    missing_rows[topic] = {identity(r): r for r in rows if not r.get('fetched_at')}
    opinions = [r for r in rows if field(r, 'is_opinion') is True]
    dates = []
    invalid_dates = 0
    for r in rows:
        if r.get('fetched_at'):
            try:
                dates.append(datetime.datetime.fromisoformat(r['fetched_at'].replace('Z', '+00:00')).date().isoformat())
            except ValueError:
                invalid_dates += 1
    waves = []
    for wp in sorted((root / 'social-samples/updates' / topic).glob('*/classified.json')):
        wr = json.loads(wp.read_text())
        rp = wp.with_name('report.json')
        report = json.loads(rp.read_text()) if rp.exists() else {}
        waves.append({'date': wp.parent.name, 'classified': len(wr),
                      'outside_canonical': len({identity(r) for r in wr} - ids),
                      'report_keys': sorted(report), 'sha256': digest(wp)})
    query_cfg = yaml.safe_load((root / cfg['refresh_config']).read_text())
    data = {'title': cfg['title'], 'sample_file': cfg['sample_file'], 'sha256': digest(path),
            'git_tracked': cfg['sample_file'] in tracked,
            'collected': len(rows), 'opinions_current_rule': len(opinions),
            'missing': {k: sum(not r.get(k) for r in rows) for k in ['text', 'tweet_id', 'url', 'fetched_at', 'query', 'source']},
            'nested_flags_missing': {k: sum(k not in r.get('classification', {}) for r in rows)
                                     for k in ['is_opinion', 'is_relevant']},
            'duplicate_id_rows': len(rows) - len(ids),
            'repeated_text_extra_rows': sum(n - 1 for n in collections.Counter(r['text'] for r in rows).values()),
            'invalid_dates': invalid_dates, 'date_min': min(dates) if dates else None,
            'date_max': max(dates) if dates else None,
            'text_over_1200': sum(len(r.get('text', '')) > 1200 for r in rows),
            'issue_counts': dict(collections.Counter(field(r, 'main_issue') for r in opinions)),
            'query_count_current_config': len(query_cfg.get('fetch_queries', [])),
            'sample_period_registry': str(cfg.get('sample_period')),
            'sample_period_source': cfg.get('sample_period_source'),
            'waves': waves}
    out['themes'][topic] = data
out['totals'] = {k: sum(t[k] for t in out['themes'].values())
                 for k in ['collected', 'opinions_current_rule', 'duplicate_id_rows']}
out['totals']['missing_fetched_at'] = sum(t['missing']['fetched_at'] for t in out['themes'].values())

# 日付の復元候補を探すだけ。別日に再取得した記録も含むため正典へは書き戻さない。
wanted = {i for rows in missing_rows.values() for i in rows}
evidence = collections.defaultdict(list)
evidence_files = {}
for path in (root / 'social-samples').rglob('*.json'):
    if 'synthetic' in path.name:
        continue
    try:
        rows = json.loads(path.read_text())
    except (ValueError, UnicodeDecodeError):
        continue
    if not isinstance(rows, list):
        continue
    matched = False
    for r in rows:
        if isinstance(r, dict) and str(r.get('tweet_id', '')) in wanted and r.get('fetched_at'):
            evidence[str(r['tweet_id'])].append(r)
            matched = True
    if matched:
        evidence_files[str(path.relative_to(root))] = digest(path)
out['recovery_evidence_files_sha256'] = evidence_files
for topic, rows in missing_rows.items():
    out['themes'][topic]['recovery_candidates'] = {
        'same_id_with_observation_date': sum(i in evidence for i in rows),
        'same_id_and_exact_text': sum(any(r.get('text') == s.get('text') for r in evidence[i]) for i, s in rows.items()),
        'multiple_observation_dates': sum(len({r['fetched_at'][:10] for r in evidence[i]}) > 1 for i in rows),
    }
out['legacy_wave_membership'] = []
for topic, name in [('school-nickname-ban', 'school-nickname-ban_hermes_cur_20260726.json'),
                    ('henoko-student-accident', 'henoko_hermes_cur_20260726.json')]:
    path = root / 'social-samples' / name
    rows = json.loads(path.read_text())
    current = {identity(r) for r in json.loads((root / themes[topic]['sample_file']).read_text())}
    out['legacy_wave_membership'].append({'topic': topic, 'path': str(path.relative_to(root)),
        'sha256': digest(path), 'total': len(rows), 'outside_canonical': len({identity(r) for r in rows} - current)})

backups = sorted(pathlib.Path('/Volumes/HD-LE-B/issue-stance-private-backups').glob('private-data-*.tar.gz'),
                 key=lambda p: p.stat().st_mtime)
if backups:
    with tarfile.open(backups[-1]) as tar:
        manifest = json.load(tar.extractfile('manifest.json'))
    entries = {f['path']: f for f in manifest['files']}
    out['backup'] = {'path': str(backups[-1]), 'file_count': len(entries), 'created_at': manifest['created_at'],
                     'canonical': {t: {'in_archive': d['sample_file'] in entries,
                        'matches_manifest': entries.get(d['sample_file'], {}).get('sha256') == d['sha256'],
                        'git_tracked': d['git_tracked']} for t, d in out['themes'].items()}}
else:
    out['backup'] = {'available': False}
print(json.dumps(out, ensure_ascii=False, indent=2))
