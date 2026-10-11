#!/usr/bin/env python3
"""生成AIと著作権ページの冒頭（題名・件数・入口の2問・短答）を生成する試作。

入力:
  - configs/ai-copyright-opening.json  冒頭の文言・短答・出典（手で書く唯一の場所）
  - docs/data/themes/ai-copyright.json 件数・論点別件数・集計期間（公開JSON）
  - data/ai-copyright_issues-reread.json 理由別の内訳がある論点の判定（buckets の有無）

出力（--out-dir、既定は quality/prototypes/ai-copyright-opening）:
  - opening-fragment.html  冒頭の部品（<section> 1つ）。将来ページへ貼る単位
  - index.html             部品を包んだ確認用の単独ページ（opening.css を読む）

日時や乱数は使わないので、同じ入力なら何度実行しても同じ出力になる。
--check を付けると書き込まず、出力が最新でなければ終了コード1で止まる。

公開HTMLを雛形にする既存の仕組み（build_ai_copyright_arena.py ほか）は変えない。
"""

from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "ai-copyright-opening.json"
DEFAULT_OUT = ROOT / "quality" / "prototypes" / "ai-copyright-opening"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def jp_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{int(y)}年{int(m)}月{int(d)}日"


def fmt(n: int) -> str:
    return f"{n:,}"


def issues_with_reasons(reason_path: Path, theme_id: str) -> set[str]:
    """理由別の内訳（buckets）がある論点の id を返す。キー learning_data → ai-copyright-learning-data。"""
    if not reason_path.exists():
        return set()
    data = load_json(reason_path)
    found = set()
    for key, value in data.items():
        if isinstance(value, dict) and value.get("buckets"):
            found.add(f"{theme_id}-{key.replace('_', '-')}")
    return found


def validate(public: dict, reasons: set[str]) -> None:
    issues = public["issues"]
    total = sum(i["count"] for i in issues)
    if total != public["opinion_count"]:
        raise SystemExit(f"論点別件数の合計 {total} が意見件数 {public['opinion_count']} と一致しない")
    ids = {i["id"] for i in issues}
    unknown = reasons - ids
    if unknown:
        raise SystemExit(f"理由データに公開JSONに無い論点がある: {sorted(unknown)}")
    if public.get("collection_period", {}).get("status") != "known":
        raise SystemExit("collection_period が known でない（集計期間を表示できない）")


def pictogram(kind: str, labels: dict, aria: str) -> str:
    """透かし紙を重ねて比べる図。文字はHTMLで置き、図形はCSSで描く。"""
    o = escape(labels["original"])
    g = escape(labels["generated"])
    if kind == "both":
        marks = (
            f'<span class="sheet-overlap"><span>{escape(labels["similarity"])}</span></span>'
            f'<span class="sheet-arrow"><span>{escape(labels["reliance"])}</span></span>'
        )
        cls = "pict pict--both"
    elif kind == "style-only":
        marks = f'<span class="sheet-style"><span>{escape(labels["style"])}</span></span>'
        cls = "pict pict--style"
    else:
        raise SystemExit(f"未知の図柄: {kind}")
    return (
        f'<div class="{cls}" role="img" aria-label="{escape(aria)}">'
        f'<span class="sheet sheet--original"><span class="sheet-name">{o}</span></span>'
        f'<span class="sheet sheet--generated"><span class="sheet-name">{g}</span></span>'
        f"{marks}</div>"
    )


def render_sources(ids: list[str], sources: dict) -> str:
    items = []
    for sid in ids:
        s = sources[sid]
        issued = f"（{escape(s['issued'])}）" if s.get("issued") else ""
        items.append(
            f'<li><a href="{escape(s["url"])}" target="_blank" rel="noopener noreferrer">'
            f'{escape(s["publisher"])}「{escape(s["title"])}」{issued} ↗</a>'
            f'<span class="src-meta">{escape(s["locator"])}。資料の確認日 {jp_date(s["checked_on"])}</span></li>'
        )
    return '<ul class="answer-sources">' + "".join(items) + "</ul>"


def render_count(public: dict, cfg: dict, reasons: set[str]) -> str:
    cb = cfg["count_block"]
    period = public["collection_period"]
    named = [i for i in public["issues"] if i.get("kind") != "other"]
    other = [i for i in public["issues"] if i.get("kind") == "other"]
    ordered = sorted(named, key=lambda i: (-i["count"], i["id"])) + other
    total = public["opinion_count"]
    mark = cb["reason_missing_mark"]

    segs, rows = [], []
    for rank, issue in enumerate(ordered):
        share = issue["count"] / total * 100
        tone = "other" if issue.get("kind") == "other" else ("a" if rank % 2 == 0 else "b")
        missing = issue["id"] not in reasons
        segs.append(
            f'<span class="ruler-seg ruler-seg--{tone}" style="flex-grow:{issue["count"]}" '
            f'title="{escape(issue["label"])} {fmt(issue["count"])}件"></span>'
        )
        rows.append(
            f'<li class="issue-row issue-row--{tone}" data-issue="{escape(issue["id"])}">'
            f'<span class="issue-swatch" aria-hidden="true"></span>'
            f'<span class="issue-name">{escape(issue["label"])}'
            + (f'<span class="issue-mark" title="{escape(cb["reason_missing_note"])}">{escape(mark)}</span>' if missing else "")
            + f'</span><span class="issue-count">{fmt(issue["count"])}<small>件</small></span>'
            f'<span class="issue-share">{share:.0f}%</span></li>'
        )
    has_missing = any(i["id"] not in reasons for i in ordered)
    return (
        '<div class="count-panel" aria-labelledby="aic-count-label">'
        f'<p class="count-label" id="aic-count-label">{escape(cb["label"])}</p>'
        f'<p class="count-number"><strong>{fmt(total)}</strong><small>件</small></p>'
        f'<p class="count-basis">{escape(cb["basis"].format(collected=fmt(public["collected_count"])))}</p>'
        f'<p class="count-period">{escape(cb["period"].format(start=jp_date(period["start"]), end=jp_date(period["end"])))}</p>'
        f'<h2 class="issues-title">{escape(cb["issues_title"].format(n=len(ordered)))}</h2>'
        f'<div class="ruler" aria-hidden="true">{"".join(segs)}</div>'
        f'<ol class="issue-list">{"".join(rows)}</ol>'
        + (f'<p class="count-note">{escape(cb["reason_missing_note"])}</p>' if has_missing else "")
        + f'<p class="count-note">{escape(cb["sample_note"])}</p>'
        "</div>"
    )


def render_fragment(cfg: dict, public: dict, reasons: set[str]) -> str:
    h = cfg["headline"]
    crumbs = " ／ ".join(escape(c) for c in cfg["breadcrumb"])
    cards = []
    for q in cfg["entry_questions"]:
        cards.append(
            f'<article class="answer-card" id="aic-q-{escape(q["id"])}">'
            f'<div class="answer-head"><span class="answer-kind">{escape(q["kind"])}</span>'
            f'<h2 class="answer-q">{escape(q["question"])}</h2></div>'
            f'{pictogram(q["pictogram"], cfg["figure_labels"], q["pictogram_label"])}'
            f'<p class="answer-text">{escape(q["answer"])}</p>'
            f'<p class="answer-note">{escape(q["note"])}</p>'
            f'{render_sources(q["sources"], cfg["sources"])}'
            "</article>"
        )
    actions = "".join(
        f'<a class="aic-button{" aic-button--sub" if n else ""}" href="{escape(a["href"])}">{escape(a["label"])} <span aria-hidden="true">↓</span></a>'
        for n, a in enumerate(cfg["actions"])
    )
    return (
        "<!-- AI_COPYRIGHT_OPENING_START: scripts/ai_copyright_opening.py で生成。直接編集しない -->\n"
        f'<section class="aic-opening" id="top" aria-labelledby="aic-title" data-theme-id="{escape(cfg["theme_id"])}" '
        f'data-updated-on="{escape(public["updated_on"])}">\n'
        '<div class="aic-wrap">\n'
        f'<nav class="aic-crumbs" aria-label="パンくず">{crumbs}</nav>\n'
        '<div class="aic-hero">\n'
        '<div class="aic-hero-copy">\n'
        f'<p class="aic-eyebrow">{escape(cfg["eyebrow"])}</p>\n'
        f'<h1 id="aic-title">{escape(h["lead"])}<br><em>{escape(h["emphasis"])}</em></h1>\n'
        f'<p class="aic-lead">{escape(cfg["lead"])}</p>\n'
        f'<p class="aic-updated">SNSの集計は{jp_date(public["collection_period"]["end"])}までの投稿です。</p>\n'
        f'<div class="aic-actions">{actions}</div>\n'
        "</div>\n"
        f'<div class="answer-grid">{"".join(cards)}</div>\n'
        f"{render_count(public, cfg, reasons)}\n"
        "</div>\n"
        f'<p class="aic-after">{escape(cfg["after_answers"])}</p>\n'
        f'<p class="aic-disclaimer">{escape(cfg["disclaimer"])}</p>\n'
        "</div>\n"
        "</section>\n"
        "<!-- AI_COPYRIGHT_OPENING_END -->\n"
    )


def render_page(cfg: dict, fragment: str) -> str:
    return (
        "<!doctype html>\n"
        '<html lang="ja">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="robots" content="noindex">\n'
        f"<title>{escape(cfg['page_title'])}</title>\n"
        '<link rel="stylesheet" href="opening.css">\n'
        "</head>\n<body>\n"
        '<header class="proto-header"><span class="proto-site">SNS反応まっぷ</span>'
        '<span class="proto-flag">冒頭の試作（非公開）</span></header>\n'
        f'<main id="main">\n{fragment}</main>\n'
        "</body>\n</html>\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--check", action="store_true", help="書き込まずに、出力が最新かだけ確かめる")
    args = ap.parse_args()

    cfg = load_json(args.config)
    public = load_json(ROOT / cfg["public_json"])
    if public.get("theme_id") != cfg["theme_id"]:
        raise SystemExit(f"公開JSONのテーマ {public.get('theme_id')} が設定 {cfg['theme_id']} と違う")
    reasons = issues_with_reasons(ROOT / cfg["reason_data"], cfg["theme_id"])
    validate(public, reasons)
    for q in cfg["entry_questions"]:
        for sid in q["sources"]:
            if sid not in cfg["sources"]:
                raise SystemExit(f"出典 {sid} が sources に無い")

    fragment = render_fragment(cfg, public, reasons)
    outputs = {
        args.out_dir / "opening-fragment.html": fragment,
        args.out_dir / "index.html": render_page(cfg, fragment),
    }
    stale = []
    for path, text in outputs.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == text:
            continue
        if args.check:
            stale.append(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            print(f"書き込み: {path.relative_to(ROOT)}")
    if stale:
        for p in stale:
            print(f"最新でない: {p.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if not args.check:
        print("完了（変更が無いファイルは書き込んでいない）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
