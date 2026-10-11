"""副首都ページの冒頭（題名・決まり方・短答・地図・件数）を生成する試作。

入力:
  configs/fukushuto-opening.json  冒頭の文言・短答・候補地・出典（手で直す場所はここだけ）
  docs/data/themes/fukushuto.json 件数・論点別件数・立場・更新日（公開JSON）
  configs/planet/fukushuto.yaml   立場の色と、理由の内訳がある論点（sub_issues）
  THEMES.yaml                     収集元の名前と次回の更新予定（collect_at）

出力（既定は quality/prototypes/fukushuto-opening/）:
  opening-fragment.html  冒頭の部品（マーカー付き）
  index.html             確認用の単独ページ（opening.css を読む）

時刻や乱数は使わないので、同じ入力なら何度実行しても同じ出力になる。
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "configs" / "fukushuto-opening.json"
DEFAULT_OUT = ROOT / "quality" / "prototypes" / "fukushuto-opening"
START = "<!-- FUKUSHUTO_OPENING_START -->"
END = "<!-- FUKUSHUTO_OPENING_END -->"

# 47都道府県のタイル配置（列, 行）。形は実際の地図ではなく、位置関係だけを保つ。
TILES = {
    "北海道": (11, 0), "青森": (11, 2), "秋田": (10, 3), "岩手": (11, 3), "山形": (10, 4), "宮城": (11, 4),
    "石川": (7, 5), "富山": (8, 5), "新潟": (9, 5), "福島": (10, 5),
    "福井": (7, 6), "長野": (8, 6), "群馬": (9, 6), "栃木": (10, 6), "茨城": (11, 6),
    "山口": (2, 7), "島根": (3, 7), "鳥取": (4, 7), "兵庫": (5, 7), "京都": (6, 7), "滋賀": (7, 7),
    "岐阜": (8, 7), "山梨": (9, 7), "埼玉": (10, 7), "千葉": (11, 7),
    "福岡": (1, 8), "広島": (3, 8), "岡山": (4, 8), "大阪": (5, 8), "奈良": (6, 8), "三重": (7, 8),
    "愛知": (8, 8), "静岡": (9, 8), "東京": (10, 8),
    "佐賀": (0, 9), "大分": (2, 9), "愛媛": (3, 9), "香川": (4, 9), "徳島": (5, 9), "和歌山": (6, 9), "神奈川": (10, 9),
    "長崎": (0, 10), "熊本": (1, 10), "宮崎": (2, 10), "高知": (4, 10),
    "鹿児島": (1, 11), "沖縄": (0, 12),
}
CAPITAL = "東京"
# 北海道だけ2×2マスで描く（面積の手掛かり）
WIDE = {"北海道": (2, 2)}
TILE = 34
GAP = 4


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def jp_date(iso: str, with_year: bool = True) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{d.year}年{d.month}月{d.day}日" if with_year else f"{d.month}月{d.day}日"


def read_next_collect(themes_path: Path, theme_id: str) -> tuple[str, str]:
    themes = yaml.safe_load(themes_path.read_text(encoding="utf-8"))
    entry = themes.get("themes", themes).get(theme_id)
    if not entry:
        raise SystemExit(f"{themes_path} に {theme_id} がありません")
    collect_at = entry.get("collect_at")
    return str(collect_at) if collect_at else "", str(entry.get("sample_source", ""))


def load_inputs(config_path: Path) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    paths = {key: ROOT / value for key, value in config["inputs"].items()}
    public = json.loads(paths["public_json"].read_text(encoding="utf-8"))
    planet = yaml.safe_load(paths["planet_config"].read_text(encoding="utf-8"))
    next_collect, source = read_next_collect(paths["themes_registry"], config["theme_id"])
    if public.get("theme_id") != config["theme_id"]:
        raise SystemExit("公開JSONのテーマIDが設定と一致しません")
    return {"config": config, "public": public, "planet": planet, "next_collect": next_collect, "source": source}


def step_states(steps: list[dict], checked_on: str) -> list[str]:
    """確認日を基準に、各段階を済み・現在・予定・未定に分ける。"""
    states = []
    for step in steps:
        if not step.get("date"):
            states.append("undecided")
        elif step["date"] <= checked_on:
            states.append("done")
        else:
            states.append("planned")
    done = [i for i, s in enumerate(states) if s == "done"]
    if done:
        states[done[-1]] = "current"
    return states


def render_title(config: dict) -> str:
    title = config["title"]
    phrases = "".join(
        f'<span class="fop-phrase{" fop-accent" if i == title["accent_index"] else ""}">{esc(p)}</span>'
        for i, p in enumerate(title["phrases"])
    )
    sub = "".join(f'<span class="fop-phrase">{esc(p)}</span>' for p in title["sub"])
    return f'<h1 class="fop-title">{phrases}<span class="fop-sub">{sub}</span></h1>'


def render_route(config: dict) -> str:
    steps = config["steps"]
    states = step_states(steps, config["checked_on"])
    state_label = {"done": "済み", "current": "確認日の時点", "planned": "予定", "undecided": "未定"}
    items = []
    for step, state in zip(steps, states):
        if step.get("date"):
            when = jp_date(step["date"], with_year=False)
        else:
            when = "時期は未定"
        note = step.get("note") or step["note_template"].format(date_end=jp_date(step["date_end"], with_year=False))
        src = step.get("source")
        link = (
            f'<a href="{esc(src["url"])}" target="_blank" rel="noopener noreferrer">{esc(src["label"])}</a>' if src else ""
        )
        current = ' aria-current="step"' if state == "current" else ""
        items.append(
            f'<li class="fop-stop fop-stop--{state}"{current}><span class="fop-stop__dot" aria-hidden="true"></span>'
            f'<small>{esc(when)}<span class="fop-sr">（{state_label[state]}）</span></small>'
            f"<strong>{esc(step['title'])}</strong><p>{esc(note)}{link}</p></li>"
        )
    decision = config["decision"]
    reached = max((i for i, s in enumerate(states) if s in ("done", "current")), default=0)
    progress = reached / max(len(steps) - 1, 1) * 100
    return (
        f'<section class="fop-route" id="fuk-op-route" aria-labelledby="fop-route-title">'
        f'<h2 id="fop-route-title" class="fop-route__label">{esc(decision["label"])}</h2>'
        f'<p class="fop-route__text">{esc(decision["text"])}</p>'
        f'<ol class="fop-route__line" style="--p:{progress:.0f}%">{"".join(items)}</ol>'
        f'<p class="fop-route__checked">{esc(jp_date(config["checked_on"]))}に一次資料で確認</p>'
        f"</section>"
    )


def render_map(config: dict) -> str:
    stage_of = {c["pref"]: c["stage"] for c in config["candidates"]}
    for pref in stage_of:
        if pref not in TILES:
            raise SystemExit(f"タイル配置に無い都道府県です: {pref}")
    cols = max(x + WIDE.get(n, (1, 1))[0] for n, (x, _) in TILES.items())
    rows = max(y + WIDE.get(n, (1, 1))[1] for n, (_, y) in TILES.items())
    width = cols * (TILE + GAP) - GAP
    height = rows * (TILE + GAP) - GAP
    tiles = []
    for name, (x, y) in TILES.items():
        px, py = x * (TILE + GAP), y * (TILE + GAP)
        span_x, span_y = WIDE.get(name, (1, 1))
        tw, th = span_x * (TILE + GAP) - GAP, span_y * (TILE + GAP) - GAP
        stage = stage_of.get(name)
        cls = f"fop-tile--{stage}" if stage else ("fop-tile--capital" if name == CAPITAL else "fop-tile--none")
        label = name if len(name) <= 2 or name in WIDE else name[:2]
        text = f'<text x="{px + tw / 2:g}" y="{py + th / 2 + 4:g}">{esc(label)}</text>' if (stage or name == CAPITAL) else ""
        title = f"<title>{esc(name)}</title>" if (stage or name == CAPITAL) else ""
        tiles.append(f'<g class="fop-tile {cls}">{title}<rect x="{px}" y="{py}" width="{tw}" height="{th}" rx="6"/>{text}</g>')
    m = config["map"]
    stages = config["stages"]
    counts = {s["key"]: sum(c["stage"] == s["key"] for c in config["candidates"]) for s in stages}
    legend = "".join(
        f'<li><span class="fop-key fop-key--{esc(s["key"])}" aria-hidden="true"></span>{esc(s["label"])}<b>{counts[s["key"]]}</b></li>'
        for s in stages
    )
    legend += f'<li><span class="fop-key fop-key--capital" aria-hidden="true"></span>{esc(m["capital_label"])}</li>'
    rows_html = "".join(
        f'<li class="fop-region fop-region--{esc(c["stage"])}"><span class="fop-key fop-key--{esc(c["stage"])}" aria-hidden="true"></span>'
        f'<strong>{esc(c["name"])}</strong><span class="fop-region__label">{esc(c["label"])}</span>'
        f'<a href="{esc(c["url"])}" target="_blank" rel="noopener noreferrer"><time datetime="{esc(c["date"])}">{esc(jp_date(c["date"]))}</time>・{esc(c["source"])}の資料</a></li>'
        for c in config["candidates"]
    )
    aria = f"都道府県のタイル地図。自治体が動きを公表した{len(config['candidates'])}地域を色分けしています"
    return (
        f'<section class="fop-map" id="fuk-op-map" aria-labelledby="fop-map-title">'
        f'<header class="fop-map__head"><h2 id="fop-map-title">{esc(m["title"])}</h2>'
        f'<p class="fop-seal"><span>{esc(m["national_label"])}</span><strong>{m["national_count"]}</strong><small>{esc(m["national_unit"])}</small></p></header>'
        f'<svg class="fop-map__svg" viewBox="-2 -2 {width + 4} {height + 4}" role="img" aria-label="{esc(aria)}">{"".join(tiles)}</svg>'
        f'<ul class="fop-legend">{legend}</ul>'
        f'<details class="fop-regions"><summary>{len(config["candidates"])}地域の資料と日付</summary><ul>{rows_html}</ul></details>'
        f'<p class="fop-map__note">{esc(m["note"])}</p>'
        f"</section>"
    )


def render_answers(config: dict, public: dict) -> str:
    steps = {s["key"]: s for s in config["steps"]}
    counts = {s["key"]: sum(c["stage"] == s["key"] for c in config["candidates"]) for s in config["stages"]}
    top = sorted((i for i in public["issues"] if i.get("kind") != "other"), key=lambda i: -i["count"])[:3]
    values = {
        "regions": len(config["candidates"]),
        "aiming": counts["aiming"],
        "considering": counts["considering"],
        "draft_date": jp_date(steps["draft"]["date"]),
        "draft_end": jp_date(steps["draft"]["date_end"], with_year=False),
        "enforce_date": jp_date(steps["enforce"]["date"]),
        "top_issues": "、".join(f"{i['label']}（{i['count']:,}件）" for i in top),
    }
    cards = []
    for a in config["answers"]:
        cards.append(
            f'<article class="fop-answer fop-answer--{esc(a["kind"])}">'
            f'<span class="fop-answer__kind">{esc(a["kind_label"])}</span>'
            f'<h2>{icon(a["key"])}{esc(a["question"])}</h2>'
            f'<p class="fop-answer__short">{esc(a["short"])}</p>'
            f'<p>{esc(a["body_template"].format(**values))}</p>'
            f'<a href="{esc(a["link"]["href"])}">{esc(a["link"]["text"])}</a></article>'
        )
    return f'<section class="fop-answers" aria-label="検索で多い疑問に短く答える">{"".join(cards)}</section>'


def icon(key: str) -> str:
    paths = {
        "where": '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11Z"/><circle cx="12" cy="10" r="2.5"/>',
        "when": '<path d="M4 12h3l2-5 3 10 2-5h6"/><circle cx="4" cy="12" r="1.5"/><circle cx="20" cy="12" r="1.5"/>',
        "merit": '<path d="M12 4v16M5 8h14M5 8l-3 6h6ZM19 8l-3 6h6Z"/>',
    }
    return (
        '<svg class="fop-picto" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{paths[key]}</svg>'
    )


def render_count(config: dict, public: dict, planet: dict, source: str, next_collect: str) -> str:
    c = config["count"]
    total = public["opinion_count"]
    stance_order = [s["id"] for s in planet["stances"]]
    color = {s["id"]: s["color"] for s in planet["stances"]}
    label = {s["id"]: s["label"] for s in planet["stances"]}
    stance_totals = {sid: 0 for sid in stance_order}
    for issue in public["issues"]:
        for s in issue["stances"]:
            stance_totals[s["id"]] += s["count"]
    if sum(stance_totals.values()) != total:
        raise SystemExit("立場の合計が意見件数と一致しません")
    # 多い順に並べる（現在は 反対・賛成・中立）
    ordered = sorted(stance_order, key=lambda sid: -stance_totals[sid])
    segs = "".join(
        f'<span class="fop-stance__seg" style="--w:{stance_totals[sid] / total * 100:.2f}%;--c:{color[sid]}"></span>' for sid in ordered
    )
    stance_items = "".join(
        f'<li><span class="fop-key" style="--c:{color[sid]}" aria-hidden="true"></span>{esc(label[sid])}'
        f"<b>{round(stance_totals[sid] / total * 100)}%</b><small>{stance_totals[sid]:,}件</small></li>"
        for sid in ordered
    )
    with_reason = set(planet.get("sub_issues", {}).keys())
    issues = sorted(public["issues"], key=lambda i: (i.get("kind") == "other", -i["count"]))
    top = max(i["count"] for i in issues)
    issue_rows = []
    missing = []
    for issue in issues:
        has_reason = issue["label"] in with_reason
        if not has_reason:
            missing.append(issue["label"])
        tag = "" if has_reason else f'<em class="fop-tag">{esc(c["no_reason_tag"])}</em>'
        issue_rows.append(
            f'<li class="fop-issue{" fop-issue--other" if issue.get("kind") == "other" else ""}"><span class="fop-issue__name">{esc(issue["label"])}{tag}</span>'
            f'<span class="fop-issue__bar" style="--w:{issue["count"] / top * 100:.2f}%" aria-hidden="true"></span>'
            f'<b>{issue["count"]:,}<small>件</small></b></li>'
        )
    if sum(i["count"] for i in issues) != total:
        raise SystemExit("論点別件数の合計が意見件数と一致しません")
    period = public["collection_period"]
    caption = c["caption_template"].format(
        source=source,
        collected=f"{public['collected_count']:,}",
        start=jp_date(period["start"]),
        end=jp_date(period["end"], with_year=False),
    )
    note = c["no_reason_note_template"].format(labels="と".join(f"「{m}」" for m in missing)) if missing else ""
    updated = c["updated_template"].format(
        updated=jp_date(public["updated_on"]),
        next=jp_date(next_collect, with_year=False) if next_collect else "未定",
    )
    return (
        f'<section class="fop-count" id="fuk-op-count" aria-labelledby="fop-count-title">'
        f'<div class="fop-count__total"><h2 id="fop-count-title">{esc(c["label"])}</h2>'
        f'<p class="fop-count__num" aria-label="{total:,}件"><strong>{total:,}</strong><span>件</span></p>'
        f'<p class="fop-count__caption">{esc(caption)}</p>'
        f'<div class="fop-stance" aria-hidden="true">{segs}</div><ul class="fop-stance__list">{stance_items}</ul>'
        f'<p class="fop-count__poll">{esc(c["not_poll"])}</p></div>'
        f'<div class="fop-count__issues"><h3>{esc(c["issues_title"])}</h3><ol class="fop-issues">{"".join(issue_rows)}</ol>'
        f'<p class="fop-count__note">{esc(note)}</p><p class="fop-count__updated">{esc(updated)}</p></div>'
        f"</section>"
    )


def render_fragment(data: dict) -> str:
    config, public = data["config"], data["public"]
    crumb = " ／ ".join(esc(c) for c in config["crumb"])
    sources = "".join(
        f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["label"])}</a>' for s in config["sources"]
    )
    return "\n".join(
        [
            START,
            '<section class="fop" aria-label="副首都の冒頭">',
            '<div class="fop-hero">',
            f'<div class="fop-hero__copy"><p class="fop-crumb">{crumb}</p>{render_title(config)}',
            f'<p class="fop-lead">{esc(config["lead"])}</p>{render_route(config)}</div>',
            render_map(config),
            "</div>",
            render_answers(config, public),
            render_count(config, public, data["planet"], data["source"], data["next_collect"]),
            f'<p class="fop-sources">{sources}</p>',
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
<title>副首都 冒頭試作</title>
<meta name="robots" content="noindex">
<link rel="stylesheet" href="opening.css">
</head>
<body>
<main class="fop-page">
{fragment}</main>
</body>
</html>
"""


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
    print(f"wrote {args.out_dir / 'opening-fragment.html'}")
    print(f"wrote {args.out_dir / 'index.html'}")


if __name__ == "__main__":
    main()
