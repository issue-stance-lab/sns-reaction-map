"""Display reproducible restore evidence without claiming a live disk check."""
import datetime as dt
import hashlib
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_CHECKS = {
    'scripts/data_asset_inventory.py', 'scripts/build_adoption_registry.py',
    'scripts/verify_public_registry.py', 'scripts/verify_reread_registry.py',
    'scripts/verify_builder_rebuildability.py', 'scripts/verify_data_assets.py',
}


def collect(today, root=ROOT):
    root = Path(root)
    result = {'status': '復元・再生成の記録なし・未確認'}
    path = root / 'company/data-restore-status.json'
    if not path.exists():
        return result
    try:
        record = json.loads(path.read_text())
        if (type(record['schema_version']) is not int or record['schema_version'] != 1
                or record['restore_and_rebuild_verified'] is not True
                or record['physical_other_machine'] is not False
                or record['method'] != 'same_machine_clean_git_clone_and_two_archives'):
            raise ValueError('復元方法または成功記録が不正です')
        if not re.fullmatch('[0-9a-f]{40}', record['git_commit']):
            raise ValueError('確認コミットの形式が不正です')
        checks = record['checks']
        if (not isinstance(checks, list) or len(checks) != len(REQUIRED_CHECKS)
                or {c['check'] for c in checks} != REQUIRED_CHECKS
                or any(c['passed'] is not True for c in checks)):
            raise ValueError('必要な復元・再生成検査の成功記録が不足しています')
        inventory = json.loads((root / 'company/data-assets.json').read_text())
        current = hashlib.sha256(json.dumps(inventory['files'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if current != record['asset_content_sha256']:
            raise ValueError('現在の資産台帳と復元対象の版が異なります。再確認が必要です')
        for name, field in [('data-backup-status.json', 'private_archive_sha256'),
                            ('data-evidence-backup-status.json', 'external_archive_sha256')]:
            receipt = json.loads((root / 'company' / name).read_text())
            if (not re.fullmatch('[0-9a-f]{64}', record[field])
                    or receipt['archive_sha256'] != record[field]
                    or receipt['restore_verified'] is not True):
                raise ValueError('現在のバックアップと復元対象の版が異なります')
        stamp = dt.datetime.fromisoformat(record['verified_at'].replace('Z', '+00:00'))
        if stamp.tzinfo is None:
            raise ValueError('確認日時のタイムゾーンがありません')
        age = (today - stamp.astimezone(dt.timezone(dt.timedelta(hours=9))).date()).days
        freshness = '確認日時が未来・要確認' if age < 0 else ('7日超・再確認が必要' if age > 7 else '7日以内の記録')
        result = {'status': 'Gitと2種類のバックアップから復元・再生成を確認 / ' + freshness,
                  'verified_at': record['verified_at'], 'git_commit': record['git_commit'], 'checks': len(checks)}
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        result['status'] = '検査失敗・復元状態未確認: ' + str(exc)
    return result


def render_card(today, root=ROOT):
    record = collect(today, root)
    esc = lambda value: escape(str(value))
    return ('<article class="panel"><h3>原本からの復元・再生成</h3><p>'
            + esc(record['status']) + '<br>確認日時: ' + esc(record.get('verified_at', '未確認'))
            + ' / 検査数: ' + esc(record.get('checks', '未確認'))
            + '<br>確認コミット: ' + esc(record.get('git_commit', '未確認'))
            + '</p><p class="small muted">同じマシンの新しいGitコピーに復元した記録です。'
            '別マシンでの復元は未実施（課題33・50）。現在の外付け接続状態は検査していません。'
            '</p></article>')
