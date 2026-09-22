"""消費税の新しい読書面に出る再読・選定・検索件数を、元記録に照合する。

一般の立場・論点集計とは母集団が違うため、値の許可リストには追加しない。
元記録と完全一致した要素だけを、数字検査へ根拠付きで返す。
"""
from collections import Counter
import json
from pathlib import Path

from bs4 import BeautifulSoup
import yaml


def verified_selectors(source: str, root: Path) -> dict[str, str]:
    if '<!-- TAX_CONNECTED_START -->' not in source:
        return {}
    soup = BeautifulSoup(source, 'html.parser')
    result = {}

    def read(path):
        return json.loads((root / path).read_text())

    def verify(element_id, expected, evidence):
        nodes = soup.select('#' + element_id)
        if len(nodes) != 1 or nodes[0].get_text(types=None) != expected:
            raise ValueError(f'連動表示の数字が元記録と一致しません: {element_id} ← {evidence}')
        result['#' + element_id] = evidence
        return nodes[0]

    cfg = yaml.safe_load((root / 'configs/planet/consumption-tax-cut.yaml').read_text())
    public = read('data/public/themes/consumption-tax-cut.json')
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
        for bid, item in items.items():
            element_id = f'tax-reason-count-{issue["id"]}-{bid}'
            node = verify(element_id, f'{item["count"]:,}件', sc['file'] + ' / ' + '/'.join(sc['path']) + ' / ' + bid)
            label = node.find_previous_sibling('span')
            if label is None or label.get_text(types=None) != item['label']:
                raise ValueError('再読分類のラベルが元記録と一致しません: ' + element_id)

    path = 'data/verification/consumption-tax-cut-veins.json'
    for item in read(path)['items']:
        sides = ' ／ '.join(s['stance_label'] + ' ' + str(len(s['representative_posts'])) + '件' for s in item['sides'])
        verify('tax-concern-count-' + item['id'], f'確認した投稿例: {sides}。確認日 {item["checked_on"]}', path + ' / ' + item['id'])
    path = 'data/verification/consumption-tax-cut-sunk-continents.json'
    for item in read(path)['items']:
        verify('tax-source-note-' + item['id'], item['sns_note'], path + ' / ' + item['id'])
    return result
