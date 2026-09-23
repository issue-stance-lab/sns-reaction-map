"""生成AIと著作権の読書面に出る再読・共通の心配・語られていない争点の件数を、元記録に照合する。

一般の立場・論点集計とは母集団が違うため、値の許可リストには追加しない。
元記録と完全一致した要素だけを、数字検査へ根拠付きで返す（consumption_tax_count_provenance.py
と同じ設計。ai-copyrightは理由の立場別内訳を持たないため、bukatsu_count_provenance.pyより単純）。
"""
from collections import Counter
import json
from pathlib import Path

from bs4 import BeautifulSoup
import yaml


def verified_selectors(source: str, root: Path) -> dict[str, str]:
    if '<!-- AI_COPYRIGHT_CONNECTED_START -->' not in source:
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

    cfg = yaml.safe_load((root / 'configs/planet/ai-copyright.yaml').read_text())
    public = read('data/public/themes/ai-copyright.json')
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
            element_id = f'aic-reason-count-{issue["id"]}-{bid}'
            node = verify(element_id, f'{item["count"]:,}件', sc['file'] + ' / ' + '/'.join(sc['path']) + ' / ' + bid)
            label = node.find_previous_sibling('span')
            if label is None or label.get_text(types=None) != item['label']:
                raise ValueError('再読分類のラベルが元記録と一致しません: ' + element_id)

    path = 'data/verification/ai-copyright-veins.json'
    for item in read(path)['items']:
        sides = ' ／ '.join(s['stance_label'] + ' ' + str(len(s['representative_posts'])) + '件' for s in item['sides'])
        text = f'確認した投稿例: {sides}。確認日 {item["checked_on"]}'
        # sharedな心配（vein）は複数論点にまたがりうるため、論点ごとに複製されたidを別々に照合する。
        for iid in item['issue_ids']:
            verify(f'aic-concern-count-{iid}-{item["id"]}', text, path + ' / ' + item['id'])
    path = 'data/verification/ai-copyright-sunk-continents.json'
    for item in read(path)['items']:
        verify('aic-source-note-' + item['id'], item['sns_note'], path + ' / ' + item['id'])
    return result
