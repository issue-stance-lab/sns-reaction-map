#!/usr/bin/env python3
"""皇室典範改正ページの冒頭（題名・短答・3つの問い・件数）を生成する試作。

入力は2つだけ。
- configs/koshitsu-tenpakai-opening.json : 問い・短答・日付・注記などの文言
- docs/data/themes/koshitsu-tenpakai.json : 件数・論点別件数・立場（公開JSON）

出力（既定は quality/prototypes/koshitsu-tenpakai-opening/）
- opening-fragment.html : 公開ページへ差し込む想定の冒頭部品
- index.html            : 確認用の単独ページ（同じフォルダーの opening.css を読む）

件数は公開JSONから読み、文言にも画像にも手で書かない。施行前・施行後の時制は
設定JSONの as_of（または --as-of）と施行日から決める。同じ入力なら出力は同じ。

    python3 scripts/koshitsu_opening.py
    python3 scripts/koshitsu_opening.py --as-of 2026-10-25 --out-dir /tmp/x   # 施行後の表示を確かめる
"""

from __future__ import annotations

import argparse
import html
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "koshitsu-tenpakai-opening.json"
OUT_DIR = ROOT / "quality" / "prototypes" / "koshitsu-tenpakai-opening"

FRAGMENT_START = "<!-- KOSHITSU_OPENING_START -->"
FRAGMENT_END = "<!-- KOSHITSU_OPENING_END -->"


def esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def ja_date(iso: str, with_year: bool = True) -> str:
    d = date.fromisoformat(iso)
    return f"{d.year}年{d.month}月{d.day}日" if with_year else f"{d.month}月{d.day}日"


def fmt(n: int) -> str:
    return f"{n:,}"


def pct(part: int, whole: int) -> str:
    return f"{part / whole * 100:.1f}"


# ---------------------------------------------------------------- データ


def load(config_path: Path) -> tuple[dict, dict]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    public = json.loads((ROOT / config["public_json"]).read_text(encoding="utf-8"))
    if public.get("theme_id") != config["theme_id"]:
        raise SystemExit("公開JSONのテーマが設定と一致しません")
    return config, public


def stance_totals(public: dict) -> dict[str, int]:
    totals: dict[str, int] = {}
    for issue in public["issues"]:
        for stance in issue["stances"]:
            totals[stance["id"]] = totals.get(stance["id"], 0) + int(stance["count"])
    return totals


def check_counts(public: dict, totals: dict[str, int]) -> None:
    """公開JSONの中で数が食い違っていたら止める（表示前の最低限の照合）。"""
    opinion = int(public["opinion_count"])
    issue_sum = sum(int(i["count"]) for i in public["issues"])
    if issue_sum != opinion:
        raise SystemExit(f"論点別件数の合計 {issue_sum} が意見数 {opinion} と一致しません")
    if sum(totals.values()) != opinion:
        raise SystemExit(f"立場の合計 {sum(totals.values())} が意見数 {opinion} と一致しません")


def phase_of(config: dict, as_of: str) -> tuple[str, int]:
    law = config["law"]
    today = date.fromisoformat(as_of)
    enforce = date.fromisoformat(law["enforcement_on"])
    if today < enforce:
        return "before", (enforce - today).days
    if law.get("enforcement_confirmed_on"):
        return "after_confirmed", (today - enforce).days
    return "after_unconfirmed", (today - enforce).days


# ---------------------------------------------------------------- 図柄（数字を含まないSVG）

INK = "#1e2238"
INDIGO = "#27346a"
VERMILION = "#b4432e"
GOLD = "#b08a3e"


def node(x: float, y: float, kind: str, *, hi: bool = False, r: float = 9) -> str:
    """系図の記号。四角＝男性、丸＝女性（系図の慣例）。hi は注目する人。"""
    fill = "#fffdf8"
    stroke = INDIGO
    ring = ""
    if hi:
        ring = f'<circle cx="{x}" cy="{y}" r="{r + 6}" fill="none" stroke="{GOLD}" stroke-width="2"/>'
        fill = INDIGO
    if kind == "m":
        shape = (f'<rect x="{x - r}" y="{y - r}" width="{2 * r}" height="{2 * r}" rx="2" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    else:
        shape = f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    return ring + shape


def line(x1, y1, x2, y2, color=INDIGO, dash: bool = False, w: float = 2.4) -> str:
    d = ' stroke-dasharray="5 4"' if dash else ""
    return (f'<path d="M{x1} {y1} V{(y1 + y2) / 2} H{x2} V{y2}" fill="none" stroke="{color}" '
            f'stroke-width="{w}"{d} stroke-linecap="round"/>')


def term_figure(kind: str) -> str:
    """短答の3語（女性天皇・女系天皇・女性宮家）を、系図の線で見分ける小図。"""
    parts: list[str] = []
    if kind == "female":
        # 父（天皇）から娘へ。娘本人が天皇になる＝女性天皇
        parts += [line(60, 22, 60, 78), node(60, 22, "m"), node(60, 78, "f", hi=True)]
        caption = "父方でつながる女性"
    elif kind == "matrilineal":
        # 父→娘→その子。娘（母）を通じてつながる子が天皇＝女系天皇
        parts += [line(40, 16, 40, 52), line(40, 52, 80, 92, VERMILION), node(40, 16, "m"),
                  node(40, 52, "f"), node(80, 92, "m", hi=True, r=8)]
        caption = "母方でつながる子"
    else:
        # 女性皇族本人は皇族の枠に残り、配偶者と子は枠の外
        parts += [f'<rect x="16" y="30" width="54" height="52" rx="10" fill="none" '
                  f'stroke="{INDIGO}" stroke-width="1.6" stroke-dasharray="4 4"/>',
                  f'<path d="M52 56 H92" stroke="{INK}" stroke-width="1.6"/>',
                  line(72, 56, 72, 96, INK, w=1.6),
                  node(42, 56, "f", hi=True), node(100, 56, "m"), node(72, 96, "f", r=7)]
        caption = "枠＝皇族。配偶者と子は枠の外"
    return (f'<svg class="ko-term-fig" viewBox="0 0 120 112" role="img" aria-label="{esc(caption)}">'
            + "".join(parts) + "</svg>")


def hero_figure() -> str:
    """冒頭の図柄。系図の線をほどいた模様で、父方（紺）と母方（朱）の2本の線を見せる。"""
    p: list[str] = []
    # 世代ごとの横の罫（和紙の罫線のような薄い線）
    for y in (40, 120, 200, 280):
        p.append(f'<path d="M0 {y} H420" stroke="#e4dccd" stroke-width="1"/>')
    # 父方の幹
    p += [line(210, 40, 130, 120), line(210, 40, 290, 120), line(130, 120, 80, 200),
          line(130, 120, 170, 200), line(290, 120, 250, 200), line(290, 120, 340, 200),
          line(80, 200, 60, 280), line(170, 200, 150, 280), line(250, 200, 230, 280)]
    # 母方の線（朱）
    p += [line(340, 200, 330, 280, VERMILION), line(170, 200, 200, 280, VERMILION)]
    # 皇族の枠（点線）。外に出る人がいることを示す
    p.append(f'<rect x="38" y="16" width="344" height="210" rx="22" fill="none" '
             f'stroke="{INDIGO}" stroke-width="1.4" stroke-dasharray="6 6" opacity=".55"/>')
    p += [node(210, 40, "m", r=12), node(130, 120, "m", r=11), node(290, 120, "m", r=11),
          node(80, 200, "m"), node(170, 200, "f", hi=True), node(250, 200, "m"),
          node(340, 200, "f"), node(60, 280, "m", r=8), node(150, 280, "m", r=8),
          node(230, 280, "f", r=8), node(330, 280, "m", r=8), node(200, 280, "f", r=8)]
    return ('<svg class="ko-hero-fig" viewBox="0 0 420 310" aria-hidden="true" focusable="false">'
            + "".join(p) + "</svg>")


ICONS = {
    # 条文（巻物）
    "scroll": ('<path d="M7 5h11a2 2 0 0 1 2 2v12H9a2 2 0 0 1-2-2z" fill="none" stroke="currentColor" '
               'stroke-width="1.8"/><path d="M4 7a2 2 0 0 1 3-2v12a2 2 0 1 1-3-2z" fill="none" '
               'stroke="currentColor" stroke-width="1.8"/><path d="M11 9h6M11 12h6M11 15h4" '
               'stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>'),
    # 人（系図の丸と、上へのびる線）
    "person": ('<path d="M12 3v5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>'
               '<circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.8"/>'
               '<path d="M5 21c1-3.5 4-5 7-5s6 1.5 7 5" fill="none" stroke="currentColor" '
               'stroke-width="1.8" stroke-linecap="round"/>'),
    # 意見（ふきだし2つ）
    "talk": ('<path d="M3 5h11v8H8l-3 3v-3H3z" fill="none" stroke="currentColor" stroke-width="1.8" '
             'stroke-linejoin="round"/><path d="M14 9h7v8h-2v3l-3-3h-5v-3" fill="none" '
             'stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>'),
}


def icon(name: str) -> str:
    return f'<svg class="ko-q-icon" viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


# ---------------------------------------------------------------- 部品


def render_fragment(config: dict, public: dict, as_of: str) -> str:
    law = config["law"]
    totals = stance_totals(public)
    check_counts(public, totals)
    phase, days = phase_of(config, as_of)
    # 本文の時制を施行後に切り替えるのは、施行後の条文を確かめてから（未確認なら施行前の書き方のまま）
    after = phase == "after_confirmed"
    opinion = int(public["opinion_count"])
    collected = int(public["collected_count"])
    period = public["collection_period"]
    issues = sorted(public["issues"], key=lambda i: (i["id"] == "koshitsu-tenpakai-other", -int(i["count"])))
    by_id = {i["id"]: i for i in public["issues"]}

    values = {
        "promulgated": ja_date(law["promulgated_on"]),
        "enforcement": ja_date(law["enforcement_on"]),
        "confirmed": ja_date(law["enforcement_confirmed_on"]) if law.get("enforcement_confirmed_on") else "",
        "days": days,
        "opinion_count": fmt(opinion),
        "collected_count": fmt(collected),
        "period_start": ja_date(period["start"]),
        "period_end": ja_date(period["end"]),
        "checked_on": ja_date(law["checked_on"]),
        "updated_on": ja_date(public["updated_on"]),
    }
    status = config["status"]
    status_text = status[phase].format(**values)
    badge = status[f"{phase}_badge"].format(**values)

    # 「何が問題？」は件数の多い順に公開JSONから決める（その他は除く）
    phrases = config["issue_phrases"]
    ranked = [i for i in issues if i["id"] in phrases][:3]
    for n, issue in enumerate(ranked, 1):
        values[f"top{n}"] = phrases[issue["id"]]
        values[f"top{n}_count"] = fmt(int(issue["count"]))

    out: list[str] = [FRAGMENT_START, '<section class="ko-open" id="koshitsu-opening" aria-labelledby="ko-title"'
                      f' data-phase="{phase}" data-as-of="{esc(as_of)}">']

    # --- 題名と短答
    h1 = "".join(f'<span class="ko-h1-line">{esc(s)}</span>' for s in config["h1"])
    sa = config["short_answer"]
    out.append('<div class="ko-hero"><div class="ko-hero-text">')
    out.append(f'<p class="ko-kicker">{esc(config["kicker"])}</p>')
    out.append(f'<h1 id="ko-title">{h1}<span class="ko-h1-sub">{esc(config["h1_sub"])}</span></h1>')
    out.append(f'<p class="ko-lead">{esc(config["lead"])}</p>')
    out.append(f'<div class="ko-status" role="note"><span class="ko-badge ko-badge-{phase}">{esc(badge)}</span>'
               f'<p>{esc(status_text)}</p></div>')
    out.append('</div><div class="ko-hero-art">' + hero_figure() + "</div></div>")

    verdict = sa["verdict_after" if after else "verdict_before"]
    out.append('<div class="ko-short" aria-labelledby="ko-short-label">')
    out.append(f'<p class="ko-short-label" id="ko-short-label">{esc(sa["label"])}</p>')
    out.append(f'<p class="ko-short-line">{esc(sa["line"])}<strong>{esc(verdict)}</strong></p>')
    out.append('<ul class="ko-terms">')
    for t in sa["terms"]:
        out.append(f'<li class="ko-term ko-term-{esc(t["this_time_kind"])}">{term_figure(t["figure"])}'
                   f'<div><p class="ko-term-name">{esc(t["term"])}</p>'
                   f'<p class="ko-term-mean">{esc(t["meaning"])}</p>'
                   f'<p class="ko-term-now"><span>今回の改正</span>{esc(t["this_time"])}</p></div></li>')
    out.append("</ul>")
    src = " ／ ".join(f'<a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["name"])}</a>'
                      for s in sa["sources"])
    out.append(f'<p class="ko-short-note">{esc(sa["note"])}出典：{src}</p>')
    out.append(f'<p class="ko-legend" aria-hidden="true"><span class="lg-m"></span>男性 <span class="lg-f"></span>女性 '
               f'<span class="lg-pat"></span>父方の線 <span class="lg-mat"></span>母方の線</p>')
    out.append("</div>")

    # --- 3つの問い
    out.append('<ol class="ko-questions">')
    for q in config["questions"]:
        if q["kind"] == "sns":
            answer = q["answer_template"].format(**values)
            detail = q["detail_template"].format(**values)
            tag = "SNSの意見"
            dated = f"SNSの集計：{values['updated_on']}まで"
        else:
            answer = q["answer_after" if after else "answer_before"]
            detail = q["detail"]
            tag = "制度の情報"
            dated = f"制度の確認日：{values['checked_on']}"
        anchor = f"#issue-{q['issue_id']}"
        out.append(f'<li class="ko-q ko-q-{esc(q["kind"])}" id="ko-q-{esc(q["id"])}">'
                   f'<p class="ko-q-tag">{icon(q["icon"])}{esc(tag)}</p>'
                   f'<h2 class="ko-q-title">{esc(q["q"])}</h2>'
                   f'<p class="ko-q-answer">{esc(answer)}</p>'
                   f'<p class="ko-q-detail">{esc(detail)}</p>'
                   f'<p class="ko-q-foot"><span>{esc(dated)}</span>'
                   f'<a href="{esc(anchor)}">{esc(q["link_label"])} →</a></p></li>')
    out.append("</ol>")

    # --- 件数
    c = config["counts"]
    colors = c["stance_colors"]
    max_count = max(int(i["count"]) for i in issues)
    out.append('<div class="ko-counts" aria-labelledby="ko-counts-title">')
    out.append(f'<div class="ko-counts-head"><h2 id="ko-counts-title">{esc(c["title"])}</h2>'
               f'<p class="ko-total"><span>SNSの意見</span><b>{fmt(opinion)}</b><span>件</span></p></div>')
    out.append('<div class="ko-counts-grid"><figure class="ko-issues">')
    out.append(f'<figcaption>{esc(c["issues_caption"].format(**values))}</figcaption><ul>')
    labels = config["issue_short_labels"]
    for issue in issues:
        n = int(issue["count"])
        other = " is-other" if issue["id"] == "koshitsu-tenpakai-other" else ""
        out.append(f'<li class="ko-issue{other}"><a href="#issue-{esc(issue["id"])}">'
                   f'<span class="ko-issue-name">{esc(labels.get(issue["id"], issue["label"]))}</span>'
                   f'<span class="ko-issue-bar"><i style="width:{n / max_count * 100:.1f}%"></i></span>'
                   f'<span class="ko-issue-n">{fmt(n)}<small>件</small></span></a></li>')
    out.append("</ul></figure>")

    groups = []
    for g in c["stance_groups"]:
        n = sum(totals.get(s, 0) for s in g["stance_ids"])
        groups.append((g, n))
    expressed = dict((g["id"], n) for g, n in groups)["expressed"]
    values["expressed"] = fmt(expressed)
    out.append('<figure class="ko-stance">')
    out.append(f'<figcaption><b>{esc(c["stance_title"].format(**values))}</b>'
               f'<span>{esc(c["stance_lead"])}</span></figcaption>')
    out.append('<div class="ko-ledger" role="img" aria-label="'
               + esc("、".join(f'{g["label"]} {fmt(n)}件' for g, n in groups)) + '">')
    for g, n in groups:
        if g["id"] == "expressed":
            inner = "".join(
                f'<i style="width:{totals.get(s, 0) / n * 100:.1f}%;background:{colors[s]}"></i>'
                for s in g["stance_ids"])
            out.append(f'<span class="ko-seg ko-seg-expressed" style="width:{pct(n, opinion)}%">{inner}</span>')
        else:
            out.append(f'<span class="ko-seg ko-seg-{esc(g["id"])}" style="width:{pct(n, opinion)}%"></span>')
    out.append("</div><dl class=\"ko-groups\">")
    for g, n in groups:
        out.append(f'<div class="ko-group ko-group-{esc(g["id"])}"><dt>{esc(g["label"])}</dt>'
                   f'<dd><b>{fmt(n)}</b>件<small>（{pct(n, opinion)}%）</small></dd></div>')
    out.append("</dl>")
    exp_group = next(g for g, _ in groups if g["id"] == "expressed")
    chips = "".join(
        f'<li><span class="sw" style="background:{colors[s]}"></span>{esc(c["stance_labels"][s])}'
        f'<b>{fmt(totals.get(s, 0))}</b>件</li>' for s in exp_group["stance_ids"])
    out.append(f'<div class="ko-expressed"><p>全体の賛否を書いた{fmt(expressed)}件の内訳</p><ul>{chips}</ul></div>')
    out.append(f'<p class="ko-unexpressed-note">{esc(c["unexpressed_note"])}</p>')
    out.append("</figure></div>")
    out.append(f'<p class="ko-basis">{esc(c["basis"].format(**values))}<strong>{esc(c["not_poll"])}</strong></p>')
    out.append("</div>")

    out.append(f'<p class="ko-dates">{esc(config["sources_line"].format(**values))}</p>')
    out.append("</section>")
    out.append(FRAGMENT_END)
    return "\n".join(out) + "\n"


def render_page(fragment: str, config: dict, as_of: str) -> str:
    title = "".join(config["h1"]) + config["h1_sub"].replace("　", "")
    return (
        "<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{esc(title)}｜冒頭の試作</title>\n"
        "<meta name=\"robots\" content=\"noindex\">\n"
        "<link rel=\"stylesheet\" href=\"opening.css\">\n</head>\n<body>\n"
        "<header class=\"ko-site\"><a href=\"#\" class=\"ko-logo\">SNS反応まっぷ</a>"
        f"<span>皇室典範改正・冒頭の試作（基準日 {esc(as_of)}）</span></header>\n"
        "<main>\n" + fragment + "</main>\n</body>\n</html>\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=CONFIG)
    ap.add_argument("--as-of", help="基準日 YYYY-MM-DD（既定は設定JSONの as_of）")
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()
    config, public = load(args.config)
    as_of = args.as_of or config["as_of"]
    date.fromisoformat(as_of)
    fragment = render_fragment(config, public, as_of)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "opening-fragment.html").write_text(fragment, encoding="utf-8")
    (args.out_dir / "index.html").write_text(render_page(fragment, config, as_of), encoding="utf-8")
    print(f"wrote {args.out_dir / 'index.html'} (phase={phase_of(config, as_of)[0]})")


if __name__ == "__main__":
    main()
