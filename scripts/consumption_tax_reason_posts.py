"""理由の投稿例は、選定したIDを公開済みの再読記録へ結び付けて作る。"""
from __future__ import annotations

import json
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(data: dict, root: Path = ROOT) -> dict:
    selection = json.loads((root / 'configs/consumption-tax-reason-posts.json').read_text())
    config = yaml.safe_load((root / 'configs/planet/consumption-tax-cut.yaml').read_text())
    if selection['theme_id'] != data['theme_id']:
        raise ValueError('理由の投稿例: テーマが一致しません')
    issues = {i['id']: i for i in data['issues'] if i['sub']['status'] == 'reread'}
    if set(selection['issues']) != set(issues):
        raise ValueError('理由の投稿例: 再読済み論点の選定が一致しません')
    config_by_id = {i['id']: config['sub_issues'].get(i['key']) for i in config['issues']}
    result = {}
    for iid, issue in issues.items():
        sc = config_by_id[iid]
        raw = json.loads((root / sc['file']).read_text())
        records = raw
        for part in sc['items_path']:
            records = records[part]
        by_id = {r['tweet_id']: r for r in records}
        reasons = {r['id']: r for r in issue['sub']['items'] if not r.get('unread') and r['id'] != '__unread__'}
        chosen = selection['issues'][iid]
        if set(chosen) != set(reasons):
            raise ValueError(f'理由の投稿例: 理由分類の選定が一致しません: {iid}')
        result[iid] = {}
        for bid, ids in chosen.items():
            if not isinstance(ids, list) or not 1 <= len(ids) <= 2 or len(ids) != len(set(ids)):
                raise ValueError(f'理由の投稿例: 重複しない1〜2件を選定してください: {iid} {bid}')
            examples = []
            for tid in ids:
                row = by_id.get(tid)
                if not row or row['bucket'] != bid or row['bucket_label'] != reasons[bid]['label']:
                    raise ValueError(f'理由の投稿例: 投稿が選んだ理由に属しません: {iid} {bid} {tid}')
                if not row.get('summary') or not re.fullmatch(r'https://(?:x|twitter)\.com/[A-Za-z0-9_]+/status/' + re.escape(tid), row['url']):
                    raise ValueError(f'理由の投稿例: 要旨またはX投稿URLが不正です: {tid}')
                examples.append({k: row[k] for k in ('tweet_id', 'url', 'summary')})
            result[iid][bid] = examples
    return result


def validate_reading(reading, iid: str, examples: dict) -> list[str]:
    """別の欄に同じURLが残っていても、理由と投稿の取り違え・要旨変更を止める。"""
    problems = []
    expected = examples.get(iid, {})
    details = reading.select('details[data-tax-reason-posts]')
    if len(details) != len(expected) or {d['data-tax-reason-posts'] for d in details} != set(expected):
        problems.append(f'理由の投稿例: 開閉項目が一致しません: {iid}')
    for bid, posts in expected.items():
        targets = reading.select(f'[data-tax-reason="{bid}"] > details[data-tax-reason-posts="{bid}"]')
        if len(targets) != 1:
            problems.append(f'理由の投稿例: 所属する理由が一致しません: {iid} {bid}')
            continue
        cards = targets[0].select('[data-tax-reason-post-url]')
        if [c['data-tax-reason-post-url'] for c in cards] != [p['url'] for p in posts]:
            problems.append(f'理由の投稿例: 投稿URLが一致しません: {iid} {bid}')
            continue
        for card, post in zip(cards, posts):
            summary = card.select_one('.tax-reason-post-summary')
            if not summary or summary.get_text(types=None) != post['summary']:
                problems.append(f'理由の投稿例: 要旨が再読記録と一致しません: {iid} {bid}')
            if {a.get('href') for a in card.select('a[href]')} != {post['url']}:
                problems.append(f'理由の投稿例: 元投稿のリンクが一致しません: {iid} {bid}')
            if len(card.select('template.tax-reason-embed-template .twitter-tweet')) != 1:
                problems.append(f'理由の投稿例: 遅延表示する埋め込みがありません: {iid} {bid}')
    return problems
