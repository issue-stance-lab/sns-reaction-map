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
    from .issue_card_counts import IssueCountError
    from .sync_portal_stats import ROOT, THEMES_YAML, parse_themes_yaml
    from .x_embed import period_label
    from .x_embed import embed_html
except ImportError:
    from issue_card_counts import IssueCountError  # type: ignore[no-redef]
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
    # 山なみ差し替え後は、この3か所だけ触ってはいけない（課題54: 高齢者段階1）。
    # ・リード文：新テンプレ側にも <p class="lead"> がクイズのJS文字列内に含まれ、
    #   1箇所一致の前提が崩れて落ちる（2箇所ヒット）
    # ・注目ポイント：旧セクションごと削除済みで、対象が見つからず落ちる（0箇所）
    # ・マップ見出し：旧セクションは消えるが、新テンプレの山なみ本体に同じクラス名・
    #   同じ見出し文言の要素が別の意味で存在し、1箇所一致してしまう。気づかず直すと
    #   新テンプレ側の表示を壊す（サイレントな誤爆）
    planet_mode = "<!-- PLANET_SECTION_START -->" in page
    if not planet_mode:
        lead = (
            f'<p class="lead">Yahooリアルタイム検索で取得した公開投稿{collected}件のうち、意見と判定した{total}件を分析対象としています。'
            '世論調査ではなく、SNS反応サンプルの論点比較です。</p>'
        )
        page = replace_once(page, r'<p class="lead">.*?</p>', lead, "リード文", flags=re.S)
    research = f'<strong style="color:var(--ink);">このマップの元データ:</strong> Yahooリアルタイム検索で取得した公開投稿{collected}件のうち、意見と判定した{total}件を分析対象としています。<br>'
    page = replace_once(page, r'<strong style="color:var\(--ink\);">このマップの元データ:</strong>.*?<br>', research, "調査条件", flags=re.S)
    page = replace_once(page, r'<span class="conclusion-count"><b>\d+</b>件</span>', f'<span class="conclusion-count"><b>{issues[ISSUE_ORDER[0]]}</b>件</span>', "議論の中心")
    if not planet_mode:
        page = replace_once(page, r'<section class="stats insight-stats".*?</section>', build_stats_from_counts(issues, stances, total, collected), "注目ポイント", flags=re.S)
        page = replace_once(page, r'<div class="panel-title"><h2>SNS反応マップ</h2><span>[^<]+</span></div>', f'<div class="panel-title"><h2>SNS反応マップ</h2><span>{total}件 | セクター=論点 / 中心に近いほど冷静 / 色=賛否 | ホバーで詳細</span></div>', "マップ見出し")
    page = replace_once(page, r'<section class="panel details-panel" id="detail-data">.*?</section>', build_details_from_counts(issues, stances, intensities, total), "詳細データ", flags=re.S)
    page = apply_elderly_stance_glance(page)
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


STANCE_GLANCE_START = "<!-- STANCE_GLANCE_START -->"
STANCE_GLANCE_END = "<!-- STANCE_GLANCE_END -->"
STANCE_GLANCE_ANCHOR = "<!-- RESEARCH_CONDITIONS_START -->"

# configs/planet/elderly-license-revocation.yaml の stances[].key と対応させる。
# 集計(count/color)は正典から取得済みの値をそのまま使い、ここでは新たに数えない。
STANCE_GLANCE_META = {
    "義務化賛成": {
        "short": "義務化賛成", "icon": "✓", "bg": "#EAF5F3", "shadow": "rgba(47,143,131,.22)",
        "desc": "年齢で一律に運転免許を返納させるべきだとする投稿",
    },
    "条件付き賛成": {
        "short": "条件付き賛成", "icon": "△", "bg": "#FBF3DF", "shadow": "rgba(217,165,32,.22)",
        "desc": "一律の義務化ではなく、適性検査など条件を付けるべきだとする投稿",
    },
    "義務化反対": {
        "short": "義務化反対", "icon": "!", "bg": "#F2EEF7", "shadow": "rgba(125,91,166,.22)",
        "desc": "年齢だけで一律に返納させることに反対する投稿",
    },
    "中立・情報": {
        "short": "中立・情報", "icon": "?", "bg": "#F1F2F3", "shadow": "rgba(139,145,153,.22)",
        "desc": "賛否を示さず、制度の説明や情報共有にとどまる投稿",
    },
}

STANCE_GLANCE_CSS = """<style>
#stance-glance {
  width: min(1180px, 100%);
  margin: 14px auto 0;
  padding: 30px 34px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: #fff;
  box-shadow: var(--topic-shadow-sm);
  box-sizing: border-box;
}
#stance-glance .sg-lead{font-size:14.5px;line-height:1.9;margin:0 0 18px;color:var(--navy)}
#stance-glance .sg-headline{font-size:15px;font-weight:800;margin:0 0 10px;color:var(--navy)}
#stance-glance .sg-headline b{font-size:30px;font-weight:900;color:var(--blue);margin-right:2px}
#stance-glance .sg-bar-wrap{margin:0 0 24px}
@keyframes sgSegPulse{
  0%{filter:brightness(1);box-shadow:inset 0 0 0 0 rgba(255,255,255,0)}
  35%{filter:brightness(1.4);box-shadow:inset 0 0 0 3px rgba(255,255,255,.9)}
  100%{filter:brightness(1);box-shadow:inset 0 0 0 0 rgba(255,255,255,0)}
}
#stance-glance .temp-seg.sg-pulse{animation:sgSegPulse .7s ease}
@keyframes sgLegendPulse{
  0%{transform:scale(1)}
  35%{transform:scale(1.12)}
  100%{transform:scale(1)}
}
#stance-glance .temp-bar-legend span{display:inline-flex;align-items:center;border-radius:6px;
  padding:2px 4px;margin:-2px -4px;transition:background .2s ease}
#stance-glance .temp-bar-legend span.sg-pulse{animation:sgLegendPulse .5s ease;background:#F2F6FD}
#stance-glance .sg-pick-label{font-size:16px;font-weight:900;margin:0 0 4px;color:var(--navy)}
#stance-glance .sg-pick-hint{font-size:12.5px;color:var(--muted);margin:0 0 12px}
#stance-glance .sg-pick-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
#stance-glance .sg-pick-btn{position:relative;display:flex;flex-direction:column;align-items:center;
  gap:8px;border:2px solid var(--line);border-radius:14px;padding:20px 10px 16px;background:#fff;
  cursor:pointer;font-family:inherit;color:var(--navy);
  transition:border-color .18s ease,background .18s ease,transform .18s ease,box-shadow .18s ease}
#stance-glance .sg-pick-btn:hover{transform:translateY(-3px);border-color:var(--sg-color);
  box-shadow:0 10px 22px -10px rgba(16,24,40,.25)}
#stance-glance .sg-pick-btn:focus-visible{outline:2px solid var(--sg-color);outline-offset:2px}
#stance-glance .sg-pick-icon{font-size:25px;line-height:1;color:var(--sg-color)}
#stance-glance .sg-pick-name{font-size:12.5px;font-weight:800;letter-spacing:.01em}
#stance-glance .sg-pick-btn[aria-pressed="true"]{border-color:var(--sg-color);background:var(--sg-bg)}
#stance-glance .sg-pick-btn[aria-pressed="true"] .sg-pick-name{color:var(--sg-color)}
#stance-glance .sg-pick-check{position:absolute;top:-8px;right:-8px;width:20px;height:20px;
  border-radius:50%;background:var(--sg-color);color:#fff;display:none;align-items:center;
  justify-content:center;font-size:11px;font-weight:900;box-shadow:0 2px 6px rgba(16,24,40,.3)}
#stance-glance .sg-pick-btn[aria-pressed="true"] .sg-pick-check{display:flex}
#stance-glance .sg-result{margin-top:14px;padding:14px 16px;border-radius:10px;background:#F2F6FD;
  display:none}
#stance-glance .sg-result p{margin:0;font-size:14px;line-height:1.8;font-weight:700;color:var(--navy)}
#stance-glance .sg-note{margin:10px 0 0;font-size:11.5px;color:var(--muted);line-height:1.7}
@media (max-width:720px){
  #stance-glance{padding:22px 18px}
  #stance-glance .sg-pick-grid{grid-template-columns:repeat(2,1fr)}
}
</style>"""


def stance_glance(stances: list[dict], opinions: int) -> str:
    """ヒーロー直後、立場の内訳＋「まず、あなたは？」を組み立てる。

    stances は bpd.build("elderly-license-revocation")["stances"]（configs/planet/
    elderly-license-revocation.yaml の4区分に正典の件数を足したもの）をそのまま使う。
    ここで新たに集計しない。投票データへの書き込みは行わない。
    """
    support_count = next((int(s["count"]) for s in stances if s["key"] == "義務化賛成"), 0)
    conditional_count = next((int(s["count"]) for s in stances if s["key"] == "条件付き賛成"), 0)
    oppose_count = next((int(s["count"]) for s in stances if s["key"] == "義務化反対"), 0)
    ratio = support_count / oppose_count if oppose_count else 0.0
    combined_pct = 100 * (support_count + conditional_count) / opinions if opinions else 0.0
    segs, legend, buttons, js_rows = [], [], [], []
    for i, s in enumerate(stances):
        meta = STANCE_GLANCE_META[s["key"]]
        count = int(s["count"])
        share = 100 * count / opinions if opinions else 0.0
        seg_label = f"{share:.0f}%" if share >= 5 else ""
        segs.append(
            f'<div class="temp-seg" data-i="{i}" style="width:{share:.1f}%;background:{s["color"]}">{seg_label}</div>'
        )
        legend.append(
            f'<span data-i="{i}"><i style="background:{s["color"]}"></i>{html.escape(meta["short"])}<b>{count}件</b></span>'
        )
        buttons.append(
            f'<button type="button" class="sg-pick-btn" data-i="{i}" aria-pressed="false" '
            f'style="--sg-color:{s["color"]};--sg-bg:{meta["bg"]}">'
            f'<span class="sg-pick-check" aria-hidden="true">✓</span>'
            f'<span class="sg-pick-icon" aria-hidden="true">{html.escape(meta["icon"])}</span>'
            f'<span class="sg-pick-name">{html.escape(meta["short"])}</span></button>'
        )
        js_rows.append(
            "{short:%s,pct:%s,desc:%s}"
            % (
                json.dumps(meta["short"], ensure_ascii=False),
                share,
                json.dumps(meta["desc"], ensure_ascii=False),
            )
        )
    bar = (
        '<div class="temp-bar-wrap sg-bar-wrap"><div class="temp-bar-label">'
        f'<span>意見{opinions:,}件の立場別内訳</span><span>意見に占める割合</span></div>'
        f'<div class="temp-bar">{"".join(segs)}</div>'
        f'<div class="temp-bar-legend">{"".join(legend)}</div></div>'
    )
    script = f"""<script>
(function(){{
  var DATA=[{",".join(js_rows)}];
  var root=document.getElementById('stance-glance');
  var box=document.getElementById('stance-glance-buttons');
  if(!root||!box)return;
  var buttons=box.querySelectorAll('.sg-pick-btn');
  var result=document.getElementById('stance-glance-result');
  var text=document.getElementById('stance-glance-result-text');
  function pulse(i){{
    root.querySelectorAll('.sg-pulse').forEach(function(el){{el.classList.remove('sg-pulse');}});
    var seg=root.querySelector('.temp-seg[data-i="'+i+'"]');
    var leg=root.querySelector('.temp-bar-legend span[data-i="'+i+'"]');
    [seg,leg].forEach(function(el){{
      if(!el)return;
      void el.offsetWidth;
      el.classList.add('sg-pulse');
    }});
  }}
  buttons.forEach(function(btn){{
    btn.addEventListener('click',function(){{
      buttons.forEach(function(b){{b.setAttribute('aria-pressed', b===btn ? 'true' : 'false');}});
      var i=parseInt(btn.dataset.i,10);
      var d=DATA[i];
      text.textContent='「'+d.short+'」: '+d.desc+'（'+d.pct.toFixed(1)+'%）';
      result.style.display='block';
      pulse(i);
    }});
  }});
}})();
</script>"""
    return f"""{STANCE_GLANCE_START}
{STANCE_GLANCE_CSS}
<aside id="stance-glance" aria-labelledby="stance-glance-title">
<div class="panel-title"><h2 id="stance-glance-title">高齢者の免許返納義務化、賛成は反対の{ratio:.1f}倍</h2><span>義務化の是非を考える前に</span></div>
<p class="sg-lead">条件付き賛成を合わせると、義務化に肯定的な投稿は意見全体の{combined_pct:.0f}%を占めます。年齢だけでの一律義務化に反対する投稿は少数派です。</p>
<div class="sg-headline"><b>{opinions:,}</b>件の意見を、4つの立場で見た内訳です</div>
{bar}
<div class="sg-pick"><p class="sg-pick-label">気になる立場を選ぶと</p>
<p class="sg-pick-hint">どんな投稿が含まれるかを表示します</p>
<div class="sg-pick-grid" id="stance-glance-buttons">
{"".join(buttons)}
</div>
<div class="sg-result" id="stance-glance-result" aria-live="polite"><p id="stance-glance-result-text"></p></div>
<p class="sg-note">※ この選択はあくまで確認用で、投票データには残りません。投票への参加はページ下部からどうぞ。</p>
</div>
</aside>
{script}
{STANCE_GLANCE_END}"""


def apply_elderly_stance_glance(page: str) -> str:
    """ヒーロー直後に、立場の内訳＋「まず、あなたは？」を貼り直す。

    build()は候補生成中の正典行から、apply_public_counts()は昇格後の公開JSONから、
    それぞれ独立にHTMLを書き換える（このファイル固有の二経路構造）。件数の集計を
    どちらか一方の呼び出し元に合わせて作ると、もう一方の経路で古い値のまま残る。
    bpd.build()で公開JSONベースの値を読み直せば、どちらの経路から呼ばれても
    同じ関数で済む（bukatsu-chiikiの後付け補完処理と同じ型）。
    build()の候補生成時点では公開JSONがまだ前回分のままで件数が古いが、
    apply_public_counts()側の貼り直しで正しい値に揃う
    （elderly.pyのfinalize()コメント「昇格してからadapterに貼り直させる」と同じ前提）。
    """
    if __package__:
        from .build_planet_page_preview import bpd
    else:  # python3 scripts/build_elderly_arena.py
        from build_planet_page_preview import bpd  # type: ignore[no-redef]

    data = bpd.build(THEME)
    opinions = int(data["totals"]["opinions"])
    stances = data["stances"]

    if STANCE_GLANCE_START in page and STANCE_GLANCE_END in page:
        start = page.index(STANCE_GLANCE_START)
        end = page.index(STANCE_GLANCE_END) + len(STANCE_GLANCE_END)
        page = page[:start] + page[end:]
        # 外したあと・貼る前の空行を2行に揃える(揃えないと貼り直しのたびに
        # 空行が増え、adapterの冪等性検査が通らない)。
        page = re.sub(r"\n\s*\n+(<!-- RESEARCH_CONDITIONS_START -->)", r"\n\n\1", page)
    block = stance_glance(stances, opinions)
    idx = page.index(STANCE_GLANCE_ANCHOR)
    page = page[:idx] + block + "\n\n" + page[idx:]

    if page.count(STANCE_GLANCE_START) != 1 or page.count(STANCE_GLANCE_END) != 1:
        raise IssueCountError("内訳セクションのマーカーが1組でない")
    if '<h2 id="stance-glance-title">' not in page:
        raise IssueCountError("内訳セクションの見出しがページにない")
    check_block = page[page.index(STANCE_GLANCE_START):page.index(STANCE_GLANCE_END)]
    seg_count = check_block.count('<div class="temp-seg"')
    btn_count = check_block.count('class="sg-pick-btn"')
    if seg_count != len(stances):
        raise IssueCountError(f"内訳バーの区画が{len(stances)}個でない: {seg_count}個")
    if btn_count != len(stances):
        raise IssueCountError(f"「あなたは？」ボタンが{len(stances)}個でない: {btn_count}個")
    if page.index(STANCE_GLANCE_START) > page.index(STANCE_GLANCE_ANCHOR):
        raise IssueCountError("内訳セクションが調査条件より後ろにある(ヒーロー直後に置くこと)")
    if '<aside id="stance-glance"' not in page:
        raise IssueCountError(
            "内訳セクションがasideでなくなっている"
            "(sectionにするとpanel:nth-of-type(even)の縞模様が後続セクション全部でずれる)"
        )
    return page


def build(
    *,
    check: bool = False,
    input_path: Path | None = None,
    html_template: Path | None = None,
    output_html: Path | None = None,
) -> tuple[list[str], bool]:
    rows, sample_file, collected = load_opinions(input_path)
    counts = Counter(str(classification(row)["main_issue"]) for row in rows)
    public_path = ROOT / "docs" / f"{THEME}-reaction-map.html"
    template = html_template or public_path
    destination = output_html or public_path
    before = template.read_text(encoding="utf-8")
    page = before
    # 山なみ差し替え後の落とし穴は apply_public_counts() と同じ3か所
    # （課題54: 高齢者段階1。詳しい理由はそちらのコメントを参照）。
    planet_mode = "<!-- PLANET_SECTION_START -->" in page

    page = replace_once(page, r"const SM_RAW = \[.*?\n\];", build_sm_raw(rows), "SM_RAW", flags=re.S)
    page = replace_once(page, r"const ISSUES=\[.*?\n  \];", build_issues(), "ISSUES", flags=re.S)
    count_line = "  SM_RAW.forEach(p=>{if(ISSUES[p.i])ISSUES[p.i].n+=1;});\n"
    if count_line not in page:
        page = replace_once(page, r"  const total=ISSUES\.reduce", count_line + "  const total=ISSUES.reduce", "SM_RAWからの件数集計")
    if not planet_mode:
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
    if not planet_mode:
        # 「論点別サマリー」「スタンス集計」は山なみ側の内容と重複するため
        # build_generic() が削除する（2026-09-11、高齢者段階2で発見）。
        page = replace_once(page, r'<section class="stats insight-stats".*?</section>', build_stats(rows, collected), "注目ポイント", flags=re.S)
        page = replace_once(page, r'<section class="panel" id="issue-blocks-section">.*?</section>', build_issue_blocks(rows), "論点別サマリー", flags=re.S)
        page = replace_once(page, r'<section class="panel conflict-panel">.*?</section>', build_stance_summary(rows), "スタンス集計", flags=re.S)
    page = replace_once(page, r'<section class="panel details-panel" id="detail-data">.*?</section>', build_details(rows), "詳細データ", flags=re.S)
    page = apply_elderly_stance_glance(page)

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
