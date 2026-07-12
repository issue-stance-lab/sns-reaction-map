#!/usr/bin/env python3
"""Embed the canonical bike 2D dataset and derived counts into its v3 page."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def replace_once(text: str, pattern: str, replacement: str, label: str, *, flags: int = 0) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise ValueError(f"{label}: expected one match, found {count}")
    return updated


def js_string(value: object) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")


def raw_lines(rows: list[dict]) -> str:
    lines = ["const SM_RAW = ["]
    for row in rows:
        lines.append(
            "  {"
            f"x:{float(row['stance_enforcement']):.1f},"
            f"y:{float(row['stance_priority']):.1f},"
            f"e:{float(row['emotional_intensity']):.1f},"
            f"c:{float(row.get('confidence', 0.5)):.2f},"
            f"s:{js_string(row.get('summary'))},"
            f"u:{js_string(row.get('url'))}"
            "},"
        )
    lines.append("];")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--updated-at", default="2026-07-12")
    args = parser.parse_args()

    rows = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("input must be a non-empty JSON list")

    total = len(rows)
    q1 = sum(1 for row in rows if row["stance_enforcement"] > 0 and row["stance_priority"] > 0)
    q3 = sum(1 for row in rows if row["stance_enforcement"] < 0 and row["stance_priority"] < 0)
    neutral = sum(1 for row in rows if row["stance_enforcement"] == 0 or row["stance_priority"] == 0)
    high = sum(1 for row in rows if row["emotional_intensity"] >= 1.5)
    calm = sum(1 for row in rows if row["emotional_intensity"] <= 0)
    q1_pct = round(q1 * 100 / total)

    html = args.html.read_text(encoding="utf-8")
    html = replace_once(
        html,
        r"const SM_RAW = \[.*?\n\];(?=\nconst SM_TOUR = \[)",
        raw_lines(rows),
        "SM_RAW",
        flags=re.DOTALL,
    )
    html = replace_once(html, r"(<h2>SNS意見スタンスマップ</h2><span>)\d+件", rf"\g<1>{total}件", "header count")
    html = replace_once(html, r"全件 \(\d+\)", f"全件 ({total})", "all filter")
    html = replace_once(html, r"取締り賛成×安全優先 \(\d+\)", f"取締り賛成×安全優先 ({q1})", "q1 filter")
    html = replace_once(html, r"取締り反対×ライダー重視 \(\d+\)", f"取締り反対×ライダー重視 ({q3})", "q3 filter")
    html = replace_once(html, r"高感情 e≥1\.5 \(\d+\)", f"高感情 e≥1.5 ({high})", "high filter")
    html = replace_once(html, r"冷静 e≤0 \(\d+\)", f"冷静 e≤0 ({calm})", "calm filter")

    for label, value in [
        (r"取締り賛成 × 安全優先 \(右上\)", q1),
        (r"取締り反対 × ライダー重視 \(左下\)", q3),
        ("中立含む（X=0またはY=0）", neutral),
        (r"高感情 \(e ≥ 1\.5\)", high),
    ]:
        html = replace_once(
            html,
            rf"(<div class=\"sm-slabel\">{label}</div><div class=\"sm-sval\"[^>]*>)\d+件",
            rf"\g<1>{value}件",
            f"stat {label}",
        )

    html = replace_once(
        html,
        r'\{title:"全体像：[^"]+",desc:"[^"]+",filter:"all"\}',
        f'{{title:"全体像：投稿分布",desc:"{total}件中{q1}件({q1_pct}%)が取締り賛成×安全優先です。",filter:"all"}}',
        "tour overview",
    )
    html = replace_once(html, r'第1象限：取締り強化支持派（\d+件）', f'第1象限：取締り強化支持派（{q1}件）', "tour q1")
    html = replace_once(html, r'第3象限：取締り反対・ライダーの自由を重視（\d+件）', f'第3象限：取締り反対・ライダーの自由を重視（{q3}件）', "tour q3")
    html = replace_once(html, r'(title:"高感情投稿（e≥1\.5）",desc:")\d+件。', rf'\g<1>{high}件。', "tour high")
    html = replace_once(html, r'(title:"冷静な投稿（e≤0）",desc:")\d+件。', rf'\g<1>{calm}件。', "tour calm")
    html = replace_once(
        html,
        r'(<span style="font-weight:700;">データの集め方:</span>).*?</div>',
        rf'\g<1> Yahooリアルタイム検索で収集し、重複除去後の公開投稿をOpenCode Go API / minimax-m2.7で2D分類しました。最終更新: {args.updated_at}。</div>',
        "data method",
    )

    args.html.write_text(html, encoding="utf-8")
    print(f"updated {args.html}: total={total} q1={q1} q3={q3} neutral={neutral} high={high} calm={calm}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
