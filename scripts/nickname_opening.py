"""学校でのあだ名禁止ページの冒頭（題名・短答・資料の図・呼び方の範囲・件数・FAQ）を生成する試作。

入力:
  configs/school-nickname-ban-opening.json   冒頭の文言・短答・出典・FAQ（手で直す場所はここだけ）
  docs/data/themes/school-nickname-ban.json  件数・論点別件数・立場・収集期間・主張照合（公開JSON）
  configs/planet/school-nickname-ban.yaml    立場の色と、理由の内訳がある論点（sub_issues）
  THEMES.yaml                                収集元の名前と次回の収集予定（collect_at）

出力（既定は quality/prototypes/school-nickname-ban-opening/）:
  opening-fragment.html  冒頭の部品（マーカー付き）
  index.html             確認用の単独ページ（同じフォルダーの opening.css を読む）
  opening.css            正本 scripts/nickname_redesign/opening.css の写し（2026-10-13に試作フォルダーから正本を移した）

国の資料の本文と制度を確かめた日は設定の checked_on 1か所。読書面（scripts/nickname_reading.py）と背景もここを読む。

時刻や乱数は使わないので、同じ入力なら何度実行しても同じ出力になる。
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
DEFAULT_CONFIG = ROOT / "configs" / "school-nickname-ban-opening.json"
DEFAULT_OUT = ROOT / "quality" / "prototypes" / "school-nickname-ban-opening"
ASSETS = ROOT / "scripts" / "nickname_redesign"
START = "<!-- SCHOOL_NICKNAME_OPENING_START -->"
END = "<!-- SCHOOL_NICKNAME_OPENING_END -->"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def jp_date(iso: str, with_year: bool = True) -> str:
    d = dt.date.fromisoformat(str(iso))
    return f"{d.year}年{d.month}月{d.day}日" if with_year else f"{d.month}月{d.day}日"


def link(url: str, label: str) -> str:
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'


# ---- 入力 -------------------------------------------------------------------

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
    if "checked" in config:
        raise SystemExit("確認日は checked_on 1か所に持つ（checked の2つの日付は使わない）")
    checked = dt.date.fromisoformat(config["checked_on"])
    if checked < dt.date.fromisoformat(public["claim_verification"]["checked_on"]):
        raise SystemExit("国の資料を確かめた日 checked_on が、主張の照合日より古くなっています")
    return {
        "config": config,
        "public": public,
        "planet": planet,
        "source": str(entry.get("sample_source", "")),
        "next_collect": str(entry["collect_at"]) if entry.get("collect_at") else "",
    }


def named_issues(public: dict) -> list[dict]:
    """件数のある論点を多い順に。「その他」は件数があるときだけ最後に置く。"""
    issues = [i for i in public["issues"] if i["count"] > 0]
    return sorted(issues, key=lambda i: (i.get("kind") == "other", -i["count"], i["id"]))


# ---- ピクトグラム（CSSの currentColor で色を変える） --------------------------

ICON_TAG = (
    '<svg class="nop-icon" viewBox="0 0 32 32" aria-hidden="true" focusable="false">'
    '<rect x="5" y="9" width="22" height="17" rx="3" fill="none" stroke="currentColor" stroke-width="2.4"/>'
    '<path d="M11 9V6a5 5 0 0 1 10 0v3" fill="none" stroke="currentColor" stroke-width="2.4"/>'
    '<path d="M10 17h12M10 21h8" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>'
)
ICON_LENS = (
    '<svg class="nop-icon" viewBox="0 0 32 32" aria-hidden="true" focusable="false">'
    '<circle cx="13" cy="13" r="8" fill="none" stroke="currentColor" stroke-width="2.6"/>'
    '<path d="M19 19l8 8" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>'
)
ICON_SCHOOL = (
    '<svg class="nop-icon" viewBox="0 0 32 32" aria-hidden="true" focusable="false">'
    '<path d="M4 28V14l12-8 12 8v14z" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/>'
    '<circle cx="16" cy="14" r="3" fill="none" stroke="currentColor" stroke-width="2"/>'
    '<path d="M13 28v-7h6v7" fill="none" stroke="currentColor" stroke-width="2.4"/></svg>'
)
ICON_DOC = (
    '<svg class="nop-doc__paper" viewBox="0 0 40 48" aria-hidden="true" focusable="false">'
    '<path d="M3 3h24l10 10v32H3z" fill="#fff" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/>'
    '<path d="M27 3v10h10" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/>'
    '<path d="M9 22h20M9 28h20M9 34h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity=".55"/></svg>'
)


# ---- 部品 -------------------------------------------------------------------

def render_title(config: dict) -> str:
    t = config["title"]
    phrases = "".join(
        f'<span class="nop-phrase{" nop-accent" if i == t["accent_index"] else ""}">{esc(p)}</span>'
        for i, p in enumerate(t["phrases"])
    )
    sub = "".join(f'<span class="nop-phrase">{esc(p)}</span>' for p in t["sub"])
    return f'<h1 class="nop-title">{phrases}<span class="nop-sub">{sub}</span></h1>'


def render_documents(config: dict) -> str:
    d = config["documents"]
    terms = "」「".join(d["terms"])
    result = d["result_template"].format(terms=terms, result=d["result_label"])
    docs = "".join(
        f'<li class="nop-doc">{ICON_DOC}<span class="nop-doc__kind">{esc(item["short"])}</span>'
        f'<span class="nop-doc__name">{link(item["url"], item["name"])}</span>'
        f'<span class="nop-doc__hit">{ICON_LENS}<b>{esc(d["result_label"])}</b></span></li>'
        for item in d["items"]
    )
    checked = jp_date(config["checked_on"])
    return (
        f'<figure class="nop-docs" aria-labelledby="nop-docs-title">'
        f'<figcaption id="nop-docs-title" class="nop-docs__title">{esc(d["title"])}</figcaption>'
        f'<p class="nop-docs__result">{esc(result)}<small>{esc(checked)}確認</small></p>'
        f'<ol class="nop-docs__list">{docs}</ol>'
        f'<div class="nop-docs__school">{ICON_SCHOOL}<p><b>{esc(d["school_label"])}</b>'
        f'<span>{esc(d["school_note"])}</span></p></div>'
        f"</figure>"
    )


def render_voices(label: str, voices: dict) -> str:
    return (
        f'<div class="nop-voices" aria-label="{esc(label)}"><p class="nop-voices__label">{esc(label)}</p>'
        f'<p><span>期待</span>{esc(voices["expectation"])}</p>'
        f'<p><span>懸念</span>{esc(voices["concern"])}</p></div>'
    )


def render_answer(config: dict, public: dict, answer: dict, index: int) -> str:
    unconfirmed = list(answer["unconfirmed"])
    if answer.get("claim_id"):
        claims = {c["id"]: c for c in public["claim_verification"]["claims"]}
        claim = claims.get(answer["claim_id"])
        if not claim:
            raise SystemExit(f"公開JSONに主張照合 {answer['claim_id']} がありません")
        if claim["verdict"] != "miss":
            raise SystemExit(f"主張照合 {answer['claim_id']} の判定が「裏が取れない」ではなくなりました。文言を見直してください")
        unconfirmed.append(answer["claim_template"].format(claim=claim["claim"]))
    ok = "".join(f"<li>{esc(t)}</li>" for t in answer["confirmed"])
    ng = "".join(f"<li>{esc(t)}</li>" for t in unconfirmed)
    figure = render_documents(config) if answer["key"] == "rule" else ""
    return (
        f'<article class="nop-answer nop-answer--{esc(answer["key"])}" aria-labelledby="nop-q-{esc(answer["key"])}">'
        f'<p class="nop-answer__num" aria-hidden="true">Q{index}</p>'
        f'<h2 class="nop-answer__q" id="nop-q-{esc(answer["key"])}">{esc(answer["q"])}</h2>'
        f'<p class="nop-answer__short">{esc(answer["short"])}</p>'
        f"{figure}"
        f'<div class="nop-split">'
        f'<div class="nop-split__ok"><h3>{esc(answer["confirmed_label"])}</h3><ul>{ok}</ul></div>'
        f'<div class="nop-split__ng"><h3>{esc(answer["unconfirmed_label"])}</h3><ul>{ng}</ul></div>'
        f"</div>"
        f"</article>"
    )


def render_scope(config: dict) -> str:
    s = config["scope"]
    for rule in s["rules"]:
        unknown = [t for t in rule["stops"] if t not in s["tags"]]
        if unknown:
            raise SystemExit(f"呼び方の範囲に未定義の呼び方があります: {unknown}")
    head = "".join(f'<th scope="col"><span class="nop-tag">{ICON_TAG}<b>{esc(t).replace("・", "・<wbr>")}</b></span></th>' for t in s["tags"])
    rows = []
    for rule in s["rules"]:
        cells = "".join(
            f'<td class="{"nop-cell--stop" if t in rule["stops"] else "nop-cell--keep"}">'
            f'{esc(s["stop_label"] if t in rule["stops"] else s["keep_label"])}</td>'
            for t in s["tags"]
        )
        rows.append(f'<tr><th scope="row">{esc(rule["label"])}</th>{cells}</tr>')
    return (
        f'<section class="nop-scope" aria-labelledby="nop-scope-title">'
        f'<h2 id="nop-scope-title">{esc(s["title"])}</h2>'
        f'<div class="nop-scope__wrap"><table class="nop-scope__table">'
        f'<thead><tr><td></td>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
        f'<p class="nop-scope__note">{esc(s["note"])}</p>'
        f"</section>"
    )


def render_count(data: dict) -> str:
    config, public, planet = data["config"], data["public"], data["planet"]
    c = config["count"]
    total = public["opinion_count"]
    if public.get("issue_assigned_count") not in (None, total):
        raise SystemExit("論点を割り当てた件数が意見件数と一致しません")

    # 立場：論点をまたいで合計。並びは planet 設定の順（禁止支持→条件付き→反対→中立）
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
        f'<span class="nop-stance__seg" style="--w:{totals[sid] / total * 100:.2f}%;--c:{color[sid]}"></span>'
        for sid in order
        if totals[sid]
    )
    stance_items = "".join(
        f'<li><span class="nop-key" style="--c:{color[sid]}" aria-hidden="true"></span>{esc(label[sid])}'
        f"<b>{totals[sid]:,}<small>件</small></b></li>"
        for sid in order
    )

    # 論点別：件数は公開JSONのまま。10件未満に「少数」の印。理由データが無い論点に「理由は未公開」
    issues = named_issues(public)
    if sum(i["count"] for i in public["issues"]) != total:
        raise SystemExit("論点別件数の合計が意見件数と一致しません")
    with_reason = set((planet.get("sub_issues") or {}).keys())
    top = max(i["count"] for i in issues)
    rows, missing, has_small = [], [], False
    for issue in issues:
        tags = ""
        if issue["count"] < c["small_threshold"]:
            has_small = True
            tags += f'<em class="nop-flag">{esc(c["small_tag"])}</em>'
        if issue["label"] not in with_reason:
            missing.append(issue["label"])
            tags += f'<em class="nop-flag nop-flag--muted">{esc(c["no_reason_tag"])}</em>'
        rows.append(
            f'<li class="nop-issue"><span class="nop-issue__name">{esc(issue["label"])}{tags}</span>'
            f'<span class="nop-issue__bar" aria-hidden="true"><i style="--w:{issue["count"] / top * 100:.2f}%"></i></span>'
            f'<b>{issue["count"]:,}<small>件</small></b></li>'
        )
    notes = []
    if has_small:
        notes.append(c["small_note"])
    if missing:
        notes.append(c["no_reason_note_template"].format(labels="と".join(f"「{m}」" for m in missing)))

    period = public["collection_period"]
    caption = c["caption_template"].format(
        source=data["source"],
        collected=f"{public['collected_count']:,}",
        start=jp_date(period["start"]),
        end=jp_date(period["end"], with_year=False),
    )
    after_day = dt.date.fromisoformat(period["end"]) + dt.timedelta(days=1)
    after = c["after_template"].format(
        after=jp_date(after_day.isoformat(), with_year=False),
        next=jp_date(data["next_collect"], with_year=False) if data["next_collect"] else "未定",
    )
    updated = c["updated_template"].format(updated=jp_date(public["updated_on"]))
    note_html = "".join(f'<p class="nop-count__note">{esc(n)}</p>' for n in notes)
    return (
        f'<section class="nop-count" id="school-nickname-opening-count" aria-labelledby="nop-count-title">'
        f'<div class="nop-count__total"><h2 id="nop-count-title">{esc(c["label"])}</h2>'
        f'<p class="nop-count__num"><strong>{total:,}</strong><span>件</span></p>'
        f'<p class="nop-count__caption">{esc(caption)}</p>'
        f'<p class="nop-count__poll">{esc(c["not_poll"])}</p>'
        f'<h3 class="nop-count__sub">{esc(c["stance_title"])}</h3>'
        f'<div class="nop-stance" aria-hidden="true">{segs}</div><ul class="nop-stance__list">{stance_items}</ul></div>'
        f'<div class="nop-count__issues"><h3 class="nop-count__sub">{esc(c["issues_title_template"].format(n=len(issues)))}</h3>'
        f'<ol class="nop-issues">{"".join(rows)}</ol>{note_html}'
        f'<p class="nop-count__after">{esc(after)}</p><p class="nop-count__updated">{esc(updated)}</p></div>'
        f"</section>"
    )


def render_faq(config: dict) -> str:
    f = config["faq"]
    items = "".join(
        f'<details class="nop-faq__item"><summary>{esc(item["q"])}</summary><p>{esc(item["a"])}</p></details>'
        for item in f["items"]
    )
    return (
        f'<section class="nop-faq" id="school-nickname-faq" aria-labelledby="nop-faq-title">'
        f'<h2 id="nop-faq-title">{esc(f["title"])}<small>{len(f["items"])}問</small></h2>{items}</section>'
    )


def render_fragment(data: dict) -> str:
    config, public = data["config"], data["public"]
    n_issues = len(named_issues(public))
    crumb = " ／ ".join(esc(c) for c in config["crumb"])
    answers = "".join(render_answer(config, public, a, i) for i, a in enumerate(config["answers"], 1))
    links = "".join(
        f'<a class="nop-link" href="{esc(l["href"])}">{esc(l["label_template"].format(n=n_issues))}</a>'
        for l in config["links"]
    )
    checked = config["checked_template"].format(checked=jp_date(config["checked_on"]),
                                                claims=jp_date(public["claim_verification"]["checked_on"]))
    sources = "".join(
        f"<li>{esc(item['publisher'])}：{link(item['url'], item['name'])}</li>" for item in config["documents"]["items"]
    )
    s = config["safety"]
    return "\n".join(
        [
            START,
            '<section class="nop" aria-label="学校でのあだ名禁止の冒頭">',
            f'<header class="nop-hero"><p class="nop-crumb">{crumb}</p>{render_title(config)}'
            f'<p class="nop-lead">{esc(config["lead"])}</p></header>',
            f'<div class="nop-answers">{answers}</div>',
            render_scope(config),
            render_count(data),
            f'<aside class="nop-safety"><b>{esc(s["title"])}</b><p>{esc(s["text"])}</p></aside>',
            f'<nav class="nop-links" aria-label="このページの読み方">{links}</nav>',
            f'<div class="nop-sources"><p data-checked-on="{esc(config["checked_on"])}">{esc(checked)}</p><ul>{sources}</ul></div>',
            "</section>",
            render_faq(config),
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
<title>学校でのあだ名禁止 冒頭試作</title>
<meta name="robots" content="noindex">
<link rel="stylesheet" href="opening.css">
</head>
<body>
<main class="nop-page">
{fragment}</main>
</body>
</html>
"""


def fragment_for(config_path: Path = DEFAULT_CONFIG) -> str:
    """冒頭の部品（マーカー付き）。読書面の試作（scripts/nickname_reading.py）がこの下に読書面をつなぐ。"""
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
