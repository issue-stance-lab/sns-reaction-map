#!/usr/bin/env python3
"""部活動の地域移行の再読データ（5論点の理由区分）に、正典の立場を写した対応表を作る。

再読データは3つのファイルに分かれている（configs/planet/bukatsu-chiiki.yaml の sub_issues）。
- data/bukatsu-chiiki_teacher-reread.json            教員の働き方（items に stance あり）
- data/bukatsu-chiiki_cost-receiver-reread.json      費用・家庭負担／受け皿・指導者（items に stance あり）
- data/verification/bukatsu-chiiki-plan-child-subissues.json  制度・移行プロセス／教育的意義・機会（items に stance が無い）
明細の stance は読み直したときの記録で、2026-10-06 の賛否の判定し直しを反映していない（棚卸しで868件中308件が正典と違った）。
公開JSONの論点×立場は正典から数えているので、明細の立場のままでは読書面の立場の内訳が公開JSONと合わない。

そこでこのスクリプトだけが正典（THEMES.yaml の sample_file）を読み、post_key（tweet_id の sha256）→ 立場 の対応表
data/bukatsu-chiiki_reread-stances.json を書く。新しい読書面（scripts/bukatsu_reading.py）は正典を読まず、この対応表から
理由区分ごとの立場と代表投稿の立場を数える。消費税減税（scripts/consumption_tax_reread_stances.py）と同じ型。
共有の再読データ・公開中のページの仕組みは変えない。

止まる条件:
- 再読データの明細に、正典に無い投稿・正典で意見でない投稿・正典と論点が違う投稿・2回出てくる投稿がある
- 正典でこの5論点の意見になっている投稿が、再読データの明細に無い（読み直しの漏れ）
- 写した立場を論点ごとに数えた結果が、公開JSON の issues[].stances と1件でも違う

定期更新や追い読みで再読データの明細が増えたら、もう一度実行する（読書面の生成器は、明細と対応表の投稿が一致しないと止まる）。
本文・tweet_id は書かない（post_key と立場の名前だけ）。

    python3 scripts/bukatsu_reread_stances.py --made-on YYYY-MM-DD
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
THEME = "bukatsu-chiiki"
PUBLIC = ROOT / "docs" / "data" / "themes" / "bukatsu-chiiki.json"
PLANET = ROOT / "configs" / "planet" / "bukatsu-chiiki.yaml"
OUT = ROOT / "data" / "bukatsu-chiiki_reread-stances.json"


def post_key(tweet_id: str) -> str:
    return hashlib.sha256(str(tweet_id).encode()).hexdigest()


def canonical_path() -> Path:
    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))
    return ROOT / themes["themes"][THEME]["sample_file"]


def items_path(sub: dict) -> list[str]:
    path = list(sub["path"])
    if path[-1] != "buckets":
        raise SystemExit(f"planet設定の sub_issues.path の最後が buckets ではありません: {path}")
    return path[:-1] + ["items"]


def reread_rows(planet: dict, root: Path | None = None) -> tuple[list[tuple[str, dict]], dict[str, str]]:
    """(論点名, 明細) の一覧と、読んだファイルの sha256。root は再読データを読む場所（更新経路の adapter は作業ツリーを渡す）。"""
    root = Path(root) if root is not None else ROOT
    rows, shas, cache = [], {}, {}
    for label, sub in (planet.get("sub_issues") or {}).items():
        f = sub["file"]
        if f not in cache:
            p = root / f
            cache[f] = json.loads(p.read_text(encoding="utf-8"))
            shas[f] = hashlib.sha256(p.read_bytes()).hexdigest()
        node = cache[f]
        for key in items_path(sub):
            node = node[key]
        rows += [(label, it) for it in node]
    return rows, shas


def table(canon: list, planet: dict, public: dict, made_on: str, canonical: str, canonical_sha256: str,
          root: Path | None = None) -> dict:
    by_id = {str(r["tweet_id"]): r for r in canon}
    stances: dict[str, str] = {}
    issue_of: dict[str, str] = {}
    differs: Counter = Counter()
    unset: Counter = Counter()
    rows, shas = reread_rows(planet, root)
    for label, item in rows:
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
    labels = set(planet.get("sub_issues") or {})
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
        "_about": "再読データの明細（post_key＝tweet_id の sha256）ごとの立場。scripts/bukatsu_reread_stances.py が正典から写した。"
                  "新しい読書面の生成器はこれを読み、理由区分ごとの立場と代表投稿の立場を数える。本文・tweet_id は含まない。"
                  "再読データの明細にある stance は読み直したときの記録で、正典と違うものがある（reread_stance_differs）。"
                  "制度・移行プロセスと教育的意義・機会の明細には stance が無い（reread_stance_unset）。読書面はこの対応表の立場だけを使う。",
        "made_on": made_on,
        "canonical": canonical,
        "canonical_sha256": canonical_sha256,
        "reread_sha256": dict(sorted(shas.items())),
        "public_updated_on": public["updated_on"],
        "count": len(stances),
        "reread_stance_differs": dict(sorted(differs.items())),
        "reread_stance_unset": dict(sorted(unset.items())),
        "public_mismatch": 0,
        "_public_mismatch": "写した立場で論点×立場を数えた結果と公開JSON issues[].stances の食い違いの件数。0でなければ書かずに止まる。",
        "stances": dict(sorted(stances.items())),
    }


def build(made_on: str) -> dict:
    canon = canonical_path()
    return table(json.loads(canon.read_text(encoding="utf-8")), yaml.safe_load(PLANET.read_text(encoding="utf-8")),
                 json.loads(PUBLIC.read_text(encoding="utf-8")), made_on, str(canon.relative_to(ROOT)),
                 hashlib.sha256(canon.read_bytes()).hexdigest())


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
