#!/usr/bin/env python3
"""再読証拠の継承、差分確認、対象固定、確認済み結果の登録。本文を新台帳へ保存しない。"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import yaml
from public_registry_common import is_opinion_record
from reread_registry import snapshot_records, assess, create_target, record_reviews

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(tid):
    return hashlib.sha256(str(tid).encode()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value, *, replace=False):
    if path.exists() and not replace:
        raise ValueError(f'既存の記録を上書きしません: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(content)
    temporary.replace(path)


def canonical(root, topic):
    themes = yaml.safe_load((root / 'THEMES.yaml').read_text())['themes']
    path = root / themes[topic]['sample_file']
    return path, read(path)


def registry_path(root, topic):
    return root / 'data/verification/reread' / f'{topic}.json'


def dig(obj, path):
    for component in path:
        obj = obj[component]
    return obj


def initialize(root, topic, snapshot_at):
    path, rows = canonical(root, topic)
    records = snapshot_records(rows)
    by_key = {r['post_key']: r for r in records}
    manifest = {'schema_version': 1, 'topic': topic, 'snapshot_at': snapshot_at,
                'canonical_sha256': digest(path), 'sources': {},
                'source_date_labels': {}, 'records': records,
                'migration_note': '移行時の本文指紋は読了時の指紋ではない。旧記録の不明な日時・確認者・版を推測で補わない。'}
    cfg_path = root / 'configs/planet' / f'{topic}.yaml'
    cfg = yaml.safe_load(cfg_path.read_text()) if cfg_path.exists() else {}
    seen = set()
    for issue, spec in (cfg.get('sub_issues') or {}).items():
        source = spec['file']
        data = read(root / source)
        manifest['sources'][source] = digest(root / source)
        manifest['source_date_labels'][source] = data.get('read_at')
        items = dig(data, spec.get('items_path', spec['path'][:-1] + ['items']))
        if spec.get('item_issue_field'):
            items = [r for r in items if r.get(spec['item_issue_field']) == issue]
        buckets = dig(data, spec['path'])
        actual = Counter(item.get('bucket') for item in items)
        if set(actual) - set(buckets) or any(actual.get(k, 0) != v['count'] for k, v in buckets.items()):
            raise ValueError('再読区分の件数と投稿IDの実数が一致しません')
        for item in items:
            pk = key(item['tweet_id'])
            if pk in seen:
                raise ValueError('再読の投稿IDが重複しています')
            seen.add(pk)
            if item.get('body_reviewed') is False or item.get('review_kind') == 'automated_classification':
                raise ValueError('自動分類を本文再読として継承できません')
            row = by_key[pk]
            if row['main_issue'] != issue or not row['is_opinion']:
                raise ValueError('再読記録と現行の論点・意見判定が一致しません')
            review_source = source
            reviewer_type = data.get('reviewer_type', 'unspecified_editorial')
            if topic == 'bike-blue-ticket' and item.get('source_id') in ('opposition', 'supplement'):
                origin = data['sources'][item['source_id']]
                review_source = origin['file']
                reviewer_type = origin['reviewer_type']
                manifest['sources'][review_source] = digest(root / review_source)
                manifest['source_date_labels'][review_source] = origin.get('read_at', origin.get('recorded_at'))
            row['review'] = {'kind': 'editorial_body_reread', 'evidence_quality': 'legacy',
                'read_at': None, 'reviewer_type': reviewer_type,
                'reviewer': None, 'method_version': None, 'text_sha256': None,
                'reason_sha256': None, 'source_file': review_source, 'source_sha256': digest(root / review_source),
                'bucket': item['bucket']}
    if topic == 'bike-blue-ticket':
        # 派生ファイルでは除外97件の読了メタデータが省略されるため、原証拠へ結び直す。
        source = 'data/bike-blue-ticket_editorial-reread-20260906.json'
        evidence = read(root / source)
        manifest['sources'][source] = digest(root / source)
        manifest['source_date_labels'][source] = evidence.get('read_at')
        method = hashlib.sha256(str(evidence['method']).encode()).hexdigest()
        strict_seen = set()
        for item in evidence['items']:
            if item.get('body_reviewed') is not True or item.get('review_kind') != 'editorial_body_reread':
                raise ValueError('追加証拠は本文再読済みである必要があります')
            if key(item['tweet_id']) in strict_seen:
                raise ValueError('追加証拠の投稿IDが重複しています')
            strict_seen.add(key(item['tweet_id']))
            row = by_key[key(item['tweet_id'])]
            if item['text_sha256'] != row['baseline_text_sha256'] or item['main_issue'] != row['main_issue']:
                raise ValueError('読了時の本文・論点と現在の原本が違います')
            row['review'] = {'kind': item['review_kind'], 'evidence_quality': 'verified',
                'read_at': item['read_at'], 'reviewer_type': evidence['reviewer_type'],
                'reviewer': item['reviewer'], 'method_version': 'sha256:' + method,
                'text_sha256': item['text_sha256'], 'reason_sha256': item['reason_sha256'],
                'source_file': source, 'source_sha256': digest(root / source), 'bucket': item['bucket']}
    assess(manifest, rows)
    return manifest


def check_sources(root, manifest):
    for source, expected in manifest.get('sources', {}).items():
        path = (root / source).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError('継承元はリポジトリ内に指定してください')
        if not path.is_file() or digest(path) != expected:
            raise ValueError(f'継承元の再読記録が変わっています: {source}。対象と証拠を確認してください')


def summarize(manifest, rows):
    result = assess(manifest, rows)
    opinions = {r['post_key'] for r in snapshot_records(rows) if r['is_opinion']}
    opinion_counts = Counter({name: 0 for name in result['summary']})
    for record in result['records']:
        if record['post_key'] in opinions:
            opinion_counts.update(record['statuses'])
    return {'all_records': result['summary'], 'current_opinions': dict(opinion_counts)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['initialize', 'status', 'prepare', 'record'])
    parser.add_argument('--topic', required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--snapshot-at')
    parser.add_argument('--issue')
    parser.add_argument('--target', type=Path)
    parser.add_argument('--reviews', type=Path)
    parser.add_argument('--private-input', type=Path)
    args = parser.parse_args()
    path, rows = canonical(ROOT, args.topic)
    ledger_path = registry_path(ROOT, args.topic)
    if args.command == 'initialize':
        stamp = args.snapshot_at or datetime.now(timezone.utc).isoformat()
        manifest = initialize(ROOT, args.topic, stamp)
        write(args.out or ledger_path, manifest)
    else:
        manifest = read(ledger_path)
        check_sources(ROOT, manifest)
        if args.command == 'prepare':
            if args.out is None:
                parser.error('prepare は --out に固定対象の保存先を指定してください')
            evaluation = assess(manifest, rows)
            fresh = {r['post_key']: r for r in snapshot_records(rows)}
            selected = [r['post_key'] for r in evaluation['records']
                        if 'removed' not in r['statuses']
                        and any(s in r['statuses'] for s in ('unreviewed','body_changed','issue_changed','opinion_changed','added'))
                        and fresh[r['post_key']]['is_opinion']
                        and (not args.issue or fresh[r['post_key']]['main_issue'] == args.issue)]
            if not selected:
                print('新たに読む対象は0件です。台帳を変更していません')
                return 0
            if args.out.exists() or (args.private_input and args.private_input.exists()):
                raise ValueError('既存の固定対象・本文付き入力を上書きしません')
            target = create_target(manifest, selected, current_rows=rows)
            if args.private_input:
                try:
                    args.private_input.resolve().relative_to(ROOT.resolve())
                except ValueError:
                    pass
                else:
                    raise ValueError('本文付き入力はリポジトリ外の非公開保存先へ指定してください')
                selected_set = set(selected)
                write(args.private_input, [{'post_key': key(r['tweet_id']), 'tweet_id': str(r['tweet_id']),
                       'text': r.get('text',''), 'main_issue': (r.get('classification') or {}).get('main_issue')}
                       for r in rows if key(r['tweet_id']) in selected_set])
            write(args.out, target)
            print(f'読む対象を固定しました: {len(selected)}件。読了としては登録していません')
            return 0
        if args.command == 'record':
            if not args.target or not args.reviews:
                parser.error('record は --target と --reviews が必要です')
            manifest = record_reviews(manifest, read(args.target), read(args.reviews), current_rows=rows)
            # 次版として保存。既存台帳の差し替えは、差分・対象・証拠を確認してから行う。
            if args.out is None:
                parser.error('record は --out に次版台帳の保存先を指定してください')
            write(args.out, manifest)
    print(json.dumps(summarize(manifest, rows), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
