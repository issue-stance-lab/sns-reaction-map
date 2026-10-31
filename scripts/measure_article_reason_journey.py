#!/usr/bin/env python3
"""課題51: 記事閲覧・論点クリック・理由一覧表示の利用者数をGA4から読む。

公開後は configs/article-reason-journey.json に公開時刻と翌日を記入する。
--baseline は閲覧だけを取得し、未計測のクリック・到達をnullで残す。
人数は各集合をGA4へ個別に問い合わせる。記事別人数を足さない。
"""
from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import re

import fetch_ga4_metrics as ga4

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'configs/article-reason-journey.json'


def string_filter(field: str, value: str, match: str = 'EXACT') -> dict:
    return {'filter': {'fieldName': field, 'stringFilter': {
        'matchType': match, 'value': value, 'caseSensitive': True}}}


def report_payload(start: str, end: str, event: str, slugs: list[str], arrival: bool) -> dict:
    alternatives = '|'.join(re.escape(s) for s in slugs)
    if arrival:
        source = string_filter('pageReferrer',
            r'https://sns-reaction-map\.jp/articles/(' + alternatives + r')\.html', 'FULL_REGEXP')
    else:
        source = string_filter('pagePath', r'/articles/(' + alternatives + r')\.html', 'FULL_REGEXP')
    return {
        'dateRanges': [{'startDate': start, 'endDate': end}],
        # no issue/page dimensions: one user visiting several reasons is counted once.
        'metrics': [{'name': 'totalUsers'}, {'name': 'eventCount'}],
        'dimensionFilter': ga4.and_filter(
            ga4.public_host_filter(ga4.DEFAULT_HOST_NAME),
            string_filter('eventName', event), source,
            {'notExpression': string_filter('pageLocation',
                r'analytics_test=1(?:&|#|$)', 'PARTIAL_REGEXP')}
        ),
    }


def read_count(report: dict) -> dict:
    metadata = report.get('metadata', {})
    limited = any(metadata.get(k) for k in
                  ('subjectToThresholding', 'dataLossFromOtherRow', 'samplingMetadatas'))
    rows = report.get('rows', [])
    if limited:
        return {'users': None, 'events': None, 'status': 'limited', 'metadata': metadata}
    if not rows:
        return {'users': 0, 'events': 0, 'status': 'measured', 'metadata': metadata}
    # Aggregate-only report must have exactly one row. Never sum grouped unique users.
    if len(rows) != 1:
        raise ValueError('集計レポートが複数行です。利用者数を足せません。')
    values = rows[0]['metricValues']
    return {'users': int(values[0]['value']), 'events': int(values[1]['value']),
            'status': 'measured', 'metadata': metadata}


def measure(query, config: dict, start: str, end: str, baseline: bool = False) -> dict:
    date.fromisoformat(start)
    date.fromisoformat(end)
    if start > end:
        raise ValueError('開始日が終了日より後です。')
    if not baseline and (not config.get('published_at') or not config.get('first_full_day')):
        raise ValueError('未公開です。公開日時と最初の終日計測日を設定してください。')
    if not baseline and start < config['first_full_day']:
        raise ValueError('計測開始前を含みます。公開翌日以降を指定してください。')
    slugs = config['focus_articles']
    output = {'period': {'start': start, 'end': end}, 'baseline': baseline,
              'published_at': config.get('published_at'), 'articles': {},
              'notes': [
                  'usersはGA4のtotalUsers。記事別人数を足して全体人数にしない。',
                  '理由表示は同一サイト記事からの直接遷移で、選択論点の理由一覧の先頭行が半分以上表示されたとき。理解・読了は表さない。',
                  '計測拒否、広告ブロック、参照元を送らない移動は数えられない。',
                  'analytics_test=1の動作確認を除外。既存の運営者アクセス除外は未確認。',
                  '人数は各行動の集合であり、同一利用者の閉じたファネルではない。転換率と断定しない。',
                  '日付はGA4プロパティのタイムゾーン。未確定の直近日は比較に使わない。'
              ]}
    for label, group in [(s, [s]) for s in slugs] + [('combined', slugs)]:
        counts = {'page_view': read_count(query(report_payload(start, end, 'page_view', group, False)))}
        for key, event in [('reason_click', config['click_event']), ('reason_view', config['view_event'])]:
            counts[key] = ({'users': None, 'events': None, 'status': 'not_measured'} if baseline
                           else read_count(query(report_payload(start, end, event, group, key == 'reason_view'))))
        if label == 'combined':
            output['combined'] = counts
        else:
            output['articles'][label] = counts
    return output


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start', required=True)
    p.add_argument('--end', required=True)
    p.add_argument('--baseline', action='store_true')
    p.add_argument('--all-articles', action='store_true', help='記事15本全体を記事別・全体で集計する')
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    config = json.loads(CONFIG.read_text())
    if args.all_articles:
        config['focus_articles'] = sorted(p.stem for p in (ROOT / 'content/articles').glob('*/*.md'))
    # Fail before any OAuth work for unpublished or mixed periods.
    measure(lambda _: {}, config, args.start, args.end, args.baseline)
    ga4.load_dotenv(ROOT / '.env')
    ga4.TOKEN_PATH = ROOT / ga4.TOKEN_PATH
    if not ga4.TOKEN_PATH.exists() or not json.loads(ga4.TOKEN_PATH.read_text()).get('refresh_token'):
        raise SystemExit('既存のGA4認証が必要です。対話認証は開始していません。')
    client = ga4.read_client_secret()
    token = ga4.get_token(client)
    prop = os.environ['GA4_PROPERTY_ID']
    result = measure(lambda payload: ga4.call_run_report(token['access_token'], prop, payload),
                     config, args.start, args.end, args.baseline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(f'保存: {args.output}')


if __name__ == '__main__':
    main()
