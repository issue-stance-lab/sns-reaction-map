#!/usr/bin/env python3
"""Build a static multi-case portal for the SNS reaction map project."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def read_json(path: str) -> Any:
    return json.loads(resolve(path).read_text(encoding="utf-8"))


def esc(value: Any) -> str:
    return html.escape(str(value or ""))


def classification(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("classification") or {}


def case_stats(case: dict[str, Any]) -> dict[str, Any]:
    data_path = str(case.get("data_path") or "")
    if not data_path:
        return {"count": 0, "categories": Counter(), "stances": Counter(), "top_category": ""}
    path = resolve(data_path)
    if not path.exists():
        return {"count": 0, "categories": Counter(), "stances": Counter(), "top_category": ""}
    rows = json.loads(path.read_text(encoding="utf-8"))
    categories = Counter(str(classification(row).get("category") or "未分類") for row in rows)
    stances = Counter(
        str(classification(row).get("stance") or classification(row).get("stance_to_target") or "その他")
        for row in rows
    )
    top_category = categories.most_common(1)[0][0] if categories else ""
    return {"count": len(rows), "categories": categories, "stances": stances, "top_category": top_category}


def link_button(label: str, url: str, variant: str = "") -> str:
    if not url:
        return ""
    cls = "link-button" + (f" {variant}" if variant else "")
    return f'<a class="{cls}" href="{esc(url)}">{esc(label)}</a>'


def extra_links(case: dict[str, Any]) -> str:
    links: list[str] = []
    for item in case.get("article_urls") or []:
        links.append(link_button(str(item.get("label") or "記事"), str(item.get("url") or ""), "ghost"))
    for item in case.get("research_urls") or []:
        links.append(link_button(str(item.get("label") or "調査メモ"), str(item.get("url") or ""), "ghost"))
    return "".join(links)


def case_card(case: dict[str, Any]) -> str:
    stats = case_stats(case)
    axes = "".join(f"<span>{esc(axis)}</span>" for axis in case.get("primary_axes") or [])
    status = str(case.get("status") or "")
    status_class = "planned" if status == "企画中" else "active"
    links = [
        link_button("反応マップ", str(case.get("reaction_map_url") or "")),
        link_button("まとめUI", str(case.get("summary_url") or "")),
        link_button("標準マップ", str(case.get("standard_map_url") or ""), "ghost"),
        extra_links(case),
    ]
    return f"""
<article class="case-card">
  <div class="case-head">
    <div>
      <div class="kicker">{esc(case.get("topic_type"))}</div>
      <h2>{esc(case.get("title"))}</h2>
    </div>
    <span class="status {status_class}">{esc(status)}</span>
  </div>
  <p>{esc(case.get("subtitle"))}</p>
  <div class="case-stats">
    <div><span>サンプル</span><strong>{stats["count"]}</strong></div>
    <div><span>最多分類</span><strong>{esc(stats["top_category"] or "未収集")}</strong></div>
    <div><span>ソース</span><strong>{esc(case.get("source_label"))}</strong></div>
  </div>
  <div class="axis-list">{axes}</div>
  <div class="link-row">{''.join(links)}</div>
</article>
"""


def build(config: dict[str, Any]) -> str:
    cases = list(config.get("cases") or [])
    ready_count = sum(1 for case in cases if case_stats(case)["count"])
    planned_count = sum(1 for case in cases if str(case.get("status")) == "企画中")
    cards = "\n".join(case_card(case) for case in cases)
    notes = "".join(f"<li>{esc(note)}</li>" for note in config.get("notes") or [])

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(config.get("site_title"))}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4f6f8;
      --panel: #ffffff;
      --ink: #172033;
      --muted: #667085;
      --line: #d7dce5;
      --accent: #1769d1;
      --accent-soft: #e7f1ff;
      --warn: #b54708;
      --ok: #16885a;
      --shadow: 0 12px 30px rgba(16, 24, 40, .06);
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
      padding: 32px min(5vw, 56px) 24px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(28px, 4vw, 44px);
      letter-spacing: 0;
    }}
    h2 {{
      margin: 0;
      font-size: 21px;
      line-height: 1.35;
      letter-spacing: 0;
    }}
    p {{ margin: 10px 0 0; }}
    .lead {{
      max-width: 980px;
      color: var(--muted);
      margin: 0;
    }}
    main {{
      padding: 22px min(5vw, 56px) 48px;
    }}
    .top-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .stat {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 15px 16px;
      box-shadow: var(--shadow);
    }}
    .stat span {{
      display: block;
      color: var(--muted);
      font-size: 13px;
    }}
    .stat strong {{
      display: block;
      margin-top: 4px;
      font-size: 26px;
      font-variant-numeric: tabular-nums;
    }}
    .section-head {{
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 16px;
      margin: 18px 0 12px;
    }}
    .section-head h2 {{ font-size: 18px; }}
    .section-head p {{
      color: var(--muted);
      font-size: 13px;
      margin: 0;
    }}
    .case-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 14px;
    }}
    .case-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
      gap: 13px;
      min-height: 360px;
    }}
    .case-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: start;
    }}
    .kicker {{
      color: var(--accent);
      font-size: 12px;
      font-weight: 800;
      margin-bottom: 4px;
    }}
    .status {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 68px;
      min-height: 28px;
      border-radius: 999px;
      padding: 3px 10px;
      font-size: 12px;
      font-weight: 800;
      white-space: nowrap;
      background: #f2f4f7;
      color: #344054;
    }}
    .status.active {{
      background: #e8f7ef;
      color: var(--ok);
    }}
    .status.planned {{
      background: #fff1e8;
      color: var(--warn);
    }}
    .case-card p {{
      color: var(--muted);
      font-size: 14px;
    }}
    .case-stats {{
      display: grid;
      grid-template-columns: 92px minmax(0, 1fr);
      gap: 8px;
      border-top: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
      padding: 12px 0;
    }}
    .case-stats div {{
      display: contents;
    }}
    .case-stats span {{
      color: var(--muted);
      font-size: 12px;
    }}
    .case-stats strong {{
      min-width: 0;
      font-size: 13px;
      overflow-wrap: anywhere;
    }}
    .axis-list {{
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
    }}
    .axis-list span {{
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fbfcfe;
      padding: 4px 9px;
      color: #344054;
      font-size: 12px;
      font-weight: 700;
    }}
    .link-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: auto;
    }}
    .link-button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 34px;
      border-radius: 8px;
      padding: 6px 11px;
      background: var(--accent);
      color: #fff;
      text-decoration: none;
      font-size: 13px;
      font-weight: 800;
    }}
    .link-button.ghost {{
      background: #fff;
      color: var(--accent);
      border: 1px solid var(--line);
    }}
    .note-panel {{
      margin-top: 18px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      box-shadow: var(--shadow);
    }}
    .note-panel h2 {{
      font-size: 16px;
      margin-bottom: 8px;
    }}
    .note-panel ul {{
      margin: 0;
      padding-left: 20px;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 720px) {{
      header, main {{ padding-inline: 14px; }}
      .section-head {{ display: block; }}
      .case-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>{esc(config.get("site_title"))}</h1>
    <p class="lead">{esc(config.get("site_subtitle"))}</p>
  </header>
  <main>
    <section class="top-grid">
      <div class="stat"><span>登録テーマ</span><strong>{len(cases)}</strong></div>
      <div class="stat"><span>データあり</span><strong>{ready_count}</strong></div>
      <div class="stat"><span>企画中</span><strong>{planned_count}</strong></div>
    </section>
    <div class="section-head">
      <h2>事例一覧</h2>
      <p>各カードから、反応マップ・まとめUI・調査メモへ移動できます。</p>
    </div>
    <section class="case-grid">
      {cards}
    </section>
    <section class="note-panel">
      <h2>表示上の注意</h2>
      <ul>{notes}</ul>
    </section>
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build multi-case portal HTML")
    parser.add_argument("--config", default="configs/site-cases.json")
    parser.add_argument("--output", default="docs/index.html")
    args = parser.parse_args()

    config = read_json(args.config)
    output = resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build(config), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
