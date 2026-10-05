#!/usr/bin/env python3
"""収集回ごとの立場・論点の割合を並べた「意見の推移」の節を作る。

「世論の潮目」は前回と今回の2回だけを比べる。こちらは収集した全回を日付順に並べ、
検索で「賛成 反対 割合」「世論 推移」と調べる人が最初に知りたい内訳を、表と折れ線で出す。
立場の変化と論点の変化を切り替えるタブを持つ（潮目と同じ呼び方）。

数字はすべて正典（THEMES.yaml の sample_file と同じ形の分類済みJSON）から計算する。
文章中の数字・増減・「ぶれの範囲」の判定も同じ計算結果から作るので、手で書き換えない。
収集日は fetched_at（UTC）を日本時間に直した日付。更新回のフォルダ名（日本時間）と揃う。

見出し（H2）の末尾と右上のバッジには、最新の収集日を「○年○月○日時点」と出す。更新のたびに自動で変わる。

潮目ウィジェットの枠（TIDE_CARD_START〜END）の中に入れる。潮目は更新のたびに丸ごと
作り直されるため、この節も同じ呼び出しで貼り直す（refresh_adapters 側から render_for を呼ぶ）。
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
TIDE_END = "<!-- TIDE_CARD_END -->"

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
        },
        # スマホの表の見出し用（\n で折り返す）。凡例・ツールチップ・PCの表は正式名を使う。
        "short_labels": {
            "stance": ["減税推進", "条件付き\n賛成", "反対・\n慎重", "中立・\n情報"],
            "issue": ["対象\n範囲", "財源・\n社保", "減税の\n効果", "給付等\n比較", "事業者\n負担", "公約・\n不信"],
        },
    },
}

Z95 = 1.96
WINDOW_DAYS = 7


def _theme_base(slug: str) -> dict:
    from inject_tide_widget import THEMES  # type: ignore[import-not-found]

    return next(item for item in THEMES if item["slug"] == slug)


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


def load_rounds(path: Path, base: dict, kind: str = "stance") -> list[dict]:
    """収集日（日本時間）ごとの件数と、収集の7日前までの投稿の割合を返す。

    kind は "stance"（立場）か "issue"（論点）。割合の分母は、その軸のラベルに入る意見だけ
    （論点の「その他」は潮目と同じく外す）。
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


def note_lines(series: list[dict], labels: list[str], name: str, kind: str = "stance") -> list[str]:
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
        f"各回の意見は{range_text(info)}です。投稿の拾い方に偏りがない場合でも、"
        f"割合には±{info['median_margin']}ポイント前後のぶれが出ます。「ぶれの範囲」はこの目安で判定しています。",
        f"収集日は日本時間です。収集の間隔は{info['gap_min']}〜{info['gap_max']}日で、一定ではありません。",
    ]
    if info["recent_floor"] is not None:
        lines.append(f"各回とも、投稿の{info['recent_floor']}%以上は、収集日の前の{WINDOW_DAYS}日間に書かれたものです。")
    return lines


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
        cells = "".join(f"<td>{pct(item['shares'][label])}</td>" for label in labels)
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
        f"<caption>収集回ごとの{axis}の割合（{unit}）</caption>"
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

    function draw() {
      if (panel.hidden) return;
      const W = Math.max(280, Math.floor(stage.clientWidth));
      const small = W < 520;
      const H = small ? 300 : 340;
      const m = {t: 14, r: small ? 52 : 60, b: 34, l: small ? 38 : 44};
      const pw = W - m.l - m.r, ph = H - m.t - m.b;
      const top = Math.max(10, Math.ceil(Math.max(...data.rounds.flatMap(r => r.v)) / 10) * 10);
      const x0 = days[0], x1 = days[lastIndex];
      const X = i => m.l + (x1 === x0 ? pw / 2 : (days[i] - x0) / (x1 - x0) * pw);
      const Y = v => m.t + ph - v / top * ph;
      stage.querySelector("svg")?.remove();
      const svg = el("svg", {viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": data.aria});
      svg.setAttribute("class", "trend-svg");
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
      const cross = el("line", {y1: m.t, y2: m.t + ph, class: "trend-cross"});
      svg.appendChild(cross);
      const dim = s => data.emph.length > 0 && data.emph.indexOf(s) < 0;
      data.labels.forEach((label, s) => {
        const points = data.rounds.map((r, i) => `${X(i).toFixed(1)},${Y(r.v[s]).toFixed(1)}`).join(" ");
        svg.appendChild(el("polyline", {points, fill: "none", stroke: data.colors[s], "stroke-width": dim(s) ? 2 : (data.emph.length ? 3 : 2), "stroke-opacity": dim(s) ? 0.5 : 1, "stroke-linejoin": "round", "stroke-linecap": "round"}));
      });
      data.labels.forEach((label, s) => {
        data.rounds.forEach((r, i) => {
          const g = el("g", {opacity: dim(s) ? 0.6 : 1});
          g.appendChild(mark(data.shapes[s], X(i), Y(r.v[s]), 5.5, "#fff"));
          g.appendChild(mark(data.shapes[s], X(i), Y(r.v[s]), 3.5, data.colors[s]));
          svg.appendChild(g);
        });
      });
      const ends = data.labels.map((l, s) => ({s, y: Y(data.rounds[lastIndex].v[s])})).sort((a, b) => a.y - b.y);
      for (let k = 1; k < ends.length; k++) if (ends[k].y - ends[k - 1].y < 14) ends[k].y = ends[k - 1].y + 14;
      ends.forEach(e => svg.appendChild(el("text", {x: X(lastIndex) + 12, y: e.y + 4, class: "trend-end"}, data.rounds[lastIndex].v[e.s].toFixed(1) + "%")));
      stage.appendChild(svg);
      geom = {X, W, cross};
      select(active, false);
    }

    function select(i, show) {
      active = i;
      if (!geom) return;
      const r = data.rounds[i];
      geom.cross.setAttribute("x1", geom.X(i));
      geom.cross.setAttribute("x2", geom.X(i));
      geom.cross.style.opacity = show ? 1 : 0;
      tip.hidden = !show;
      if (!show) return;
      tip.textContent = "";
      const head = document.createElement("p");
      head.className = "trend-tip-head";
      head.textContent = jp(r.d) + "の収集分（意見" + r.n + "件）";
      tip.appendChild(head);
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
        tip.appendChild(row);
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
    stage.addEventListener("pointermove", e => geom && select(nearest(e.clientX), true));
    stage.addEventListener("pointerleave", () => select(active, false));
    stage.addEventListener("focus", () => select(active, true));
    stage.addEventListener("blur", () => select(active, false));
    stage.addEventListener("keydown", e => {
      if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
        e.preventDefault();
        select(Math.min(Math.max(active + (e.key === "ArrowRight" ? 1 : -1), 0), lastIndex), true);
      } else if (e.key === "Home" || e.key === "End") {
        e.preventDefault();
        select(e.key === "Home" ? 0 : lastIndex, true);
      }
    });
    return {draw};
  }

  const charts = {};
  const nodes = {};
  root.querySelectorAll("[data-trend-panel]").forEach(panel => {
    const kind = panel.getAttribute("data-trend-panel");
    nodes[kind] = panel;
    if (panels[kind]) charts[kind] = chart(panel, panels[kind]);
  });
  const tabs = root.querySelectorAll("[data-trend-tab]");
  function show(kind) {
    if (!nodes[kind]) return;
    Object.keys(nodes).forEach(k => { nodes[k].hidden = k !== kind; });
    tabs.forEach(t => t.setAttribute("aria-pressed", t.getAttribute("data-trend-tab") === kind ? "true" : "false"));
    if (charts[kind]) charts[kind].draw();
  }
  tabs.forEach(t => t.addEventListener("click", () => show(t.getAttribute("data-trend-tab"))));
  const fromHash = Object.keys(nodes).find(k => location.hash === "#" + nodes[k].id);
  show(fromHash || Object.keys(nodes)[0]);
  let timer = 0;
  window.addEventListener("resize", () => {
    clearTimeout(timer);
    timer = setTimeout(() => Object.keys(nodes).forEach(k => { if (!nodes[k].hidden && charts[k]) charts[k].draw(); }), 120);
  });
})();
"""


def trend_css() -> str:
    return f"""{CSS_START}
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
.trend-legend{{display:flex;flex-wrap:wrap;gap:6px 18px;margin:16px 0 4px;padding:0;list-style:none;color:#26364f;font-size:13px;font-weight:800}}
.trend-legend li{{display:inline-flex;align-items:center;gap:7px}}
.trend-stage{{position:relative;margin-top:6px;outline:none;touch-action:pan-y}}
.trend-stage:focus-visible{{box-shadow:0 0 0 3px #bcd0ff;border-radius:10px}}
.trend-svg{{display:block;max-width:100%;overflow:visible}}
.trend-grid{{stroke:#e4e9f1;stroke-width:1}}
.trend-cross{{stroke:#9aa8bd;stroke-width:1;opacity:0;pointer-events:none}}
.trend-tick{{fill:#66758b;font-size:12px;font-weight:700}}
.trend-end{{fill:#0b1d3a;font-size:13px;font-weight:900}}
.trend-tip{{position:absolute;top:6px;z-index:2;min-width:190px;padding:10px 12px;border:1px solid #d9e2ef;border-radius:12px;background:#fff;box-shadow:0 10px 28px rgba(18,35,64,.16);pointer-events:none;font-size:12px;line-height:1.5}}
.trend-tip[hidden]{{display:none}}
.trend-tip p{{margin:0}}.trend-tip-head{{margin-bottom:5px!important;color:#66758b;font-weight:800}}
.trend-tip-row{{display:flex;align-items:center;gap:8px;padding:1px 0}}
.trend-tip-row i{{width:14px;height:2px;border-radius:2px;flex:none}}
.trend-tip-row b{{min-width:46px;color:#0b1d3a;font-size:14px;font-weight:900}}
.trend-tip-row span{{color:#4b5c74;font-weight:700}}
.trend-table-wrap{{margin-top:18px;overflow-x:auto;border-radius:12px;outline:none}}
.trend-table-wrap:focus-visible{{box-shadow:0 0 0 3px #bcd0ff}}
.trend-table{{width:100%;min-width:560px;border-collapse:collapse;font-size:14px}}
.trend-table caption{{padding:0 0 8px;color:#66758b;font-size:13px;font-weight:800;text-align:left}}
.trend-table th,.trend-table td{{padding:8px 10px;border-top:1px solid #e4e9f1;text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
.trend-table thead th{{border-top:0;border-bottom:1px solid #cdd7e5;color:#4b5c74;font-size:12px;font-weight:900;white-space:normal;vertical-align:bottom}}
.trend-table tbody th{{text-align:left;color:#26364f;font-weight:900}}
.trend-table .is-latest th,.trend-table .is-latest td{{background:#f3f6fb;color:#0b1d3a;font-weight:900}}
.trend-note{{margin:16px 0 0;padding:14px 0 0;border-top:1px solid #e4e9f1;color:#66758b;font-size:12px;line-height:1.75;list-style:none}}
.trend-note li+li{{margin-top:3px}}
.trend-short{{display:none}}
@media(max-width:640px){{.trend-card{{padding:20px 16px;border-radius:16px}}.trend-card h2{{font-size:21px}}.trend-h2-date{{display:block;margin-left:0;margin-top:2px;font-size:.62em}}.trend-lead{{font-size:15px}}.trend-asof{{white-space:normal}}
.trend-full{{display:none}}.trend-short{{display:inline}}
.trend-table-wrap{{overflow-x:visible}}.trend-table{{min-width:0;table-layout:fixed;font-size:12.5px}}
.trend-table th,.trend-table td{{padding:7px 3px}}
.trend-table thead th{{padding:7px 2px;font-size:11px;line-height:1.35}}
.trend-table tbody th{{width:17%}}.trend-table td.col-n{{width:15%}}
.trend-table--wide{{font-size:11.5px}}.trend-table--wide .col-n{{display:none}}.trend-table--wide tbody th{{width:18%}}.trend-table--wide thead th{{font-size:10.5px}}}}
@media print{{.trend-tip{{display:none!important}}}}
{CSS_END}"""


def _panel(slug: str, kind: str, series: list[dict], *, hidden: bool) -> tuple[str, dict]:
    base = _theme_base(slug)
    theme = TREND_THEMES[slug]
    spec = KINDS[kind]
    labels = base[spec["labels_key"]]
    colors, shapes = spec["colors"][: len(labels)], spec["shapes"][: len(labels)]
    # ラベルを増減したのに色・形・短い見出しが追いつかないと、列や線が黙って欠ける。作る前に止める。
    if len(labels) > len(spec["colors"]) or len(theme["short_labels"][kind]) != len(labels):
        raise ValueError(
            f"{slug} の{kind}: ラベル{len(labels)}個に対し、色{len(spec['colors'])}・短い見出し{len(theme['short_labels'][kind])}です。"
            "scripts/build_trend_section.py の KINDS / TREND_THEMES を合わせてください"
        )
    last = series[-1]
    axis = "立場" if kind == "stance" else "論点"
    data = {
        "labels": labels,
        "colors": colors,
        "shapes": shapes,
        "emph": emphasized(series, labels),
        "rounds": [{"d": item["date"], "n": item["n"], "v": [item["shares"][label] for label in labels]} for item in series],
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
    span = range_text(summary(series, labels))
    wrapped = f'<span id="{panel_id}-n-range">{span}</span>'
    notes = "".join(
        f"<li>{html.escape(text).replace(span, wrapped)}</li>"
        for text in note_lines(series, labels, theme["name"], kind)
    )
    hidden_attr = " hidden" if hidden else ""
    markup = f"""  <div class="trend-panel" id="{panel_id}" data-trend-panel="{kind}"{hidden_attr}>
    <h2 id="{panel_id}-title">{html.escape(theme["headings"][kind])}<span class="trend-h2-date">（{jp_date(last["date"], year=True)}時点）</span></h2>
    {lead}
    {_legend(labels, colors, shapes)}
    <div class="trend-stage" data-trend-stage tabindex="0" role="group" aria-label="推移グラフ。左右の矢印キーで収集回を切り替えると、その回の数字が出ます。">
      <div class="trend-tip" data-trend-tip hidden></div>
    </div>
    {_table(series, labels, theme["short_labels"][kind], kind, panel_id)}
    <ul class="trend-note">{notes}</ul>
  </div>"""
    return markup, data


def render_section(slug: str, stance_series: list[dict], issue_series: list[dict] | None = None) -> str:
    if len(stance_series) < 2 or (issue_series is not None and len(issue_series) < 2):
        raise ValueError("推移を出すには2回以上の収集が必要です")
    widget_id = f"{slug}-trend"
    with_tabs = issue_series is not None
    stance_markup, stance_data = _panel(slug, "stance", stance_series, hidden=False)
    panels = {"stance": stance_data}
    markup = [stance_markup]
    if issue_series is not None:
        issue_markup, issue_data = _panel(slug, "issue", issue_series, hidden=True)
        markup.append(issue_markup)
        panels["issue"] = issue_data
    tabs = ""
    if with_tabs:
        buttons = "".join(
            f'<button type="button" class="trend-tab" data-trend-tab="{kind}" aria-controls="{widget_id}-panel-{kind}" '
            f'aria-pressed="{"true" if kind == "stance" else "false"}">{KINDS[kind]["tab"]}</button>'
            for kind in ("stance", "issue")
        )
        tabs = f'  <div class="trend-tabs" role="group" aria-label="推移の見方を切り替え">{buttons}</div>\n'
    script = (
        TREND_JS.replace("__ID__", widget_id)
        .replace("__DATA__", json.dumps(panels, ensure_ascii=False, separators=(",", ":")))
        .replace("__SHAPES__", json.dumps(SHAPE_PATHS, separators=(",", ":")))
    )
    latest = max(stance_series[-1]["date"], issue_series[-1]["date"] if issue_series else "")
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
    """節を TIDE_CARD_END の直前（潮目の枠の中）へ入れる。すでにあれば置き換える。"""
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if pattern.search(page_html):
        page_html = pattern.sub(lambda _m: section, page_html, count=1)
    else:
        if TIDE_END not in page_html:
            raise ValueError("潮目の枠（TIDE_CARD_END）が見つかりません")
        page_html = page_html.replace(TIDE_END, section + "\n" + TIDE_END, 1)
    css_pattern = re.compile(re.escape(CSS_START) + r".*?" + re.escape(CSS_END), re.S)
    if css_pattern.search(page_html):
        return css_pattern.sub(lambda _m: css, page_html, count=1)
    return page_html.replace("</style>", "\n" + css + "\n</style>", 1)


def keep_existing(old_html: str, new_html: str) -> str:
    """作り直す元データが無いとき、古いページにあった節を新しいページへそのまま移す。

    潮目の枠ごと入れ替わる処理で、節が黙って消えないようにするための保険。
    正典が使える通常の更新では render_for で数え直すので、これは使わない。
    """
    found = re.search(re.escape(START) + r".*?" + re.escape(END), old_html, re.S)
    if not found:
        return new_html
    return insert_into_html(new_html, found.group(0), trend_css())


def render_for(slug: str, page_html: str, source: Path) -> str:
    base = _theme_base(slug)
    stance = load_rounds(source, base, "stance")
    issue = load_rounds(source, base, "issue") if base.get("issue_labels") else None
    return insert_into_html(page_html, render_section(slug, stance, issue), trend_css())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True, choices=sorted(TREND_THEMES))
    parser.add_argument("--source", type=Path, help="分類済みJSON（省略時はTHEMES.yamlのsample_file）")
    parser.add_argument("--page", type=Path, help="対象のHTML（省略時はTHEMES.yamlと同じ公開ページ）")
    parser.add_argument("--apply", action="store_true", help="HTMLへ書き込む（付けなければ表だけ表示）")
    args = parser.parse_args()

    import yaml

    base = _theme_base(args.topic)
    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
    source = args.source or ROOT / themes[args.topic]["sample_file"]
    page = args.page or ROOT / base["html"]
    for kind in ("stance", "issue"):
        labels = base[KINDS[kind]["labels_key"]]
        print(f"[{kind}]")
        for item in load_rounds(source, base, kind):
            print(item["date"], item["n"], *(f"{item['shares'][label]:5.1f}" for label in labels))
    if args.apply:
        page.write_text(render_for(args.topic, page.read_text(encoding="utf-8"), source), encoding="utf-8")
        print(f"書き込みました: {page}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
