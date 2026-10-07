#!/usr/bin/env python3
"""収集回ごとの立場・論点の割合を並べた「意見の推移」の節を作る。

「世論の潮目」は前回と今回の2回だけを比べる。こちらは収集した全回を日付順に並べ、
検索で「賛成 反対 割合」「世論 推移」と調べる人が最初に知りたい内訳を、表と折れ線で出す。
立場の変化と論点の変化を切り替えるタブを持つ（潮目と同じ呼び方）。

数字はすべて正典（THEMES.yaml の sample_file と同じ形の分類済みJSON）から計算する。
文章中の数字・増減・「ぶれの範囲」の判定も同じ計算結果から作るので、手で書き換えない。
収集日は fetched_at（UTC）を日本時間に直した日付。更新回のフォルダ名（日本時間）と揃う。

見出し（H2）の末尾と右上のバッジには、最新の収集日を「○年○月○日時点」と出す。更新のたびに自動で変わる。

ページの外枠（`<section class="update-dashboard">`）の中に入れる。枠はページ生成器
（build_consumption_tax_page.py）が作り直しても残し、中の節は更新のたびに adapter が render_for で貼り直す。

2026-10-05 まで、この枠には「世論の潮目」（前回と今回の2回比較）のカードが同居していた。内容が推移と
重なるため、潮目は外して推移に一本化した（前回との比較は previous_sentence と、グラフの「前回→今回」の帯）。
古い形のページを直すには `--drop-tide`（drop_tide_card）を使う。
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

JST = dt.timezone(dt.timedelta(hours=9))
START = "<!-- TREND_CARD_START -->"
END = "<!-- TREND_CARD_END -->"
CSS_START = "/* TREND_CARD_START */"
CSS_END = "/* TREND_CARD_END */"
# 旧形式（潮目カードと同居していた頃）の目印。drop_tide_card だけが使う。
TIDE_START = "<!-- TIDE_CARD_START -->"
TIDE_END = "<!-- TIDE_CARD_END -->"
TIDE_CSS_RE = re.compile(r"/\* TIDE_CARD_START \*/.*?/\* TIDE_CARD_END \*/\n?", re.S)
DASHBOARD_OPEN = '<section class="update-dashboard">'

# 折れ線の端の印。色だけに頼らないよう、系列ごとに違う形を使う。単位パス（半径1）。
SHAPE_PATHS = {
    "circle": None,
    "square": "M-1-1H1V1H-1Z",
    "diamond": "M0-1.35L1.35 0L0 1.35L-1.35 0Z",
    "triangle": "M0-1.3L1.3 1.05L-1.3 1.05Z",
    "triangle-down": "M0 1.3L1.3-1.05L-1.3-1.05Z",
    "plus": "M-.5-1.5H.5V-.5H1.5V.5H.5V1.5H-.5V.5H-1.5V-.5H-.5Z",
}

# 立場: 潮目カードの series-0〜3 と同じ色。灰色の「中立」が色として弱い警告は、
# 形・数値の直接表示・凡例・表で補う（隣の潮目と同じ色であることを優先）。
# 論点: 潮目の論点タブの色（青と紫の差が小さい）は検証に落ちたため、全項目に合格した6色を使う。
KINDS = {
    "stance": {
        "labels_key": "stance_labels",
        "field": "stance",
        "tab": "立場の変化",
        "colors": ["#10b981", "#f59e0b", "#ef476f", "#64748b"],
        "shapes": ["circle", "square", "diamond", "triangle"],
    },
    "issue": {
        "labels_key": "issue_labels",
        "field": "main_issue",
        "tab": "論点の変化",
        "colors": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#4a3aa7"],
        "shapes": ["circle", "square", "diamond", "triangle", "triangle-down", "plus"],
    },
}

# 主な語を見出しに入れるテーマだけここに足す。立場・論点の並びと関連・意見の絞り込みは
# inject_tide_widget.THEMES と同じ定義を使う（潮目と数字がずれないようにするため）。
TREND_THEMES = {
    "consumption-tax-cut": {
        "name": "消費税減税",
        "headings": {
            "stance": "消費税減税の賛成・反対の割合は変わった？",
            "issue": "消費税減税で語られる論点は変わった？",
            "reason": "消費税減税に反対・慎重な投稿は、何を理由に挙げている？",
        },
        # グラフの縦線と「同じ期間にあった出来事」の元。ページの年表と同じ設定ファイル。
        "events_file": "configs/consumption-tax-background.json",
        # 「反対・慎重の理由」タブで内訳を出す立場（inject_tide_widget.THEMES の stance_labels のどれか）。
        "focus_stance": "減税反対・慎重",
        # 立場・論点のグラフを、単体の画像（PNG）としても配る（scripts/build_trend_images.py）。
        "share_images": True,
        # スマホの表の見出し用（\n で折り返す）。凡例・ツールチップ・PCの表は正式名を使う。
        "short_labels": {
            "stance": ["減税推進", "条件付き\n賛成", "反対・\n慎重", "中立・\n情報"],
            "issue": ["対象\n範囲", "財源・\n社保", "減税の\n効果", "給付等\n比較", "事業者\n負担", "公約・\n不信"],
        },
    },
    "bukatsu-chiiki": {
        "name": "部活動の地域移行",
        # 立場・論点の並びは scripts/bukatsu_taxonomy.py（inject_tide_widget.THEMES には無いテーマ）。
        "taxonomy": "bukatsu",
        "headings": {
            "stance": "部活動の地域移行への賛否の割合は変わった？",
            "issue": "部活動の地域移行で語られる論点は変わった？",
        },
        # 「反対・慎重の理由」タブは出さない（ページに、理由の立場別内訳が別にある）。年表の出来事も、
        # 収集期間（2026年6月〜）に入るものが無いので出さない。
        "share_images": True,
        # 集計のしかたが変わる前の回は、同じ尺度で数えていないので並べない（軸ごとの、並べ始める収集日）。
        #  論点: 2026-07-23の回から、収集に使う検索語を7本から10本に増やした（それ以前の2回は7本）。検索語の違いは数え直せない。
        #  立場: 並べ始める日は無い。2026-09-12に賛否の判定基準を見直したが（コミット e81f86b5）、見直し前の回の賛否は
        #        2026-10-06に新しい基準で判定し直した（scripts/rejudge_bukatsu_stance.py。判定し直す前は、
        #        「中立・情報」が約3%から約3割へ跳ねる見かけの動きが出ていた）。
        "series_from": {"issue": "2026-07-23"},
        # 上の事情を、グラフの注意書きに出す（日付つきの固定の文なので、更新で嘘にならない）。
        "series_notes": {
            "stance": [
                "2026年9月12日に、AIが賛否を判定する基準を見直しました。見直し前の回（2026年9月2日まで）は、"
                "2026年10月6日に新しい基準で判定し直しました。賛否は、すべての回を同じ基準・同じAIで判定しています。",
            ],
            "issue": [
                "2026年7月23日の回から、収集に使う検索語を増やしました。それ以前の回は検索語が少なく、拾う投稿の偏りが違うため、"
                "この図は2026年7月23日の回から並べています。",
            ],
        },
        # 分類に使うAIを切り替えた最初の収集日（軸ごと）。回の間の差にAIの違いが混じるので、注意書きに出す。
        # 新しい回でAIが変わると、adapter が止まる（両方の軸に日付を足してから進める）。
        #  立場は、2026-10-01より前の回も同じAIで判定し直したので、この切替の影響を受けない。
        #  論点は、判定し直していないので、2026-10-01の切替の影響が残る。
        "model_breaks": {"stance": [], "issue": ["2026-10-01"]},
        "short_labels": {
            "stance": ["移行\n支持", "条件付き・\n改善要求", "慎重・\n反対", "中立・\n情報"],
            "issue": ["費用・\n家庭負担", "受け皿・\n指導者", "教員の\n働き方", "教育的\n意義・機会", "地域\n格差", "制度・\n移行"],
        },
    },
    "ai-copyright": {
        "name": "生成AIと著作権",
        # 立場・論点の並びは scripts/ai_copyright_taxonomy.py。潮目の定義（inject_tide_widget.THEMES）は
        # 立場が2つ（規制・推進）だけで、ページの内訳（中立・情報を含む3つ）と合わないので使わない。
        "taxonomy": "ai-copyright",
        "headings": {
            "stance": "生成AIと著作権への賛否の割合は変わった？",
            "issue": "生成AIと著作権で語られる論点は変わった？",
        },
        # 立場・論点のグラフを、単体の画像（PNG）としても配る（scripts/build_trend_images.py）。
        "share_images": True,
        # 立場の3ラベル（規制・推進・中立）に、意味の合う色を選ぶ（KINDS["stance"] の位置）。
        #  規制＝赤（ひし形）、推進＝緑（丸）、中立＝灰（三角）。
        "palette": {"stance": [2, 0, 3]},
        # 2026-07-26までの回は、分類のしかたが今と違う。2026-07-12は2D分類（minimax-m2.7）、2026-07-26は
        # 1D分類へ切り替えた回で（themes/ai-copyright.md）、論点・立場の割合が他の回と同じ尺度で並ばない。
        # 2026-08-07に論点定義を単一ソース化した後の最初の回、2026-08-03から並べる。
        "series_from": {"stance": "2026-08-03", "issue": "2026-08-03"},
        "series_notes": {
            "stance": [
                "2026年7月26日までの回は、分類のしかたが今と違うため、この図には並べていません。"
                "2026年9月5日の回は、分類結果の出力の傾向（要約の長さなど）が他の回と違うことを確認しています。"
                "この回の割合は、前後の回と同じ尺度で比べられない可能性があります。",
            ],
            "issue": [
                "2026年7月26日までの回は、分類のしかたが今と違うため、この図には並べていません。"
                "2026年9月5日の回は、分類結果の出力の傾向（要約の長さなど）が他の回と違うことを確認しています。"
                "この回の割合は、前後の回と同じ尺度で比べられない可能性があります。",
            ],
        },
        # 分類に使うAIを切り替えた最初の収集日。2026-09-20は kimi-k2.6、2026-09-29から kimi-k2.7-code。
        # 論点・立場とも判定し直していないので、両方の軸に切替の影響が残る。
        "model_breaks": {"stance": ["2026-09-29"], "issue": ["2026-09-29"]},
        "short_labels": {
            "stance": ["規制\n支持", "推進\n支持", "中立・\n情報"],
            "issue": ["学習\nデータ", "クリエ\nイター", "法制度・\n規制", "技術\n競争", "モラル・\n倫理", "AI生成物\nの権利"],
        },
        # ひと目版の見出し（2項目が並ぶ文）は、論点名が長いと画像の幅に収まらない。文の中だけ短い呼び名にする。
        "headline_labels": {
            "issue": {
                "学習データ・無断利用": "学習データ",
                "クリエイター保護・権利": "クリエイター保護",
                "AI生成物の権利・創作性": "AI生成物の権利",
                "利用者モラル・倫理": "モラル・倫理",
            },
        },
    },
}

REASON_TAB = "反対・慎重の理由"

# 単体で配る画像（scripts/build_trend_images.py が作る）。公開URLは正式ドメイン。
SITE_HOST = "sns-reaction-map.jp"
SITE_URL = f"https://{SITE_HOST}/"
IMAGE_DIR = Path("docs/images/trend")
IMAGE_SIZE = (1200, 675)
EMBED_SIZE = (600, 338)
# 課題77 案5「図表・データの利用条件」。方針変更なのでオーナー（CEO）の承認が要る。承認前は公開しない。
EMBED_TERMS = (
    "出典（SNS反応まっぷ）とリンクを明記すれば、記事・ブログ・授業・SNSで自由に使えます。"
    "画像の切り取りや、数字・注意書きの書き換えはしないでください。"
)
EVENT_DATE_RE = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")

Z95 = 1.96
WINDOW_DAYS = 7


# 画像は貼る場所で使い分ける2種類。ひと目版は、スマホのタイムラインや記事の本文幅（幅300〜600px）に
# 縮めても読めるよう、文字を大きくして線を2本に絞る。詳細版は、資料や数字の根拠の確認向けに全項目を入れる。
IMAGE_VARIANTS = {
    "summary": {
        "name": "ひと目版",
        "use": "記事・Xの投稿・授業のスライド向け",
        "hint": "文字を大きくし、最初と最新で差が大きい2つに絞りました。小さく表示しても読めます。",
    },
    "detail": {
        "name": "詳細版",
        "use": "資料・数字の確認向け",
        "hint": "すべての{noun}と、各回の動きを入れた細かい図です。大きく表示して使ってください。",
    },
}


def image_filename(slug: str, kind: str, variant: str = "detail") -> str:
    """画像検索で何の図か分かるファイル名（テーマ・立場か論点・推移・種類）。"""
    if variant not in IMAGE_VARIANTS:
        raise ValueError(f"画像の種類が不明です: {variant}")
    return f"{slug}-{kind}-trend-{variant}.png"


def page_url(slug: str) -> str:
    return SITE_URL + Path(_theme_base(slug)["html"]).name


def _theme_base(slug: str) -> dict:
    taxonomy = TREND_THEMES.get(slug, {}).get("taxonomy")
    if taxonomy == "bukatsu":
        return _bukatsu_base(slug)
    if taxonomy == "ai-copyright":
        return _ai_copyright_base(slug)
    from inject_tide_widget import THEMES  # type: ignore[import-not-found]

    return next(item for item in THEMES if item["slug"] == slug)


def _ai_copyright_base(slug: str) -> dict:
    """生成AIと著作権は、ページと同じ3立場・論点体系（ai_copyright_taxonomy）から作る。

    立場は「中立・情報」を最後に置く（他のテーマと同じ並び）。論点の「その他」は、ほかのテーマと同じく
    割合から外す。並びは単一ソース（ai_copyright_taxonomy）から導き、ここに別の定義を持たない。
    """
    import yaml
    from ai_copyright_taxonomy import ISSUE_ORDER, OTHER, STANCE_ORDER  # type: ignore[import-not-found]

    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
    neutral = "中立・情報"
    return {
        "slug": slug,
        "html": themes[slug]["html"],
        "use_relevance_filter": True,
        "stance_labels": [label for label in STANCE_ORDER if label != neutral] + [neutral],
        "issue_labels": [label for label in ISSUE_ORDER if label != OTHER],
    }


def palette_for(slug: str, kind: str, count: int) -> tuple[list[str], list[str]]:
    """そのテーマ・軸の、線の色と端の印。TREND_THEMES の palette があれば、その位置の色を使う。

    立場のラベルが少ないテーマ（生成AIと著作権は3つ）で、意味の合う色を選ぶためのもの。
    指定が無いテーマは、従来どおり先頭から count 個。
    """
    spec = KINDS[kind]
    picks = TREND_THEMES[slug].get("palette", {}).get(kind)
    if picks is None:
        return spec["colors"][:count], spec["shapes"][:count]
    if len(picks) != count or any(not 0 <= i < len(spec["colors"]) for i in picks):
        raise ValueError(f"{slug} の{kind}: palette {picks} がラベル数{count}と合いません")
    return [spec["colors"][i] for i in picks], [spec["shapes"][i] for i in picks]


def _bukatsu_base(slug: str) -> dict:
    """部活動の地域移行は潮目の定義（inject_tide_widget.THEMES）を持たないので、論点体系から作る。

    論点の「その他」は、ページの論点カードにも投票にも出さないので、他のテーマと同じく割合から外す。
    """
    import yaml
    from bukatsu_taxonomy import ISSUES, STANCES  # type: ignore[import-not-found]

    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
    return {
        "slug": slug,
        "html": themes[slug]["html"],
        "use_relevance_filter": True,
        "stance_labels": list(STANCES),
        "issue_labels": [label for label in ISSUES if label != "その他"],
    }


def _keep(classification: dict, base: dict) -> bool:
    if base["use_relevance_filter"]:
        return bool(classification.get("is_relevant")) and bool(classification.get("is_opinion"))
    return True


def collected_date(fetched_at: str) -> str:
    stamp = dt.datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
    return stamp.astimezone(JST).date().isoformat()


def posted_at(tweet_id: str) -> dt.datetime | None:
    """Xの投稿IDは時刻を含む。投稿日が必要なとき（収集日との差）だけに使う。"""
    try:
        millis = (int(tweet_id) >> 22) + 1288834974657
    except (TypeError, ValueError):
        return None
    return dt.datetime.fromtimestamp(millis / 1000, JST)


def load_rounds(path: Path, base: dict, kind: str = "stance", since: str | None = None) -> list[dict]:
    """収集日（日本時間）ごとの件数と、収集の7日前までの投稿の割合を返す。

    kind は "stance"（立場）か "issue"（論点）。割合の分母は、その軸のラベルに入る意見だけ
    （論点の「その他」は潮目と同じく外す）。since（ISO日付）を渡すと、その日以降の回だけを返す。
    """
    spec = KINDS[kind]
    rows = json.loads(path.read_text(encoding="utf-8"))
    labels = base[spec["labels_key"]]
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    recent: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in rows:
        classification = row.get("classification", {})
        fetched = row.get("fetched_at")
        if not fetched or not _keep(classification, base):
            continue
        value = classification.get(spec["field"])
        if value not in labels:
            continue
        day = collected_date(fetched)
        if since is not None and day < since:
            continue
        counts[day][value] += 1
        posted = posted_at(row.get("tweet_id", ""))
        if posted is not None:
            collected = dt.datetime.fromisoformat(fetched.replace("Z", "+00:00")).astimezone(JST)
            recent[day][1] += 1
            if (collected - posted).total_seconds() <= WINDOW_DAYS * 86400:
                recent[day][0] += 1
    series = []
    for day in sorted(counts):
        n = sum(counts[day].values())
        within, known = recent[day]
        series.append({
            "date": day,
            "n": n,
            "counts": {label: counts[day].get(label, 0) for label in labels},
            "shares": {label: round(counts[day].get(label, 0) / n * 100, 1) for label in labels},
            "recent_share": (within / known) if known else None,
        })
    return series


def series_start(slug: str, kind: str) -> str | None:
    """その軸で、並べ始める収集日（集計のしかたが変わる前の回は並べない）。無ければ全回を並べる。"""
    return TREND_THEMES[slug].get("series_from", {}).get(kind)


def rounds_for(slug: str, source: Path, kind: str) -> list[dict]:
    """ページ・画像・数字検査が共通で使う、そのテーマの推移の回（並べ始める日を適用ずみ）。"""
    return load_rounds(source, _theme_base(slug), kind, series_start(slug, kind))


def margin(p_percent: float, n: int) -> float:
    p = p_percent / 100
    return Z95 * math.sqrt(p * (1 - p) / n) * 100


def _beyond(count0: int, n0: int, count1: int, n1: int) -> bool:
    p0, p1 = count0 / n0, count1 / n1
    se = math.sqrt(p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1)
    return abs(p1 - p0) > Z95 * se


def beyond_noise(first: dict, last: dict, label: str) -> bool:
    """2つの回の差が、投稿の拾い方に偏りがない場合のぶれ（95%）を超えるか。"""
    return _beyond(first["counts"][label], first["n"], last["counts"][label], last["n"])


def largest_reversal(series: list[dict], label: str) -> tuple[dict, dict, float] | None:
    """全体の向きと逆に動いた、隣り合う2回のうち、ぶれを超えて最も大きいものを返す。"""
    overall = series[-1]["shares"][label] - series[0]["shares"][label]
    best = None
    for a, b in zip(series, series[1:]):
        move = round(b["shares"][label] - a["shares"][label], 1)
        if move * overall >= 0 or not beyond_noise(a, b, label):
            continue
        if best is None or abs(move) > abs(best[2]):
            best = (a, b, move)
    return best


def jp_date(value: str, *, year: bool = False) -> str:
    parsed = dt.date.fromisoformat(value)
    return f"{parsed.year}年{parsed.month}月{parsed.day}日" if year else f"{parsed.month}月{parsed.day}日"


def pct(value: float) -> str:
    return f"{value:.1f}%"


def row_id(panel_id: str, date: str) -> str:
    return f"{panel_id}-row-{date}"


def range_text(info: dict) -> str:
    return f"{info['n_min']}〜{info['n_max']}件"


def subject(kind: str, label: str) -> str:
    """文の主語。論点は「主な論点が〜の投稿」と書き、立場の割合と取り違えないようにする。"""
    return f"「{label}」" if kind == "stance" else f"主な論点が「{label}」の投稿"


def summary(series: list[dict], labels: list[str]) -> dict:
    first, last = series[0], series[-1]
    deltas = {label: round(last["shares"][label] - first["shares"][label], 1) for label in labels}
    movers = sorted(labels, key=lambda label: (-abs(deltas[label]), labels.index(label)))[:2]
    gaps = [
        (dt.date.fromisoformat(b["date"]) - dt.date.fromisoformat(a["date"])).days
        for a, b in zip(series, series[1:])
    ]
    ns = [item["n"] for item in series]
    median_n = int(statistics.median(ns))
    recent_values = [item["recent_share"] for item in series if item["recent_share"] is not None]
    return {
        "first": first, "last": last, "deltas": deltas, "movers": movers,
        "gap_min": min(gaps) if gaps else 0, "gap_max": max(gaps) if gaps else 0,
        "n_min": min(ns), "n_max": max(ns), "median_n": median_n,
        "median_margin": round(margin(50, median_n)),
        "recent_floor": int(math.floor(min(recent_values) * 100)) if recent_values else None,
    }


def glance_lines(kind: str, items: list[dict]) -> list[str]:
    """ひと目版の見出し（1〜2行）。ぶれの範囲を超えた動きだけを「上がった・下がった」と言い切る。

    どちらも超えなければ変化なしと書く。差が小さい項目を、増減があったように見せない。
    items は差が大きい順（label・delta・beyond を持つ）。
    """
    moved = [item for item in items if item["beyond"]]
    prefix = "" if kind == "stance" else "論点では"

    def word(item: dict, connective: bool = False) -> str:
        up = item["delta"] > 0
        return ("上がり" if up else "下がり") if connective else ("上がった" if up else "下がった")

    if not moved:
        axis = "立場" if kind == "stance" else "論点"
        return [f"{axis}の割合に、大きな変化はありません", "（最初と最新の差は、ぶれの範囲内）"]
    if len(moved) == 1:
        return [f"{prefix}「{moved[0]['label']}」の割合が{word(moved[0])}"]
    a, b = moved[:2]
    if (a["delta"] > 0) == (b["delta"] > 0):
        return [f"{prefix}「{a['label']}」と「{b['label']}」の割合が、", f"どちらも{word(a)}"]
    return [f"{prefix}「{a['label']}」の割合が{word(a, True)}、", f"「{b['label']}」が{word(b)}"]


def headline_name(slug: str, kind: str, label: str) -> str:
    """ひと目版の見出しの文に入れる項目名。

    項目名が長いテーマは、TREND_THEMES の headline_labels で、見出しの文の中だけ短くできる
    （2項目が並ぶ文が画像の幅に収まらなくなるのを防ぐ）。グラフの凡例・表・数字の下の名前は正式名のまま。
    """
    return TREND_THEMES[slug].get("headline_labels", {}).get(kind, {}).get(label, label)


def glance(slug: str, kind: str, series: list[dict], labels: list[str]) -> dict:
    """ひと目版の画像に出す内容。最初と最新の差が大きい2項目（本文が取り上げるのと同じ2項目）と、見出しの文。"""
    info = summary(series, labels)
    first, last = info["first"], info["last"]
    items = [
        {
            "label": label,
            "index": labels.index(label),
            "start": first["shares"][label],
            "end": last["shares"][label],
            "start_count": first["counts"][label],
            "end_count": last["counts"][label],
            "delta": info["deltas"][label],
            "beyond": beyond_noise(first, last, label),
        }
        for label in info["movers"]
    ]
    lines = glance_lines(kind, [{**item, "label": headline_name(slug, kind, item["label"])} for item in items])
    return {"items": items, "lines": lines, "headline": "".join(lines), "info": info}


def emphasized(series: list[dict], labels: list[str]) -> list[int]:
    """線が多いとき（5本以上）、ぶれを超えて大きく動いた上位2本だけを濃く見せる。"""
    if len(labels) <= 4:
        return []
    info = summary(series, labels)
    return [labels.index(label) for label in info["movers"] if beyond_noise(info["first"], info["last"], label)]


def lead_paragraphs(series: list[dict], labels: list[str], name: str, kind: str = "stance") -> list[str]:
    info = summary(series, labels)
    first, last = info["first"], info["last"]
    # 冒頭は数字が並ぶ。1文に詰めると80字を超えるので、先頭の1項目と残りの2文に分ける。
    if kind == "stance":
        head, rest = labels[0], labels[1:]
        opening = (
            f"{jp_date(last['date'], year=True)}の収集分では、{name}に関する意見の投稿のうち、"
            f"{head}が{pct(last['shares'][head])}でした。"
            + "、".join(f"{label}は{pct(last['shares'][label])}" for label in rest) + "です。"
        )
    else:
        ranked = sorted(labels, key=lambda label: (-last["shares"][label], labels.index(label)))[:3]
        opening = (
            f"{jp_date(last['date'], year=True)}の収集分では、{name}に関する意見の投稿のうち、"
            f"主な論点が最も多いのは「{ranked[0]}」の{pct(last['shares'][ranked[0]])}でした。"
            f"続いて「{ranked[1]}」が{pct(last['shares'][ranked[1]])}、"
            f"「{ranked[2]}」が{pct(last['shares'][ranked[2]])}です。"
        )
    particle = "は" if kind == "stance" else "は、"
    moves = []
    flags = []
    for label in info["movers"]:
        delta = info["deltas"][label]
        word = "下がり" if delta < 0 else "上がり"
        flags.append(beyond_noise(first, last, label))
        moves.append(
            f"{subject(kind, label)}{particle}{jp_date(first['date'])}の{pct(first['shares'][label])}から"
            f"{pct(last['shares'][label])}へ、{abs(delta):.1f}ポイント{word}ました。"
        )
    if len(set(flags)) == 1:
        # 2つとも同じ判定なら1文にまとめる
        verdict = "ぶれの範囲を超える差です。" if flags[0] else "ぶれの範囲に収まる差です。"
        moves.append(f"どちらも、{verdict}")
    else:
        moves = [m + ("ぶれの範囲を超える差です。" if f else "ぶれの範囲に収まる差です。") for m, f in zip(moves, flags)]
    # 最初と最新だけを比べると一直線の変化に見える。途中で逆向きに動いた回があれば添える。
    swing = ""
    reversal = largest_reversal(series, info["movers"][0])
    if reversal:
        a, b, move = reversal
        word = "下がった" if move < 0 else "上がった"
        swing = (
            f"途中には、{jp_date(a['date'])}から{jp_date(b['date'])}にかけて"
            f"{subject(kind, info['movers'][0])}が{abs(move):.1f}ポイント{word}回もあり、一直線の変化ではありません。"
        )
    return [
        opening,
        f"{jp_date(first['date'])}から{jp_date(last['date'])}までの{len(series)}回の収集を、日付順に並べました。"
        + "".join(moves)
        + swing,
    ]


def previous_sentence(series: list[dict], labels: list[str], kind: str = "stance") -> str | None:
    """直前の回と最新の回を比べた1行。いちばん大きく動いた項目を取り上げ、ぶれの範囲の判定を添える。

    潮目（前回と今回の比較）が見せていた内容を、推移に取り込んだもの。収集が1回だけなら出さない。
    """
    if len(series) < 2:
        return None
    previous, last = series[-2], series[-1]
    deltas = {label: round(last["shares"][label] - previous["shares"][label], 1) for label in labels}
    label = max(labels, key=lambda name: (abs(deltas[name]), -labels.index(name)))
    delta = deltas[label]
    verdict = "ぶれの範囲を超える差です。" if beyond_noise(previous, last, label) else "ぶれの範囲に収まる差です。"
    if delta == 0:
        return f"前回（{jp_date(previous['date'])}）から今回（{jp_date(last['date'])}）にかけて、どの項目の割合も変わりませんでした。"
    word = "下がり" if delta < 0 else "上がり"
    particle = "は" if kind == "stance" else "は、"
    return (
        f"前回（{jp_date(previous['date'])}）から今回（{jp_date(last['date'])}）にかけて、{subject(kind, label)}{particle}"
        f"{pct(previous['shares'][label])}から{pct(last['shares'][label])}へ、{abs(delta):.1f}ポイント{word}ました。{verdict}"
    )


def model_break_notes(slug: str, series: list[dict], kind: str) -> list[str]:
    """分類に使うAIを切り替えた回が、その軸のグラフの中（最初の回より後）にあれば、その注意書き。"""
    first, last = series[0]["date"], series[-1]["date"]
    return [
        f"{jp_date(day, year=True)}の回から、分類に使うAIを切り替えました。それ以前の回との差には、AIの違いも含まれます。"
        for day in TREND_THEMES[slug].get("model_breaks", {}).get(kind, [])
        if first < day <= last
    ]


def note_lines(series: list[dict], labels: list[str], name: str, kind: str = "stance", extra: list[str] | None = None) -> list[str]:
    """グラフの下の注意書き。extra は、そのテーマ・軸だけの事情（集計のしかたの変更など）で、先頭の2文のあとに入れる。"""
    info = summary(series, labels)
    if kind == "stance":
        target = (
            f"集計の対象は、各回で初めて見つかった投稿のうち、{name}について意見を述べた投稿です。"
            "同じ検索語のセットで集め、AIで立場を分類しています。同じ投稿は重ねて数えません。"
        )
    else:
        target = (
            f"集計の対象は、各回で初めて見つかった投稿のうち、{name}について意見を述べた投稿です。"
            "AIが主な論点を1つに分類しています。複数の話題に触れる投稿も、1つにだけ数えます。"
            "「その他」は除いて割合を出しています。同じ投稿は重ねて数えません。"
        )
    lines = [
        target,
        "Xの投稿サンプルの構成比であり、世論調査ではありません。"
        "同じ人の意見が動いたことも、世論全体の変化も示しません。",
        *(extra or []),
        f"各回の意見は{range_text(info)}です。投稿の拾い方に偏りがない場合でも、"
        f"割合には±{info['median_margin']}ポイント前後のぶれが出ます。「ぶれの範囲」はこの目安で判定しています。",
        f"収集日は日本時間です。収集の間隔は{info['gap_min']}〜{info['gap_max']}日で、一定ではありません。",
    ]
    if info["recent_floor"] is not None:
        lines.append(f"各回とも、投稿の{info['recent_floor']}%以上は、収集日の前の{WINDOW_DAYS}日間に書かれたものです。")
    return lines


# ------------------------------------------------------------ 出来事（年表）

def load_events(slug: str) -> list[dict]:
    """ページの年表（設定ファイル）から、日付つきの出来事を読む。日付を読めない行は飛ばす。

    飛ばした行は、数字検査（consumption_tax_count_provenance）が設定ファイルと突き合わせて止める。
    データ更新そのものを、年表の書き方で止めないための分け方。
    """
    path = TREND_THEMES[slug].get("events_file")
    if not path:
        return []
    data = json.loads((ROOT / path).read_text(encoding="utf-8"))
    events = []
    for item in data.get("timeline", []):
        found = EVENT_DATE_RE.fullmatch(str(item.get("date", "")).strip())
        if not found:
            continue
        iso = dt.date(int(found[1]), int(found[2]), int(found[3])).isoformat()
        events.append({
            "id": item["id"], "date": iso, "title": item["title"],
            "links": [(url, label) for url, label in item.get("links", [])],
        })
    return sorted(events, key=lambda event: (event["date"], event["id"]))


def events_in_range(events: list[dict], first: str, last: str) -> list[dict]:
    """グラフの期間（最初の収集日〜最新の収集日）に入る出来事だけ。"""
    return [event for event in events if first <= event["date"] <= last]


def event_moves(series: list[dict], labels: list[str], event_date: str) -> dict | None:
    """出来事の直前の回と直後の回を比べ、ぶれを超えて動いたものを返す。

    直前＝出来事の日より前で最後の回、直後＝出来事の日以後で最初の回。
    収集日が出来事と同じ日なら、その回は「直後」に数える（グラフのツールチップと同じ規則）。
    """
    before = [item for item in series if item["date"] < event_date]
    after = [item for item in series if item["date"] >= event_date]
    if not before or not after:
        return None
    a, b = before[-1], after[0]
    moved = []
    for label in labels:
        delta = round(b["shares"][label] - a["shares"][label], 1)
        if delta != 0 and beyond_noise(a, b, label):
            moved.append((label, delta))
    moved.sort(key=lambda pair: (-abs(pair[1]), labels.index(pair[0])))
    gap = (dt.date.fromisoformat(b["date"]) - dt.date.fromisoformat(a["date"])).days
    return {"before": a, "after": b, "gap": gap, "moved": moved[:3]}


def event_sentences(moves: dict, kind: str) -> list[str]:
    """出来事の前後の動きを、事実だけで書く。原因は書かない。"""
    a, b = moves["before"], moves["after"]
    out = [f"直後の{jp_date(b['date'])}の回を、直前の{jp_date(a['date'])}の回と比べました。"]
    if not moves["moved"]:
        out.append("ぶれの範囲を超える動きはありませんでした。")
    else:
        prefix = "主な論点の割合で、" if kind == "issue" else ""
        down = [(label, delta) for label, delta in moves["moved"] if delta < 0]
        up = [(label, delta) for label, delta in moves["moved"] if delta > 0]
        for verb, group in (("下がった", down), ("上がった", up)):
            if group:
                out.append(f"{prefix}{verb}のは" + "と".join(f"「{label}」の{abs(delta):.1f}ポイント" for label, delta in group) + "です。")
                prefix = ""
        out.append("この差はぶれの範囲を超えています。" if len(moves["moved"]) == 1 else "どれもぶれの範囲を超える差です。")
    out.append(f"回の間隔は{moves['gap']}日あります。")
    return out


def event_id(panel_id: str, event: dict) -> str:
    return f"{panel_id}-event-{event['id']}"


def _events_block(panel_id: str, kind: str, series: list[dict], labels: list[str], events: list[dict]) -> str:
    if not events:
        return ""
    items = []
    for number, event in enumerate(events, start=1):
        sources = "".join(
            f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">{html.escape(label)}</a>'
            for url, label in event["links"]
        )
        source = f'<p class="trend-event-src">一次資料: {sources}</p>' if sources else ""
        moves = event_moves(series, labels, event["date"])
        text = "".join(event_sentences(moves, kind)) if moves else ""
        moves_html = f'<p class="trend-event-moves">{html.escape(text)}</p>' if text else ""
        items.append(
            f'<li class="trend-event" id="{event_id(panel_id, event)}">'
            f'<span class="trend-event-badge" aria-hidden="true">{number}</span>'
            f'<div><p class="trend-event-head"><b>{jp_date(event["date"])}</b> {html.escape(event["title"])}</p>'
            f"{source}{moves_html}</div></li>"
        )
    return (
        '<div class="trend-events">'
        "<h3>同じ期間にあった出来事</h3>"
        '<p class="trend-events-note">グラフの縦線の番号と対応します。年表に載せた出来事だけです。'
        "出来事が原因だと示すものではありません。</p>"
        f'<ol class="trend-event-list">{"".join(items)}</ol></div>'
    )


# ------------------------------------------------------------ 反対・慎重の理由（論点の内訳）

def _half_up(value: float) -> int:
    return int(value + 0.5)


def load_reasons(path: Path, base: dict, stance_label: str) -> dict:
    """ある立場の投稿が、どの論点を主に語っているか。全収集回を合わせた内訳と、回ごとの幅。"""
    rows = json.loads(path.read_text(encoding="utf-8"))
    issues = base["issue_labels"]
    per_round: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        classification = row.get("classification", {})
        fetched = row.get("fetched_at")
        if not fetched or not _keep(classification, base):
            continue
        if classification.get("stance") != stance_label or classification.get("main_issue") not in issues:
            continue
        per_round[collected_date(fetched)][classification["main_issue"]] += 1
    days = sorted(per_round)
    totals = {label: sum(per_round[day].get(label, 0) for day in days) for label in issues}
    n = sum(totals.values())
    round_n = [sum(per_round[day].values()) for day in days]
    items = []
    for label in sorted(issues, key=lambda name: (-totals[name], issues.index(name))):
        shares = [per_round[day].get(label, 0) / sum(per_round[day].values()) * 100 for day in days]
        items.append({
            "label": label, "count": totals[label], "share": round(totals[label] / n * 100, 1),
            "lo": _half_up(min(shares)), "hi": _half_up(max(shares)),
        })
    return {
        "stance": stance_label, "n": n, "rounds": len(days),
        "first": days[0], "last": days[-1],
        "n_min": min(round_n), "n_max": max(round_n),
        "median_margin": round(margin(50, int(statistics.median(round_n)))),
        "items": items,
    }


def _wrap_once(text: str, fragment: str, element_id: str) -> str:
    """文中の1か所だけを、数字検査が照合できる目印（span）で包む。"""
    return html.escape(text).replace(html.escape(fragment), f'<span id="{element_id}">{html.escape(fragment)}</span>', 1)


def reason_paragraphs(info: dict, name: str) -> list[tuple[str, tuple[str, str] | None]]:
    """（文章, 目印で包む断片とid）の並び。"""
    top = info["items"][:3]
    lo_hi = f"{top[0]['lo']}〜{top[0]['hi']}%"
    total = f"{info['n']}件"
    spread = f"{info['n_min']}〜{info['n_max']}件"
    return [
        (f"{jp_date(info['first'])}から{jp_date(info['last'])}までの{info['rounds']}回の収集で、{name}について立場が「{info['stance']}」の投稿は{total}ありました。"
         f"主な論点は、「{top[0]['label']}」が{pct(top[0]['share'])}、「{top[1]['label']}」が{pct(top[1]['share'])}、"
         f"「{top[2]['label']}」が{pct(top[2]['share'])}でした。", (total, "total")),
        (f"回ごとの割合は、「{top[0]['label']}」で{lo_hi}の間を動いています。"
         f"1回あたりの「{info['stance']}」の投稿は{spread}と少なく、ぶれが大きいため、全期間でまとめました。", (spread, "n-range-lead")),
    ]


def reason_notes(info: dict, name: str) -> list[tuple[str, tuple[str, str] | None]]:
    spread = f"{info['n_min']}〜{info['n_max']}件"
    return [
        (f"集計の対象は、各回で初めて見つかった投稿のうち、{name}について立場が「{info['stance']}」の投稿です。"
         "AIが立場と主な論点を分類しています。「その他」は除いて割合を出しています。", None),
        ("Xの投稿サンプルの構成比であり、世論調査ではありません。"
         "同じ人の意見が動いたことも、世論全体の変化も示しません。", None),
        ("論点は話題の分類で、賛否の理由そのものではありません。"
         "論点ごとの理由は、ページ上の論点別の解説で確かめられます。", None),
        (f"1回あたりの「{info['stance']}」の投稿は{spread}です。割合には±{info['median_margin']}ポイント前後のぶれが出ます。"
         "「回ごとの幅」は、各回の割合の最小と最大です。", (spread, "n-range-note")),
        ("収集日は日本時間です。", None),
    ]


def reason_row_id(panel_id: str, index: int) -> str:
    return f"{panel_id}-row-{index}"


def _reason_table(info: dict, panel_id: str) -> str:
    body = "".join(
        f'<tr id="{reason_row_id(panel_id, index)}"><th scope="row">{html.escape(item["label"])}</th>'
        f'<td>{item["count"]}件</td>'
        f'<td class="trend-bar-cell"><span class="trend-bar" style="width:{item["share"]}%"></span><b>{pct(item["share"])}</b></td>'
        f'<td>{item["lo"]}〜{item["hi"]}%</td></tr>'
        for index, item in enumerate(info["items"])
    )
    return (
        f'<div class="trend-table-wrap" tabindex="0" role="region" aria-label="{html.escape(info["stance"])}の投稿の論点別の内訳の表">'
        '<table class="trend-table trend-table--reason">'
        f"<caption>{html.escape(info['stance'])}の投稿の主な論点（「その他」を除く、全期間）</caption>"
        '<thead><tr><th scope="col">論点</th><th scope="col">件数</th><th scope="col">割合</th><th scope="col">回ごとの幅</th></tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


# ------------------------------------------------------------ 画像で使う（ダウンロード・埋め込み）

X_HASHTAG = "#SNS反応まっぷ"
X_ICON = (
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 '
    '8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>'
)


def x_post_text(name: str, lines: list[str], when: str) -> str:
    """「Xで投稿する」で開く投稿画面の下書き。見出しの文と、世論調査ではないことを入れる。

    日本語は1字で2字分に数えられ、全体で280字分まで（URLは23字分）。最も長い見出しでも収まる長さにしてある。
    """
    return f"{name}：{''.join(lines)}\nSNS上の意見の推移（{when}時点）。世論調査ではありません。\n{X_HASHTAG}"


def image_alt(slug: str, kind: str, series: list[dict], labels: list[str], variant: str = "detail") -> str:
    """画像の代替テキスト。最新の割合まで書く（画像検索と読み上げに効く）。"""
    last = series[-1]
    when = f"{jp_date(last['date'], year=True)}時点"
    tail = "Xの投稿サンプルの分析で、世論調査ではありません。"
    if variant == "summary":
        info = glance(slug, kind, series, labels)
        moves = "、".join(
            f"{item['label']}は{jp_date(series[0]['date'])}の{pct(item['start'])}から{pct(item['end'])}へ" for item in info["items"]
        )
        return (
            f"{TREND_THEMES[slug]['name']}に関するSNS上の意見の推移の折れ線グラフ（{when}）。{info['headline']}。"
            f"{moves}。{tail}"
        )
    latest = "、".join(f"{label}{pct(last['shares'][label])}" for label in labels)
    return (
        f"{TREND_THEMES[slug]['headings'][kind]} SNS上の意見の推移の折れ線グラフ（{when}）。"
        f"最新の割合は、{latest}。{tail}"
    )


def embed_code(slug: str, kind: str, alt: str, panel_id: str, variant: str = "summary") -> str:
    """他のサイトに貼る埋め込みコード。画像に出典のリンクを付ける。"""
    image_url = SITE_URL + str(IMAGE_DIR.relative_to("docs")) + "/" + image_filename(slug, kind, variant)
    page = page_url(slug)
    width, height = EMBED_SIZE
    return (
        f'<a href="{page}#{panel_id}"><img src="{image_url}" alt="{html.escape(alt, quote=True)}" '
        f'width="{width}" height="{height}" style="max-width:100%;height:auto"></a>\n'
        f'<p>出典：<a href="{page}">SNS反応まっぷ</a>（Xの投稿サンプルの分析。世論調査ではありません）</p>'
    )


def _share_item(slug: str, kind: str, variant: str, series: list[dict], labels: list[str], panel_id: str) -> str:
    spec = IMAGE_VARIANTS[variant]
    relative = str(IMAGE_DIR.relative_to("docs")) + "/" + image_filename(slug, kind, variant)  # ページからの相対パス
    alt = image_alt(slug, kind, series, labels, variant)
    code = embed_code(slug, kind, alt, panel_id, variant)
    width, height = IMAGE_SIZE
    noun = "立場" if kind == "stance" else "論点"
    last = jp_date(series[-1]["date"], year=True)
    return f"""<div class="trend-share-item" data-variant="{variant}">
          <h3 class="trend-share-name">{spec["name"]}<span>{html.escape(spec["use"])}</span></h3>
          <p class="trend-share-hint">{html.escape(spec["hint"].format(noun=noun))}</p>
          <figure class="trend-share-fig">
            <a href="{relative}"><img src="{relative}" width="{width}" height="{height}" loading="lazy" decoding="async" alt="{html.escape(alt, quote=True)}"></a>
            <figcaption>PNG、{width}×{height}。{last}時点の数字で、更新のたびに最新の数字に差し替わります。</figcaption>
          </figure>
          <div class="trend-share-actions">
            <a class="trend-share-btn" href="{relative}" download data-trend-download="{kind}" data-variant="{variant}">画像をダウンロード</a>
            <button type="button" class="trend-share-btn" data-trend-copy="{kind}" data-variant="{variant}">埋め込みコードをコピー</button>
            <span class="trend-share-status" role="status" aria-live="polite"></span>
          </div>
          <textarea class="trend-share-code" readonly rows="5" aria-label="{spec["name"]}の埋め込みコード">{html.escape(code)}</textarea>
        </div>"""


def _share_block(slug: str, kind: str, series: list[dict], labels: list[str], panel_id: str) -> str:
    if not TREND_THEMES[slug].get("share_images"):
        return ""
    items = "\n        ".join(_share_item(slug, kind, variant, series, labels, panel_id) for variant in IMAGE_VARIANTS)
    post = x_post_text(TREND_THEMES[slug]["name"], glance(slug, kind, series, labels)["lines"], jp_date(series[-1]["date"], year=True))
    return f"""<details class="trend-share" open>
      <summary>このグラフを画像で使う</summary>
      <div class="trend-share-body">
        <p class="trend-share-lead">貼る場所に合わせて、2種類の画像があります。</p>
        <div class="trend-share-x">
          <button type="button" class="trend-share-btn trend-share-xbtn" data-trend-x="{kind}" data-share-url="{page_url(slug)}" data-share-panel="{panel_id}" data-share-text="{html.escape(post, quote=True)}">{X_ICON}Xで投稿する</button>
          <span class="trend-share-xnote">投稿画面が開きます。画像は自動では付かないので、下の「画像をダウンロード」で保存して添付してください（おすすめはひと目版です）。</span>
        </div>
        <div class="trend-share-grid">
        {items}
        </div>
        <p class="trend-share-terms">{html.escape(EMBED_TERMS)}</p>
      </div>
    </details>"""


def _shape_svg(shape: str, r: float) -> str:
    path = SHAPE_PATHS[shape]
    if path is None:
        return f'<circle r="{r}"/>'
    return f'<path d="{path}" transform="scale({r})"/>'


def _legend(labels: list[str], colors: list[str], shapes: list[str]) -> str:
    items = []
    for index, label in enumerate(labels):
        items.append(
            f'<li><svg width="26" height="12" viewBox="0 0 26 12" aria-hidden="true">'
            f'<line x1="0" y1="6" x2="26" y2="6" stroke="{colors[index]}" stroke-width="2" stroke-linecap="round"/>'
            f'<g transform="translate(13 6)" fill="{colors[index]}">{_shape_svg(shapes[index], 4.5)}</g></svg>'
            f"<span>{html.escape(label)}</span></li>"
        )
    return f'<ul class="trend-legend" aria-label="凡例">{"".join(items)}</ul>'


def _table(series: list[dict], labels: list[str], short_labels: list[str], kind: str, panel_id: str) -> str:
    wide = len(labels) > 4
    head = "".join(
        f'<th scope="col"><span class="trend-full">{html.escape(label)}</span>'
        f'<span class="trend-short">{html.escape(short).replace(chr(10), "<br>")}</span></th>'
        for label, short in zip(labels, short_labels)
    )
    body = []
    for index, item in enumerate(series):
        cells = "".join(
            f"<td>{pct(item['shares'][label])}<span class=\"trend-c\">（{item['counts'][label]}件）</span></td>" for label in labels
        )
        current = ' class="is-latest"' if index == len(series) - 1 else ""
        # 行のidは scripts/consumption_tax_count_provenance.py が正典と1行ずつ照合するための目印。
        body.append(
            f'<tr id="{row_id(panel_id, item["date"])}"{current}><th scope="row">{jp_date(item["date"])}</th>'
            f'<td class="col-n">{item["n"]}件</td>{cells}</tr>'
        )
    axis = "立場別" if kind == "stance" else "論点別"
    unit = "意見の投稿に占める割合" if kind == "stance" else "「その他」を除く意見の投稿に占める割合"
    return (
        f'<div class="trend-table-wrap" tabindex="0" role="region" aria-label="収集回ごとの{axis}の割合の表">'
        f'<table class="trend-table{" trend-table--wide" if wide else ""}">'
        f"<caption>収集回ごとの{axis}の割合（{unit}）。割合の下のかっこ内は、その{axis[:2]}の投稿の数</caption>"
        f'<thead><tr><th scope="col">収集日</th><th scope="col" class="col-n">意見数</th>{head}</tr></thead>'
        f"<tbody>{''.join(body)}</tbody></table></div>"
    )


TREND_JS = r"""
(() => {
  const root = document.getElementById("__ID__");
  if (!root) return;
  const panels = __DATA__;
  const NS = "http://www.w3.org/2000/svg";
  const SHAPES = __SHAPES__;
  const el = (name, attrs, text) => {
    const node = document.createElementNS(NS, name);
    Object.keys(attrs || {}).forEach(k => node.setAttribute(k, attrs[k]));
    if (text != null) node.textContent = text;
    return node;
  };
  const mark = (shape, cx, cy, r, color) => {
    const path = SHAPES[shape];
    if (!path) return el("circle", {cx, cy, r, fill: color});
    return el("path", {d: path, transform: `translate(${cx} ${cy}) scale(${r})`, fill: color});
  };
  const jp = d => { const [, m, dd] = d.split("-"); return Number(m) + "月" + Number(dd) + "日"; };
  const sh = d => { const [, m, dd] = d.split("-"); return Number(m) + "/" + Number(dd); };

  function chart(panel, data) {
    const stage = panel.querySelector("[data-trend-stage]");
    const tip = panel.querySelector("[data-trend-tip]");
    if (!stage || !tip) return {draw() {}};
    const days = data.rounds.map(r => Date.parse(r.d + "T00:00:00Z") / 86400000);
    const lastIndex = data.rounds.length - 1;
    let active = lastIndex;
    let geom = null;
    // 再生（時間経過の動き）。動きを減らす設定の端末・古いブラウザでは使わず、最初から完成した状態で出す。
    const kind = panel.getAttribute("data-trend-panel");
    const playBtn = panel.querySelector("[data-trend-play]");
    const reduced = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    const canAnimate = !reduced && lastIndex >= 1 && "IntersectionObserver" in window && typeof requestAnimationFrame === "function";
    let pending = canAnimate;   // 画面に入ったら1回だけ自動で再生する。それまでは、線を描く前の状態で待つ
    let playing = false, frame = 0, shownIndex = -1;
    if (playBtn) playBtn.hidden = !canAnimate;
    const setPlayLabel = on => { if (playBtn) playBtn.textContent = on ? "■ 最後まで表示" : "▶ 変化を再生"; };

    function draw() {
      if (panel.hidden) return;
      stopPlay();
      const W = Math.max(280, Math.floor(stage.clientWidth));
      const small = W < 520;
      const H = small ? 300 : 340;
      const hasCounts = data.rounds.every(r => r.c);
      const m = {t: data.events.length ? 26 : 14, r: (small ? 52 : 60) + (hasCounts ? (small ? 38 : 56) : 0), b: 34, l: small ? 38 : 44};
      const pw = W - m.l - m.r, ph = H - m.t - m.b;
      const top = Math.max(10, Math.ceil(Math.max(...data.rounds.flatMap(r => r.v)) / 10) * 10);
      const x0 = days[0], x1 = days[lastIndex];
      const XD = day => m.l + (x1 === x0 ? pw / 2 : (day - x0) / (x1 - x0) * pw);
      const X = i => XD(days[i]);
      const Y = v => m.t + ph - v / top * ph;
      stage.querySelector("svg")?.remove();
      const svg = el("svg", {viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": data.aria});
      svg.setAttribute("class", "trend-svg");
      // 線・点・帯は、この「窓」の中だけに見える。再生では窓を左から右へ広げる（完成した絵を隠しておいて見せていく）。
      const clipId = panel.id + "-clip";
      const clipRect = el("rect", {x: 0, y: 0, width: W, height: H});
      const defs = el("defs");
      const clip = el("clipPath", {id: clipId});
      clip.appendChild(clipRect);
      defs.appendChild(clip);
      svg.appendChild(defs);
      for (let v = 0; v <= top; v += 10) {
        svg.appendChild(el("line", {x1: m.l, x2: m.l + pw, y1: Y(v), y2: Y(v), class: "trend-grid"}));
        svg.appendChild(el("text", {x: m.l - 8, y: Y(v) + 4, "text-anchor": "end", class: "trend-tick"}, v + "%"));
      }
      const shown = [];
      data.rounds.forEach((r, i) => {
        if (shown.length && X(i) - X(shown[shown.length - 1]) < 46) return;
        shown.push(i);
      });
      if (shown[shown.length - 1] !== lastIndex) {
        while (shown.length > 1 && X(lastIndex) - X(shown[shown.length - 1]) < 46) shown.pop();
        shown.push(lastIndex);
      }
      shown.forEach(i => svg.appendChild(el("text", {x: X(i), y: H - 10, "text-anchor": i === 0 ? "start" : (i === lastIndex ? "end" : "middle"), class: "trend-tick"}, sh(data.rounds[i].d))));
      // 出来事の縦線と番号（下の「同じ期間にあった出来事」の番号と対応）。原因を示すものではない。
      data.events.forEach(e => {
        const ex = XD(Date.parse(e.d + "T00:00:00Z") / 86400000);
        svg.appendChild(el("line", {x1: ex, x2: ex, y1: 14, y2: m.t + ph, class: "trend-event-line"}));
        svg.appendChild(el("circle", {cx: ex, cy: 10, r: 8, class: "trend-event-dot"}));
        svg.appendChild(el("text", {x: ex, y: 13.5, "text-anchor": "middle", class: "trend-event-no"}, String(e.n)));
      });
      const cross = el("line", {y1: m.t, y2: m.t + ph, class: "trend-cross"});
      svg.appendChild(cross);
      const body = el("g", {"clip-path": `url(#${clipId})`});
      // 直前の回から最新の回までの帯（潮目が見せていた「前回→今回」）。収集が3回以上のときだけ。
      if (lastIndex >= 2) {
        const bx = X(lastIndex - 1), bw = X(lastIndex) - bx;
        body.appendChild(el("rect", {x: bx, y: m.t, width: bw, height: ph, class: "trend-band"}));
        body.appendChild(el("text", {x: bx + bw, y: m.t + 11, "text-anchor": "end", class: "trend-band-label"}, "前回→今回"));
      }
      const dim = s => data.emph.length > 0 && data.emph.indexOf(s) < 0;
      data.labels.forEach((label, s) => {
        const points = data.rounds.map((r, i) => `${X(i).toFixed(1)},${Y(r.v[s]).toFixed(1)}`).join(" ");
        body.appendChild(el("polyline", {points, fill: "none", stroke: data.colors[s], "stroke-width": dim(s) ? 2 : (data.emph.length ? 3 : 2), "stroke-opacity": dim(s) ? 0.5 : 1, "stroke-linejoin": "round", "stroke-linecap": "round"}));
      });
      data.labels.forEach((label, s) => {
        data.rounds.forEach((r, i) => {
          const g = el("g", {opacity: dim(s) ? 0.6 : 1});
          g.appendChild(mark(data.shapes[s], X(i), Y(r.v[s]), 5.5, "#fff"));
          g.appendChild(mark(data.shapes[s], X(i), Y(r.v[s]), 3.5, data.colors[s]));
          body.appendChild(g);
        });
      });
      svg.appendChild(body);
      const endsGroup = el("g", {class: "trend-ends"});
      const ends = data.labels.map((l, s) => ({s, y: Y(data.rounds[lastIndex].v[s])})).sort((a, b) => a.y - b.y);
      for (let k = 1; k < ends.length; k++) if (ends[k].y - ends[k - 1].y < 14) ends[k].y = ends[k - 1].y + 14;
      ends.forEach(e => {
        const label = el("text", {x: X(lastIndex) + 12, y: e.y + 4, class: "trend-end"}, data.rounds[lastIndex].v[e.s].toFixed(1) + "%");
        if (hasCounts) label.appendChild(el("tspan", {dx: 5, class: "trend-end-n"}, data.rounds[lastIndex].c[e.s] + "件"));
        endsGroup.appendChild(label);
      });
      svg.appendChild(endsGroup);
      stage.appendChild(svg);
      geom = {X, XD, W, cross, clipRect, endsGroup};
      select(active, false);
      if (pending) {   // 自動再生を待つ間は、線を描く前の状態
        clipRect.setAttribute("width", 0);
        endsGroup.classList.add("is-hidden");
      }
    }

    // 再生: 窓を左（最初の回）から右（最新の回）へ広げる。各回に届くたびに、その回の数字を吹き出しで見せる。
    // 点と点の間の数字は出さない（直線でつないでいるだけで、その間の割合は測っていないため）。
    function play() {
      if (!geom || !canAnimate || panel.hidden) return;
      stopPlay();
      pending = false;
      playing = true;
      shownIndex = -1;
      setPlayLabel(true);
      geom.endsGroup.classList.add("is-hidden");
      const start = performance.now(), sweep = 3200, hold = 900;
      const step = now => {
        const elapsed = now - start;
        const t = Math.min(1, elapsed / sweep);
        const head = days[0] + (days[lastIndex] - days[0]) * (0.5 - Math.cos(Math.PI * t) / 2);
        geom.clipRect.setAttribute("width", geom.XD(head) + 6);
        let passed = 0;
        days.forEach((d, i) => { if (d <= head + 1e-9) passed = i; });
        if (passed !== shownIndex) { shownIndex = passed; select(passed, true, geom.W < 520); }
        if (elapsed < sweep + hold) frame = requestAnimationFrame(step); else finish();
      };
      frame = requestAnimationFrame(step);
    }

    function stopPlay() {
      if (frame) cancelAnimationFrame(frame);
      frame = 0;
      if (playing) { playing = false; setPlayLabel(false); }
    }

    // 最後まで表示する（再生の終わり・「最後まで表示」・キー操作・印刷の前）。
    function finish() {
      pending = false;
      stopPlay();
      if (!geom) return;
      geom.clipRect.setAttribute("width", geom.W);
      geom.endsGroup.classList.remove("is-hidden");
      select(lastIndex, false);
    }

    if (canAnimate) {
      new IntersectionObserver(entries => {
        if (pending && !panel.hidden && entries.some(entry => entry.isIntersecting)) play();
      }, {threshold: 0.35}).observe(stage);
    }
    if (playBtn) {
      playBtn.addEventListener("click", () => {
        if (playing) { finish(); return; }
        play();
        track("trend_play", kind);
      });
    }

    function select(i, show, compact) {
      active = i;
      if (!geom) return;
      const r = data.rounds[i];
      geom.cross.setAttribute("x1", geom.X(i));
      geom.cross.setAttribute("x2", geom.X(i));
      geom.cross.style.opacity = show ? 1 : 0;
      tip.hidden = !show;
      if (!show) return;
      tip.textContent = "";
      tip.classList.toggle("is-compact", !!compact);   // 狭い画面の再生中は、日付と意見数だけの小さな表示（グラフを覆わない）
      const head = document.createElement("p");
      head.className = "trend-tip-head";
      head.textContent = jp(r.d) + "の収集分（意見" + r.n + "件）";
      tip.appendChild(head);
      if (compact) {
        const wide = tip.offsetWidth || 150;
        tip.style.left = Math.min(Math.max(geom.X(i) - wide / 2, 0), geom.W - wide) + "px";
        return;
      }
      data.labels.forEach((label, s) => {
        const row = document.createElement("p");
        row.className = "trend-tip-row";
        const key = document.createElement("i");
        key.style.background = data.colors[s];
        const value = document.createElement("b");
        value.textContent = r.v[s].toFixed(1) + "%";
        const name = document.createElement("span");
        name.textContent = label;
        row.append(key, value, name);
        if (r.c) {
          const count = document.createElement("span");
          count.className = "trend-tip-n";
          count.textContent = "（" + r.c[s] + "件）";
          row.appendChild(count);
        }
        tip.appendChild(row);
      });
      // 直前の回のあとから、この回までにあった出来事（日付がこの回と同じ日なら、この回に数える）。
      const before = i > 0 ? days[i - 1] : -Infinity;
      data.events.forEach(e => {
        const day = Date.parse(e.d + "T00:00:00Z") / 86400000;
        if (day > before && day <= days[i]) {
          const note = document.createElement("p");
          note.className = "trend-tip-event";
          note.textContent = "出来事" + e.n + "：" + jp(e.d) + " " + e.t;
          tip.appendChild(note);
        }
      });
      // 縦線の脇に出す。右半分の回は左側、左半分の回は右側へ寄せ、その回の点に重ねない。
      const x = geom.X(i);
      const wide = tip.offsetWidth || 190;
      const left = x > geom.W / 2 ? x - wide - 14 : x + 14;
      tip.style.left = Math.min(Math.max(left, 0), geom.W - wide) + "px";
    }

    function nearest(clientX) {
      const box = stage.getBoundingClientRect();
      const x = clientX - box.left;
      let best = 0, gap = Infinity;
      data.rounds.forEach((r, i) => { const d = Math.abs(geom.X(i) - x); if (d < gap) { gap = d; best = i; } });
      return best;
    }
    stage.addEventListener("pointermove", e => geom && !playing && select(nearest(e.clientX), true));
    stage.addEventListener("pointerleave", () => { if (!playing) select(active, false); });
    stage.addEventListener("focus", () => { if (!playing) select(active, true); });
    stage.addEventListener("blur", () => { if (!playing) select(active, false); });
    stage.addEventListener("keydown", e => {
      if (playing) finish();   // キーを押したら、再生を止めて最後まで表示する
      if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
        e.preventDefault();
        select(Math.min(Math.max(active + (e.key === "ArrowRight" ? 1 : -1), 0), lastIndex), true);
      } else if (e.key === "Home" || e.key === "End") {
        e.preventDefault();
        select(e.key === "Home" ? 0 : lastIndex, true);
      }
    });
    return {draw, finish, replay() { if (!pending) play(); }};
  }

  const charts = {};
  const nodes = {};
  root.querySelectorAll("[data-trend-panel]").forEach(panel => {
    const kind = panel.getAttribute("data-trend-panel");
    nodes[kind] = panel;
    if (panels[kind]) charts[kind] = chart(panel, panels[kind]);
  });
  // 画像のダウンロード・埋め込みコードのコピー（計測つき）。計測が無くても動く。
  const track = (name, kind, variant) => { if (typeof gtag === "function") gtag("event", name, {theme: "__SLUG__", panel: kind, variant: variant}); };
  root.querySelectorAll("[data-trend-copy]").forEach(button => button.addEventListener("click", async () => {
    const item = button.closest(".trend-share-item");
    const area = item.querySelector("textarea");
    const status = item.querySelector(".trend-share-status");
    let ok = false;
    try { await navigator.clipboard.writeText(area.value); ok = true; }
    catch (error) { area.focus(); area.select(); try { ok = document.execCommand("copy"); } catch (inner) { ok = false; } }
    status.textContent = ok ? "コピーしました" : "選択しました。コピーしてください";
    track("trend_image_copy", button.getAttribute("data-trend-copy"), button.getAttribute("data-variant"));
  }));
  // 「Xで投稿する」。共有URLのUTMとクリック計測は、サイト共通の window.buildShareUrl / trackShareClick（topic-modern.js）を通す。
  root.querySelectorAll("[data-trend-x]").forEach(button => button.addEventListener("click", () => {
    const base = button.getAttribute("data-share-url");
    const build = typeof window.buildShareUrl === "function" ? window.buildShareUrl : (u, c) => u + (u.indexOf("?") === -1 ? "?" : "&") + "utm_source=share_button&utm_medium=social&utm_campaign=" + c;
    const url = build(base, "trend_share") + "#" + button.getAttribute("data-share-panel");
    window.open("https://x.com/intent/tweet?text=" + encodeURIComponent(button.getAttribute("data-share-text")) + "&url=" + encodeURIComponent(url), "_blank", "noopener");
    if (typeof window.trackShareClick === "function") window.trackShareClick("trend_share");
    track("trend_x_post", button.getAttribute("data-trend-x"));
  }));
  root.querySelectorAll("[data-trend-download]").forEach(link => link.addEventListener("click", () => track("trend_image_download", link.getAttribute("data-trend-download"), link.getAttribute("data-variant"))));
  const tabs = root.querySelectorAll("[data-trend-tab]");
  function show(kind) {
    if (!nodes[kind]) return;
    Object.keys(nodes).forEach(k => { nodes[k].hidden = k !== kind; });
    tabs.forEach(t => t.setAttribute("aria-pressed", t.getAttribute("data-trend-tab") === kind ? "true" : "false"));
    if (charts[kind]) { charts[kind].draw(); charts[kind].replay(); }   // タブを切り替えるたびに、もう一度再生する（初回は画面に入ったときに自動で）
  }
  tabs.forEach(t => t.addEventListener("click", () => show(t.getAttribute("data-trend-tab"))));
  const fromHash = Object.keys(nodes).find(k => location.hash === "#" + nodes[k].id);
  show(fromHash || Object.keys(nodes)[0]);
  window.addEventListener("beforeprint", () => Object.keys(charts).forEach(k => charts[k].finish()));
  let timer = 0;
  window.addEventListener("resize", () => {
    clearTimeout(timer);
    timer = setTimeout(() => Object.keys(nodes).forEach(k => { if (!nodes[k].hidden && charts[k]) charts[k].draw(); }), 120);
  });
})();
"""


def trend_css() -> str:
    return f"""{CSS_START}
.update-dashboard{{padding:18px min(4vw,40px) 34px;background:var(--bg)}}
.trend-card{{max-width:1180px;margin:18px auto 0;padding:26px 28px;border:1px solid #d9e2ef;border-radius:20px;background:#fff;box-shadow:0 16px 40px rgba(18,35,64,.09);color:var(--ink)}}
.trend-head{{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:12px}}
.trend-kicker{{display:inline-flex;margin:0;padding:5px 10px;border-radius:999px;background:#eaf1ff;color:#315bd8;font-size:13px;font-weight:900}}
.trend-asof{{display:inline-flex;padding:8px 12px;border-radius:12px;background:#f3f6fb;color:#26364f;font-size:14px;font-weight:900;white-space:nowrap}}
.trend-tabs{{display:flex;gap:6px;width:max-content;max-width:100%;margin:0 0 16px;padding:4px;border-radius:12px;background:#eef3f9}}
.trend-tab{{min-height:38px;padding:8px 14px;border:0;border-radius:9px;background:transparent;color:#53647c;font:inherit;font-size:13px;font-weight:900;cursor:pointer}}
.trend-tab[aria-pressed="true"]{{background:#13223d;color:#fff;box-shadow:0 4px 12px rgba(18,35,64,.15)}}
.trend-panel[hidden]{{display:none}}
.trend-card h2{{margin:0 0 10px;font-size:26px;letter-spacing:-.02em;line-height:1.4}}
.trend-h2-date{{display:inline-block;margin-left:.5em;color:#66758b;font-size:.56em;font-weight:800;letter-spacing:0;white-space:nowrap}}
.trend-lead{{margin:0 0 8px;color:#26364f;font-size:16px;line-height:1.85}}
.trend-legend-row{{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px 16px;margin:16px 0 4px}}
.trend-legend{{display:flex;flex-wrap:wrap;gap:6px 18px;margin:0;padding:0;list-style:none;color:#26364f;font-size:13px;font-weight:800}}
.trend-play{{flex:none;min-height:34px;padding:6px 12px;border:1px solid #d9e2ef;border-radius:999px;background:#fff;color:#315bd8;font:inherit;font-size:13px;font-weight:900;cursor:pointer}}
.trend-play:hover{{background:#eaf1ff}}
.trend-play[hidden]{{display:none}}
.trend-prev{{display:flex;gap:10px;align-items:flex-start;margin:4px 0 0;padding:10px 12px;border-radius:12px;background:#f1f5ff;color:#13223d;font-size:15px;font-weight:800;line-height:1.75}}
.trend-prev-key{{flex:none;width:14px;height:14px;margin-top:6px;border-radius:3px;background:#b8c9f5}}
.trend-band{{fill:#315bd8;fill-opacity:.1;pointer-events:none}}
.trend-band-label{{fill:#315bd8;font-size:10.5px;font-weight:900;paint-order:stroke;stroke:#fff;stroke-width:3px;pointer-events:none}}
.trend-ends{{transition:opacity .4s}}
.trend-ends.is-hidden{{opacity:0}}
.trend-legend li{{display:inline-flex;align-items:center;gap:7px}}
.trend-stage{{position:relative;margin-top:6px;outline:none;touch-action:pan-y}}
.trend-stage:focus-visible{{box-shadow:0 0 0 3px #bcd0ff;border-radius:10px}}
.trend-svg{{display:block;max-width:100%;overflow:visible}}
.trend-grid{{stroke:#e4e9f1;stroke-width:1}}
.trend-cross{{stroke:#9aa8bd;stroke-width:1;opacity:0;pointer-events:none}}
.trend-tick{{fill:#66758b;font-size:12px;font-weight:700}}
.trend-end{{fill:#0b1d3a;font-size:13px;font-weight:900}}
.trend-end-n{{fill:#66758b;font-size:11px;font-weight:700}}
.trend-tip{{position:absolute;top:6px;z-index:2;min-width:190px;padding:10px 12px;border:1px solid #d9e2ef;border-radius:12px;background:#fff;box-shadow:0 10px 28px rgba(18,35,64,.16);pointer-events:none;font-size:12px;line-height:1.5}}
.trend-tip[hidden]{{display:none}}
.trend-tip.is-compact{{min-width:0;padding:6px 10px;white-space:nowrap}}
.trend-tip.is-compact .trend-tip-head{{margin:0!important}}
.trend-tip p{{margin:0}}.trend-tip-head{{margin-bottom:5px!important;color:#66758b;font-weight:800}}
.trend-tip-row{{display:flex;align-items:center;gap:8px;padding:1px 0}}
.trend-tip-row i{{width:14px;height:2px;border-radius:2px;flex:none}}
.trend-tip-row b{{min-width:46px;color:#0b1d3a;font-size:14px;font-weight:900}}
.trend-tip-row span{{color:#4b5c74;font-weight:700}}
.trend-tip-row .trend-tip-n{{margin-left:auto;padding-left:8px;color:#66758b;white-space:nowrap}}
.trend-tip-event{{margin-top:5px!important;padding-top:5px;border-top:1px solid #e4e9f1;color:#26364f;font-weight:800;line-height:1.5}}
.trend-event-line{{stroke:#7b8aa3;stroke-width:1;pointer-events:none}}
.trend-event-dot{{fill:#fff;stroke:#53647c;stroke-width:1.5}}
.trend-event-no{{fill:#26364f;font-size:11px;font-weight:900;pointer-events:none}}
.trend-events{{margin-top:20px}}
.trend-events h3{{margin:0 0 6px;font-size:17px;letter-spacing:-.01em}}
.trend-events-note{{margin:0 0 10px;color:#66758b;font-size:13px;line-height:1.7}}
.trend-event-list{{display:grid;gap:10px;margin:0;padding:0;list-style:none}}
.trend-event{{display:grid;grid-template-columns:24px 1fr;gap:10px;padding:12px 14px;border:1px solid #e1e7f0;border-radius:12px;background:#f9fbfe}}
.trend-event-badge{{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border:1.5px solid #53647c;border-radius:50%;background:#fff;color:#26364f;font-size:12px;font-weight:900}}
.trend-event p{{margin:0}}
.trend-event-head{{color:#0b1d3a;font-size:15px;font-weight:700;line-height:1.6}}
.trend-event-src{{margin-top:2px!important;color:#66758b;font-size:12px;line-height:1.6}}
.trend-event-src a{{color:#315bd8;word-break:break-all}}
.trend-event-moves{{margin-top:6px!important;color:#26364f;font-size:14px;line-height:1.75}}
.trend-table--reason td.trend-bar-cell{{min-width:150px;text-align:left}}
.trend-table--reason thead th:first-child,.trend-table--reason thead th:nth-child(3){{text-align:left}}
.trend-bar{{display:block;height:8px;min-width:2px;margin-bottom:3px;border-radius:0 4px 4px 0;background:#2a78d6}}
.trend-bar-cell b{{color:#0b1d3a;font-size:14px;font-weight:900}}
.trend-share{{margin-top:18px;border:1px solid #e1e7f0;border-radius:12px;background:#f9fbfe}}
.trend-share summary{{padding:12px 16px;color:#26364f;font-size:14px;font-weight:900;cursor:pointer}}
.trend-share-body{{padding:4px 16px 16px}}
.trend-share-lead{{margin:0 0 12px;color:#26364f;font-size:13px;font-weight:700;line-height:1.7}}
.trend-share-x{{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;margin:0 0 14px}}
.trend-share-xbtn{{gap:7px;border-color:#000;background:#000;color:#fff}}
.trend-share-xbtn:hover{{background:#26364f;border-color:#26364f}}
.trend-share-xnote{{flex:1 1 260px;color:#4b5c74;font-size:12.5px;line-height:1.7}}
.trend-share-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}
.trend-share-item{{min-width:0;padding:12px;border:1px solid #e1e7f0;border-radius:10px;background:#fff}}
.trend-share-name{{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 10px;margin:0;font-size:16px;line-height:1.5}}
.trend-share-name span{{color:#53647c;font-size:12px;font-weight:800}}
.trend-share-hint{{margin:4px 0 10px;color:#4b5c74;font-size:12.5px;line-height:1.7}}
.trend-share-fig{{margin:0}}
.trend-share-fig img{{display:block;width:100%;height:auto;border:1px solid #e1e7f0;border-radius:8px;background:#fff}}
.trend-share-fig figcaption{{margin-top:6px;color:#66758b;font-size:12px;line-height:1.7}}
.trend-share-terms{{margin:14px 0 0;color:#26364f;font-size:13px;font-weight:700;line-height:1.7}}
.trend-share-actions{{display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-top:10px}}
.trend-share-btn{{display:inline-flex;align-items:center;min-height:38px;padding:8px 14px;border:1px solid #d9e2ef;border-radius:9px;background:#fff;color:#20314d;font:inherit;font-size:13px;font-weight:900;text-decoration:none;cursor:pointer}}
.trend-share-btn:hover{{background:#f3f6fb}}
.trend-share-status{{color:#047857;font-size:13px;font-weight:800}}
.trend-share-code{{display:block;width:100%;margin-top:10px;padding:10px 12px;border:1px solid #d9e2ef;border-radius:8px;background:#f9fbfe;color:#26364f;font:12px/1.6 ui-monospace,SFMono-Regular,Menlo,monospace;resize:vertical}}
@media(max-width:760px){{.trend-share-grid{{grid-template-columns:minmax(0,1fr)}}}}
.trend-table-wrap{{margin-top:18px;overflow-x:auto;border-radius:12px;outline:none}}
.trend-table-wrap:focus-visible{{box-shadow:0 0 0 3px #bcd0ff}}
.trend-table{{width:100%;min-width:560px;border-collapse:collapse;font-size:14px}}
.trend-table caption{{padding:0 0 8px;color:#66758b;font-size:13px;font-weight:800;text-align:left}}
.trend-table th,.trend-table td{{padding:8px 10px;border-top:1px solid #e4e9f1;text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
.trend-table thead th{{border-top:0;border-bottom:1px solid #cdd7e5;color:#4b5c74;font-size:12px;font-weight:900;white-space:normal;vertical-align:bottom}}
.trend-table tbody th{{text-align:left;color:#26364f;font-weight:900}}
.trend-table .is-latest th,.trend-table .is-latest td{{background:#f3f6fb;color:#0b1d3a;font-weight:900}}
.trend-c{{display:block;margin-top:1px;color:#66758b;font-size:11px;font-weight:700;line-height:1.3}}
.trend-table .is-latest .trend-c{{color:#53647c}}
.trend-note{{margin:16px 0 0;padding:14px 0 0;border-top:1px solid #e4e9f1;color:#66758b;font-size:12px;line-height:1.75;list-style:none}}
.trend-note li+li{{margin-top:3px}}
.trend-short{{display:none}}
@media(max-width:720px){{.update-dashboard{{padding:10px 10px 24px}}}}
@media(max-width:640px){{.trend-card{{padding:20px 16px;border-radius:16px}}.trend-card h2{{font-size:21px}}.trend-h2-date{{display:block;margin-left:0;margin-top:2px;font-size:.62em}}.trend-lead{{font-size:15px}}.trend-asof{{white-space:normal}}
.trend-full{{display:none}}.trend-short{{display:inline}}
.trend-table-wrap{{overflow-x:visible}}.trend-table{{min-width:0;table-layout:fixed;font-size:12.5px}}
.trend-table th,.trend-table td{{padding:7px 3px}}
.trend-table thead th{{padding:7px 2px;font-size:11px;line-height:1.35}}.trend-c{{font-size:10.5px}}
.trend-table tbody th{{width:17%}}.trend-table td.col-n{{width:15%}}
.trend-table--reason{{font-size:12.5px}}.trend-table--reason thead th{{font-size:11px}}.trend-table--reason td.trend-bar-cell{{min-width:0}}
.trend-table--reason tbody th{{width:34%;white-space:normal;line-height:1.4}}.trend-table--reason td:nth-of-type(1){{width:15%}}.trend-table--reason td:nth-of-type(3){{width:17%}}
.trend-event{{padding:11px 12px}}.trend-event-head{{font-size:14px}}.trend-event-moves{{font-size:13px}}
.trend-table--wide{{font-size:11.5px}}.trend-table--wide .trend-c{{font-size:9px;letter-spacing:-.04em}}.trend-table--wide td{{padding-left:1px;padding-right:1px}}.trend-table--wide .col-n{{display:none}}.trend-table--wide tbody th{{width:16%}}.trend-table--wide thead th{{font-size:10.5px}}}}
@media print{{.trend-tip{{display:none!important}}.trend-play{{display:none!important}}}}
@media (prefers-reduced-motion:reduce){{.trend-ends{{transition:none}}}}
{CSS_END}"""


def _panel(slug: str, kind: str, series: list[dict], *, hidden: bool, events: list[dict] | None = None) -> tuple[str, dict]:
    base = _theme_base(slug)
    theme = TREND_THEMES[slug]
    spec = KINDS[kind]
    labels = base[spec["labels_key"]]
    colors, shapes = palette_for(slug, kind, len(labels))
    # ラベルを増減したのに色・形・短い見出しが追いつかないと、列や線が黙って欠ける。作る前に止める。
    if len(labels) > len(spec["colors"]) or len(theme["short_labels"][kind]) != len(labels):
        raise ValueError(
            f"{slug} の{kind}: ラベル{len(labels)}個に対し、色{len(spec['colors'])}・短い見出し{len(theme['short_labels'][kind])}です。"
            "scripts/build_trend_section.py の KINDS / TREND_THEMES を合わせてください"
        )
    last = series[-1]
    axis = "立場" if kind == "stance" else "論点"
    events = events_in_range(events or [], series[0]["date"], last["date"])
    data = {
        "labels": labels,
        "events": [{"d": event["date"], "n": number, "t": event["title"]} for number, event in enumerate(events, start=1)],
        "colors": colors,
        "shapes": shapes,
        "emph": emphasized(series, labels),
        "rounds": [
            {
                "d": item["date"], "n": item["n"],
                "v": [item["shares"][label] for label in labels],
                "c": [item["counts"][label] for label in labels],
            }
            for item in series
        ],
        "aria": (
            f"{jp_date(series[0]['date'])}から{jp_date(last['date'])}までの{len(series)}回の収集について、"
            f"{axis}ごとの割合の推移を示す折れ線グラフです。同じ数字は下の表にあります。"
        ),
    }
    panel_id = f"{slug}-trend-panel-{kind}"
    lead = "".join(
        f'<p class="trend-lead">{html.escape(text)}</p>'
        for text in lead_paragraphs(series, labels, theme["name"], kind)
    )
    previous = previous_sentence(series, labels, kind)
    # 帯の色の見本を先頭に付け、グラフの「前回→今回」の帯と結びつける
    previous_block = (
        f'<p class="trend-prev" id="{panel_id}-prev"><span class="trend-prev-key" aria-hidden="true"></span>{html.escape(previous)}</p>'
        if previous else ""
    )
    span = range_text(summary(series, labels))
    wrapped = f'<span id="{panel_id}-n-range">{span}</span>'
    notes = "".join(
        f"<li>{html.escape(text).replace(span, wrapped)}</li>"
        for text in note_lines(
            series, labels, theme["name"], kind,
            theme.get("series_notes", {}).get(kind, []) + model_break_notes(slug, series, kind),
        )
    )
    hidden_attr = " hidden" if hidden else ""
    markup = f"""  <div class="trend-panel" id="{panel_id}" data-trend-panel="{kind}"{hidden_attr}>
    <h2 id="{panel_id}-title">{html.escape(theme["headings"][kind])}<span class="trend-h2-date">（{jp_date(last["date"], year=True)}時点）</span></h2>
    {lead}
    {previous_block}
    <div class="trend-legend-row">
      {_legend(labels, colors, shapes)}
      <button type="button" class="trend-play" data-trend-play hidden>▶ 変化を再生</button>
    </div>
    <div class="trend-stage" data-trend-stage tabindex="0" role="group" aria-label="推移グラフ。左右の矢印キーで収集回を切り替えると、その回の数字が出ます。">
      <div class="trend-tip" data-trend-tip hidden></div>
    </div>
    {_events_block(panel_id, kind, series, labels, events)}
    {_table(series, labels, theme["short_labels"][kind], kind, panel_id)}
    {_share_block(slug, kind, series, labels, panel_id)}
    <ul class="trend-note">{notes}</ul>
  </div>"""
    return markup, data


def _reason_panel(slug: str, info: dict, *, hidden: bool) -> str:
    theme = TREND_THEMES[slug]
    panel_id = f"{slug}-trend-panel-reason"
    lead = "".join(
        f'<p class="trend-lead">{_wrap_once(text, wrap[0], f"{panel_id}-{wrap[1]}") if wrap else html.escape(text)}</p>'
        for text, wrap in reason_paragraphs(info, theme["name"])
    )
    notes = "".join(
        f"<li>{_wrap_once(text, wrap[0], f'{panel_id}-{wrap[1]}') if wrap else html.escape(text)}</li>"
        for text, wrap in reason_notes(info, theme["name"])
    )
    hidden_attr = " hidden" if hidden else ""
    return f"""  <div class="trend-panel" id="{panel_id}" data-trend-panel="reason"{hidden_attr}>
    <h2 id="{panel_id}-title">{html.escape(theme["headings"]["reason"])}<span class="trend-h2-date">（{jp_date(info["last"], year=True)}時点）</span></h2>
    {lead}
    {_reason_table(info, panel_id)}
    <ul class="trend-note">{notes}</ul>
  </div>"""


def render_section(
    slug: str,
    stance_series: list[dict],
    issue_series: list[dict] | None = None,
    *,
    reason: dict | None = None,
    events: list[dict] | None = None,
) -> str:
    if len(stance_series) < 2 or (issue_series is not None and len(issue_series) < 2):
        raise ValueError("推移を出すには2回以上の収集が必要です")
    widget_id = f"{slug}-trend"
    stance_markup, stance_data = _panel(slug, "stance", stance_series, hidden=False, events=events)
    panels = {"stance": stance_data}
    markup = [stance_markup]
    tab_order = ["stance"]
    if issue_series is not None:
        issue_markup, issue_data = _panel(slug, "issue", issue_series, hidden=True, events=events)
        markup.append(issue_markup)
        panels["issue"] = issue_data
        tab_order.append("issue")
    if reason is not None:
        markup.append(_reason_panel(slug, reason, hidden=True))
        tab_order.append("reason")
    tabs = ""
    if len(tab_order) > 1:
        names = {kind: KINDS[kind]["tab"] for kind in ("stance", "issue")} | {"reason": REASON_TAB}
        buttons = "".join(
            f'<button type="button" class="trend-tab" data-trend-tab="{kind}" aria-controls="{widget_id}-panel-{kind}" '
            f'aria-pressed="{"true" if kind == "stance" else "false"}">{names[kind]}</button>'
            for kind in tab_order
        )
        tabs = f'  <div class="trend-tabs" role="group" aria-label="推移の見方を切り替え">{buttons}</div>\n'
    script = (
        TREND_JS.replace("__ID__", widget_id)
        .replace("__SLUG__", slug)
        .replace("__DATA__", json.dumps(panels, ensure_ascii=False, separators=(",", ":")))
        .replace("__SHAPES__", json.dumps(SHAPE_PATHS, separators=(",", ":")))
    )
    latest = max(stance_series[-1]["date"], issue_series[-1]["date"] if issue_series else "", reason["last"] if reason else "")
    return f"""{START}
<section class="trend-card" id="{widget_id}" aria-label="SNS上の意見の推移">
  <div class="trend-head">
    <p class="trend-kicker">SNS上の意見の推移</p>
    <span class="trend-asof">{jp_date(latest, year=True)}時点</span>
  </div>
{tabs}{chr(10).join(markup)}
  <script>{script}</script>
</section>
{END}"""


def insert_into_html(page_html: str, section: str, css: str) -> str:
    """ページにある推移の節（START〜END）を置き換える。節が無いページには入れない（止める）。

    枠（update-dashboard）はページ生成器が残すので、ここでは中の節だけを差し替える。
    """
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(page_html):
        if TIDE_END in page_html:
            raise ValueError("古い形のページです（潮目カードと同居）。`--drop-tide` で推移だけの形に直してください")
        raise ValueError("意見の推移の枠（update-dashboard）が見つかりません")
    page_html = pattern.sub(lambda _m: section, page_html, count=1)
    css_pattern = re.compile(re.escape(CSS_START) + r".*?" + re.escape(CSS_END), re.S)
    if css_pattern.search(page_html):
        return css_pattern.sub(lambda _m: css, page_html, count=1)
    return page_html.replace("</style>", "\n" + css + "\n</style>", 1)


def drop_tide_card(page_html: str) -> str:
    """古い形のページ（潮目カードと推移が同じ枠にある）から、潮目カードとそのCSSを外す。

    枠は残し、中身を推移だけにする。すでに外してあるページは、そのまま返す（何度流しても同じ）。
    枠の先頭にあった潮目の目印（TIDE_CARD_*）と、枠の見出し用の aria-label も外す。
    """
    if TIDE_END not in page_html:
        return page_html
    start = page_html.index('<section class="update-dashboard"')
    trend_start = page_html.index(START)
    trend_end = page_html.index(END) + len(END)
    close = page_html.index(TIDE_END, trend_end) + len(TIDE_END)
    if not page_html[close:].startswith("</section>"):
        raise ValueError("潮目の枠の終わり（</section>）が見つかりません")
    close += len("</section>")
    dashboard = DASHBOARD_OPEN + page_html[trend_start:trend_end] + "</section>"
    page_html = page_html[:start] + dashboard + page_html[close:]
    return TIDE_CSS_RE.sub("", page_html, count=1)


def keep_existing(old_html: str, new_html: str) -> str:
    """作り直す元データが無いとき、古いページにあった節を新しいページへそのまま移す。

    ページの作り直しで、節が黙って消えないようにするための保険。
    正典が使える通常の更新では render_for で数え直すので、これは使わない。
    """
    found = re.search(re.escape(START) + r".*?" + re.escape(END), old_html, re.S)
    if not found:
        return new_html
    return insert_into_html(new_html, found.group(0), trend_css())


def render_for(slug: str, page_html: str, source: Path) -> str:
    base = _theme_base(slug)
    theme = TREND_THEMES[slug]
    stance = rounds_for(slug, source, "stance")
    issue = rounds_for(slug, source, "issue") if base.get("issue_labels") else None
    focus = theme.get("focus_stance")
    if focus is not None and focus not in base["stance_labels"]:
        raise ValueError(f"{slug}: focus_stance「{focus}」が stance_labels にありません")
    reason = load_reasons(source, base, focus) if focus and issue is not None else None
    events = load_events(slug)
    return insert_into_html(page_html, render_section(slug, stance, issue, reason=reason, events=events), trend_css())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True, choices=sorted(TREND_THEMES))
    parser.add_argument("--source", type=Path, help="分類済みJSON（省略時はTHEMES.yamlのsample_file）")
    parser.add_argument("--page", type=Path, help="対象のHTML（省略時はTHEMES.yamlと同じ公開ページ）")
    parser.add_argument("--apply", action="store_true", help="HTMLへ書き込む（付けなければ表だけ表示）")
    parser.add_argument("--drop-tide", action="store_true", help="古い形のページから、潮目カードを外す（--apply と一緒に使う）")
    args = parser.parse_args()

    import yaml

    base = _theme_base(args.topic)
    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
    source = args.source or ROOT / themes[args.topic]["sample_file"]
    page = args.page or ROOT / base["html"]
    for kind in ("stance", "issue"):
        labels = base[KINDS[kind]["labels_key"]]
        print(f"[{kind}]")
        for item in rounds_for(args.topic, source, kind):
            print(item["date"], item["n"], *(f"{item['shares'][label]:5.1f}" for label in labels))
    if args.apply:
        html = page.read_text(encoding="utf-8")
        if args.drop_tide:
            html = drop_tide_card(html)
        page.write_text(render_for(args.topic, html, source), encoding="utf-8")
        print(f"書き込みました: {page}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
