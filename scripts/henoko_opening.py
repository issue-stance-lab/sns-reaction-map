"""辺野古の転覆事故ページの冒頭（題名・短答・年表・件数）を生成する試作。

入力:
  configs/henoko-student-accident-opening.json      冒頭の文言・短答・年表・FAQ・出典（手で直す場所はここだけ）
  docs/data/themes/henoko-student-accident.json     件数・論点別件数・立場・更新日（公開JSON）
  data/henoko-student-accident_issues-reread.json   論点ごとの理由の区分と件数（再読データ）
  configs/planet/henoko-student-accident.yaml       立場の表示名（山なみと同じ名前を使う）
  THEMES.yaml                                       収集元の名前と次回の更新予定（collect_at）

出力（既定は quality/prototypes/henoko-student-accident-opening/）:
  opening-fragment.html  冒頭の部品（マーカー付き）
  index.html             確認用の単独ページ（opening.css を読む）

見た目の正本は scripts/henoko_redesign/opening.css（試作フォルダーへ写す）。
一次資料を確かめた日は設定の checked_on 1か所。運輸安全委員会の報告書の公表は設定の report（published_on が null の間は
「未公表」）で、短答・未公表欄と背景（scripts/henoko_background.py）が同じ文を読む。読書面（scripts/henoko_reading.py）は
fragment_for() でこの冒頭の下に読書面をつなぐ。

時刻や乱数は使わないので、同じ入力なら何度実行しても同じ出力になる。
件数の合計が合わないときは、表示を作らずに止める。
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "configs" / "henoko-student-accident-opening.json"
DEFAULT_OUT = ROOT / "quality" / "prototypes" / "henoko-student-accident-opening"
ASSETS = ROOT / "scripts" / "henoko_redesign"
REPORT_PHASES = ("unpublished", "published_unchecked", "published_checked")
START = "<!-- HENOKO_OPENING_START -->"
END = "<!-- HENOKO_OPENING_END -->"

# 理由の区分を塗り分ける濃淡（SNSの欄の色。多い順に濃い色から使う）
REASON_TONES = ["#6f5a47", "#8c7660", "#a8937c", "#c2b29e", "#d9cdbd"]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def jp_date(iso: str, with_year: bool = True) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{d.year}年{d.month}月{d.day}日" if with_year else f"{d.month}月{d.day}日"


def link(src: dict | None) -> str:
    if not src or not src.get("url"):
        return ""
    return f'<a class="hop-src" href="{esc(src["url"])}" target="_blank" rel="noopener noreferrer">{esc(src["label"])}</a>'


def links(item: dict) -> str:
    """出典は source（1件）か sources（複数）。"""
    return "".join(link(s) for s in item.get("sources") or [item.get("source")])


def report_phase(config: dict) -> str:
    """運輸安全委員会の報告書の段階。日付のありえない組み合わせは止める（基準日では切り替えない）。"""
    r = config["report"]
    checked = dt.date.fromisoformat(config["checked_on"])
    pub, read = r.get("published_on"), r.get("content_checked_on")
    if set(r["texts"]) != set(REPORT_PHASES):
        raise SystemExit("report.texts に3段階の文がそろっていません")
    if pub is None:
        if read is not None:
            raise SystemExit("報告書の公表日が無いのに、内容を確かめた日 content_checked_on があります")
        return "unpublished"
    if dt.date.fromisoformat(pub) > checked:
        raise SystemExit("報告書の公表日 published_on が、資料を確かめた日 checked_on より後です")
    if read is None:
        return "published_unchecked"
    if not dt.date.fromisoformat(pub) <= dt.date.fromisoformat(read) <= checked:
        raise SystemExit("報告書の内容を確かめた日 content_checked_on は、公表日以後・checked_on 以前にしてください")
    return "published_checked"


def report_text(config: dict, key: str) -> str:
    r = config["report"]
    values = {"checked": jp_date(config["checked_on"]),
              "published": jp_date(r["published_on"]) if r.get("published_on") else "",
              "content_checked": jp_date(r["content_checked_on"]) if r.get("content_checked_on") else ""}
    return r["texts"][report_phase(config)][key].format(**values)


def icon(key: str) -> str:
    """落ち着いた線画のピクトグラム。船・波・浮き輪など事故を連想させる形は使わない。"""
    paths = {
        # 公表資料（書類）
        "fact": '<path d="M7 3h7l4 4v14H7Z"/><path d="M14 3v4h4M10 12h5M10 16h5"/>',
        # まだ公表されていない（砂時計）
        "pending": '<path d="M7 3h10M7 21h10M8 3c0 5 8 6 8 9s-8 4-8 9M16 3c0 5-8 6-8 9s8 4 8 9"/>',
        # SNSの意見（吹き出し2つ）
        "voice": '<path d="M4 5h11v8H9l-3 3v-3H4Z"/><path d="M15 9h5v8h-2v3l-3-3h-4v-2"/>',
    }
    return (
        f'<svg class="hop-picto hop-picto--{key}" aria-hidden="true" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{paths[key]}</svg>'
    )


def read_registry(themes_path: Path, theme_id: str) -> tuple[str, str]:
    themes = yaml.safe_load(themes_path.read_text(encoding="utf-8"))
    entry = themes.get("themes", themes).get(theme_id)
    if not entry:
        raise SystemExit(f"{themes_path} に {theme_id} がありません")
    collect_at = entry.get("collect_at")
    return (str(collect_at) if collect_at else ""), str(entry.get("sample_source", ""))


def load_inputs(config_path: Path) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    paths = {key: ROOT / value for key, value in config["inputs"].items()}
    public = json.loads(paths["public_json"].read_text(encoding="utf-8"))
    reread = json.loads(paths["reread_json"].read_text(encoding="utf-8"))
    planet = yaml.safe_load(paths["planet_config"].read_text(encoding="utf-8"))
    next_collect, source = read_registry(paths["themes_registry"], config["theme_id"])
    if public.get("theme_id") != config["theme_id"]:
        raise SystemExit("公開JSONのテーマIDが設定と一致しません")
    if "checked" in config:
        raise SystemExit("確認日は checked_on 1か所に持つ")
    checked = dt.date.fromisoformat(config["checked_on"])
    # 冒頭の対象は事故調査・制度の背景。投稿との照合日とは分けて確認する。
    ledger = json.loads((ROOT / "data/verification/henoko-student-accident-background.json").read_text(encoding="utf-8"))
    if checked < dt.date.fromisoformat(ledger["checked_on"]):
        raise SystemExit("冒頭の確認日が背景台帳の確認日より古くなっています")
    for e in config["timeline"]["entries"]:
        if dt.date.fromisoformat(e["date"]) > checked:
            raise SystemExit(f"年表の {e['date']} が、資料を確かめた日 checked_on より後です")
        if not (e.get("source") or e.get("sources")):
            raise SystemExit(f"年表の {e['date']} {e['title']} に出典がありません")
    report_phase(config)
    known = {k for b in reread.get("buckets", {}).values() for k in b}
    if set(config["count"].get("reason_label_overrides", {})) - known:
        raise SystemExit("reason_label_overrides に再読データに無い区分があります")
    return {
        "config": config,
        "public": public,
        "reread": reread,
        "planet": planet,
        "next_collect": next_collect,
        "source": source,
    }


def stance_totals(public: dict, planet: dict) -> list[dict]:
    """論点をまたいで立場ごとに合計する。合計が意見件数と違えば止める。"""
    order = [s["id"] for s in planet["stances"]]
    label = {s["id"]: s["label"] for s in planet["stances"]}
    totals = {sid: 0 for sid in order}
    for issue in public["issues"]:
        for s in issue["stances"]:
            if s["id"] not in totals:
                raise SystemExit(f"planet設定に無い立場です: {s['id']}")
            totals[s["id"]] += s["count"]
    if sum(totals.values()) != public["opinion_count"]:
        raise SystemExit("立場の合計が意見件数と一致しません")
    return [{"id": sid, "label": label[sid], "count": totals[sid]} for sid in order]


def issue_reasons(public: dict, reread: dict, overrides: dict | None = None) -> list[dict]:
    """論点ごとに理由の区分を多い順に並べる。区分の合計が論点の件数と違えば止める。"""
    buckets = reread.get("buckets", {})
    rows = []
    for issue in public["issues"]:
        if issue.get("kind") == "other" and issue["count"] == 0:
            continue
        reasons = sorted(
            ({"key": k, "label": (overrides or {}).get(k, v["label"]), "count": v["count"]}
             for k, v in buckets.get(issue["label"], {}).items()),
            key=lambda r: (-r["count"], r["key"]),
        )
        if reasons and sum(r["count"] for r in reasons) != issue["count"]:
            raise SystemExit(f"理由の区分の合計が論点の件数と一致しません: {issue['label']}")
        rows.append({"label": issue["label"], "count": issue["count"], "other": issue.get("kind") == "other", "reasons": reasons})
    if sum(r["count"] for r in rows) != public["opinion_count"]:
        raise SystemExit("論点別件数の合計が意見件数と一致しません")
    return sorted(rows, key=lambda r: (r["other"], -r["count"]))


def render_title(config: dict) -> str:
    t = config["title"]
    phrases = "".join(f'<span class="hop-phrase hop-tone--{esc(p["tone"])}">{esc(p["text"])}</span>' for p in t["phrases"])
    return f'<h1 class="hop-title">{phrases}<span class="hop-sub">{esc(t["sub"])}</span></h1>'


def render_answers(config: dict, public: dict, issues: list[dict], stances: list[dict]) -> str:
    entries = config["timeline"]["entries"]
    named = [i for i in issues if not i["other"]]
    by_id = {s["id"]: s["count"] for s in stances}
    decided = by_id["henoko-student-accident-ministry-support"] + by_id["henoko-student-accident-ministry-oppose"]
    values = {
        "accident_date": jp_date(entries[0]["date"]),
        "checked": jp_date(config["checked_on"]),
        "report_status": report_text(config, "status"),
        "top_issues": "、".join(f"{i['label']}（{i['count']:,}件）" for i in named[:3]),
        "decided": f"{decided:,}",
    }
    cards = []
    for a in config["answers"]:
        cards.append(
            f'<article class="hop-answer hop-zone--{esc(a["zone"])}">'
            f'<p class="hop-kind">{icon(a["zone"])}{esc(a["kind_label"])}</p>'
            f'<h2>{esc(a["question"])}</h2>'
            f'<p class="hop-answer__short">{esc(a["short"] if "short" in a else report_text(config, "short"))}</p>'
            f'<p class="hop-answer__body">{esc(a["body_template"].format(**values))}</p>'
            f'<a class="hop-more" href="{esc(a["link"]["href"])}">{esc(a["link"]["text"])}</a></article>'
        )
    return f'<section class="hop-answers" aria-label="検索で多い疑問に短く答える">{"".join(cards)}</section>'


def event_items(config: dict) -> list[str]:
    """年表の1件ずつ（同じ日の2件目は「同じ日」）。冒頭の年表と背景の年表の行（scripts/henoko_background.py）が使う。"""
    tl = config["timeline"]
    items = []
    prev = None
    for e in tl["entries"]:
        same = e["date"] == prev
        prev = e["date"]
        when = "同じ日" if same else jp_date(e["date"], with_year=False)
        items.append(
            f'<li class="hop-event{" hop-event--same" if same else ""}">'
            f'<time datetime="{esc(e["date"])}">{esc(when)}</time>'
            f'<div class="hop-event__body"><p class="hop-event__head"><span class="hop-actor">{esc(e["actor"])}</span>'
            f'<strong>{esc(e["title"])}</strong></p>'
            f'<p class="hop-event__text">{esc(e["text"])}{links(e)}</p></div></li>'
        )
    return items


def render_timeline(config: dict) -> str:
    """冒頭に年表を置くとき（timeline.placement が "opening"）だけ使う。"background" のときは背景の行が描く。"""
    tl = config["timeline"]
    items = event_items(config)
    head_n = tl["open_count"]
    events_html = f'<ol class="hop-events">{"".join(items[:head_n])}</ol>'
    if len(items) > head_n:
        label = tl["more_label_template"].format(n=len(items) - head_n)
        events_html += (
            f'<details class="hop-more-events"><summary>{esc(label)}</summary>'
            f'<ol class="hop-events hop-events--rest">{"".join(items[head_n:])}</ol></details>'
        )
    pending = render_pending_items(config)
    year = dt.date.fromisoformat(tl["entries"][0]["date"]).year
    pending_note = tl["pending_note_template"].format(checked=jp_date(config["checked_on"]))
    checked_note = config["checked_note"].format(checked=jp_date(config["checked_on"]))
    return (
        f'<section class="hop-timeline hop-zone--fact" id="hop-timeline" aria-labelledby="hop-timeline-title">'
        f'<header class="hop-panel__head"><p class="hop-kind">{icon("fact")}{esc(tl["kind_label"])}</p>'
        f'<h2 id="hop-timeline-title">{esc(tl["title"])}<small>{year}年</small></h2></header>'
        f'{events_html}'
        f'<div class="hop-pending" id="hop-pending"><h3>{icon("pending")}{esc(tl["pending_title"])}</h3>'
        f'<ol class="hop-events">{pending}</ol><p class="hop-pending__note">{esc(pending_note)}</p></div>'
        f'<p class="hop-panel__note">{esc(tl["note"])}</p>'
        f'<p class="hop-checked" data-checked-on="{esc(config["checked_on"])}">{esc(checked_note)}</p>'
        f"</section>"
    )


def render_pending_items(config: dict) -> str:
    """まだ公表されていないもの。報告書（key "report"）の文と札は report の段階から作る。"""
    out = []
    for p in config["timeline"]["pending"]:
        if p.get("key") == "report":
            text, badge = report_text(config, "status"), report_text(config, "badge")
            phase = report_phase(config)
        else:
            text, badge, phase = p["text"], "未公表", "unpublished"
        out.append(
            f'<li class="hop-event hop-event--pending" data-report-phase="{phase}"><span class="hop-when-pending">{esc(badge)}</span>'
            f'<div class="hop-event__body"><p class="hop-event__head"><span class="hop-actor">{esc(p["actor"])}</span>'
            f'<strong>{esc(p["title"])}</strong></p><p class="hop-event__text">{esc(text)}{links(p)}</p></div></li>'
        )
    return "".join(out)


def render_count(config: dict, public: dict, issues: list[dict], stances: list[dict], source: str, next_collect: str) -> str:
    c = config["count"]
    total = public["opinion_count"]
    top = max(i["count"] for i in issues)
    rows = []
    for issue in issues:
        reasons = issue["reasons"]
        if reasons:
            segs = "".join(
                f'<span style="--w:{r["count"] / issue["count"] * 100:.2f}%;--c:{REASON_TONES[min(n, len(REASON_TONES) - 1)]}"></span>'
                for n, r in enumerate(reasons)
            )
            first = reasons[0]
            top_line = f'<p class="hop-issue__top"><span>{esc(c["top_reason_label"])}</span>{esc(first["label"])}（{first["count"]:,}件）</p>'
            listing = "".join(
                f'<li><span class="hop-swatch" style="--c:{REASON_TONES[min(n, len(REASON_TONES) - 1)]}" aria-hidden="true"></span>'
                f'{esc(r["label"])}<b>{r["count"]:,}件</b></li>'
                for n, r in enumerate(reasons)
            )
            detail = f'<details class="hop-reasons"><summary>理由{len(reasons)}区分を開く</summary><ul>{listing}</ul></details>'
        else:
            segs = '<span style="--w:100%;--c:#c9c6c0"></span>'
            top_line = '<p class="hop-issue__top">理由の内訳は未公開です</p>'
            detail = ""
        rows.append(
            f'<li class="hop-issue"><p class="hop-issue__head"><strong>{esc(issue["label"])}</strong>'
            f'<b>{issue["count"]:,}<small>件</small></b></p>'
            f'<div class="hop-issue__track" aria-hidden="true"><div class="hop-issue__bar" style="--w:{issue["count"] / top * 100:.2f}%">{segs}</div></div>'
            f"{top_line}{detail}</li>"
        )
    by_id = {s["id"]: s for s in stances}
    distinguish = by_id["henoko-student-accident-distinguish-issues"]
    stance_text = c["stance_template"].format(
        support=f'{by_id["henoko-student-accident-ministry-support"]["count"]:,}',
        oppose=f'{by_id["henoko-student-accident-ministry-oppose"]["count"]:,}',
        distinguish=f'{distinguish["count"]:,}',
        distinguish_pct=round(distinguish["count"] / total * 100),
        distinguish_label=distinguish["label"],
    )
    period = public["collection_period"]
    caption = c["caption_template"].format(
        source=source,
        collected=f"{public['collected_count']:,}",
        start=jp_date(period["start"]),
        end=jp_date(period["end"], with_year=False),
    )
    updated = c["updated_template"].format(
        updated=jp_date(public["updated_on"]),
        next=jp_date(next_collect, with_year=False) if next_collect else "未定",
    )
    return (
        f'<section class="hop-count hop-zone--voice" id="hop-count" aria-labelledby="hop-count-title">'
        f'<header class="hop-panel__head"><p class="hop-kind">{icon("voice")}{esc(c["label"])}</p>'
        f'<h2 id="hop-count-title" class="hop-count__num"><strong>{total:,}</strong><span>件</span></h2></header>'
        f'<p class="hop-count__caption">{esc(caption)}</p>'
        f'<p class="hop-count__poll">{esc(c["not_poll"])}</p>'
        f'<h3 class="hop-count__issues-title">{esc(c["issues_title"])}</h3>'
        f'<p class="hop-count__hint">{esc(c["issues_hint"])}</p>'
        f'<ol class="hop-issues">{"".join(rows)}</ol>'
        f'<p class="hop-count__note">{esc(c["reason_note"])}</p>'
        f'<p class="hop-count__stance">{esc(stance_text)}</p>'
        f'<p class="hop-count__updated">{esc(updated)}</p>'
        f"</section>"
    )


def render_faq(config: dict) -> str:
    """FAQ。faq.placement が "background" のときは冒頭に出さない（背景の「よくある質問」の行が読む）。"""
    f = config["faq"]
    if f.get("placement") == "background":
        return ""
    items = "".join(
        f'<details class="hop-faq__item"><summary>{esc(i["q"])}</summary><p>{esc(i["a"])}{link(i.get("source"))}</p></details>'
        for i in f["items"]
    )
    return f'<section class="hop-faq" aria-labelledby="hop-faq-title"><h2 id="hop-faq-title">{esc(f["title"])}</h2>{items}</section>'


def timeline_here(config: dict) -> bool:
    """年表と未公表欄を冒頭に置くか（"opening"）、背景の開閉行に置くか（"background"）。"""
    place = config["timeline"].get("placement", "opening")
    if place not in ("opening", "background"):
        raise SystemExit(f"timeline.placement {place} を知りません")
    return place == "opening"


def render_fragment(data: dict) -> str:
    config, public = data["config"], data["public"]
    stances = stance_totals(public, data["planet"])
    issues = issue_reasons(public, data["reread"], config["count"].get("reason_label_overrides"))
    crumb = " ／ ".join(esc(c) for c in config["crumb"])
    return "\n".join(
        [
            START,
            '<section class="hop" aria-label="辺野古の転覆事故の冒頭">',
            f'<header class="hop-hero"><p class="hop-crumb">{crumb}</p>{render_title(config)}<p class="hop-lead">{esc(config["lead"])}</p></header>',
            render_answers(config, public, issues, stances),
            ('<div class="hop-split">' + render_timeline(config) if timeline_here(config) else '<div class="hop-split hop-split--count">'),
            render_count(config, public, issues, stances, data["source"], data["next_collect"]),
            "</div>",
            render_faq(config),
            "</section>",
            END,
            "",
        ]
    )


def render_page(fragment: str) -> str:
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>辺野古の転覆事故 冒頭試作</title>
<meta name="robots" content="noindex">
<link rel="stylesheet" href="opening.css">
</head>
<body>
<main class="hop-page">
{fragment}</main>
</body>
</html>
"""


def fragment_for(config_path: Path = DEFAULT_CONFIG) -> str:
    """冒頭の部品（マーカー付き）。読書面の試作（scripts/henoko_reading.py）がこの下に読書面をつなぐ。"""
    return render_fragment(load_inputs(config_path))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    data = load_inputs(args.config)
    fragment = render_fragment(data)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "opening-fragment.html").write_text(fragment, encoding="utf-8")
    (args.out_dir / "index.html").write_text(render_page(fragment), encoding="utf-8")
    shutil.copyfile(ASSETS / "opening.css", args.out_dir / "opening.css")
    print(f"wrote {args.out_dir / 'opening-fragment.html'}")
    print(f"wrote {args.out_dir / 'index.html'}")


if __name__ == "__main__":
    main()
