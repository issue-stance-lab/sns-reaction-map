#!/usr/bin/env python3
"""消費税減税ページの「背景として開く内容」（開閉行）を生成する部品。

scripts/consumption_tax_reading.py から呼ぶ（単独では実行しない）。辺野古（scripts/henoko_background.py）と同じ型で、
このテーマ固有の点は次のとおり。
- 時制：冒頭の設定 law と同じ判定関数（consumption_tax_opening.phase_of）で、基準日（--as-of）ごとに
  審議中→成立→引下げ中→終了→成立未確認 の5段階を決める。設定の文が段階ごとの辞書なら、その段階の文を使う
  （無ければ "all"）。hide_in に書いた段階では項目を出さない。
- 年表の後半（大綱・法律案・成立・予約販売の区切り・引下げ開始・終わり）は、冒頭の設定 steps.items と law を読み、
  冒頭の段階図と同じ判定（consumption_tax_opening.step_states）で状態を付ける。日付も状態も二重に持たない。
- 税率の数字は冒頭の設定 rates から差し込む（手で書かない）。
- 制度の行の項目は一次資料メモの節（memo_section）を指し、節の確認日が法律案の提出日より前か、冒頭の checked_on
  より後なら止まる（年表の前半と各党の案は、法律案の前の出来事なので提出日の条件は外す）。
- 0%案と各党の案（政党名・法案名）は、この背景の行でだけ扱う。
- 授業向けの欄は configs/classroom/consumption-tax-cut.json を読むだけ（既存の仕組みに残す）。

入力
- configs/consumption-tax-cut-background.json : 行の名前・並び・手書きの文言（SNSの件数は書かない）
- configs/consumption-tax-cut-opening.json : law・rates・steps・checked_on（読書面の生成器が読んだもの）
- configs/classroom/consumption-tax-cut.json : 授業向けの理由・資料・問い（読むだけ）
- THEMES.yaml・公開JSON : 更新日・収集期間の一致、次回の収集予定
- quality/research/consumption-tax-cut-primary-sources.md : 項目ごとの節の確認日

行はすべて <details> で、初期状態は閉じる。JavaScriptなしでも開ける。
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from html import escape
from pathlib import Path

import yaml

import consumption_tax_opening as opening

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "consumption-tax-cut-background.json"
KINDS = ("system", "status", "timeline", "parties", "faq", "classroom", "unverified")
# 法律案の前の出来事を書く行（提出日より前に確かめた節を指してよい）
BEFORE_BILL_OK = ("timeline", "parties")


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
    return {
        "cfg": cfg,
        "classroom": json.loads((ROOT / inp["classroom"]).read_text(encoding="utf-8")),
        "theme": themes["themes"][cfg["theme_id"]],
    }


def values(d: dict, as_of: str) -> dict:
    """文に差し込む値。法律の日付と段階の言葉は冒頭と同じ関数から、税率は冒頭の設定 rates から作る。"""
    ocfg, public, theme = d["ocfg"], d["public"], d["bg"]["theme"]
    v = dict(opening.values_for(ocfg, as_of))
    v["transition"] = jp_date(ocfg["law"]["transition_on"])
    for key, rate in ocfg["rates"].items():
        if key.startswith("_"):
            continue
        for part in ("total", "national", "local"):
            v[f"{key}_{part}"] = rate[part]
    after = date.fromisoformat(public["collection_period"]["end"]) + timedelta(days=1)
    nxt = theme.get("collect_at")
    v["after"] = jp_date(after.isoformat(), False)
    v["next_collect"] = jp_date(str(nxt), False) if nxt else "未定"
    v["updated_on"] = jp_date(public["updated_on"])
    return v


def txt(value, ctx: dict) -> str:
    """段階ごとの辞書なら段階の文（無ければ all）を選び、値を差し込む。"""
    if isinstance(value, dict):
        value = opening.by_phase(value, ctx["phase"])
    return value.format(**ctx["v"])


def shown(item: dict, ctx: dict) -> bool:
    return ctx["phase"] not in item.get("hide_in", []) and bool(txt(item.get("text", item.get("a", "x")), ctx))


def rows(cfg: dict):
    for g in cfg["groups"]:
        yield from g["rows"]


def anchor(row: dict) -> str:
    return row.get("anchor") or f'bg-{row["id"]}'


def memo_items(row: dict) -> list[dict]:
    out = []
    for key in ("items", "decided", "pending", "before"):
        out += [i for i in row.get(key, []) if isinstance(i, dict) and i.get("memo_section")]
    return out


def check(d: dict) -> None:
    b, public, ocfg = d["bg"], d["public"], d["ocfg"]
    cfg, theme = b["cfg"], b["theme"]
    if str(theme["updated_at"]) != public["updated_on"]:
        raise SystemExit(f"THEMES.yaml の updated_at {theme['updated_at']} と公開JSONの updated_on {public['updated_on']} が違います")
    period = f'{public["collection_period"]["start"]}〜{public["collection_period"]["end"]}'
    if str(theme["sample_period"]) != period:
        raise SystemExit(f"THEMES.yaml の sample_period {theme['sample_period']} と公開JSONの収集期間 {period} が違います")
    ids = {i["id"] for i in public["issues"]}
    all_rows = list(rows(cfg))
    anchors = [anchor(r) for r in all_rows]
    if len(anchors) != len(set(anchors)) or len({r["id"] for r in all_rows}) != len(all_rows):
        raise SystemExit("背景の行のIDかアンカーが重なっています")
    checked = date.fromisoformat(ocfg["checked_on"])
    bill_on = date.fromisoformat(ocfg["law"]["bill_on"])
    opening_questions = {a["question"] for a in ocfg["answers"]}
    step_keys = {s["key"] for s in ocfg["steps"]["items"]}
    for row in all_rows:
        if row["kind"] not in KINDS:
            raise SystemExit(f"背景の行の種類 {row['kind']} を知りません")
        for iid in row.get("issue_ids", []):
            if iid not in ids:
                raise SystemExit(f"背景の行 {row['id']} の論点 {iid} が公開JSONにありません")
        for item in memo_items(row):
            when = date.fromisoformat(d["memo"].checked_on(item["memo_section"]))
            if when > checked:
                raise SystemExit(f"背景の行 {row['id']} の節「{item['memo_section']}」の確認日が冒頭の checked_on より後です")
            if when < bill_on and row["kind"] not in BEFORE_BILL_OK:
                raise SystemExit(f"背景の行 {row['id']} の節「{item['memo_section']}」は法律案の提出より前に確かめたものです")
        for key in ("items", "decided", "pending"):
            for item in row.get(key, []):
                if row["kind"] in ("system", "status", "faq") and not item.get("sources"):
                    raise SystemExit(f"背景の行 {row['id']} に出典の無い項目があります")
                for ph in item.get("hide_in", []):
                    if ph not in opening.PHASES:
                        raise SystemExit(f"背景の行 {row['id']} の hide_in に知らない段階 {ph} があります")
        if row["kind"] == "faq":
            same = {i["q"] for i in row["items"]} & opening_questions
            if same:
                raise SystemExit(f"よくある質問に、冒頭の短答と同じ問いがあります: {same}")
        if row["kind"] == "timeline":
            if set(row["step_sources"]) != step_keys:
                raise SystemExit("年表の step_sources が冒頭の設定 steps.items の段と一致しません")
            if any(e["date"] >= ocfg["law"]["outline_on"] for e in row["before"]):
                raise SystemExit("年表の before は大綱より前の出来事だけ（大綱から後は冒頭の steps を読む）")
        if row["kind"] == "classroom":
            cr = b["classroom"]
            for r in cr["reasons_pro"] + cr["reasons_con"]:
                if r["issue_id"] not in ids:
                    raise SystemExit(f"授業の設定の論点 {r['issue_id']} が公開JSONにありません")
    # 冒頭・読書面からのリンクの行き先
    needed = {a["link"]["href"][1:] for a in ocfg["answers"] if a["link"]["href"].startswith("#bg-")}
    for icfg in d["cfg"]["issues"].values():
        needed |= {l["href"][1:] for l in icfg.get("see_also", []) if l["href"].startswith("#bg-") or l["href"] == "#tax-faq"}
    if needed - set(anchors):
        raise SystemExit(f"冒頭・読書面からのリンク先の行がありません: {needed - set(anchors)}")


# ---------------------------------------------------------------- 行の中身


def links(sources: list[dict]) -> str:
    if not sources:
        return ""
    return '<ul class="fb-src-list">' + "".join(
        f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["name"])}</a></li>' for s in sources) + "</ul>"


def issue_links(d: dict, row: dict) -> str:
    ids = row.get("issue_ids", [])
    if not ids:
        return ""
    names = {i["id"]: d["cfg"]["issues"][i["id"]].get("name") or i["label"] for i in d["public"]["issues"]}
    out = "／".join(f'<a href="#issue-{esc(i)}">{esc(names[i])}</a>' for i in ids)
    return f'<p class="fb-issues">関わる論点：{out}</p>'


def checked_line(d: dict, ctx: dict) -> str:
    return (f'<p class="fb-cite" data-checked-on="{esc(d["ocfg"]["checked_on"])}">'
            f'{esc(txt(d["bg"]["cfg"]["checked_line"], ctx))}</p>')


def body_system(d: dict, row: dict, ctx: dict) -> str:
    out = ['<dl class="fb-terms">']
    for item in row["items"]:
        if not shown(item, ctx):
            continue
        out.append(f'<div><dt>{esc(item["label"])}</dt><dd>{esc(txt(item["text"], ctx))}{links(item["sources"])}</dd></div>')
    out.append("</dl>")
    return "".join(out) + checked_line(d, ctx)


def body_status(d: dict, row: dict, ctx: dict) -> str:
    out = []
    for key, title in (("decided", "decided_title"), ("pending", "pending_title")):
        items = [i for i in row[key] if shown(i, ctx)]
        if not items:
            continue
        out.append(f'<h4 data-status="{key}">{esc(txt(row[title], ctx))}</h4><ul class="fb-unverified">')
        out += [f'<li>{esc(txt(i["text"], ctx))}{links(i["sources"])}</li>' for i in items]
        out.append("</ul>")
    return "".join(out) + checked_line(d, ctx)


def body_timeline(d: dict, row: dict, ctx: dict) -> str:
    ocfg = d["ocfg"]
    labels = ocfg["phase_text"]["state_labels"]
    out = ['<ol class="fb-timeline">']
    for e in row["before"]:
        out.append(f'<li data-state="done"><p class="fb-when"><b>{esc(jp_date(e["date"]))}</b><span>{esc(labels["done"])}</span></p>'
                   f'<p class="fb-strong">{esc(e["title"])}</p><p>{esc(txt(e["text"], ctx))}</p>{links(e["sources"])}</li>')
    states = opening.step_states(ocfg, ctx["as_of"])
    for step, state in zip(ocfg["steps"]["items"], states):
        when = opening.lookup(ocfg, step.get("date_from"))
        day = jp_date(when) if when else ""
        if step["key"] == "enact":
            note = step["note_done"] if state in ("done", "current") else step["note_undecided"]
            if ocfg["law"].get("promulgated_on") and state in ("done", "current"):
                note = step["note_promulgated"]
        else:
            note = step["note"]
        state_label = labels[state].format(as_of=ctx["v"]["as_of"])
        when_html = f'<b>{esc(day)}</b><span>{esc(state_label)}</span>' if when else f'<b>{esc(state_label)}</b>'
        out.append(f'<li data-state="{esc(state)}" data-step="{esc(step["key"])}"><p class="fb-when">{when_html}</p>'
                   f'<p class="fb-strong">{esc(step["title"])}</p><p>{esc(note.format(diet=ctx["v"]["diet"], promulgated=ctx["v"]["promulgated"]))}</p>'
                   f'{links(row["step_sources"][step["key"]])}</li>')
    out.append("</ol>")
    return "".join(out) + checked_line(d, ctx)


def body_parties(d: dict, row: dict, ctx: dict) -> str:
    out = [f'<p>{esc(txt(row["lead"], ctx))}</p><dl class="fb-terms">']
    for item in row["items"]:
        out.append(f'<div><dt>{esc(item["label"])}</dt><dd>{esc(txt(item["text"], ctx))}{links(item["sources"])}</dd></div>')
    out.append("</dl>")
    out.append(f'<p class="fb-cite">{esc(txt(row["note"], ctx))}</p>')
    return "".join(out)


def body_faq(d: dict, row: dict, ctx: dict) -> str:
    out = ['<dl class="fb-faq">']
    for item in row["items"]:
        if ctx["phase"] in item.get("hide_in", []):
            continue
        out.append(f'<div><dt>{esc(item["q"])}</dt><dd>{esc(txt(item["a"], ctx))}{links(item["sources"])}</dd></div>')
    out.append("</dl>")
    out.append(f'<p class="fb-cite">{esc(txt(row["note"], ctx))}</p>')
    return "".join(out) + checked_line(d, ctx)


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
    items = "".join(f'<li>{esc(txt(i["text"], ctx))}</li>' for i in row["items"] if shown(i, ctx))
    return f'<p>{esc(row["lead"])}</p><ul class="fb-unverified">{items}</ul>'


BODIES = {
    "system": body_system, "status": body_status, "timeline": body_timeline, "parties": body_parties,
    "faq": body_faq, "classroom": body_classroom, "unverified": body_unverified,
}


# ---------------------------------------------------------------- 全体


def render(d: dict, as_of: str, order: list[dict]) -> str:
    check(d)
    phase = opening.phase_of(d["ocfg"], as_of)
    ctx = {"phase": phase, "as_of": as_of, "v": values(d, as_of)}
    cfg = d["bg"]["cfg"]
    sec = cfg["section"]
    out = [f'<section class="fb" id="consumption-tax-cut-background" aria-labelledby="fb-title" data-phase="{phase}">',
           f'<p class="fr-eyebrow">{esc(sec["eyebrow"])}</p><h2 id="fb-title">{esc(sec["title"])}</h2>',
           f'<p class="fr-lead">{esc(sec["lead"])}</p>']
    for g in cfg["groups"]:
        out.append(f'<div class="fb-group" data-group="{esc(g["id"])}"><h3 class="fb-group-label">{esc(g["label"])}</h3>')
        for row in g["rows"]:
            body = BODIES[row["kind"]](d, row, ctx) + issue_links(d, row)
            out.append(f'<details class="fb-row" id="{esc(anchor(row))}" data-row="{esc(row["id"])}"><summary>'
                       f'<span class="fb-title">{esc(row["title"])}</span>'
                       f'<span class="fb-sum">{esc(txt(row["summary"], ctx))}</span></summary><div class="fb-body">{body}</div></details>')
        out.append("</div>")
    out.append(f'<p class="fr-footer">{esc(txt(cfg["dates_line"], ctx))}</p>')
    out.append("</section>")
    return "\n".join(out) + "\n"
