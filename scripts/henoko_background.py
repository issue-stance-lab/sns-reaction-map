#!/usr/bin/env python3
"""辺野古高校生死亡事故ページの「背景として開く内容」（開閉行）を生成する部品。

scripts/henoko_reading.py から呼ぶ（単独では実行しない）。学校でのあだ名禁止の scripts/nickname_background.py と同じ型。
「◯月◯日時点」は冒頭の設定の checked_on（一次資料を確かめた日、1か所だけ）から作る。あだ名と違うのは次の点。
- 年表の行（kind "timeline"）は、冒頭の設定 timeline.entries を正本として読む（冒頭の部品 henoko_opening.event_items で描く）。
  背景台帳 data/verification/henoko-student-accident-background.json の timeline は使わない（手順7まで現行ページだけが読む）。
  冒頭の設定 timeline.placement が "background" でないと止まる（冒頭と背景に同じ年表が出るのを防ぐ）。
- 公的機関の公表と未公表の行（kind "official"）は、公表された資料に書かれていることを並べ、その下に冒頭の設定の
  未公表欄（運輸安全委員会の報告書は report の段階で文が変わる）を henoko_opening.render_pending_items で描く。
  各論点の根拠欄の最後のリンク（#bg-official）と、冒頭の短答「まだ公表されていないものを見る」の行き先。
- よくある質問（kind "faq"）は、冒頭の設定 faq.items を番号で読む（文は二重に持たない）。冒頭の設定 faq.placement が
  "background" でないと止まる。冒頭の短答と同じ問いがあっても止まる。
- 用語（kind "terms"）は、言葉ごとに出典を持つ。

入力
- configs/henoko-student-accident-background.json : 行の名前・並び・手書きの文言（SNSの件数・日付は書かない）
- data/verification/henoko-student-accident-background.json : 背景台帳（なぜ議論になるのか・確認日）
- configs/henoko-student-accident-opening.json : checked_on・report・年表・未公表欄・FAQ
- configs/classroom/henoko-student-accident.json : 授業向けの理由・資料・問い（既存の仕組みと共有。読むだけ）
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

import henoko_opening as opening

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "henoko-student-accident-background.json"
KINDS = ("timeline", "official", "faq", "terms", "ledger_text", "classroom", "unverified")


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
            "next_collect": jp_date(str(nxt), False) if nxt else "未定",
            "report_status": opening.report_text(d["ocfg"], "status"),
            "report_short": opening.report_text(d["ocfg"], "short").rstrip("。")}


def rows(cfg: dict):
    for g in cfg["groups"]:
        yield from g["rows"]


def anchor(row: dict) -> str:
    return row.get("anchor") or f'bg-{row["id"]}'


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
    all_rows = list(rows(cfg))
    anchors = [anchor(r) for r in all_rows]
    if len(anchors) != len(set(anchors)) or len({r["id"] for r in all_rows}) != len(all_rows):
        raise SystemExit("背景の行のIDかアンカーが重なっています")
    # 読書面と冒頭からのリンクの行き先がそろっているか
    needed = {d["cfg"]["sources_common"]["official_href"][1:]}
    needed |= {a["link"]["href"][1:] for a in ocfg["answers"] if a["link"]["href"].startswith("#bg-")}
    if needed - set(anchors):
        raise SystemExit(f"冒頭・読書面からのリンク先の行がありません: {needed - set(anchors)}")
    for row in all_rows:
        if row["kind"] not in KINDS:
            raise SystemExit(f"背景の行の種類 {row['kind']} を知りません")
        for iid in row.get("issue_ids", []):
            if iid not in ids:
                raise SystemExit(f"背景の行 {row['id']} の論点 {iid} が公開JSONにありません")
        if row["kind"] == "timeline" and ocfg["timeline"].get("placement") != "background":
            raise SystemExit("冒頭に年表が出ている間は、背景に年表の行を出さない（冒頭の設定 timeline.placement）")
        if row["kind"] == "official":
            if ocfg["timeline"].get("placement") != "background":
                raise SystemExit("冒頭に未公表欄が出ている間は、背景に公表と未公表の行を出さない")
            for p in row["points"]:
                if not p.get("sources"):
                    raise SystemExit(f"公表の行の {p['label']} に出典がありません")
        if row["kind"] == "terms":
            for t in row["items"]:
                if not t.get("sources"):
                    raise SystemExit(f"用語 {t['term']} に出典がありません")
        if row["kind"] == "faq":
            if ocfg["faq"].get("placement") != "background":
                raise SystemExit("冒頭にFAQが出ている間は、背景にFAQの行を出さない（冒頭の設定 faq.placement）")
            n = len(ocfg["faq"]["items"])
            if any(not 0 <= k < n for k in row["from_opening"]) or len(set(row["from_opening"])) != len(row["from_opening"]):
                raise SystemExit("よくある質問の番号が冒頭の設定 faq.items に無いか、重なっています")
            qs = {ocfg["faq"]["items"][k]["q"] for k in row["from_opening"]}
            if qs & {a["question"] for a in ocfg["answers"]}:
                raise SystemExit("よくある質問に、冒頭の短答と同じ問いがあります")
        if row["kind"] == "ledger_text":
            if not row.get("sources"):
                raise SystemExit(f"背景の行 {row['id']} に出典がありません")
            if any(not 0 <= k < len(ledger["cause"]) for k in row["cause_paragraphs"]):
                raise SystemExit(f"背景の行 {row['id']} の cause_paragraphs が背景台帳の cause にありません")
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
    out = "／".join(f'<a href="#issue-{esc(i)}">{esc(names[i])}</a>' for i in ids)  # 論点名に読点があるので／で区切る
    return f'<p class="fb-issues">関わる論点：{out}</p>'


def body_timeline(d: dict, row: dict, ctx: dict) -> str:
    tl = d["ocfg"]["timeline"]
    year = date.fromisoformat(tl["entries"][0]["date"]).year
    return (f'<p class="fb-cite">{esc(tl["kind_label"])}・{year}年</p>'
            f'<ol class="hop-events">{"".join(opening.event_items(d["ocfg"]))}</ol>'
            f'<p class="fb-cite">{esc(tl["note"])}</p>'
            f'<p class="fb-cite" data-checked-on="{esc(d["ocfg"]["checked_on"])}">'
            f'{esc(d["ocfg"]["checked_note"].format(checked=ctx["dates"]["checked"]))}</p>')


def body_official(d: dict, row: dict, ctx: dict) -> str:
    tl = d["ocfg"]["timeline"]
    out = [f'<p>{esc(row["lead"].format(**ctx["dates"]))}</p><dl class="fb-official">']
    for p in row["points"]:
        out.append(f'<div><dt>{esc(p["label"])}</dt><dd>{esc(p["text"])}{links(p["sources"])}</dd></div>')
    out.append("</dl>")
    pending_note = tl["pending_note_template"].format(checked=ctx["dates"]["checked"])
    out.append(f'<div class="hop-pending"><h4>{esc(tl["pending_title"])}</h4>'
               f'<ol class="hop-events">{opening.render_pending_items(d["ocfg"])}</ol>'
               f'<p class="hop-pending__note">{esc(pending_note)}</p></div>')
    out.append(f'<p class="fb-unconfirmed">{esc(row["not_decided"])}</p>')
    return "".join(out)


def body_faq(d: dict, row: dict, ctx: dict) -> str:
    items = [d["ocfg"]["faq"]["items"][k] for k in row["from_opening"]]
    out = ['<dl class="fb-faq">']
    for item in items:
        src = item.get("source")
        cite = (f' <a href="{esc(src["url"])}" target="_blank" rel="noopener noreferrer">{esc(src["label"])}</a>' if src else "")
        out.append(f'<div><dt>{esc(item["q"])}</dt><dd>{esc(item["a"])}{cite}</dd></div>')
    out.append("</dl>")
    out.append(f'<p class="fb-cite">{esc(row["note"].format(**ctx["dates"]))}</p>')
    return "".join(out)


def body_terms(d: dict, row: dict, ctx: dict) -> str:
    out = ['<dl class="fb-terms">']
    for t in row["items"]:
        out.append(f'<div><dt>{esc(t["term"])}</dt><dd>{esc(t["text"])}{links(t["sources"])}</dd></div>')
    out.append("</dl>")
    return "".join(out)


def body_ledger_text(d: dict, row: dict, ctx: dict) -> str:
    ledger = d["bg"]["ledger"]
    out = [f'<p class="fb-strong">{esc(ledger["definition"]["now"])}</p>']
    out += [f"<p>{esc(ledger['cause'][k])}</p>" for k in row["cause_paragraphs"]]
    out.append(f'<div class="fb-cite">出典{links(row["sources"])}（背景台帳の確認日 {esc(jp_date(ledger["checked_on"]))}）</div>')
    return "".join(out)


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
    out.append(f'<p class="fb-cite">{esc(row["note"])}</p>')
    return "".join(out)


def body_unverified(d: dict, row: dict, ctx: dict) -> str:
    phase = opening.report_phase(d["ocfg"])
    items = "".join(f'<li>{esc(i["text"].format(**ctx["dates"]))}</li>' for i in row["items"]
                    if phase not in i.get("hide_when_report", []))
    return f'<p>{esc(row["lead"])}</p><ul class="fb-unverified">{items}</ul>'


BODIES = {
    "timeline": body_timeline, "official": body_official, "faq": body_faq, "terms": body_terms,
    "ledger_text": body_ledger_text, "classroom": body_classroom, "unverified": body_unverified,
}


# ---------------------------------------------------------------- 全体


def render(d: dict, as_of: str, order: list[dict]) -> str:
    check(d)
    ctx = {"dates": dates(d)}
    cfg, public, ledger = d["bg"]["cfg"], d["public"], d["bg"]["ledger"]
    sec = cfg["section"]
    phase = opening.report_phase(d["ocfg"])
    out = [f'<section class="fb" id="henoko-student-accident-background" aria-labelledby="fb-title" data-report-phase="{phase}">',
           f'<p class="fr-eyebrow">{esc(sec["eyebrow"])}</p><h2 id="fb-title">{esc(sec["title"])}</h2>',
           f'<p class="fr-lead">{esc(sec["lead"])}</p>']
    for g in cfg["groups"]:
        out.append(f'<div class="fb-group" data-group="{esc(g["id"])}"><h3 class="fb-group-label">{esc(g["label"])}</h3>')
        for row in g["rows"]:
            body = BODIES[row["kind"]](d, row, ctx) + issue_links(d, row)
            summary = row["summary"].format(**ctx["dates"])
            out.append(f'<details class="fb-row" id="{esc(anchor(row))}" data-row="{esc(row["id"])}"><summary><span class="fb-title">{esc(row["title"])}</span>'
                       f'<span class="fb-sum">{esc(summary)}</span></summary><div class="fb-body">{body}</div></details>')
        out.append("</div>")
    line = cfg["dates_line"].format(checked=jp_date(d["ocfg"]["checked_on"]), ledger_checked_on=jp_date(ledger["checked_on"]),
                                    updated_on=jp_date(public["updated_on"]), next_collect=ctx["dates"]["next_collect"])
    out.append(f'<p class="fr-footer">{esc(line)}</p>')
    out.append("</section>")
    return "\n".join(out) + "\n"
