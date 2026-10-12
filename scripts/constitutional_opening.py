#!/usr/bin/env python3
"""憲法改正論議ページの冒頭（試作）を、設定JSONと公開JSONから生成する。

入力:
  configs/constitutional-amendment-opening.json   冒頭の文言・短答・出典（正典）
  docs/data/themes/constitutional-amendment.json  件数・論点別件数・立場（公開JSON）
  configs/planet/constitutional-amendment.yaml    立場の色と模様（山並みと同じ値）
  data/verification/constitutional-amendment-background.json  背景台帳（確認日の照合用）

出力（--out-dir、既定は quality/prototypes/constitutional-amendment-opening）:
  opening-fragment.html  冒頭の部品（将来ページへ差し込む単位）
  index.html             確認用の単独ページ（同じフォルダーの opening.css を読む）
  opening.css            scripts/constitutional_redesign/opening.css（正本）の写し

確認日: 設定の checked_on（1か所）。「いまの段階」の確認日と、FAQ の「◯月◯日時点」はここから作る
（2026-10-12 に一次資料を確かめ直したときに、背景台帳の確認日 2026-09-13 から切り替えた）。

時制（2026-10-12、副首都 fukushuto_opening.phase_of と同じ型）: 国民投票法の改正（令和8年法律第73号）の施行を、
基準日（--as-of、既定は公開JSONの updated_on）で3段階に切り替える。施行日を過ぎても生成は止めない。
- before（基準日が施行日より前）／ after_unconfirmed（施行日を過ぎ、law.enforcement_confirmed_on が null）／
  after_confirmed（施行後の条文を確かめた日を law.enforcement_confirmed_on に入れたとき）
段階ごとの文は procedure.footnote_phase に書く。欠けていたら止める。

同じ入力なら出力は毎回同じ（日時や乱数を使わない）。--check は書かずに差分の有無だけ返す。
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "constitutional-amendment-opening.json"
DEFAULT_OUT = ROOT / "quality" / "prototypes" / "constitutional-amendment-opening"
ASSETS = ROOT / "scripts" / "constitutional_redesign"
LAW_PHASES = ("before", "after_unconfirmed", "after_confirmed")

PATTERN_CLASS = {"plain": "pat-plain", "diagonal": "pat-diagonal", "dots": "pat-dots", "mesh": "pat-mesh"}

# 手続きのピクトグラム（線画。色は CSS の currentColor）
ICONS = {
    "draft": (
        '<path d="M14 6h14l8 8v28H14z" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/>'
        '<path d="M28 6v8h8" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/>'
        '<path d="M19 22h12M19 28h12M19 34h8" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>'
    ),
    "diet": (
        '<path d="M25 7v4" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>'
        '<path d="M18 19c0-5 3-8 7-8s7 3 7 8z" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/>'
        '<path d="M8 23h34M10 41h30M8 44h34" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>'
        '<path d="M14 27v11M21 27v11M29 27v11M36 27v11" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>'
    ),
    "ballot": (
        '<path d="M8 24h34v18H8z" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/>'
        '<path d="M18 24h14" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>'
        '<path d="M17 6h16v20H17z" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/>'
        '<path d="M21 14l3 3 6-6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
    ),
    "approve": (
        '<circle cx="25" cy="25" r="17" fill="none" stroke="currentColor" stroke-width="2.4"/>'
        '<path d="M17 25.5l5.5 5.5L34 19.5" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
    ),
}


class OpeningError(Exception):
    pass


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def jp_date(iso: str, with_year: bool = True) -> str:
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    if not m:
        raise OpeningError(f"日付の形式が不正です: {iso!r}")
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return f"{y}年{mo}月{d}日" if with_year else f"{mo}月{d}日"


def fmt_int(n: int) -> str:
    return f"{n:,}"


def fmt_pct(count: int, total: int) -> str:
    return f"{count / total * 100:.1f}%"


def fill(template: str, values: dict) -> str:
    def repl(m: re.Match) -> str:
        key = m.group(1)
        if key not in values:
            raise OpeningError(f"差し込み値 {{{key}}} がありません: {template!r}")
        return str(values[key])

    return re.sub(r"\{([a-z_]+)\}", repl, template)


def load_inputs(config_path: Path) -> tuple[dict, dict, list, dict]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    inputs = config["inputs"]
    public = json.loads((ROOT / inputs["public_json"]).read_text(encoding="utf-8"))
    planet = yaml.safe_load((ROOT / inputs["stance_config"]).read_text(encoding="utf-8"))
    background = json.loads((ROOT / inputs["background_json"]).read_text(encoding="utf-8"))
    if public.get("theme_id") != config["theme_id"] or planet.get("theme_id") != config["theme_id"]:
        raise OpeningError("theme_id が設定と入力で一致しません")
    return config, public, planet, background


def iso(value: str, where: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or ""):
        raise OpeningError(f"{where} の日付の形式が不正です: {value!r}")
    return value


def phase_of(config: dict, as_of: str) -> str:
    """国民投票法の改正の施行の段階。施行の確認日のありえない組み合わせは止める。"""
    law = config["law"]
    iso(as_of, "基準日")
    for key in ("promulgated_on", "enforcement_on"):
        iso(law[key], f"law.{key}")
    confirmed = law.get("enforcement_confirmed_on")
    if confirmed:
        iso(confirmed, "law.enforcement_confirmed_on")
        if confirmed < law["enforcement_on"]:
            raise OpeningError("law.enforcement_confirmed_on が施行日より前です（施行後の条文を確かめた日を入れてください）")
        if as_of < law["enforcement_on"]:
            raise OpeningError("law.enforcement_confirmed_on が入っていますが、基準日が施行日より前です")
    if as_of < law["enforcement_on"]:
        return "before"
    return "after_confirmed" if confirmed else "after_unconfirmed"


def law_values(config: dict) -> dict:
    law = config["law"]
    return {
        "promulgated": jp_date(law["promulgated_on"]),
        "enforcement": jp_date(law["enforcement_on"]),
        "confirmed": jp_date(law["enforcement_confirmed_on"]) if law.get("enforcement_confirmed_on") else "",
    }


def default_as_of(public: dict) -> str:
    return public["updated_on"]


def summarize(public: dict, planet: dict) -> dict:
    """公開JSONから件数・論点・立場を集計し、整合を検査する。"""
    opinion = int(public["opinion_count"])
    collected = int(public["collected_count"])
    issues = public["issues"]
    if sum(int(i["count"]) for i in issues) != int(public["issue_assigned_count"]):
        raise OpeningError("論点別件数の合計が issue_assigned_count と一致しません")
    style = {s["id"]: s for s in planet["stances"]}
    totals: dict[str, dict] = {}
    for issue in issues:
        for s in issue["stances"]:
            t = totals.setdefault(s["id"], {"id": s["id"], "label": s["label"], "count": 0})
            t["count"] += int(s["count"])
    if sum(t["count"] for t in totals.values()) != opinion:
        raise OpeningError("立場別件数の合計が opinion_count と一致しません")
    stances = []
    for t in sorted(totals.values(), key=lambda x: (-x["count"], x["id"])):
        st = style.get(t["id"])
        if not st:
            raise OpeningError(f"立場 {t['id']} の色が {planet.get('theme_id')} の設定にありません")
        stances.append({**t, "color": st["color"], "pattern": st.get("pattern", "plain")})
    period = public["collection_period"]
    return {
        "opinion": opinion,
        "collected": collected,
        "issues": {i["id"]: i for i in issues},
        "stances": stances,
        "period_start": period["start"],
        "period_end": period["end"],
        "updated_on": public["updated_on"],
    }


def source_links(refs: list, sources: dict, cls: str = "ca-src") -> str:
    parts = []
    for ref in refs:
        if ref not in sources:
            raise OpeningError(f"出典 {ref} が sources にありません")
        s = sources[ref]
        parts.append(f'<a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["name"])}</a>')
    return f'<p class="{cls}"><span>出典</span>{"".join(parts)}</p>'


def icon(name: str) -> str:
    if name not in ICONS:
        raise OpeningError(f"ピクトグラム {name} がありません")
    return f'<svg class="ca-step__icon" viewBox="0 0 50 50" aria-hidden="true" focusable="false">{ICONS[name]}</svg>'


def render_fragment(config: dict, data: dict, background: dict, source_label: str, as_of: str | None = None) -> str:
    sources = config["sources"]
    as_of = as_of or data["updated_on"]
    law_phase = phase_of(config, as_of)
    checked_on = iso(config["checked_on"], "checked_on")
    if checked_on < background["checked_on"]:
        raise OpeningError("冒頭の checked_on が背景台帳の確認日より古くなっています")
    period_same_year = data["period_start"][:4] == data["period_end"][:4]
    values = {
        "opinion_count": fmt_int(data["opinion"]),
        "collected_count": fmt_int(data["collected"]),
        "status_checked_on": jp_date(checked_on),
        "period_start": jp_date(data["period_start"]),
        "period_end": jp_date(data["period_end"], with_year=not period_same_year),
        "updated_on": jp_date(data["updated_on"]),
        "source_label": source_label,
    }
    out: list[str] = []
    w = out.append

    w(f'<section class="ca-open" id="ca-open" aria-labelledby="ca-open-title" data-as-of="{esc(as_of)}" '
      f'data-checked-on="{esc(checked_on)}" data-law-phase="{law_phase}">')
    w('<div class="ca-open__hero">')
    # 左: 題名と短答
    w('<div class="ca-open__lead">')
    w(f'<p class="ca-open__crumb">{esc(config["breadcrumb"])}</p>')
    w(f'<p class="ca-open__eyebrow">{esc(config["eyebrow"])}</p>')
    lines = []
    for idx, line in enumerate(config["title_lines"]):
        cls = ' class="is-accent"' if idx == config.get("title_accent_line") else ""
        lines.append(f"<span{cls}>{esc(line)}</span>")
    w(f'<h1 id="ca-open-title">{"".join(lines)}</h1>')
    w('<div class="ca-open__answer">')
    w('<p class="ca-open__answer-k">短い答え</p>')
    for p in config["short_answer"]:
        w(f"<p>{esc(fill(p, values))}</p>")
    w(source_links(config.get("short_answer_sources", []), sources))
    w("</div>")
    st = config["status"]
    if st.get("checked_on_from") != "checked_on":
        raise OpeningError("status.checked_on_from は checked_on（設定の確認日）のみ対応")
    w(
        f'<p class="ca-open__status"><b>{esc(st["label"])}</b><span>{esc(fill(st["text"], values))}</span>'
        f'<time datetime="{esc(checked_on)}">{esc(fill(st["checked_label"], values))}</time></p>'
    )
    w('<nav class="ca-open__entrances" aria-label="知りたいことから読む">')
    for e in config["entrances"]:
        w(
            f'<a href="{esc(e["href"])}"><span class="num">{esc(e["num"])}</span>'
            f'<b>{esc(e["label"])}</b><small>{esc(e["sub"])}</small></a>'
        )
    w("</nav>")
    w("</div>")

    # 右: 手続きの流れ図
    pr = config["procedure"]
    step_ids = [s["id"] for s in pr["steps"]]
    if pr["current_step"] not in step_ids:
        raise OpeningError("procedure.current_step が steps にありません")
    w(f'<figure class="ca-flow" id="{esc(pr["id"])}" aria-labelledby="{esc(pr["id"])}-title">')
    w(
        f'<figcaption><span class="ca-kicker">{esc(pr["kicker"])}</span>'
        f'<b id="{esc(pr["id"])}-title">{esc(pr["title"])}</b></figcaption>'
    )
    w('<ol class="ca-flow__steps">')
    for n, s in enumerate(pr["steps"], start=1):
        current = s["id"] == pr["current_step"]
        cls = "ca-step is-current" if current else "ca-step"
        aria = ' aria-current="step"' if current else ""
        marker = f'<span class="ca-step__now">{esc(pr["current_label"])}</span>' if current else ""
        w(f'<li class="{cls}"{aria}>')
        w(f'<span class="ca-step__mark">{icon(s["icon"])}<span class="ca-step__n">{n}</span></span>')
        w(
            f'<div class="ca-step__body"><p class="ca-step__label">{esc(s["label"])}{marker}</p>'
            f'<p class="ca-step__rule">{esc(s["rule"])}</p><p class="ca-step__note">{esc(s["note"])}</p></div>'
        )
        w("</li>")
    w("</ol>")
    fp = pr["footnote_phase"]
    if set(fp) != set(LAW_PHASES):
        raise OpeningError("procedure.footnote_phase に施行の3段階の文がそろっていません")
    w(f'<p class="ca-flow__foot" data-phase="{law_phase}">{esc(fill(fp[law_phase], law_values(config)))}</p>')
    refs: list[str] = []
    for s in pr["steps"]:
        for r in s["sources"]:
            if r not in refs:
                refs.append(r)
    for r in pr.get("footnote_sources", []):
        if r not in refs:
            refs.append(r)
    w(source_links(refs, sources))
    w("</figure>")
    w("</div>")

    # 下段: 争点2枚と件数
    w('<div class="ca-open__band">')
    iss = config["issues"]
    w(f'<section class="ca-issues" id="{esc(iss["id"])}" aria-labelledby="{esc(iss["id"])}-title">')
    w(
        f'<header><span class="ca-kicker">{esc(iss["kicker"])}</span>'
        f'<h2 id="{esc(iss["id"])}-title">{esc(iss["title"])}</h2></header>'
    )
    w('<div class="ca-issues__grid">')
    for c in iss["cards"]:
        issue = data["issues"].get(c["issue_id"])
        if issue is None:
            raise OpeningError(f"論点 {c['issue_id']} が公開JSONにありません")
        cnt = int(issue["count"])
        share = fill(iss["share_label"], {"share": fmt_pct(cnt, data["opinion"])})
        w(f'<article class="ca-issue" data-issue-id="{esc(c["issue_id"])}">')
        w(f'<p class="ca-issue__code">{esc(c["code"])}</p>')
        w(f'<h3>{esc(c["heading"])}</h3>')
        w(
            '<dl class="ca-issue__dl">'
            f'<div><dt>いま</dt><dd>{esc(c["now"])}</dd></div>'
            f'<div><dt>提案</dt><dd>{esc(c["proposal"])}</dd></div>'
            "</dl>"
        )
        w(
            f'<p class="ca-issue__count"><span>{esc(iss["count_label"])}「{esc(issue["label"])}」</span>'
            f'<strong>{fmt_int(cnt)}<small>件</small></strong><em>{esc(share)}</em></p>'
        )
        w(source_links(c["sources"], sources))
        w("</article>")
    w("</div>")
    w("</section>")

    cf = config["counts"]
    w('<aside class="ca-count" aria-labelledby="ca-count-title">')
    w(f'<p class="ca-kicker" id="ca-count-title">{esc(cf["kicker"])}</p>')
    w(
        f'<p class="ca-count__num"><strong>{fmt_int(data["opinion"])}</strong>'
        f'<small>{esc(cf["unit"])}</small></p>'
    )
    w(f'<p class="ca-count__sub">{esc(fill(cf["sub"], values))}</p>')
    w(f'<p class="ca-count__bar-title">{esc(fill(cf["bar_title"], values))}</p>')
    w(f'<p class="ca-count__caveat">{esc(fill(cf["caveat"], values))}</p>')
    bar = []
    legend = []
    for s in data["stances"]:
        pct = fmt_pct(s["count"], data["opinion"])
        pat = PATTERN_CLASS.get(s["pattern"], "pat-plain")
        bar.append(
            f'<span class="ca-bar__seg {pat}" style="--c:{esc(s["color"])};width:{pct}" '
            f'title="{esc(s["label"])} {fmt_int(s["count"])}件"></span>'
        )
        legend.append(
            f'<li><i class="{pat}" style="--c:{esc(s["color"])}" aria-hidden="true"></i>'
            f'<span>{esc(s["label"])}</span><b>{fmt_int(s["count"])}件</b><em>{pct}</em></li>'
        )
    w(f'<div class="ca-bar" aria-hidden="true">{"".join(bar)}</div>')
    w(f'<ul class="ca-legend">{"".join(legend)}</ul>')
    w(f'<p class="ca-count__extra">{esc(fill(cf["caveat_extra"], values))}</p>')
    w(f'<p class="ca-count__period">{esc(fill(cf["period"], values))}</p>')
    w("</aside>")
    w("</div>")

    # よく聞かれること（旧FAQ。日付は確認日から差し込む）
    fq = config["faq"]
    w('<section class="ca-faq" aria-labelledby="ca-faq-title">')
    w(f'<h2 id="ca-faq-title">{esc(fq["title"])}</h2>')
    w('<div class="ca-faq__list">')
    for item in fq["items"]:
        w(f'<details><summary>{esc(item["q"])}</summary><p>{esc(fill(item["a"], values))}</p></details>')
    w("</div>")
    w("</section>")

    # 出典と確認日
    w(f'<details class="ca-sources"><summary>{esc(config["sources_title"])}</summary><ul>')
    for key in sorted(sources):
        s = sources[key]
        w(
            f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["name"])}</a>'
            f'<span>{esc(jp_date(s["checked_on"]))}確認</span></li>'
        )
    w("</ul></details>")
    w("</section>")

    fragment = "\n".join(out) + "\n"
    leftover = re.findall(r"\{[a-z_]+\}", fragment)
    if leftover:
        raise OpeningError(f"差し込まれていない値があります: {leftover}")
    return fragment


def render_page(fragment: str, config: dict) -> str:
    title = "".join(config["title_lines"])
    return (
        "<!doctype html>\n"
        '<html lang="ja">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="robots" content="noindex">\n'
        f"<title>{esc(title)}（冒頭の試作）</title>\n"
        '<link rel="stylesheet" href="opening.css">\n'
        "</head>\n<body>\n"
        '<header class="ca-site"><span class="ca-site__logo">SNS反応まっぷ</span>'
        '<span class="ca-site__note">冒頭の試作（公開前）</span></header>\n'
        "<main>\n"
        f"{fragment}"
        "</main>\n</body>\n</html>\n"
    )


def fragment_for(config_path: Path = DEFAULT_CONFIG, as_of: str | None = None) -> str:
    """読書面の試作（scripts/constitutional_reading.py）が冒頭をそのまま差し込むための入口。"""
    config, public, planet, background = load_inputs(config_path)
    data = summarize(public, planet)
    return render_fragment(config, data, background, planet.get("source_label") or "検索", as_of)


def build(config_path: Path, as_of: str | None = None) -> dict[str, str]:
    config, public, planet, background = load_inputs(config_path)
    fragment = fragment_for(config_path, as_of)
    return {"opening-fragment.html": fragment, "index.html": render_page(fragment, config),
            "opening.css": (ASSETS / "opening.css").read_text(encoding="utf-8")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--as-of", help="基準日 YYYY-MM-DD（既定は公開JSONの updated_on。施行の段階を決める）")
    ap.add_argument("--check", action="store_true", help="書き込まず、出力と既存ファイルの差分の有無だけ返す")
    args = ap.parse_args()
    try:
        outputs = build(args.config, args.as_of)
    except OpeningError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 2
    changed = []
    for name, text in outputs.items():
        path = args.out_dir / name
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old != text:
            changed.append(name)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    if args.check:
        print("差分あり: " + ", ".join(changed) if changed else "差分なし")
        return 1 if changed else 0
    print("更新: " + ", ".join(changed) if changed else "変更なし")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
