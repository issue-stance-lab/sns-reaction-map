#!/usr/bin/env python3
"""生成AIと著作権ページの「背景として開く内容」（開閉行）を生成する部品。

scripts/ai_copyright_reading.py から呼ぶ（単独では実行しない）。副首都の scripts/fukushuto_background.py と同じ型。

入力
- configs/ai-copyright-background.json       : 行の名前・並び・手書きの文言（日付・件数は書かない）
- data/verification/ai-copyright-background.json : 背景台帳（定義・年表・checklist・確認日）
- configs/ai-copyright-opening.json           : 制度の確認日 checked_on とプリンシプル・コードの日付（冒頭と同じデータ）
- configs/classroom/ai-copyright.json         : 授業向けの理由・資料・問い（既存の仕組みと共有。読むだけ）
- quality/research/ai-copyright-primary-sources.md : 一次資料メモ（各資料の確認日、未確認の項目）
- THEMES.yaml・公開JSON                        : 更新日・収集期間の一致を確かめる

行はすべて <details> で、JavaScriptなしでも開ける。日付・件数を手で書かず、
台帳・メモ・登録簿と食い違ったら止まる。

時制: このテーマには施行日のような期限付きの制度イベントは無い。制度の記述は冒頭の設定 checked_on
（確認日、1か所）から「◯月◯日時点」を作る。プリンシプル・コードの届出の開始日だけは基準日で切り替える。
- 届出: before（基準日が開始日より前）／ after_unconfirmed（開始日を過ぎ、filing_confirmed_on が null）／ after_confirmed
段階ごとの文は設定の phase_filing・events[].texts・unverified の hide_when に書く。欠けていたら止める。
"""

from __future__ import annotations

import json
from datetime import date
from html import escape
from pathlib import Path

import yaml

import ai_copyright_opening as opening

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "ai-copyright-background.json"
FILING_PHASES = ("before", "after_unconfirmed", "after_confirmed")


def esc(value: object) -> str:
    return escape(str(value), quote=True)


def jp_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.year}年{d.month}月{d.day}日"


def lookup(cfg: dict, dotted: str):
    node = cfg
    for part in dotted.split("."):
        node = node[part]
    return node


def filing_phase(ocfg: dict, as_of: str) -> str:
    pc = ocfg["principle_code"]
    date.fromisoformat(as_of)
    confirmed = pc.get("filing_confirmed_on")
    if confirmed and confirmed < pc["filing_starts_on"]:
        raise SystemExit("届出開始の確認日が開始日より前です")
    if as_of < pc["filing_starts_on"]:
        if confirmed:
            raise SystemExit("基準日が届出の開始日より前なのに、開始の確認日が入っています")
        return "before"
    if confirmed and confirmed <= as_of:
        return "after_confirmed"
    return "after_unconfirmed"


def load(d: dict, config_path: Path = CONFIG) -> dict:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    if cfg["theme_id"] != d["public"]["theme_id"]:
        raise SystemExit("背景の設定と公開JSONのテーマが一致しません")
    opening.check_words(cfg, config_path.name)
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


def dates(ocfg: dict) -> dict:
    pc = ocfg["principle_code"]
    return {
        "checked": jp_date(ocfg["checked_on"]),
        "filing_starts": jp_date(pc["filing_starts_on"]),
        "filing_confirmed": jp_date(pc["filing_confirmed_on"]) if pc.get("filing_confirmed_on") else "",
    }


def rows(cfg: dict):
    for g in cfg["groups"]:
        yield from g["rows"]


def check(d: dict, as_of: str) -> None:
    b, public, memo, ocfg = d["bg"], d["public"], d["memo"], d["ocfg"]
    cfg, ledger, theme = b["cfg"], b["ledger"], b["theme"]
    filing_phase(ocfg, as_of)
    if str(theme["updated_at"]) != public["updated_on"]:
        raise SystemExit(f"THEMES.yaml の updated_at {theme['updated_at']} と公開JSONの updated_on {public['updated_on']} が違います")
    period = f'{public["collection_period"]["start"]}〜{public["collection_period"]["end"]}'
    if theme["sample_period"] != period:
        raise SystemExit(f"THEMES.yaml の sample_period {theme['sample_period']} と公開JSONの収集期間 {period} が違います")
    ids = {i["id"] for i in public["issues"]}
    timeline_ids = {t["id"] for t in ledger["timeline"]}
    for row in rows(cfg):
        for iid in row.get("issue_ids", []):
            if iid not in ids:
                raise SystemExit(f"背景の行 {row['id']} の論点 {iid} が公開JSONにありません")
        for para in row.get("paragraphs", []):
            memo.checked_on(para["memo_section"])
        for key in ("memo_section",):
            if row.get(key):
                memo.checked_on(row[key])
        for it in row.get("items", []):
            if it.get("memo_section"):
                memo.checked_on(it["memo_section"])
            if it.get("memo_ref") and not memo.has_ref(it["memo_ref"]):
                raise SystemExit(f"一次資料メモに「{it['memo_ref']}」がありません")
            for group, phases in it.get("hide_when", {}).items():
                if group != "filing" or set(phases) - set(FILING_PHASES):
                    raise SystemExit(f"未確認事項の hide_when が不正です: {it['text'][:20]}")
            if "phase_filing" in it and set(it["phase_filing"]) != set(FILING_PHASES):
                raise SystemExit(f"よくある質問「{it['q']}」に届出の3段階の文がそろっていません")
        if "phase_filing" in row and set(row["phase_filing"]) != set(FILING_PHASES):
            raise SystemExit(f"背景の行 {row['id']} の phase_filing に3段階の文がそろっていません")
        for tid in row.get("text_overrides", {}):
            if tid not in timeline_ids:
                raise SystemExit(f"年表の言い換え先 {tid} が背景台帳にありません")
        known = set(timeline_ids)
        for e in row.get("events", []):
            if e["after"] not in known:
                raise SystemExit(f"年表の差し込み先 {e['after']} がありません")
            known.add(e["id"])
            date.fromisoformat(lookup(ocfg, e["date_from"]))
            memo.checked_on(e["memo_section"])
            if e.get("phase") and set(e["texts"]) != set(FILING_PHASES):
                raise SystemExit(f"年表 {e['id']} に段階ごとの era と text がそろっていません")
        for key in row.get("from_ledger", []):
            if not ledger["checklist"].get(key):
                raise SystemExit(f"背景台帳の checklist.{key} がありません")
        if row["kind"] == "classroom":
            cr = b["classroom"]
            for r in cr["reasons_pro"] + cr["reasons_con"]:
                if r["issue_id"] not in ids:
                    raise SystemExit(f"授業の設定の論点 {r['issue_id']} が公開JSONにありません")
        if row["kind"] == "points" and not row.get("points"):
            raise SystemExit(f"背景の行 {row['id']} に要点がありません")


# ---------------------------------------------------------------- 行の中身


def links(sources: list[dict]) -> str:
    return " ／ ".join(f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["name"])}</a>'
                       for s in sources)


def issue_links(d: dict, row: dict) -> str:
    ids = row.get("issue_ids", [])
    if not ids:
        return ""
    names = {i["id"]: d["cfg"]["issues"][i["id"]].get("name") or i["label"] for i in d["public"]["issues"]}
    out = "、".join(f'<a href="#issue-{esc(i)}">{esc(names[i])}</a>' for i in ids)
    return f'<p class="fb-issues">関わる論点：{out}</p>'


def memo_note(d: dict, section: str) -> str:
    return f'<span class="fb-checked">（一次資料メモの確認日 {esc(jp_date(d["memo"].checked_on(section)))}）</span>'


def paragraphs(d: dict, row: dict) -> str:
    return "".join(f'<p>{esc(p["text"])}{memo_note(d, p["memo_section"])}</p>' for p in row.get("paragraphs", []))


def body_article(d: dict, row: dict, ctx: dict) -> str:
    out = [f'<blockquote class="fb-quote">{esc(row["quote"])}<cite>{esc(row["quote_cite"])}</cite></blockquote>',
           paragraphs(d, row), f'<p class="fb-strong">{esc(row["now"].format(**ctx["dates"]))}</p>',
           f'<p class="fb-cite">出典：{links(row["sources"])}</p>']
    return "".join(out)


def body_points(d: dict, row: dict, ctx: dict) -> str:
    out = [f'<p>{esc(row["lead"])}{memo_note(d, row["memo_section"])}</p><dl class="fb-editorial">']
    for p in row["points"]:
        out.append(f'<div><dt>{esc(p["label"])}</dt><dd>{esc(p["text"])}<span class="fb-checked">（{esc(p["location"])}）</span></dd></div>')
    out.append("</dl>")
    out.append(f'<p class="fb-cite">出典：{links(row["sources"])}</p>')
    return "".join(out)


def body_rules(d: dict, row: dict, ctx: dict) -> str:
    ledger = d["bg"]["ledger"]
    out = [f'<p>{esc(ledger["checklist"][k])}</p>' for k in row.get("from_ledger", [])]
    out.append('<dl class="fb-editorial">')
    for it in row["items"]:
        out.append(f'<div><dt>{esc(it["label"])}</dt><dd>{esc(it["text"])}{memo_note(d, it["memo_section"])}</dd></div>')
    out.append("</dl>")
    out.append(f'<p data-phase="{ctx["filing"]}">{esc(row["phase_filing"][ctx["filing"]].format(**ctx["dates"]))}</p>')
    out.append(f'<p class="fb-cite">出典：{links(row["sources"])}</p>')
    return "".join(out)


def body_timeline(d: dict, row: dict, ctx: dict) -> str:
    ledger, ocfg, memo = d["bg"]["ledger"], d["ocfg"], d["memo"]
    events = []
    for t in ledger["timeline"]:
        e = dict(t)
        if t["id"] in row.get("text_overrides", {}):
            e["text"] = row["text_overrides"][t["id"]]
        events.append(e)
    for e in row.get("events", []):
        when = lookup(ocfg, e["date_from"])
        if e.get("phase"):
            t = e["texts"][ctx[e["phase"]]]
            era, text = t["era"], t["text"]
        else:
            era, text = e["era"], e["text"]
        item = {"id": e["id"], "when": jp_date(when), "era": era, "text": text.format(**ctx["dates"]),
                "sources": e["sources"], "checked": memo.checked_on(e["memo_section"])}
        pos = next(i for i, x in enumerate(events) if x["id"] == e["after"])
        events.insert(pos + 1, item)
    out = ['<ol class="fb-timeline">']
    for e in events:
        checked = f'（一次資料メモの確認日 {jp_date(e["checked"])}）' if e.get("checked") else ""
        out.append(f'<li data-event="{esc(e["id"])}"><p class="fb-when"><b>{esc(e["when"])}</b>{esc(e["era"])}</p>'
                   f'<p>{esc(e["text"])}</p><p class="fb-cite">出典：{links(e["sources"])}{esc(checked)}</p></li>')
    out.append("</ol>")
    out.append(f'<p class="fb-cite">背景台帳の確認日：{esc(jp_date(ledger["checked_on"]))}</p>')
    return "".join(out)


def body_faq(d: dict, row: dict, ctx: dict) -> str:
    out = ['<dl class="fb-faq">']
    for item in row["items"]:
        a = item["a"]
        if "phase_filing" in item:
            a = a + item["phase_filing"][ctx["filing"]]
        out.append(f'<div><dt>{esc(item["q"])}</dt><dd>{esc(a.format(**ctx["dates"]))}</dd></div>')
    out.append("</dl>")
    out.append(f'<p class="fb-cite">制度の確認：{esc(ctx["dates"]["checked"])}時点{memo_note(d, row["memo_section"])}</p>')
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
    return "".join(out)


def body_unverified(d: dict, row: dict, ctx: dict) -> str:
    items = []
    for i in row["items"]:
        if any(ctx[group] in phases for group, phases in i.get("hide_when", {}).items()):
            continue
        items.append(i["text"].format(**ctx["dates"]))
    return '<ul class="fb-unverified">' + "".join(f"<li>{esc(t)}</li>" for t in items) + "</ul>"


BODIES = {
    "article": body_article, "points": body_points, "rules": body_rules, "timeline": body_timeline,
    "faq": body_faq, "classroom": body_classroom, "unverified": body_unverified,
}


# ---------------------------------------------------------------- 全体


def render(d: dict, as_of: str, order: list[dict]) -> str:
    check(d, as_of)
    filing = filing_phase(d["ocfg"], as_of)
    ctx = {"filing": filing, "dates": dates(d["ocfg"])}
    cfg, public, memo, ledger = d["bg"]["cfg"], d["public"], d["memo"], d["bg"]["ledger"]
    sec = cfg["section"]
    out = [f'<section class="fb" id="ai-copyright-background" aria-labelledby="fb-title" data-filing-phase="{filing}">',
           f'<p class="fr-eyebrow">{esc(sec["eyebrow"])}</p><h2 id="fb-title">{esc(sec["title"])}</h2>',
           f'<p class="fr-lead">{esc(sec["lead"])}</p>']
    for g in cfg["groups"]:
        out.append(f'<div class="fb-group" data-group="{esc(g["id"])}"><h3 class="fb-group-label">{esc(g["label"])}</h3>')
        for row in g["rows"]:
            kind = row["kind"]
            if kind not in BODIES:
                raise SystemExit(f"背景の行の種類 {kind} を知りません")
            body = BODIES[kind](d, row, ctx) + issue_links(d, row)
            out.append(f'<details class="fb-row" id="bg-{esc(row["id"])}"><summary><span class="fb-title">{esc(row["title"])}</span>'
                       f'<span class="fb-sum">{esc(row["summary"])}</span></summary><div class="fb-body">{body}</div></details>')
        out.append("</div>")
    line = cfg["dates_line"].format(checked=jp_date(d["ocfg"]["checked_on"]), ledger_checked_on=jp_date(ledger["checked_on"]),
                                    memo_latest=jp_date(memo.latest()), updated_on=jp_date(public["updated_on"]))
    out.append(f'<p class="fr-footer">{esc(line)}{esc(cfg["phase_note"].format(as_of=jp_date(as_of)))}</p>')
    out.append("</section>")
    return "\n".join(out) + "\n"
