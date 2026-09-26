"""憲法改正テーマの連動表示に出る再読・資料照合の件数を元記録へ照合する。"""

from collections import Counter
import json
from pathlib import Path

from bs4 import BeautifulSoup
import yaml

from scripts.constitutional_connected import planet_data


def verified_selectors(source: str, root: Path) -> dict[str, str]:
    if '<!-- CONSTITUTIONAL_CONNECTED_START -->' not in source:
        return {}
    soup = BeautifulSoup(source, 'html.parser')
    result: dict[str, str] = {}

    def read(path: str):
        return json.loads((root / path).read_text(encoding='utf-8'))

    def verify_in(container, element_id: str, expected: str, evidence: str):
        nodes = container.select('#' + element_id)
        if len(nodes) != 1 or nodes[0].get_text('', strip=True) != expected:
            raise ValueError(f'連動表示の数字が元記録と一致しません: {element_id} ← {evidence}')
        result['#' + element_id] = evidence
        return nodes[0]

    def verify(element_id: str, expected: str, evidence: str):
        return verify_in(soup, element_id, expected, evidence)

    cfg = yaml.safe_load((root / 'configs/planet/constitutional-amendment.yaml').read_text())
    data = planet_data(source)
    issues = {item['id']: item for item in data['issues']}
    reading_soup = BeautifulSoup(
        ''.join(template.decode_contents() for template in soup.select('template[id^="constitutional-amendment-reading-"]')),
        'html.parser',
    )
    for config_issue in cfg['issues']:
        iid = config_issue['id']
        sc = cfg['sub_issues'].get(config_issue['key'])
        if not sc:
            continue
        raw = read(sc['file'])
        buckets = raw
        for part in sc['path']:
            buckets = buckets[part]
        records = raw
        for part in sc.get('items_path', sc['path'][:-1] + ['items']):
            records = records[part]
        actual = Counter(record['bucket'] for record in records if record.get('main_issue') == config_issue['key'])
        if set(actual) - set(buckets) or any(actual[key] != bucket['count'] for key, bucket in buckets.items()):
            raise ValueError('再読分類の件数と投稿記録が一致しません: ' + iid)

        public_issue = issues[iid]
        expected_items = public_issue['sub']['items']
        if sum(item['count'] for item in expected_items) != public_issue['sub']['reread_count'] + public_issue['sub']['unread_count']:
            raise ValueError('再読表示の小計が公開データと一致しません: ' + iid)
        for item in expected_items:
            element_id = f'ca-reason-count-{iid}-{item["id"]}'
            node = verify_in(reading_soup, element_id, f'{item["count"]:,}件', sc['file'] + ' / ' + item['id'])
            label = node.find_parent('li').select_one('.ca-reason-row > span')
            if label is None or label.get_text('', strip=True) != item['label']:
                raise ValueError('再読分類のラベルが元記録と一致しません: ' + element_id)

    ocean = data['ocean']
    for item in ocean['veins']:
        sides = ' ／ '.join(side['stance_label'] + ' ' + str(side['post_count']) + '件' for side in item['sides'])
        expected = f'確認した投稿例: {sides}。確認日 {item["checked_on"]}'
        for iid in item.get('issue_ids', []):
            verify_in(reading_soup, f'ca-concern-count-{iid}-{item["id"]}', expected, 'PLANET_DATA / ' + item['id'])

    sunk = ocean['sunk_continents']
    source_items = soup.select('#ocean .sunk')
    if len(source_items) != len(sunk):
        raise ValueError('資料3タブへ移す資料項目の件数がPLANET_DATAと一致しません')
    for item, node in zip(sunk, source_items):
        if item['topic'] not in node.get_text(' ', strip=True) or item['sns_note'] not in node.get_text(' ', strip=True):
            raise ValueError('資料3タブへ移す資料の本文が元記録と一致しません: ' + item['id'])
        result['#ocean .sunk:' + item['id']] = 'PLANET_DATA / ocean.sunk_continents'

    return result
