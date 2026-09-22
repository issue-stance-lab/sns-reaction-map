"""連動候補の投票を、公開済みの固定番号とIDで接続する。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r"\(function\(\)\{\n  var TOPIC='consumption-tax-cut-issue-stance-v1';.*?\n\}\)\(\);", re.S)


def registry(data):
    value = json.loads((ROOT / 'configs/consumption-tax-vote-choices.json').read_text())
    for key in ('issues', 'stances'):
        entries = value[key]
        if {e['id'] for e in entries} != {e['id'] for e in data[key]}:
            raise ValueError('投票の固定IDが表示データと一致しません: ' + key)
        if [e['slot'] for e in entries] != list(range(len(entries))):
            raise ValueError('投票の固定番号が連続していません: ' + key)
    if len(value['issues']) != 7 or len(value['stances']) != 4:
        raise ValueError('公開済みの28通りの投票定義を変更できません')
    return value


def apply(source, data):
    value = registry(data)
    match = PATTERN.search(source)
    if not match or len(PATTERN.findall(source)) != 1:
        raise ValueError('消費税の投票処理が1つではありません')

    def rows(name, entries):
        body = re.search(r'var ' + name + r'=\[(.*?)\];', match[0], re.S)[1]
        found = re.findall(r"\{[^{}]*\bk:'([^']+)'[^{}]*\}", body)
        if found != [e['label'] for e in entries]:
            raise ValueError('公開済みの投票の並び・意味が変化しています: ' + name)
        by_label = {e['label']: e for e in entries}

        def add_ids(row):
            item = by_label[re.search(r"\bk:'([^']+)'", row[0])[1]]
            cleaned = re.sub(r"(?:id:'[^']+',\s*|slot:\d+,\s*)", '', row[0][1:])
            return "{id:'" + item['id'] + "',slot:" + str(item['slot']) + ',' + cleaned
        return re.sub(r"\{[^{}]*\bk:'[^']+'[^{}]*\}", add_ids, body).strip()

    code = (ROOT / 'scripts/templates/consumption_tax_connected_vote.js').read_text()
    code = code.replace('__ISSUES__', rows('VOTE_ISSUES', value['issues'])).replace('__STANCES__', rows('STANCES', value['stances']))
    # 保存番号は固定登録簿から生成。表示上の配列位置からは計算しない。
    choices = {i['id']: {s['id']: i['slot'] * 4 + s['slot'] for s in value['stances']} for i in value['issues']}
    code = code.replace('__CHOICES__', json.dumps(choices, ensure_ascii=False, separators=(',', ':')))
    return source[:match.start()] + code.rstrip() + source[match.end():]
