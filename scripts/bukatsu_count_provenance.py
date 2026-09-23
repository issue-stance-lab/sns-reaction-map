"""bukatsu-chiikiの読書面に出る再読・共通の心配・語られていない争点の件数を、元記録に照合する。

一般の立場・論点集計とは母集団が違うため、値の許可リストには追加しない。
元記録と完全一致した要素だけを、数字検査へ根拠付きで返す。
scripts/consumption_tax_count_provenance.pyのbukatsu-chiiki版（同じ考え方の移植）。
"""
from collections import Counter
import json
from pathlib import Path

from bs4 import BeautifulSoup
import yaml

from scripts.bukatsu_connected import START as BUKATSU_CONNECTED_START


def verified_selectors(source: str, root: Path) -> dict[str, str]:
    if BUKATSU_CONNECTED_START not in source:
        return {}
    soup = BeautifulSoup(source, 'html.parser')
    result = {}

    def read(path):
        return json.loads((root / path).read_text())

    def verify(element_id, expected, evidence):
        # bukatsu-chiikiは地下水脈・沈んだ大陸が複数の論点にまたがることがあり（消費税には無い形）、
        # 同じidが論点ごとの読書面テンプレート（<template>、実行時は1つしかDOMに現れない）へ
        # 複数回焼き込まれる。ページ本文の静的HTMLはtemplateを全部同時に含むため、id一致は
        # 1件だけに限定せず、見つかった全件が同じ内容であることを確認する。
        nodes = soup.select('#' + element_id)
        if not nodes or any(node.get_text(types=None) != expected for node in nodes):
            raise ValueError(f'連動表示の数字が元記録と一致しません: {element_id} ← {evidence}')
        result['#' + element_id] = evidence
        return nodes[0]

    cfg = yaml.safe_load((root / 'configs/planet/bukatsu-chiiki.yaml').read_text())
    public = read('data/public/themes/bukatsu-chiiki.json')
    counts = {i['id']: i['count'] for i in public['issues']}
    for issue in cfg['issues']:
        sc = cfg['sub_issues'].get(issue['key'])
        if not sc:
            continue
        raw = read(sc['file'])
        buckets = raw
        for part in sc['path']:
            buckets = buckets[part]
        records = raw
        for part in sc.get('items_path', sc['path'][:-1] + ['items']):
            records = records[part]
        actual = Counter(r['bucket'] for r in records)
        if set(actual) - set(buckets) or any(actual[k] != b['count'] for k, b in buckets.items()):
            raise ValueError('再読分類の件数と投稿記録が一致しません: ' + issue['id'])
        items = {k: {'label': b['label'], 'count': actual[k]} for k, b in buckets.items()}
        gap = counts[issue['id']] - len(records)
        if gap < 0:
            raise ValueError('再読記録が論点の母数を超えています: ' + issue['id'])
        if gap:
            items['__unread__'] = {'label': 'まだ読み直していない分', 'count': gap}
        # 立場別の内訳（data-bkt-counts）は、生データにstanceが付いている論点の通常の理由行だけ
        # 照合する（制度・移行プロセス・教育的意義・機会は立場が無く対象外。__unread__の立場別内訳は
        # 論点の立場別母数の再算出が要り、ここでの独立再計算はbuild_planet_data.py側の内部一致検査に譲る）。
        has_stance = bool(records) and all('stance' in r for r in records)
        stance_keys = [s['key'] for s in cfg['stances']] if has_stance else []
        for bid, item in items.items():
            element_id = f'bkt-reason-count-{issue["id"]}-{bid}'
            node = verify(element_id, f'{item["count"]:,}件', sc['file'] + ' / ' + '/'.join(sc['path']) + ' / ' + bid)
            label = node.find_previous_sibling('span')
            if label is None or label.get_text(types=None) != item['label']:
                raise ValueError('再読分類のラベルが元記録と一致しません: ' + element_id)
            if not has_stance or bid == '__unread__':
                continue
            # data-bkt-countsはnode（<b>、idで論点まで一意）の祖先<li>にある。
            # data-bkt-reason属性値（バケット文字）は論点をまたいで使い回されるため単独では検索しない。
            expected = {'all': item['count'], **{
                sk: sum(1 for r in records if r['bucket'] == bid and r['stance'] == sk) for sk in stance_keys
            }}
            li = node.find_parent('li')
            try:
                actual_counts = json.loads(li['data-bkt-counts']) if li else None
            except (KeyError, TypeError, ValueError):
                actual_counts = None
            if actual_counts != expected:
                raise ValueError(f'連動表示の理由の立場別内訳が元記録と一致しません: {element_id}')

    path = 'data/verification/bukatsu-chiiki-veins.json'
    for item in read(path)['items']:
        sides = ' ／ '.join(s['stance_label'] + ' ' + str(len(s['representative_posts'])) + '件' for s in item['sides'])
        verify('bkt-concern-count-' + item['id'], f'確認した投稿例: {sides}。確認日 {item["checked_on"]}', path + ' / ' + item['id'])
    path = 'data/verification/bukatsu-chiiki-sunk-continents.json'
    for item in read(path)['items']:
        # 語られていない争点は「issue_bucket」が付いた項目だけ論点の読書面に現れる
        # （沈んだ大陸4件中1件のみが現在タグ付け済み。他3件は編集部推定をせず未タグのまま）。
        if not item.get('issue_bucket'):
            continue
        verify('bkt-source-note-' + item['id'], item['sns_note'], path + ' / ' + item['id'])
    return result
