#!/usr/bin/env python3
"""生成AIと著作権ページの「山なみ＋論点の読書面」を、冒頭の試作の下につないで生成する試作。

副首都（scripts/fukushuto_reading.py）・皇室典範改正と同じ型。テーマごとに違うのは設定JSONと次の点。
- 立場は「規制・制限強化支持／中立・情報／推進・活用支持」の3つを帯で出す。
- 理由区分ごとの立場の内訳と代表投稿の立場は、再読データの明細の stance から数える（副首都と同じ）。
  2026-10-07 の判定し直しで11件が公開JSONとずれていたため、2026-10-11 に正典の立場へ一度だけ合わせた
  （再読データの stance_resync_2026_10_11）。明細の立場を数えた結果が公開JSONの立場と一致しなければ止まる。
  非公開の正典は読まない。GitHub の自動検査でも同じ生成・検査が動く。
- 立場が違っても共通する心配（公開JSON ocean_layer.veins）を一次資料との照合の欄に出す。
- 手書きの文言に「違法」「合法」を使わない（冒頭と同じ検査）。

入力
- configs/ai-copyright-reading.json        : 論点の説明・理由の言い換え・照合の注記・投稿の選定（手書き文言）
- configs/ai-copyright-opening.json        : 冒頭の文言と制度の確認日（冒頭部品をそのまま使う）
- docs/data/themes/ai-copyright.json       : 件数・論点・立場・強い表現・主張の照合・資料にしかない話・共通する心配（公開JSON）
- configs/planet/ai-copyright.yaml         : 立場の色と順序、理由区分のある論点（sub_issues）と再読データのキー
- data/ai-copyright_issues-reread.json     : 理由区分（5論点。明細の bucket を数え直す）
- data/verification/ai-copyright-claims.json : 主張ごとの該当投稿（件数の照合だけに使う）
- data/verification/ai-copyright-background.json : 制度の確認4項目
- quality/research/ai-copyright-primary-sources.md : 一次資料メモ（資料の確認日）
- configs/ai-copyright-background.json ほか : 背景の開閉行（scripts/ai_copyright_background.py が描く。設定に background_config があるときだけ）

出力: quality/prototypes/ai-copyright-reading/index.html
（同じフォルダーに reading.css・reading.js・opening.css の写しを置く。正本は scripts/ai_copyright_redesign/）

基準日（--as-of）の既定は公開JSONの updated_on。今日の日付・乱数は使わない。件数・割合は手で書かない。
合計が公開JSONと合わなければ止まる。同じ入力なら出力は同じ。

    python3 scripts/ai_copyright_reading.py
"""

from __future__ import annotations

import argparse
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

import ai_copyright_opening as opening  # noqa: E402
from bukatsu_redesign.x_embeds import add_x_embeds  # noqa: E402

CONFIG = ROOT / "configs" / "ai-copyright-reading.json"
OUT_DIR = ROOT / "quality" / "prototypes" / "ai-copyright-reading"
ASSETS = opening.ASSETS
READING_START = "<!-- AI_COPYRIGHT_READING_START -->"
READING_END = "<!-- AI_COPYRIGHT_READING_END -->"
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


def norm_text(t: str) -> str:
    """同じ文面かどうかを見るための正規化（収集時の強調の目印と空白を除く。投稿の選び直しのときの検査用）。"""
    return re.sub(r"\s+", "", t.replace("\tSTART\t", "").replace("\tEND\t", "").replace("START", "").replace("END", ""))


# ---------------------------------------------------------------- 一次資料メモ


class Memo:
    """一次資料メモを見出しで引く。確認日は節の中の「確認日：YYYY-MM-DD」の最新を使う（皇室と同じ読み方）。"""

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
        """「確認できなかったこと 6」は節の中の番号付きの項目、それ以外は見出し。"""
        m = re.fullmatch(r"(.+?) (\d+)", ref)
        if m:
            body = self.section(m.group(1))
            return re.search(rf"^{m.group(2)}\. ", body, flags=re.M) is not None
        self.section(ref)
        return True


# ---------------------------------------------------------------- データと照合


def load(config_path: Path = CONFIG) -> dict:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    data = opening.load_inputs(ROOT / cfg["opening_config"])
    public = data["public"]
    if public.get("theme_id") != cfg["theme_id"] or data["config"]["theme_id"] != cfg["theme_id"]:
        raise SystemExit("設定と公開JSONのテーマが一致しません")
    if cfg["public_json"] != data["config"]["public_json"]:
        raise SystemExit("冒頭と読書面で別の公開JSONを読もうとしています")
    opening.check_words(cfg, config_path.name)
    planet = yaml.safe_load((ROOT / "configs" / "planet" / f"{cfg['theme_id']}.yaml").read_text(encoding="utf-8"))
    raw = read_json(cfg["reread_json"])
    reread = {}
    for label, sub in (planet.get("sub_issues") or {}).items():
        if sub["file"] != cfg["reread_json"]:
            raise SystemExit(f"planet設定の理由区分 {label} が別のファイル {sub['file']} を指しています")
        key, leaf = sub["path"]
        if leaf != "buckets" or key not in raw:
            raise SystemExit(f"再読データに {key}.buckets がありません（{label}）")
        reread[label] = raw[key]
    d = {
        "cfg": cfg,
        "data": data,
        "ocfg": data["config"],
        "public": public,
        "planet": planet,
        "reread": reread,
        "claim_posts": read_json(cfg["claim_posts_json"]),
        "background": read_json(cfg["background_json"]),
        "memo": Memo(ROOT / cfg["primary_memo"]),
    }
    if cfg.get("background_config"):
        import ai_copyright_background as background  # 背景の部品（手順6）

        d["bg"] = background.load(d, ROOT / cfg["background_config"])
    return d


def stance_order(d: dict) -> list[dict]:
    """立場の順序・色・名前は planet 設定（冒頭・現行の山なみと同じ定義）。"""
    return list(d["planet"]["stances"])


def stance_id(d: dict, key: str) -> str:
    """再読データの明細の立場（分類名）を planet 設定の id に直す。"""
    return {s["key"]: s["id"] for s in stance_order(d)}.get(key, key)


def post_stance(d: dict, issue: dict, post: dict) -> str | None:
    """代表投稿の立場。再読データのある論点は明細の立場、無い論点は設定の stance_id。"""
    rr = d["reread"].get(issue["label"])
    rec = post_record(rr, post["id"]) if rr else None
    return stance_id(d, rec["stance"]) if rec else post.get("stance_id")


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
        if len({i["tweet_id"] for i in items}) != n:
            raise SystemExit(f"{issue['id']}: 再読データの明細に同じ投稿が重複しています")
        tally = Counter(i["bucket"] for i in items)
        for bid, b in buckets.items():
            if tally[bid] != int(b["count"]):
                raise SystemExit(f"{issue['id']}: 理由区分 {bid} の件数が明細と一致しません")
        if set(tally) - set(buckets):
            raise SystemExit(f"{issue['id']}: 明細に区分の定義が無い bucket があります")
        for i in items:
            if i.get("main_issue") != issue["label"]:
                raise SystemExit(f"{issue['id']}: 再読データの投稿 {i['tweet_id']} の論点が {i.get('main_issue')} になっています")
        st = Counter(stance_id(d, i["stance"]) for i in items)
        if set(st) - set(stance_ids):
            raise SystemExit(f"{issue['id']}: 再読データの明細に planet 設定に無い立場があります: {set(st) - set(stance_ids)}")
        if {s["id"]: int(s["count"]) for s in issue["stances"]} != {sid: st.get(sid, 0) for sid in stance_ids}:
            raise SystemExit(f"{issue['id']}: 再読データの明細の立場の内訳が公開JSONと一致しません"
                             "（判定し直しの後は明細の stance を正典に合わせてください。DATA_REFRESH.md）")
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
        if sc["nearest_issue_id"] not in ids:
            raise SystemExit(f"資料にしかない話 {sc['id']} の論点 {sc['nearest_issue_id']} が公開JSONにありません")
        if int(sc["sns_base"]) != opinion:
            raise SystemExit(f"資料にしかない話 {sc['id']} の母数 {sc['sns_base']} が意見数 {opinion} と違います（再検索の記録を更新してください）")
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
            raise SystemExit(f"{iid}: 完成扱いの論点で、言い換えの無い理由区分があります")
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
            if p.get("stance_id") and p["stance_id"] not in stance_ids:
                raise SystemExit(f"{iid}: 投稿 {p['id']} の stance_id が planet 設定にありません")
            if rr is not None and p.get("stance_id") and p["stance_id"] != post_stance(d, issue, {"id": p["id"]}):
                raise SystemExit(f"{iid}: 投稿 {p['id']} の stance_id が再読データの立場と違います")
    # 他の論点の投稿を使い回していないか（論点をまたいで同じ投稿を出さない）
    all_posts = [p["id"] for c in cfg["issues"].values() for p in c.get("posts", {}).get("items", [])]
    if len(all_posts) != len(set(all_posts)):
        raise SystemExit("同じ投稿が2つの論点に選ばれています")


def post_record(rr: dict, tweet_id: str) -> dict | None:
    return next((i for i in rr["items"] if i["tweet_id"] == tweet_id), None)


# ---------------------------------------------------------------- 山なみ（静的SVG）


def ordered_issues(d: dict) -> list[dict]:
    """件数の多い順。「その他」は最後（皇室と同じ）。"""
    other = d["cfg"]["other_issue_id"]
    return sorted(d["public"]["issues"], key=lambda i: (i["id"] == other, -int(i["count"]), i["id"]))


def issue_name(d: dict, issue: dict) -> str:
    return d["cfg"]["issues"].get(issue["id"], {}).get("name") or issue["label"]


def high_pct(issue: dict) -> float:
    high = next((int(x["count"]) for x in issue["intensities"] if x["id"] == "high"), 0)
    return round(high / int(issue["count"]) * 100, 1)


def mountains_svg(d: dict, issues: list[dict], selected: str) -> str:
    """幅＝意見の件数、高さ＝強い表現の割合。皇室・副首都の新デザインと同じ形と規則。色は冒頭の藍と古紙。"""
    W, B, T, L, GAP, MIN = 1100, 230, 24, 40, 10, 96
    usable = W - L - 10 - GAP * (len(issues) - 1)
    total = sum(int(i["count"]) for i in issues)
    widths = [max(MIN, usable * int(i["count"]) / total) for i in issues]
    over = sum(widths) - usable
    slack = sum(max(0, w - MIN) for w in widths)
    widths = [w - over * (w - MIN) / slack if w > MIN else w for w in widths]
    top_pct = max(high_pct(i) for i in issues)
    vmax = max(40, -(-int(top_pct) // 20) * 20)
    p = ['<defs><linearGradient id="fr-hill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#cdd3ea"/>'
         '<stop offset="1" stop-color="#efece2"/></linearGradient>'
         '<linearGradient id="fr-hill-on" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#2b3d8f"/>'
         '<stop offset="1" stop-color="#8a96d4"/></linearGradient></defs>']
    for v in range(0, vmax + 1, 20):
        y = B - (B - T) * v / vmax
        dash = ' stroke-dasharray="3 7"' if v else ""
        p.append(f'<line x1="{L}" x2="{W - 10}" y1="{y:.1f}" y2="{y:.1f}" stroke="#d9d6cb"{dash}/>'
                 f'<text class="fr-axis" x="{L - 8}" y="{y + 4:.1f}" text-anchor="end">{v}%</text>')
    x = float(L)
    for issue, w in zip(issues, widths):
        rate = high_pct(issue)
        top = B - (B - T) * rate / vmax
        cx = x + w / 2
        h = B - top
        path = (f"M{x:.1f} {B} L{x + w * .24:.1f} {top + h * .52:.1f} L{x + w * .34:.1f} {top + h * .6:.1f} "
                f"L{cx:.1f} {top:.1f} L{x + w * .72:.1f} {top + h * .45:.1f} L{x + w * .8:.1f} {top + h * .4:.1f} "
                f"L{x + w:.1f} {B} Z")
        on = issue["id"] == selected
        aria = f'{issue_name(d, issue)}、{fmt(issue["count"])}件、強い表現{rate}%'
        p.append(f'<a class="fr-hill{" is-on" if on else ""}" href="#issue-{esc(issue["id"])}" '
                 f'data-issue-id="{esc(issue["id"])}" tabindex="-1" aria-label="{esc(aria)}">'
                 f'<rect class="fr-hit" x="{x:.1f}" y="8" width="{w:.1f}" height="{B + 4}" fill="transparent"/>'
                 f'<path class="fr-silhouette" d="{path}"/>'
                 f'<text class="fr-hill-n" x="{cx:.1f}" y="{top - 10:.1f}" text-anchor="middle">'
                 f'{fmt(issue["count"])}<tspan>件</tspan></text></a>')
        x += w + GAP
    return ('<svg class="fr-mountains" viewBox="0 0 1100 250" role="group" '
            'aria-label="論点の山なみ。幅は意見の件数、高さは強い表現の割合">' + "".join(p) + "</svg>")


# ---------------------------------------------------------------- 読書面の部品


def details_sources(items: list[dict], label: str) -> str:
    if not items:
        return ""
    rows = "".join(f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["name"])}</a>'
                   + (f'<span>{esc(s["location"])}</span>' if s.get("location") else "") + "</li>" for s in items)
    return f'<details class="fr-sources"><summary>{esc(label)}</summary><ul>{rows}</ul></details>'


def stance_bar(d: dict, counts: dict, total: int, cls: str = "fr-band") -> str:
    """立場の帯。色と順序は planet 設定（冒頭の帯と同じ）。"""
    segs = "".join(f'<i style="width:{counts.get(s["id"], 0) / total * 100:.2f}%;background:{s["color"]}"></i>'
                   for s in stance_order(d) if total)
    aria = "、".join(f'{s["label"]} {fmt(counts.get(s["id"], 0))}件' for s in stance_order(d))
    return f'<span class="{cls}" role="img" aria-label="{esc(aria)}">{segs}</span>'


def render_stance(d: dict, issue: dict) -> str:
    sc = d["cfg"]["stance_common"]
    n = int(issue["count"])
    by = {s["id"]: int(s["count"]) for s in issue["stances"]}
    items = "".join(f'<li><span class="fr-sw" style="background:{s["color"]}"></span>{esc(s["label"])}'
                    f'<b>{fmt(by[s["id"]])}</b>件<small>{pct1(by[s["id"]], n)}%</small></li>' for s in stance_order(d))
    return (f'<section class="fr-block fr-stance" aria-label="{esc(sc["title"])}"><h4>{esc(sc["title"])}</h4>'
            f'<p class="fr-lead">{esc(sc["lead"].format(count=fmt(n)))}</p>'
            + stance_bar(d, by, n) + f'<ul class="fr-stance-list">{items}</ul>'
            f'<p class="fr-fine">{esc(sc["note"])}</p></section>')


def render_trend(d: dict, issue: dict) -> str:
    t = d["cfg"]["trend"]
    public = d["public"]
    period = public["collection_period"]
    row = t["row_label"].format(period_start=jp_date(period["start"]), period_end=jp_date(period["end"], False))
    n, total = int(issue["count"]), int(public["opinion_count"])
    return (f'<section class="fr-block fr-trend"><h4>{esc(t["title"])}</h4>'
            '<table><thead><tr><th scope="col">収集</th><th scope="col">件数</th>'
            '<th scope="col">意見全体に占める割合</th></tr></thead>'
            f'<tbody><tr><th scope="row">{esc(row)}</th><td>{fmt(n)}件</td>'
            f'<td>{pct1(n, total)}%<small>（{fmt(total)}件中）</small></td></tr></tbody></table>'
            f'<p class="fr-fine">{esc(t["note"])}</p></section>')


def render_reasons(d: dict, issue: dict, icfg: dict) -> str:
    rc = d["cfg"]["reasons_common"]
    n = int(issue["count"])
    rr = d["reread"].get(issue["label"])
    out = [f'<section class="fr-block fr-reasons"><h4>{esc(rc["title"])}</h4>']
    if not rr:
        out.append(f'<p class="fr-empty" data-unpublished>{esc(rc["unpublished"])}</p></section>')
        return "".join(out)
    buckets = rr["buckets"]
    voices = icfg.get("reasons", {})
    items = list(buckets.items())
    if icfg.get("reason_sort", "count_desc") == "config" and voices:
        order = list(voices)
        items.sort(key=lambda kv: order.index(kv[0]) if kv[0] in order else len(order))
    else:
        items.sort(key=lambda kv: (-int(kv[1]["count"]), kv[0]))
    stances = stance_order(d)
    per = {bid: Counter(stance_id(d, i["stance"]) for i in rr["items"] if i["bucket"] == bid) for bid in buckets}
    top = max(int(b["count"]) for _, b in items)
    out.append(f'<p class="fr-lead">{esc(rc["lead"].format(count=fmt(n)))}</p><ol class="fr-reason-list">')
    for bid, b in items:
        c = int(b["count"])
        label = voices.get(bid, {}).get("label_override", b["label"])
        voice = voices.get(bid, {}).get("voice")
        st = per[bid]
        st_text = "・".join(f'{s["label"]}{fmt(st.get(s["id"], 0))}' for s in stances)
        out.append(f'<li class="fr-reason" data-reason="{esc(bid)}"><div class="fr-reason-head">'
                   f'<span class="fr-reason-name">{esc(label)}</span>'
                   f'<span class="fr-reason-n"><b>{fmt(c)}</b>件<small>{pct1(c, n)}%</small></span></div>'
                   f'<span class="fr-reason-bar" aria-hidden="true"><i style="width:{c / top * 100:.1f}%"></i></span>')
        if voice:
            out.append(f'<p class="fr-voice"><span>{esc(rc["voice_label"])}</span>{esc(voice)}</p>')
        out.append(f'<p class="fr-reason-stance">{stance_bar(d, st, c, "fr-mini")}'
                   f'<span>{esc(rc["stance_label"])}：{esc(st_text)}</span></p></li>')
    out.append(f'</ol><p class="fr-fine">{esc(rc["note"].format(count=fmt(n)))}</p></section>')
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
    out = [f'<section class="fr-block fr-posts"><h4>{esc(pc["title"])}</h4><p class="fr-lead">{esc(lead)}</p>']
    if len(posts) == 1 and icfg["posts"].get("one_reason"):
        out.append(f'<p class="fr-fine">{esc(icfg["posts"]["one_reason"])}</p>')
    out.append('<ul class="fr-post-list">')
    for p in posts:
        rec = post_record(rr, p["id"]) if rr else None
        meta = []
        if rec:
            label = icfg.get("reasons", {}).get(rec["bucket"], {}).get("label_override", rr["buckets"][rec["bucket"]]["label"])
            meta.append(f'{pc["bucket_label"]}：{label}')
        st = stances.get(post_stance(d, issue, p))
        if st:
            meta.append(f'{pc["stance_label"]}：{st["label"]}')
        out.append(f'<li class="fr-post"><p class="fr-post-label">{esc(p["label"])}</p><p>{esc(p["summary"])}</p>'
                   + (f'<p class="fr-fine">{esc("／".join(meta))}</p>' if meta else "") + "</li>")
    out.append("</ul>")
    links = "".join(f'<a href="{esc(p["url"])}">{esc(p["label"])}</a>' for p in posts)
    out.append(f'<details class="original-posts"><summary>{esc(pc["summary"].format(n=len(posts)))}</summary>{links}</details>')
    out.append("</section>")
    return "".join(out)


def render_evidence(d: dict, issue: dict, icfg: dict) -> str:
    """一次資料との照合（主張の照合・資料の確認・資料にしかない話）。"""
    s = d["cfg"]["sources_common"]
    iid = issue["id"]
    cv = d["public"]["claim_verification"]
    claims = [c for c in cv["claims"] if iid in c["issue_ids"]]
    memo_checks = icfg.get("memo_checks", [])
    out = [f'<section class="fr-block fr-evidence"><h4>{esc(s["title"])}</h4><p class="fr-lead">{esc(s["lead"])}</p>']
    for c in claims:
        lab = d["cfg"]["verdict_labels"][c["verdict"]]
        note = icfg.get("claim_notes", {}).get(c["id"])
        out.append(f'<article class="fr-claim fr-verdict-{esc(c["verdict"])}" data-claim="{esc(c["id"])}">'
                   f'<p class="fr-eyebrow">{esc(s["claim_eyebrow"])}<span>{esc(s["checked"].format(checked_on=jp_date(cv["checked_on"])))}</span></p>'
                   f'<h5>「{esc(c["claim"])}」</h5><p class="fr-verdict">{esc(lab)}</p><p>{esc(c["finding"])}</p>'
                   + (f'<p class="fr-fine">{esc(note)}</p>' if note else "")
                   + f'<p class="fr-fine">{esc(s["matched"].format(n=fmt(c["matched_post_count"])))}</p>'
                   + details_sources(c["sources"], s["sources_label"]) + "</article>")
    for mc in memo_checks:
        when = d["memo"].checked_on(mc["memo_section"])
        out.append(f'<article class="fr-check fr-memo-check" data-memo-check="{esc(mc["id"])}"><p class="fr-eyebrow">{esc(s["memo_eyebrow"])}'
                   f'<span>{esc(s["memo_checked"].format(checked_on=jp_date(when)))}</span></p>'
                   f'<h5>{esc(mc["label"])}：{esc(mc["ask"])}</h5><p>{esc(mc["found"])}</p>'
                   + details_sources(mc["sources"], s["sources_label"]) + "</article>")
    sunk = [x for x in d["public"]["ocean_layer"]["sunk_continents"] if x["nearest_issue_id"] == iid]
    if sunk:
        sk = d["cfg"]["sunk_common"]
        out.append(f'<div class="fr-sunk"><p class="fr-eyebrow">{esc(sk["title"])}</p>')
        for x in sunk:
            srcs = [{"name": s2["name"], "url": s2["url"], "location": s2.get("location")} for s2 in x["sources"]]
            out.append(f'<article class="fr-sunk-item" data-sunk="{esc(x["id"])}"><h5>{esc(x["topic"])}</h5><p>{esc(x["life_impact"])}</p>'
                       f'<p class="fr-fine">{esc(sk["count"].format(base=fmt(x["sns_base"]), n=fmt(x["sns_count"]), checked_on=jp_date(x["checked_on"])))}</p>'
                       f'<details class="fr-sources"><summary>{esc(sk["note_label"])}</summary><p class="fr-fine">{esc(x["sns_note"])}</p></details>'
                       + details_sources(srcs, s["sources_label"]) + "</article>")
        out.append("</div>")
    veins = [v for v in d["public"]["ocean_layer"].get("veins", []) if iid in v["issue_ids"]]
    if veins:
        vc = d["cfg"]["veins_common"]
        out.append(f'<div class="fr-veins"><p class="fr-eyebrow">{esc(vc["title"])}</p>')
        for v in veins:
            sides = "・".join(f'{x["stance_label"]}{fmt(x["post_count"])}件' for x in v["sides"])
            out.append(f'<article class="fr-vein" data-vein="{esc(v["id"])}">'
                       f'<p><b>{esc(vc["shared_label"])}</b>{esc(v["shared_concern"])}</p>'
                       f'<p><b>{esc(vc["diverging_label"])}</b>{esc(v["diverging_reason"])}</p>'
                       f'<p class="fr-fine">{esc(vc["sides"].format(sides=sides, checked_on=jp_date(v["checked_on"])))}</p></article>')
        out.append("</div>")
    if not claims and not memo_checks and not sunk and not veins:
        out.append(f'<p class="fr-empty">{esc(s["empty"])}</p>')
    out.append("</section>")
    return "".join(out)


def render_checks(d: dict, issue: dict, icfg: dict) -> str:
    """制度の確認（背景台帳の checklist のうち、この論点に紐づく項目）。"""
    s = d["cfg"]["sources_common"]
    bg = d["background"]
    checks = [c for c in bg["checklist"]["items"] if issue["id"] in (c.get("issue_ids") or [])]
    if not checks:
        return ""
    out = [f'<section class="fr-block fr-checks"><h4>{esc(s["check_eyebrow"])}</h4>']
    for c in checks:
        note = icfg.get("check_notes", {}).get(c["id"])
        ask = icfg.get("check_overrides", {}).get(c["id"], {}).get("ask", c["ask"])
        out.append(f'<article class="fr-check" data-check="{esc(c["id"])}"><p class="fr-eyebrow">{esc(c["label"])}'
                   f'<span>{esc(s["checked"].format(checked_on=jp_date(bg["checked_on"])))}</span></p>'
                   f'<h5>{esc(ask)}</h5><p>{esc(c["found"])}</p>'
                   + (f'<p class="fr-fine">{esc(note)}</p>' if note else "")
                   + details_sources(c["sources"], s["sources_label"]) + "</article>")
    out.append("</section>")
    return "".join(out)


def render_see_also(d: dict, icfg: dict) -> str:
    links = icfg.get("see_also", [])
    if not links:
        return ""
    items = "".join(f'<li><a href="{esc(l["href"])}">{esc(l["text"])}</a></li>' for l in links)
    return (f'<section class="fr-block fr-see"><h4>{esc(d["cfg"]["see_also_common"]["title"])}</h4>'
            f'<ul>{items}</ul></section>')


def render_panel(d: dict, issue: dict, selected: str, rank: int) -> str:
    cfg, public = d["cfg"], d["public"]
    iid = issue["id"]
    icfg = cfg["issues"].get(iid, {})
    n, total = int(issue["count"]), int(public["opinion_count"])
    name = issue_name(d, issue)
    complete = icfg.get("status") == "complete"
    k = len(public["issues"])
    rank_text = f"{k}つの論点で最も多い件数です。" if rank == 1 else f"{k}つの論点のうち{rank}番目の件数です。"
    out = [f'<section class="fr-panel issue-panel{" is-complete" if complete else " is-pending"}" id="issue-{esc(iid)}" '
           f'data-issue-panel="{esc(iid)}" aria-labelledby="fr-h-{esc(iid)}"{" data-selected" if iid == selected else ""}>',
           '<header class="fr-panel-head"><div>'
           f'<p class="fr-eyebrow">選んだ論点<span>分類名「{esc(issue["label"])}」</span></p>'
           f'<h3 id="fr-h-{esc(iid)}" tabindex="-1">{esc(name)}</h3>']
    for para in icfg.get("description", []):
        out.append(f'<p class="fr-desc">{esc(para)}</p>')
    out.append(f'</div><p class="fr-count"><b>{fmt(n)}</b><span>件</span>'
               f'<small>SNSの意見{fmt(total)}件のうち{pct1(n, total)}%。{esc(rank_text)}</small></p></header>')
    out.append(render_stance(d, issue))
    if not complete:
        out.append(f'<p class="fr-pending">{esc(cfg["pending_note"])}</p>')
        out.append(render_reasons(d, issue, icfg))
        out.append("</section>")
        return "".join(out)
    out.append('<div class="fr-grid"><div class="fr-main">')
    out.append(render_reasons(d, issue, icfg))
    out.append(render_posts(d, issue, icfg))
    out.append('</div><div class="fr-side">')
    out.append(render_evidence(d, issue, icfg))
    out.append(render_checks(d, issue, icfg))
    out.append(render_see_also(d, icfg))
    out.append(render_trend(d, issue))
    out.append("</div></div></section>")
    return "".join(out)


def render_reading(d: dict) -> str:
    cfg = d["cfg"]
    sec = cfg["section"]
    issues = ordered_issues(d)
    completes = [i["id"] for i in issues if cfg["issues"][i["id"]].get("status") == "complete"]
    selected = completes[0] if completes else issues[0]["id"]
    total = int(d["public"]["opinion_count"])
    out = [READING_START, '<section class="fr" id="ai-copyright-reading" aria-labelledby="fr-title" '
           f'data-default-issue="{esc(selected)}">', '<div class="fr-map">',
           f'<p class="fr-eyebrow">{esc(sec["eyebrow"])}</p><h2 id="fr-title">{esc(sec["title"])}</h2>',
           f'<p class="fr-lead">{esc(sec["lead"])}</p>',
           '<div class="fr-map-shell">' + mountains_svg(d, issues, selected) + "</div>",
           f'<p class="fr-fine">{esc(sec["axis_note"])}{esc(sec["min_width_note"])}</p>',
           f'<nav class="fr-chips" aria-label="{esc(sec["chips_label"])}"><ul>']
    for issue in issues:
        n = int(issue["count"])
        other = " is-other" if issue["id"] == cfg["other_issue_id"] else ""
        current = ' aria-current="true"' if issue["id"] == selected else ""
        out.append(f'<li><a class="fr-chip{other}" href="#issue-{esc(issue["id"])}" data-issue-id="{esc(issue["id"])}"{current}>'
                   f'<span class="fr-chip-name">{esc(issue_name(d, issue))}</span>'
                   f'<span class="fr-chip-n">{fmt(n)}<small>件・{pct1(n, total)}%</small></span></a></li>')
    out.append('</ul></nav><p class="fr-live" aria-live="polite" id="fr-live"></p></div>')
    out.append('<div class="fr-panels">')
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
    return opening.default_as_of(d["data"])


def render_page(d: dict, as_of: str) -> str:
    fragment = opening.render_fragment(d["data"], as_of)
    reading = render_reading(d)
    bg = ""
    if "bg" in d:
        import ai_copyright_background as background

        bg = background.render(d, as_of, ordered_issues(d))
    title = "生成AIと著作権・論点の読書面" + ("と背景" if bg else "") + "の試作"
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
    print(f"wrote {build(args.out_dir, args.as_of, args.config)}")


if __name__ == "__main__":
    main()
