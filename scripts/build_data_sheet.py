#!/usr/bin/env python3
"""11テーマのデータの中身を1枚にまとめた `DATA_SHEET.md` を生成する。

手で書くと必ず古くなるので、正典データ（THEMES.yaml の sample_file）と
公開ページから毎回作り直す。数字はこのスクリプトの出力だけを信じる。

    python3 scripts/build_data_sheet.py           # DATA_SHEET.md を書き出す
    python3 scripts/build_data_sheet.py --check   # 書き換えずに差分の有無だけ見る
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / "DATA_SHEET.md"


def field(record: dict, name: str):
    """分類結果を取り出す。テーマにより classification の下と直下の両方がある。"""
    nested = record.get("classification")
    if isinstance(nested, dict) and name in nested:
        return nested[name]
    return record.get(name)


def arena_points(html: str, theme: str) -> int | str:
    """散布マップの点の数。外部jsに切り出しているテーマはそちらを読む。"""
    external = ROOT / "docs" / f"{theme}-arena-data.js"
    sources = [html]
    if external.is_file():
        sources.append(external.read_text(encoding="utf-8"))
    # 変数名はテーマごとに違う（SM_RAW / HENOKO_ARENA_RAW / window.TAKAICHI_ARENA_DATA / const P）
    pattern = re.compile(r"(?:SM_RAW|const P|[A-Z_]*ARENA_(?:RAW|DATA))\s*=\s*\[(.*?)\];", re.S)
    for text in sources:
        match = pattern.search(text)
        if match:
            return match.group(1).count("{")
    return "—"


def theme_rows() -> list[dict]:
    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
    rows = []
    for key, theme in themes.items():
        records = json.loads((ROOT / theme["sample_file"]).read_text(encoding="utf-8"))
        html = (ROOT / theme["html"]).read_text(encoding="utf-8")
        judged = any(field(r, "is_opinion") is not None for r in records)
        opinions = [r for r in records if field(r, "is_opinion") is True] if judged else records
        issues = collections.Counter(
            field(r, "main_issue") for r in opinions if field(r, "main_issue")
        )
        stances = collections.Counter(field(r, "stance") for r in opinions if field(r, "stance"))
        rows.append(
            {
                "key": key,
                "title": theme["title"],
                "collected": len(records),
                "judged": judged,
                "opinions": len(opinions),
                "issues": issues,
                "stances": stances,
                "points": arena_points(html, key),
                "period": theme.get("sample_period") or "unknown",
                "updated_at": theme.get("updated_at") or "—",
            }
        )
    rows.sort(key=lambda r: -r["opinions"])
    return rows


def render(rows: list[dict]) -> str:
    out = [
        "# DATA_SHEET — 11テーマのデータの中身",
        "",
        "`scripts/build_data_sheet.py` が生成する。**手で書き換えない。**",
        "数字の出所は THEMES.yaml の `sample_file`（正典データ）と公開ページ。",
        "",
        "- **収集** … 集めた投稿の総数",
        "- **意見** … そのうち意見と判定されたもの。判定していないテーマは「未判定」",
        "- **論点 / 賛否 / マップの点** … 同じ意見の集合を数えていれば3つとも一致する",
        "",
        "## 一覧",
        "",
        "| テーマ | 収集 | 意見 | 論点の合計 | 賛否の合計 | マップの点 | 取得期間 | 最終更新 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        opinions = str(row["opinions"]) if row["judged"] else "未判定"
        out.append(
            f"| {row['title']} | {row['collected']} | {opinions} | "
            f"{sum(row['issues'].values())} | {sum(row['stances'].values()) or '—'} | "
            f"{row['points']} | {row['period']} | {row['updated_at']} |"
        )

    out += ["", "## テーマごとの中身", ""]
    for row in rows:
        out.append(f"### {row['title']}（`{row['key']}`）")
        out.append("")
        opinions = f"意見 {row['opinions']}件" if row["judged"] else "意見 **未判定**"
        out.append(f"収集 {row['collected']}件 / {opinions} / 取得期間 {row['period']}")
        out.append("")
        out.append("**論点**")
        out.append("")
        for label, count in row["issues"].most_common():
            out.append(f"- {label} … {count}")
        out.append("")
        out.append("**賛否**")
        out.append("")
        if row["stances"]:
            for label, count in row["stances"].most_common():
                out.append(f"- {label} … {count}")
        else:
            out.append("- （賛否のラベルなし）")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="書き換えずに差分の有無だけ見る")
    args = parser.parse_args()

    text = render(theme_rows())
    if args.check:
        current = SHEET.read_text(encoding="utf-8") if SHEET.is_file() else ""
        if current == text:
            print("OK  DATA_SHEET.md は最新です")
            return 0
        print("NG  DATA_SHEET.md が古くなっています。python3 scripts/build_data_sheet.py で作り直してください")
        return 1
    SHEET.write_text(text, encoding="utf-8")
    print(f"書き出しました: {SHEET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
