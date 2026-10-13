#!/usr/bin/env python3
"""学校でのあだ名禁止の再読データ（理由区分）に、正典の立場を写した対応表を作る。

再読データ data/school-nickname-ban_issues-reread.json の明細（平坦な items）は post_key（tweet_id の sha256）・論点名・
理由区分だけを持ち、立場（stance）と tweet_id を持たない。新デザインの読書面（scripts/nickname_reading.py）は理由区分ごとの
立場の内訳と代表投稿の立場を出すが、GitHub の自動検査でも同じ生成ができるよう、非公開の正典は読まない。そこでこのスクリプト
だけが正典（THEMES.yaml の sample_file）を読み、post_key → 立場 の対応表 data/school-nickname-ban_reread-stances.json を書く。
自転車の青切符（scripts/bike_reread_stances.py）と同じ考え方で、共有の再読データ・台帳は変えない。

除外した明細（再読データの excluded_items）は対応表に入れない。正典で意見でない投稿（is_opinion=false）であることだけ確かめる。

止まる条件:
- 再読データの明細に、正典に無い投稿・正典で意見でない投稿・正典と論点が違う投稿・2回出てくる投稿がある
- 正典の意見（classification.is_opinion=true）に、再読データの明細に無い投稿がある（読み直しの漏れ）
- 除外した明細が、正典で意見になっている
- 写した立場を論点ごとに数えた結果が、公開JSON の issues[].stances と1件でも違う

データ更新（追い読み・定期更新）で再読データの明細が増えたら、もう一度実行する。読書面の生成器は、明細と対応表の投稿が
一致しないと止まる。本文・tweet_id は書かない（post_key と立場の名前だけ）。

    python3 scripts/nickname_reread_stances.py --made-on YYYY-MM-DD
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
THEME = "school-nickname-ban"
REREAD = ROOT / "data" / "school-nickname-ban_issues-reread.json"
PUBLIC = ROOT / "docs" / "data" / "themes" / "school-nickname-ban.json"
OUT = ROOT / "data" / "school-nickname-ban_reread-stances.json"


def post_key(tweet_id: str) -> str:
    return hashlib.sha256(str(tweet_id).encode()).hexdigest()


def canonical_path() -> Path:
    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))
    return ROOT / themes["themes"][THEME]["sample_file"]


def table(canon: list, reread: dict, public: dict, made_on: str, canonical: str, canonical_sha256: str,
          reread_sha256: str) -> dict:
    """正典の行と再読データから対応表を作る。公開JSONの論点×立場と1件でも違えば止まる。"""
    by_key = {post_key(r["tweet_id"]): r for r in canon}
    stances: dict[str, str] = {}
    for item in reread["items"]:
        key = item["post_key"]
        row = by_key.get(key)
        if row is None:
            raise SystemExit(f"再読データの投稿 {key[:12]}… が正典にありません")
        c = row["classification"]
        if not c.get("is_opinion"):
            raise SystemExit(f"再読データの投稿 {key[:12]}… は正典で意見ではありません")
        if c.get("main_issue") != item["main_issue"]:
            raise SystemExit(f"再読データの投稿 {key[:12]}… の論点が正典と違います")
        if key in stances:
            raise SystemExit(f"再読データの投稿 {key[:12]}… が2回あります")
        stances[key] = c["stance"]
    opinions = {post_key(r["tweet_id"]) for r in canon if r["classification"].get("is_opinion")}
    if opinions - set(stances):
        raise SystemExit(f"正典の意見のうち {len(opinions - set(stances))} 件が再読データの明細にありません（追い読みが要ります）")
    for item in reread.get("excluded_items", []):
        row = by_key.get(item["post_key"])
        if row is not None and row["classification"].get("is_opinion"):
            raise SystemExit(f"除外した明細 {item['post_key'][:12]}… が正典では意見になっています")
    tally = Counter((i["main_issue"], stances[i["post_key"]]) for i in reread["items"])
    for issue in public["issues"]:
        for s in issue["stances"]:
            if tally[(issue["label"], s["label"])] != int(s["count"]):
                raise SystemExit(f"{issue['label']}×{s['label']}: 写した立場 {tally[(issue['label'], s['label'])]} 件が"
                                 f"公開JSONの {s['count']} 件と違います")
    return {
        "theme_id": THEME,
        "_about": "再読データの明細（post_key＝tweet_id の sha256）ごとの立場。scripts/nickname_reread_stances.py が正典から写した。"
                  "読書面の生成器はこれを読み、理由区分ごとの立場と代表投稿の立場を数える。本文・tweet_id は含まない。"
                  "再読データの excluded_items（質問だけの投稿1件。正典で意見でない）は入れていない。",
        "made_on": made_on,
        "canonical": canonical,
        "canonical_sha256": canonical_sha256,
        "reread_sha256": reread_sha256,
        "public_updated_on": public["updated_on"],
        "count": len(stances),
        "excluded_count": len(reread.get("excluded_items", [])),
        "public_mismatch": 0,
        "_public_mismatch": "論点×立場を数えた結果と公開JSON issues[].stances の食い違いの件数。0でなければ書かずに止まる。",
        "stances": dict(sorted(stances.items())),
    }


def build(made_on: str) -> dict:
    canon = canonical_path()
    return table(json.loads(canon.read_text(encoding="utf-8")), json.loads(REREAD.read_text(encoding="utf-8")),
                 json.loads(PUBLIC.read_text(encoding="utf-8")), made_on, str(canon.relative_to(ROOT)),
                 hashlib.sha256(canon.read_bytes()).hexdigest(), hashlib.sha256(REREAD.read_bytes()).hexdigest())


def text_of(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=1) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--made-on", required=True, help="作った日 YYYY-MM-DD（今日の日付を自動では入れない）")
    args = ap.parse_args()
    data = build(args.made_on)
    text = text_of(data)
    old = OUT.read_text(encoding="utf-8") if OUT.exists() else None
    if old != text:
        OUT.write_text(text, encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)}（{data['count']}件）")
    else:
        print("変更なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
