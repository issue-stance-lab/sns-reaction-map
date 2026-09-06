"""Read body-free data ledgers for the local dashboard; unknown never becomes zero."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
import subprocess
import yaml
from verify_adoption_registry import verify
from reread_registry import validate_manifest
from manage_reread_registry import check_sources
from verify_data_assets import verify as verify_assets

ROOT = Path(__file__).resolve().parents[2]


def _read(path):
    return json.loads(path.read_text())


def _age(stamp, today):
    if not isinstance(stamp, str):
        raise ValueError('日時がありません')
    parsed = dt.datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('日時にタイムゾーンがありません')
    return (today - parsed.astimezone(dt.timezone(dt.timedelta(hours=9))).date()).days


def _fresh(stamp, today):
    age = _age(stamp, today)
    return '確認時点が未来です' if age < 0 else ('7日超・再確認が必要' if age > 7 else '7日以内の記録')


def collect_data_assets(today, root=ROOT):
    root = Path(root)
    result = {'themes': [], 'adoption_status': '未確認', 'snapshot_at': None,
              'backup': {'status': '記録なし・未確認'}, 'operations': [], 'operations_status': '未確認'}
    try:
        themes = yaml.safe_load((root / 'THEMES.yaml').read_text())['themes']
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
        result['adoption_status'] = 'テーマ台帳が読めません: ' + str(exc)
        return result
    registry = None
    try:
        verify(root)
        registry = _read(root / 'data/verification/adoption/registry.json')
        # The CI verifier checks Git evidence. Check private files too when available.
        for item in registry['topics'].values():
            path = root / item['canonical_file']
            if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != item['canonical_sha256']:
                raise ValueError('正典の版が照合記録から変わっています')
        result['snapshot_at'] = registry['snapshot_at']
        result['adoption_status'] = '台帳検査合格 / ' + _fresh(registry['snapshot_at'], today)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        registry = None
        result['adoption_status'] = '検査失敗・件数未確認: ' + str(exc)
    for topic, theme in themes.items():
        row = {'topic': topic, 'title': theme['title'], 'published': theme.get('published') == 'done',
               'canonical': None, 'saved': None, 'pending': None, 'unknown': None, 'unresolved': None,
               'excluded': None, 'reread_status': '共通台帳未管理', 'active': None, 'reread_excluded': None, 'unreviewed': None}
        item = registry['topics'][topic] if registry else None
        if item:
            row.update(canonical=sum(r['canonical_presence'] for r in item['records']), saved=item['saved_unique_records'])
            for label, status in [('pending','pending_review'), ('unknown','decision_unknown'), ('unresolved','unresolved'), ('excluded','excluded_confirmed')]:
                row[label] = sum(not r['canonical_presence'] and r['adoption_status'] == status for r in item['records'])
        path = root / f'data/verification/reread/{topic}.json'
        if path.exists():
            try:
                manifest = _read(path)
                validate_manifest(manifest)
                check_sources(root, manifest)
                if manifest['topic'] != topic or not item or manifest['canonical_sha256'] != item['canonical_sha256']:
                    raise ValueError('正典との版照合が未確認または不一致')
                freshness = _fresh(manifest['snapshot_at'], today)
                row['active'] = sum(r['review'] is not None and r['is_opinion'] for r in manifest['records'])
                row['reread_excluded'] = sum(r['review'] is not None and not r['is_opinion'] for r in manifest['records'])
                row['unreviewed'] = sum(r['review'] is None and r['is_opinion'] for r in manifest['records'])
                row['reread_status'] = '台帳検査合格 / ' + freshness
            except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
                row['reread_status'] = '検査失敗・件数未確認: ' + str(exc)
        result['themes'].append(row)
    try:
        backup = _read(root / 'company/data-backup-status.json')
        if backup['schema_version'] != 1 or backup['restore_verified'] is not True:
            raise ValueError('復元検証の成功記録がありません')
        if not isinstance(backup['files'], list) or len(backup['files']) != backup['file_count']:
            raise ValueError('バックアップのファイル件数が不一致')
        if not re.fullmatch(r'[0-9a-f]{64}', backup['archive_sha256']) or not re.fullmatch(r'[0-9a-f]{40}', backup['git_commit']):
            raise ValueError('バックアップの指紋が不正')
        if any(type(f['bytes']) is not int or f['bytes'] < 0 or not re.fullmatch(r'[0-9a-f]{64}', f['sha256']) for f in backup['files']):
            raise ValueError('ファイルの指紋または容量が不正')
        if sum(f['bytes'] for f in backup['files']) != backup['total_bytes']:
            raise ValueError('バックアップの容量が不一致')
        result['backup'] = {'status': '最終復元確認の記録（同じマシン） / ' + _fresh(backup['verified_at'], today),
                            'verified_at': backup['verified_at'], 'file_count': backup['file_count'],
                            'archive_name': backup['archive_name'], 'git_commit': backup['git_commit']}
    except FileNotFoundError:
        pass
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        result['backup'] = {'status': '検査失敗・未確認: ' + str(exc)}
    try:
        ops = yaml.safe_load((root / 'company/data-operations.yaml').read_text())
        if ops['schema_version'] != 1 or not isinstance(ops['operations'], list):
            raise ValueError('運用台帳の形式が不正')
        entries = []
        for op in ops['operations']:
            due = dt.date.fromisoformat(str(op['due_at']))
            if op['status'] not in {'pending', 'done'} or not all(op.get(k) for k in ('id','title','owner','task','next_action')):
                raise ValueError('担当・期日・次の作業が不足')
            entries.append({**op, 'due_at': due.isoformat(), 'overdue': op['status'] != 'done' and due < today})
        result['operations'], result['operations_status'] = entries, '担当・期日を登録済み'
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        result['operations_status'] = '検査失敗・予定未確認: ' + str(exc)
    result['inventory'] = {'status': '保管境界の記録なし・未確認'}
    try:
        inventory = _read(root / 'company/data-assets.json')
        verify_assets(root)
        for entry in inventory['files']:
            path = root / entry['path']
            if entry['storage'] == 'private_backup' and path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
                raise ValueError('非公開の原本が保管記録から変わっています')
        if inventory['schema_version'] != 1:
            raise ValueError('保管境界の形式が不正')
        summary = {key: sum(f['storage'] == key for f in inventory['files']) for key in ('git', 'private_backup', 'external_evidence')}
        if summary != inventory['summary']:
            raise ValueError('保管境界の件数が不一致')
        coverage = inventory['backup']
        for value in coverage.values():
            if value['status'] not in {'verified', 'missing', 'stale'}:
                raise ValueError('保全照合の状態が不明')
            if value['status'] == 'verified' and (value['missing'] or value['changed']):
                raise ValueError('保全照合の成功記録に欠落・変更があります')
        result['inventory'] = {'status': _fresh(inventory['snapshot_at'], today), 'summary': summary,
                               'coverage': {k: {'status': v['status'], 'missing': len(v['missing']), 'changed': len(v['changed'])} for k,v in coverage.items()}}
    except FileNotFoundError:
        pass
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError, subprocess.SubprocessError) as exc:
        result['inventory'] = {'status': '検査失敗・保管状態未確認: ' + str(exc)}
    return result
