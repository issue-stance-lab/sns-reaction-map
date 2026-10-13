#!/usr/bin/env python3
"""学校でのあだ名禁止ページの「背景として開く内容」（開閉行）を生成する部品。

scripts/nickname_reading.py から呼ぶ（単独では実行しない）。高齢者免許返納の scripts/elderly_background.py と同じ型。
期限付きの制度イベントは無いので、段階の切り替えは持たない。「◯月◯日時点」は冒頭の設定の checked_on
（国の資料の本文を確かめた日、1か所だけ）から作る。高齢者と違うのは次の点。
- 1行目「国は、あだ名や呼び方を決めているのか」（kind "national"）は、確認できたこと／確認できないことを分けて並べる。
  各論点の根拠欄の最後のリンク（#bg-national）の行き先。
- 期待と懸念（kind "voices"）は、冒頭の設定 background_candidates（旧検索入口の3タブ）から読み、「ここからはSNSの意見」と明示する。
- よくある質問（kind "faq"）は、冒頭の設定 faq.items から、冒頭と重ならない問いを番号で選んで読む（文は二重に持たない）。
  冒頭の設定 faq.placement が "background" でないと止まる（冒頭と背景に同じFAQが出るのを防ぐ）。
- 相談先（kind "help"）は、冒頭の「つらい場合」の案内からこの行へつなぐ。電話番号は冒頭の設定 safety.phone の1か所から読む（冒頭にも同じ番号が出る）。

入力
- configs/school-nickname-ban-background.json : 行の名前・並び・手書きの文言（SNSの件数・日付は書かない）
- data/verification/school-nickname-ban-background.json : 背景台帳（定義・なぜ議論になるのか・年表・確認日）
- configs/school-nickname-ban-opening.json : checked_on・期待と懸念・FAQ
- configs/classroom/school-nickname-ban.json : 授業向けの理由・資料・問い（既存の仕組みと共有。読むだけ）
- THEMES.yaml・公開JSON : 更新日・収集期間の一致、次回の収集予定

行はすべて <details> で、初期状態は閉じる。JavaScriptなしでも開ける。日付・件数を手で書かず、
台帳・登録簿と食い違ったら止まる。
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from html import escape
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "school-nickname-ban-background.json"
KINDS = ("national", "points", "voices", "ledger_text", "timeline", "faq", "help", "classroom", "unverified")


def esc(value: object) -> str:
    return escape(str(value), quote=True)


def jp_date(iso: str, with_year: bool = True) -> str:
    d = date.fromisoformat(str(iso))
    return f"{d.year}年{d.month}月{d.day}日" if with_year else f"{d.month}月{d.day}日"


def load(d: dict, config_path: Path = CONFIG) -> dict:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    if cfg["theme_id"] != d["public"]["theme_id"]:
        raise SystemExit("背景の設定と公開JSONのテーマが一致しません")
    inp = cfg["inputs"]
    themes = yaml.safe_load((ROOT / inp["themes_yaml"]).read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / inp["background_ledger"]).read_text(encoding="utf-8"))
    if ledger != d["background"]:
        raise SystemExit("読書面と背景で別の背景台帳を読もうとしています")
    return {
        "cfg": cfg,
        "ledger": ledger,
        "classroom": json.loads((ROOT / inp["classroom"]).read_text(encoding="utf-8")),
        "theme": themes["themes"][cfg["theme_id"]],
    }


def dates(d: dict) -> dict:
    public, theme = d["public"], d["bg"]["theme"]
    after = date.fromisoformat(public["collection_period"]["end"]) + timedelta(days=1)
    nxt = theme.get("collect_at")
    return {"checked": jp_date(d["ocfg"]["checked_on"]), "after": jp_date(after.isoformat(), False),
            "next_collect": jp_date(str(nxt), False) if nxt else "未定"}


def rows(cfg: dict):
    for g in cfg["groups"]:
        yield from g["rows"]


def check(d: dict) -> None:
    b, public, ocfg = d["bg"], d["public"], d["ocfg"]
    cfg, ledger, theme = b["cfg"], b["ledger"], b["theme"]
    if str(theme["updated_at"]) != public["updated_on"]:
        raise SystemExit(f"THEMES.yaml の updated_at {theme['updated_at']} と公開JSONの updated_on {public['updated_on']} が違います")
    period = f'{public["collection_period"]["start"]}〜{public["collection_period"]["end"]}'
    if str(theme["sample_period"]) != period:
        raise SystemExit(f"THEMES.yaml の sample_period {theme['sample_period']} と公開JSONの収集期間 {period} が違います")
    if date.fromisoformat(ocfg["checked_on"]) < date.fromisoformat(ledger["checked_on"]):
        raise SystemExit("冒頭の checked_on が背景台帳の確認日より古くなっています")
    ids = {i["id"] for i in public["issues"]}
    timeline_ids = {t["id"] for t in ledger["timeline"]}
    seen = set()
    all_rows = list(rows(cfg))
    if not any(r["id"] == "national" for r in all_rows):
        raise SystemExit("背景に国の定めの行（national）がありません（各論点の根拠欄のリンク #bg-national の行き先）")
    for row in all_rows:
        if row["id"] in seen:
            raise SystemExit(f"背景の行 {row['id']} が2回あります")
        seen.add(row["id"])
        if row["kind"] not in KINDS:
            raise SystemExit(f"背景の行の種類 {row['kind']} を知りません")
        for iid in row.get("issue_ids", []) + [i["issue_id"] for i in row.get("items", []) if "issue_id" in i]:
            if iid not in ids:
                raise SystemExit(f"背景の行 {row['id']} の論点 {iid} が公開JSONにありません")
        if row["kind"] == "help" and not (ocfg.get("safety") or {}).get("phone"):
            raise SystemExit("相談先の行には、冒頭の設定 safety.phone（電話番号）が要ります")
        if row["kind"] in ("national", "points", "ledger_text", "help") and not row.get("sources"):
            raise SystemExit(f"背景の行 {row['id']} に出典がありません")
        if row["kind"] == "national" and not (row.get("confirmed") and row.get("unconfirmed")):
            raise SystemExit("国の定めの行には、確認できたことと確認できないことの両方が要ります")
        if row["kind"] == "voices":
            cand = ocfg["background_candidates"]["items"]
            keys = [i["key"] for i in row["items"]]
            if set(keys) != set(cand):
                raise SystemExit(f"期待と懸念の行が、冒頭の設定 background_candidates と食い違います: {set(keys) ^ set(cand)}")
        if row["kind"] == "faq":
            if ocfg["faq"].get("placement") != "background":
                raise SystemExit("冒頭にFAQが出ている間は、背景にFAQの行を出さない（冒頭の設定 faq.placement）")
            n = len(ocfg["faq"]["items"])
            if any(not 0 <= k < n for k in row["from_opening"]) or len(set(row["from_opening"])) != len(row["from_opening"]):
                raise SystemExit("よくある質問の番号が冒頭の設定 faq.items に無いか、重なっています")
            qs = {ocfg["faq"]["items"][k]["q"] for k in row["from_opening"]}
            if qs & {a["q"] for a in ocfg["answers"]}:
                raise SystemExit("よくある質問に、冒頭の短答と同じ問いがあります")
        for ev in row.get("extra", []):
            if date.fromisoformat(ev["date"]) <= date.fromisoformat(ledger["checked_on"]) and not ev.get("before_ledger_reason"):
                raise SystemExit(f"年表に足す出来事 {ev['id']} は背景台帳の確認日より前です（台帳に無い理由を書く）")
            if ev["id"] in timeline_ids:
                raise SystemExit(f"年表に足す出来事 {ev['id']} は背景台帳にすでにあります")
        if row["kind"] == "classroom":
            cr = b["classroom"]
            for r in cr["reasons_pro"] + cr["reasons_con"]:
                if r["issue_id"] not in ids:
                    raise SystemExit(f"授業の設定の論点 {r['issue_id']} が公開JSONにありません")


# ---------------------------------------------------------------- 行の中身


def links(sources: list[dict]) -> str:
    """出典は1件ずつ別の行に並べる。"""
    return '<ul class="fb-src-list">' + "".join(
        f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["name"])}</a></li>' for s in sources) + "</ul>"


def issue_links(d: dict, row: dict) -> str:
    ids = row.get("issue_ids", [])
    if not ids:
        return ""
    names = {i["id"]: d["cfg"]["issues"][i["id"]].get("name") or i["label"] for i in d["public"]["issues"]}
    out = "、".join(f'<a href="#issue-{esc(i)}">{esc(names[i])}</a>' for i in ids)
    return f'<p class="fb-issues">関わる論点：{out}</p>'


def body_national(d: dict, row: dict, ctx: dict) -> str:
    ok = "".join(f"<li>{esc(t.format(**ctx['dates']))}</li>" for t in row["confirmed"])
    ng = "".join(f"<li>{esc(t.format(**ctx['dates']))}</li>" for t in row["unconfirmed"])
    return (f'<div class="fb-split"><div class="fb-ok"><h4>{esc(row["confirmed_label"])}</h4><ul>{ok}</ul></div>'
            f'<div class="fb-ng"><h4>{esc(row["unconfirmed_label"])}</h4><ul>{ng}</ul></div></div>'
            f'<p class="fb-cite">{esc(row["note"])}</p>'
            f'<div class="fb-cite" data-checked-on="{esc(d["ocfg"]["checked_on"])}">出典（{esc(ctx["dates"]["checked"])}に本文を確認）{links(row["sources"])}</div>')


def body_points(d: dict, row: dict, ctx: dict) -> str:
    out = [f'<p>{esc(row["lead"].format(**ctx["dates"]))}</p><dl class="fb-editorial">']
    for p in row["points"]:
        out.append(f'<div><dt>{esc(p["label"])}</dt><dd>{esc(p["text"])}</dd></div>')
    out.append("</dl>")
    if row.get("unconfirmed"):
        out.append(f'<p class="fb-unconfirmed">{esc(row["unconfirmed"])}</p>')
    out.append(f'<div class="fb-cite">出典{links(row["sources"])}</div>')
    return "".join(out)


def body_voices(d: dict, row: dict, ctx: dict) -> str:
    cand = d["ocfg"]["background_candidates"]["items"]
    names = {i["id"]: d["cfg"]["issues"][i["id"]].get("name") or i["label"] for i in d["public"]["issues"]}
    out = [f'<p class="fb-opinion-label">{esc(d["bg"]["cfg"]["opinion_label"])}</p><p>{esc(row["lead"])}</p><div class="fb-voices">']
    for it in row["items"]:
        v = cand[it["key"]]
        out.append(f'<section data-voice="{esc(it["key"])}"><h4>{esc(it["topic"])}</h4>'
                   f'<p><span class="fb-tag">期待</span>{esc(v["expectation"])}</p>'
                   f'<p><span class="fb-tag fb-tag-concern">懸念</span>{esc(v["concern"])}</p>'
                   f'<p class="fb-cite"><a class="fb-to-issue" href="#issue-{esc(it["issue_id"])}">論点「{esc(names[it["issue_id"]])}」の投稿を読む</a></p></section>')
    out.append("</div>")
    return "".join(out)


def body_ledger_text(d: dict, row: dict, ctx: dict) -> str:
    ledger = d["bg"]["ledger"]
    df = ledger["definition"]
    out = [f'<p class="fb-strong">{esc(df["one_line"])}</p><p>{esc(df["now"])}</p>']
    out += [f"<p>{esc(p)}</p>" for p in ledger["cause"]]
    out.append(f'<div class="fb-cite">出典{links(row["sources"])}（背景台帳の確認日 {esc(jp_date(ledger["checked_on"]))}）</div>')
    return "".join(out)


def body_timeline(d: dict, row: dict, ctx: dict) -> str:
    ledger = d["bg"]["ledger"]
    events = list(ledger["timeline"]) + [{**ev, "added": True} for ev in row.get("extra", [])]
    events.sort(key=lambda e: int(e["when"][:4]))  # 年の順。台帳の出来事と足した出来事を混ぜて並べる
    out = ['<ol class="fb-timeline">']
    for e in events:
        out.append(f'<li data-event="{esc(e["id"])}"{" data-added" if e.get("added") else ""}><p class="fb-when"><b>{esc(e["when"])}</b>{esc(e["era"])}</p>'
                   f'<p>{esc(e["text"])}</p><div class="fb-cite">出典{links(e["sources"])}</div></li>')
    out.append("</ol>")
    out.append(f'<p class="fb-strong" data-checked-on="{esc(d["ocfg"]["checked_on"])}">{esc(row["latest"].format(**ctx["dates"]))}</p>')
    out.append(f'<p class="fb-cite">背景台帳の確認日：{esc(jp_date(ledger["checked_on"]))}</p>')
    return "".join(out)


def body_faq(d: dict, row: dict, ctx: dict) -> str:
    items = [d["ocfg"]["faq"]["items"][k] for k in row["from_opening"]]
    out = ['<dl class="fb-faq">']
    for item in items:
        out.append(f'<div><dt>{esc(item["q"])}</dt><dd>{esc(item["a"])}</dd></div>')
    out.append("</dl>")
    out.append(f'<p class="fb-cite">国の資料の確認：{esc(ctx["dates"]["checked"])}時点</p>')
    return "".join(out)


def body_help(d: dict, row: dict, ctx: dict) -> str:
    phone = d["ocfg"]["safety"]["phone"]  # 番号は冒頭の設定の1か所（冒頭の案内にも同じ番号を出す）
    return (f'<p>{esc(row["text"])}</p>'
            f'<p class="fb-phone"><span>{esc(phone["label"])}</span><a href="tel:{esc(phone["tel"])}">{esc(phone["number"])}</a></p>'
            f'<p>{esc(row["more"])}</p><div class="fb-cite">出典（{esc(ctx["dates"]["checked"])}に確認）{links(row["sources"])}</div>')


def body_classroom(d: dict, row: dict, ctx: dict) -> str:
    cr = d["bg"]["classroom"]
    names = {i["id"]: d["cfg"]["issues"][i["id"]].get("name") or i["label"] for i in d["public"]["issues"]}
    out = [f'<p>{esc(row["intro"])}</p><div class="fb-sides">']
    for label, items in ((cr["pro_label"], cr["reasons_pro"]), (cr["con_label"], cr["reasons_con"])):
        out.append(f'<section><h4>{esc(label)}の理由</h4><ol>')
        for r in items:
            out.append(f'<li>{esc(r["text"])} <a class="fb-to-issue" href="#issue-{esc(r["issue_id"])}">論点「{esc(names[r["issue_id"]])}」へ</a></li>')
        out.append("</ol></section>")
    out.append("</div>")
    src = "".join(f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["title"])}</a>'
                  f'<span>{esc(s["note"])}</span></li>' for s in cr["primary_sources"])
    out.append(f'<p class="fb-src-label">{esc(row["sources_label"])}</p><ul class="fb-src">{src}</ul>')
    out.append(f'<p class="fb-src-label">{esc(row["questions_label"])}</p><ol class="fb-questions">'
               + "".join(f"<li>{esc(q)}</li>" for q in cr["questions"]) + "</ol>")
    return "".join(out)


def body_unverified(d: dict, row: dict, ctx: dict) -> str:
    items = "".join(f'<li>{esc(i["text"].format(**ctx["dates"]))}</li>' for i in row["items"])
    return f'<p>{esc(row["lead"])}</p><ul class="fb-unverified">{items}</ul>'


BODIES = {
    "national": body_national, "points": body_points, "voices": body_voices, "ledger_text": body_ledger_text,
    "timeline": body_timeline, "faq": body_faq, "help": body_help, "classroom": body_classroom, "unverified": body_unverified,
}


# ---------------------------------------------------------------- 全体


def render(d: dict, as_of: str, order: list[dict]) -> str:
    check(d)
    ctx = {"dates": dates(d)}
    cfg, public, ledger = d["bg"]["cfg"], d["public"], d["bg"]["ledger"]
    sec = cfg["section"]
    out = ['<section class="fb" id="school-nickname-ban-background" aria-labelledby="fb-title">',
           f'<p class="fr-eyebrow">{esc(sec["eyebrow"])}</p><h2 id="fb-title">{esc(sec["title"])}</h2>',
           f'<p class="fr-lead">{esc(sec["lead"])}</p>']
    for g in cfg["groups"]:
        out.append(f'<div class="fb-group" data-group="{esc(g["id"])}"><h3 class="fb-group-label">{esc(g["label"])}</h3>')
        for row in g["rows"]:
            body = BODIES[row["kind"]](d, row, ctx) + issue_links(d, row)
            rid = row.get("anchor") or f'bg-{row["id"]}'
            out.append(f'<details class="fb-row" id="{esc(rid)}" data-row="{esc(row["id"])}"><summary><span class="fb-title">{esc(row["title"])}</span>'
                       f'<span class="fb-sum">{esc(row["summary"])}</span></summary><div class="fb-body">{body}</div></details>')
        out.append("</div>")
    line = cfg["dates_line"].format(checked=jp_date(d["ocfg"]["checked_on"]), ledger_checked_on=jp_date(ledger["checked_on"]),
                                    updated_on=jp_date(public["updated_on"]), next_collect=ctx["dates"]["next_collect"])
    out.append(f'<p class="fr-footer">{esc(line)}</p>')
    out.append("</section>")
    return "\n".join(out) + "\n"
