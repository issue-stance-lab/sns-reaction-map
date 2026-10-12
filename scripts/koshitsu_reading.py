#!/usr/bin/env python3
"""皇室典範改正ページの「山なみ＋6論点の読書面＋背景の開閉行」を、冒頭の試作の下につないで生成する試作。

入力
- configs/koshitsu-tenpakai-reading.json : 論点の説明・理由の言い換え・照合の注記・投稿の選定（手書き文言）
- configs/koshitsu-tenpakai-opening.json : 冒頭の文言（冒頭部品と立場の色・区分をそのまま使う）
- docs/data/themes/koshitsu-tenpakai.json : 件数・論点・立場・強い表現・主張の照合・共通の心配（公開JSON）
- data/koshitsu-tenpakai_issues-reread.json : 理由区分（意見2,016件すべて）
- data/verification/koshitsu-tenpakai-source-checks.json : 照合の判定ラベル
- data/verification/koshitsu-tenpakai-background.json : 制度確認3項目
- quality/research/koshitsu-tenpakai-primary-sources.md : 一次資料メモ（資料の確認日。照合日がメモにあるかも確かめる）
- configs/koshitsu-tenpakai-background.json ほか : 背景の開閉行（scripts/koshitsu_background.py が描く）

出力: quality/prototypes/koshitsu-tenpakai-reading/index.html
（同じフォルダーの reading.css・reading.js と、冒頭の試作の opening.css を読む。正本は scripts/koshitsu_redesign/ で、生成時に写す）

冒頭は scripts/koshitsu_opening.py の render_fragment() をそのまま呼ぶ（冒頭の生成器は変えない）。
X投稿の遅延読み込みは部活動の新デザインと同じ scripts/bukatsu_redesign/x_embeds.py を使う。
件数・割合は手で書かない。合計が公開JSONと合わなければ止まる。同じ入力なら出力は同じ。

    python3 scripts/koshitsu_reading.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import koshitsu_background as background  # noqa: E402
import koshitsu_opening as opening  # noqa: E402
from bukatsu_redesign.x_embeds import add_x_embeds  # noqa: E402

CONFIG = ROOT / "configs" / "koshitsu-tenpakai-reading.json"
OUT_DIR = ROOT / "quality" / "prototypes" / "koshitsu-tenpakai-reading"
IMG_DIR = ROOT / "docs" / "images" / "topics" / "koshitsu-tenpakai"
IMG_HREF = "../../../docs/images/topics/koshitsu-tenpakai/"
READING_START = "<!-- KOSHITSU_READING_START -->"
READING_END = "<!-- KOSHITSU_READING_END -->"

esc = opening.esc
fmt = opening.fmt
ja_date = opening.ja_date


def pct1(part: int, whole: int) -> str:
    return f"{part / whole * 100:.1f}" if whole else "0.0"


def read_json(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- データと照合


def load(config_path: Path) -> dict:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    ocfg, public = opening.load(ROOT / cfg["opening_config"])
    if public.get("theme_id") != cfg["theme_id"] or ocfg["theme_id"] != cfg["theme_id"]:
        raise SystemExit("設定と公開JSONのテーマが一致しません")
    if cfg["public_json"] != ocfg["public_json"]:
        raise SystemExit("冒頭と読書面で別の公開JSONを読もうとしています")
    return {
        "cfg": cfg,
        "ocfg": ocfg,
        "public": public,
        "reread": read_json(cfg["reread_json"]),
        "checks": read_json(cfg["source_checks_json"]),
        "background": read_json(cfg["background_json"]),
        "memo": background.Memo(ROOT / cfg["primary_memo"]),
        "bg": background.load(public, ocfg, ROOT / cfg["background_config"]),
    }


def check_all(d: dict) -> None:
    """表示する数が公開JSONとずれていたら止める。"""
    public, reread, cfg = d["public"], d["reread"], d["cfg"]
    opinion = int(public["opinion_count"])
    opening.check_counts(public, opening.stance_totals(public))
    if cfg["trend"]["public_json_key"] in public:
        raise SystemExit("公開JSONに推移データが入りました。読書面の推移表示を作ってから生成してください")
    if len(reread["items"]) != opinion:
        raise SystemExit(f"再読データの件数 {len(reread['items'])} が意見数 {opinion} と一致しません")
    tally = Counter((i["main_issue"], i["bucket"]) for i in reread["items"])
    labels = {i["label"] for i in public["issues"]}
    if set(reread["buckets"]) - labels:
        raise SystemExit(f"再読データに公開JSONに無い論点があります: {set(reread['buckets']) - labels}")
    for issue in public["issues"]:
        n = int(issue["count"])
        if sum(int(s["count"]) for s in issue["stances"]) != n:
            raise SystemExit(f"{issue['id']}: 立場の合計が論点の件数と一致しません")
        if sum(int(x["count"]) for x in issue["intensities"]) != n:
            raise SystemExit(f"{issue['id']}: 強さの合計が論点の件数と一致しません")
        buckets = reread["buckets"].get(issue["label"])
        if buckets is None:
            continue  # 理由データが無い論点は「未公開」と表示する
        if sum(int(b["count"]) for b in buckets.values()) != n:
            raise SystemExit(f"{issue['id']}: 理由区分の合計が論点の件数 {n} と一致しません")
        for bid, b in buckets.items():
            if tally[(issue["label"], bid)] != int(b["count"]):
                raise SystemExit(f"{issue['id']}: 理由区分 {bid} の件数が明細と一致しません")
    ids = {i["id"] for i in public["issues"]}
    memo = d["memo"]
    for when, what in ((public["claim_verification"]["checked_on"], "主張照合の照合日"),
                       (d["background"]["checked_on"], "背景台帳の確認日")):
        if not memo.has_date(when):
            raise SystemExit(f"{what} {when} が一次資料メモにありません")
    for sc in public["ocean_layer"]["sunk_continents"]:
        if sc["nearest_issue_id"] not in ids:
            raise SystemExit(f"資料にしかない話 {sc['id']} の論点 {sc['nearest_issue_id']} が公開JSONにありません")
        if int(sc["sns_base"]) != opinion:
            raise SystemExit(f"資料にしかない話 {sc['id']} の母数 {sc['sns_base']} が意見数 {opinion} と違います（再検索の記録を更新してください）")
    if set(cfg["issues"]) != ids:
        raise SystemExit(f"設定の論点と公開JSONの論点が一致しません: {set(cfg['issues']) ^ ids}")
    for iid, icfg in cfg["issues"].items():
        if iid not in ids:
            raise SystemExit(f"設定の論点 {iid} が公開JSONにありません")
        issue = next(i for i in public["issues"] if i["id"] == iid)
        buckets = reread["buckets"].get(issue["label"], {})
        extra = set(icfg.get("reasons", {})) - set(buckets)
        if extra:
            raise SystemExit(f"{iid}: 再読データに無い理由区分が設定にあります: {extra}")
        if icfg.get("status") == "complete" and set(icfg.get("reasons", {})) != set(buckets):
            raise SystemExit(f"{iid}: 完成扱いの論点で、言い換えの無い理由区分があります")
        claims = {c["id"] for c in public["claim_verification"]["claims"] if iid in c["issue_ids"]}
        if set(icfg.get("claim_notes", {})) - claims:
            raise SystemExit(f"{iid}: この論点に無い照合への注記があります")
        checks = {c["id"] for c in d["background"]["checklist"]["items"] if iid in (c.get("issue_ids") or [])}
        if set(icfg.get("check_notes", {})) - checks:
            raise SystemExit(f"{iid}: この論点に無い制度確認への注記があります")
        for mc in icfg.get("memo_checks", []):
            memo.checked_on(mc["memo_section"])
        fig = icfg.get("figure")
        if fig and not (IMG_DIR / fig["file"]).is_file():
            raise SystemExit(f"{iid}: 図解の画像 {fig['file']} がありません")
        posts = icfg.get("posts", {}).get("items", [])
        if len(posts) > 2:
            raise SystemExit(f"{iid}: X投稿は最大2件です")
        for p in posts:
            if not p["url"].endswith("/status/" + p["id"]) or not p["url"].startswith("https://x.com/"):
                raise SystemExit(f"{iid}: 投稿IDとURLが一致しません: {p['id']}")
            if post_record(d, p["id"]) is None or post_record(d, p["id"])["main_issue"] != issue["label"]:
                raise SystemExit(f"{iid}: 投稿 {p['id']} は再読データでこの論点に入っていません")


def post_record(d: dict, tweet_id: str) -> dict | None:
    """再読データの post_key は tweet_id の sha256。本文を持たずに論点と理由区分を引ける。"""
    key = hashlib.sha256(tweet_id.encode()).hexdigest()
    return next((i for i in d["reread"]["items"] if i["post_key"] == key), None)


# ---------------------------------------------------------------- 山なみ（静的SVG）


def ordered_issues(d: dict) -> list[dict]:
    other = d["cfg"]["other_issue_id"]
    return sorted(d["public"]["issues"], key=lambda i: (i["id"] == other, -int(i["count"])))


def high_pct(issue: dict) -> float:
    high = next((int(x["count"]) for x in issue["intensities"] if x["id"] == "high"), 0)
    return round(high / int(issue["count"]) * 100, 1)


def mountains_svg(issues: list[dict], selected: str, labels: dict) -> str:
    """幅＝意見の件数、高さ＝強い表現の割合。部活動の新デザイン（app.js draw）と同じ形と規則。"""
    W, B, T, L, GAP, MIN = 1100, 230, 24, 40, 10, 96
    usable = W - L - 10 - GAP * (len(issues) - 1)
    total = sum(int(i["count"]) for i in issues)
    widths = [max(MIN, usable * int(i["count"]) / total) for i in issues]
    over = sum(widths) - usable
    slack = sum(max(0, w - MIN) for w in widths)
    widths = [w - over * (w - MIN) / slack if w > MIN else w for w in widths]
    top_pct = max(high_pct(i) for i in issues)
    vmax = max(40, -(-int(top_pct) // 20) * 20)
    p = ['<defs><linearGradient id="kr-hill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#c9cee2"/>'
         '<stop offset="1" stop-color="#ebe6dc"/></linearGradient>'
         '<linearGradient id="kr-hill-on" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#27346a"/>'
         '<stop offset="1" stop-color="#8f99c4"/></linearGradient></defs>']
    for v in range(0, vmax + 1, 20):
        y = B - (B - T) * v / vmax
        dash = ' stroke-dasharray="3 7"' if v else ""
        p.append(f'<line x1="{L}" x2="{W - 10}" y1="{y:.1f}" y2="{y:.1f}" stroke="#e4dccd"{dash}/>'
                 f'<text class="kr-axis" x="{L - 8}" y="{y + 4:.1f}" text-anchor="end">{v}%</text>')
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
        name = labels.get(issue["id"], issue["label"])
        aria = f'{name}、{fmt(int(issue["count"]))}件、強い表現{rate}%'
        p.append(f'<a class="kr-hill{" is-on" if on else ""}" href="#issue-{esc(issue["id"])}" '
                 f'data-issue-id="{esc(issue["id"])}" tabindex="-1" aria-label="{esc(aria)}">'
                 f'<rect class="kr-hit" x="{x:.1f}" y="8" width="{w:.1f}" height="{B + 4}" fill="transparent"/>'
                 f'<path class="kr-silhouette" d="{path}"/>'
                 f'<text class="kr-hill-n" x="{cx:.1f}" y="{top - 10:.1f}" text-anchor="middle">'
                 f'{fmt(int(issue["count"]))}<tspan>件</tspan></text></a>')
        x += w + GAP
    return ('<svg class="kr-mountains" viewBox="0 0 1100 250" role="group" '
            'aria-label="論点の山なみ。幅は意見の件数、高さは強い表現の割合">' + "".join(p) + "</svg>")


# ---------------------------------------------------------------- 読書面の部品


def details_sources(items: list[dict], label: str) -> str:
    rows = "".join(f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["name"])}</a>'
                   + (f'<span>{esc(s["location"])}</span>' if s.get("location") else "") + "</li>" for s in items)
    return f'<details class="kr-sources"><summary>{esc(label)}</summary><ul>{rows}</ul></details>'


def compact(d: dict) -> dict:
    """2026-10-12 の部活動型の圧縮で使う見出し・折りたたみの名前（設定 compact）。生成AIと著作権・副首都と同じ型。"""
    return d["cfg"]["compact"]


def fold(cls: str, summary: str, body: str, attrs: str = "") -> str:
    """JavaScriptが無くても開閉できる折りたたみ。初期状態は閉じる。"""
    return f'<details class="kr-fold {cls}"{attrs}><summary>{summary}</summary>{body}</details>'


def render_trend(d: dict, issue: dict) -> str:
    """収集ごとの割合と件数（最新の累計の1行）。推移の図は公開データに無いので、表を折りたたむだけ。"""
    t = d["cfg"]["trend"]
    public = d["public"]
    period = public["collection_period"]
    row = t["row_label"].format(period_start=ja_date(period["start"]), period_end=ja_date(period["end"], False))
    n, total = int(issue["count"]), int(public["opinion_count"])
    body = ('<table><thead><tr><th scope="col">収集</th><th scope="col">件数</th>'
            '<th scope="col">意見全体に占める割合</th></tr></thead>'
            f'<tbody><tr><th scope="row">{esc(row)}</th><td>{fmt(n)}件</td>'
            f'<td>{pct1(n, total)}%<small>（{fmt(total)}件中）</small></td></tr></tbody></table>'
            f'<p class="kr-fine">{esc(t["note"])}</p>')
    return fold("kr-block kr-trend", esc(t["title"]), body)


def ordered_reasons(d: dict, issue: dict, icfg: dict) -> list[tuple[str, dict]]:
    buckets = d["reread"]["buckets"].get(issue["label"])
    if not buckets:
        return []
    voices = icfg.get("reasons", {})
    items = list(buckets.items())
    if icfg.get("reason_sort", "count_desc") == "config" and voices:
        order = list(voices)
        items.sort(key=lambda kv: order.index(kv[0]) if kv[0] in order else len(order))
    else:
        items.sort(key=lambda kv: (-int(kv[1]["count"]), kv[0]))
    return items


def reason_label(icfg: dict, bid: str, bucket: dict) -> str:
    return icfg.get("reasons", {}).get(bid, {}).get("label_override", bucket["label"])


def render_reasons(d: dict, issue: dict, icfg: dict) -> str:
    """理由一覧：理由名と件数の1行ずつ。上位 top_reasons 件だけ見せ、残りと数え方の注記は折りたたみ。"""
    rc, c = d["cfg"]["reasons_common"], compact(d)
    n = int(issue["count"])
    iid = issue["id"]
    items = ordered_reasons(d, issue, icfg)
    if not items:
        return (f'<section class="kr-block kr-reasons"><h4>{esc(rc["title"])}</h4>\n'
                f'<p class="kr-empty">{esc(rc["unpublished"])}</p></section>')
    top = int(c["top_reasons"])

    def row(i: int, bid: str, b: dict) -> str:
        cnt = int(b["count"])
        current = ' aria-current="true"' if i == 0 else ""
        return (f'<li class="kr-reason" data-reason="{esc(bid)}"><a class="kr-reason-pick" href="#kr-r-{esc(iid)}-{esc(bid)}" '
                f'data-reason-pick="{esc(bid)}"{current}><span class="kr-reason-name">{esc(reason_label(icfg, bid, b))}</span>'
                f'<span class="kr-reason-n"><b>{fmt(cnt)}</b>件<small>{pct1(cnt, n)}%</small></span></a></li>')

    out = [f'<section class="kr-block kr-reasons"><h4>{esc(c["reasons_index_title"].format(k=len(items)))}</h4>'
           f'<p class="kr-lead">{esc(rc["title"])}</p>',
           '<ol class="kr-reason-list">' + "".join(row(i, bid, b) for i, (bid, b) in enumerate(items[:top])) + "</ol>"]
    rest = items[top:]
    if rest:
        out.append(fold("kr-reason-more", esc(c["reasons_more"].format(k=len(rest))),
                        f'<ol class="kr-reason-list" start="{top + 1}">'
                        + "".join(row(top + i, bid, b) for i, (bid, b) in enumerate(rest)) + "</ol>"))
    out.append("</section>")
    return "".join(out)


def render_reason_details(d: dict, issue: dict, icfg: dict) -> str:
    """選んだ理由の説明（どんな声か）。JavaScriptが動くときは1つだけ見せる（最初は件数1位）。
    皇室の理由区分には区分ごとの立場の内訳が無い（前から出していない）ので、説明は「どんな声か」だけ。"""
    rc, c = d["cfg"]["reasons_common"], compact(d)
    items = ordered_reasons(d, issue, icfg)
    if not items:
        return ""
    n, iid = int(issue["count"]), issue["id"]
    out = ['<div class="kr-reason-reading">']
    for i, (bid, b) in enumerate(items):
        cnt = int(b["count"])
        voice = icfg.get("reasons", {}).get(bid, {}).get("voice")
        nb, nxt = items[(i + 1) % len(items)]
        out.append(f'<article class="kr-reason-detail" id="kr-r-{esc(iid)}-{esc(bid)}" data-reason="{esc(bid)}"'
                   f'{" data-on" if i == 0 else ""}><p class="kr-eyebrow">{esc(c["reason_eyebrow"])}'
                   f'<span>{fmt(cnt)}件・{pct1(cnt, n)}%</span></p><h5>{esc(reason_label(icfg, bid, b))}</h5>')
        if voice:
            out.append(f'<p class="kr-voice"><span>{esc(rc["voice_label"])}</span>{esc(voice)}</p>')
        if len(items) > 1:
            out.append(f'<p class="kr-next"><span>{esc(c["reason_next"])}</span>'
                       f'<a href="#kr-r-{esc(iid)}-{esc(nb)}" data-reason-pick="{esc(nb)}">'
                       f'{esc(reason_label(icfg, nb, nxt))} →</a></p>')
        out.append("</article>")
    # 数え方の説明は、前と同じく理由の説明のあと・2つの段落で置き、折りたたむ（生成AIは「ほかの理由」の折りたたみの中に1段落）。
    # 皇室では、説明（どんな声か）の直後に立場の文が続くと文末が3回以上そろい、1段落にまとめると生成AIの同じ役目の文と似すぎるため
    out.append(fold("kr-reason-method", esc(c["method_fold"]),
                    f'<p class="kr-fine">{esc(rc["lead"].format(count=fmt(n)))}</p>'
                    f'<p class="kr-fine">{esc(rc["note"].format(count=fmt(n)))}</p>'))
    out.append("</div>")
    return "".join(out)


def render_stance(d: dict, issue: dict, icfg: dict) -> str:
    """今回案全体への賛否。部活動と同じく折りたたむ（中身は前と同じ帯・3区分・内訳・注記）。
    「同じ心配から、違う結論へ」は根拠の欄（render_sources）へ移した。"""
    sc = d["cfg"]["stance_common"]
    c = d["ocfg"]["counts"]
    colors, names = c["stance_colors"], c["stance_labels"]
    n = int(issue["count"])
    by = {s["id"]: int(s["count"]) for s in issue["stances"]}
    groups = [(g, sum(by.get(s, 0) for s in g["stance_ids"])) for g in c["stance_groups"]]
    expressed = dict((g["id"], k) for g, k in groups)["expressed"]
    out = [f'<p class="kr-fold-title">{esc(sc["title"])}</p>',
           f'<p class="kr-lead">{esc(sc["lead"].format(count=fmt(n), expressed=fmt(expressed)))}</p>']
    if icfg.get("stance_note"):
        out.append(f'<p>{esc(icfg["stance_note"])}</p>')
    out.append('<div class="ko-ledger kr-ledger" role="img" aria-label="'
               + esc("、".join(f'{g["label"]} {fmt(k)}件' for g, k in groups)) + '">')
    for g, k in groups:
        if g["id"] == "expressed":
            inner = "".join(f'<i style="width:{by.get(s, 0) / k * 100:.1f}%;background:{colors[s]}"></i>'
                            for s in g["stance_ids"]) if k else ""
            out.append(f'<span class="ko-seg ko-seg-expressed" style="width:{pct1(k, n)}%">{inner}</span>')
        else:
            out.append(f'<span class="ko-seg ko-seg-{esc(g["id"])}" style="width:{pct1(k, n)}%"></span>')
    out.append('</div><dl class="ko-groups kr-groups">')
    for g, k in groups:
        out.append(f'<div class="ko-group ko-group-{esc(g["id"])}"><dt>{esc(g["label"])}</dt>'
                   f'<dd><b>{fmt(k)}</b>件<small>（{pct1(k, n)}%）</small></dd></div>')
    out.append("</dl>")
    exp = next(g for g, _ in groups if g["id"] == "expressed")
    chips = "".join(f'<li><span class="sw" style="background:{colors[s]}"></span>{esc(names[s])}'
                    f'<b>{fmt(by.get(s, 0))}</b>件</li>' for s in exp["stance_ids"])
    out.append(f'<div class="ko-expressed"><p>全体の賛否を書いた{fmt(expressed)}件の内訳</p><ul>{chips}</ul></div>')
    out.append(f'<p class="kr-fine">{esc(c["unexpressed_note"])}</p>')
    return fold("kr-block kr-stance", esc(compact(d)["stance_fold"]), "".join(out))


def render_sources(d: dict, issue: dict, icfg: dict) -> str:
    """根拠にあたる：同じ心配から違う結論へ・制度の確認・資料の確認・主張の照合・資料にしかない話。
    部活動と同じく、項目ごとに見出し（と判定ラベル）だけを見せる折りたたみにする（中身の文・件数・出典は前と同じ）。"""
    s = d["cfg"]["sources_common"]
    iid = issue["id"]
    out = [f'<section class="kr-block kr-evidence"><h4>{esc(compact(d)["evidence_title"])}</h4>'
           + fold("kr-evidence-about", esc(s["title"]), f'<p class="kr-lead">{esc(s["lead"])}</p>')]
    # 同じ心配から、違う結論へ（前は立場の欄の中）。照合の文の直後に置くと文末が3回以上そろうので、根拠の欄の先頭に置く
    veins = [v for v in d["public"]["ocean_layer"]["veins"] if iid in v["issue_ids"]]
    if veins:
        sc = d["cfg"]["stance_common"]
        out.append(f'<div class="kr-concerns"><p class="kr-eyebrow">{esc(sc["concern_title"])}</p>')
        for v in veins:
            sides = "、".join(f'{x["stance_label"]}{x["post_count"]}件' for x in v["sides"])
            body = (f'<p>{esc(v["diverging_reason"])}</p>'
                    f'<p class="kr-fine">{esc(sc["concern_count"].format(sides=sides, checked_on=ja_date(v["checked_on"])))}</p>')
            out.append(fold("kr-concern", f'<span class="kr-sum-text">{esc(v["shared_concern"])}</span>', body,
                            f' data-concern="{esc(v["id"])}"'))
        out.append("</div>")
    bg = d["background"]
    checks = [c for c in bg["checklist"]["items"] if iid in (c.get("issue_ids") or [])]
    for c in checks:
        note = icfg.get("check_notes", {}).get(c["id"])
        body = (f'<p class="kr-eyebrow">{esc(s["check_eyebrow"])}'
                f'<span>{esc(s["checked"].format(checked_on=ja_date(bg["checked_on"])))}</span></p>'
                f'<p>{esc(c["found"])}</p>'
                + (f'<p class="kr-fine">{esc(note)}</p>' if note else "")
                + details_sources(c["sources"], s["sources_label"]))
        out.append(fold("kr-check", f'<span class="kr-sum-text">{esc(c["label"])}：{esc(c["ask"])}</span>', body,
                        f' data-check="{esc(c["id"])}"'))
    law_dates = background.law_dates(d["ocfg"])
    memo_checks = icfg.get("memo_checks", [])
    for mc in memo_checks:
        when = d["memo"].checked_on(mc["memo_section"])
        body = (f'<p class="kr-eyebrow">{esc(s["memo_eyebrow"])}'
                f'<span>{esc(s["memo_checked"].format(checked_on=ja_date(when)))}</span></p>'
                f'<p>{esc(mc["found"].format(**law_dates))}</p>' + details_sources(mc["sources"], s["sources_label"]))
        out.append(fold("kr-check kr-memo-check", f'<span class="kr-sum-text">{esc(mc["label"])}：{esc(mc["ask"])}</span>',
                        body, f' data-memo-check="{esc(mc["id"])}"'))
    labels = {c["key"]: c for c in d["checks"]["checks"]}
    cv = d["public"]["claim_verification"]
    claims = [c for c in cv["claims"] if iid in c["issue_ids"]]
    for c in claims:
        lab = labels.get(c["id"], {}).get("verdict_label", c["verdict"])
        note = icfg.get("claim_notes", {}).get(c["id"])
        body = (f'<p class="kr-eyebrow">{esc(s["claim_eyebrow"])}<span>{esc(s["checked"].format(checked_on=ja_date(cv["checked_on"])))}</span></p>'
                f'<p>{esc(c["finding"])}</p>'
                + (f'<p class="kr-fine">{esc(note)}</p>' if note else "")
                + f'<p class="kr-fine">{esc(s["matched"].format(n=fmt(int(c["matched_post_count"]))))}</p>'
                + details_sources(c["sources"], s["sources_label"]))
        out.append(fold(f'kr-claim kr-verdict-{esc(c["verdict"])}',
                        f'<span class="kr-sum-text">「{esc(c["claim"])}」</span><span class="kr-verdict">{esc(lab)}</span>',
                        body, f' data-claim="{esc(c["id"])}"'))
    sunk = [x for x in d["public"]["ocean_layer"]["sunk_continents"] if x["nearest_issue_id"] == iid]
    if sunk:
        sk = d["cfg"]["sunk_common"]
        # 見出しは前と同じく見出し要素（h5）。段落にすると副首都の同じ見出しと「同じ文」に数えられる
        out.append(f'<div class="kr-sunk"><h5 class="kr-eyebrow kr-group-title">{esc(sk["title"])}</h5>')
        for x in sunk:
            srcs = [{"name": s2["name"], "url": s2["url"], "location": s2.get("location")} for s2 in x["sources"]]
            body = (f'<p>{esc(x["life_impact"])}</p>'
                    f'<p class="kr-fine">{esc(sk["count"].format(base=fmt(int(x["sns_base"])), n=fmt(int(x["sns_count"])), checked_on=ja_date(x["checked_on"])))}</p>'
                    f'<details class="kr-sources"><summary>{esc(sk["note_label"])}</summary><p class="kr-fine">{esc(x["sns_note"])}</p></details>'
                    + details_sources(srcs, s["sources_label"]))
            out.append(fold("kr-sunk-item", f'<span class="kr-sum-text">{esc(x["topic"])}</span>', body,
                            f' data-sunk="{esc(x["id"])}"'))
        out.append("</div>")
    if not claims and not checks and not memo_checks and not sunk and not veins:
        out.append(f'<p class="kr-empty">{esc(s["empty"])}</p>')
    out.append("</section>")
    return "".join(out)


def render_posts(d: dict, issue: dict, icfg: dict) -> str:
    pc = d["cfg"]["posts_common"]
    posts = icfg.get("posts", {}).get("items", [])
    if not posts:
        return (f'<section class="kr-block kr-posts"><h4>{esc(pc["title"])}</h4>'
                f'<p class="kr-empty">{esc(pc["none"])}</p></section>')
    buckets = d["reread"]["buckets"].get(issue["label"], {})
    lead = pc["lead_two"] if len(posts) == 2 else pc["lead_one"]
    out = [f'<p class="kr-fold-title">{esc(pc["title"])}</p><p class="kr-lead">{esc(lead)}</p><ul class="kr-post-list">']
    for p in posts:
        rec = post_record(d, p["id"])
        bucket = buckets.get(rec["bucket"], {}).get("label", "") if rec else ""
        out.append(f'<li class="kr-post"><p class="kr-post-label">{esc(p["label"])}</p><p>{esc(p["summary"])}</p>'
                   + (f'<p class="kr-fine">{esc(pc["bucket_label"])}：{esc(bucket)}</p>' if bucket else "") + "</li>")
    out.append("</ul>")
    links = "".join(f'<a href="{esc(p["url"])}">{esc(p["label"])}</a>' for p in posts)
    out.append(f'<details class="original-posts"><summary>{esc(pc["summary"].format(n=len(posts)))}</summary>{links}</details>')
    return fold("kr-block kr-posts", esc(compact(d)["posts_fold"].format(n=len(posts))), "".join(out))


def render_figure(d: dict, icfg: dict) -> str:
    fig = icfg.get("figure")
    if not fig:
        return ""
    fc = d["cfg"]["figure_common"]
    return (f'<p class="kr-figure"><a href="{esc(IMG_HREF + fig["file"])}" target="_blank" rel="noopener" '
            f'aria-label="{esc(fc["label"] + "：" + fig["alt"])}">{esc(fc["label"])}</a>'
            f'<span>{esc(fc["note"])}</span></p>')


def render_panel(d: dict, issue: dict, selected: str, labels: dict, rank: int) -> str:
    cfg, public, c = d["cfg"], d["public"], compact(d)
    iid = issue["id"]
    icfg = cfg["issues"].get(iid, {})
    n, total = int(issue["count"]), int(public["opinion_count"])
    name = icfg.get("name") or labels.get(iid, issue["label"])
    complete = icfg.get("status") == "complete"
    rank_text = (f"{len(public['issues'])}つの分類で最も多い件数です。" if rank == 1
                 else f"{len(public['issues'])}つの分類のうち{rank}番目の件数です。")
    out = [f'<section class="kr-panel issue-panel{" is-complete" if complete else " is-pending"}" id="issue-{esc(iid)}" '
           f'data-issue-panel="{esc(iid)}" aria-labelledby="kr-h-{esc(iid)}"{" data-selected" if iid == selected else ""}>',
           '<header class="kr-panel-head"><div>'
           f'<p class="kr-eyebrow">選んだ論点<span>分類名「{esc(issue["label"])}」</span></p>'
           f'<h3 id="kr-h-{esc(iid)}" tabindex="-1">{esc(name)}</h3>']
    paras = icfg.get("description", [])
    # 論点の説明は1段落目だけを見せ、2段落目からは折りたたみ（文は変えない）
    for para in paras[:1]:
        out.append(f'<p class="kr-desc">{esc(para)}</p>')
    if len(paras) > 1:
        out.append(fold("kr-desc-more", esc(c["desc_more"]), "".join(f'<p class="kr-desc">{esc(p)}</p>' for p in paras[1:])))
    out.append(render_figure(d, icfg))
    out.append(f'</div><p class="kr-count"><b>{fmt(n)}</b><span>件</span>'
               f'<small>SNSの意見{fmt(total)}件のうち{pct1(n, total)}%。{esc(rank_text)}</small></p>'
               f'<p class="kr-back"><a href="#koshitsu-reading">{esc(c["back"])}</a></p></header>')
    if not complete:
        out.append(f'<p class="kr-pending">{esc(cfg["pending_note"])}</p>')
        out.append(render_reasons(d, issue, icfg))
        out.append("</section>")
        return "".join(out)
    out.append('<div class="kr-grid"><div class="kr-main">')
    out.append(render_reasons(d, issue, icfg))
    out.append(render_reason_details(d, issue, icfg))
    out.append(render_stance(d, issue, icfg))
    out.append(render_posts(d, issue, icfg))
    out.append('</div><div class="kr-side">')
    out.append(render_sources(d, issue, icfg))  # 資料にしかない話・同じ心配から違う結論へもこの中に入る
    out.append(render_trend(d, issue))
    out.append("</div></div></section>")
    return "".join(out)


def render_tabs(d: dict, issues: list[dict], selected: str, labels: dict) -> str:
    """論点タブ（アイコン＋論点名）。山なみの図とは別に、読書面の上で論点を切り替える。アイコンは山なみの設定から。"""
    import yaml  # noqa: PLC0415

    planet = yaml.safe_load((ROOT / "configs" / "planet" / f'{d["cfg"]["theme_id"]}.yaml').read_text(encoding="utf-8"))
    icons = {i["id"]: i.get("icon", "") for i in planet.get("issues", [])}
    on = ' aria-current="true"'
    items = "".join(
        f'<li><a class="kr-tab" href="#issue-{esc(i["id"])}" data-issue-id="{esc(i["id"])}"'
        f'{on if i["id"] == selected else ""}>'
        f'<span class="kr-tab-icon" aria-hidden="true">{esc(icons.get(i["id"], ""))}</span>'
        f'{esc(d["cfg"]["issues"].get(i["id"], {}).get("name") or labels.get(i["id"], i["label"]))}</a></li>'
        for i in issues)
    return f'<nav class="kr-tabs" aria-label="{esc(compact(d)["tabs_label"])}"><ul>{items}</ul></nav>'


def render_reading(d: dict) -> str:
    cfg = d["cfg"]
    sec = cfg["section"]
    labels = d["ocfg"]["issue_short_labels"]
    issues = ordered_issues(d)
    completes = [i for i, c in cfg["issues"].items() if c.get("status") == "complete"]
    selected = completes[0] if completes else issues[0]["id"]
    total = int(d["public"]["opinion_count"])
    out = [READING_START, '<section class="kr" id="koshitsu-reading" aria-labelledby="kr-title" '
           f'data-default-issue="{esc(selected)}">', '<div class="kr-map">',
           f'<p class="kr-eyebrow">{esc(sec["eyebrow"])}</p><h2 id="kr-title">{esc(sec["title"])}</h2>',
           f'<p class="kr-lead">{esc(sec["lead"])}</p>',
           '<div class="kr-map-shell">' + mountains_svg(issues, selected, labels) + "</div>",
           f'<p class="kr-fine">{esc(sec["axis_note"])}{esc(sec["min_width_note"])}</p>',
           f'<nav class="kr-chips" aria-label="{esc(sec["chips_label"])}"><ul>']
    for issue in issues:
        n = int(issue["count"])
        other = " is-other" if issue["id"] == cfg["other_issue_id"] else ""
        current = ' aria-current="true"' if issue["id"] == selected else ""
        out.append(f'<li><a class="kr-chip{other}" href="#issue-{esc(issue["id"])}" data-issue-id="{esc(issue["id"])}"{current}>'
                   f'<span class="kr-chip-name">{esc(labels.get(issue["id"], issue["label"]))}</span>'
                   f'<span class="kr-chip-n">{fmt(n)}<small>件・{pct1(n, total)}%</small></span></a></li>')
    out.append('</ul></nav><p class="kr-live" aria-live="polite" id="kr-live"></p></div>')
    out.append('<div class="kr-panels">')
    out.append(render_tabs(d, issues, selected, labels))
    ranks = {i["id"]: r for r, i in enumerate(sorted(d["public"]["issues"], key=lambda i: (-int(i["count"]), i["id"])), 1)}
    # 完成した論点を先頭に置く（JavaScriptなしで最初に読めるように）。残りは件数順。
    for issue in sorted(issues, key=lambda i: i["id"] != selected):
        out.append(render_panel(d, issue, selected, labels, ranks[issue["id"]]))
    out.append("</div>")
    out.append(f'<p class="kr-footer">{esc(cfg["footer"].format(updated_on=ja_date(d["public"]["updated_on"])))}</p>')
    out.append("</section>")
    out.append(READING_END)
    return "\n".join(out) + "\n"


def render_page(d: dict, as_of: str) -> str:
    fragment = opening.render_fragment(d["ocfg"], d["public"], as_of)
    reading = render_reading(d)
    bg = background.render(d["bg"], as_of, ordered_issues(d), d["ocfg"]["issue_short_labels"])
    title = "".join(d["ocfg"]["h1"]) + "｜論点の読書面と背景の試作"
    page = (
        "<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{esc(title)}</title>\n<meta name=\"robots\" content=\"noindex\">\n"
        "<link rel=\"stylesheet\" href=\"../koshitsu-tenpakai-opening/opening.css\">\n"
        "<link rel=\"stylesheet\" href=\"reading.css\">\n"
        "<script src=\"reading.js\" defer></script>\n</head>\n<body>\n"
        "<header class=\"ko-site\"><a href=\"#\" class=\"ko-logo\">SNS反応まっぷ</a>"
        f"<span>皇室典範改正・論点の読書面と背景の試作（基準日 {esc(as_of)}）</span></header>\n"
        "<main>\n" + fragment + reading + bg + "</main>\n</body>\n</html>\n"
    )
    return add_x_embeds(page)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=CONFIG)
    ap.add_argument("--as-of", help="冒頭の基準日 YYYY-MM-DD（既定は冒頭の設定JSONの as_of）")
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    d = load(args.config)
    check_all(d)
    as_of = args.as_of or d["ocfg"]["as_of"]
    date.fromisoformat(as_of)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / "index.html"
    out.write_text(render_page(d, as_of), encoding="utf-8")
    for name in ("reading.css", "reading.js"):
        shutil.copyfile(opening.ASSETS / name, args.out_dir / name)
    opening_dir = args.out_dir.parent / "koshitsu-tenpakai-opening"
    if opening_dir.is_dir():
        shutil.copyfile(opening.ASSETS / "opening.css", opening_dir / "opening.css")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
