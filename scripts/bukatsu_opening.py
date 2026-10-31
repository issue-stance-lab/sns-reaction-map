"""部活動の地域移行ページの冒頭（題名・段階の一言・短答3つ・黄色の件数札・改革の期間の図・件数）を生成する試作。

消費税減税の冒頭（scripts/consumption_tax_opening.py）と同じ型。テーマごとに違うのは設定JSONと次の点。
- 時制は法案ではなく年度の進行。改革推進期間（2023〜2025年度）→改革実行期間の前期（2026〜2028年度）→後期
  （2029〜2031年度）→期間の後、を基準日で切り替える。前期の終わりの中間評価を確かめないまま後期に入ると
  「中間評価の結果は未確認」の段階（kouki_unchecked）になる。
- 図柄は現行ページの黄色の斜めの件数札（SVG）を引き継ぐ。件数は生成時に公開JSONから入れる（画像に焼き込まない）。

入力:
  configs/bukatsu-chiiki-opening.json  冒頭の文言・短答・改革の期間と日付・出典・確認日（手で直す場所はここだけ）
  docs/data/themes/bukatsu-chiiki.json 件数・論点別件数・立場・収集期間・更新日（公開JSON）
  configs/planet/bukatsu-chiiki.yaml   立場の色と並び、理由の内訳がある論点（sub_issues）
  THEMES.yaml                          収集元の名前と次回の更新予定（collect_at）
  quality/research/bukatsu-chiiki-primary-sources.md  確認日の照合（設定の memo_section の節）
  configs/theme-seo.json               display_headline（H1 と一致を確かめるだけ）

出力（既定は quality/prototypes/bukatsu-chiiki-opening/）:
  opening-fragment.html  冒頭の部品（マーカー付き）
  index.html             確認用の単独ページ（同じフォルダーの opening.css を読む）
  opening.css            正本 scripts/bukatsu_redesign/opening.css の写し

段階は「今日」ではなく基準日で決める。基準日の既定は公開JSONの updated_on で、--as-of で上書きできる。
  suishin          改革推進期間（2023-04-01〜2026-03-31）
  zenki            改革実行期間の前期（2026-04-01〜2029-03-31）
  kouki            後期で、中間評価の結果を確かめた（period.midterm_checked_on あり）
  kouki_unchecked  後期で、中間評価の結果をまだ確かめていない
  ended            改革実行期間の後（2032-04-01 以降）
日付を過ぎても生成は止めない。期間の日付の順番が崩れている、確認日がメモの節と違う、
display_headline と H1 が違う、件数の合計が公開JSONと合わない、といった組み合わせだけ止める。

時刻や乱数は使わないので、同じ入力なら何度実行しても同じ出力になる。

    python3 scripts/bukatsu_opening.py [--as-of YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "configs" / "bukatsu-chiiki-opening.json"
DEFAULT_OUT = ROOT / "quality" / "prototypes" / "bukatsu-chiiki-opening"
ASSETS = ROOT / "scripts" / "bukatsu_redesign"
START = "<!-- BUKATSU_OPENING_START -->"
END = "<!-- BUKATSU_OPENING_END -->"
PHASES = ("suishin", "zenki", "kouki", "kouki_unchecked", "ended")
PERIOD_ORDER = ("suishin_from", "suishin_to", "zenki_from", "zenki_to", "kouki_from", "kouki_to")
MEMO_DATE = re.compile(r"確認日[:：]\s*(\d{4}-\d{2}-\d{2})")


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def jp_date(iso: str, with_year: bool = True) -> str:
    d = dt.date.fromisoformat(str(iso))
    return f"{d.year}年{d.month}月{d.day}日" if with_year else f"{d.month}月{d.day}日"


def jp_month(iso: str) -> str:
    d = dt.date.fromisoformat(str(iso))
    return f"{d.year}年{d.month}月"


def fiscal_year(iso: str) -> int:
    """日本の年度（4月始まり）。"""
    d = dt.date.fromisoformat(str(iso))
    return d.year if d.month >= 4 else d.year - 1


def link(url: str, label: str) -> str:
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'


def lookup(config: dict, dotted: str | None):
    """"period.zenki_from" のような参照を設定から引く。"""
    if not dotted:
        return None
    node = config
    for part in dotted.split("."):
        node = node[part]
    return node


def memo_checked_on(memo_text: str, heading: str) -> str:
    """一次資料メモの節（見出しに heading を含む ### 節）の「確認日」の最新。節が1つでなければ止める。"""
    lines = memo_text.splitlines()
    hits = [i for i, l in enumerate(lines) if re.match(r"#{2,3} ", l) and heading in l]
    if len(hits) != 1:
        raise SystemExit(f"一次資料メモで見出し「{heading}」が {len(hits)} 件あります（1件だけのはず）")
    start = hits[0]
    level = len(lines[start]) - len(lines[start].lstrip("#"))
    end = next((j for j in range(start + 1, len(lines)) if re.match(r"#{1,%d} " % level, lines[j])), len(lines))
    dates = MEMO_DATE.findall("\n".join(lines[start:end]))
    if not dates:
        raise SystemExit(f"一次資料メモの「{heading}」に確認日がありません")
    return max(dates)


# ---- 入力と検査 ---------------------------------------------------------------

def headline_of(config: dict) -> str:
    return "".join(config["title"]["phrases"]) + "".join(config["title"]["sub"])


def check_config(config: dict, public: dict, memo_text: str, display_headline: str | None) -> None:
    period = config["period"]
    days = [dt.date.fromisoformat(period[k]) for k in PERIOD_ORDER]
    if days != sorted(days):
        raise SystemExit("period の日付の順番が崩れています（推進期間→前期→後期）")
    for a, b in (("suishin_to", "zenki_from"), ("zenki_to", "kouki_from")):
        if dt.date.fromisoformat(period[a]) + dt.timedelta(days=1) != dt.date.fromisoformat(period[b]):
            raise SystemExit(f"period の {a} と {b} がつながっていません（翌日から次の期間）")
    if not (period["zenki_from"] <= period["certification_transition_to"] <= period["zenki_to"]):
        raise SystemExit("認定の経過措置の終わりが前期の中にありません")
    if not (period["suishin_from"] <= period["guideline_on"] < period["zenki_from"]):
        raise SystemExit("ガイドラインの策定日が改革推進期間の中にありません")
    checked = config["checked_on"]
    if checked < period["guideline_on"]:
        raise SystemExit("checked_on がガイドラインの策定日より前です")
    if checked < public["claim_verification"]["checked_on"]:
        raise SystemExit("制度の確認日 checked_on が、主張の照合日より古くなっています")
    memo_on = memo_checked_on(memo_text, config["memo_section"])
    if memo_on != checked:
        raise SystemExit(f"一次資料メモの節「{config['memo_section']}」の確認日 {memo_on} が checked_on {checked} と違います"
                         "（確認し直したら、メモに節を足して memo_section を直してください）")
    mid = period.get("midterm_checked_on")
    if mid:
        if mid > checked:
            raise SystemExit("period.midterm_checked_on が確認日 checked_on より後です")
        if mid < period["kouki_from"][:4] + "-01-01":
            raise SystemExit("period.midterm_checked_on が前期の終わり（中間評価）より前です")
    if display_headline is not None and display_headline != headline_of(config):
        raise SystemExit(f"H1（{headline_of(config)}）が configs/theme-seo.json の display_headline（{display_headline}）と違います")
    issue_ids = {issue["id"] for issue in public["issues"]}
    for a in config["answers"]:
        for item in a.get("issue_links", []):
            if item["id"] not in issue_ids or not item.get("text"):
                raise SystemExit(f"短答 {a['key']} の論点リンクが不正です: {item}")
        for key in ("short", "body"):
            missing = set(PHASES) - set(a[key]) if "all" not in a[key] else set()
            if missing:
                raise SystemExit(f"短答 {a['key']} の {key} に段階 {sorted(missing)} の文がありません")
    for p in PHASES:
        for key in ("status", "status_label"):
            if p not in config["phase_text"][key]:
                raise SystemExit(f"phase_text.{key} に段階 {p} の文がありません")


def load_inputs(config_path: Path = DEFAULT_CONFIG) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    paths = {key: ROOT / value for key, value in config["inputs"].items()}
    public = json.loads(paths["public_json"].read_text(encoding="utf-8"))
    planet = yaml.safe_load(paths["planet_config"].read_text(encoding="utf-8"))
    themes = yaml.safe_load(paths["themes_registry"].read_text(encoding="utf-8"))
    seo = json.loads(paths["theme_seo"].read_text(encoding="utf-8"))
    entry = themes.get("themes", themes).get(config["theme_id"])
    if not entry:
        raise SystemExit(f"THEMES.yaml に {config['theme_id']} がありません")
    if public.get("theme_id") != config["theme_id"]:
        raise SystemExit("公開JSONのテーマIDが設定と一致しません")
    seo_entry = next((t for t in seo["themes"] if t["id"] == config["theme_id"]), {})
    check_config(config, public, paths["primary_memo"].read_text(encoding="utf-8"), seo_entry.get("display_headline"))
    return {
        "config": config,
        "public": public,
        "planet": planet,
        "source": str(entry.get("sample_source", "")),
        "next_collect": str(entry["collect_at"]) if entry.get("collect_at") else "",
    }


# ---- 段階 ---------------------------------------------------------------------

def phase_of(config: dict, as_of: str) -> str:
    dt.date.fromisoformat(as_of)
    p = config["period"]
    if as_of < p["suishin_from"]:
        raise SystemExit("基準日が改革推進期間より前です（この冒頭は2023年度以後の段階だけを扱います）")
    if as_of <= p["suishin_to"]:
        return "suishin"
    if as_of <= p["zenki_to"]:
        return "zenki"
    if as_of <= p["kouki_to"]:
        mid = p.get("midterm_checked_on")
        return "kouki" if mid and mid <= as_of else "kouki_unchecked"
    return "ended"


def span(config: dict, a: str, b: str) -> str:
    p = config["period"]
    return f"{fiscal_year(p[a])}〜{fiscal_year(p[b])}年度"


def values_for(config: dict, as_of: str, public: dict | None = None) -> dict:
    p = config["period"]
    v = {
        "checked": jp_date(config["checked_on"]),
        "checked_dot": config["checked_on"].replace("-", "."),
        "as_of": jp_date(as_of),
        "guideline": jp_date(p["guideline_on"]),
        "guideline_ym": jp_month(p["guideline_on"]),
        "zenki_span": span(config, "zenki_from", "zenki_to"),
        "kouki_span": span(config, "kouki_from", "kouki_to"),
        "kouki_end": jp_date(p["kouki_to"]),
        "year_in_zenki": max(1, fiscal_year(as_of) - fiscal_year(p["zenki_from"]) + 1),
    }
    if public:
        top = max(public["issues"], key=lambda i: (i.get("kind") != "other", int(i["count"])))
        v["top_issue"] = top["label"]
        v["top_count"] = f"{int(top['count']):,}"
    return v


def by_phase(text: dict, phase: str) -> str:
    """phase ごとの文言（無ければ all）。"""
    return text[phase] if phase in text else text["all"]


def step_states(config: dict, as_of: str) -> list[str]:
    """基準日で各段を 済み・現在・予定・目安・未確認 に分ける。中間評価（target）は日付が示されていないので「目安」。"""
    states = []
    mid_checked = config["period"].get("midterm_checked_on")
    for step in config["steps"]["items"]:
        date = lookup(config, step.get("date_from"))
        if date <= as_of:
            if step.get("target") and not (mid_checked and mid_checked <= as_of):
                states.append("unconfirmed")
            else:
                states.append("done")
        else:
            states.append("target" if step.get("target") else "planned")
    done = [i for i, s in enumerate(states) if s == "done"]
    if done:
        states[done[-1]] = "current"
    return states


# ---- 部品 ---------------------------------------------------------------------

def render_title(config: dict) -> str:
    title = config["title"]
    accents = set(title.get("accent_indices", []))
    phrases = "".join(
        f'<span class="bko-phrase{" bko-accent" if i in accents else ""}">{esc(p)}</span>'
        for i, p in enumerate(title["phrases"])
    )
    sub = "".join(f'<span class="bko-sub-phrase">{esc(p)}</span>' for p in title["sub"])
    return f'<h1 class="bko-title">{phrases}<span class="bko-sub">{sub}</span></h1>'


def render_poster(config: dict, public: dict) -> str:
    """黄色の斜めの件数札（現行ページの図柄）。数字は公開JSONの意見件数を文字で入れる。"""
    c = config["count_poster"]
    total = f"{int(public['opinion_count']):,}"
    return (
        f'<div class="bko-poster" aria-label="{esc(c["label"])} {esc(total)}件（{esc(c["caption"])}）">'
        '<svg class="bko-poster__svg" viewBox="0 0 440 270" aria-hidden="true">'
        f'<text class="bko-poster__label" x="24" y="42">{esc(c["label"])}</text>'
        f'<text class="bko-poster__digits" x="16" y="207" textLength="340" lengthAdjust="spacingAndGlyphs">{esc(total)}</text>'
        '<text class="bko-poster__unit" x="363" y="204">件</text>'
        '<path class="bko-poster__rays" d="M358 65l4-17M375 71l12-13M388 86l17-6"/>'
        f'<text class="bko-poster__caption" x="220" y="246" text-anchor="middle">{esc(c["caption"])}</text>'
        "</svg></div>"
    )


def render_status(config: dict, as_of: str) -> str:
    phase = phase_of(config, as_of)
    pt = config["phase_text"]
    text = pt["status"][phase].format(**values_for(config, as_of))
    return (
        f'<p class="bko-status bko-status--{phase}"><b>{esc(pt["status_label"][phase])}</b>'
        f"<span>{esc(text)}</span></p>"
    )


def icon(key: str) -> str:
    paths = {
        # カレンダー（いつから）。現行ページのピクトグラムを引き継ぐ
        "when": '<rect x="3" y="5" width="18" height="17" rx="2"/><path d="M7 2v6M17 2v6M3 11h18M7 15h2M15 15h2M7 18h2"/>',
        # 財布（費用）
        "cost": '<rect x="3" y="6" width="18" height="15" rx="2"/><path d="m4 6 13-3v3M16 11h6v6h-6Z"/><circle cx="18" cy="14" r=".5"/>',
        # 吹き出し（SNSの意見）
        "issues": '<path d="M3 4h18v13H9l-6 4Z"/><circle cx="7" cy="10" r=".5"/><circle cx="12" cy="10" r=".5"/><circle cx="17" cy="10" r=".5"/>',
    }
    return (
        '<svg class="bko-picto" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{paths[key]}</svg>'
    )


def render_answers(config: dict, as_of: str, public: dict) -> str:
    phase = phase_of(config, as_of)
    values = values_for(config, as_of, public)
    cards = []
    for i, a in enumerate(config["answers"], 1):
        short = by_phase(a["short"], phase).format(**values)
        body = by_phase(a["body"], phase).format(**values)
        issue_links = "".join(
            f'<a class="bko-issue-link" href="#issue-{esc(item["id"])}" '
            f'data-opening-issue="{esc(item["id"])}">{esc(item["text"])}</a>'
            for item in a.get("issue_links", [])
        )
        links_html = f'<nav class="bko-issue-links" aria-label="{esc(a["question"])}に関係する論点">{issue_links}</nav>' if issue_links else ""
        detail_link = (
            f'<a class="bko-answer__link" href="{esc(a["link"]["href"])}">{esc(a["link"]["text"])} →</a>'
            if a["link"]["href"] not in {"#issue-" + item["id"] for item in a.get("issue_links", [])} else ""
        )
        cards.append(
            f'<article class="bko-answer bko-answer--{esc(a["key"])}" aria-labelledby="bko-q{i}">'
            f'<p class="bko-answer__kind bko-answer__kind--{esc(a["kind"])}">{esc(a["kind_label"])}</p>'
            f'<h2 id="bko-q{i}">{icon(a["key"])}{esc(a["question"])}</h2>'
            f'<p class="bko-answer__short">{esc(short)}</p>{links_html}'
            f'<p class="bko-answer__body">{esc(body)}</p>'
            f'{detail_link}</article>'
        )
    return f'<div class="bko-answers" aria-label="検索で多い3つの疑問への短い答え">{"".join(cards)}</div>'


def position(config: dict, iso: str) -> float:
    axis = config["steps"]["axis"]
    start, end = dt.date.fromisoformat(axis["from"]), dt.date.fromisoformat(axis["to"])
    day = min(max(dt.date.fromisoformat(iso), start), end)
    return (day - start).days / (end - start).days * 100


def render_band(config: dict, as_of: str) -> str:
    """時間に比例した帯。推進期間・前期・後期を塗り分け、各段の日付に印、基準日に縦線を置く。"""
    axis = config["steps"]["axis"]
    first = fiscal_year(axis["from"])
    last = fiscal_year(axis["to"])
    ticks = "".join(
        f'<span class="bko-band__tick" style="--x:{position(config, f"{y}-04-01"):.2f}%">{y}</span>'
        for y in range(first, last + 1)
    )
    bands = "".join(
        f'<span class="bko-band__seg bko-band__seg--{esc(b["key"])}" style="--l:{position(config, lookup(config, b["from"])):.2f}%;'
        f'--r:{100 - position(config, lookup(config, b["to"])):.2f}%"><b>{esc(b["label"])}</b></span>'
        for b in config["steps"]["bands"]
    )
    marks = "".join(
        f'<span class="bko-band__mark" style="--x:{position(config, lookup(config, s["date_from"])):.2f}%"></span>'
        for s in config["steps"]["items"]
    )
    now = position(config, as_of)
    return (
        f'<div class="bko-band" aria-hidden="true">'
        f'<div class="bko-band__track">{bands}{marks}'
        f'<span class="bko-band__now{" bko-band__now--right" if now > 50 else ""}" style="--x:{now:.2f}%">'
        f'<i>{esc(jp_date(as_of))}</i></span></div>'
        f'<div class="bko-band__ticks">{ticks}<span class="bko-band__unit">年度</span></div></div>'
    )


def render_steps(config: dict, as_of: str) -> str:
    s = config["steps"]
    values = values_for(config, as_of)
    labels = config["phase_text"]["state_labels"]
    states = step_states(config, as_of)
    policy = "".join(
        f'<div class="bko-policy__row bko-policy__row--{esc(p["key"])}"><dt>{esc(p["label"])}</dt><dd>{esc(p["text"])}</dd></div>'
        for p in s["policy"]
    )
    items = []
    for step, state in zip(s["items"], states):
        date = lookup(config, step["date_from"])
        when = jp_month(date) + "末ごろ" if step.get("target") else jp_date(date)
        current = ' aria-current="step"' if state == "current" else ""
        items.append(
            f'<li class="bko-step bko-step--{state}"{current}>'
            f'<span class="bko-step__box" aria-hidden="true"></span>'
            f'<time datetime="{esc(date)}">{esc(when)}</time>'
            f'<strong>{esc(step["title"])}</strong>'
            f'<em class="bko-step__state">{esc(labels[state].format(**values))}</em>'
            f'<p>{esc(step["note"])}</p></li>'
        )
    checked = config["phase_text"]["checked_line"].format(**values)
    srcs = "".join(f"<li>{link(x['url'], x['label'])}</li>" for x in s["sources"])
    return (
        f'<section class="bko-steps" id="bko-steps" aria-labelledby="bko-steps-title">'
        f'<h2 id="bko-steps-title" class="bko-steps__label">{esc(s["label"])}</h2>'
        f'<dl class="bko-policy">{policy}</dl>'
        f'<p class="bko-steps__target">{esc(s["target_note"])}</p>'
        f"{render_band(config, as_of)}"
        f'<ol class="bko-steps__list">{"".join(items)}</ol>'
        f'<p class="bko-steps__checked" data-checked-on="{esc(config["checked_on"])}">{esc(checked)}</p>'
        f'<ul class="bko-steps__sources">{srcs}</ul>'
        f"</section>"
    )


def render_count(data: dict) -> str:
    config, public, planet = data["config"], data["public"], data["planet"]
    c = config["count"]
    total = public["opinion_count"]
    if public.get("issue_assigned_count") not in (None, total):
        raise SystemExit("論点を割り当てた件数が意見件数と一致しません")

    # 立場：論点をまたいで合計。並びと色は planet 設定（山なみと同じ）
    order = [s["id"] for s in planet["stances"]]
    color = {s["id"]: s["color"] for s in planet["stances"]}
    label = {s["id"]: s["label"] for s in planet["stances"]}
    totals = {sid: 0 for sid in order}
    for issue in public["issues"]:
        for s in issue["stances"]:
            if s["id"] not in totals:
                raise SystemExit(f"planet設定に無い立場です: {s['id']}")
            totals[s["id"]] += s["count"]
    if sum(totals.values()) != total:
        raise SystemExit("立場の合計が意見件数と一致しません")
    segs = "".join(
        f'<span style="--w:{totals[sid] / total * 100:.2f}%;--c:{color[sid]}"></span>' for sid in order if totals[sid]
    )
    stance_items = "".join(
        f'<li><span class="bko-key" style="--c:{color[sid]}" aria-hidden="true"></span>{esc(label[sid])}'
        f"<b>{totals[sid] / total * 100:.1f}%</b><small>{totals[sid]:,}件</small></li>"
        for sid in order
    )

    # 論点別：多い順。「その他」は最後。理由の内訳（planet の sub_issues）が無い論点に印
    if sum(i["count"] for i in public["issues"]) != total:
        raise SystemExit("論点別件数の合計が意見件数と一致しません")
    issues = sorted(
        (i for i in public["issues"] if i["count"] > 0), key=lambda i: (i.get("kind") == "other", -i["count"])
    )
    with_reason = set((planet.get("sub_issues") or {}).keys())
    top = max(i["count"] for i in issues)
    rows, missing = [], []
    for issue in issues:
        tag = ""
        if issue["label"] not in with_reason:
            missing.append(issue["label"])
            tag = f'<em class="bko-flag">{esc(c["no_reason_tag"])}</em>'
        rows.append(
            f'<li class="bko-issue{" bko-issue--other" if issue.get("kind") == "other" else ""}" data-issue="{esc(issue["id"])}">'
            f'<span class="bko-issue__name">{esc(issue["label"])}{tag}</span>'
            f'<span class="bko-issue__bar" aria-hidden="true"><i style="--w:{issue["count"] / top * 100:.2f}%"></i></span>'
            f'<b>{issue["count"]:,}<small>件</small></b></li>'
        )
    note = c["no_reason_note_template"].format(labels="".join(f"「{m}」" for m in missing)) if missing else ""

    period = public["collection_period"]
    caption = c["caption_template"].format(
        source=data["source"],
        collected=f"{public['collected_count']:,}",
        start=jp_date(period["start"]),
        end=jp_date(period["end"], with_year=False),
    )
    updated = c["updated_template"].format(
        updated=jp_date(public["updated_on"]),
        next=jp_date(data["next_collect"], with_year=False) if data["next_collect"] else "未定",
    )
    return (
        f'<section class="bko-count" id="bko-count" aria-labelledby="bko-count-title">'
        f'<div class="bko-count__total"><h2 id="bko-count-title">{esc(c["label"])}</h2>'
        f'<p class="bko-count__num"><strong>{total:,}</strong><span>件</span></p>'
        f'<p class="bko-count__poll">{esc(c["not_poll"])}</p>'
        f'<p class="bko-count__caption">{esc(caption)}</p>'
        f'<h3 class="bko-count__sub">{esc(c["stance_title"])}</h3>'
        f'<div class="bko-stance" aria-hidden="true">{segs}</div><ul class="bko-stance__list">{stance_items}</ul></div>'
        f'<div class="bko-count__issues"><h3 class="bko-count__sub">{esc(c["issues_title_template"].format(n=len(issues)))}</h3>'
        f'<ol class="bko-issues">{"".join(rows)}</ol>'
        + (f'<p class="bko-count__note">{esc(note)}</p>' if note else "")
        + f'<p class="bko-count__updated">{esc(updated)}</p></div>'
        f"</section>"
    )


def default_as_of(data: dict) -> str:
    """基準日の既定は公開JSONの更新日（今日の日付は使わない）。"""
    return data["public"]["updated_on"]


def render_fragment(data: dict, as_of: str | None = None) -> str:
    config, public = data["config"], data["public"]
    as_of = as_of or default_as_of(data)
    phase = phase_of(config, as_of)
    values = values_for(config, as_of, public)
    crumb = " ／ ".join(esc(c) for c in config["crumb"])
    sources = "".join(f"<li>{link(s['url'], s['label'])}</li>" for s in config["sources"])
    return "\n".join(
        [
            START,
            f'<section class="bko" aria-label="部活動の地域移行の冒頭" data-as-of="{esc(as_of)}" data-phase="{phase}">',
            f'<header class="bko-hero"><p class="bko-crumb"><span>{crumb}</span>'
            f'<span data-checked-on="{esc(config["checked_on"])}">{esc(config["crumb_checked"].format(**values))}</span></p>'
            f'<div class="bko-heading">{render_title(config)}{render_poster(config, public)}</div>'
            f'<p class="bko-lead">{esc(config["lead"])}</p>'
            f'<p class="bko-name-note">{esc(config["name_note"].format(**values))}</p>'
            f"{render_status(config, as_of)}</header>",
            render_answers(config, as_of, public),
            render_steps(config, as_of),
            render_count(data),
            f'<aside class="bko-sources"><h2>{esc(config["sources_title"])}</h2><ul>{sources}</ul></aside>',
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
<title>部活動の地域移行 冒頭試作</title>
<meta name="robots" content="noindex">
<link rel="stylesheet" href="opening.css">
</head>
<body>
<main class="bko-page">
{fragment}</main>
</body>
</html>
"""


def fragment_for(config_path: Path = DEFAULT_CONFIG, as_of: str | None = None) -> str:
    """冒頭の部品（マーカー付き）。読書面の試作がこの下に読書面をつなぐ。"""
    return render_fragment(load_inputs(config_path), as_of)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--as-of", help="基準日 YYYY-MM-DD（既定は公開JSONの updated_on）")
    args = parser.parse_args()
    data = load_inputs(args.config)
    fragment = render_fragment(data, args.as_of)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "opening-fragment.html").write_text(fragment, encoding="utf-8")
    (args.out_dir / "index.html").write_text(render_page(fragment), encoding="utf-8")
    shutil.copyfile(ASSETS / "opening.css", args.out_dir / "opening.css")
    print(f"wrote {args.out_dir / 'opening-fragment.html'}")
    print(f"wrote {args.out_dir / 'index.html'}")


if __name__ == "__main__":
    main()
