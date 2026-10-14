"""消費税減税ページの冒頭（題名・段階の一言・短答3つ・レシート・段階図・件数）を生成する試作。

入力:
  configs/consumption-tax-cut-opening.json  冒頭の文言・短答・法律の段階と日付・税率と対象品目・出典（手で直す場所はここだけ）
  docs/data/themes/consumption-tax-cut.json 件数・論点別件数・立場・収集期間・更新日（公開JSON）
  configs/planet/consumption-tax-cut.yaml   立場の色と並び、理由の内訳がある論点（sub_issues）
  THEMES.yaml                               収集元の名前と次回の更新予定（collect_at）

出力（既定は quality/prototypes/consumption-tax-cut-opening/）:
  opening-fragment.html  冒頭の部品（マーカー付き）
  index.html             確認用の単独ページ（同じフォルダーの opening.css と opening.js を読む）
  opening.css / opening.js  正本 scripts/consumption_tax_redesign/ の写し

段階は「今日」ではなく基準日で決める。基準日の既定は公開JSONの updated_on で、--as-of で上書きできる。
  bill       法律案が国会で審議中（law.enacted_on が null か、基準日より後）
  enacted    成立して、引下げ開始（law.start_on）の前
  in_effect  引下げ中（start_on〜end_on）
  ended      引下げ終了（end_on の翌日以降）
  overdue    成立を確かめないまま、引下げ開始の予定日を過ぎた
日付を過ぎても生成は止めない。日付の順番が崩れている、確認日より後の成立日が入っている、
税率の国税＋地方が合計と合わない、件数の合計が公開JSONと合わない、といった組み合わせだけ止める。

時刻や乱数は使わないので、同じ入力なら何度実行しても同じ出力になる。
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import shutil
from decimal import Decimal
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "configs" / "consumption-tax-cut-opening.json"
DEFAULT_OUT = ROOT / "quality" / "prototypes" / "consumption-tax-cut-opening"
ASSETS = ROOT / "scripts" / "consumption_tax_redesign"
START = "<!-- CONSUMPTION_TAX_OPENING_START -->"
END = "<!-- CONSUMPTION_TAX_OPENING_END -->"
PHASES = ("bill", "enacted", "in_effect", "ended", "overdue")


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def jp_date(iso: str, with_year: bool = True) -> str:
    d = dt.date.fromisoformat(str(iso))
    return f"{d.year}年{d.month}月{d.day}日" if with_year else f"{d.month}月{d.day}日"


def jp_month(iso: str) -> str:
    d = dt.date.fromisoformat(str(iso))
    return f"{d.year}年{d.month}月"


def link(url: str, label: str) -> str:
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'


def lookup(config: dict, dotted: str | None):
    """"law.start_on" のような参照を設定から引く。"""
    if not dotted:
        return None
    node = config
    for part in dotted.split("."):
        node = node[part]
    return node


# ---- 入力と検査 ---------------------------------------------------------------

def check_config(config: dict, public: dict) -> None:
    law = config["law"]
    order = ["outline_on", "bill_on", "transition_on", "start_on", "end_on"]
    days = [dt.date.fromisoformat(law[k]) for k in order]
    if days != sorted(days) or len(set(days)) != len(days):
        raise SystemExit("law の日付の順番が崩れています（大綱→法律案→予約販売の区切り→引下げ開始→終了）")
    checked = dt.date.fromisoformat(config["checked_on"])
    if checked < dt.date.fromisoformat(law["bill_on"]):
        raise SystemExit("checked_on が法律案の提出日より前です")
    if checked < dt.date.fromisoformat(public["claim_verification"]["checked_on"]):
        raise SystemExit("制度の確認日 checked_on が、主張の照合日より古くなっています")
    enacted, promulgated = law.get("enacted_on"), law.get("promulgated_on")
    if enacted:
        if enacted < law["bill_on"]:
            raise SystemExit("law.enacted_on が法律案の提出日より前です")
        if enacted > config["checked_on"]:
            raise SystemExit("law.enacted_on が確認日 checked_on より後です（成立を確かめた日に checked_on を直してください）")
    if promulgated and (not enacted or promulgated < enacted):
        raise SystemExit("law.promulgated_on は成立日（law.enacted_on）以後の日付だけ入れられます")
    for key, rate in config["rates"].items():
        if key.startswith("_"):
            continue
        if Decimal(rate["national"]) + Decimal(rate["local"]) != Decimal(rate["total"]):
            raise SystemExit(f"税率 {key} の国税＋地方が合計と合いません")
    for item in config["calc"]["items"]:
        for side in ("before", "after"):
            if item[side] not in config["rates"]:
                raise SystemExit(f"calc.items の {item['key']} が未定義の税率 {item[side]} を指しています")


def load_inputs(config_path: Path) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    paths = {key: ROOT / value for key, value in config["inputs"].items()}
    public = json.loads(paths["public_json"].read_text(encoding="utf-8"))
    planet = yaml.safe_load(paths["planet_config"].read_text(encoding="utf-8"))
    themes = yaml.safe_load(paths["themes_registry"].read_text(encoding="utf-8"))
    entry = themes.get("themes", themes).get(config["theme_id"])
    if not entry:
        raise SystemExit(f"THEMES.yaml に {config['theme_id']} がありません")
    if public.get("theme_id") != config["theme_id"]:
        raise SystemExit("公開JSONのテーマIDが設定と一致しません")
    check_config(config, public)
    return {
        "config": config,
        "public": public,
        "planet": planet,
        "source": str(entry.get("sample_source", "")),
        "next_collect": str(entry["collect_at"]) if entry.get("collect_at") else "",
    }


# ---- 段階 ---------------------------------------------------------------------

def enacted_by(config: dict, as_of: str) -> bool:
    enacted = config["law"].get("enacted_on")
    return bool(enacted) and enacted <= as_of


def phase_of(config: dict, as_of: str) -> str:
    dt.date.fromisoformat(as_of)
    law = config["law"]
    if as_of < law["bill_on"]:
        raise SystemExit("基準日が法律案の提出日より前です（この冒頭は提出後の段階だけを扱います）")
    if not enacted_by(config, as_of):
        return "overdue" if as_of >= law["start_on"] else "bill"
    if as_of < law["start_on"]:
        return "enacted"
    if as_of <= law["end_on"]:
        return "in_effect"
    return "ended"


def values_for(config: dict, as_of: str) -> dict:
    law = config["law"]
    phase = phase_of(config, as_of)
    return {
        "checked": jp_date(config["checked_on"]),
        "as_of": jp_date(as_of),
        "bill": jp_date(law["bill_on"]),
        "enacted": jp_date(law["enacted_on"]) if law.get("enacted_on") else "",
        "promulgated": jp_date(law["promulgated_on"]) if law.get("promulgated_on") else "",
        "start": jp_date(law["start_on"]),
        "end": jp_date(law["end_on"]),
        "start_ym": jp_month(law["start_on"]),
        "end_ym": jp_month(law["end_on"]),
        "diet": law["diet_session"],
        "law_word": config["phase_text"]["law_word"][phase],
        "base": f"{config['calc']['base_price']:,}",
    }


def by_phase(text: dict, phase: str) -> str:
    """phase ごとの文言（無ければ all）。"""
    return text[phase] if phase in text else text["all"]


def step_states(config: dict, as_of: str) -> list[str]:
    """基準日で各段階を 済み・現在・予定（法律案の日付）・未定・未確認 に分ける。"""
    enacted = enacted_by(config, as_of)
    states = []
    for step in config["steps"]["items"]:
        date = lookup(config, step.get("date_from"))
        if step["key"] == "enact":
            states.append("done" if enacted else "undecided")
        elif not date:
            states.append("undecided")
        elif date <= as_of:
            states.append("unconfirmed" if step.get("law_dependent") and not enacted else "done")
        else:
            states.append("planned_bill" if step.get("law_dependent") and not enacted else "planned")
    done = [i for i, s in enumerate(states) if s == "done"]
    if done:
        states[done[-1]] = "current"
    return states


# ---- 部品 ---------------------------------------------------------------------

def render_title(config: dict) -> str:
    title = config["title"]
    accents = set(title.get("accent_indices", []))
    phrases = "".join(
        f'<span class="cto-phrase{" cto-accent" if i in accents else ""}">{esc(p)}</span>'
        for i, p in enumerate(title["phrases"])
    )
    sub = "".join(f'<span class="cto-phrase">{esc(p)}</span>' for p in title["sub"])
    return f'<h1 class="cto-title">{phrases}<span class="cto-sub">{sub}</span></h1>'


def render_status(config: dict, as_of: str) -> str:
    phase = phase_of(config, as_of)
    pt = config["phase_text"]
    text = pt["status"][phase].format(**values_for(config, as_of))
    return (
        f'<p class="cto-status cto-status--{phase}"><b>{esc(pt["status_label"][phase])}</b>'
        f"<span>{esc(text)}</span></p>"
    )


def icon(key: str) -> str:
    paths = {
        # カレンダーに矢印（いつから・いつまで）
        "when": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4M8 15h8M13 12l3 3-3 3"/>',
        # 硬貨と手（税率＋給付）
        "mechanism": '<circle cx="15" cy="8" r="4.5"/><path d="M15 6v4M2 16h4l3 2h6a2 2 0 0 0 0-4h-4M6 21H2"/>',
        # 買い物かご（対象品目）
        "items": '<path d="M3 9h18l-2 11H5Z"/><path d="M8 9l3-5M16 9l-3-5M9 13v4M15 13v4"/>',
    }
    return (
        '<svg class="cto-picto" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{paths[key]}</svg>'
    )


def render_answers(config: dict, as_of: str) -> str:
    phase = phase_of(config, as_of)
    values = values_for(config, as_of)
    cards = []
    for i, a in enumerate(config["answers"], 1):
        short = by_phase(a["short"], phase).format(**values)
        body = by_phase(a["body"], phase).format(**values)
        cards.append(
            f'<article class="cto-answer" aria-labelledby="cto-q{i}">'
            f'<p class="cto-answer__kind"><span>Q{i}</span>{esc(a["kind_label"])}</p>'
            f'<h2 id="cto-q{i}">{icon(a["key"])}{esc(a["question"])}</h2>'
            f'<p class="cto-answer__short">{esc(short)}</p>'
            f'<p class="cto-answer__body">{esc(body)}</p>'
            f'<a class="cto-answer__link" href="{esc(a["link"]["href"])}">{esc(a["link"]["text"])}</a></article>'
        )
    return f'<div class="cto-answers" aria-label="検索で多い3つの疑問への短い答え">{"".join(cards)}</div>'


def price(base: int, rate_total: str) -> int:
    value = Decimal(base) * (Decimal(100) + Decimal(rate_total)) / Decimal(100)
    if value != value.to_integral_value():
        raise SystemExit(f"税込額が整数になりません（税率 {rate_total}%）")
    return int(value)


def calc_rows(config: dict) -> list[dict]:
    c, rates = config["calc"], config["rates"]
    rows = []
    for item in c["items"]:
        before, after = rates[item["before"]], rates[item["after"]]
        b, a = price(c["base_price"], before["total"]), price(c["base_price"], after["total"])
        rows.append(
            {
                "key": item["key"],
                "label": item["label"],
                "tag": item["tag"],
                "note": item["note"],
                "before_rate": before["total"],
                "after_rate": after["total"],
                "before_name": before["label"],
                "after_name": after["label"],
                "after_special": item["after"] == "special",
                "before_price": f"{b:,}円",
                "after_price": f"{a:,}円",
                "delta": f"−{b - a:,}円" if b > a else "±0円",
            }
        )
    return rows


def render_calc(config: dict, as_of: str) -> str:
    """レシートの計算部品。JSなしでは全品目の表を出し、JSがあれば買い方を選ぶタブに切り替える。
    税率と税込額はここで計算して埋め込むので、JSは文字を差し替えるだけ（税率を持たない）。"""
    phase = phase_of(config, as_of)
    values = values_for(config, as_of)
    c = config["calc"]
    special = config["rates"]["special"]
    rows = calc_rows(config)
    before_label = c["before_label"][phase].format(**values)
    after_label = c["after_label"][phase].format(**values)
    base = values["base"]
    first = rows[0]

    tabs = "".join(
        f'<button type="button" role="tab" id="cto-tab-{esc(r["key"])}" aria-controls="cto-receipt" '
        f'aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}" data-cto-item="{esc(r["key"])}">'
        f'<small>{esc(r["tag"])}</small>{esc(r["label"])}</button>'
        for i, r in enumerate(rows)
    )
    static_rows = "".join(
        f'<tr><th scope="row">{esc(r["label"])}</th><td>{esc(r["before_rate"])}%</td>'
        f'<td class="{"cto-down" if r["after_special"] else ""}">{esc(r["after_rate"])}%</td>'
        f'<td>{esc(r["before_price"])} → {esc(r["after_price"])}</td></tr>'
        for r in rows
    )
    data = json.dumps(
        {r["key"]: {k: r[k] for k in ("before_rate", "after_rate", "before_name", "after_name", "before_price",
                                     "after_price", "delta", "note", "after_special")} for r in rows},
        ensure_ascii=False,
        sort_keys=True,
    ).replace("</", "<\\/")
    rate_note = c["rate_note"].format(national=special["national"], local=special["local"])
    return (
        f'<section class="cto-calc" id="cto-calc" aria-labelledby="cto-calc-title" data-cto-calc>'
        f'<h2 id="cto-calc-title" class="cto-calc__title">{esc(c["title"][phase])}</h2>'
        f'<p class="cto-calc__intro">{esc(c["intro"].format(**values))}</p>'
        f'<div class="cto-keys" role="tablist" aria-label="買い方を選ぶ" hidden>{tabs}</div>'
        f'<div class="cto-receipt" id="cto-receipt" role="tabpanel" aria-labelledby="cto-tab-{esc(first["key"])}" hidden>'
        f'<p class="cto-receipt__head">税抜<b>{esc(base)}円</b>の場合</p>'
        f'<dl class="cto-receipt__lines">'
        f'<div><dt>{esc(before_label)}<small data-cto="before_name">{esc(first["before_name"])}</small></dt>'
        f'<dd><b data-cto="before_rate">{esc(first["before_rate"])}%</b><span data-cto="before_price">{esc(first["before_price"])}</span></dd></div>'
        f'<div class="cto-receipt__after"><dt>{esc(after_label)}<small data-cto="after_name">{esc(first["after_name"])}</small></dt>'
        f'<dd><b data-cto="after_rate">{esc(first["after_rate"])}%</b><span data-cto="after_price">{esc(first["after_price"])}</span></dd></div>'
        f'</dl>'
        f'<p class="cto-receipt__delta">差額<b data-cto="delta">{esc(first["delta"])}</b></p>'
        f'<p class="cto-receipt__note" data-cto="note" aria-live="polite">{esc(first["note"])}</p>'
        f"</div>"
        f'<table class="cto-calc__table" data-cto-static><caption>{esc(c["static_caption"].format(**values))}</caption>'
        f'<thead><tr><th scope="col">買い方</th><th scope="col">{esc(before_label)}</th><th scope="col">{esc(after_label)}</th>'
        f'<th scope="col">税込額</th></tr></thead><tbody>{static_rows}</tbody></table>'
        f'<p class="cto-calc__rate">{esc(rate_note)}</p>'
        f'<p class="cto-calc__caution">{esc(c["caution"])}</p>'
        f'<script type="application/json" id="cto-calc-data">{data}</script>'
        f"</section>"
    )


def position(config: dict, iso: str) -> float:
    axis = config["steps"]["axis"]
    start, end = dt.date.fromisoformat(axis["from"]), dt.date.fromisoformat(axis["to"])
    day = min(max(dt.date.fromisoformat(iso), start), end)
    return (day - start).days / (end - start).days * 100


def render_band(config: dict, as_of: str) -> str:
    """時間に比例した帯。1%の期間を塗り、各段階の日付に印、基準日に縦線を置く。"""
    law, axis = config["law"], config["steps"]["axis"]
    first_year = dt.date.fromisoformat(axis["from"]).year + 1
    last_year = dt.date.fromisoformat(axis["to"]).year
    ticks = "".join(
        f'<span class="cto-band__tick" style="--x:{position(config, f"{y}-01-01"):.2f}%">{y}年</span>'
        for y in range(first_year, last_year + 1)
    )
    marks = "".join(
        f'<span class="cto-band__mark" style="--x:{position(config, lookup(config, s["date_from"])):.2f}%"></span>'
        for s in config["steps"]["items"]
        if lookup(config, s.get("date_from"))
    )
    left, right = position(config, law["start_on"]), position(config, law["end_on"])
    now = position(config, as_of)
    pending = "" if enacted_by(config, as_of) else " cto-band__period--pending"
    return (
        f'<div class="cto-band" aria-hidden="true">'
        f'<div class="cto-band__track">{marks}'
        f'<span class="cto-band__period{pending}" style="--l:{left:.2f}%;--r:{100 - right:.2f}%">'
        f'<b>{esc(config["steps"]["band_label"])}</b></span>'
        f'<span class="cto-band__now{" cto-band__now--right" if now > 50 else ""}" style="--x:{now:.2f}%"><i>{esc(jp_date(as_of, with_year=False))}</i></span></div>'
        f'<div class="cto-band__ticks">{ticks}</div></div>'
    )


def render_steps(config: dict, as_of: str) -> str:
    s = config["steps"]
    values = values_for(config, as_of)
    labels = config["phase_text"]["state_labels"]
    states = step_states(config, as_of)
    items = []
    for step, state in zip(s["items"], states):
        date = lookup(config, step.get("date_from"))
        shown = date if (date and (step["key"] != "enact" or state != "undecided")) else None
        when = jp_date(shown) if shown else "日付は未定"
        if step["key"] == "enact":
            if state == "undecided":
                note = step["note_undecided"]
            elif config["law"].get("promulgated_on") and config["law"]["promulgated_on"] <= as_of:
                note = step["note_promulgated"].format(**values)
            else:
                note = step["note_done"]
        else:
            note = step["note"].format(**values)
        src = step.get("source")
        src_html = link(src["url"], src["label"]) if src else ""
        current = ' aria-current="step"' if state == "current" else ""
        items.append(
            f'<li class="cto-step cto-step--{state}"{current}>'
            f'<span class="cto-step__box" aria-hidden="true"></span>'
            f'<time{f" datetime={chr(34)}{esc(shown)}{chr(34)}" if shown else ""}>{esc(when)}</time>'
            f'<strong>{esc(step["title"])}</strong>'
            f'<em class="cto-step__state">{esc(labels[state].format(**values))}</em>'
            f'<p>{esc(note)}{src_html}</p></li>'
        )
    checked = config["phase_text"]["checked_line"].format(**values)
    return (
        f'<section class="cto-steps" id="cto-steps" aria-labelledby="cto-steps-title">'
        f'<h2 id="cto-steps-title" class="cto-steps__label">{esc(s["label"])}</h2>'
        f'<p class="cto-steps__text">{esc(by_phase(s["text"], phase_of(config, as_of)))}</p>'
        f"{render_band(config, as_of)}"
        f'<ol class="cto-steps__list">{"".join(items)}</ol>'
        f'<p class="cto-steps__checked" data-checked-on="{esc(config["checked_on"])}">{esc(checked)}</p>'
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
        f'<li><span class="cto-key" style="--c:{color[sid]}" aria-hidden="true"></span>{esc(label[sid])}'
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
            tag = f'<em class="cto-flag">{esc(c["no_reason_tag"])}</em>'
        rows.append(
            f'<li class="cto-issue{" cto-issue--other" if issue.get("kind") == "other" else ""}">'
            f'<span class="cto-issue__name">{esc(issue["label"])}{tag}</span>'
            f'<span class="cto-issue__bar" aria-hidden="true"><i style="--w:{issue["count"] / top * 100:.2f}%"></i></span>'
            f'<b>{issue["count"]:,}<small>件</small></b></li>'
        )
    note = (
        c["no_reason_note_template"].format(labels="".join(f"「{m}」" for m in missing), n=len(missing)) if missing else ""
    )

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
        f'<section class="cto-count" id="cto-count" aria-labelledby="cto-count-title">'
        f'<div class="cto-count__total"><h2 id="cto-count-title">{esc(c["label"])}</h2>'
        f'<p class="cto-count__num"><strong>{total:,}</strong><span>件</span></p>'
        f'<p class="cto-count__poll">{esc(c["not_poll"])}</p>'
        f'<p class="cto-count__caption">{esc(caption)}</p>'
        f'<h3 class="cto-count__sub">{esc(c["stance_title"])}</h3>'
        f'<div class="cto-stance" aria-hidden="true">{segs}</div><ul class="cto-stance__list">{stance_items}</ul></div>'
        f'<div class="cto-count__issues"><h3 class="cto-count__sub">{esc(c["issues_title_template"].format(n=len(issues)))}</h3>'
        f'<ol class="cto-issues">{"".join(rows)}</ol>'
        + (f'<p class="cto-count__note">{esc(note)}</p>' if note else "")
        + f'<p class="cto-count__updated">{esc(updated)}</p></div>'
        f"</section>"
    )


def default_as_of(data: dict) -> str:
    """基準日の既定は公開JSONの更新日（今日の日付は使わない）。"""
    return data["public"]["updated_on"]


def render_fragment(data: dict, as_of: str | None = None) -> str:
    config = data["config"]
    as_of = as_of or default_as_of(data)
    phase = phase_of(config, as_of)
    crumb = " ／ ".join(esc(c) for c in config["crumb"])
    sources = "".join(f"<li>{link(s['url'], s['label'])}</li>" for s in config["sources"])
    return "\n".join(
        [
            START,
            f'<section class="cto" aria-label="消費税減税の冒頭" data-as-of="{esc(as_of)}" data-phase="{phase}">',
            '<div class="cto-top">',
            f'<header class="cto-hero"><p class="cto-crumb">{crumb}</p>{render_title(config)}'
            f'<p class="cto-lead">{esc(config["lead"])}</p>{render_status(config, as_of)}</header>',
            render_answers(config, as_of),
            render_calc(config, as_of),
            "</div>",
            render_steps(config, as_of),
            render_count(data),
            f'<aside class="cto-sources"><h2>{esc(config["sources_title"])}</h2><ul>{sources}</ul></aside>',
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
<title>消費税減税 冒頭試作</title>
<meta name="robots" content="noindex">
<link rel="stylesheet" href="opening.css">
<script src="opening.js" defer></script>
</head>
<body>
<main class="cto-page">
{fragment}</main>
</body>
</html>
"""


def fragment_for(config_path: Path = DEFAULT_CONFIG, as_of: str | None = None) -> str:
    """冒頭の部品（マーカー付き）。読書面の試作がこの下に読書面をつなぐ想定。"""
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
    for name in ("opening.css", "opening.js"):
        shutil.copyfile(ASSETS / name, args.out_dir / name)
    print(f"wrote {args.out_dir / 'opening-fragment.html'}")
    print(f"wrote {args.out_dir / 'index.html'}")


if __name__ == "__main__":
    main()
