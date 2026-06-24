#!/usr/bin/env python3
"""Build a constitutional amendment dashboard with hierarchical issue axes."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def esc(value: Any) -> str:
    return html.escape(str(value or ""))


def classification(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("classification") or {}


def category(row: dict[str, Any]) -> str:
    return str(classification(row).get("category") or "未分類")


def stance(row: dict[str, Any]) -> str:
    return str(classification(row).get("stance") or classification(row).get("stance_to_target") or "その他")


def issue(row: dict[str, Any]) -> str:
    return str(classification(row).get("issue") or "不明")


def post_type(row: dict[str, Any]) -> str:
    explicit = str(classification(row).get("post_type") or "")
    if explicit:
        return explicit
    c = category(row)
    text = str(row.get("text") or "")
    if c == "事実確認・情報共有" or "http" in text and len(text) < 140:
        return "情報共有"
    if c == "政党・議員批判":
        return "政党・議員批判"
    if c in {"未確認・過激表現", "その他・分類保留"}:
        return "要確認・保留"
    if "?" in text or "どう" in text or "なぜ" in text:
        return "疑問・問題提起"
    return "意見表明"


def parent_group(row: dict[str, Any]) -> str:
    c = category(row)
    if c in {"改憲賛成・推進", "改憲反対・護憲"}:
        return "改憲全体"
    if c in {"9条・自衛隊明記に賛成", "9条・自衛隊明記に反対"} or issue(row) == "9条・自衛隊":
        return "9条・自衛隊明記"
    if c in {"緊急事態条項に賛成", "緊急事態条項に反対"} or issue(row) == "緊急事態条項":
        return "緊急事態条項"
    if c == "国民投票法・広告規制を重視" or issue(row) == "国民投票法":
        return "国民投票法・広告規制"
    if c in {"政党・議員批判", "手続き・発議可能性への関心"}:
        return "政党・手続き"
    return "保留・注意領域"


def count_rows(rows: list[dict[str, Any]], names: list[str]) -> int:
    allowed = set(names)
    return sum(1 for row in rows if category(row) in allowed)


def card(title: str, count: int, desc: str, tone: str) -> str:
    return f"""
<article class="axis-card {tone}">
  <div class="axis-kicker">{esc(tone_label(tone))}</div>
  <h3>{esc(title)}</h3>
  <div class="axis-count">{count}<span>件</span></div>
  <p>{esc(desc)}</p>
</article>
"""


def tone_label(tone: str) -> str:
    return {
        "positive": "推進側",
        "negative": "慎重・反対側",
        "process": "手続き",
        "warn": "注意",
    }.get(tone, "分類")


def bar_rows(counts: Counter[str], order: list[str]) -> str:
    max_value = max(counts.values(), default=1)
    out = []
    for name in order:
        value = counts.get(name, 0)
        width = round(value / max_value * 100) if max_value else 0
        out.append(
            f'<div class="bar-row"><div class="bar-meta"><span>{esc(name)}</span><strong>{value}</strong></div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div></div>'
        )
    return "".join(out)


def sample_list(rows: list[dict[str, Any]], group: str, limit: int = 4) -> str:
    candidates = [row for row in rows if parent_group(row) == group]
    candidates.sort(key=lambda row: (classification(row).get("risk") == "high", -float(classification(row).get("confidence") or 0)))
    items = []
    for row in candidates[:limit]:
        c = classification(row)
        url = str(row.get("url") or "")
        embed = (
            '<div class="tweet-embed">'
            '<blockquote class="twitter-tweet" data-dnt="true" data-theme="light">'
            f'<a href="{esc(url)}"></a>'
            '</blockquote>'
            f'<div class="embed-fallback"><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">元投稿を開く</a></div>'
            '</div>'
            if url
            else '<div class="embed-fallback">投稿URLがありません</div>'
        )
        items.append(
            "<article class=\"sample\">"
            f"<div class=\"sample-meta\">{esc(category(row))} / {esc(stance(row))} / {esc(post_type(row))}</div>"
            f"<p>{esc(c.get('summary') or '')}</p>"
            f"{embed}"
            "</article>"
        )
    return "".join(items) or '<p class="muted">該当サンプルなし</p>'


def build(rows: list[dict[str, Any]]) -> str:
    parent_counts = Counter(parent_group(row) for row in rows)
    type_counts = Counter(post_type(row) for row in rows)
    stance_counts = Counter(stance(row) for row in rows)
    category_counts = Counter(category(row) for row in rows)

    promote = count_rows(rows, ["改憲賛成・推進", "9条・自衛隊明記に賛成", "緊急事態条項に賛成"])
    oppose = count_rows(rows, ["改憲反対・護憲", "9条・自衛隊明記に反対", "緊急事態条項に反対"])
    process = count_rows(rows, ["国民投票法・広告規制を重視", "手続き・発議可能性への関心"])
    pending = count_rows(rows, ["その他・分類保留", "未確認・過激表現", "政党・議員批判"])

    groups = ["改憲全体", "9条・自衛隊明記", "緊急事態条項", "国民投票法・広告規制", "政党・手続き", "保留・注意領域"]
    types = ["意見表明", "情報共有", "疑問・問題提起", "政党・議員批判", "要確認・保留"]
    stances = ["改憲支持", "改憲反対", "項目別賛成", "項目別反対", "手続き重視", "慎重", "中立", "未確認", "その他"]

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>憲法改正論議 論点ダッシュボード</title>
  <style>
    :root {{ --bg:#f4f6f8; --panel:#fff; --ink:#172033; --muted:#667085; --line:#d7dce5; --blue:#1769d1; --red:#b54708; --green:#16885a; --warn:#7a4cc2; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Yu Gothic","Noto Sans JP",sans-serif; line-height:1.65; }}
    header {{ background:#fff; border-bottom:1px solid var(--line); padding:28px min(5vw,56px) 20px; }}
    main {{ padding:20px min(5vw,56px) 48px; }}
    h1 {{ margin:0 0 8px; font-size:clamp(26px,4vw,42px); letter-spacing:0; }}
    h2 {{ margin:0 0 14px; font-size:20px; }}
    h3 {{ margin:0; font-size:18px; }}
    .lead,.muted {{ color:var(--muted); margin:0; }}
    .top-nav {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:16px; }}
    .top-nav a,.sample a {{ color:var(--blue); text-decoration:none; font-weight:800; }}
    .top-nav a {{ border:1px solid var(--line); border-radius:8px; background:#fbfcfe; padding:5px 10px; }}
    .notice {{ background:#fff; border:1px solid var(--line); border-left:5px solid var(--warn); border-radius:8px; padding:14px 16px; margin:0 0 16px; color:var(--muted); }}
    .axis-grid,.panel-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:12px; }}
    .axis-card,.panel,.sample {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .axis-card {{ min-height:190px; border-top:5px solid var(--muted); }}
    .axis-card.positive {{ border-top-color:var(--blue); }}
    .axis-card.negative {{ border-top-color:var(--red); }}
    .axis-card.process {{ border-top-color:var(--green); }}
    .axis-card.warn {{ border-top-color:var(--warn); }}
    .axis-kicker {{ font-size:12px; font-weight:900; color:var(--muted); }}
    .axis-count {{ font-size:34px; font-weight:900; margin:8px 0; }}
    .axis-count span {{ font-size:13px; color:var(--muted); margin-left:4px; }}
    .section {{ margin-top:18px; }}
    .bar-row {{ display:grid; gap:6px; margin:9px 0; }}
    .bar-meta {{ display:flex; justify-content:space-between; gap:12px; font-size:14px; }}
    .bar-track {{ height:10px; border-radius:999px; background:#eef2f7; overflow:hidden; }}
    .bar-fill {{ height:100%; background:linear-gradient(90deg,#dceeff,var(--blue)); }}
    .sample-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:12px; }}
    .sample {{ margin-bottom:10px; background:#fbfcfe; }}
    .sample-meta {{ color:var(--blue); font-size:12px; font-weight:900; }}
    .sample p {{ margin:6px 0 8px; }}
    .tweet-embed {{ margin-top:10px; min-height:72px; }}
    .tweet-embed iframe {{ max-width:100% !important; }}
    .embed-fallback {{ border:1px dashed var(--line); border-radius:8px; padding:10px 12px; background:#fff; color:var(--muted); font-size:13px; }}
    .small {{ font-size:13px; }}
    @media(max-width:720px) {{ header,main {{ padding-inline:14px; }} }}
  </style>
</head>
<body>
  <header>
    <nav class="top-nav"><a href="index.html">トップ</a><a href="constitutional-amendment-reaction-map.html">反応マップ</a><a href="constitutional-amendment-summary.html">まとめUI</a></nav>
    <h1>憲法改正論議 論点ダッシュボード</h1>
    <p class="lead">賛否を単純比較せず、改憲全体・項目別・手続き・投稿の性質に分けて表示します。</p>
  </header>
  <main>
    <p class="notice">このページの件数はYahooリアルタイム検索で取得した192件のサンプル内分類です。検索語に「賛成」「反対」「国民投票法」などを含むため、世論比率としては扱えません。</p>
    <section class="axis-grid">
      {card("改憲推進側", promote, "改憲全体、9条・自衛隊明記、緊急事態条項への賛成を含む親カテゴリ。", "positive")}
      {card("改憲慎重・反対側", oppose, "護憲、9条改正反対、緊急事態条項への警戒を含む親カテゴリ。", "negative")}
      {card("手続き重視", process, "国民投票法、広告規制、資金、SNS上の情報環境を重視する反応。", "process")}
      {card("保留・注意領域", pending, "政党批判、未確認・過激表現、分類保留。記事化前の確認対象。", "warn")}
    </section>
    <section class="section panel-grid">
      <div class="panel"><h2>親論点別</h2>{bar_rows(parent_counts, groups)}</div>
      <div class="panel"><h2>投稿の性質</h2>{bar_rows(type_counts, types)}</div>
      <div class="panel"><h2>スタンス別</h2>{bar_rows(stance_counts, stances)}</div>
      <div class="panel"><h2>分類別 上位</h2>{bar_rows(category_counts, [name for name,_ in category_counts.most_common(8)])}</div>
    </section>
    <section class="section">
      <h2>論点別サンプル</h2>
      <div class="sample-grid">
        <div class="panel"><h3>改憲全体</h3>{sample_list(rows, "改憲全体")}</div>
        <div class="panel"><h3>9条・自衛隊明記</h3>{sample_list(rows, "9条・自衛隊明記")}</div>
        <div class="panel"><h3>緊急事態条項</h3>{sample_list(rows, "緊急事態条項")}</div>
        <div class="panel"><h3>国民投票法・広告規制</h3>{sample_list(rows, "国民投票法・広告規制")}</div>
      </div>
    </section>
  </main>
  <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build constitutional amendment dashboard")
    parser.add_argument("--input", default="social-samples/constitutional_amendment_ollama_classified.json")
    parser.add_argument("--output", default="docs/constitutional-amendment-dashboard.html")
    args = parser.parse_args()
    rows = json.loads(resolve(args.input).read_text(encoding="utf-8"))
    output = resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build(rows), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
