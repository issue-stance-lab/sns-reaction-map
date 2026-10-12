#!/usr/bin/env python3
"""憲法改正論議ページの「論点ごとの読書面」を、冒頭の試作の下につないで生成する試作。

生成AI（scripts/ai_copyright_reading.py）の部活動型の圧縮済みの型で、最初から作る。テーマごとに違うのは設定JSONと次の点。
- 山なみは作らない。公開ページでは手順7で元HTMLの対話式の山なみ（#planet-block）を写すので、読書面は論点タブから始める。
- 立場は「慎重・反対／改正推進／中立／手続き重視」の4つ。並びは公開JSONの立場の合計が多い順（冒頭の帯と同じ）、色は planet 設定。
- 再読データの明細は post_key（tweet_id の sha256）と理由区分だけを持ち、立場を持たない。区分ごとの立場と代表投稿の立場は、
  正典から写した対応表 data/constitutional-amendment_reread-stances.json（scripts/constitutional_reread_stances.py）から数える。
  明細と対応表の投稿が一致しないか、論点×立場の合計が公開JSONと違えば止まる。非公開の正典は読まない。
- 公開JSONの「資料にしかない話」のうち論点が null の項目は、設定 sunk_issue_overrides で論点に置く。

入力
- configs/constitutional-amendment-reading.json  : 論点の説明・理由の言い換え・照合の注記・投稿の選定（手書き文言）
- configs/constitutional-amendment-opening.json  : 冒頭の文言と制度の確認日（冒頭部品 scripts/constitutional_opening.py をそのまま使う）
- docs/data/themes/constitutional-amendment.json : 件数・論点・立場・強い表現・主張の照合・資料にしかない話・共通する心配（公開JSON）
- configs/planet/constitutional-amendment.yaml   : 立場の色、論点のアイコン、理由区分のある論点（sub_issues）
- data/constitutional-amendment_issues-reread.json : 理由区分（7論点すべて。明細の bucket を数え直す）
- data/constitutional-amendment_reread-stances.json : 明細ごとの立場
- data/constitutional-amendment_claim_posts.json : 主張ごとの該当投稿（件数の照合だけに使う）
- data/verification/constitutional-amendment-background.json : 制度の確認（checklist）
- quality/research/constitutional-amendment-primary-sources.md : 一次資料メモ（資料の確認日）
- configs/constitutional-amendment-background.json : 背景の開閉行（scripts/constitutional_background.py が描く。設定に background_config があるときだけ）

出力: quality/prototypes/constitutional-amendment-reading/index.html
（同じフォルダーに reading.css・reading.js・opening.css の写しを置く。正本は scripts/constitutional_redesign/）

基準日（--as-of）の既定は公開JSONの updated_on。今日の日付・乱数は使わない。件数・割合は手で書かない。
合計が公開JSONと合わなければ止まる。同じ入力なら出力は同じ。

    python3 scripts/constitutional_reading.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from collections import Counter
from datetime import date
from html import escape
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import constitutional_opening as opening  # noqa: E402
from bukatsu_redesign.x_embeds import add_x_embeds  # noqa: E402

CONFIG = ROOT / "configs" / "constitutional-amendment-reading.json"
OUT_DIR = ROOT / "quality" / "prototypes" / "constitutional-amendment-reading"
ASSETS = opening.ASSETS
SECTION_ID = "constitutional-amendment-reading"
READING_START = "<!-- CONSTITUTIONAL_READING_START -->"
READING_END = "<!-- CONSTITUTIONAL_READING_END -->"
DATE_RE = re.compile(r"確認日[:：]\s*(\d{4}-\d{2}-\d{2})")
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
    """再読データの post_key は tweet_id の sha256（皇室と同じ）。本文を持たずに論点と理由区分を引ける。"""
    return hashlib.sha256(str(tweet_id).encode()).hexdigest()


# ---------------------------------------------------------------- 一次資料メモ


class Memo:
    """一次資料メモを見出しで引く。確認日は節の中の「確認日：YYYY-MM-DD」の最新を使う（生成AI・皇室と同じ読み方）。"""

    def __init__(self, path: Path):
        self.text = path.read_text(encoding="utf-8")
        self.lines = self.text.splitlines()

    def section(self, heading: str) -> str:
        hits = [i for i, l in enumerate(self.lines) if re.match(r"#{2,3} ", l) and heading in l]
        if len(hits) != 1:
            raise SystemExit(f"一次資料メモで見出し「{heading}」が {len(hits)} 件あります（1件だけのはず）")
        start = hits[0]
        level = len(self.lines[start]) - len(self.lines[start].lstrip("#"))
        end = next((j for j in range(start + 1, len(self.lines))
                    if re.match(r"#{1,%d} " % level, self.lines[j])), len(self.lines))
        return "\n".join(self.lines[start:end])

    def checked_on(self, heading: str) -> str:
        dates = DATE_RE.findall(self.section(heading))
        if not dates:
            raise SystemExit(f"一次資料メモの「{heading}」に確認日がありません")
        return max(dates)

    def latest(self) -> str:
        return max(DATE_RE.findall(self.text))

    def has_ref(self, ref: str) -> bool:
        """「確認できなかったこと 5」は節の中の番号付きの項目、それ以外は見出し。"""
        m = re.fullmatch(r"(.+?) (\d+)", ref)
        if m:
            body = self.section(m.group(1))
            return re.search(rf"^{m.group(2)}\. ", body, flags=re.M) is not None
        self.section(ref)
        return True


# ---------------------------------------------------------------- データと照合


def load(config_path: Path = CONFIG) -> dict:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    ocfg, public, planet, background = opening.load_inputs(ROOT / cfg["opening_config"])
    if public.get("theme_id") != cfg["theme_id"] or ocfg["theme_id"] != cfg["theme_id"]:
        raise SystemExit("設定と公開JSONのテーマが一致しません")
    if cfg["public_json"] != ocfg["inputs"]["public_json"]:
        raise SystemExit("冒頭と読書面で別の公開JSONを読もうとしています")
    if cfg["background_json"] != ocfg["inputs"]["background_json"]:
        raise SystemExit("冒頭と読書面で別の背景台帳を読もうとしています")
    raw = read_json(cfg["reread_json"])
    reread = {}
    for label, sub in (planet.get("sub_issues") or {}).items():
        if sub["file"] != cfg["reread_json"]:
            raise SystemExit(f"planet設定の理由区分 {label} が別のファイル {sub['file']} を指しています")
        if list(sub["path"]) != ["buckets", label] or label not in raw["buckets"]:
            raise SystemExit(f"再読データに buckets.{label} がありません")
        reread[label] = {"buckets": raw["buckets"][label],
                         "items": [i for i in raw["items"] if i.get("main_issue") == label]}
    stances = read_json(cfg["stances_json"])
    d = {
        "cfg": cfg,
        "ocfg": ocfg,
        "public": public,
        "planet": planet,
        "background": background,
        "reread": reread,
        "reread_items": raw["items"],
        "stances": stances["stances"],
        "claim_posts": read_json(cfg["claim_posts_json"]),
        "memo": Memo(ROOT / cfg["primary_memo"]),
    }
    if cfg.get("background_config"):
        import constitutional_background as background_rows  # 背景の部品（手順6）

        d["bg"] = background_rows.load(d, ROOT / cfg["background_config"])
    return d


def stance_order(d: dict) -> list[dict]:
    """立場の並びは公開JSONの合計が多い順（冒頭の帯と同じ）。色・名前・分類名は planet 設定。"""
    style = {s["id"]: s for s in d["planet"]["stances"]}
    totals = Counter()
    for issue in d["public"]["issues"]:
        for s in issue["stances"]:
            totals[s["id"]] += int(s["count"])
    if set(totals) != set(style):
        raise SystemExit(f"公開JSONの立場と planet 設定の立場が違います: {set(totals) ^ set(style)}")
    return [style[sid] for sid in sorted(totals, key=lambda k: (-totals[k], k))]


def stance_id(d: dict, key: str) -> str:
    """正典の立場の名前（分類名）を planet 設定の id に直す。"""
    return {s["key"]: s["id"] for s in d["planet"]["stances"]}.get(key, key)


def item_stance(d: dict, item: dict) -> str:
    return stance_id(d, d["stances"][item["post_key"]])


def post_record(rr: dict, tweet_id: str) -> dict | None:
    key = post_key(tweet_id)
    return next((i for i in rr["items"] if i["post_key"] == key), None)


def post_stance(d: dict, issue: dict, post: dict) -> str | None:
    """代表投稿の立場。明細の立場（対応表）から引く。"""
    rr = d["reread"].get(issue["label"])
    rec = post_record(rr, post["id"]) if rr else None
    return item_stance(d, rec) if rec else post.get("stance_id")


def sunk_issue(d: dict, sc: dict) -> str | None:
    over = d["cfg"].get("sunk_issue_overrides", {})
    if sc["nearest_issue_id"] and sc["id"] in over:
        raise SystemExit(f"資料にしかない話 {sc['id']} は公開JSONに論点があるので、sunk_issue_overrides は使えません")
    return sc["nearest_issue_id"] or over.get(sc["id"])


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
    if set(keys) != set(d["stances"]):
        raise SystemExit("再読データの明細と立場の対応表の投稿が一致しません"
                         "（追い読みの後は scripts/constitutional_reread_stances.py をもう一度実行してください）")
    if {i.get("main_issue") for i in d["reread_items"]} - labels:
        raise SystemExit("再読データの明細に、公開JSONに無い論点があります")
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
            continue  # 理由データが無い論点は「未公開」と表示する
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
            raise SystemExit(f"{issue['id']}: 立場の対応表に planet 設定に無い立場があります: {set(st) - set(stance_ids)}")
        if {s["id"]: int(s["count"]) for s in issue["stances"]} != {sid: st.get(sid, 0) for sid in stance_ids}:
            raise SystemExit(f"{issue['id']}: 明細の立場の内訳が公開JSONと一致しません"
                             "（判定し直しの後は scripts/constitutional_reread_stances.py で対応表を作り直してください）")
    cv = public["claim_verification"]
    per_claim = Counter(p["claim"] for p in d["claim_posts"])
    for c in cv["claims"]:
        if c["verdict"] not in cfg["verdict_labels"]:
            raise SystemExit(f"主張 {c['id']} の判定 {c['verdict']} の言い換えが設定にありません")
        if set(c["issue_ids"]) - ids:
            raise SystemExit(f"主張 {c['id']} の論点が公開JSONにありません")
        if per_claim[c["id"]] != int(c["matched_post_count"]):
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
    if set(cfg["issues"]) != ids:
        raise SystemExit(f"設定の論点と公開JSONの論点が一致しません: {set(cfg['issues']) ^ ids}")
    memo = d["memo"]
    checklist = d["background"]["checklist"]["items"]
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
        checks = {c["id"] for c in checklist if iid in (c.get("issue_ids") or [])}
        if (set(icfg.get("check_notes", {})) | set(icfg.get("check_overrides", {}))) - checks:
            raise SystemExit(f"{iid}: この論点に無い制度確認への注記・言い換えがあります")
        for mc in icfg.get("memo_checks", []):
            memo.checked_on(mc["memo_section"])
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
            if rr is None and not p.get("stance_id"):
                raise SystemExit(f"{iid}: 再読データの無い論点の投稿 {p['id']} には stance_id（正典の立場）が要ります")
        if len(posts) == 2 and len({post_stance(d, issue, p) for p in posts}) != 2 and not icfg["posts"].get("same_stance_reason"):
            raise SystemExit(f"{iid}: 投稿2件の立場が同じです（理由を same_stance_reason に書いてください）")
    # 他の論点の投稿を使い回していないか（論点をまたいで同じ投稿を出さない）
    all_posts = [p["id"] for c in cfg["issues"].values() for p in c.get("posts", {}).get("items", [])]
    if len(all_posts) != len(set(all_posts)):
        raise SystemExit("同じ投稿が2つの論点に選ばれています")


# ---------------------------------------------------------------- 読書面の部品


def ordered_issues(d: dict) -> list[dict]:
    """件数の多い順。「その他」は最後。"""
    other = d["cfg"]["other_issue_id"]
    return sorted(d["public"]["issues"], key=lambda i: (i["id"] == other, -int(i["count"]), i["id"]))


def issue_name(d: dict, issue: dict) -> str:
    return d["cfg"]["issues"].get(issue["id"], {}).get("name") or issue["label"]


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


def render_head_stance(d: dict, issue: dict) -> str:
    """論点の見出しの下の立場の帯（4立場の名前と件数）と、世論調査ではない旨の注記。"""
    sc = d["cfg"]["stance_common"]
    n = int(issue["count"])
    by = {s["id"]: int(s["count"]) for s in issue["stances"]}
    legend = "".join(f'<li><span class="fr-sw" style="background:{s["color"]}"></span>{esc(s["label"])}'
                     f'<b>{fmt(by[s["id"]])}</b></li>' for s in stance_order(d))
    return (f'<div class="fr-head-stance">{stance_bar(d, by, n)}<ul class="fr-stance-list fr-stance-mini">{legend}</ul>'
            f'<p class="fr-caveat">{esc(sc["caveat"])}</p></div>')


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
    （build_constitutional_redesign.py）が元HTMLの潮目のカード（前回と今回の収集の比較）から .fr-glance-chart に入れる。
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
    return icfg.get("reasons", {}).get(bid, {}).get("label_override", bucket["label"])


def render_reasons(d: dict, issue: dict, icfg: dict) -> str:
    """理由一覧：理由名と件数の1行ずつ。上位 top_reasons 件だけ見せ、残りは「ほかの理由を読む」の折りたたみ。"""
    rc, c = d["cfg"]["reasons_common"], compact(d)
    n = int(issue["count"])
    iid = issue["id"]
    items = ordered_reasons(d, issue, icfg)
    if not items:
        return (f'<section class="fr-block fr-reasons"><h4>{esc(rc["title"])}</h4>'
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
    stances = stance_order(d)
    out = ['<div class="fr-reason-reading">']
    for i, (bid, b) in enumerate(items):
        cnt = int(b["count"])
        st = Counter(item_stance(d, x) for x in rr["items"] if x["bucket"] == bid)
        st_text = "・".join(f'{s["label"]}{fmt(st.get(s["id"], 0))}' for s in stances)
        voice = icfg.get("reasons", {}).get(bid, {}).get("voice")
        nb, nxt = items[(i + 1) % len(items)]
        out.append(f'<article class="fr-reason-detail" id="fr-r-{esc(iid)}-{esc(bid)}" data-reason="{esc(bid)}"'
                   f'{" data-on" if i == 0 else ""}><p class="fr-eyebrow">{esc(c["reason_eyebrow"])}'
                   f'<span>{fmt(cnt)}件・{pct1(cnt, n)}%</span></p><h5>{esc(reason_label(d, icfg, bid, b))}</h5>')
        if voice:
            out.append(f'<p class="fr-voice"><span>{esc(rc["voice_label"])}</span>{esc(voice)}</p>')
        out.append(f'<p class="fr-reason-stance">{stance_bar(d, st, cnt, "fr-mini")}'
                   f'<span>{esc(rc["stance_label"])}：{esc(st_text)}</span></p>')
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
    lead = pc["lead_two"] if len(posts) == 2 else pc["lead_one"]
    out = [f'<p class="fr-fold-title">{esc(pc["title"])}</p><p class="fr-lead">{esc(lead)}</p>']
    if len(posts) == 1 and icfg["posts"].get("one_reason"):
        out.append(f'<p class="fr-fine">{esc(icfg["posts"]["one_reason"])}</p>')
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
    memo_checks = icfg.get("memo_checks", [])
    out = [f'<section class="fr-block fr-evidence"><h4>{esc(compact(d)["evidence_title"])}</h4>'
           + fold("fr-evidence-about", esc(s["title"]), f'<p class="fr-lead">{esc(s["lead"])}</p>')]
    for c in claims:
        lab = d["cfg"]["verdict_labels"][c["verdict"]]
        note = icfg.get("claim_notes", {}).get(c["id"])
        body = (f'<p class="fr-eyebrow">{esc(s["claim_eyebrow"])}<span>{esc(s["checked"].format(checked_on=jp_date(cv["checked_on"])))}</span></p>'
                f'<p>{esc(c["finding"])}</p>'
                + (f'<p class="fr-fine">{esc(note)}</p>' if note else "")
                + f'<p class="fr-fine">{esc(s["matched"].format(n=fmt(c["matched_post_count"])))}</p>'
                + details_sources(c["sources"], s["sources_label"]))
        out.append(fold(f'fr-claim fr-verdict-{esc(c["verdict"])}',
                        f'<span class="fr-sum-text">「{esc(c["claim"])}」</span><span class="fr-verdict">{esc(lab)}</span>',
                        body, f' data-claim="{esc(c["id"])}"'))
    for mc in memo_checks:
        when = d["memo"].checked_on(mc["memo_section"])
        body = (f'<p class="fr-eyebrow">{esc(s["memo_eyebrow"])}<span>{esc(s["memo_checked"].format(checked_on=jp_date(when)))}</span></p>'
                f'<p>{esc(mc["found"])}</p>' + details_sources(mc["sources"], s["sources_label"]))
        out.append(fold("fr-check fr-memo-check", f'<span class="fr-sum-text">{esc(mc["label"])}：{esc(mc["ask"])}</span>',
                        body, f' data-memo-check="{esc(mc["id"])}"'))
    sunk = [x for x in d["public"]["ocean_layer"]["sunk_continents"] if sunk_issue(d, x) == iid]
    if sunk:
        sk = d["cfg"]["sunk_common"]
        out.append(f'<div class="fr-sunk"><p class="fr-eyebrow">{esc(sk["title"])}</p>')
        for x in sunk:
            srcs = [{"name": s2["name"], "url": s2["url"], "location": s2.get("location")} for s2 in x["sources"]]
            body = (f'<p>{esc(x["life_impact"])}</p>'
                    f'<p class="fr-fine">{esc(sk["count"].format(base=fmt(x["sns_base"]), n=fmt(x["sns_count"]), checked_on=jp_date(x["checked_on"])))}</p>'
                    f'<details class="fr-sources"><summary>{esc(sk["note_label"])}</summary><p class="fr-fine">{esc(x["sns_note"])}</p></details>'
                    + details_sources(srcs, s["sources_label"]))
            out.append(fold("fr-sunk-item", f'<span class="fr-sum-text">{esc(x["topic"])}</span>', body,
                            f' data-sunk="{esc(x["id"])}"'))
        out.append("</div>")
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
    if not claims and not memo_checks and not sunk and not veins and not checks:
        out.append(f'<p class="fr-empty">{esc(s["empty"])}</p>')
    out.append(checks)
    out.append("</section>")
    return "".join(out)


def render_checks(d: dict, issue: dict, icfg: dict) -> str:
    """制度の確認（背景台帳の checklist のうち、この論点に紐づく項目）。問いだけを見せる折りたたみ。"""
    s = d["cfg"]["sources_common"]
    bg = d["background"]
    checks = [c for c in bg["checklist"]["items"] if issue["id"] in (c.get("issue_ids") or [])]
    if not checks:
        return ""
    out = [f'<div class="fr-checks"><p class="fr-eyebrow">{esc(s["check_eyebrow"])}</p>']
    for c in checks:
        note = icfg.get("check_notes", {}).get(c["id"])
        ask = icfg.get("check_overrides", {}).get(c["id"], {}).get("ask", c["ask"])
        body = (f'<p class="fr-eyebrow">{esc(c["label"])}'
                f'<span>{esc(s["checked"].format(checked_on=jp_date(bg["checked_on"])))}</span></p>'
                f'<p>{esc(c["found"])}</p>'
                + (f'<p class="fr-fine">{esc(note)}</p>' if note else "")
                + details_sources(c["sources"], s["sources_label"]))
        out.append(fold("fr-check", f'<span class="fr-sum-text">{esc(ask)}</span>', body, f' data-check="{esc(c["id"])}"'))
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
    k = len(public["issues"])
    rank_text = f"{k}つの分類で最も多い件数です。" if rank == 1 else f"{k}つの分類のうち{rank}番目の件数です。"
    out = [f'<section class="fr-panel issue-panel{" is-complete" if complete else " is-pending"}" id="issue-{esc(iid)}" '
           f'data-issue-panel="{esc(iid)}" aria-labelledby="fr-h-{esc(iid)}"{" data-selected" if iid == selected else ""}>',
           '<header class="fr-panel-head"><div>'
           f'<p class="fr-eyebrow">選んだ論点<span>分類名「{esc(issue["label"])}」</span></p>'
           f'<h3 id="fr-h-{esc(iid)}" tabindex="-1">{esc(name)}</h3>']
    paras = icfg.get("description", [])
    # 論点の説明は1段落目だけを見せ、2段落目からは「くわしく」の折りたたみ
    for para in paras[:1]:
        out.append(f'<p class="fr-desc">{esc(para)}</p>')
    if len(paras) > 1:
        out.append(fold("fr-desc-more", esc(c["desc_more"]), "".join(f'<p class="fr-desc">{esc(p)}</p>' for p in paras[1:])))
    out.append(f'</div><p class="fr-count"><b>{fmt(n)}</b><span>件</span>'
               f'<small>SNSの意見{fmt(total)}件のうち{pct1(n, total)}%。{esc(rank_text)}</small></p>'
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


def render_tabs(d: dict, issues: list[dict], selected: str) -> str:
    """論点タブ（アイコン＋論点名）。読書面の上で論点を切り替える（山なみは手順7で上に入る）。"""
    icons = {i["id"]: i.get("icon", "") for i in d["planet"].get("issues", [])}
    other = d["cfg"]["other_issue_id"]
    on = ' aria-current="true"'
    items = "".join(
        f'<li><a class="fr-tab{" is-other" if i["id"] == other else ""}" href="#issue-{esc(i["id"])}" data-issue-id="{esc(i["id"])}"'
        f'{on if i["id"] == selected else ""}>'
        f'<span class="fr-tab-icon" aria-hidden="true">{esc(icons.get(i["id"], ""))}</span>{esc(issue_name(d, i))}'
        f'<small>{fmt(i["count"])}</small></a></li>'
        for i in issues)
    return f'<nav class="fr-tabs" aria-label="{esc(compact(d)["tabs_label"])}"><ul>{items}</ul></nav>'


def render_reading(d: dict) -> str:
    cfg = d["cfg"]
    sec = cfg["section"]
    issues = ordered_issues(d)
    completes = [i["id"] for i in issues if cfg["issues"][i["id"]].get("status") == "complete"]
    selected = completes[0] if completes else issues[0]["id"]
    out = [READING_START, f'<section class="fr" id="{SECTION_ID}" aria-labelledby="fr-title" '
           f'data-default-issue="{esc(selected)}">', '<header class="fr-head">',
           f'<p class="fr-eyebrow">{esc(sec["eyebrow"])}</p><h2 id="fr-title">{esc(sec["title"])}</h2>',
           f'<p class="fr-lead">{esc(sec["lead"])}</p><p class="fr-live" aria-live="polite" id="fr-live"></p></header>',
           '<div class="fr-panels">', render_tabs(d, issues, selected)]
    ranks = {i["id"]: r for r, i in enumerate(sorted(d["public"]["issues"], key=lambda i: (-int(i["count"]), i["id"])), 1)}
    # 既定の論点を先頭に置く（JavaScriptなしで最初に読めるように）。残りは件数順（その他は最後）。
    for issue in sorted(issues, key=lambda i: i["id"] != selected):
        out.append(render_panel(d, issue, selected, ranks[issue["id"]]))
    out.append("</div>")
    out.append(f'<p class="fr-footer">{esc(cfg["footer"].format(updated_on=jp_date(d["public"]["updated_on"])))}</p>')
    out.append("</section>")
    out.append(READING_END)
    return "\n".join(out) + "\n"


def default_as_of(d: dict) -> str:
    return opening.default_as_of(d["public"])


def render_page(d: dict, as_of: str) -> str:
    fragment = opening.fragment_for(ROOT / d["cfg"]["opening_config"], as_of)
    reading = render_reading(d)
    bg = ""
    if "bg" in d:
        import constitutional_background as background_rows

        bg = background_rows.render(d, as_of, ordered_issues(d))
    title = "憲法改正論議・論点の読書面" + ("と背景" if bg else "") + "の試作"
    page = (
        "<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{esc(title)}</title>\n<meta name=\"robots\" content=\"noindex\">\n"
        "<link rel=\"stylesheet\" href=\"opening.css\">\n"
        "<link rel=\"stylesheet\" href=\"reading.css\">\n"
        "<script src=\"reading.js\" defer></script>\n</head>\n<body>\n"
        "<header class=\"fr-site\"><a href=\"#\" class=\"fr-logo\">SNS反応まっぷ</a>"
        f"<span>{esc(title)}（基準日 {esc(as_of)}）</span></header>\n"
        "<main id=\"main\">\n" + fragment + reading + bg + "</main>\n</body>\n</html>\n"
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
    except opening.OpeningError as exc:
        raise SystemExit(f"エラー: {exc}")


if __name__ == "__main__":
    main()
