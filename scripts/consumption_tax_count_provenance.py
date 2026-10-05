"""消費税の新しい読書面に出る再読・選定・検索件数を、元記録に照合する。

一般の立場・論点集計とは母集団が違うため、値の許可リストには追加しない。
元記録と完全一致した要素だけを、数字検査へ根拠付きで返す。

「意見の推移」の節（scripts/build_trend_section.py）は、表の1行ずつを正典から数え直して照合する。
生成器の計算は使わず、ここで独立に数える。更新のたびに貼り直しが漏れて古い数字が残ると、
ここで止まる（課題90の「潮目だけ古いまま」と同じ事故を防ぐ）。
"""
from collections import Counter, defaultdict
import datetime as dt
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
import yaml


_JST = dt.timezone(dt.timedelta(hours=9))
_TREND_ID = 'consumption-tax-cut-trend'
_FOCUS_STANCE = '減税反対・慎重'  # 「反対・慎重の理由」タブで内訳を出す立場
_EVENT_DATE = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日')
_PANELS = re.compile(r'const panels = (\{.*\});\n\s*const NS', re.S)


def _trend_rounds(root: Path, field: str, labels: list[str],
                  sample_file: Path | None = None) -> dict[str, tuple[int, list[float], list[int]]]:
    """正典から、日本時間の収集日ごとの（意見の件数, 各ラベルの割合, 各ラベルの投稿数）を数え直す。"""
    if sample_file is None:
        themes = yaml.safe_load((root / 'THEMES.yaml').read_text())['themes']
        sample_file = root / themes['consumption-tax-cut']['sample_file']
    rows = json.loads(Path(sample_file).read_text())
    per_day = defaultdict(Counter)
    for row in rows:
        c = row.get('classification') or {}
        if not (c.get('is_relevant') and c.get('is_opinion')) or c.get(field) not in labels:
            continue
        fetched = dt.datetime.fromisoformat(row['fetched_at'].replace('Z', '+00:00'))
        per_day[fetched.astimezone(_JST).date().isoformat()][c[field]] += 1
    result = {}
    for day, counter in per_day.items():
        n = sum(counter.values())
        result[day] = (n, [round(counter[label] / n * 100, 1) for label in labels], [counter[label] for label in labels])
    return result


def _config_events(root: Path) -> list[tuple[str, str, str]]:
    """ページの年表（設定ファイル）から、（ISO日付, id, 題名）を独立に読む。読めない日付は止める。"""
    data = json.loads((root / 'configs/consumption-tax-background.json').read_text())
    events = []
    for item in data['timeline']:
        found = _EVENT_DATE.fullmatch(str(item['date']).strip())
        if not found:
            raise ValueError(f'年表の日付を読めません（推移のグラフに出せません）: {item["id"]} {item["date"]}')
        events.append((dt.date(int(found[1]), int(found[2]), int(found[3])).isoformat(), item['id'], item['title']))
    return sorted(events)


def _reason_recount(root: Path, issues: list[str], sample_file: Path | None = None) -> dict:
    """正典から、注目する立場の投稿が主に語る論点を数え直す（全回の合計と、回ごとの割合の幅）。"""
    if sample_file is None:
        themes = yaml.safe_load((root / 'THEMES.yaml').read_text())['themes']
        sample_file = root / themes['consumption-tax-cut']['sample_file']
    per_day = defaultdict(Counter)
    for row in json.loads(Path(sample_file).read_text()):
        c = row.get('classification') or {}
        if not (c.get('is_relevant') and c.get('is_opinion')):
            continue
        if c.get('stance') != _FOCUS_STANCE or c.get('main_issue') not in issues:
            continue
        fetched = dt.datetime.fromisoformat(row['fetched_at'].replace('Z', '+00:00'))
        per_day[fetched.astimezone(_JST).date().isoformat()][c['main_issue']] += 1
    days = sorted(per_day)
    totals = {label: sum(per_day[d][label] for d in days) for label in issues}
    n = sum(totals.values())
    round_n = [sum(per_day[d].values()) for d in days]
    rows = []
    for label in sorted(issues, key=lambda name: (-totals[name], issues.index(name))):
        shares = [per_day[d][label] / sum(per_day[d].values()) * 100 for d in days]
        rows.append(f'{label}{totals[label]}件{round(totals[label] / n * 100, 1):.1f}%'
                    f'{int(min(shares) + 0.5)}〜{int(max(shares) + 0.5)}%')
    return {'rows': rows, 'total': f'{n}件', 'spread': f'{min(round_n)}〜{max(round_n)}件'}


def private_verified_selectors(source: str, root: Path, *, sample_file: Path | None = None) -> dict[str, str]:
    """推移の節の表の行と「N〜M件」を、非公開正典の数え直しと照合する。

    非公開正典（social-samples/）を読むので、公開CIでは呼ばない。数字検査（verify_number_provenance.py）が
    verified_selectors と合わせて呼ぶ。
    """
    if 'id="' + _TREND_ID + '"' not in source:
        if 'id="consumption-tax-cut-tide-widget"' in source:
            # 潮目はあるのに推移が無い。潮目の貼り直しで枠ごと消えた可能性が高い。
            raise ValueError('「意見の推移」の節がありません（潮目の貼り直しで消えた可能性）')
        return {}
    from inject_tide_widget import THEMES  # 立場・論点の並びの定義だけを使う（計算は使わない）
    base = next(item for item in THEMES if item['slug'] == 'consumption-tax-cut')
    soup = BeautifulSoup(source, 'html.parser')
    result = {}
    for kind, field, key in (('stance', 'stance', 'stance_labels'), ('issue', 'main_issue', 'issue_labels')):
        panel_id = f'{_TREND_ID}-panel-{kind}'
        if not soup.select('#' + panel_id):
            continue
        actual = _trend_rounds(root, field, base[key], sample_file)
        rows = soup.select(f'#{panel_id} tbody tr')
        dates = sorted(actual)
        if [r.get('id') for r in rows] != [f'{panel_id}-row-{d}' for d in dates]:
            raise ValueError(f'推移の表の収集回が正典と一致しません（貼り直し漏れの可能性）: {kind}')
        for row, day in zip(rows, dates):
            n, shares, counts = actual[day]
            _, month, date = day.split('-')
            expected = f'{int(month)}月{int(date)}日{n}件' + ''.join(
                f'{share:.1f}%（{count}件）' for share, count in zip(shares, counts))
            if row.get_text(types=None) != expected:
                raise ValueError(f'推移の表の数字が正典の数え直しと一致しません: {row.get("id")} ← {expected}')
            result['#' + row['id']] = f'THEMES.yaml の sample_file を日本時間の収集日で数え直した{kind}別の件数と割合'
        # グラフ（と、ツールチップ・単体の画像の指紋）が読む埋め込みデータも、同じ数え直しと一致するか。
        # 表だけ合っていて、ツールチップの割合・件数が古いまま残る事故を止める。
        found = _PANELS.search(source)
        if not found:
            raise ValueError('推移のグラフの埋め込みデータが見つかりません')
        shown = json.loads(found.group(1)).get(kind, {}).get('rounds')
        expected_rounds = [{'d': d, 'n': actual[d][0], 'v': actual[d][1], 'c': actual[d][2]} for d in dates]
        if shown != expected_rounds:
            raise ValueError(f'推移のグラフの埋め込みデータ（割合・件数）が正典の数え直しと一致しません: {kind}')
        ns = [actual[d][0] for d in dates]
        span = soup.select('#' + panel_id + '-n-range')
        if len(span) != 1 or span[0].get_text(types=None) != f'{min(ns)}〜{max(ns)}件':
            raise ValueError(f'推移の節の「各回の意見の件数」が正典と一致しません: {kind}')
        result['#' + panel_id + '-n-range'] = '同じ数え直しの最小〜最大'
        # グラフの縦線と「同じ期間にあった出来事」: 年表（設定ファイル）の、グラフの期間に入る分と一致するか。
        first, last = dates[0], dates[-1]
        expected = [(d, i, t) for d, i, t in _config_events(root) if first <= d <= last]
        items = soup.select(f'#{panel_id} li.trend-event')
        if [li.get('id') for li in items] != [f'{panel_id}-event-{i}' for _, i, _ in expected]:
            raise ValueError(f'推移の「同じ期間にあった出来事」が年表と一致しません（貼り直し漏れの可能性）: {kind}')
        for li, (d, i, title) in zip(items, expected):
            _, month, date = d.split('-')
            head = li.select_one('.trend-event-head')
            if head is None or head.get_text(types=None) != f'{int(month)}月{int(date)}日 {title}':
                raise ValueError(f'推移の出来事の日付・題名が年表と一致しません: {li.get("id")}')
            result['#' + li['id']] = f'configs/consumption-tax-background.json の年表（{i}）'
    # 「反対・慎重の理由」タブ: 立場が注目する立場の投稿の、論点ごとの件数・割合・回ごとの幅。
    panel_id = f'{_TREND_ID}-panel-reason'
    if not soup.select('#' + panel_id):
        raise ValueError('「反対・慎重の理由」のタブがありません（貼り直しで消えた可能性）')
    recount = _reason_recount(root, base['issue_labels'], sample_file)
    rows = soup.select(f'#{panel_id} tbody tr')
    if len(rows) != len(recount['rows']):
        raise ValueError('「反対・慎重の理由」の表の行数が正典と一致しません（貼り直し漏れの可能性）')
    for index, (row, expected_text) in enumerate(zip(rows, recount['rows'])):
        if row.get('id') != f'{panel_id}-row-{index}' or row.get_text(types=None) != expected_text:
            raise ValueError(f'「反対・慎重の理由」の表の数字が正典の数え直しと一致しません: {row.get("id")} ← {expected_text}')
        result['#' + row['id']] = f'THEMES.yaml の sample_file で「{_FOCUS_STANCE}」の投稿を論点別に数え直した件数・割合・回ごとの幅'
    for suffix, expected_text in (('total', recount['total']), ('n-range-lead', recount['spread']), ('n-range-note', recount['spread'])):
        found = soup.select(f'#{panel_id}-{suffix}')
        if len(found) != 1 or found[0].get_text(types=None) != expected_text:
            raise ValueError(f'「反対・慎重の理由」の件数（{suffix}）が正典と一致しません: {expected_text}')
        result[f'#{panel_id}-{suffix}'] = '同じ数え直し'
    return result


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
        excluded = raw
        excluded_path = sc.get('excluded_items_path', sc['path'][:-1] + ['excluded_items'])
        try:
            for part in excluded_path:
                excluded = excluded[part]
        except (KeyError, TypeError):
            excluded = []
        actual = Counter(r['bucket'] for r in records)
        if set(actual) - set(buckets) or any(actual[k] != b['count'] for k, b in buckets.items()):
            raise ValueError('再読分類の件数と投稿記録が一致しません: ' + issue['id'])
        items = {k: {'label': b['label'], 'count': actual[k]} for k, b in buckets.items()}
        if excluded:
            items['__excluded__'] = {
                'label': '本文確認で理由分類の対象外とした分',
                'count': len(excluded),
            }
        gap = counts[issue['id']] - len(records) - len(excluded)
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
        evidence = sc['file'] + ' / ' + '/'.join(sc['path'][:-1])
        verify('tax-reason-total-' + issue['id'], f'{counts[issue["id"]]:,}件',
               'data/public/themes/consumption-tax-cut.json / issues / ' + issue['id'])
        verify('tax-reason-reviewed-' + issue['id'], f'{len(records) + len(excluded):,}件', evidence)
        verify('tax-reason-classified-' + issue['id'], f'{len(records):,}件', evidence + ' / items')
        if excluded:
            verify('tax-reason-excluded-' + issue['id'], f'{len(excluded):,}件',
                   evidence + ' / excluded_items')

    path = 'data/verification/consumption-tax-cut-veins.json'
    for item in read(path)['items']:
        sides = ' ／ '.join(s['stance_label'] + ' ' + str(len(s['representative_posts'])) + '件' for s in item['sides'])
        verify('tax-concern-count-' + item['id'], f'確認した投稿例: {sides}。確認日 {item["checked_on"]}', path + ' / ' + item['id'])
    path = 'data/verification/consumption-tax-cut-sunk-continents.json'
    for item in read(path)['items']:
        verify('tax-source-note-' + item['id'], item['sns_note'], path + ' / ' + item['id'])
    return result
