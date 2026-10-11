"""高齢者免許返納ページの冒頭（題名・短答・年齢のものさし・返納後の流れ・件数）を生成する試作。

入力:
  configs/elderly-license-revocation-opening.json  冒頭の文言・短答・FAQ・出典（手で直す場所はここだけ）
  docs/data/themes/elderly-license-revocation.json  件数・論点別件数・立場・収集期間・更新日・照合日（公開JSON）
  configs/planet/elderly-license-revocation.yaml    立場の色と、理由の内訳がある論点（sub_issues）
  THEMES.yaml                                       収集元の名前と次回の収集予定（collect_at）

出力（既定は quality/prototypes/elderly-license-revocation-opening/）:
  opening-fragment.html  冒頭の部品（マーカー付き）
  index.html             確認用の単独ページ（同じフォルダーの opening.css を読む）

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
DEFAULT_CONFIG = ROOT / "configs" / "elderly-license-revocation-opening.json"
DEFAULT_OUT = ROOT / "quality" / "prototypes" / "elderly-license-revocation-opening"
START = "<!-- ELDERLY_OPENING_START -->"
END = "<!-- ELDERLY_OPENING_END -->"

# ピクトグラム（24×24、線画）。色は currentColor。
PICTOS = {
    # 相談（受話器と吹き出し）
    "any": '<path d="M5 4h4l1.5 4-2 1.5a10 10 0 0 0 5 5l1.5-2 4 1.5v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2Z"/>',
    # 講習（黒板と人）
    "70": '<rect x="3" y="4" width="13" height="9" rx="1"/><path d="M6 8h7M6 10.5h4"/><circle cx="19" cy="9" r="2"/><path d="M15.5 20a3.5 3.5 0 0 1 7 0"/>',
    # 検査（チェック表）
    "75": '<rect x="5" y="3.5" width="14" height="17" rx="2"/><path d="M9 3.5h6v3H9z"/><path d="m8.5 12 2 2 4-4M8.5 17h7"/>',
    # 返納（免許証と戻す矢印）
    "return": '<rect x="2.5" y="6" width="13" height="9" rx="1.5"/><path d="M5.5 9.5h4M5.5 12h6"/><path d="M21.5 10.5v4a3 3 0 0 1-3 3h-6m0 0 2.5-2.5M12.5 17.5 15 20"/>',
    # 運転経歴証明書（顔写真入りのカード）
    "card": '<rect x="2.5" y="5" width="19" height="14" rx="2"/><circle cx="8" cy="11" r="2"/><path d="M5 16a3 3 0 0 1 6 0M14 10h4.5M14 13h4.5"/>',
    # 割引・支援（バス）
    "perk": '<rect x="4" y="3.5" width="16" height="14" rx="3"/><path d="M4 11h16M8 21v-3.5M16 21v-3.5"/><circle cx="8" cy="14.5" r="1"/><circle cx="16" cy="14.5" r="1"/>',
    # 短答: 年齢（ものさし）
    "age": '<rect x="2.5" y="8" width="19" height="8" rx="1.5"/><path d="M6 8v3.5M9.5 8v2M13 8v3.5M16.5 8v2M20 8v3.5"/>',
    # 短答: 切り出す（2つの吹き出し）
    "talk": '<path d="M3 5h11v7H8l-3 3v-3H3z"/><path d="M14 9h7v7h-2v3l-3-3h-5v-3"/>',
    # 短答: 返納後（カード）
    "after": '<rect x="2.5" y="5" width="19" height="14" rx="2"/><circle cx="8" cy="11" r="2"/><path d="M5 16a3 3 0 0 1 6 0M14 10h4.5M14 13h4.5"/>',
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def picto(key: str, cls: str = "elo-picto") -> str:
    return (
        f'<svg class="{cls}" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{PICTOS[key]}</svg>'
    )


def jp_date(iso: str, with_year: bool = True) -> str:
    d = dt.date.fromisoformat(str(iso))
    return f"{d.year}年{d.month}月{d.day}日" if with_year else f"{d.month}月{d.day}日"


def link(href: str, text: str) -> str:
    external = href.startswith("http")
    attrs = ' target="_blank" rel="noopener noreferrer"' if external else ""
    return f'<a href="{esc(href)}"{attrs}>{esc(text)}</a>'


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
    return {
        "config": config,
        "public": public,
        "planet": planet,
        "source": str(entry.get("sample_source", "")),
        "next_collect": str(entry.get("collect_at") or ""),
    }


def render_title(config: dict) -> str:
    title = config["title"]
    phrases = "".join(
        f'<span class="elo-phrase{" elo-accent" if i == title["accent_index"] else ""}">{esc(p)}</span>'
        for i, p in enumerate(title["phrases"])
    )
    sub = "".join(f'<span class="elo-phrase">{esc(p)}</span>' for p in title["sub"])
    return f'<h1 class="elo-title">{phrases}<span class="elo-sub">{sub}</span></h1>'


def render_answers(config: dict) -> str:
    cards = []
    for a in config["answers"]:
        cards.append(
            f'<article class="elo-answer elo-answer--{esc(a["key"])}">'
            f'<span class="elo-answer__kind">{esc(a["kind_label"])}</span>'
            f'<h2>{picto(a["key"])}{esc(a["question"])}</h2>'
            f'<p class="elo-answer__short">{esc(a["short"])}</p>'
            f'<p>{esc(a["body"])}</p>{link(a["link"]["href"], a["link"]["text"])}</article>'
        )
    return f'<section class="elo-answers" aria-label="検索で多い疑問に短く答える">{"".join(cards)}</section>'


def render_ages(config: dict) -> str:
    ages = config["ages"]
    lo, hi = ages["scale"]["from"], ages["scale"]["to"]

    def pos(age: int) -> float:
        if not lo <= age <= hi:
            raise SystemExit(f"ものさしの範囲外の年齢です: {age}")
        return (age - lo) / (hi - lo) * 100

    ticks = "".join(
        f'<span class="elo-tick{" elo-tick--mark" if any(m["age"] == a for m in ages["marks"]) else ""}" '
        f'style="--x:{pos(a):.2f}%"><i>{a}{"+" if a == hi else ""}</i></span>'
        for a in range(lo, hi + 1, 5)
    )
    timed = [m for m in ages["marks"] if m["age"] is not None]
    bands = "".join(
        f'<span class="elo-band elo-band--{esc(m["key"])}" style="--x:{pos(m["age"]):.2f}%;--row:{i + 2}">'
        f'{esc(m["title"].replace("更新時に", ""))}</span>'
        for i, m in enumerate(timed)
    )
    anytime = next((m for m in ages["marks"] if m["age"] is None), None)
    any_band = f'<span class="elo-band elo-band--any" style="--x:0%;--row:1">{esc(anytime["title"])}</span>' if anytime else ""
    cards = "".join(
        f'<li class="elo-mark elo-mark--{esc(m["key"])}">{picto(m["key"])}'
        f'<span class="elo-mark__badge">{esc(m["badge"])}</span><strong>{esc(m["title"])}</strong>'
        f'<p>{esc(m["note"])}</p></li>'
        for m in ages["marks"]
    )
    return (
        f'<section class="elo-ages" id="elo-ages" aria-labelledby="elo-ages-title">'
        f'<h2 id="elo-ages-title" class="elo-pill">{esc(ages["label"])}</h2>'
        f'<p class="elo-ages__text">{esc(ages["text"])}</p>'
        f'<div class="elo-ruler" role="img" aria-label="{esc(ages["aria"])}">'
        f'<div class="elo-ruler__bands">{any_band}{bands}</div>'
        f'<div class="elo-ruler__scale">{ticks}</div></div>'
        f'<ol class="elo-marks">{cards}</ol></section>'
    )


def render_steps(config: dict) -> str:
    steps = config["steps"]
    items = "".join(
        f'<li class="elo-step">{picto(s["key"])}<span class="elo-step__num" aria-hidden="true">{i}</span>'
        f'<strong>{esc(s["title"])}</strong><p>{esc(s["note"])}</p></li>'
        for i, s in enumerate(steps["items"], start=1)
    )
    st = steps["stat"]
    stat_text = st["text"].format(year=st["year"], returned=f"{st['returned']:,}", cards=f"{st['cards']:,}")
    return (
        f'<section class="elo-steps" id="elo-steps" aria-labelledby="elo-steps-title">'
        f'<h2 id="elo-steps-title" class="elo-pill">{esc(steps["label"])}</h2>'
        f'<ol class="elo-steps__list">{items}</ol>'
        f'<p class="elo-stat">{esc(stat_text)}<small>{esc(st["caveat"])}{link(st["source"]["url"], st["source"]["label"])}</small></p>'
        f"</section>"
    )


def render_faq(config: dict) -> str:
    faq = config["faq"]
    items = "".join(
        f'<details class="elo-faq__item"><summary>{esc(f["q"])}</summary><p>{esc(f["a"])}</p></details>' for f in faq["items"]
    )
    return (
        f'<section class="elo-faq" id="elo-faq" aria-labelledby="elo-faq-title">'
        f'<h2 id="elo-faq-title">{esc(faq["title"])}</h2>{items}'
        f'<p class="elo-faq__note">{esc(faq["medical_note"])}</p></section>'
    )


def render_count(data: dict) -> str:
    config, public, planet = data["config"], data["public"], data["planet"]
    c = config["count"]
    total = public["opinion_count"]
    order = [s["id"] for s in planet["stances"]]
    color = {s["id"]: s["color"] for s in planet["stances"]}
    label = {s["id"]: s["label"] for s in planet["stances"]}
    totals = {sid: 0 for sid in order}
    for issue in public["issues"]:
        for s in issue["stances"]:
            totals[s["id"]] += s["count"]
    if sum(totals.values()) != total:
        raise SystemExit("立場の合計が意見件数と一致しません")
    # 立場は planet 設定の順（賛成→条件付き→反対→中立）。並べ替えると読み手が順序を取り違えるため固定する。
    segs = "".join(
        f'<span class="elo-stance__seg" style="--w:{totals[sid] / total * 100:.2f}%;--c:{color[sid]}"></span>' for sid in order
    )
    stance_items = "".join(
        f'<li><span class="elo-key" style="--c:{color[sid]}" aria-hidden="true"></span>{esc(label[sid])}'
        f"<b>{round(totals[sid] / total * 100)}%</b><small>{totals[sid]:,}件</small></li>"
        for sid in order
    )
    with_reason = set((planet.get("sub_issues") or {}).keys())
    issues = sorted(public["issues"], key=lambda i: (i.get("kind") == "other", -i["count"]))
    if sum(i["count"] for i in issues) != total:
        raise SystemExit("論点別件数の合計が意見件数と一致しません")
    top = max(i["count"] for i in issues)
    rows, missing = [], []
    for issue in issues:
        has_reason = issue["label"] in with_reason
        if not has_reason:
            missing.append(issue["label"])
        tag = "" if has_reason else f'<em class="elo-tag">{esc(c["no_reason_tag"])}</em>'
        other = " elo-issue--other" if issue.get("kind") == "other" else ""
        rows.append(
            f'<li class="elo-issue{other}"><span class="elo-issue__name">{esc(issue["label"])}{tag}</span>'
            f'<span class="elo-issue__bar" style="--w:{issue["count"] / top * 100:.2f}%" aria-hidden="true"></span>'
            f'<b>{issue["count"]:,}<small>件</small></b></li>'
        )
    period = public["collection_period"]
    caption = c["caption_template"].format(
        source=data["source"],
        collected=f"{public['collected_count']:,}",
        start=jp_date(period["start"]),
        end=jp_date(period["end"], with_year=False),
    )
    note = c["no_reason_note_template"].format(labels="・".join(f"「{m}」" for m in missing)) if missing else ""
    updated = c["updated_template"].format(
        updated=jp_date(public["updated_on"]),
        next=jp_date(data["next_collect"], with_year=False) if data["next_collect"] else "未定",
    )
    dates = config["dates"]
    checked = c["checked_template"].format(
        memo_from=jp_date(dates["memo_checked_from"]),
        memo_to=jp_date(dates["memo_checked_to"], with_year=False),
        claims=jp_date(public["claim_verification"]["checked_on"]),
    )
    return (
        f'<section class="elo-count" id="elo-count" aria-labelledby="elo-count-title">'
        f'<div class="elo-count__total"><h2 id="elo-count-title">{esc(c["label"])}</h2>'
        f'<p class="elo-count__num" aria-label="{total:,}件"><strong>{total:,}</strong><span>件</span></p>'
        f'<p class="elo-count__caption">{esc(caption)}</p>'
        f'<p class="elo-count__poll">{esc(c["not_poll"])}</p>'
        f'<h3>{esc(c["stance_title"])}</h3>'
        f'<div class="elo-stance" aria-hidden="true">{segs}</div><ul class="elo-stance__list">{stance_items}</ul></div>'
        f'<div class="elo-count__issues"><h3>{esc(c["issues_title"])}</h3><p class="elo-count__lead">{esc(c["issues_lead"])}</p>'
        f'<ol class="elo-issues">{"".join(rows)}</ol>'
        f'<p class="elo-count__note">{esc(note)}</p><p class="elo-count__updated">{esc(updated)}</p>'
        f'<p class="elo-count__updated">{esc(checked)}</p></div>'
        f"</section>"
    )


def render_fragment(data: dict) -> str:
    config = data["config"]
    crumb = " ／ ".join(esc(c) for c in config["crumb"])
    sources = "".join(link(s["url"], s["label"]) for s in config["sources"])
    return "\n".join(
        [
            START,
            '<section class="elo" aria-label="高齢者免許返納の冒頭">',
            '<div class="elo-hero">',
            f'<div class="elo-hero__copy"><p class="elo-crumb">{crumb}</p>{render_title(config)}'
            f'<p class="elo-lead">{esc(config["lead"])}</p></div>',
            render_answers(config),
            f'<div class="elo-figure">{render_ages(config)}{render_steps(config)}</div>',
            "</div>",
            render_faq(config),
            render_count(data),
            f'<p class="elo-sources"><span>出典</span>{sources}</p>',
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
<title>高齢者免許返納 冒頭試作</title>
<meta name="robots" content="noindex">
<link rel="stylesheet" href="opening.css">
</head>
<body>
<main class="elo-page">
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
