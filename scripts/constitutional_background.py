#!/usr/bin/env python3
"""憲法改正論議ページの「背景として開く内容」（開閉行）を生成する部品。

scripts/constitutional_reading.py から呼ぶ（単独では実行しない）。生成AIの scripts/ai_copyright_background.py と同じ型。

入力
- configs/constitutional-amendment-background.json : 行の名前・並び・手書きの文言（日付・件数は書かない）
- data/verification/constitutional-amendment-background.json : 背景台帳（定義・なぜ始まったか・年表・checklist・確認日）
- configs/constitutional-amendment-opening.json : 制度の確認日 checked_on と国民投票法の改正の日付 law（冒頭と同じデータ）
- configs/classroom/constitutional-amendment.json : 授業向けの理由・資料・問い（既存の仕組みと共有。読むだけ）
- quality/research/constitutional-amendment-primary-sources.md : 一次資料メモ（各資料の確認日、未確認の項目）
- THEMES.yaml・公開JSON : 更新日・収集期間の一致を確かめる

行はすべて <details> で、初期状態は閉じる。JavaScriptなしでも開ける。日付・件数を手で書かず、
台帳・メモ・登録簿と食い違ったら止まる。

時制は冒頭と同じ（constitutional_opening.phase_of）。基準日で切り替え、施行日を過ぎても生成は止めない。
- 国民投票法の改正: before ／ after_unconfirmed（law.enforcement_confirmed_on が null）／ after_confirmed
段階ごとの文は設定の phase_law・events[].texts・unverified の hide_when に書く。欠けていたら止める。
"""

from __future__ import annotations

import json
from datetime import date
from html import escape
from pathlib import Path

import yaml

import constitutional_opening as opening

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "constitutional-amendment-background.json"
LAW_PHASES = opening.LAW_PHASES
KINDS = ("article", "rules", "points", "ledger_text", "timeline", "faq", "classroom", "unverified")


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


def dates(ocfg: dict) -> dict:
    return {"checked": jp_date(ocfg["checked_on"]), **opening.law_values(ocfg)}


def rows(cfg: dict):
    for g in cfg["groups"]:
        yield from g["rows"]


def check(d: dict, as_of: str) -> None:
    b, public, memo, ocfg = d["bg"], d["public"], d["memo"], d["ocfg"]
    cfg, ledger, theme = b["cfg"], b["ledger"], b["theme"]
    opening.phase_of(ocfg, as_of)  # 施行の確認日のありえない組み合わせはここで止まる
    if str(theme["updated_at"]) != public["updated_on"]:
        raise SystemExit(f"THEMES.yaml の updated_at {theme['updated_at']} と公開JSONの updated_on {public['updated_on']} が違います")
    period = f'{public["collection_period"]["start"]}〜{public["collection_period"]["end"]}'
    if theme["sample_period"] != period:
        raise SystemExit(f"THEMES.yaml の sample_period {theme['sample_period']} と公開JSONの収集期間 {period} が違います")
    ids = {i["id"] for i in public["issues"]}
    timeline_ids = {t["id"] for t in ledger["timeline"]}
    seen = set()
    for row in rows(cfg):
        if row["id"] in seen:
            raise SystemExit(f"背景の行 {row['id']} が2回あります")
        seen.add(row["id"])
        if row["kind"] not in KINDS:
            raise SystemExit(f"背景の行の種類 {row['kind']} を知りません")
        for iid in row.get("issue_ids", []):
            if iid not in ids:
                raise SystemExit(f"背景の行 {row['id']} の論点 {iid} が公開JSONにありません")
        for part in row.get("paragraphs", []) + row.get("points", []) + [i for i in row.get("items", []) if "memo_section" in i]:
            memo.checked_on(part["memo_section"])
        if row["kind"] in ("rules",) and set(row.get("phase_law", {})) != set(LAW_PHASES):
            raise SystemExit(f"背景の行 {row['id']} の phase_law に施行の3段階の文がそろっていません")
        for it in row.get("items", []):
            if it.get("memo_ref") and not memo.has_ref(it["memo_ref"]):
                raise SystemExit(f"一次資料メモに「{it['memo_ref']}」がありません")
            for group, phases in it.get("hide_when", {}).items():
                if group != "law" or set(phases) - set(LAW_PHASES):
                    raise SystemExit(f"未確認事項の hide_when が不正です: {it['text'][:20]}")
        for tid, over in row.get("overrides", {}).items():
            if tid not in timeline_ids:
                raise SystemExit(f"年表の差し替え先 {tid} が背景台帳にありません")
            if over.get("memo_section"):
                memo.checked_on(over["memo_section"])
        known = set(timeline_ids)
        for e in row.get("events", []):
            if e["after"] not in known:
                raise SystemExit(f"年表の差し込み先 {e['after']} がありません")
            known.add(e["id"])
            date.fromisoformat(lookup(ocfg, e["date_from"]))
            memo.checked_on(e["memo_section"])
            if e.get("phase") and set(e["texts"]) != set(LAW_PHASES):
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
    """出典は1件ずつ別の行に並べる（「／」でつなぐと1文に数えられて長くなる）。"""
    return '<ul class="fb-src-list">' + "".join(
        f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["name"])}</a></li>' for s in sources) + "</ul>"


def issue_links(d: dict, row: dict) -> str:
    ids = row.get("issue_ids", [])
    if not ids:
        return ""
    names = {i["id"]: d["cfg"]["issues"][i["id"]].get("name") or i["label"] for i in d["public"]["issues"]}
    out = "、".join(f'<a href="#issue-{esc(i)}">{esc(names[i])}</a>' for i in ids)
    return f'<p class="fb-issues">関わる論点：{out}</p>'


def memo_note(d: dict, section: str) -> str:
    return f'<span class="fb-checked">（一次資料メモの確認日 {esc(jp_date(d["memo"].checked_on(section)))}）</span>'


def body_article(d: dict, row: dict, ctx: dict) -> str:
    paras = "".join(f'<p>{esc(p["text"])}{memo_note(d, p["memo_section"])}</p>' for p in row["paragraphs"])
    return (f'<blockquote class="fb-quote">{esc(row["quote"])}<cite>{esc(row["quote_cite"])}</cite></blockquote>'
            + paras + f'<p class="fb-strong">{esc(row["now"].format(**ctx["dates"]))}</p>'
            f'<div class="fb-cite">出典{links(row["sources"])}</div>')


def body_rules(d: dict, row: dict, ctx: dict) -> str:
    out = [f'<p>{esc(row["lead"])}</p><dl class="fb-editorial">']
    for it in row["items"]:
        out.append(f'<div><dt>{esc(it["label"])}</dt><dd>{esc(it["text"])}{memo_note(d, it["memo_section"])}</dd></div>')
    out.append("</dl>")
    out.append(f'<p class="fb-strong" data-phase="{ctx["law"]}">{esc(row["phase_law"][ctx["law"]].format(**ctx["dates"]))}</p>')
    out.append(f'<div class="fb-cite">出典{links(row["sources"])}</div>')
    return "".join(out)


def body_points(d: dict, row: dict, ctx: dict) -> str:
    out = [f'<p>{esc(row["lead"])}</p><dl class="fb-editorial">']
    for p in row["points"]:
        out.append(f'<div><dt>{esc(p["label"])}</dt><dd>{esc(p["text"])}{memo_note(d, p["memo_section"])}</dd></div>')
    out.append("</dl>")
    out.append(f'<div class="fb-cite">出典{links(row["sources"])}</div>')
    return "".join(out)


def body_ledger_text(d: dict, row: dict, ctx: dict) -> str:
    ledger = d["bg"]["ledger"]
    df = ledger["definition"]
    out = [f'<p class="fb-strong">{esc(df["one_line"])}</p><p>{esc(df["now"])}</p>']
    out += [f"<p>{esc(p)}</p>" for p in ledger["cause"]]
    out.append(f'<div class="fb-cite">出典{links(ledger["cause_sources"])}（背景台帳の確認日 {esc(jp_date(ledger["checked_on"]))}）</div>')
    return "".join(out)


def body_timeline(d: dict, row: dict, ctx: dict) -> str:
    ledger, ocfg, memo = d["bg"]["ledger"], d["ocfg"], d["memo"]
    events = []
    for t in ledger["timeline"]:
        e = dict(t)
        over = row.get("overrides", {}).get(t["id"])
        if over:
            for key in ("when", "era", "text", "sources"):
                if key in over:
                    e[key] = over[key]
            if over.get("memo_section"):
                e["checked"] = memo.checked_on(over["memo_section"])
        e["text"] = e["text"].format(**ctx["dates"])
        events.append(e)
    for e in row.get("events", []):
        when = lookup(ocfg, e["date_from"])
        t = e["texts"][ctx[e["phase"]]] if e.get("phase") else e
        item = {"id": e["id"], "when": jp_date(when), "era": t["era"], "text": t["text"].format(**ctx["dates"]),
                "sources": e["sources"], "checked": memo.checked_on(e["memo_section"])}
        pos = next(i for i, x in enumerate(events) if x["id"] == e["after"])
        events.insert(pos + 1, item)
    out = ['<ol class="fb-timeline">']
    for e in events:
        checked = f'（一次資料メモの確認日 {jp_date(e["checked"])}）' if e.get("checked") else ""
        out.append(f'<li data-event="{esc(e["id"])}"><p class="fb-when"><b>{esc(e["when"])}</b>{esc(e["era"])}</p>'
                   f'<p>{esc(e["text"])}</p><div class="fb-cite">出典{links(e["sources"])}{esc(checked)}</div></li>')
    out.append("</ol>")
    out.append(f'<p class="fb-cite">背景台帳の確認日：{esc(jp_date(ledger["checked_on"]))}</p>')
    return "".join(out)


def body_faq(d: dict, row: dict, ctx: dict) -> str:
    out = ['<dl class="fb-faq">']
    for item in row["items"]:
        out.append(f'<div><dt>{esc(item["q"])}</dt><dd>{esc(item["a"].format(**ctx["dates"]))}'
                   f'{memo_note(d, item["memo_section"])}</dd></div>')
    out.append("</dl>")
    out.append(f'<p class="fb-cite">制度の確認：{esc(ctx["dates"]["checked"])}時点</p>')
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
    ledger = d["bg"]["ledger"]
    texts = []
    for key in row.get("from_ledger", []):
        texts += [t.strip() for t in ledger["checklist"][key].split("。 ") if t.strip()]
    texts = [t if t.endswith("。") else t + "。" for t in texts]
    for i in row["items"]:
        if any(ctx[group] in phases for group, phases in i.get("hide_when", {}).items()):
            continue
        texts.append(i["text"].format(**ctx["dates"]))
    return '<ul class="fb-unverified">' + "".join(f"<li>{esc(t)}</li>" for t in texts) + "</ul>"


BODIES = {
    "article": body_article, "rules": body_rules, "points": body_points, "ledger_text": body_ledger_text,
    "timeline": body_timeline, "faq": body_faq, "classroom": body_classroom, "unverified": body_unverified,
}


# ---------------------------------------------------------------- 全体


def render(d: dict, as_of: str, order: list[dict]) -> str:
    check(d, as_of)
    law = opening.phase_of(d["ocfg"], as_of)
    ctx = {"law": law, "dates": dates(d["ocfg"])}
    cfg, public, memo, ledger = d["bg"]["cfg"], d["public"], d["memo"], d["bg"]["ledger"]
    sec = cfg["section"]
    out = [f'<section class="fb" id="constitutional-amendment-background" aria-labelledby="fb-title" data-law-phase="{law}">',
           f'<p class="fr-eyebrow">{esc(sec["eyebrow"])}</p><h2 id="fb-title">{esc(sec["title"])}</h2>',
           f'<p class="fr-lead">{esc(sec["lead"])}</p>']
    for g in cfg["groups"]:
        out.append(f'<div class="fb-group" data-group="{esc(g["id"])}"><h3 class="fb-group-label">{esc(g["label"])}</h3>')
        for row in g["rows"]:
            body = BODIES[row["kind"]](d, row, ctx) + issue_links(d, row)
            out.append(f'<details class="fb-row" id="bg-{esc(row["id"])}"><summary><span class="fb-title">{esc(row["title"])}</span>'
                       f'<span class="fb-sum">{esc(row["summary"])}</span></summary><div class="fb-body">{body}</div></details>')
        out.append("</div>")
    line = cfg["dates_line"].format(checked=jp_date(d["ocfg"]["checked_on"]), ledger_checked_on=jp_date(ledger["checked_on"]),
                                    memo_latest=jp_date(memo.latest()), updated_on=jp_date(public["updated_on"]))
    out.append(f'<p class="fr-footer">{esc(line)}{esc(cfg["phase_note"].format(as_of=jp_date(as_of)))}</p>')
    out.append("</section>")
    return "\n".join(out) + "\n"
