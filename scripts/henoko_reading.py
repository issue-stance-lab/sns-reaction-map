#!/usr/bin/env python3
"""辺野古高校生死亡事故ページの「論点ごとの読書面」を、冒頭の試作の下につないで生成する試作。

学校でのあだ名禁止（scripts/nickname_reading.py。高齢者・自転車から写した部活動型の圧縮済みの型）を写した。違うのは設定JSONと次の点。
- 人が亡くなった事故のテーマ。論点タブにアイコンを付けない（planet 設定の論点アイコンには浮き輪があり、冒頭で避けた
  船・波・海の図柄に当たる）。投稿の例は設定の選定基準（実名・特定情報・事故の生々しい描写・煽る表現を除く）で選ぶ。
- 立場は「文科省判断を支持／反発／論点を切り分ける／中立・情報共有」の4つで、「論点を切り分ける」が9割を占める。
  冒頭と同じく立場の帯を主役にせず、論点の見出しの下は立場の1文（件数のある立場だけ）にする。
  帯は折りたたみの「立場ごとの件数と割合」の中だけに置く。理由ごとの立場も、件数のある立場を文で並べる。
- 再読データは buckets[論点名] と全論点を含む平坦な items（post_key・main_issue・bucket）を持ち、立場と tweet_id を持たない。
  立場は scripts/henoko_reread_stances.py が正典から写した対応表（data/henoko-student-accident_reread-stances.json）から読む。
  明細と対応表の投稿が一致しなければ止まる。非公開の正典は読まない。6論点すべてに理由区分がある。
- 「その他」が0件のあいだは、タブも欄も出さない（公開JSONで1件以上になれば自動で最後に出る）。
- 制度の確認は背景台帳の checklist の項目を、設定 issues[].checks で論点に割り当てる（台帳は現行ページと共有なので変えない）。
  報告書が公表されたかと公的機関の公表の一覧は論点ごとに繰り返さず、背景の行（#bg-official）への1行のリンクにする。
- 収集期間の翌日以降が未収集で、次回の収集予定（THEMES.yaml の collect_at）を読書面の上に注記する。

入力
- configs/henoko-student-accident-reading.json : 論点の説明・理由の声・投稿の選定（手書き文言）
- configs/henoko-student-accident-opening.json : 冒頭の文言・一次資料の確認日 checked_on・報告書の公表 report（冒頭部品 scripts/henoko_opening.py）
- docs/data/themes/henoko-student-accident.json : 件数・論点・立場・強い表現・主張の照合・資料にしかない話（公開JSON）
- configs/planet/henoko-student-accident.yaml   : 立場の色と並び、理由区分のある論点（sub_issues）
- data/henoko-student-accident_issues-reread.json : 理由区分（明細の bucket を数え直す）
- data/henoko-student-accident_reread-stances.json : 明細ごとの立場（post_key → 立場の名前）
- data/henoko-student-accident_claim_posts.json : 主張ごとの該当投稿（件数の照合だけに使う）
- data/verification/henoko-student-accident-background.json : 背景台帳（制度の確認が読む）
- configs/henoko-student-accident-background.json : 背景の開閉行（scripts/henoko_background.py が描く。設定に background_config があるときだけ）

出力: quality/prototypes/henoko-student-accident-reading/index.html
（同じフォルダーに reading.css・reading.js・opening.css の写しを置く。正本は scripts/henoko_redesign/）

基準日（--as-of）の既定は公開JSONの updated_on。今日の日付・乱数は使わない。件数・割合は手で書かない。
合計が公開JSONと合わなければ止まる。同じ入力なら出力は同じ。

    python3 scripts/henoko_reading.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from datetime import date, timedelta
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import henoko_opening as opening  # noqa: E402
from bukatsu_redesign.x_embeds import add_x_embeds  # noqa: E402

CONFIG = ROOT / "configs" / "henoko-student-accident-reading.json"
OUT_DIR = ROOT / "quality" / "prototypes" / "henoko-student-accident-reading"
ASSETS = opening.ASSETS  # scripts/henoko_redesign/
SECTION_ID = "henoko-student-accident-reading"
READING_START = "<!-- HENOKO_READING_START -->"
READING_END = "<!-- HENOKO_READING_END -->"
POST_URL = re.compile(r"^https://x\.com/[A-Za-z0-9_]+/status/(\d+)$")


def esc(value: object) -> str:
    return escape(str(value), quote=True)


def jp_date(iso: str, with_year: bool = True) -> str:
    d = date.fromisoformat(iso)
    return f"{d.year}年{d.month}月{d.day}日" if with_year else f"{d.month}月{d.day}日"


def fmt(n: int) -> str:
    return f"{int(n):,}"


def pct1(part: int, whole: int) -> str:
    return f"{part / whole * 100:.1f}" if whole else "0.0"


def read_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def post_key(tweet_id: str) -> str:
    """再読データの post_key は tweet_id の sha256（自転車・憲法と同じ）。"""
    return hashlib.sha256(str(tweet_id).encode()).hexdigest()


def dig(node, path: list[str]):
    for key in path:
        node = node[key]
    return node


# ---------------------------------------------------------------- データと照合


def load(config_path: Path = CONFIG) -> dict:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    octx = opening.load_inputs(ROOT / cfg["opening_config"])
    ocfg, public, planet = octx["config"], octx["public"], octx["planet"]
    octx["next_collect"] = octx["next_collect"] or None
    if public.get("theme_id") != cfg["theme_id"] or ocfg["theme_id"] != cfg["theme_id"]:
        raise SystemExit("設定と公開JSONのテーマが一致しません")
    if cfg["public_json"] != ocfg["inputs"]["public_json"]:
        raise SystemExit("冒頭と読書面で別の公開JSONを読もうとしています")
    raw = read_json(cfg["reread_json"])
    table = read_json(cfg["reread_stances_json"])
    if table["theme_id"] != cfg["theme_id"]:
        raise SystemExit("立場の対応表のテーマが違います")
    reread, items = {}, []
    for label, sub in (planet.get("sub_issues") or {}).items():
        if sub["file"] != cfg["reread_json"]:
            raise SystemExit(f"planet設定の理由区分 {label} が別のファイル {sub['file']} を指しています")
        if list(sub["path"]) != ["buckets", label] or label not in raw.get("buckets", {}):
            raise SystemExit(f"再読データに buckets.{label} がありません")
        field = sub.get("item_issue_field", "main_issue")
        rows = [{"post_key": i["post_key"], "bucket": i["bucket"], "main_issue": i[field],
                 "stance": table["stances"].get(i["post_key"])}
                for i in dig(raw, list(sub["items_path"])) if i[field] == label]
        reread[label] = {"buckets": raw["buckets"][label], "items": rows}
        items += rows
    # 理由区分のある論点に入っていない明細（planet 設定に無い論点の明細）が混じっていないか
    stray = {i["main_issue"] for i in raw.get("items", [])} - set(reread)
    if stray:
        raise SystemExit(f"再読データの明細に、planet 設定の sub_issues に無い論点があります: {stray}")
    # 立場の対応表は、再読データの明細とちょうど同じ投稿を持つ（追い読みの後に作り直し忘れると止まる）
    if set(table["stances"]) != {i["post_key"] for i in raw.get("items", [])}:
        raise SystemExit("立場の対応表と再読データの明細の投稿が一致しません。scripts/henoko_reread_stances.py を実行してください")
    excluded = {i["post_key"] for i in raw.get("excluded_items", [])}
    if excluded & set(table["stances"]):
        raise SystemExit("除外した明細が立場の対応表に入っています")
    d = {
        "cfg": cfg,
        "ocfg": ocfg,
        "octx": octx,
        "public": public,
        "planet": planet,
        "background": read_json(cfg["background_json"]),
        "reread": reread,
        "reread_items": items,
        "claim_posts": read_json(cfg["claim_posts_json"])["claims"],
    }
    if cfg.get("background_config"):
        import henoko_background as background_rows  # 背景の部品（手順6）

        d["bg"] = background_rows.load(d, ROOT / cfg["background_config"])
    return d


def stance_order(d: dict) -> list[dict]:
    """立場の並びは planet 設定の順（冒頭の件数欄の帯と同じ）。公開JSONの立場の種類と違えば止まる。"""
    style = [s for s in d["planet"]["stances"]]
    seen = {s["id"] for issue in d["public"]["issues"] for s in issue["stances"]}
    if seen != {s["id"] for s in style}:
        raise SystemExit(f"公開JSONの立場と planet 設定の立場が違います: {seen ^ {s['id'] for s in style}}")
    return style


def stance_id(d: dict, label: str | None) -> str | None:
    """再読データの立場の名前（planet 設定の key）を planet 設定の id に直す。"""
    table = {}
    for s in d["planet"]["stances"]:
        table[s["key"]] = s["id"]
        table[s["label"]] = s["id"]
    return table.get(label)


def item_stance(d: dict, item: dict) -> str | None:
    return stance_id(d, item["stance"])


def post_record(rr: dict, tweet_id: str) -> dict | None:
    key = post_key(tweet_id)
    return next((i for i in rr["items"] if i["post_key"] == key), None)


def post_stance(d: dict, issue: dict, post: dict) -> str | None:
    """代表投稿の立場。理由区分のある論点は明細の立場、無い論点は設定の stance_id（正典の立場）。"""
    rr = d["reread"].get(issue["label"])
    rec = post_record(rr, post["id"]) if rr else None
    return item_stance(d, rec) if rec else post.get("stance_id")


def sunk_issue(d: dict, sc: dict) -> str | None:
    over = d["cfg"].get("sunk_issue_overrides", {})
    if sc["nearest_issue_id"] and sc["id"] in over:
        raise SystemExit(f"資料にしかない話 {sc['id']} は公開JSONに論点があるので、sunk_issue_overrides は使えません")
    return sc["nearest_issue_id"] or over.get(sc["id"])


def issue_name(d: dict, issue: dict) -> str:
    return d["cfg"]["issues"].get(issue["id"], {}).get("name") or issue["label"]


def check_all(d: dict) -> None:
    """表示する数が公開JSONとずれていたら止める。"""
    public, cfg = d["public"], d["cfg"]
    opinion = int(public["opinion_count"])
    issues = public["issues"]
    ids = {i["id"] for i in issues}
    labels = {i["label"] for i in issues}
    if sum(int(i["count"]) for i in issues) != opinion:
        raise SystemExit("論点の合計が意見数と一致しません")
    stances = stance_order(d)
    stance_ids = [s["id"] for s in stances]
    if sum(int(s["count"]) for i in issues for s in i["stances"]) != opinion:
        raise SystemExit("立場の合計が意見数と一致しません")
    if cfg["trend"]["public_json_key"] in public:
        raise SystemExit("公開JSONに推移データが入りました。読書面の推移表示を作ってから生成してください")
    if set(d["reread"]) - labels:
        raise SystemExit(f"理由区分のある論点に、公開JSONに無い論点があります: {set(d['reread']) - labels}")
    keys = [i["post_key"] for i in d["reread_items"]]
    if len(keys) != len(set(keys)):
        raise SystemExit("再読データの明細に同じ投稿が重複しています")
    for issue in issues:
        n = int(issue["count"])
        if sorted(s["id"] for s in issue["stances"]) != sorted(stance_ids):
            raise SystemExit(f"{issue['id']}: 立場の種類が planet 設定と違います")
        if sum(int(s["count"]) for s in issue["stances"]) != n:
            raise SystemExit(f"{issue['id']}: 立場の合計が論点の件数と一致しません")
        if sum(int(x["count"]) for x in issue["intensities"]) != n:
            raise SystemExit(f"{issue['id']}: 強さの合計が論点の件数と一致しません")
        rr = d["reread"].get(issue["label"])
        if rr is None:
            continue  # 理由データが無い論点は「理由は未公開」と表示する
        buckets, items = rr["buckets"], rr["items"]
        if sum(int(b["count"]) for b in buckets.values()) != n:
            raise SystemExit(f"{issue['id']}: 理由区分の合計が論点の件数 {n} と一致しません")
        if len(items) != n:
            raise SystemExit(f"{issue['id']}: 再読データの明細 {len(items)} 件が論点の件数 {n} と一致しません")
        tally = Counter(i["bucket"] for i in items)
        for bid, b in buckets.items():
            if tally[bid] != int(b["count"]):
                raise SystemExit(f"{issue['id']}: 理由区分 {bid} の件数が明細と一致しません")
        if set(tally) - set(buckets):
            raise SystemExit(f"{issue['id']}: 明細に区分の定義が無い bucket があります")
        st = Counter(item_stance(d, i) for i in items)
        if set(st) - set(stance_ids):
            raise SystemExit(f"{issue['id']}: 再読データの明細に planet 設定に無い立場があります")
        if {s["id"]: int(s["count"]) for s in issue["stances"]} != {sid: st.get(sid, 0) for sid in stance_ids}:
            raise SystemExit(f"{issue['id']}: 再読データの明細の立場の内訳が公開JSONと一致しません"
                             "（判定し直しの後は再読データの stance を正典に合わせてください）")
    cv = public["claim_verification"]
    per_claim = {cid: len(set(tids)) for cid, tids in d["claim_posts"].items()}
    if any(len(set(tids)) != len(tids) for tids in d["claim_posts"].values()):
        raise SystemExit("照合データの同じ主張に、同じ投稿が2回入っています")
    if set(per_claim) != {c["id"] for c in cv["claims"]}:
        raise SystemExit("照合データの主張と公開JSONの主張が一致しません")
    for c in cv["claims"]:
        if c["verdict"] not in cfg["verdict_labels"]:
            raise SystemExit(f"主張 {c['id']} の判定 {c['verdict']} の言い換えが設定にありません")
        if set(c["issue_ids"]) - ids:
            raise SystemExit(f"主張 {c['id']} の論点が公開JSONにありません")
        if per_claim.get(c["id"]) != int(c["matched_post_count"]):
            raise SystemExit(f"主張 {c['id']} の該当投稿数 {c['matched_post_count']} が照合データの {per_claim[c['id']]} 件と違います")
    for sc in public["ocean_layer"]["sunk_continents"]:
        iid = sunk_issue(d, sc)
        if iid not in ids:
            raise SystemExit(f"資料にしかない話 {sc['id']} の論点 {iid} が公開JSONにありません")
        if int(sc["sns_base"]) != opinion:
            raise SystemExit(f"資料にしかない話 {sc['id']} の母数 {sc['sns_base']} が意見数 {opinion} と違います（再検索の記録を更新してください）")
    if set(cfg.get("sunk_issue_overrides", {})) - {sc["id"] for sc in public["ocean_layer"]["sunk_continents"]}:
        raise SystemExit("sunk_issue_overrides に公開JSONに無い項目があります")
    stance_labels = {s["label"] for s in stances}
    for v in public["ocean_layer"].get("veins", []):
        if set(v["issue_ids"]) - ids:
            raise SystemExit(f"共通する心配 {v['id']} の論点が公開JSONにありません")
        if {s["stance_label"] for s in v["sides"]} - stance_labels:
            raise SystemExit(f"共通する心配 {v['id']} の立場名が planet 設定にありません")
    if set(cfg.get("claim_finding_overrides", {})) - {c["id"] for c in cv["claims"]}:
        raise SystemExit("claim_finding_overrides に公開JSONに無い主張があります")
    for cid, over in cfg.get("claim_finding_overrides", {}).items():
        src = next(c for c in cv["claims"] if c["id"] == cid)["finding"]
        if over.get("public_finding") != src:
            raise SystemExit(f"主張 {cid} の照合文が公開JSONで変わりました。読書面の言い換えを見直してください")
    if set(cfg["issues"]) != ids:
        raise SystemExit(f"設定の論点と公開JSONの論点が一致しません: {set(cfg['issues']) ^ ids}")
    if date.fromisoformat(d["ocfg"]["checked_on"]) < date.fromisoformat(d["background"]["checked_on"]):
        raise SystemExit("冒頭の checked_on が背景台帳の確認日より古くなっています")
    check_ids = {c["id"] for c in d["background"]["checklist"]["items"]}
    for iid, icfg in cfg["issues"].items():
        issue = next(i for i in issues if i["id"] == iid)
        rr = d["reread"].get(issue["label"])
        buckets = rr["buckets"] if rr else {}
        extra = set(icfg.get("reasons", {})) - set(buckets)
        if extra:
            raise SystemExit(f"{iid}: 再読データに無い理由区分が設定にあります: {extra}")
        complete = icfg.get("status") == "complete"
        if complete and set(icfg.get("reasons", {})) != set(buckets):
            raise SystemExit(f"{iid}: 完成扱いの論点で、説明（voice）の無い理由区分があります")
        if complete and not all(r.get("voice") for r in icfg.get("reasons", {}).values()):
            raise SystemExit(f"{iid}: 完成扱いの論点で、voice が空の理由区分があります")
        if complete and not icfg.get("description"):
            raise SystemExit(f"{iid}: 完成扱いの論点に説明がありません")
        claims = {c["id"] for c in cv["claims"] if iid in c["issue_ids"]}
        if set(icfg.get("claim_notes", {})) - claims:
            raise SystemExit(f"{iid}: この論点に無い照合への注記があります")
        for cid in icfg.get("checks", []):
            if cid not in check_ids:
                raise SystemExit(f"{iid}: 制度の確認 {cid} が背景台帳の checklist にありません")
        if set(icfg.get("check_overrides", {})) - set(icfg.get("checks", [])):
            raise SystemExit(f"{iid}: 開いていない制度の確認に言い換えがあります")
        for link in icfg.get("see_also", []):
            if not link["href"].startswith("#"):
                raise SystemExit(f"{iid}: あわせて確かめるのリンクはページ内（#…）だけです")
        posts = icfg.get("posts", {}).get("items", [])
        if len(posts) > 2:
            raise SystemExit(f"{iid}: X投稿は最大2件です")
        if len({p["id"] for p in posts}) != len(posts):
            raise SystemExit(f"{iid}: 同じ投稿を2回選んでいます")
        if complete and posts and not icfg["posts"].get("selection_basis"):
            raise SystemExit(f"{iid}: 投稿の選定理由（selection_basis）がありません")
        if complete and len(posts) == 1 and not icfg["posts"].get("one_reason"):
            raise SystemExit(f"{iid}: 投稿が1件の理由（one_reason）がありません")
        for p in posts:
            m = POST_URL.match(p["url"])
            if not m or m.group(1) != p["id"]:
                raise SystemExit(f"{iid}: 投稿IDとURLが一致しません: {p['id']}")
            if rr is not None and post_record(rr, p["id"]) is None:
                raise SystemExit(f"{iid}: 投稿 {p['id']} は再読データでこの論点に入っていません")
            if rr is None and p.get("stance_id") not in stance_ids:
                raise SystemExit(f"{iid}: 再読データの無い論点の投稿 {p['id']} には stance_id（正典の立場）が要ります")
            if rr is not None and p.get("stance_id"):
                raise SystemExit(f"{iid}: 投稿 {p['id']} の立場は再読データの明細から読むので、stance_id は書かない")
        if len(posts) == 2 and len({post_stance(d, issue, p) for p in posts}) != 2 and not icfg["posts"].get("same_stance_reason"):
            raise SystemExit(f"{iid}: 投稿2件の立場が同じです（理由を same_stance_reason に書いてください）")
    # 他の論点の投稿を使い回していないか（論点をまたいで同じ投稿を出さない）
    all_posts = [p["id"] for c in cfg["issues"].values() for p in c.get("posts", {}).get("items", [])]
    if len(all_posts) != len(set(all_posts)):
        raise SystemExit("同じ投稿が2つの論点に選ばれています")


# ---------------------------------------------------------------- 読書面の部品


def ordered_issues(d: dict) -> list[dict]:
    """件数の多い順。「その他」は最後。0件の論点（いまは「その他」）はタブも欄も出さない。"""
    other = d["cfg"]["other_issue_id"]
    shown = [i for i in d["public"]["issues"] if int(i["count"]) > 0]
    return sorted(shown, key=lambda i: (i["id"] == other, -int(i["count"]), i["id"]))


def small_flag(d: dict, issue: dict) -> bool:
    """設定 small.threshold 未満の論点に「少数」の印を付ける（いまは該当なし。最少の論点も25件）。"""
    return int(issue["count"]) < int(d["cfg"]["small"]["threshold"])


def compact(d: dict) -> dict:
    """部活動型の圧縮で使う見出し・折りたたみの名前（設定 compact）。"""
    return d["cfg"]["compact"]


def fold(cls: str, summary: str, body: str, attrs: str = "") -> str:
    """JavaScriptが無くても開閉できる折りたたみ。初期状態は閉じる。"""
    return f'<details class="fr-fold {cls}"{attrs}><summary>{summary}</summary>{body}</details>'


def details_sources(items: list[dict], label: str) -> str:
    if not items:
        return ""
    rows = "".join(f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["name"])}</a>'
                   + (f'<span>{esc(s["location"])}</span>' if s.get("location") else "") + "</li>" for s in items)
    return f'<details class="fr-sources"><summary>{esc(label)}</summary><ul>{rows}</ul></details>'


def stance_bar(d: dict, counts: dict, total: int, cls: str = "fr-band") -> str:
    """立場の帯。色は planet 設定（冒頭の帯と同じ）。"""
    segs = "".join(f'<i style="width:{counts.get(s["id"], 0) / total * 100:.2f}%;background:{s["color"]}"></i>'
                   for s in stance_order(d) if total)
    aria = "、".join(f'{s["label"]} {fmt(counts.get(s["id"], 0))}件' for s in stance_order(d))
    return f'<span class="{cls}" role="img" aria-label="{esc(aria)}">{segs}</span>'


def stance_words(d: dict, counts: dict) -> str:
    """件数のある立場だけを、多い順に「名前N件」で並べる（同数は planet 設定の順）。"""
    order = {s["id"]: k for k, s in enumerate(stance_order(d))}
    rows = sorted((s for s in stance_order(d) if counts.get(s["id"], 0)), key=lambda s: (-counts[s["id"]], order[s["id"]]))
    return "・".join(f'{s["label"]}{fmt(counts[s["id"]])}件' for s in rows)


def render_head_stance(d: dict, issue: dict) -> str:
    """論点の見出しの下の立場は1文だけ（冒頭と同じく、立場の帯を主役にしない）。帯は折りたたみの立場別集計の中に置く。"""
    sc = d["cfg"]["stance_common"]
    by = {s["id"]: int(s["count"]) for s in issue["stances"]}
    n = int(issue["count"])
    top = max(stance_order(d), key=lambda s: by[s["id"]])
    key = "head_all" if by[top["id"]] == n else "head"
    text = sc[key].format(stances=stance_words(d, by), top=top["label"], pct=round(by[top["id"]] / n * 100) if n else 0)
    return f'<p class="fr-head-stance" data-stance-note>{esc(text)}{esc(sc["caveat"])}</p>'


def render_stance(d: dict, issue: dict) -> str:
    """立場別集計（割合・数え方の注記）。部活動と同じく折りたたむ。"""
    sc = d["cfg"]["stance_common"]
    n = int(issue["count"])
    by = {s["id"]: int(s["count"]) for s in issue["stances"]}
    items = "".join(f'<li><span class="fr-sw" style="background:{s["color"]}"></span>{esc(s["label"])}'
                    f'<b>{fmt(by[s["id"]])}</b>件<small>{pct1(by[s["id"]], n)}%</small></li>' for s in stance_order(d))
    body = (f'<p class="fr-fold-title">{esc(sc["title"])}</p>'
            f'<p class="fr-lead">{esc(sc["lead"].format(count=fmt(n)))}</p>'
            + stance_bar(d, by, n) + f'<ul class="fr-stance-list">{items}</ul>'
            f'<p class="fr-fine">{esc(sc["note"])}</p>')
    return fold("fr-block fr-stance", esc(compact(d)["stance_fold"]), body)


def render_cumulative(d: dict, issue: dict) -> str:
    """前回の収集と比べた、この論点の割合（生成AIの render_glance と同じ型）。小さな折れ線と数字2つは、公開ページの組み立て
    （手順7で作る）が元HTMLの潮目のカード（前回と今回の収集の比較）から .fr-glance-chart に入れる。
    最新の累計の表は折りたたむ。"""
    t, c = d["cfg"]["trend"], compact(d)
    public = d["public"]
    period = public["collection_period"]
    row = t["row_label"].format(period_start=jp_date(period["start"]), period_end=jp_date(period["end"], False))
    n, total = int(issue["count"]), int(public["opinion_count"])
    table = ('<table><thead><tr><th scope="col">収集</th><th scope="col">件数</th>'
             '<th scope="col">意見全体に占める割合</th></tr></thead>'
             f'<tbody><tr><th scope="row">{esc(row)}</th><td>{fmt(n)}件</td>'
             f'<td>{pct1(n, total)}%<small>（{fmt(total)}件中）</small></td></tr></tbody></table>'
             f'<p class="fr-fine">{esc(t["note"])}</p>')
    return (f'<section class="fr-block fr-glance fr-trend" data-glance="{esc(issue["label"])}">'
            f'<p class="fr-eyebrow fr-glance-head">{esc(c["glance_eyebrow"])}'
            f'<a class="fr-glance-link" href="#{esc(t["widget_id"])}" data-tide-mode="issue">{esc(c["glance_link"])}</a></p>'
            '<div class="fr-glance-chart"></div>'
            + fold("fr-glance-table", esc(t["title"]), f'<p class="fr-fine fr-glance-note">{esc(c["glance_note"])}</p>' + table)
            + "</section>")


def ordered_reasons(d: dict, issue: dict, icfg: dict) -> list[tuple[str, dict]]:
    rr = d["reread"].get(issue["label"])
    if not rr:
        return []
    voices = icfg.get("reasons", {})
    items = list(rr["buckets"].items())
    if icfg.get("reason_sort", "count_desc") == "config" and voices:
        order = list(voices)
        items.sort(key=lambda kv: order.index(kv[0]) if kv[0] in order else len(order))
    else:
        items.sort(key=lambda kv: (-int(kv[1]["count"]), kv[0]))
    return items


def reason_label(d: dict, icfg: dict, bid: str, bucket: dict) -> str:
    # 表示名の言い換えは冒頭の設定 count.reason_label_overrides の1か所（冒頭の理由一覧と同じ名前にする）
    shared = d["ocfg"]["count"].get("reason_label_overrides", {}).get(bid, bucket["label"])
    return icfg.get("reasons", {}).get(bid, {}).get("label_override", shared)


def render_reasons(d: dict, issue: dict, icfg: dict) -> str:
    """理由一覧：理由名と件数の1行ずつ。上位 top_reasons 件だけ見せ、残りは「ほかの理由を読む」の折りたたみ。"""
    rc, c = d["cfg"]["reasons_common"], compact(d)
    n = int(issue["count"])
    iid = issue["id"]
    items = ordered_reasons(d, issue, icfg)
    if not items:
        return (f'<section class="fr-block fr-reasons is-unpublished"><h4>{esc(rc["title"])}</h4>'
                f'<p class="fr-empty" data-unpublished>{esc(rc["unpublished"])}</p></section>')
    top = int(c["top_reasons"])
    complete = icfg.get("status") == "complete"

    def row(i: int, bid: str, b: dict) -> str:
        cnt = int(b["count"])
        name = (f'<span class="fr-reason-name">{esc(reason_label(d, icfg, bid, b))}</span>'
                f'<span class="fr-reason-n"><b>{fmt(cnt)}</b>件<small>{pct1(cnt, n)}%</small></span>')
        if not complete:  # 説明が無い論点では、行を押しても開くものが無い
            return f'<li class="fr-reason" data-reason="{esc(bid)}"><span class="fr-reason-pick">{name}</span></li>'
        current = ' aria-current="true"' if i == 0 else ""
        return (f'<li class="fr-reason" data-reason="{esc(bid)}"><a class="fr-reason-pick" href="#fr-r-{esc(iid)}-{esc(bid)}" '
                f'data-reason-pick="{esc(bid)}"{current}>{name}</a></li>')

    out = [f'<section class="fr-block fr-reasons"><h4>{esc(c["reasons_index_title"].format(k=len(items)))}</h4>'
           f'<p class="fr-lead">{esc(rc["title"])}</p>',
           '<ol class="fr-reason-list">' + "".join(row(i, bid, b) for i, (bid, b) in enumerate(items[:top])) + "</ol>"]
    rest = items[top:]
    method = f'<p class="fr-fine">{esc(rc["lead"].format(count=fmt(n)))}{esc(rc["note"].format(count=fmt(n)))}</p>'
    if rest:
        out.append(fold("fr-reason-more", esc(c["reasons_more"].format(k=len(rest))),
                        f'<ol class="fr-reason-list" start="{top + 1}">'
                        + "".join(row(top + i, bid, b) for i, (bid, b) in enumerate(rest)) + "</ol>" + method))
    else:
        out.append(method)
    out.append("</section>")
    return "".join(out)


def render_reason_details(d: dict, issue: dict, icfg: dict) -> str:
    """選んだ理由の説明（どんな声か・立場の内訳）。JavaScriptが動くときは1つだけ見せる（最初は件数1位）。"""
    rc, c = d["cfg"]["reasons_common"], compact(d)
    items = ordered_reasons(d, issue, icfg)
    if not items:
        return ""
    rr = d["reread"][issue["label"]]
    n, iid = int(issue["count"]), issue["id"]
    out = ['<div class="fr-reason-reading">']
    for i, (bid, b) in enumerate(items):
        cnt = int(b["count"])
        st = Counter(item_stance(d, x) for x in rr["items"] if x["bucket"] == bid)
        st_text = stance_words(d, st)
        voice = icfg.get("reasons", {}).get(bid, {}).get("voice")
        nb, nxt = items[(i + 1) % len(items)]
        out.append(f'<article class="fr-reason-detail" id="fr-r-{esc(iid)}-{esc(bid)}" data-reason="{esc(bid)}"'
                   f'{" data-on" if i == 0 else ""}><p class="fr-eyebrow">{esc(c["reason_eyebrow"])}'
                   f'<span>{fmt(cnt)}件・{pct1(cnt, n)}%</span></p><h5>{esc(reason_label(d, icfg, bid, b))}</h5>')
        if voice:
            out.append(f'<p class="fr-voice"><span>{esc(rc["voice_label"])}</span>{esc(voice)}</p>')
        out.append(f'<p class="fr-reason-stance"><span>{esc(rc["stance_label"])}：{esc(st_text)}</span></p>')
        if len(items) > 1:
            out.append(f'<p class="fr-next"><span>{esc(c["reason_next"])}</span>'
                       f'<a href="#fr-r-{esc(iid)}-{esc(nb)}" data-reason-pick="{esc(nb)}">'
                       f'{esc(reason_label(d, icfg, nb, nxt))} →</a></p>')
        out.append("</article>")
    out.append("</div>")
    return "".join(out)


def render_posts(d: dict, issue: dict, icfg: dict) -> str:
    pc = d["cfg"]["posts_common"]
    posts = icfg.get("posts", {}).get("items", [])
    if not posts:
        return (f'<section class="fr-block fr-posts"><h4>{esc(pc["title"])}</h4>'
                f'<p class="fr-empty">{esc(pc["none"])}</p></section>')
    rr = d["reread"].get(issue["label"])
    stances = {s["id"]: s for s in stance_order(d)}
    same = len(posts) == 2 and len({post_stance(d, issue, p) for p in posts}) == 1
    lead = pc["lead_one"] if len(posts) == 1 else pc["lead_same"] if same else pc["lead_two"]
    out = [f'<p class="fr-fold-title">{esc(pc["title"])}</p><p class="fr-lead">{esc(lead)}</p>']
    if len(posts) == 1 and icfg["posts"].get("one_reason"):
        out.append(f'<p class="fr-fine">{esc(icfg["posts"]["one_reason"])}</p>')
    if same:  # 立場が同じ2件は、理由を必ず見せる（check_all が same_stance_reason の無い組を止める）
        out.append(f'<p class="fr-fine" data-same-stance>{esc(icfg["posts"]["same_stance_reason"])}</p>')
    out.append('<ul class="fr-post-list">')
    for p in posts:
        rec = post_record(rr, p["id"]) if rr else None
        meta = []
        if rec:
            meta.append(f'{pc["bucket_label"]}：{reason_label(d, icfg, rec["bucket"], rr["buckets"][rec["bucket"]])}')
        st = stances.get(post_stance(d, issue, p))
        if st:
            meta.append(f'{pc["stance_label"]}：{st["label"]}')
        out.append(f'<li class="fr-post"><p class="fr-post-label">{esc(p["label"])}</p><p>{esc(p["summary"])}</p>'
                   + (f'<p class="fr-fine">{esc("／".join(meta))}</p>' if meta else "") + "</li>")
    out.append("</ul>")
    links = "".join(f'<a href="{esc(p["url"])}">{esc(p["label"])}</a>' for p in posts)
    out.append(f'<details class="original-posts"><summary>{esc(pc["summary"].format(n=len(posts)))}</summary>{links}</details>')
    return fold("fr-block fr-posts", esc(compact(d)["posts_fold"].format(n=len(posts))), "".join(out))


def render_evidence(d: dict, issue: dict, icfg: dict) -> str:
    """根拠にあたる：主張の照合・条文の確認・資料にしかない話・共通する心配・制度の確認。
    部活動と同じく、1件ずつ見出し（と判定ラベル）だけを見せる折りたたみにする。"""
    s = d["cfg"]["sources_common"]
    iid = issue["id"]
    cv = d["public"]["claim_verification"]
    claims = [c for c in cv["claims"] if iid in c["issue_ids"]]
    out = [f'<section class="fr-block fr-evidence"><h4>{esc(compact(d)["evidence_title"])}</h4>'
           + fold("fr-evidence-about", esc(s["title"]), f'<p class="fr-lead">{esc(s["lead"])}</p>')]
    for c in claims:
        lab = d["cfg"]["verdict_labels"][c["verdict"]]
        note = icfg.get("claim_notes", {}).get(c["id"])
        finding = d["cfg"].get("claim_finding_overrides", {}).get(c["id"], {}).get("finding", c["finding"])
        body = (f'<p class="fr-eyebrow">{esc(s["claim_eyebrow"])}<span>{esc(s["checked"].format(checked_on=jp_date(cv["checked_on"])))}</span></p>'
                f'<p>{esc(finding)}</p>'
                + (f'<p class="fr-fine">{esc(note)}</p>' if note else "")
                + f'<p class="fr-fine">{esc(s["matched"].format(n=fmt(c["matched_post_count"])))}</p>'
                + details_sources(c["sources"], s["sources_label"]))
        out.append(fold(f'fr-claim fr-verdict-{esc(c["verdict"])}',
                        f'<span class="fr-sum-text">「{esc(c["claim"])}」</span><span class="fr-verdict">{esc(lab)}</span>',
                        body, f' data-claim="{esc(c["id"])}"'))
    sunk = [x for x in d["public"]["ocean_layer"]["sunk_continents"] if sunk_issue(d, x) == iid]
    if sunk:
        sk = d["cfg"]["sunk_common"]
        # 辺野古は安全管理の論点に4件が集まるので、見出しごと1つの折りたたみにまとめる（375pxで論点の欄を2,500px以下に保つ）
        out.append(f'<details class="fr-fold fr-sunk" data-sunk-group><summary><span class="fr-sum-text">'
                   f'{esc(compact(d)["sunk_fold"].format(title=sk["title"], n=len(sunk)))}</span></summary>')
        for x in sunk:
            srcs = [{"name": s2["name"], "url": s2["url"], "location": s2.get("location")} for s2 in x["sources"]]
            body = (f'<p>{esc(x["life_impact"])}</p>'
                    f'<p class="fr-fine">{esc(sk["count"].format(base=fmt(x["sns_base"]), n=fmt(x["sns_count"]), checked_on=jp_date(x["checked_on"])))}</p>'
                    f'<details class="fr-sources"><summary>{esc(sk["note_label"])}</summary>{sns_note_html(sk, x["sns_note"])}</details>'
                    + details_sources(srcs, s["sources_label"]))
            out.append(fold("fr-sunk-item", f'<span class="fr-sum-text">{esc(x["topic"])}</span>', body,
                            f' data-sunk="{esc(x["id"])}"'))
        out.append("</details>")
    veins = [v for v in d["public"]["ocean_layer"].get("veins", []) if iid in v["issue_ids"]]
    if veins:
        vc = d["cfg"]["veins_common"]
        out.append(f'<div class="fr-veins"><p class="fr-eyebrow">{esc(vc["title"])}</p>')
        for v in veins:
            sides = "・".join(f'{x["stance_label"]}{fmt(x["post_count"])}件' for x in v["sides"])
            body = (f'<p><b>{esc(vc["diverging_label"])}</b>{esc(v["diverging_reason"])}</p>'
                    f'<p class="fr-fine">{esc(vc["sides"].format(sides=sides, checked_on=jp_date(v["checked_on"])))}</p>')
            out.append(fold("fr-vein", f'<span class="fr-sum-text"><b>{esc(vc["shared_label"])}</b>{esc(v["shared_concern"])}</span>',
                            body, f' data-vein="{esc(v["id"])}"'))
        out.append("</div>")
    checks = render_checks(d, issue, icfg)
    if not claims and not sunk and not veins and not icfg.get("checks"):
        out.append(f'<p class="fr-empty">{esc(s["empty"])}</p>')
    out.append(checks)
    out.append("</section>")
    return "".join(out)


RECHECK = re.compile(r"\((\d{4}-\d{2}-\d{2})再確認[:：]\s*([^)]*)\)")


def sns_note_html(sk: dict, note: str) -> str:
    """公開JSONの sns_note は本文の後ろに「(YYYY-MM-DD再確認: …)」の履歴がつながった1文になっている。
    文が長くなりすぎるので、表示だけ本文と再確認の履歴に分けて並べる（中身は変えない）。"""
    rechecks = RECHECK.findall(note)
    main = RECHECK.sub("", note).strip()
    if main and main[-1] not in "。」":
        main += "。"
    out = f'<p class="fr-fine">{esc(main)}</p>'
    if rechecks:
        out += '<ul class="fr-rechecks">' + "".join(
            f'<li>{esc(sk["recheck"].format(when=jp_date(w), text=txt.strip().rstrip("。")))}</li>' for w, txt in rechecks) + "</ul>"
    return out


def render_checks(d: dict, issue: dict, icfg: dict) -> str:
    """制度の確認（背景台帳 checklist のうち、設定 issues[].checks でこの論点に割り当てた項目）。問いだけを見せる折りたたみ。
    台帳の項目は論点を持たないので、割り当ては設定に持つ（台帳は現行ページと共有なので変えない）。確認日は台帳の checked_on。
    報告書の公表の有無と公的機関の公表の一覧は論点ごとに繰り返さず、最後に背景の行（#bg-official）への1行のリンクを置く。"""
    s = d["cfg"]["sources_common"]
    bg = d["background"]
    by = {c["id"]: c for c in bg["checklist"]["items"]}
    out = [f'<div class="fr-checks"><p class="fr-eyebrow">{esc(s["check_eyebrow"])}</p>']
    for cid in icfg.get("checks", []):
        c = by[cid]
        over = icfg.get("check_overrides", {}).get(cid, {})
        ask = over.get("ask", c["ask"])
        found = over.get("found", c["found"])  # 台帳の文を読書面だけ言い換える（理由は設定の _check_overrides）
        body = (f'<p class="fr-eyebrow">{esc(c["label"])}'
                f'<span>{esc(s["ledger_checked"].format(checked_on=jp_date(bg["checked_on"])))}</span></p>'
                f'<p>{esc(found)}</p>' + details_sources(c["sources"], s["sources_label"]))
        out.append(fold("fr-check", f'<span class="fr-sum-text">{esc(ask)}</span>', body, f' data-check="{esc(cid)}"'))
    out.append(f'<p class="fr-national"><a href="{esc(s["official_href"])}">{esc(s["official"])} →</a></p>')
    out.append("</div>")
    return "".join(out)


def render_see_also(d: dict, icfg: dict) -> str:
    links = icfg.get("see_also", [])
    if not links:
        return ""
    items = "".join(f'<li><a href="{esc(l["href"])}">{esc(l["text"])}</a></li>' for l in links)
    return (f'<section class="fr-block fr-see"><h4>{esc(d["cfg"]["see_also_common"]["title"])}</h4>'
            f'<ul>{items}</ul></section>')


def render_panel(d: dict, issue: dict, selected: str, rank: int) -> str:
    cfg, public, c = d["cfg"], d["public"], compact(d)
    iid = issue["id"]
    icfg = cfg["issues"].get(iid, {})
    n, total = int(issue["count"]), int(public["opinion_count"])
    name = issue_name(d, issue)
    complete = icfg.get("status") == "complete"
    k = len(ordered_issues(d))
    rank_text = c["rank_first"].format(k=k) if rank == 1 else c["rank_other"].format(k=k, rank=rank)
    out = [f'<section class="fr-panel issue-panel{" is-complete" if complete else " is-pending"}" id="issue-{esc(iid)}" '
           f'data-issue-panel="{esc(iid)}" aria-labelledby="fr-h-{esc(iid)}"{" data-selected" if iid == selected else ""}>',
           '<header class="fr-panel-head"><div>'
           f'<p class="fr-eyebrow">選んだ論点<span>分類名「{esc(issue["label"])}」</span></p>'
           f'<h3 id="fr-h-{esc(iid)}" tabindex="-1">{esc(name)}'
           + (f'<em class="fr-small" data-small>{esc(d["cfg"]["small"]["tag"])}</em>' if small_flag(d, issue) else "")
           + '</h3>']
    paras = icfg.get("description", [])
    # 論点の説明は1段落目だけを見せ、2段落目からは「くわしく」の折りたたみ
    for para in paras[:1]:
        out.append(f'<p class="fr-desc">{esc(para)}</p>')
    if iid == cfg["other_issue_id"]:
        out.append(render_other_note(d, issue))
    if len(paras) > 1:
        out.append(fold("fr-desc-more", esc(c["desc_more"]), "".join(f'<p class="fr-desc">{esc(p)}</p>' for p in paras[1:])))
    out.append(f'</div><p class="fr-count"><b>{fmt(n)}</b><span>件</span>'
               f'<small>{esc(c["count_caption"].format(total=fmt(total), pct=pct1(n, total)))}{esc(rank_text)}</small></p>'
               + (f'<p class="fr-small-note">{esc(c["small_note"].format(threshold=d["cfg"]["small"]["threshold"]))}</p>'
                  if small_flag(d, issue) else "")
               + render_head_stance(d, issue)
               + f'<p class="fr-back"><a href="#{SECTION_ID}">{esc(c["back"])}</a></p></header>')
    if not complete:
        out.append(f'<p class="fr-pending">{esc(cfg["pending_note"])}</p>')
        out.append(render_reasons(d, issue, icfg))
        out.append(render_stance(d, issue))
        out.append("</section>")
        return "".join(out)
    out.append('<div class="fr-grid"><div class="fr-main">')
    out.append(render_reasons(d, issue, icfg))
    out.append(render_reason_details(d, issue, icfg))
    out.append(render_stance(d, issue))
    out.append(render_cumulative(d, issue))
    out.append(render_posts(d, issue, icfg))
    out.append('</div><div class="fr-side">')
    out.append(render_evidence(d, issue, icfg))  # 制度の確認（render_checks）もこの中に入る
    out.append(render_see_also(d, icfg))
    out.append("</div></div></section>")
    return "".join(out)


def render_other_note(d: dict, issue: dict) -> str:
    """「その他」の見出しの下の1文。最も多い理由区分とその割合を、冒頭の「その他」の中身と同じ数え方で出す。"""
    rr = d["reread"].get(issue["label"])
    if not rr or not d["cfg"].get("other_note"):
        return ""  # 「その他」に理由区分が無いうちは出さない（再読データに加われば設定の other_note で出せる）
    bid, b = sorted(rr["buckets"].items(), key=lambda kv: (-int(kv[1]["count"]), kv[0]))[0]
    share = round(int(b["count"]) / int(issue["count"]) * 100)
    text = d["cfg"]["other_note"].format(top=b["label"], share=share)
    return f'<p class="fr-desc fr-other-note" data-other-top="{esc(bid)}">{esc(text)}</p>'


def render_tabs(d: dict, issues: list[dict], selected: str) -> str:
    """論点タブ（論点名＋件数）。アイコンは付けない（planet 設定の浮き輪などは、冒頭で避けた船・海の図柄に当たる）。
    読書面の上で論点を切り替える（山なみは手順7で上に入る）。"""
    other = d["cfg"]["other_issue_id"]
    on = ' aria-current="true"'
    items = "".join(
        f'<li><a class="fr-tab{" is-other" if i["id"] == other else ""}" href="#issue-{esc(i["id"])}" data-issue-id="{esc(i["id"])}"'
        f'{on if i["id"] == selected else ""}>'
        f'{esc(issue_name(d, i))}'
        f'<small>{fmt(i["count"])}{"・" + esc(d["cfg"]["small"]["tag"]) if small_flag(d, i) else ""}</small></a></li>'
        for i in issues)
    return f'<nav class="fr-tabs" aria-label="{esc(compact(d)["tabs_label"])}"><ul>{items}</ul></nav>'


def render_note(d: dict) -> str:
    """意見が少ないことと、収集期間の翌日以降は未収集であることの注記（冒頭の件数欄と同じ日付の作り方）。"""
    public = d["public"]
    after = date.fromisoformat(public["collection_period"]["end"]) + timedelta(days=1)
    nxt = d["octx"]["next_collect"]
    text = d["cfg"]["section"]["note"].format(total=fmt(public["opinion_count"]), after=jp_date(after.isoformat(), False),
                                              next=jp_date(nxt, False) if nxt else "未定")
    return f'<p class="fr-note" data-after="{esc(after.isoformat())}">{esc(text)}</p>'


def render_reading(d: dict) -> str:
    cfg = d["cfg"]
    sec = cfg["section"]
    issues = ordered_issues(d)
    completes = [i["id"] for i in issues if cfg["issues"][i["id"]].get("status") == "complete"]
    selected = completes[0] if completes else issues[0]["id"]
    out = [READING_START, f'<section class="fr" id="{SECTION_ID}" aria-labelledby="fr-title" '
           f'data-default-issue="{esc(selected)}">', '<header class="fr-head">',
           f'<p class="fr-eyebrow">{esc(sec["eyebrow"])}</p><h2 id="fr-title">{esc(sec["title"])}</h2>',
           f'<p class="fr-lead">{esc(sec["lead"])}</p>{render_note(d)}<p class="fr-live" aria-live="polite" id="fr-live"></p></header>',
           '<div class="fr-panels">', render_tabs(d, issues, selected)]
    ranks = {i["id"]: r for r, i in enumerate(sorted(issues, key=lambda i: (-int(i["count"]), i["id"])), 1)}
    # 既定の論点を先頭に置く（JavaScriptなしで最初に読めるように）。残りは件数順（その他は最後）。
    for issue in sorted(issues, key=lambda i: i["id"] != selected):
        out.append(render_panel(d, issue, selected, ranks[issue["id"]]))
    out.append("</div>")
    out.append(f'<p class="fr-footer">{esc(cfg["footer"].format(updated_on=jp_date(d["public"]["updated_on"])))}</p>')
    out.append("</section>")
    out.append(READING_END)
    return "\n".join(out) + "\n"


def default_as_of(d: dict) -> str:
    """基準日の既定は公開JSONの更新日（今日の日付は使わない）。"""
    return d["public"]["updated_on"]


def render_page(d: dict, as_of: str) -> str:
    fragment = opening.fragment_for(ROOT / d["cfg"]["opening_config"])
    reading = render_reading(d)
    bg = ""
    if "bg" in d:
        import henoko_background as background_rows

        bg = background_rows.render(d, as_of, ordered_issues(d))
    title = "辺野古の転覆事故・論点の読書面" + ("と背景" if bg else "") + "の試作"
    page = (
        "<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{esc(title)}</title>\n<meta name=\"robots\" content=\"noindex\">\n"
        "<link rel=\"stylesheet\" href=\"opening.css\">\n"
        "<link rel=\"stylesheet\" href=\"reading.css\">\n"
        "<script src=\"reading.js\" defer></script>\n</head>\n<body>\n"
        "<header class=\"fr-site\"><a href=\"#\" class=\"fr-logo\">SNS反応まっぷ</a>"
        f"<span>{esc(title)}（基準日 {esc(as_of)}）</span></header>\n"
        f"<main id=\"main\" data-as-of=\"{esc(as_of)}\">\n<div class=\"hop-page\">" + fragment + "</div>\n" + reading + bg + "</main>\n</body>\n</html>\n"
    )
    return add_x_embeds(page)


def build(out_dir: Path = OUT_DIR, as_of: str | None = None, config: Path = CONFIG) -> Path:
    d = load(config)
    check_all(d)
    as_of = as_of or default_as_of(d)
    date.fromisoformat(as_of)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "index.html"
    out.write_text(render_page(d, as_of), encoding="utf-8")
    for name in ("reading.css", "reading.js", "opening.css"):
        shutil.copyfile(ASSETS / name, out_dir / name)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=CONFIG)
    ap.add_argument("--as-of", help="基準日 YYYY-MM-DD（既定は公開JSONの updated_on）")
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    try:
        print(f"wrote {build(args.out_dir, args.as_of, args.config)}")
    except KeyError as exc:
        raise SystemExit(f"エラー: 設定に {exc} がありません")


if __name__ == "__main__":
    main()
