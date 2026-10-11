#!/usr/bin/env python3
"""皇室典範改正ページの「背景として開く内容」（開閉行）を生成する部品。

scripts/koshitsu_reading.py から呼ぶ（単独では実行しない）。

入力
- configs/koshitsu-tenpakai-background.json : 行の名前・並び・手書きの文言（日付・件数は書かない）
- data/verification/koshitsu-tenpakai-background.json : 背景台帳（cause・年表・未確認事項・確認日）
- scripts/koshitsu_background_detail.py の SECTIONS : 制度の解説本文（現行ページと同じ文。読むだけ）
- quality/research/koshitsu-tenpakai-primary-sources.md : 一次資料メモ（各資料の確認日、未確認の項目）
- THEMES.yaml : 公開日・更新日・次回更新予定・収集元
- configs/theme-seo.json : 収集方法の文
- 公開JSON・冒頭の設定 : 件数・立場・成立日・公布日・施行日

行はすべて <details> で、JavaScriptなしでも開ける。日付・件数を手で書かず、
台帳・メモ・登録簿と食い違ったら止まる。
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import yaml

import koshitsu_opening as opening
from koshitsu_background_detail import LAW as DETAIL_LAW, SECTIONS as DETAIL_SECTIONS

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "koshitsu-tenpakai-background.json"

esc = opening.esc
fmt = opening.fmt
ja_date = opening.ja_date
DATE_RE = re.compile(r"確認日[:：]\s*(\d{4}-\d{2}-\d{2})")


# ---------------------------------------------------------------- 一次資料メモ


class Memo:
    """一次資料メモを見出しで引く。確認日は節の中の「確認日：YYYY-MM-DD」の最新を使う。"""

    def __init__(self, path: Path):
        self.text = path.read_text(encoding="utf-8")
        self.lines = self.text.splitlines()

    def section(self, heading: str) -> str:
        """`### 資料K` のような見出しで始まる節。同じ見出しが2つ以上あれば止める。"""
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

    def has_date(self, iso: str) -> bool:
        return iso in self.text

    def has_ref(self, ref: str) -> bool:
        """「確認できなかったこと 7」は節の中の番号付きの項目、それ以外は見出し。"""
        m = re.fullmatch(r"(.+?) (\d+)", ref)
        if m:
            body = self.section(m.group(1))
            return re.search(rf"^{m.group(2)}\. ", body, flags=re.M) is not None
        self.section(ref)
        return True


# ---------------------------------------------------------------- 読み込みと照合


def load(public: dict, ocfg: dict, config_path: Path = CONFIG) -> dict:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    if cfg["theme_id"] != public["theme_id"]:
        raise SystemExit("背景の設定と公開JSONのテーマが一致しません")
    inp = cfg["inputs"]
    themes = yaml.safe_load((ROOT / inp["themes_yaml"]).read_text(encoding="utf-8"))
    theme = themes["themes"][cfg["theme_id"]]
    seo = json.loads((ROOT / inp["theme_seo"]).read_text(encoding="utf-8"))
    seo_entry = next((t for t in seo["themes"] if t["id"] == cfg["theme_id"]), None)
    if seo_entry is None or "collection" not in seo_entry:
        raise SystemExit("configs/theme-seo.json にこのテーマの収集方法の文がありません")
    return {
        "cfg": cfg,
        "ocfg": ocfg,
        "public": public,
        "ledger": json.loads((ROOT / inp["background_ledger"]).read_text(encoding="utf-8")),
        "memo": Memo(ROOT / inp["primary_memo"]),
        "theme": theme,
        "seo": seo_entry,
    }


def check(b: dict, as_of: str) -> None:
    cfg, public, ledger, memo, theme, law = b["cfg"], b["public"], b["ledger"], b["memo"], b["theme"], b["ocfg"]["law"]
    if date.fromisoformat(as_of) >= date.fromisoformat(law["enforcement_on"]):
        raise SystemExit("施行日を過ぎました。背景の年表とよくある質問の時制を見直してから生成してください")
    if str(theme["updated_at"]) != public["updated_on"]:
        raise SystemExit(f"THEMES.yaml の updated_at {theme['updated_at']} と公開JSONの updated_on {public['updated_on']} が違います")
    period = f'{public["collection_period"]["start"]}〜{public["collection_period"]["end"]}'
    if theme["sample_period"] != period:
        raise SystemExit(f"THEMES.yaml の sample_period {theme['sample_period']} と公開JSONの収集期間 {period} が違います")
    if not memo.has_date(ledger["checked_on"]):
        raise SystemExit(f"背景台帳の確認日 {ledger['checked_on']} が一次資料メモにありません")
    timeline_ids = {t["id"] for t in ledger["timeline"]}
    n_sections = len(DETAIL_SECTIONS)
    for g in cfg["groups"]:
        for row in g["rows"]:
            for key in ("section_index", "also_section_index"):
                if key in row and not 0 <= row[key] < n_sections:
                    raise SystemExit(f"背景の行 {row['id']}: {key} {row[key]} が SECTIONS の範囲外です")
            for ins in row.get("insert", []):
                if ins["after"] not in timeline_ids:
                    raise SystemExit(f"年表の差し込み先 {ins['after']} が背景台帳にありません")
                if not law.get(ins["date_key"]):
                    raise SystemExit(f"年表に差し込む日付 law.{ins['date_key']} が冒頭の設定にありません")
                memo.checked_on(ins["memo_section"])
            for item in row.get("items", []):
                if "memo_ref" in item and not memo.has_ref(item["memo_ref"]):
                    raise SystemExit(f"一次資料メモに「{item['memo_ref']}」がありません")
            for key in row.get("from_ledger", []):
                if not ledger["checklist"].get(key):
                    raise SystemExit(f"背景台帳の checklist.{key} がありません")
            for iid in row.get("issue_ids", []) + [i.get("issue_id") for s in row.get("sides", []) for i in s["items"]]:
                if iid and iid not in {i["id"] for i in public["issues"]}:
                    raise SystemExit(f"背景の行 {row['id']} の論点 {iid} が公開JSONにありません")


# ---------------------------------------------------------------- 行の中身


def sources_list(items: list[dict], label: str) -> str:
    rows = "".join(f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["name"])}</a>'
                   + (f'<span>{esc(s["note"])}</span>' if s.get("note") else "") + "</li>" for s in items)
    return f'<p class="kb-src-label">{esc(label)}</p><ul class="kb-src">{rows}</ul>'


def detail_section(index: int, with_title: bool) -> str:
    title, body, url, label = DETAIL_SECTIONS[index]
    srcs = [{"name": label, "url": url}]
    if title.startswith(("検討", "女性")):  # 現行ページと同じく、改正後の条文へのリンクを添える
        srcs.append({"name": "改正後の条文", "url": DETAIL_LAW})
    out = [f"<h4>{esc(title)}</h4>" if with_title else ""]
    out += [f"<p>{esc(p)}</p>" for p in body]
    links = " ／ ".join(f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["name"])}</a>' for s in srcs)
    out.append(f'<p class="kb-cite">出典：{links}</p>')
    return "".join(out)


def law_dates(ocfg: dict) -> dict:
    law = ocfg["law"]
    return {"enacted": ja_date(law["enacted_on"]), "promulgated": ja_date(law["promulgated_on"]),
            "enforcement": ja_date(law["enforcement_on"])}


def issue_links(row: dict, labels: dict) -> str:
    ids = row.get("issue_ids", [])
    if not ids:
        return ""
    links = "、".join(f'<a href="#issue-{esc(i)}">{esc(labels[i])}</a>' for i in ids)
    return f'<p class="kb-issues">関わる論点：{links}</p>'


def body_detail(b: dict, row: dict) -> str:
    out = []
    if row.get("lead_from_ledger"):
        out += [f"<p>{esc(p)}</p>" for p in b["ledger"][row["lead_from_ledger"]]]
    out.append(detail_section(row["section_index"], with_title=bool(out)))
    if "also_section_index" in row:
        out.append(detail_section(row["also_section_index"], with_title=True))
    return "".join(out)


def body_timeline(b: dict, row: dict) -> str:
    law, memo = b["ocfg"]["law"], b["memo"]
    events = []
    for t in b["ledger"]["timeline"]:
        events.append(t)
        for ins in row.get("insert", []):
            if ins["after"] == t["id"]:
                events.append({"id": ins["id"], "when": ja_date(law[ins["date_key"]]), "era": ins["era"],
                               "text": ins["text"], "sources": ins["sources"],
                               "checked": memo.checked_on(ins["memo_section"])})
    out = ['<ol class="kb-timeline">']
    for e in events:
        links = " ／ ".join(f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["name"])}</a>'
                            for s in e["sources"])
        checked = f'（一次資料メモの確認日 {ja_date(e["checked"])}）' if e.get("checked") else ""
        out.append(f'<li data-event="{esc(e["id"])}"><p class="kb-when"><b>{esc(e["when"])}</b>{esc(e["era"])}</p>'
                   f'<p>{esc(e["text"])}</p><p class="kb-cite">出典：{links}{esc(checked)}</p></li>')
    out.append("</ol>")
    out.append(f'<p class="kb-cite">背景台帳の確認日：{esc(ja_date(b["ledger"]["checked_on"]))}</p>')
    return "".join(out)


def body_faq(b: dict, row: dict) -> str:
    dates = law_dates(b["ocfg"])
    out = ['<dl class="kb-faq">']
    for item in row["items"]:
        out.append(f'<div><dt>{esc(item["q"])}</dt><dd>{esc(item["a"].format(**dates))}</dd></div>')
    out.append("</dl>")
    return "".join(out)


def body_classroom(b: dict, row: dict, labels: dict) -> str:
    out = [f'<p>{esc(row["intro"])}</p><div class="kb-sides">']
    for side in row["sides"]:
        out.append(f'<section><h4>{esc(side["label"])}</h4><ol>')
        for item in side["items"]:
            link = (f' <a class="kb-to-issue" href="#issue-{esc(item["issue_id"])}">論点「{esc(labels[item["issue_id"]])}」へ</a>'
                    if item.get("issue_id") else "")
            out.append(f'<li>{esc(item["text"])}{link}</li>')
        out.append("</ol></section>")
    out.append("</div>")
    out.append(sources_list(row["sources"], row["sources_label"]))
    out.append(f'<p class="kb-src-label">{esc(row["questions_label"])}</p><ol class="kb-questions">'
               + "".join(f"<li>{esc(q)}</li>" for q in row["questions"]) + "</ol>")
    out.append(f'<p>{esc(row["howto"])}</p>')
    return "".join(out)


def body_table(b: dict, row: dict, order: list[dict], labels: dict) -> str:
    public = b["public"]
    stance_ids = [s["id"] for s in public["issues"][0]["stances"]]
    stance_names = {s["id"]: s["label"] for s in public["issues"][0]["stances"]}
    totals = opening.stance_totals(public)
    head = "".join(f'<th scope="col">{esc(stance_names[s])}</th>' for s in stance_ids)
    rows = []
    for issue in order:
        by = {s["id"]: int(s["count"]) for s in issue["stances"]}
        if [s["id"] for s in issue["stances"]] != stance_ids:
            raise SystemExit(f"{issue['id']}: 立場の並びがほかの論点と違います")
        cells = "".join(f"<td>{fmt(by[s])}</td>" for s in stance_ids)
        rows.append(f'<tr><th scope="row">{esc(labels.get(issue["id"], issue["label"]))}</th>'
                    f'<td><b>{fmt(int(issue["count"]))}</b></td>{cells}</tr>')
    foot = "".join(f"<td>{fmt(totals[s])}</td>" for s in stance_ids)
    rows.append(f'<tr class="kb-total"><th scope="row">合計</th><td><b>{fmt(int(public["opinion_count"]))}</b></td>{foot}</tr>')
    caption = row["caption"].format(opinion_count=fmt(int(public["opinion_count"])))
    notes = "".join(f"<li>{esc(n)}</li>" for n in row["notes"])
    return (f'<p class="kb-table-cap">{esc(caption)}</p>'
            f'<div class="kb-table-wrap" tabindex="0" role="region" aria-label="{esc(caption)}"><table class="kb-table">'
            f'<thead><tr><th scope="col">論点</th><th scope="col">計</th>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div><ul class="kb-notes">{notes}</ul>')


def body_method(b: dict, row: dict) -> str:
    public, theme, seo = b["public"], b["theme"], b["seo"]
    collection = seo["collection"].format(total=fmt(int(public["collected_count"])),
                                          opinions=fmt(int(public["opinion_count"])))
    period = public["collection_period"]
    fe = next(int(i["count"]) for i in public["issues"] if i["id"] == "koshitsu-tenpakai-female-emperor")
    facts = [
        ("公開日", ja_date(str(theme["published_at"]))),
        ("最終更新日", ja_date(public["updated_on"])),
        ("次回の更新予定", ja_date(str(theme["refresh_at"]))),
        ("収集期間", f'{ja_date(period["start"])}〜{ja_date(period["end"])}'),
        ("収集元", theme["sample_source"]),
        ("編集・分析", row["publisher"]),
    ]
    out = ['<dl class="kb-facts">' + "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in facts) + "</dl>"]
    out.append(f"<p>{esc(collection)}</p>")
    out.append(f'<p>{esc(row["observation"].format(female_emperor_count=fmt(fe)))}</p>')
    out.append(f'<p class="kb-strong">{esc(row["not_poll"])}</p>')
    ed = public["editorial_summary"]
    kinds = row["editorial_kinds"]
    out.append(f'<h4>{esc(row["editorial_title"])}</h4><dl class="kb-editorial">')
    for f in ed["findings"]:
        if f["kind"] not in kinds:
            raise SystemExit(f"編集部の整理に設定に無い種類 {f['kind']} があります")
        out.append(f'<div><dt>{esc(kinds[f["kind"]])}</dt><dd>{esc(f["text"])}</dd></div>')
    out.append(f'</dl><p class="kb-cite">編集部の整理の確認日：{esc(ja_date(ed["checked_on"]))}</p>')
    c = row["contact"]
    out.append(f'<p>{esc(c["text"])}<a href="{esc(c["href"])}">{esc(c["label"])}</a></p>')
    return "".join(out)


def body_unverified(b: dict, row: dict) -> str:
    items = [b["ledger"]["checklist"][k] for k in row["from_ledger"]] + [i["text"] for i in row["items"]]
    return '<ul class="kb-unverified">' + "".join(f"<li>{esc(t)}</li>" for t in items) + "</ul>"


# ---------------------------------------------------------------- 全体


def render(b: dict, as_of: str, order: list[dict], labels: dict) -> str:
    check(b, as_of)
    cfg, public, memo = b["cfg"], b["public"], b["memo"]
    sec = cfg["section"]
    out = ['<section class="kb" id="koshitsu-background" aria-labelledby="kb-title">',
           f'<p class="kr-eyebrow">{esc(sec["eyebrow"])}</p><h2 id="kb-title">{esc(sec["title"])}</h2>',
           f'<p class="kr-lead">{esc(sec["lead"])}</p>']
    for g in cfg["groups"]:
        out.append(f'<div class="kb-group" data-group="{esc(g["id"])}"><h3 class="kb-group-label">{esc(g["label"])}</h3>')
        for row in g["rows"]:
            kind = row["kind"]
            if kind == "detail_section":
                body = body_detail(b, row) + issue_links(row, labels)
            elif kind == "timeline":
                body = body_timeline(b, row)
            elif kind == "faq":
                body = body_faq(b, row)
            elif kind == "classroom":
                body = body_classroom(b, row, labels)
            elif kind == "table":
                body = body_table(b, row, order, labels)
            elif kind == "method":
                body = body_method(b, row)
            elif kind == "unverified":
                body = body_unverified(b, row)
            else:
                raise SystemExit(f"背景の行の種類 {kind} を知りません")
            out.append(f'<details class="kb-row" id="bg-{esc(row["id"])}"><summary><span class="kb-title">{esc(row["title"])}</span>'
                       f'<span class="kb-sum">{esc(row["summary"])}</span></summary><div class="kb-body">{body}</div></details>')
        out.append("</div>")
    out.append(f'<p class="kr-footer">{esc(cfg["dates_line"].format(ledger_checked_on=ja_date(b["ledger"]["checked_on"]), memo_latest=ja_date(memo.latest()), updated_on=ja_date(public["updated_on"])))}</p>')
    out.append("</section>")
    return "\n".join(out) + "\n"
