#!/usr/bin/env python3
"""消費税減税の再読データ（4論点の理由区分）に、正典の立場を写した対応表を作る。

再読データ data/consumption-tax-cut_4issues-reread.json の明細（hani・kouka・kyufu・jigyosha の items と excluded_items）は
tweet_id・理由区分・立場（stance）を持つ。ただし明細の立場は読み直したときの記録で、その後の分類のやり直しを反映していない。
2026-10-13 に正典と比べると、4論点で102件の立場が正典と違い、区分に当てはまらないとして除いた明細（excluded_items）36件には
立場が無かった。公開JSONの論点×立場は正典から数えているので、明細の立場のままでは読書面の立場の内訳が公開JSONと合わない。

そこでこのスクリプトだけが正典（THEMES.yaml の sample_file）を読み、post_key（tweet_id の sha256）→ 立場 の対応表
data/consumption-tax-cut_reread-stances.json を書く。新デザインの読書面（scripts/consumption_tax_reading.py）は、
GitHub の自動検査でも同じ生成ができるよう正典を読まず、この対応表から理由区分ごとの立場と代表投稿の立場を数える。
辺野古（scripts/henoko_reread_stances.py）を写した。共有の再読データ・台帳・現行ページの連動表示は変えない。

除いた明細（excluded_items）も、正典では意見でこの論点に入っている（公開JSONの件数に含まれる）ので対応表に入れる。

止まる条件:
- 再読データの明細（除いたものを含む）に、正典に無い投稿・正典で意見でない投稿・正典と論点が違う投稿・2回出てくる投稿がある
- 正典でこの論点の意見になっている投稿が、再読データの明細に無い（読み直しの漏れ）
- 写した立場を論点ごとに数えた結果が、公開JSON の issues[].stances と1件でも違う

データ更新（定期更新・追い読み）で再読データの明細が増えたら、もう一度実行する。読書面の生成器は、明細と対応表の投稿が
一致しないと止まる。本文・tweet_id は書かない（post_key と立場の名前だけ）。

    python3 scripts/consumption_tax_reread_stances.py --made-on YYYY-MM-DD
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
THEME = "consumption-tax-cut"
REREAD = ROOT / "data" / "consumption-tax-cut_4issues-reread.json"
PUBLIC = ROOT / "docs" / "data" / "themes" / "consumption-tax-cut.json"
PLANET = ROOT / "configs" / "planet" / "consumption-tax-cut.yaml"
OUT = ROOT / "data" / "consumption-tax-cut_reread-stances.json"


def post_key(tweet_id: str) -> str:
    return hashlib.sha256(str(tweet_id).encode()).hexdigest()


def canonical_path() -> Path:
    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))
    return ROOT / themes["themes"][THEME]["sample_file"]


def reread_rows(reread: dict, planet: dict) -> list[tuple[str, dict, bool]]:
    """(論点名, 明細, 除いた明細か) の一覧。planet 設定の sub_issues.items_path で論点ごとの明細を引く。"""
    rows = []
    for label, sub in (planet.get("sub_issues") or {}).items():
        path = list(sub["items_path"])
        node = reread
        for key in path[:-1]:
            node = node[key]
        rows += [(label, it, False) for it in node[path[-1]]]
        rows += [(label, it, True) for it in node.get("excluded_items", [])]
    return rows


def table(canon: list, reread: dict, planet: dict, public: dict, made_on: str, canonical: str,
          canonical_sha256: str, reread_sha256: str) -> dict:
    """正典の行と再読データから対応表を作る。公開JSONの論点×立場と1件でも違えば止まる。"""
    by_id = {str(r["tweet_id"]): r for r in canon}
    stances: dict[str, str] = {}
    issue_of: dict[str, str] = {}
    differs: Counter = Counter()
    unset: Counter = Counter()
    for label, item, excluded in reread_rows(reread, planet):
        tid = str(item["tweet_id"])
        key = post_key(tid)
        row = by_id.get(tid)
        if row is None:
            raise SystemExit(f"再読データの投稿 {key[:12]}… が正典にありません")
        c = row["classification"]
        if not c.get("is_opinion"):
            raise SystemExit(f"再読データの投稿 {key[:12]}… は正典で意見ではありません")
        if c.get("main_issue") != label:
            raise SystemExit(f"再読データの投稿 {key[:12]}… の論点が正典と違います（{label} と {c.get('main_issue')}）")
        if key in stances:
            raise SystemExit(f"再読データの投稿 {key[:12]}… が2回あります")
        stances[key] = c["stance"]
        issue_of[key] = label
        if item.get("stance") is None:
            unset[label] += 1
        elif item["stance"] != c["stance"]:
            differs[label] += 1
    labels = set((planet.get("sub_issues") or {}))
    opinions = {post_key(r["tweet_id"]) for r in canon
                if r["classification"].get("is_opinion") and r["classification"].get("main_issue") in labels}
    if opinions - set(stances):
        raise SystemExit(f"正典の意見のうち {len(opinions - set(stances))} 件が再読データの明細にありません（追い読みが要ります）")
    tally = Counter((issue_of[k], s) for k, s in stances.items())
    for issue in public["issues"]:
        if issue["label"] not in labels:
            continue
        for s in issue["stances"]:
            if tally[(issue["label"], s["label"])] != int(s["count"]):
                raise SystemExit(f"{issue['label']}×{s['label']}: 写した立場 {tally[(issue['label'], s['label'])]} 件が"
                                 f"公開JSONの {s['count']} 件と違います")
    return {
        "theme_id": THEME,
        "_about": "再読データの明細（post_key＝tweet_id の sha256。除いた明細 excluded_items を含む）ごとの立場。"
                  "scripts/consumption_tax_reread_stances.py が正典から写した。読書面の生成器はこれを読み、理由区分ごとの立場と"
                  "代表投稿の立場を数える。本文・tweet_id は含まない。再読データの明細にある stance は読み直したときの記録で、"
                  "正典と違うものがある（reread_stance_differs）。読書面はこの対応表の立場だけを使う。",
        "made_on": made_on,
        "canonical": canonical,
        "canonical_sha256": canonical_sha256,
        "reread_sha256": reread_sha256,
        "public_updated_on": public["updated_on"],
        "count": len(stances),
        "excluded_count": sum(1 for _, _, ex in reread_rows(reread, planet) if ex),
        "reread_stance_differs": dict(sorted(differs.items())),
        "_reread_stance_differs": "再読データの明細の stance が正典と違った件数（論点ごと）。除いた明細は stance を持たないので reread_stance_unset に数える。",
        "reread_stance_unset": dict(sorted(unset.items())),
        "public_mismatch": 0,
        "_public_mismatch": "写した立場で論点×立場を数えた結果と公開JSON issues[].stances の食い違いの件数。0でなければ書かずに止まる。",
        "stances": dict(sorted(stances.items())),
    }


def build(made_on: str) -> dict:
    canon = canonical_path()
    return table(json.loads(canon.read_text(encoding="utf-8")), json.loads(REREAD.read_text(encoding="utf-8")),
                 yaml.safe_load(PLANET.read_text(encoding="utf-8")), json.loads(PUBLIC.read_text(encoding="utf-8")),
                 made_on, str(canon.relative_to(ROOT)),
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
