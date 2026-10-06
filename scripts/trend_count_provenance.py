"""「意見の推移」の節（scripts/build_trend_section.py）の数字を、非公開正典の数え直しに照合する。

表の1行ずつ、グラフの埋め込みデータ、前回比の1行、各回の件数の幅、出来事の縦線、
「反対・慎重の理由」の表を、ここで独立に数える。生成器の計算は使わない。
更新のたびに貼り直しが漏れて古い数字が残ると、ここで止まる（課題90の「潮目だけ古いまま」と同じ事故を防ぐ）。

消費税減税（consumption_tax_count_provenance）と部活動の地域移行（bukatsu_count_provenance）が使う。
テーマごとの違い（立場・論点の並び、並べ始める収集日、年表、理由タブ）は SPECS にまとめた。
非公開正典（social-samples/）を読むので、公開CIでは呼ばない。
"""
from collections import Counter, defaultdict
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup
import yaml

# 生成器（build_trend_section）と並びの定義（bukatsu_taxonomy・inject_tide_widget）は、scripts/ の直下から読む。
# パッケージ（scripts.xxx）として読み込まれたときも探せるようにしておく。
_SCRIPTS = str(Path(__file__).resolve().parent)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)


_JST = dt.timezone(dt.timedelta(hours=9))
_EVENT_DATE = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日')
_PANELS = re.compile(r'const panels = (\{.*\});\n\s*const NS', re.S)
_PREVIOUS = re.compile(
    r'前回（(\d+)月(\d+)日）から今回（(\d+)月(\d+)日）にかけて、'
    r'(?:どの項目の割合も変わりませんでした。|(?:主な論点が)?「(.+?)」(?:の投稿)?は、?([\d.]+)%から([\d.]+)%へ、'
    r'([\d.]+)ポイント(上がり|下がり)ました。ぶれの範囲(を超える|に収まる)差です。)')

# テーマごとの違い。ラベルの並びは生成器と同じ定義（計算ではなく並び順だけ）を読む。
SPECS = {
    'consumption-tax-cut': {
        'events_file': 'configs/consumption-tax-background.json',
        'focus_stance': '減税反対・慎重',  # 「反対・慎重の理由」タブで内訳を出す立場
        'returned_tide_id': 'consumption-tax-cut-tide-widget',
        'returned_tide_message': '潮目カードが戻っています。消費税減税は、潮目を外して「意見の推移」に一本化しています',
    },
    'bukatsu-chiiki': {
        'events_file': None,
        'focus_stance': None,
        'returned_tide_id': 'bukatsu-tide-widget',
        'returned_tide_message': '潮目カードが戻っています。部活動の地域移行は、潮目を外して「意見の推移」に一本化しています',
    },
}


def _labels(slug: str) -> dict[str, list[str]]:
    """立場・論点の並び。「その他」は割合の分母に入れない。"""
    if slug == 'bukatsu-chiiki':
        from bukatsu_taxonomy import ISSUES, STANCES
        return {'stance': list(STANCES), 'issue': [label for label in ISSUES if label != 'その他']}
    from inject_tide_widget import THEMES
    base = next(item for item in THEMES if item['slug'] == slug)
    return {'stance': base['stance_labels'], 'issue': base['issue_labels']}


def _series_start(slug: str, kind: str) -> str | None:
    """並べ始める収集日。集計のしかたが変わる前の回は並べない（設定の値を読むだけで、計算は使わない）。"""
    from build_trend_section import TREND_THEMES
    return TREND_THEMES[slug].get('series_from', {}).get(kind)


def _sample_file(root: Path, slug: str, sample_file: Path | None) -> Path:
    if sample_file is not None:
        return Path(sample_file)
    themes = yaml.safe_load((root / 'THEMES.yaml').read_text())['themes']
    return root / themes[slug]['sample_file']


def _trend_rounds(slug: str, root: Path, field: str, labels: list[str], kind: str,
                  sample_file: Path | None = None) -> dict[str, tuple[int, list[float], list[int]]]:
    """正典から、日本時間の収集日ごとの（意見の件数, 各ラベルの割合, 各ラベルの投稿数）を数え直す。"""
    since = _series_start(slug, kind)
    rows = json.loads(_sample_file(root, slug, sample_file).read_text())
    per_day = defaultdict(Counter)
    for row in rows:
        c = row.get('classification') or {}
        if not (c.get('is_relevant') and c.get('is_opinion')) or c.get(field) not in labels:
            continue
        fetched = dt.datetime.fromisoformat(row['fetched_at'].replace('Z', '+00:00'))
        day = fetched.astimezone(_JST).date().isoformat()
        if since is not None and day < since:
            continue
        per_day[day][c[field]] += 1
    result = {}
    for day, counter in per_day.items():
        n = sum(counter.values())
        result[day] = (n, [round(counter[label] / n * 100, 1) for label in labels], [counter[label] for label in labels])
    return result


def _config_events(root: Path, events_file: str | None) -> list[tuple[str, str, str]]:
    """ページの年表（設定ファイル）から、（ISO日付, id, 題名）を独立に読む。読めない日付は止める。"""
    if not events_file:
        return []
    data = json.loads((root / events_file).read_text())
    events = []
    for item in data['timeline']:
        found = _EVENT_DATE.fullmatch(str(item['date']).strip())
        if not found:
            raise ValueError(f'年表の日付を読めません（推移のグラフに出せません）: {item["id"]} {item["date"]}')
        events.append((dt.date(int(found[1]), int(found[2]), int(found[3])).isoformat(), item['id'], item['title']))
    return sorted(events)


def _reason_recount(slug: str, root: Path, issues: list[str], focus_stance: str,
                    sample_file: Path | None = None) -> dict:
    """正典から、注目する立場の投稿が主に語る論点を数え直す（全回の合計と、回ごとの割合の幅）。"""
    per_day = defaultdict(Counter)
    for row in json.loads(_sample_file(root, slug, sample_file).read_text()):
        c = row.get('classification') or {}
        if not (c.get('is_relevant') and c.get('is_opinion')):
            continue
        if c.get('stance') != focus_stance or c.get('main_issue') not in issues:
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


def _check_previous_sentence(soup, panel_id: str, kind: str, labels: list[str], dates: list[str],
                             actual: dict) -> None:
    """推移の冒頭の「前回から今回にかけて…」の1行を、正典の数え直しと照合する。

    直前の回と最新の回の日付、取り上げた項目がいちばん大きく動いた項目であること、前回と今回の割合、
    増減の向きと大きさ、「ぶれの範囲」の判定（95%）を、ここで独立に数え直して突き合わせる。
    """
    node = soup.select_one('#' + panel_id + '-prev')
    if len(dates) < 2:
        if node is not None:
            raise ValueError(f'収集が1回なのに、前回との比較の1行があります: {kind}')
        return
    if node is None:
        raise ValueError(f'推移の冒頭に、前回との比較の1行がありません: {kind}')
    found = _PREVIOUS.fullmatch(node.get_text(types=None))
    if not found:
        raise ValueError(f'前回との比較の1行の形を読めません: {kind}')
    previous_day, last_day = dates[-2], dates[-1]
    shown_days = (f'{int(previous_day[5:7])}月{int(previous_day[8:])}日', f'{int(last_day[5:7])}月{int(last_day[8:])}日')
    if (f'{int(found[1])}月{int(found[2])}日', f'{int(found[3])}月{int(found[4])}日') != shown_days:
        raise ValueError(f'前回との比較の1行の日付が、正典の直前の回・最新の回と一致しません: {kind}')
    (n0, share0, count0), (n1, share1, count1) = (actual[previous_day][0], actual[previous_day][1], actual[previous_day][2]), \
        (actual[last_day][0], actual[last_day][1], actual[last_day][2])
    deltas = [round(b - a, 1) for a, b in zip(share0, share1)]
    top = max(range(len(labels)), key=lambda i: (abs(deltas[i]), -i))
    if found[5] is None:
        if deltas[top] != 0:
            raise ValueError(f'前回との比較の1行は「変わらない」ですが、正典では動いています: {kind}')
        return
    if found[5] != labels[top]:
        raise ValueError(f'前回との比較の1行が、いちばん大きく動いた項目（{labels[top]}）を取り上げていません: {kind}')
    if (float(found[6]), float(found[7])) != (share0[top], share1[top]):
        raise ValueError(f'前回との比較の1行の割合が、正典の数え直しと一致しません: {kind}')
    if float(found[8]) != abs(deltas[top]) or (found[9] == '上がり') != (deltas[top] > 0):
        raise ValueError(f'前回との比較の1行の増減が、正典の数え直しと一致しません: {kind}')
    p0, p1 = count0[top] / n0, count1[top] / n1
    beyond = abs(p1 - p0) > 1.96 * math.sqrt(p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1)
    if (found[10] == 'を超える') != beyond:
        raise ValueError(f'前回との比較の1行の「ぶれの範囲」の判定が、正典の数え直しと一致しません: {kind}')


def private_verified_selectors(slug: str, source: str, root: Path, *, sample_file: Path | None = None) -> dict[str, str]:
    """推移の節の表の行と「N〜M件」を、非公開正典の数え直しと照合する。

    非公開正典（social-samples/）を読むので、公開CIでは呼ばない。数字検査（verify_number_provenance.py）が
    verified_selectors と合わせて呼ぶ。
    """
    spec = SPECS[slug]
    trend_id = f'{slug}-trend'
    if 'id="' + spec['returned_tide_id'] + '"' in source:
        # 2026年10月に潮目カードは外した（前回との比較は推移の冒頭の1行と帯）。古い更新処理や単体スクリプトで戻ってきたら止める。
        raise ValueError(spec['returned_tide_message'])
    if 'id="' + trend_id + '"' not in source:
        if 'class="update-dashboard"' in source:
            # 枠はあるのに推移が無い。ページの作り直しで中身が消えた可能性が高い。
            raise ValueError('「意見の推移」の節がありません（ページの作り直しで消えた可能性）')
        return {}
    labels = _labels(slug)
    soup = BeautifulSoup(source, 'html.parser')
    result = {}
    for kind, field in (('stance', 'stance'), ('issue', 'main_issue')):
        panel_id = f'{trend_id}-panel-{kind}'
        if not soup.select('#' + panel_id):
            continue
        actual = _trend_rounds(slug, root, field, labels[kind], kind, sample_file)
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
        _check_previous_sentence(soup, panel_id, kind, labels[kind], dates, actual)
        ns = [actual[d][0] for d in dates]
        span = soup.select('#' + panel_id + '-n-range')
        if len(span) != 1 or span[0].get_text(types=None) != f'{min(ns)}〜{max(ns)}件':
            raise ValueError(f'推移の節の「各回の意見の件数」が正典と一致しません: {kind}')
        result['#' + panel_id + '-n-range'] = '同じ数え直しの最小〜最大'
        # グラフの縦線と「同じ期間にあった出来事」: 年表（設定ファイル）の、グラフの期間に入る分と一致するか。
        first, last = dates[0], dates[-1]
        expected = [(d, i, t) for d, i, t in _config_events(root, spec['events_file']) if first <= d <= last]
        items = soup.select(f'#{panel_id} li.trend-event')
        if [li.get('id') for li in items] != [f'{panel_id}-event-{i}' for _, i, _ in expected]:
            raise ValueError(f'推移の「同じ期間にあった出来事」が年表と一致しません（貼り直し漏れの可能性）: {kind}')
        for li, (d, i, title) in zip(items, expected):
            _, month, date = d.split('-')
            head = li.select_one('.trend-event-head')
            if head is None or head.get_text(types=None) != f'{int(month)}月{int(date)}日 {title}':
                raise ValueError(f'推移の出来事の日付・題名が年表と一致しません: {li.get("id")}')
            result['#' + li['id']] = f'{spec["events_file"]} の年表（{i}）'
    focus = spec['focus_stance']
    if focus is None:
        # 理由タブを持たないテーマ。生成器が出していないことを確かめる（出ていたら、照合の範囲外の数字が増える）。
        if soup.select(f'#{trend_id}-panel-reason'):
            raise ValueError('理由のタブが出ていますが、このテーマは理由タブを持たない設定です')
        return result
    # 「反対・慎重の理由」タブ: 立場が注目する立場の投稿の、論点ごとの件数・割合・回ごとの幅。
    panel_id = f'{trend_id}-panel-reason'
    if not soup.select('#' + panel_id):
        raise ValueError('「反対・慎重の理由」のタブがありません（貼り直しで消えた可能性）')
    recount = _reason_recount(slug, root, labels['issue'], focus, sample_file)
    rows = soup.select(f'#{panel_id} tbody tr')
    if len(rows) != len(recount['rows']):
        raise ValueError('「反対・慎重の理由」の表の行数が正典と一致しません（貼り直し漏れの可能性）')
    for index, (row, expected_text) in enumerate(zip(rows, recount['rows'])):
        if row.get('id') != f'{panel_id}-row-{index}' or row.get_text(types=None) != expected_text:
            raise ValueError(f'「反対・慎重の理由」の表の数字が正典の数え直しと一致しません: {row.get("id")} ← {expected_text}')
        result['#' + row['id']] = f'THEMES.yaml の sample_file で「{focus}」の投稿を論点別に数え直した件数・割合・回ごとの幅'
    for suffix, expected_text in (('total', recount['total']), ('n-range-lead', recount['spread']), ('n-range-note', recount['spread'])):
        found = soup.select(f'#{panel_id}-{suffix}')
        if len(found) != 1 or found[0].get_text(types=None) != expected_text:
            raise ValueError(f'「反対・慎重の理由」の件数（{suffix}）が正典と一致しません: {expected_text}')
        result[f'#{panel_id}-{suffix}'] = '同じ数え直し'
    return result
