#!/usr/bin/env python3
"""Build a Togetter-like summary UI from classified reaction JSON."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent


DEFAULT_CONFIG = {
    "title": "SNS反応まとめ",
    "subtitle": "投稿サンプルを論点ごとに整理したまとめビューです。",
    "lead": "これは世論調査ではなく、取得した投稿サンプルの論点整理です。",
    "category_order": [],
    "stance_order": ["批判", "擁護", "文科省支持", "反発", "追悼支持", "比較", "未確認", "保留", "その他"],
    "show_raw_text": False,
    "show_embeds": True,
    "max_cards": 120,
    "scorecards": [],
    "versus": None,
    "nav_links": [],
}


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def read_json(path: str) -> Any:
    return json.loads(resolve(path).read_text(encoding="utf-8"))


def merge_config(config_path: str | None) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if config_path:
        config.update(read_json(config_path))
    return config


def esc(value: Any) -> str:
    return html.escape(str(value or ""))


def classification(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("classification") or {}


def category(row: dict[str, Any]) -> str:
    return str(classification(row).get("category") or "未分類")


def stance(row: dict[str, Any]) -> str:
    return str(classification(row).get("stance") or classification(row).get("stance_to_target") or "その他")


def confidence(row: dict[str, Any]) -> float:
    try:
        return float(classification(row).get("confidence") or 0)
    except (TypeError, ValueError):
        return 0.0


def ordered(found: set[str], preferred: list[str]) -> list[str]:
    result = [item for item in preferred if item in found]
    result.extend(sorted(found - set(result)))
    return result


def scorecard_html(scorecards: list[dict[str, Any]]) -> str:
    if not scorecards:
        return ""
    rows = []
    for item in scorecards:
        rows.append(
            "<tr>"
            f"<th>{esc(item.get('topic'))}</th>"
            f"<td>{esc(item.get('criticism_score'))}</td>"
            f"<td>{esc(item.get('defense_score'))}</td>"
            f"<td>{esc(item.get('verdict'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel scorecard"><h2>論点スコアカード</h2>'
        '<table><thead><tr><th>論点</th><th>指摘側</th><th>反論側</th><th>判定</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></section>"
    )


def nav_html(config: dict[str, Any]) -> str:
    links = config.get("nav_links") or []
    if not links:
        return ""
    items = []
    for link in links:
        label = str(link.get("label") or "").strip()
        url = str(link.get("url") or "").strip()
        if label and url:
            items.append(f'<a href="{esc(url)}">{esc(label)}</a>')
    if not items:
        return ""
    return f'<nav class="top-nav">{"".join(items)}</nav>'


def mini_card_html(row: dict[str, Any], show_embeds: bool) -> str:
    c = classification(row)
    url = str(row.get("url") or "")
    embed = embed_html(url) if show_embeds else ""
    return (
        '<article class="mini-card">'
        f'<div class="mini-meta">{esc(category(row))} / {esc(stance(row))}</div>'
        f'<p>{esc(c.get("summary") or "")}</p>'
        f"{embed}"
        "</article>"
    )


def versus_html(rows: list[dict[str, Any]], config: dict[str, Any]) -> str:
    versus = config.get("versus") or {}
    if not versus:
        return ""
    left_categories = set(versus.get("left_categories") or [])
    right_categories = set(versus.get("right_categories") or [])
    if not left_categories or not right_categories:
        return ""

    show_embeds = bool(config.get("show_embeds", True))
    sample_limit = int(versus.get("sample_limit") or 3)
    left_rows = [row for row in rows if category(row) in left_categories]
    right_rows = [row for row in rows if category(row) in right_categories]
    left_rows = sorted(left_rows, key=lambda row: (not bool(classification(row).get("article_usable", False)), -confidence(row)))[:sample_limit]
    right_rows = sorted(right_rows, key=lambda row: (not bool(classification(row).get("article_usable", False)), -confidence(row)))[:sample_limit]
    left_count = sum(1 for row in rows if category(row) in left_categories)
    right_count = sum(1 for row in rows if category(row) in right_categories)

    return f"""
<section class="versus panel">
  <div class="versus-head">
    <h2>{esc(versus.get("title") or "評価する VS 評価しない")}</h2>
    <p>{esc(versus.get("description") or "")}</p>
  </div>
  <div class="versus-grid">
    <div class="side side-left">
      <div class="side-title"><span>{esc(versus.get("left_label") or "評価する")}</span><strong>{left_count}</strong></div>
      <p class="side-copy">{esc(versus.get("left_description") or "")}</p>
      {''.join(mini_card_html(row, show_embeds) for row in left_rows)}
    </div>
    <div class="vs-mark">VS</div>
    <div class="side side-right">
      <div class="side-title"><span>{esc(versus.get("right_label") or "評価しない")}</span><strong>{right_count}</strong></div>
      <p class="side-copy">{esc(versus.get("right_description") or "")}</p>
      {''.join(mini_card_html(row, show_embeds) for row in right_rows)}
    </div>
  </div>
</section>
"""


def chips_html(items: list[str], attr: str) -> str:
    buttons = [f'<button class="chip active" data-filter-{attr}="all">すべて</button>']
    buttons.extend(f'<button class="chip" data-filter-{attr}="{esc(item)}">{esc(item)}</button>' for item in items)
    return "".join(buttons)


def embed_html(url: str) -> str:
    if not url:
        return '<div class="embed-fallback">投稿URLがありません</div>'
    return (
        '<div class="tweet-embed">'
        '<blockquote class="twitter-tweet" data-dnt="true" data-theme="light">'
        f'<a href="{esc(url)}"></a>'
        '</blockquote>'
        f'<div class="embed-fallback"><a href="{esc(url)}" target="_blank" rel="noopener noreferrer">元投稿を開く</a></div>'
        '</div>'
    )


def card_html(row: dict[str, Any], index: int, show_raw_text: bool, show_embeds: bool) -> str:
    c = classification(row)
    text = str(row.get("text", "")).replace("\n", " ")
    if len(text) > 260:
        text = text[:257] + "..."
    summary = str(c.get("summary") or text)
    reason = str(c.get("reason") or "")
    url = str(row.get("url") or "")
    raw = f'<blockquote>{esc(text)}</blockquote>' if show_raw_text else ""
    embed = embed_html(url) if show_embeds else ""
    article_usable = "記事向き" if c.get("article_usable") else "要確認"
    return f"""
<article class="post-card" data-category="{esc(category(row))}" data-stance="{esc(stance(row))}">
  <div class="post-head">
    <span class="num">#{index}</span>
    <span class="badge">{esc(category(row))}</span>
    <span class="stance">{esc(stance(row))}</span>
  </div>
  <p class="summary">{esc(summary)}</p>
  {raw}
  {embed}
  <div class="reason">{esc(reason)}</div>
  <div class="post-meta">
    <span>信頼度 {confidence(row):.2f}</span>
    <span>{esc(article_usable)}</span>
    <span>検索語: {esc(row.get("query", ""))}</span>
  </div>
  <div class="post-actions">
    <a href="{esc(url)}" target="_blank" rel="noopener noreferrer">元投稿を開く</a>
  </div>
</article>
"""


def build(rows: list[dict[str, Any]], config: dict[str, Any]) -> str:
    category_order = ordered({category(row) for row in rows}, list(config.get("category_order") or []))
    stance_order = ordered({stance(row) for row in rows}, list(config.get("stance_order") or []))
    category_counts = Counter(category(row) for row in rows)
    stance_counts = Counter(stance(row) for row in rows)
    query_counts = Counter(str(row.get("query") or "") for row in rows)

    sorted_rows = sorted(
        rows,
        key=lambda row: (
            category_order.index(category(row)) if category(row) in category_order else 999,
            not bool(classification(row).get("article_usable", False)),
            -confidence(row),
        ),
    )
    max_cards = int(config.get("max_cards") or len(sorted_rows))
    visible_rows = sorted_rows[:max_cards]

    category_summary = "".join(
        f'<li><span>{esc(name)}</span><strong>{count}</strong></li>'
        for name, count in category_counts.most_common()
    )
    stance_summary = "".join(
        f'<li><span>{esc(name)}</span><strong>{count}</strong></li>'
        for name, count in stance_counts.most_common()
    )
    query_summary = "".join(
        f'<li><span>{esc(name)}</span><strong>{count}</strong></li>'
        for name, count in query_counts.most_common(8)
    )
    cards = "\n".join(
        card_html(
            row,
            i,
            bool(config.get("show_raw_text")),
            bool(config.get("show_embeds", True)),
        )
        for i, row in enumerate(visible_rows, 1)
    )
    scorecards = config.get("scorecards") or []

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(config.get('title'))}</title>
  <style>
    :root {{
      --bg: #f5f6f8;
      --panel: #ffffff;
      --ink: #182033;
      --muted: #667085;
      --line: #d7dce5;
      --accent: #1769d1;
      --accent-soft: #e7f1ff;
      --warn: #b54708;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", "Noto Sans JP", sans-serif;
      line-height: 1.65;
    }}
    header {{
      background: #fff;
      border-bottom: 1px solid var(--line);
      padding: 26px min(5vw, 56px) 18px;
    }}
    .top-nav {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 16px;
    }}
    .top-nav a {{
      display: inline-flex;
      align-items: center;
      min-height: 32px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 5px 10px;
      background: #fbfcfe;
      color: var(--accent);
      text-decoration: none;
      font-weight: 800;
      font-size: 13px;
    }}
    h1 {{ margin: 0 0 6px; font-size: clamp(26px, 4vw, 42px); letter-spacing: 0; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; }}
    h3 {{ margin: 0; font-size: 15px; }}
    .lead {{ margin: 0; color: var(--muted); max-width: 980px; }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 360px;
      gap: 18px;
      padding: 18px min(5vw, 56px) 48px;
      align-items: start;
    }}
    .main, aside {{ min-width: 0; }}
    .panel, .post-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 12px;
    }}
    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 4;
      background: rgba(245,246,248,.94);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid var(--line);
      padding: 10px 0;
      margin-bottom: 12px;
    }}
    .chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }}
    .chip {{
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      cursor: pointer;
    }}
    .chip.active {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
    .post-head {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
    .num {{ color: var(--muted); font-size: 12px; font-weight: 700; }}
    .badge, .stance {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 2px 9px;
      font-size: 12px;
      font-weight: 700;
    }}
    .badge {{ background: var(--accent-soft); color: #0f4e9d; }}
    .stance {{ background: #f2f4f7; color: #344054; }}
    .summary {{ font-size: 16px; margin: 12px 0 8px; }}
    blockquote {{
      margin: 10px 0;
      padding: 10px 12px;
      border-left: 3px solid var(--line);
      background: #fbfcfe;
      color: #344054;
      font-size: 13px;
    }}
    .reason {{ color: var(--muted); font-size: 13px; }}
    .tweet-embed {{
      margin: 12px 0;
      min-height: 72px;
    }}
    .tweet-embed iframe {{
      max-width: 100% !important;
    }}
    .embed-fallback {{
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 10px 12px;
      background: #fbfcfe;
      font-size: 13px;
      color: var(--muted);
    }}
    .post-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px 12px;
      color: var(--muted);
      font-size: 12px;
      margin-top: 10px;
    }}
    .post-actions {{ margin-top: 10px; }}
    a {{ color: var(--accent); text-decoration: none; font-weight: 700; }}
    a:hover {{ text-decoration: underline; }}
    .stat-list {{ list-style: none; padding: 0; margin: 0; }}
    .stat-list li {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      border-bottom: 1px solid var(--line);
      padding: 8px 0;
      font-size: 13px;
    }}
    .stat-list li:last-child {{ border-bottom: 0; }}
    .stat-list span {{ color: var(--muted); overflow-wrap: anywhere; }}
    .stat-list strong {{ white-space: nowrap; }}
    .scorecard table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    .scorecard th, .scorecard td {{ border: 1px solid var(--line); padding: 8px; text-align: left; vertical-align: top; }}
    .scorecard thead th {{ background: #eef2f7; }}
    .versus-head p {{ margin: 0; color: var(--muted); font-size: 13px; }}
    .versus-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 64px minmax(0, 1fr);
      gap: 12px;
      align-items: start;
      margin-top: 14px;
    }}
    .side {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: #fbfcfe;
    }}
    .side-left {{ border-top: 4px solid #1769d1; }}
    .side-right {{ border-top: 4px solid #b54708; }}
    .side-title {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      font-weight: 800;
      font-size: 18px;
    }}
    .side-title strong {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 42px;
      height: 32px;
      border-radius: 999px;
      background: #fff;
      border: 1px solid var(--line);
      font-size: 16px;
    }}
    .side-copy {{ margin: 8px 0 12px; color: var(--muted); font-size: 13px; }}
    .vs-mark {{
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 96px;
      border-radius: 8px;
      background: var(--ink);
      color: #fff;
      font-weight: 900;
      letter-spacing: 0;
    }}
    .mini-card {{
      border-top: 1px solid var(--line);
      padding-top: 10px;
      margin-top: 10px;
    }}
    .mini-meta {{ color: var(--accent); font-size: 12px; font-weight: 800; }}
    .mini-card p {{ margin: 6px 0 8px; font-size: 14px; }}
    .notice {{ color: var(--muted); font-size: 13px; }}
    @media (max-width: 960px) {{
      .layout {{ grid-template-columns: 1fr; }}
      aside {{ order: -1; }}
      .toolbar {{ position: static; }}
      .versus-grid {{ grid-template-columns: 1fr; }}
      .vs-mark {{ min-height: 44px; }}
    }}
  </style>
</head>
<body>
  <header>
    {nav_html(config)}
    <h1>{esc(config.get('title'))}</h1>
    <p class="lead">{esc(config.get('subtitle'))}</p>
  </header>
  <div class="layout">
    <main class="main">
      <section class="panel">
        <h2>まとめの前提</h2>
        <p class="notice">{esc(config.get('lead'))}</p>
      </section>
      {versus_html(rows, config)}
      {scorecard_html(scorecards)}
      <div class="toolbar">
        <h2>フィルタ</h2>
        <div class="chip-row" id="categoryFilters">{chips_html(category_order, "category")}</div>
        <div class="chip-row" id="stanceFilters">{chips_html(stance_order, "stance")}</div>
      </div>
      <section id="cards">
        {cards}
      </section>
    </main>
    <aside>
      <section class="panel">
        <h2>全体</h2>
        <ul class="stat-list">
          <li><span>投稿サンプル</span><strong>{len(rows)}</strong></li>
          <li><span>表示カード</span><strong>{len(visible_rows)}</strong></li>
        </ul>
      </section>
      <section class="panel">
        <h2>分類別</h2>
        <ul class="stat-list">{category_summary}</ul>
      </section>
      <section class="panel">
        <h2>立場別</h2>
        <ul class="stat-list">{stance_summary}</ul>
      </section>
      <section class="panel">
        <h2>検索語</h2>
        <ul class="stat-list">{query_summary}</ul>
      </section>
    </aside>
  </div>
  <script>
    let categoryFilter = "all";
    let stanceFilter = "all";
    function updateCards() {{
      document.querySelectorAll(".post-card").forEach(card => {{
        const okCategory = categoryFilter === "all" || card.dataset.category === categoryFilter;
        const okStance = stanceFilter === "all" || card.dataset.stance === stanceFilter;
        card.style.display = okCategory && okStance ? "" : "none";
      }});
    }}
    function bindFilters(containerId, attr, setter) {{
      document.querySelectorAll(`#${{containerId}} .chip`).forEach(button => {{
        button.addEventListener("click", () => {{
          document.querySelectorAll(`#${{containerId}} .chip`).forEach(item => item.classList.remove("active"));
          button.classList.add("active");
          setter(button.dataset[`filter${{attr}}`]);
          updateCards();
        }});
      }});
    }}
    bindFilters("categoryFilters", "Category", value => categoryFilter = value);
    bindFilters("stanceFilters", "Stance", value => stanceFilter = value);
  </script>
  <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Togetter-like summary UI")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config", default="")
    parser.add_argument("--scorecards", default="")
    args = parser.parse_args()

    rows = read_json(args.input)
    config = merge_config(args.config or None)
    if args.scorecards:
        config["scorecards"] = read_json(args.scorecards)
    output = resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build(rows, config), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
