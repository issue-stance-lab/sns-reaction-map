#!/usr/bin/env python3
"""高齢者免許返納ページを、正典の「意見」投稿だけから再生成する。

生成対象は SM_RAW、論点セクター、論点別サマリー、スタンス集計、詳細表。
件数は SM_RAW をブラウザ側で数え、HTMLへ手書きしない。

    python3 scripts/build_elderly_arena.py
    python3 scripts/build_elderly_arena.py --check
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .issue_card_counts import IssueCountError, span_html
    from .sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml
    from .x_embed import period_label
    from .x_embed import embed_html
except ImportError:
    from issue_card_counts import IssueCountError, span_html  # type: ignore[no-redef]
    from sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml  # type: ignore[no-redef]
    from x_embed import period_label  # type: ignore[no-redef]
    from x_embed import embed_html  # type: ignore[no-redef]

THEME = "elderly-license-revocation"
PUBLIC_THEME = ROOT / "data" / "public" / "themes" / f"{THEME}.json"
ISSUE_ORDER = (
    "義務化・事故防止",
    "地方の足・移動権",
    "適性検査強化",
    "代替交通整備",
    "自主返納支援",
    "その他",
)
ISSUE_SLUG = {
    "義務化・事故防止": "gimuka",
    "地方の足・移動権": "chiho",
    "適性検査強化": "tekisei",
    "代替交通整備": "daitai",
    "自主返納支援": "jishu",
    "その他": "sonota",
}
STANCE_ORDER = ("義務化賛成", "条件付き賛成", "義務化反対", "中立・情報")
STANCE_X = {
    "義務化賛成": 2.0,
    "条件付き賛成": 1.0,
    "義務化反対": -2.0,
    "中立・情報": 0.0,
}
INTENSITY_E = {"low": 0.6, "medium": 1.3, "high": 2.0}


def classification(record: dict[str, Any]) -> dict[str, Any]:
    nested = record.get("classification")
    if not isinstance(nested, dict):
        raise IssueCountError("classification を持たないレコードがあります")
    return nested


def sample_period() -> str:
    """台帳に書かれた取得期間。ページの表示はここだけを出所にする。"""
    return str(parse_themes_yaml(THEMES_YAML)[THEME].get("sample_period") or "unknown")


def load_opinions(input_path: Path | None = None) -> tuple[list[dict[str, Any]], str, int]:
    themes = parse_themes_yaml(THEMES_YAML)
    sample_file = str(themes[THEME].get("sample_file") or "")
    if not sample_file or "synthetic" in sample_file:
        raise IssueCountError(f"{THEME}: 正典 sample_file が不正です: {sample_file}")
    source = input_path or ROOT / sample_file
    records = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise IssueCountError(f"{THEME}: 正典が空、またはJSON配列ではありません")

    opinions: list[dict[str, Any]] = []
    for number, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise IssueCountError(f"{number}件目がJSONオブジェクトではありません")
        c = classification(record)
        if "is_opinion" not in c or not isinstance(c["is_opinion"], bool):
            raise IssueCountError(f"{number}件目の classification.is_opinion が欠落またはboolではありません")
        if not c["is_opinion"]:
            continue
        issue = c.get("main_issue")
        stance = c.get("stance")
        intensity = c.get("intensity")
        if issue not in ISSUE_ORDER:
            raise IssueCountError(f"未知の main_issue: {issue}")
        if stance not in STANCE_X:
            raise IssueCountError(f"未知の stance: {stance}")
        if intensity not in INTENSITY_E:
            raise IssueCountError(f"未知の intensity: {intensity}")
        opinions.append(record)
    if not opinions:
        raise IssueCountError("意見と判定されたレコードがありません")
    return opinions, str(source), len(records)


def build_sm_raw(rows: list[dict[str, Any]]) -> str:
    issue_index = {issue: i for i, issue in enumerate(ISSUE_ORDER)}
    points = []
    for row in rows:
        c = classification(row)
        points.append(
            {
                "x": STANCE_X[str(c["stance"])],
                "e": INTENSITY_E[str(c["intensity"])],
                "c": round(float(c.get("confidence", 0.7)), 2),
                "i": issue_index[str(c["main_issue"])],
                "s": str(c.get("summary") or "")[:80],
                "u": str(row.get("url") or ""),
            }
        )
    body = ",\n".join("  " + json.dumps(p, ensure_ascii=False, separators=(",", ":")) for p in points)
    return f"const SM_RAW = [\n{body}\n];"


def build_issues() -> str:
    body = ",\n    ".join(f"{{k:{json.dumps(issue, ensure_ascii=False)},n:0}}" for issue in ISSUE_ORDER)
    return f"const ISSUES=[\n    {body}\n  ];"


def stance_counts(rows: list[dict[str, Any]], issue: str | None = None) -> Counter[str]:
    return Counter(
        str(classification(row)["stance"])
        for row in rows
        if issue is None or classification(row)["main_issue"] == issue
    )


def build_stats_from_counts(
    issue_counts: Counter[str], stances: Counter[str], total: int, total_collected: int
) -> str:
    return "\n".join(
        [
            '<section class="stats insight-stats" aria-label="このテーマの4つの注目ポイント">',
            '<article class="stat insight-stat"><div class="insight-head"><span class="insight-icon" aria-hidden="true">🗣️</span><span class="insight-label">分析対象の意見</span></div>',
            f'<strong class="insight-value">{total}<small>件</small></strong><p class="insight-note">収集{total_collected}件から意見のみを抽出</p><div class="insight-meter" aria-hidden="true"><i style="width:100%"></i></div></article>',
            '<article class="stat insight-stat" data-tone="debate"><div class="insight-head"><span class="insight-icon" aria-hidden="true">🚘</span><span class="insight-label">最も多い立場</span></div>',
            f'<strong class="insight-value">義務化賛成 {stances["義務化賛成"]}<small>件</small></strong><p class="insight-note">意見の{round(stances["義務化賛成"] / total * 100)}%</p><div class="insight-meter" aria-hidden="true"><i style="width:{round(stances["義務化賛成"] / total * 100)}%"></i></div></article>',
            '<article class="stat insight-stat" data-tone="option"><div class="insight-head"><span class="insight-icon" aria-hidden="true">💡</span><span class="insight-label">条件付き賛成</span></div>',
            f'<strong class="insight-value">{stances["条件付き賛成"]}<small>件</small></strong><p class="insight-note">一律義務化ではなく条件や代替策を重視</p><div class="insight-meter" aria-hidden="true"><i style="width:{round(stances["条件付き賛成"] / total * 100)}%"></i></div></article>',
            '<article class="stat insight-stat" data-tone="insight"><div class="insight-head"><span class="insight-icon" aria-hidden="true">🔥</span><span class="insight-label">最も話された論点</span></div>',
            f'<strong class="insight-value">義務化・事故防止 {issue_counts["義務化・事故防止"]}<small>件</small></strong><p class="insight-note">意見の{round(issue_counts["義務化・事故防止"] / total * 100)}%</p><div class="insight-meter" aria-hidden="true"><i style="width:{round(issue_counts["義務化・事故防止"] / total * 100)}%"></i></div></article>',
            "</section>",
        ]
    )


def build_stats(rows: list[dict[str, Any]], total_collected: int) -> str:
    return build_stats_from_counts(
        Counter(str(classification(row)["main_issue"]) for row in rows),
        stance_counts(rows),
        len(rows),
        total_collected,
    )


def build_issue_blocks(rows: list[dict[str, Any]]) -> str:
    issue_counts = Counter(str(classification(row)["main_issue"]) for row in rows)
    articles = []
    for number, issue in enumerate(ISSUE_ORDER, start=1):
        stances = stance_counts(rows, issue)
        samples = [row for row in rows if classification(row)["main_issue"] == issue and row.get("url")][:2]
        sides = "".join(
            f'<div class="side {"pos" if stance == "義務化賛成" else "neg" if stance == "義務化反対" else "neu"}"><strong>{html.escape(stance)} {stances[stance]}件</strong>正典の意見投稿から集計</div>'
            for stance in STANCE_ORDER
            if stances[stance]
        )
        sample_html = "\n".join(
            '<div class="sample-card-x"><div class="meta">{stance} / {intensity}</div><p>{summary}</p>{embed}</div>'.format(
                stance=html.escape(str(classification(row)["stance"])),
                intensity=html.escape(str(classification(row)["intensity"])),
                summary=html.escape(str(classification(row).get("summary") or "")),
                embed=embed_html(row["url"]),
            )
            for row in samples
        )
        badge = "・最大勢力" if issue_counts[issue] == max(issue_counts.values()) else ""
        articles.append(
            f'<article class="issue-block" id="issue-{ISSUE_SLUG[issue]}"><div class="issue-head">'
            f'<span class="axis-kicker">論点{number}{badge}</span><h3>{html.escape(issue)}</h3>'
            f'<p class="issue-desc">この論点に分類された意見は{issue_counts[issue]}件。スタンス別内訳は正典から自動集計しています。</p>'
            f'<div class="issue-sides">{sides}</div></div><div class="sample-grid">{sample_html}</div></article>'
        )
    return (
        '<section class="panel" id="issue-blocks-section">\n'
        f'<div class="panel-title"><h2>論点別サマリー</h2><span>SM_RAWと同じ意見{len(rows)}件から自動生成</span></div>\n'
        + "\n".join(articles)
        + "\n</section>"
    )


def build_stance_summary(rows: list[dict[str, Any]]) -> str:
    stances = stance_counts(rows)
    cards = "".join(
        f'<article class="axis-card"><div class="axis-kicker">スタンス</div><h3>{html.escape(stance)}</h3><div class="axis-count">{stances[stance]}<span>件</span></div><p>意見{len(rows)}件を正典の classification.stance で集計。</p></article>'
        for stance in STANCE_ORDER
    )
    return f'<section class="panel conflict-panel"><div class="panel-title"><h2>スタンス集計</h2><span>意見のみ</span></div><div class="axis-grid">{cards}</div></section>'


def build_details(rows: list[dict[str, Any]]) -> str:
    return build_details_from_counts(
        Counter(str(classification(row)["main_issue"]) for row in rows),
        stance_counts(rows),
        Counter(str(classification(row)["intensity"]) for row in rows),
        len(rows),
    )


def build_details_from_counts(
    issues: Counter[str], stances: Counter[str], intensities: Counter[str], total: int
) -> str:
    issue_rows = "".join(f"<tr><th>{html.escape(issue)}</th><td>{issues[issue]}</td></tr>" for issue in ISSUE_ORDER)
    stance_rows = "".join(f"<tr><th>{html.escape(stance)}</th><td>{stances[stance]}</td></tr>" for stance in STANCE_ORDER)
    intensity_rows = "".join(f"<tr><th>{key}</th><td>{intensities[key]}</td></tr>" for key in ("high", "medium", "low"))
    return (
        '<section class="panel details-panel" id="detail-data"><div class="panel-title"><h2>詳細データ</h2><span>意見のみ</span></div>'
        f'<details open><summary>論点別件数</summary><div class="table-wrap"><table><tbody>{issue_rows}<tr><th>合計</th><td>{total}</td></tr></tbody></table></div></details>'
        f'<details><summary>スタンス別件数</summary><div class="table-wrap"><table><tbody>{stance_rows}</tbody></table></div></details>'
        f'<details><summary>表現強度別件数</summary><div class="table-wrap"><table><tbody>{intensity_rows}</tbody></table></div></details></section>'
    )


def _public_counts(data: dict[str, Any]) -> tuple[int, int, Counter[str], Counter[str], Counter[str]]:
    """公開JSONの論点・立場・強度集計を検査してページ用に読み込む。"""
    if data.get("theme_id") != THEME:
        raise IssueCountError(f"高齢者免許返納の公開JSONではありません: {data.get('theme_id')}")
    items = {str(item["label"]): item for item in data.get("issues", [])}
    if set(items) != set(ISSUE_ORDER):
        raise IssueCountError("公開JSONの論点がページ定義と一致しません: " + ", ".join(sorted(items)))
    issues: Counter[str] = Counter()
    stances: Counter[str] = Counter()
    intensities: Counter[str] = Counter()
    for issue in ISSUE_ORDER:
        item = items[issue]
        count = int(item["count"])
        issues[issue] = count
        by_stance = {str(value["label"]): int(value["count"]) for value in item.get("stances", [])}
        if set(by_stance) != set(STANCE_ORDER) or sum(by_stance.values()) != count:
            raise IssueCountError(f"公開JSONの立場集計が一致しません: {issue}")
        stances.update(by_stance)
        by_intensity = {str(value["id"]): int(value["count"]) for value in item.get("intensities", [])}
        if set(by_intensity) != set(INTENSITY_E) or sum(by_intensity.values()) != count:
            raise IssueCountError(f"公開JSONの強度集計が一致しません: {issue}")
        intensities.update(by_intensity)
    collected = int(data["collected_count"])
    opinions = int(data["opinion_count"])
    if sum(issues.values()) != opinions or sum(stances.values()) != opinions or sum(intensities.values()) != opinions:
        raise IssueCountError("公開JSONの意見数と集計値が一致しません")
    return collected, opinions, issues, stances, intensities


def apply_public_counts(page: str, public_theme: Path = PUBLIC_THEME) -> str:
    """候補公開JSONを正典に、ページ上の集計表示を貼り直す。"""
    collected, total, issues, stances, intensities = _public_counts(
        json.loads(public_theme.read_text(encoding="utf-8"))
    )
    lead = (
        f'<p class="lead">Yahooリアルタイム検索で取得した公開投稿{collected}件のうち、意見と判定した{total}件を分析対象としています。'
        '世論調査ではなく、SNS反応サンプルの論点比較です。</p>'
    )
    page = replace_once(page, r'<p class="lead">.*?</p>', lead, "リード文", flags=re.S)
    research = f'<strong style="color:var(--ink);">このマップの元データ:</strong> Yahooリアルタイム検索で取得した公開投稿{collected}件のうち、意見と判定した{total}件を分析対象としています。<br>'
    page = replace_once(page, r'<strong style="color:var\(--ink\);">このマップの元データ:</strong>.*?<br>', research, "調査条件", flags=re.S)
    page = replace_once(page, r'<span class="conclusion-count"><b>\d+</b>件</span>', f'<span class="conclusion-count"><b>{issues[ISSUE_ORDER[0]]}</b>件</span>', "議論の中心")
    page = replace_once(page, r'<section class="stats insight-stats".*?</section>', build_stats_from_counts(issues, stances, total, collected), "注目ポイント", flags=re.S)
    page = replace_once(page, r'<div class="panel-title"><h2>SNS反応マップ</h2><span>[^<]+</span></div>', f'<div class="panel-title"><h2>SNS反応マップ</h2><span>{total}件 | セクター=論点 / 中心に近いほど冷静 / 色=賛否 | ホバーで詳細</span></div>', "マップ見出し")
    page = replace_once(page, r'<section class="panel details-panel" id="detail-data">.*?</section>', build_details_from_counts(issues, stances, intensities, total), "詳細データ", flags=re.S)
    return page


def sync_vote_counts(page: str, counts: Counter[str]) -> str:
    """投票の選択肢の説明文にある「（N件）」を論点別件数に合わせる。

    選択肢そのもの（k）は触らない。選択肢の数が変わると choiceIdx の意味がずれ、
    Edge Function の再デプロイと既存票の破棄が要る。ここで変えるのは説明文の中の件数だけ。
    """
    pattern = re.compile(
        r"(\{k:'(?P<key>[^']+)',\s*icon:'[^']*',desc:'[^']*?)（\d[\d,]*件）(')"
    )
    # 投票の選択肢のキーは論点名と1文字違うものがある（代替交通の整備が先 ⇔ 代替交通整備）
    aliases = {"代替交通の整備が先": "代替交通整備", "自主返納・支援充実": "自主返納支援"}

    def replace(match: re.Match[str]) -> str:
        key = aliases.get(match.group("key"), match.group("key"))
        if key not in counts:
            raise IssueCountError(f"投票の選択肢が論点にありません: {match.group('key')}")
        return f"{match.group(1)}（{counts[key]}件）{match.group(3)}"

    result, replaced = pattern.subn(replace, page)
    if replaced < 1:
        raise IssueCountError("投票の選択肢の説明文に件数が見つかりません")
    return result


def replace_once(page: str, pattern: str, replacement: str, label: str, *, flags: int = 0) -> str:
    result, count = re.subn(pattern, lambda _: replacement, page, count=1, flags=flags)
    if count != 1:
        raise IssueCountError(f"{label}: 1箇所だけ一致する必要があります（{count}箇所）")
    return result


def build(
    *,
    check: bool = False,
    input_path: Path | None = None,
    html_template: Path | None = None,
    output_html: Path | None = None,
) -> tuple[list[str], bool]:
    rows, sample_file, collected = load_opinions(input_path)
    counts = Counter(str(classification(row)["main_issue"]) for row in rows)
    config = json.loads((ROOT / "configs" / f"{THEME}-reaction-map.json").read_text(encoding="utf-8"))
    public_path = ROOT / "docs" / f"{THEME}-reaction-map.html"
    template = html_template or public_path
    destination = output_html or public_path
    before = template.read_text(encoding="utf-8")
    page = before

    page = replace_once(page, r"const SM_RAW = \[.*?\n\];", build_sm_raw(rows), "SM_RAW", flags=re.S)
    page = replace_once(page, r"const ISSUES=\[.*?\n  \];", build_issues(), "ISSUES", flags=re.S)
    count_line = "  SM_RAW.forEach(p=>{if(ISSUES[p.i])ISSUES[p.i].n+=1;});\n"
    if count_line not in page:
        page = replace_once(page, r"  const total=ISSUES\.reduce", count_line + "  const total=ISSUES.reduce", "SM_RAWからの件数集計")
    page = replace_once(page, r'<div class="panel-title"><h2>SNS反応マップ</h2><span>[^<]+</span></div>', f'<div class="panel-title"><h2>SNS反応マップ</h2><span>{len(rows)}件 | セクター=論点 / 中心に近いほど冷静 / 色=賛否 | ホバーで詳細</span></div>', "マップ見出し")
    lead = f'Yahooリアルタイム検索で取得した公開投稿{collected}件のうち、意見と判定した{len(rows)}件を分析対象としています。世論調査ではなく、SNS反応サンプルの論点比較です。'
    page = replace_once(page, r'<p class="lead">.*?</p>', f'<p class="lead">{lead}</p>', "リード文", flags=re.S)
    research = f'<strong style="color:var(--ink);">このマップの元データ:</strong> Yahooリアルタイム検索で取得した公開投稿{collected}件のうち、意見と判定した{len(rows)}件を分析対象としています。<br>'
    page = replace_once(page, r'<strong style="color:var\(--ink\);">このマップの元データ:</strong>.*?<br>', research, "調査条件", flags=re.S)
    # 取得期間も台帳（THEMES.yaml の sample_period）から書く。ページに直書きすると、
    # 収集を重ねたときに前回の日付のまま公開される（2026-08-17 に自転車で発生）。
    page = replace_once(
        page,
        r"（取得期間: [^／]*／",
        f"（取得期間: {period_label(sample_period())}／",
        "取得期間",
    )
    # 「記事の検証方法」の収集方法の文はここでは書かない。
    # configs/theme-seo.json の collection を apply_theme_trust.py が {total} / {opinions} を
    # 解決して書き込む。昇格処理はビルダーの後に apply_theme_trust.py を呼ぶため、両方が
    # 別々の文言で同じ場所を書くと、次にビルダーを流したとき差し替え対象を見失って止まる
    # （2026-08-08 に「1箇所だけ一致する必要があります（0箇所）」で実際に発生）。
    # 1つの文の書き手は1つに保つ。
    page = replace_once(page, r'<span class="conclusion-count"><b>\d+</b>件</span>', f'<span class="conclusion-count"><b>{counts[ISSUE_ORDER[0]]}</b>件</span>', "議論の中心")
    page = sync_vote_counts(page, counts)
    page = replace_once(page, r'<section class="stats insight-stats".*?</section>', build_stats(rows, collected), "注目ポイント", flags=re.S)
    page = replace_once(page, r'<section class="panel" id="issue-blocks-section">.*?</section>', build_issue_blocks(rows), "論点別サマリー", flags=re.S)
    page = replace_once(page, r'<section class="panel conflict-panel">.*?</section>', build_stance_summary(rows), "スタンス集計", flags=re.S)
    page = replace_once(page, r'<section class="panel details-panel" id="detail-data">.*?</section>', build_details(rows), "詳細データ", flags=re.S)

    for card in config["issue_counts"]["cards"]:
        total = sum(counts[str(issue)] for issue in card["main_issue"])
        page = replace_once(page, rf'<span class="explainer-count" id="issue-count-{THEME}-{card["slug"]}">\d+件</span>', span_html(THEME, str(card["slug"]), total), f'論点カード {card["slug"]}')

    changed = page != before
    if not check:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(page, encoding="utf-8")
    detail = " / ".join(f"{issue}={counts[issue]}" for issue in ISSUE_ORDER)
    return [f"出所: {sample_file}（収集{collected}件 / 意見{len(rows)}件）", f"論点: {detail}", "スタンス: " + " / ".join(f"{s}={stance_counts(rows)[s]}" for s in STANCE_ORDER)], changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--html-template", type=Path)
    parser.add_argument("--output-html", type=Path)
    parser.add_argument("--public-counts-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.check and any((args.input, args.html_template, args.output_html, args.public_counts_only)):
            parser.error("--checkは公開ページと正典の一致確認専用です")
        if args.public_counts_only:
            if args.input or args.html_template:
                parser.error("--public-counts-only は --output-html だけを指定してください")
            destination = args.output_html or ROOT / "docs" / f"{THEME}-reaction-map.html"
            destination.write_text(apply_public_counts(destination.read_text(encoding="utf-8")), encoding="utf-8")
            print(f"OK: 公開JSONから集計表示を更新しました: {destination}")
            return 0
        if any((args.input, args.html_template, args.output_html)) and not all(
            (args.input, args.html_template, args.output_html)
        ):
            parser.error("候補生成では--input/--html-template/--output-htmlをすべて指定してください")
        lines, changed = build(
            check=args.check,
            input_path=args.input,
            html_template=args.html_template,
            output_html=args.output_html,
        )
        print("\n".join(lines))
        if args.check and changed:
            print("NG: HTMLに差分があります", file=sys.stderr)
            return 1
        print("OK: 差分なし" if not changed else "UPDATE: HTMLを更新しました")
        return 0
    except (IssueCountError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
