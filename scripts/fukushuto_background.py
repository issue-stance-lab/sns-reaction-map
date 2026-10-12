#!/usr/bin/env python3
"""副首都ページの「背景として開く内容」（開閉行）を生成する部品。

scripts/fukushuto_reading.py から呼ぶ（単独では実行しない）。皇室の scripts/koshitsu_background.py と同じ型。

入力
- configs/fukushuto-background.json        : 行の名前・並び・手書きの文言（日付・件数は書かない）
- data/verification/fukushuto-background.json : 背景台帳（定義・cause・年表・未確認事項・確認日）
- configs/fukushuto-opening.json            : 成立日・公布日・施行予定日・施行の確認日・意見募集の日付・候補地8地域（冒頭と同じデータ）
- configs/classroom/fukushuto.json          : 授業向けの理由・資料・問い（既存の仕組みと共有。読むだけ）
- quality/research/fukushuto-primary-sources.md : 一次資料メモ（各資料の確認日、未確認の項目）
- THEMES.yaml・公開JSON                      : 更新日・収集期間の一致を確かめる

行はすべて <details> で、JavaScriptなしでも開ける。日付・件数を手で書かず、
台帳・メモ・登録簿と食い違ったら止まる。

時制は冒頭と同じ（fukushuto_opening.phase_of）。基準日で切り替え、施行日・締切を過ぎても生成は止めない。
- 法律: before ／ after_unconfirmed（law.enforcement_confirmed_on が null）／ after_confirmed
- 意見募集: open ／ closed（comment.result_published_on が null）／ published
段階ごとの文は設定の phase_now・phase_comment・events[].texts・faq の phase・unverified の hide_when に書く。
段階の文が設定に欠けていたら止める（未来形のまま公開しないため）。
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import yaml

import fukushuto_opening as opening

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "fukushuto-background.json"

esc = opening.esc
jp_date = opening.jp_date
LAW_PHASES = ("before", "after_unconfirmed", "after_confirmed")
COMMENT_PHASES = ("open", "closed", "published")


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
    law, comment = ocfg["law"], ocfg["comment"]
    return {
        "enacted": jp_date(law["enacted_on"]),
        "promulgated": jp_date(law["promulgated_on"]),
        "enforcement": jp_date(law["enforcement_on"]),
        "confirmed": jp_date(law["enforcement_confirmed_on"]) if law.get("enforcement_confirmed_on") else "",
        "closes": jp_date(comment["closes_on"]),
        "published": jp_date(comment["result_published_on"]) if comment.get("result_published_on") else "",
    }


def rows(cfg: dict):
    for g in cfg["groups"]:
        yield from g["rows"]


def check(d: dict, as_of: str) -> None:
    b, public, memo, ocfg = d["bg"], d["public"], d["memo"], d["ocfg"]
    cfg, ledger, theme = b["cfg"], b["ledger"], b["theme"]
    date.fromisoformat(as_of)
    opening.phase_of(ocfg, as_of)  # 施行の確認日などのありえない組み合わせはここで止まる
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
        if "phase_now" in row and set(row["phase_now"]) != set(LAW_PHASES):
            raise SystemExit(f"背景の行 {row['id']} の phase_now に3段階の文がそろっていません")
        if "phase_comment" in row and set(row["phase_comment"]) != set(COMMENT_PHASES):
            raise SystemExit(f"背景の行 {row['id']} の phase_comment に3段階の文がそろっていません")
        for tid in row.get("drop", []):
            if tid not in timeline_ids:
                raise SystemExit(f"年表から外す {tid} が背景台帳にありません")
        known = set(timeline_ids)
        for e in row.get("events", []):
            if e["after"] not in known:
                raise SystemExit(f"年表の差し込み先 {e['after']} がありません")
            known.add(e["id"])
            if not opening.lookup(ocfg, e["date_from"]):
                raise SystemExit(f"年表に差し込む日付 {e['date_from']} が冒頭の設定にありません")
            memo.checked_on(e["memo_section"])
            if e.get("phase"):
                need = LAW_PHASES if e["phase"] == "law" else COMMENT_PHASES
                if set(e["texts"]) != set(need):
                    raise SystemExit(f"年表 {e['id']} に段階ごとの era と text がそろっていません")
        if row["kind"] == "faq":
            for item in row["items"]:
                if "{enforcement}" in item["a"] or "施行" in item["q"]:
                    for ph in LAW_PHASES[1:]:
                        alt = item.get("phase", {}).get(ph, {})
                        if not alt.get("q") or not alt.get("a"):
                            raise SystemExit(f"よくある質問「{item['q']}」に施行後（{ph}）の q と a がありません")
        for key in row.get("from_ledger", []):
            if not ledger["checklist"].get(key):
                raise SystemExit(f"背景台帳の checklist.{key} がありません")
        for item in row.get("items", []):
            if item.get("memo_ref") and not memo.has_ref(item["memo_ref"]):
                raise SystemExit(f"一次資料メモに「{item['memo_ref']}」がありません")
            for group, phases in item.get("hide_when", {}).items():
                allowed = LAW_PHASES if group == "law" else COMMENT_PHASES
                if group not in ("law", "comment") or set(phases) - set(allowed):
                    raise SystemExit(f"未確認事項の hide_when が不正です: {item['text'][:20]}")
        if row["kind"] == "classroom":
            cr = b["classroom"]
            for r in cr["reasons_pro"] + cr["reasons_con"]:
                if r["issue_id"] not in ids:
                    raise SystemExit(f"授業の設定の論点 {r['issue_id']} が公開JSONにありません")
    stages = {s["key"] for s in ocfg["stages"]}
    if {c["stage"] for c in ocfg["candidates"]} - stages:
        raise SystemExit("冒頭の候補地に、凡例に無い段階があります")


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


def paragraphs(d: dict, row: dict) -> str:
    out = []
    for para in row.get("paragraphs", []):
        when = d["memo"].checked_on(para["memo_section"])
        out.append(f'<p>{esc(para["text"])}<span class="fb-checked">（一次資料メモの確認日 {esc(jp_date(when))}）</span></p>')
    return "".join(out)


def body_definition(d: dict, row: dict, ctx: dict) -> str:
    ledger = d["bg"]["ledger"]
    out = [f'<p class="fb-strong">{esc(ledger["definition"]["one_line"])}</p>', paragraphs(d, row)]
    out.append(f'<p data-phase="{ctx["law"]}">{esc(row["phase_now"][ctx["law"]].format(**ctx["dates"]))}</p>')
    out.append(f'<p class="fb-cite">出典：{links(row["sources"])}</p>')
    return "".join(out)


def body_cause(d: dict, row: dict, ctx: dict) -> str:
    ledger = d["bg"]["ledger"]
    out = [f"<p>{esc(p)}</p>" for p in ledger["cause"]]
    out.append(paragraphs(d, row))
    out.append(f'<p class="fb-cite">出典：{links(row["sources"])}（背景台帳の確認日 {esc(jp_date(ledger["checked_on"]))}）</p>')
    return "".join(out)


def body_selection(d: dict, row: dict, ctx: dict) -> str:
    out = [paragraphs(d, row)]
    out.append(f'<p data-phase="{ctx["comment"]}">{esc(row["phase_comment"][ctx["comment"]].format(**ctx["dates"]))}</p>')
    out.append(f'<p class="fb-cite">出典：{links(row["sources"])}</p>')
    return "".join(out)


def body_candidates(d: dict, row: dict, ctx: dict) -> str:
    ocfg = d["ocfg"]
    labels = {s["key"]: s["label"] for s in ocfg["stages"]}
    out = [f'<p>{esc(row["lead"])}<a href="{esc(row["map_link"]["href"])}">{esc(row["map_link"]["text"])}</a></p>',
           '<div class="fb-table-wrap" tabindex="0" role="region" aria-label="自治体の動き"><table class="fb-table fb-cand">'
           '<thead><tr><th scope="col">地域</th><th scope="col">段階</th><th scope="col">資料の内容</th><th scope="col">日付・資料</th></tr></thead><tbody>']
    for s in ocfg["stages"]:
        for c in (c for c in ocfg["candidates"] if c["stage"] == s["key"]):
            out.append(f'<tr><th scope="row">{esc(c["name"])}</th><td><span class="fop-key fop-key--{esc(c["stage"])}" aria-hidden="true"></span>{esc(labels[c["stage"]])}</td>'
                       f'<td>{esc(c["label"])}</td><td><a href="{esc(c["url"])}" target="_blank" rel="noopener noreferrer">'
                       f'<time datetime="{esc(c["date"])}">{esc(jp_date(c["date"]))}</time>・{esc(c["source"])}</a></td></tr>')
    out.append("</tbody></table></div>")
    out.append(f'<p class="fb-cite">{esc(ocfg["map"]["note"])}確認日 {esc(jp_date(ocfg["checked_on"]))}。</p>')
    return "".join(out)


def body_timeline(d: dict, row: dict, ctx: dict) -> str:
    ledger, ocfg, memo = d["bg"]["ledger"], d["ocfg"], d["memo"]
    events = [dict(t) for t in ledger["timeline"] if t["id"] not in row.get("drop", [])]
    for e in row.get("events", []):
        when = opening.lookup(ocfg, e["date_from"])
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
        if ctx["law"] != "before" and ctx["law"] in item.get("phase", {}):
            item = item["phase"][ctx["law"]]
        out.append(f'<div><dt>{esc(item["q"])}</dt><dd>{esc(item["a"].format(**ctx["dates"]))}</dd></div>')
    out.append("</dl>")
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
    items = [ledger["checklist"][k] for k in row["from_ledger"]]
    for i in row["items"]:
        if any(ctx[group] in phases for group, phases in i.get("hide_when", {}).items()):
            continue
        items.append(i["text"].format(**ctx["dates"]))
    return '<ul class="fb-unverified">' + "".join(f"<li>{esc(t)}</li>" for t in items) + "</ul>"


BODIES = {
    "definition": body_definition, "cause": body_cause, "selection": body_selection, "candidates": body_candidates,
    "timeline": body_timeline, "faq": body_faq, "classroom": body_classroom, "unverified": body_unverified,
}


# ---------------------------------------------------------------- 全体


def render(d: dict, as_of: str, order: list[dict]) -> str:
    check(d, as_of)
    law, comment = opening.phase_of(d["ocfg"], as_of)
    ctx = {"law": law, "comment": comment, "dates": dates(d["ocfg"])}
    cfg, public, memo, ledger = d["bg"]["cfg"], d["public"], d["memo"], d["bg"]["ledger"]
    sec = cfg["section"]
    out = [f'<section class="fb" id="fukushuto-background" aria-labelledby="fb-title" data-law-phase="{law}" data-comment-phase="{comment}">',
           f'<p class="fr-eyebrow">{esc(sec["eyebrow"])}</p><h2 id="fb-title">{esc(sec["title"])}</h2>',
           f'<p class="fr-lead">{esc(sec["lead"])}</p>']
    regions = len(d["ocfg"]["candidates"])
    for g in cfg["groups"]:
        out.append(f'<div class="fb-group" data-group="{esc(g["id"])}"><h3 class="fb-group-label">{esc(g["label"])}</h3>')
        for row in g["rows"]:
            kind = row["kind"]
            if kind not in BODIES:
                raise SystemExit(f"背景の行の種類 {kind} を知りません")
            title = row.get("title") or row["title_template"].format(regions=regions)
            body = BODIES[kind](d, row, ctx) + issue_links(d, row)
            out.append(f'<details class="fb-row" id="bg-{esc(row["id"])}"><summary><span class="fb-title">{esc(title)}</span>'
                       f'<span class="fb-sum">{esc(row["summary"])}</span></summary><div class="fb-body">{body}</div></details>')
        out.append("</div>")
    line = cfg["dates_line"].format(ledger_checked_on=jp_date(ledger["checked_on"]), opening_checked_on=jp_date(d["ocfg"]["checked_on"]),
                                    memo_latest=jp_date(memo.latest()), updated_on=jp_date(public["updated_on"]))
    out.append(f'<p class="fr-footer">{esc(line)}{esc(cfg["phase_note"].format(as_of=jp_date(as_of)))}</p>')
    out.append("</section>")
    return "\n".join(out) + "\n"
