#!/usr/bin/env python3
"""自転車の青切符の再読データ（理由区分）に、正典の立場を写した対応表を作る。

再読データ data/bike-blue-ticket_issues-reread.json の明細（論点名ごとの items）は tweet_id と理由区分だけを持ち、
立場（stance）を持たない。新デザインの読書面（scripts/bike_reading.py）は理由区分ごとの立場の内訳と代表投稿の立場を出すが、
GitHub の自動検査でも同じ生成ができるよう、非公開の正典は読まない。そこでこのスクリプトだけが正典を読み、
post_key（tweet_id の sha256）→ 立場 の対応表 data/bike-blue-ticket_reread-stances.json を書く。
憲法改正論議（scripts/constitutional_reread_stances.py）と同じ考え方で、共有の再読データ・台帳は変えない。

止まる条件:
- 再読データの明細に、正典に無い投稿・正典で意見でない投稿・正典と論点が違う投稿がある
- 写した立場を論点ごとに数えた結果が、公開JSON の issues[].stances と1件でも違う

データ更新（追い読み・定期更新）で再読データの明細が増えたら、もう一度実行する。読書面の生成器は、明細と対応表の投稿が
一致しないと止まる。本文・tweet_id は書かない（post_key と立場の名前だけ）。

    python3 scripts/bike_reread_stances.py --made-on YYYY-MM-DD
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "social-samples" / "bike-blue-ticket_2d_classified.json"
REREAD = ROOT / "data" / "bike-blue-ticket_issues-reread.json"
PUBLIC = ROOT / "docs" / "data" / "themes" / "bike-blue-ticket.json"
OUT = ROOT / "data" / "bike-blue-ticket_reread-stances.json"


def post_key(tweet_id: str) -> str:
    return hashlib.sha256(str(tweet_id).encode()).hexdigest()


def reread_items(reread: dict, public: dict) -> list[tuple[str, dict]]:
    """論点名ごとの items を (論点名, 明細) の並びにする。論点名は公開JSONの issues[].label。"""
    out = []
    for issue in public["issues"]:
        for item in reread[issue["label"]]["items"]:
            out.append((issue["label"], item))
    return out


def build(made_on: str) -> dict:
    canon = json.loads(CANON.read_text(encoding="utf-8"))
    by_key = {post_key(r["tweet_id"]): r for r in canon}
    reread = json.loads(REREAD.read_text(encoding="utf-8"))
    public = json.loads(PUBLIC.read_text(encoding="utf-8"))
    stances: dict[str, str] = {}
    pairs = reread_items(reread, public)
    for label, item in pairs:
        key = post_key(item["tweet_id"])
        row = by_key.get(key)
        if row is None:
            raise SystemExit(f"再読データの投稿 {key[:12]}… が正典にありません")
        c = row["classification"]
        if not row.get("is_opinion"):
            raise SystemExit(f"再読データの投稿 {key[:12]}… は正典で意見ではありません")
        if c.get("main_issue") != label:
            raise SystemExit(f"再読データの投稿 {key[:12]}… の論点が正典と違います")
        if key in stances:
            raise SystemExit(f"再読データの投稿 {key[:12]}… が2回あります")
        stances[key] = c["stance"]
    tally = Counter((label, stances[post_key(i["tweet_id"])]) for label, i in pairs)
    for issue in public["issues"]:
        for s in issue["stances"]:
            if tally[(issue["label"], s["label"])] != int(s["count"]):
                raise SystemExit(f"{issue['label']}×{s['label']}: 写した立場 {tally[(issue['label'], s['label'])]} 件が"
                                 f"公開JSONの {s['count']} 件と違います")
    return {
        "theme_id": "bike-blue-ticket",
        "_about": "再読データの明細（post_key＝tweet_id の sha256）ごとの立場。scripts/bike_reread_stances.py が正典から写した。"
                  "読書面の生成器はこれを読み、理由区分ごとの立場と代表投稿の立場を数える。本文・tweet_id は含まない。",
        "made_on": made_on,
        "canonical": str(CANON.relative_to(ROOT)),
        "canonical_sha256": hashlib.sha256(CANON.read_bytes()).hexdigest(),
        "reread_sha256": hashlib.sha256(REREAD.read_bytes()).hexdigest(),
        "public_updated_on": public["updated_on"],
        "count": len(stances),
        "public_mismatch": 0,
        "_public_mismatch": "論点×立場を数えた結果と公開JSON issues[].stances の食い違いの件数。0でなければ書かずに止まる。",
        "stances": dict(sorted(stances.items())),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--made-on", required=True, help="作った日 YYYY-MM-DD（今日の日付を自動では入れない）")
    args = ap.parse_args()
    data = build(args.made_on)
    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    old = OUT.read_text(encoding="utf-8") if OUT.exists() else None
    if old != text:
        OUT.write_text(text, encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)}（{data['count']}件）")
    else:
        print("変更なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
