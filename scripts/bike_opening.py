"""自転車の青切符ページの冒頭（題名・青切符の図・短答・件数）を生成する試作。

入力:
  configs/bike-blue-ticket-opening.json   冒頭の文言・短答・反則金の例・FAQ・出典（手で直す場所はここだけ）
  docs/data/themes/bike-blue-ticket.json  件数・論点別件数・立場・収集期間・更新日（公開JSON）
  configs/planet/bike-blue-ticket.yaml    立場の色（山なみと同じ色を使う）
  data/bike-blue-ticket_issues-reread.json 論点ごとの理由区分（「その他」の中身と、理由未公開の判定）
  THEMES.yaml                              収集元の名前と次回の収集予定（collect_at）

出力（既定は quality/prototypes/bike-blue-ticket-opening/）:
  opening-fragment.html  冒頭の部品（マーカー付き）
  index.html             確認用の単独ページ（同じフォルダーの opening.css と opening.js を読む）

時刻や乱数は使わないので、同じ入力なら何度実行しても同じ出力になる。
件数の合計が公開JSONの意見件数と合わないときは、生成を止める。
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "configs" / "bike-blue-ticket-opening.json"
DEFAULT_OUT = ROOT / "quality" / "prototypes" / "bike-blue-ticket-opening"
START = "<!-- BIKE_BLUE_TICKET_OPENING_START -->"
END = "<!-- BIKE_BLUE_TICKET_OPENING_END -->"

# ピクトグラム（24×24、線画）。色は currentColor。
PICTO = {
    "age": '<circle cx="6" cy="16" r="3.5"/><circle cx="18" cy="16" r="3.5"/><path d="M6 16l4-7h5l3 7M10 9l2 7h-6M13 6h3"/>',
    "fines": '<circle cx="12" cy="12" r="8.5"/><path d="M8.5 7.5 12 12l3.5-4.5M12 12v5M9 12.5h6M9 15h6"/>',
    "after": '<path d="M3 7h18v3a2 2 0 0 0 0 4v3H3v-3a2 2 0 0 0 0-4Z"/><path d="M15 7v10" stroke-dasharray="2 2"/>',
    "warning": '<path d="M4 5h16v10H9l-5 4Z"/><path d="M12 8v3M12 13h.01"/>',
    "faq": '<circle cx="12" cy="12" r="8.5"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .8-1 1.5v.5M12 16.5h.01"/>',
    "bike": '<circle cx="5.5" cy="16" r="4"/><circle cx="18.5" cy="16" r="4"/><path d="M5.5 16 9 9h7l2.5 7M9 9l3 7M14 6h3l-1 3"/>',
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def yen(amount: int) -> str:
    return f"{amount:,}"


def jp_date(iso: str, with_year: bool = True) -> str:
    d = dt.date.fromisoformat(str(iso))
    return f"{d.year}年{d.month}月{d.day}日" if with_year else f"{d.month}月{d.day}日"


def picto(name: str) -> str:
    return (
        '<svg class="bop-picto" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{PICTO[name]}</svg>'
    )


def ext_link(url: str, text: str, cls: str = "") -> str:
    klass = f' class="{cls}"' if cls else ""
    return f'<a{klass} href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(text)}</a>'


# ---------------------------------------------------------------- 入力


def load_inputs(config_path: Path) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    paths = {key: ROOT / value for key, value in config["inputs"].items()}
    public = json.loads(paths["public_json"].read_text(encoding="utf-8"))
    planet = yaml.safe_load(paths["planet_config"].read_text(encoding="utf-8"))
    reread = json.loads(paths["reread"].read_text(encoding="utf-8"))
    themes = yaml.safe_load(paths["themes_registry"].read_text(encoding="utf-8"))
    entry = themes.get("themes", themes).get(config["theme_id"])
    if not entry:
        raise SystemExit(f"THEMES.yaml に {config['theme_id']} がありません")
    if public.get("theme_id") != config["theme_id"]:
        raise SystemExit("公開JSONのテーマIDが設定と一致しません")
    for key in ("age", "fines", "after", "warning", "faq"):
        for src in _source_ids(config[key]):
            if src not in config["sources"]:
                raise SystemExit(f"出典 {src} が sources にありません（{key}）")
    return {
        "config": config,
        "public": public,
        "planet": planet,
        "reread": reread,
        "next_collect": str(entry.get("collect_at") or ""),
        "sample_source": str(entry.get("sample_source") or ""),
    }


def _source_ids(node: object) -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("source", "license_source") and isinstance(v, str):
                found.append(v)
            elif k == "sources" and isinstance(v, list):
                found.extend(v)
            else:
                found.extend(_source_ids(v))
    elif isinstance(node, list):
        for v in node:
            found.extend(_source_ids(v))
    return found


def stance_totals(public: dict, planet: dict) -> list[dict]:
    totals: dict[str, int] = {}
    labels: dict[str, str] = {}
    for issue in public["issues"]:
        for st in issue["stances"]:
            totals[st["id"]] = totals.get(st["id"], 0) + int(st["count"])
            labels[st["id"]] = st["label"]
    if sum(totals.values()) != public["opinion_count"]:
        raise SystemExit("立場の合計が意見件数と一致しません")
    colors = {s["id"]: s["color"] for s in planet["stances"]}
    rows = [
        {"id": sid, "label": labels[sid], "count": n, "color": colors.get(sid, "#8B9199")}
        for sid, n in totals.items()
    ]
    rows.sort(key=lambda r: (-r["count"], r["id"]))
    return rows


def issue_rows(public: dict, reread: dict) -> tuple[list[dict], dict]:
    issues = public["issues"]
    if sum(int(i["count"]) for i in issues) != public["opinion_count"]:
        raise SystemExit("論点別件数の合計が意見件数と一致しません")
    named = [i for i in issues if i.get("kind") != "other"]
    others = [i for i in issues if i.get("kind") == "other"]
    if len(others) != 1:
        raise SystemExit("「その他」の論点がちょうど1つではありません")
    named.sort(key=lambda i: (-int(i["count"]), i["id"]))
    other = others[0]
    buckets = reread.get(other["label"], {}).get("buckets", {})
    bucket_list = sorted(
        ({"key": k, "label": v["label"], "count": int(v["count"])} for k, v in buckets.items()),
        key=lambda b: (-b["count"], b["key"]),
    )
    if bucket_list and sum(b["count"] for b in bucket_list) != int(other["count"]):
        raise SystemExit("「その他」の理由区分の合計が論点の件数と一致しません")
    rows = []
    for i in named + [other]:
        has_reason = bool(reread.get(i["label"], {}).get("buckets"))
        rows.append({"id": i["id"], "label": i["label"], "count": int(i["count"]),
                     "other": i is other, "has_reason": has_reason})
    return rows, {"count": int(other["count"]), "buckets": bucket_list}


# ---------------------------------------------------------------- 描画


def render_title(c: dict) -> str:
    t = c["title"]
    sub = "".join(f'<span class="bop-phrase">{esc(s)}</span>' for s in t["sub"])
    return (
        '<h1 class="bop-title">'
        f'<span class="bop-phrase">{esc(t["lead"])}</span>'
        f'<span class="bop-phrase"><span class="bop-accent">{esc(t["accent"])}</span>{esc(t["tail"])}</span>'
        f'<span class="bop-sub">{sub}</span></h1>'
    )


def render_ticket(c: dict, fines_range: str) -> str:
    tk = c["ticket"]
    rows = []
    for f in tk["fields"]:
        value = fines_range if f.get("value_from") == "fines_range" else f["value"]
        note = f'<small>{esc(f["note"])}</small>' if f.get("note") else ""
        rows.append(f'<div class="bop-ticket__row"><dt>{esc(f["key"])}</dt><dd>{esc(value)}{note}</dd></div>')
    return (
        '<figure class="bop-ticket" aria-labelledby="bop-ticket-label">'
        '<div class="bop-ticket__card">'
        '<div class="bop-ticket__main">'
        f'<p class="bop-ticket__label" id="bop-ticket-label">{picto("bike")}{esc(tk["label"])}</p>'
        f'<dl class="bop-ticket__fields">{"".join(rows)}</dl>'
        '</div>'
        f'<p class="bop-ticket__stub"><span>{esc(tk["stub"])}</span></p>'
        '</div>'
        f'<figcaption>{esc(tk["caption"])}</figcaption>'
        '</figure>'
    )


def src_link(c: dict, sid: str, text: str | None = None) -> str:
    s = c["sources"][sid]
    return ext_link(s["url"], (text or s["label"]) + " ↗", "bop-src")


def render_age(c: dict) -> str:
    a = c["age"]
    default = next(o for o in a["options"] if o["id"] == a["default"])
    buttons = "".join(
        f'<button type="button" data-bop-age="{esc(o["id"])}" data-title="{esc(o["title"])}" '
        f'data-body="{esc(o["body"])}" aria-pressed="{"true" if o is default else "false"}">{esc(o["label"])}</button>'
        for o in a["options"]
    )
    srcs = "".join(src_link(c, s) for s in a["sources"])
    return (
        '<article class="bop-answer bop-answer--age" id="bop-age" aria-labelledby="bop-age-q">'
        f'<span class="bop-answer__kind">{esc(a["kind"])}</span>'
        f'<h3 id="bop-age-q">{picto("age")}{esc(a["question"])}</h3>'
        f'<p class="bop-answer__short">{esc(a["short"])}</p>'
        f'<p class="bop-hint">{esc(a["hint"])}</p>'
        f'<div class="bop-age__options" role="group" aria-label="年齢を選ぶ">{buttons}</div>'
        '<div class="bop-age__answer" aria-live="polite" aria-atomic="true">'
        f'<strong data-bop-age-title>{esc(default["title"])}</strong>'
        f'<p data-bop-age-body>{esc(default["body"])}</p></div>'
        f'<p class="bop-sources">{srcs}</p>'
        '</article>'
    )


def render_fines(c: dict) -> tuple[str, str]:
    f = c["fines"]
    items = f["items"]
    amounts = sorted({int(i["amount"]) for i in items}, reverse=True)
    lo, hi = min(amounts), max(amounts)
    short = f["short_template"].format(min=yen(lo), max=yen(hi))
    chips = '<button type="button" data-bop-fee="all" aria-pressed="true">すべて</button>' + "".join(
        f'<button type="button" data-bop-fee="{a}" aria-pressed="false">{yen(a)}円</button>' for a in sorted(amounts)
    )
    rows = []
    for it in items:
        s = c["sources"][it["source"]]
        rows.append(
            f'<li class="bop-fine" data-bop-amount="{int(it["amount"])}" '
            f'data-bop-search="{esc(it["keywords"] + " " + str(it["amount"]))}">'
            f'<span class="bop-fine__name">{esc(it["name"])}</span>'
            f'<strong class="bop-fine__amount">{yen(int(it["amount"]))}<small>円</small></strong>'
            f'{ext_link(s["url"], s["label"].split("｜")[0] + "の資料", "bop-fine__src")}</li>'
        )
    html_ = (
        '<article class="bop-answer bop-answer--fines" id="bop-fines" aria-labelledby="bop-fines-q">'
        f'<span class="bop-answer__kind">{esc(f["kind"])}</span>'
        f'<h3 id="bop-fines-q">{picto("fines")}{esc(f["question"])}</h3>'
        f'<p class="bop-answer__short">{esc(short)}</p>'
        f'<label class="bop-fines__label" for="bop-fine-search">{esc(f["search_label"])}</label>'
        f'<input id="bop-fine-search" type="search" placeholder="{esc(f["placeholder"])}" autocomplete="off">'
        f'<div class="bop-fines__chips" role="group" aria-label="反則金で絞り込む">{chips}</div>'
        f'<p class="bop-fines__count" data-bop-fine-count aria-live="polite">主な例 {len(items)}件</p>'
        f'<ul class="bop-fines__list">{"".join(rows)}</ul>'
        f'<p class="bop-fines__empty" data-bop-fine-empty hidden>{esc(f["empty"])}</p>'
        f'<p class="bop-caveat">{esc(f["caveat"])}</p>'
        '</article>'
    )
    return html_, f"{yen(lo)}〜{yen(hi)}円"


def render_after(c: dict) -> str:
    a = c["after"]
    steps = []
    for n, s in enumerate(a["steps"], 1):
        link = src_link(c, s["source"]) if s.get("source") else ""
        steps.append(
            f'<li class="bop-step"><span class="bop-step__num" aria-hidden="true">{n}</span>'
            f'<div><strong>{esc(s["title"])}</strong><p>{esc(s["body"])}</p>{link}</div></li>'
        )
    return (
        '<article class="bop-answer bop-answer--after" id="bop-after" aria-labelledby="bop-after-q">'
        f'<span class="bop-answer__kind bop-answer__kind--new">{esc(a["kind"])}</span>'
        f'<h3 id="bop-after-q">{picto("after")}{esc(a["question"])}</h3>'
        f'<p class="bop-answer__short">{esc(a["short"])}</p>'
        f'<ol class="bop-steps">{"".join(steps)}</ol>'
        f'<p class="bop-license">{esc(a["license"])} {src_link(c, a["license_source"])}</p>'
        '</article>'
    )


def render_warning(c: dict) -> str:
    w = c["warning"]
    tickets, warnings = int(w["tickets"]), int(w["warnings"])
    ratio = round(warnings / tickets)
    body = w["body_template"].format(period=w["period"], tickets=yen(tickets), warnings=yen(warnings))
    label = w["picto_label"].format(ratio=ratio)
    cells = '<span class="bop-cell bop-cell--ticket"></span>' + '<span class="bop-cell"></span>' * ratio
    srcs = "".join(src_link(c, s) for s in w["sources"])
    return (
        '<article class="bop-answer bop-answer--warning" id="bop-warning" aria-labelledby="bop-warning-q">'
        f'<span class="bop-answer__kind">{esc(w["kind"])}</span>'
        f'<h3 id="bop-warning-q">{picto("warning")}{esc(w["question"])}</h3>'
        f'<p class="bop-answer__short">{esc(w["short"])}</p>'
        f'<p>{esc(body)}</p>'
        f'<figure class="bop-cells-fig"><div class="bop-cells" role="img" aria-label="{esc(label)}">{cells}</div>'
        f'<figcaption><span class="bop-key bop-key--ticket" aria-hidden="true"></span>青切符'
        f'<span class="bop-key" aria-hidden="true"></span>指導警告票<b>{esc(label)}</b></figcaption></figure>'
        f'<p class="bop-note">{esc(w["note"])}</p>'
        f'<p class="bop-sources">{srcs}</p>'
        '</article>'
    )


def render_faq(c: dict) -> str:
    f = c["faq"]
    items = "".join(
        f'<details class="bop-faq__item" id="bop-faq-{esc(i["id"])}"><summary>{esc(i["q"])}</summary>'
        f'<p>{esc(i["a"])} {src_link(c, i["source"], i["link_text"])}</p></details>'
        for i in f["items"]
    )
    return (
        '<section class="bop-faq" id="bop-faq" aria-labelledby="bop-faq-title">'
        f'<div class="bop-faq__head"><span class="bop-answer__kind">{esc(f["kind"])}</span>'
        f'<h3 id="bop-faq-title">{picto("faq")}{esc(f["heading"])}</h3></div>'
        f'<div class="bop-faq__grid">{items}</div></section>'
    )


def render_count(ctx: dict) -> str:
    c, public = ctx["config"], ctx["public"]
    k = c["count"]
    total = int(public["opinion_count"])
    stances = stance_totals(public, ctx["planet"])
    rows, other = issue_rows(public, ctx["reread"])
    period = public["collection_period"]
    caption = k["caption_template"].format(
        source=ctx["sample_source"], collected=yen(int(public["collected_count"])),
        start=jp_date(period["start"]), end=jp_date(period["end"]),
    )
    segs = "".join(
        f'<span class="bop-stance__seg" style="--w:{s["count"] / total * 100:.2f}%;--c:{s["color"]}"></span>'
        for s in stances
    )
    slist = "".join(
        f'<li><span class="bop-key" style="--c:{s["color"]}" aria-hidden="true"></span>{esc(s["label"])}'
        f'<b>{round(s["count"] / total * 100)}%</b><small>{yen(s["count"])}件</small></li>'
        for s in stances
    )
    peak = max(r["count"] for r in rows)
    issue_items = []
    for r in rows:
        tag = "" if r["has_reason"] else f'<em class="bop-tag">{esc(k["no_reason_tag"])}</em>'
        name = esc(r["label"])
        if r["other"]:
            name = f'{esc(k["other_label"])}<small>{esc(k["other_sub"])}</small>'
        cls = "bop-issue bop-issue--other" if r["other"] else "bop-issue"
        issue_items.append(
            f'<li class="{cls}"><span class="bop-issue__name">{name}{tag}</span>'
            f'<span class="bop-issue__track" aria-hidden="true"><span class="bop-issue__bar" style="--w:{r["count"] / peak * 100:.2f}%"></span></span>'
            f'<b>{yen(r["count"])}<small>件</small></b></li>'
        )
    other_html = ""
    if other["buckets"]:
        top_n = int(k["other_top_n"])
        top = other["buckets"][:top_n]
        rest = other["buckets"][top_n:]
        share = round(top[0]["count"] / other["count"] * 100)
        lead = k["other_lead_template"].format(share=share, top=top[0]["label"])
        lis = "".join(f'<li>{esc(b["label"])}<b>{yen(b["count"])}件</b></li>' for b in top)
        if rest:
            lis += f'<li class="bop-other__rest">ほか{len(rest)}区分<b>{yen(sum(b["count"] for b in rest))}件</b></li>'
        other_html = (
            f'<div class="bop-other"><p class="bop-other__lead">{esc(lead)}</p>'
            f'<p class="bop-other__label">「その他」の中身（理由の区分）</p><ul>{lis}</ul></div>'
        )
    updated = k["updated_template"].format(
        updated=jp_date(public["updated_on"]),
        next=jp_date(ctx["next_collect"], with_year=False) if ctx["next_collect"] else "未定",
    )
    return (
        '<section class="bop-count" id="bop-count" aria-labelledby="bop-count-title">'
        '<div class="bop-count__total">'
        f'<h2 id="bop-count-title">{esc(k["heading"])}</h2>'
        f'<p class="bop-count__num"><strong>{yen(total)}</strong><span>件</span></p>'
        f'<p class="bop-count__caption">{esc(caption)}</p>'
        f'<div class="bop-stance" aria-hidden="true">{segs}</div>'
        f'<ul class="bop-stance__list">{slist}</ul>'
        f'<p class="bop-count__poll">{esc(k["poll_note"])}</p>'
        '</div>'
        '<div class="bop-count__issues">'
        f'<h3>{esc(k["issues_heading"])}</h3>'
        f'<ol class="bop-issues">{"".join(issue_items)}</ol>'
        f'{other_html}'
        f'<p class="bop-count__updated">{esc(updated)}</p>'
        '</div></section>'
    )


def render_sources(c: dict) -> str:
    dated = sorted({s["checked_on"] for s in c["sources"].values() if s.get("checked_on")})
    note = c["checked_note_template"].format(first=jp_date(dated[0]), last=jp_date(dated[-1], with_year=False))
    links = "".join(f"<li>{ext_link(s['url'], s['label'])}</li>" for s in c["sources"].values())
    return f'<footer class="bop-foot"><p>{esc(note)}</p><ul class="bop-foot__links">{links}</ul></footer>'


def render_fragment(ctx: dict) -> str:
    c = ctx["config"]
    fines_html, fines_range = render_fines(c)
    hero = (
        '<div class="bop-hero"><div class="bop-hero__copy">'
        f'<p class="bop-crumb">{esc(c["crumb"])}</p>{render_title(c)}'
        f'<p class="bop-lead">{esc(c["lead"])}</p>'
        '<nav class="bop-jump" aria-label="冒頭の目次">'
        '<a href="#bop-answers">制度の疑問</a><a href="#bop-count">SNSの意見の件数</a></nav>'
        f'</div>{render_ticket(c, fines_range)}</div>'
    )
    answers = (
        '<section class="bop-answers" id="bop-answers" aria-labelledby="bop-answers-title">'
        f'<h2 class="bop-section-title" id="bop-answers-title">{esc(c["answers_heading"])}</h2>'
        f'<div class="bop-answers__grid">{render_age(c)}{fines_html}{render_after(c)}{render_warning(c)}</div>'
        f'{render_faq(c)}</section>'
    )
    body = (
        '<section class="bop" aria-label="自転車の青切符の冒頭">'
        f'{hero}{answers}{render_count(ctx)}{render_sources(c)}</section>'
    )
    return f"{START}\n{body}\n{END}\n"


PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>自転車の青切符 冒頭試作</title>
<meta name="robots" content="noindex">
<link rel="stylesheet" href="opening.css">
</head>
<body>
<main class="bop-page">
{fragment}</main>
<script src="opening.js"></script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    ctx = load_inputs(args.config)
    fragment = render_fragment(ctx)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "opening-fragment.html").write_text(fragment, encoding="utf-8")
    (args.out / "index.html").write_text(PAGE.format(fragment=fragment), encoding="utf-8")
    print(f"wrote {args.out / 'opening-fragment.html'}")
    print(f"wrote {args.out / 'index.html'}")


if __name__ == "__main__":
    main()
