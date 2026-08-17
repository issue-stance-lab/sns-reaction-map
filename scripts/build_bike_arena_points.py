#!/usr/bin/env python3
"""自転車青切符ページの論点アリーナの点（SM_RAW）を、正典から作り直す。

    python3 scripts/build_bike_arena_points.py

このテーマは page_update_mode: manual だが、アリーナの点だけは再実行できる。
`docs/bike-blue-ticket-reaction-map.html` の `const SM_RAW = [ … ];` を丸ごと
差し替える。何度実行しても結果は同じ。

2026-08-17 まで、この配列は 2026-06 の旧1D分類のまま 181 点で止まっていて、
論点の内訳（ISSUES）とセクターごとの点の数が合っていなかった。
`scripts/verify_theme_page.py` の「母数の統一」で落ちる。

点の座標の意味（描画側は docs のページ内スクリプト）:

    i … ISSUES の添字。セクター（論点）を決める
    x … 色。>=0.5 が賛成の赤、<=-0.5 が反対の青、その間が中立の灰
    e … 中心からの距離。大きいほど外側＝主張が強い
    y, c … 描画には使っていない。配列の形をそろえるために残す
    s … ツールチップに出る要旨（AI生成の要約。本文そのままではない）
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
THEME = "bike-blue-ticket"
PAGE = ROOT / "docs" / f"{THEME}-reaction-map.html"

# ページ内 const ISSUES=[…] と同じ並び。ここがずれるとセクターと点が食い違う。
ISSUE_ORDER = [
    "取締り強化賛成",
    "インフラ整備優先",
    "車道走行への不安",
    "免許制要求",
    "ルール曖昧・不信",
    "その他",
]

STANCE_X = {
    "賛成（取締り強化支持）": 2.0,
    "反対（インフラ・制度優先）": -2.0,
    "どちらでもない": 0.0,
}

INTENSITY_E = {"low": 0.5, "medium": 1.2, "high": 2.0}

SM_RE = re.compile(r"const SM_RAW = \[.*?\n\];", re.DOTALL)


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
    samples = json.loads((ROOT / themes[THEME]["sample_file"]).read_text(encoding="utf-8"))

    rows = []
    for s in samples:
        c = s["classification"]
        issue = c["main_issue"]
        if issue not in ISSUE_ORDER:
            raise SystemExit(f"ISSUE_ORDER に無い論点があります: {issue}")
        if c["stance"] not in STANCE_X:
            raise SystemExit(f"STANCE_X に無い立場があります: {c['stance']}")
        rows.append(
            '  {{x:{x},y:0.0,e:{e},c:{c:.2f},s:"{s}",u:"{u}",i:{i}}}'.format(
                x=STANCE_X[c["stance"]],
                e=INTENSITY_E.get(c.get("intensity"), 1.2),
                c=float(c.get("confidence") or 0.7),
                s=esc(c.get("summary") or ""),
                u=esc(s["url"]),
                i=ISSUE_ORDER.index(issue),
            )
        )

    page = PAGE.read_text(encoding="utf-8")
    if len(SM_RE.findall(page)) != 1:
        raise SystemExit("const SM_RAW = [ … ]; が1つだけ必要です")
    # 要旨には「7159件」のような一次情報の数字が入る。数字の出所検査から外すために
    # この配列だけを id 付きの <script> に入れてある（configs の exclude_selectors）。
    if '<script id="bike-arena-points">' not in page:
        raise SystemExit('SM_RAW を囲む <script id="bike-arena-points"> がありません')
    block = "const SM_RAW = [\n" + ",\n".join(rows) + "\n];"
    PAGE.write_text(SM_RE.sub(lambda _m: block, page, count=1), encoding="utf-8")
    print(f"OK  SM_RAW を {len(rows)}点で作り直しました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
