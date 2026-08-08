#!/usr/bin/env python3
"""憲法改正ページを正典の「意見」だけから再生成する。

入力は THEMES.yaml に記載した正典だけ。マップ、論点別の声、スタンス集計、
詳細表、論点カードの件数を同じ意見集合から作る。

    python3 scripts/build_constitutional_arena.py
    python3 scripts/build_constitutional_arena.py --check
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

import yaml

try:
    from .issue_card_counts import IssueCountError, span_html
except ImportError:
    from issue_card_counts import IssueCountError, span_html  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parent.parent
THEME = "constitutional-amendment"
PAGE = ROOT / "docs" / "constitutional-amendment-reaction-map.html"
CONFIG = ROOT / "configs" / "constitutional-amendment-reaction-map.json"

# 先頭6件は投票 choiceIdx と論点カードの順序なので固定する。「その他」は投票対象に
# 加えないが、正典の main_issue を改変せずマップと詳細集計へ含める。
ISSUES = [
    ("改憲全般", "憲法を時代に合わせるべきか、現行憲法の原則を守るべきか。"),
    ("9条・自衛隊", "自衛隊を憲法に明記する意義と、9条の平和主義への影響。"),
    ("緊急事態条項", "災害などへの迅速な対応と、政府への権限集中リスク。"),
    ("国民投票・広告", "CM・ネット広告・資金力の差を含む国民投票の公平性。"),
    ("政党・発議手続き", "政党の姿勢、国会での合意形成、発議までの進め方。"),
    ("情報・議論の質", "事実確認、過激な断定、論点を理解できる情報環境。"),
    ("その他", "主要6論点に収まらない憲法改正に関する意見。"),
]
ISSUE_INDEX = {name: idx for idx, (name, _) in enumerate(ISSUES)}

STANCES = ("慎重・反対", "中立", "手続き重視", "改正推進")
STANCE_KEY = {
    "慎重・反対": "con",
    "中立": "neutral",
    "手続き重視": "process",
    "改正推進": "pro",
}
STANCE_COLORS = {
    "慎重・反対": "#dc2626",
    "中立": "#64748b",
    "手続き重視": "#059669",
    "改正推進": "#2563eb",
}
INTENSITY = {"low": 0.34, "medium": 0.66, "high": 0.94}


def classification(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("classification")
    return value if isinstance(value, dict) else {}


def load_canon() -> tuple[list[dict[str, Any]], int, str]:
    themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
    sample_file = str(themes[THEME]["sample_file"])
    if "synthetic" in sample_file:
        raise IssueCountError(f"合成データは正典にできません: {sample_file}")
    records = json.loads((ROOT / sample_file).read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise IssueCountError(f"正典が空、またはJSON配列ではありません: {sample_file}")

    missing_opinion = [r for r in records if "is_opinion" not in classification(r)]
    if missing_opinion:
        raise IssueCountError(
            f"is_opinion を持たないレコードがあります（{len(missing_opinion)}件）: {sample_file}"
        )
    rows = [r for r in records if classification(r).get("is_opinion") is True]
    if not rows:
        raise IssueCountError("意見と判定されたレコードが0件です")

    missing_issue = [r for r in rows if classification(r).get("main_issue") not in ISSUE_INDEX]
    if missing_issue:
        values = Counter(str(classification(r).get("main_issue")) for r in missing_issue)
        raise IssueCountError(f"未知または未設定の main_issue があります: {dict(values)}")
    missing_stance = [r for r in rows if classification(r).get("stance") not in STANCE_KEY]
    if missing_stance:
        values = Counter(str(classification(r).get("stance")) for r in missing_stance)
        raise IssueCountError(f"未知または未設定の stance があります: {dict(values)}")
    return rows, len(records), sample_file


def js_string(value: object) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False)


def build_map_data(rows: list[dict[str, Any]]) -> str:
    issue_lines = [f"  {{k:{js_string(name)},n:0}}" for name, _ in ISSUES]
    point_lines = []
    for row in rows:
        value = classification(row)
        point_lines.append(
            "  {i:%d,t:%.2f,s:%s,u:%s,k:%s}"
            % (
                ISSUE_INDEX[str(value["main_issue"])],
                INTENSITY.get(str(value.get("intensity")), 0.66),
                js_string(str(value.get("summary") or "")[:120]),
                js_string(row.get("url") or ""),
                js_string(STANCE_KEY[str(value["stance"])]),
            )
        )
    return (
        "const ISSUES=[\n" + ",\n".join(issue_lines) + "\n];\n"
        "const SM_RAW = [\n" + ",\n".join(point_lines) + "\n];\n"
        "SM_RAW.forEach(p=>{if(ISSUES[p.i])ISSUES[p.i].n+=1;});\n"
    )


def sample_cards(rows: list[dict[str, Any]], issue: str) -> str:
    candidates = [
        r for r in rows
        if classification(r)["main_issue"] == issue
        and r.get("url")
        and classification(r).get("article_usable", True)
        and classification(r).get("risk", "low") != "high"
    ]
    candidates.sort(key=lambda r: -float(classification(r).get("confidence") or 0))
    picked: list[dict[str, Any]] = []
    used: set[str] = set()
    for stance in STANCES:
        for row in candidates:
            url = str(row["url"])
            if classification(row)["stance"] == stance and url not in used:
                picked.append(row)
                used.add(url)
                break
        if len(picked) == 2:
            break
    for row in candidates:
        if len(picked) == 2:
            break
        if str(row["url"]) not in used:
            picked.append(row)
            used.add(str(row["url"]))

    return "".join(
        '<div class="sample-card"><div class="meta">{stance} / conf {confidence:.2g}</div>'
        '<p>{summary}</p><blockquote class="twitter-tweet" data-conversation="none" '
        'data-dnt="true"><a href="{url}"></a></blockquote></div>'.format(
            stance=html.escape(str(classification(row)["stance"])),
            confidence=float(classification(row).get("confidence") or 0),
            summary=html.escape(str(classification(row).get("summary") or "")),
            url=html.escape(str(row["url"]), quote=True),
        )
        for row in picked
    )


def build_issue_section(rows: list[dict[str, Any]]) -> str:
    blocks = []
    for idx, (issue, desc) in enumerate(ISSUES[:6], start=1):
        subset = [r for r in rows if classification(r)["main_issue"] == issue]
        counts = Counter(str(classification(r)["stance"]) for r in subset)
        total = len(subset)
        segments = []
        legends = []
        for stance in STANCES:
            count = counts[stance]
            if not count:
                continue
            pct = count / total * 100
            label = f"{round(pct)}%" if pct >= 7 else ""
            key = STANCE_KEY[stance]
            segments.append(
                f'<div class="temp-seg {key}" style="width:{pct:.2f}%">{label}</div>'
            )
            legends.append(
                f'<span><i class="{key}"></i>{html.escape(stance)}（{count}件）</span>'
            )
        blocks.append(
            f'<article class="issue-block" id="issue-{idx - 1}">'
            f'<div class="issue-head"><span class="axis-kicker">論点 {idx}</span>'
            f'<h3>{html.escape(issue)}<span class="issue-count">{total}件</span></h3></div>'
            f'<p class="issue-desc">{html.escape(desc)}</p>'
            '<div class="temp-bar-wrap"><div class="temp-bar-label">'
            f'<span>X投稿のスタンス構成</span><span>合計 {total}件</span></div>'
            f'<div class="temp-bar">{"".join(segments)}</div>'
            f'<div class="temp-bar-legend">{"".join(legends)}</div></div>'
            f'<div class="sample-grid">{sample_cards(rows, issue)}</div></article>'
        )
    other = sum(1 for r in rows if classification(r)["main_issue"] == "その他")
    return (
        '<section class="panel conflict-panel"><div class="panel-title">'
        '<h2>6つの論点とXの声</h2><span>論点ごとに立場を読み比べる</span></div>'
        + "".join(blocks)
        + f'<p class="data-method">主要6論点のほか「その他」{other}件も、マップと詳細集計には含めています。</p>'
        + "</section>"
    )


def build_insights(rows: list[dict[str, Any]], collected: int) -> str:
    issues = Counter(str(classification(r)["main_issue"]) for r in rows)
    stances = Counter(str(classification(r)["stance"]) for r in rows)
    total = len(rows)
    top_issue, top_issue_count = issues.most_common(1)[0]
    top_stance, top_stance_count = stances.most_common(1)[0]
    opinion_pct = round(total / collected * 100)
    return f'''<section class="stats insight-stats" aria-label="このテーマの4つの注目ポイント">
      <article class="stat insight-stat">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">🗣️</span><span class="insight-label">分析対象の意見</span></div>
        <strong class="insight-value">{total}<small>件</small></strong>
        <p class="insight-note">収集した{collected}件のうち意見と判定した投稿</p>
        <div class="insight-meter" aria-hidden="true"><i style="width:{opinion_pct}%"></i></div>
      </article>
      <article class="stat insight-stat" data-tone="debate">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">⚖️</span><span class="insight-label">最も多い立場</span></div>
        <strong class="insight-value">{html.escape(top_stance)} {round(top_stance_count / total * 100)}%</strong>
        <p class="insight-note">{top_stance_count}件。4つの立場を同じ意見{total}件から集計</p>
        <div class="insight-meter" aria-hidden="true"><i style="width:{round(top_stance_count / total * 100)}%"></i></div>
      </article>
      <article class="stat insight-stat" data-tone="topic">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">🔥</span><span class="insight-label">最も話された論点</span></div>
        <strong class="insight-value">{html.escape(top_issue)} {top_issue_count}<small>件</small></strong>
        <p class="insight-note">正典の main_issue をそのまま集計</p>
        <div class="insight-meter" aria-hidden="true"><i style="width:{round(top_issue_count / total * 100)}%"></i></div>
      </article>
      <article class="stat insight-stat" data-tone="insight">
        <div class="insight-head"><span class="insight-icon" aria-hidden="true">💬</span><span class="insight-label">意見と情報共有</span></div>
        <div class="insight-versus"><span>意見<b>{total}</b></span><em>VS</em><span>情報共有<b>{collected-total}</b></span></div>
        <p class="insight-note">マップ・論点・賛否は意見だけを対象</p>
      </article>
    </section>'''


def build_details(rows: list[dict[str, Any]]) -> str:
    issues = Counter(str(classification(r)["main_issue"]) for r in rows)
    stances = Counter(str(classification(r)["stance"]) for r in rows)
    intensities = Counter(str(classification(r).get("intensity") or "未設定") for r in rows)
    total = len(rows)

    def table(counter: Counter[str], order: list[str]) -> str:
        body = "".join(
            f"<tr><th>{html.escape(label)}</th><td>{counter[label]}</td></tr>" for label in order
        )
        return (
            f'<div class="table-wrap"><table><tbody>{body}'
            f'<tr><th style="font-weight:900">合計</th><td style="font-weight:900">{total}</td>'
            "</tr></tbody></table></div>"
        )

    issue_table = table(issues, [name for name, _ in ISSUES])
    stance_table = table(stances, list(STANCES))
    intensity_table = table(intensities, ["high", "medium", "low"])
    return (
        '<section class="panel details-panel" id="detail-data">'
        '<div class="panel-title"><h2>詳細データ</h2><span>必要な人向けに折りたたみ</span></div>'
        f'<details open><summary>論点別件数（main_issue）</summary>{issue_table}</details>'
        f'<details><summary>改正への態度（stance）</summary>{stance_table}</details>'
        f'<details><summary>感情の強さ（intensity）</summary>{intensity_table}</details>'
        f'<details><summary>件数の出所</summary><p>ページ上の件数はすべて正典の意見{total}件から'
        ' scripts/build_constitutional_arena.py が生成しています。</p></details></section>'
    )


def replace_once(source: str, pattern: str, replacement: str, label: str, *, flags: int = 0) -> str:
    updated, count = re.subn(pattern, lambda _: replacement, source, count=1, flags=flags)
    if count != 1:
        raise IssueCountError(f"{label}: 1箇所だけ一致する必要があります（{count}箇所）")
    return updated


def build(*, check: bool = False) -> tuple[list[str], bool]:
    rows, collected, sample_file = load_canon()
    total = len(rows)
    issue_counts = Counter(str(classification(r)["main_issue"]) for r in rows)
    stance_counts = Counter(str(classification(r)["stance"]) for r in rows)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    before = PAGE.read_text(encoding="utf-8")
    page = before

    lead = (
        f'<p class="lead">Yahooリアルタイム検索で取得した公開投稿{collected}件のうち、'
        f'意見と判定した{total}件を分析対象としています。AIが主要6論点とその他に整理しました。'
        '世論調査ではなく、SNS反応サンプルの論点比較です。</p>'
    )
    page = replace_once(page, r'<p class="lead">.*?</p>', lead, "ヒーローの母数表記", flags=re.S)
    page = replace_once(
        page,
        r'<span class="conclusion-count"><b>\d+</b>件</span>',
        f'<span class="conclusion-count"><b>{issue_counts["改憲全般"]}</b>件</span>',
        "議論の中心",
    )
    research = (
        '<!-- RESEARCH_CONDITIONS_START -->\n'
        '<aside class="research-conditions" aria-label="SNSデータの調査条件" '
        'style="padding:16px min(6vw,72px);background:#fff;border-bottom:1px solid var(--line);'
        'font-size:13px;line-height:1.8;color:var(--muted);">\n'
        '<p style="max-width:1000px;margin:0 auto;"><strong style="color:var(--ink);">'
        f'このマップの元データ:</strong> Yahooリアルタイム検索で取得した公開投稿 {collected}件のうち、'
        f'意見と判定した{total}件を分析対象としています。<br>\n'
        '  （取得期間: 2026-06-20〜2026-07-25／AI分類・人間による代表投稿の確認あり）<br>\n'
        '  <strong>社会全体の世論調査ではありません。</strong></p>\n'
        '</aside>\n<!-- RESEARCH_CONDITIONS_END -->'
    )
    page = replace_once(
        page,
        r'<!-- RESEARCH_CONDITIONS_START -->.*?<!-- RESEARCH_CONDITIONS_END -->',
        research,
        "調査条件",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<section class="stats insight-stats".*?</section>',
        build_insights(rows, collected),
        "注目ポイント",
        flags=re.S,
    )
    trust_method = (
        '<div class="article-trust-method">\n'
        '    <h3>SNS投稿の収集方法</h3>\n'
        f'    <p>Yahooリアルタイム検索で取得した公開投稿{collected}件のうち、意見と判定した'
        f'{total}件を、マップ・論点・賛否の分析対象としています。</p>\n'
        '    <h3>AIを使用した工程</h3>\n'
        '    <p>収集後の投稿について、AIを関連性・意見性の判定、論点・立場・表現強度の分類、'
        '要旨作成の補助に使用しています。ページ内にAI生成の図解・漫画がある場合は、その制作補助にも'
        '使用しています。AIによる分類には誤りや偏りが含まれる可能性があります。</p>\n'
        '  </div>'
    )
    page = replace_once(
        page,
        r'<div class="article-trust-method">.*?</div>',
        trust_method,
        "収集方法",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<div class="panel-title"><h2>SNS反応マップ</h2><span>.*?</span></div>',
        f'<div class="panel-title"><h2>SNS反応マップ</h2><span>意見{total}件 | セクター=main_issue / '
        '中心に近いほど冷静 / 色=立場 | ホバーで詳細・クリックでXへ</span></div>',
        "マップ見出し",
    )
    page = replace_once(
        page,
        r'const ISSUES=.*?(?=const colors=)',
        build_map_data(rows),
        "SM_RAW と ISSUES",
        flags=re.S,
    )
    page = page.replace("P.forEach((p,j)=>", "SM_RAW.forEach((p,j)=>")
    if "main_issue の小セクター同士でラベルが重ならないよう離す" not in page:
        page = replace_once(
            page,
            r"    const rad=v\.mid\*Math\.PI/180,lx=CX\+R_LBL\*Math\.cos\(rad\),ly=CY\+R_LBL\*Math\.sin\(rad\),c=Math\.cos\(rad\);",
            "    const rad=v.mid*Math.PI/180,lx=CX+R_LBL*Math.cos(rad),c=Math.cos(rad);\n"
            "    let ly=CY+R_LBL*Math.sin(rad);\n"
            "    // main_issue の小セクター同士でラベルが重ならないよう離す\n"
            "    if(i===5)ly-=18;if(i===6)ly+=18;",
            "マップのラベル衝突回避",
        )
    page = replace_once(
        page,
        r'<section class="panel conflict-panel">.*?(?=<section class="panel background-panel">)',
        build_issue_section(rows) + "\n",
        "論点別の声",
        flags=re.S,
    )
    page = replace_once(
        page,
        r'<section class="panel details-panel" id="detail-data">.*?</section>',
        build_details(rows),
        "詳細データ",
        flags=re.S,
    )

    # 6枚のカード順は投票 choiceIdx と同じなので変更せず、件数だけ正典から更新する。
    cards = config["issue_counts"]["cards"]
    if len(cards) != 6:
        raise IssueCountError(f"論点カードは6枚である必要があります: {len(cards)}枚")
    for card in cards:
        count = sum(issue_counts[str(issue)] for issue in card["main_issue"])
        page = replace_once(
            page,
            rf'<span class="explainer-count" id="issue-count-{THEME}-{card["slug"]}">\d+件</span>',
            span_html(THEME, str(card["slug"]), count),
            f'論点カード {card["slug"]}',
        )

    if page.count("const SM_RAW = [") != 1 or page.count("SM_RAW.forEach(p=>") != 1:
        raise IssueCountError("SM_RAW の生成ブロックが1箇所ではありません")
    if sum(issue_counts.values()) != total or sum(stance_counts.values()) != total:
        raise IssueCountError("論点またはスタンスの合計が意見件数と一致しません")

    changed = page != before
    if changed and not check:
        PAGE.write_text(page, encoding="utf-8")
    lines = [
        f"出所: {sample_file}（収集{collected}件 → 意見{total}件）",
        "論点: " + " / ".join(f"{name}={issue_counts[name]}" for name, _ in ISSUES),
        "賛否: " + " / ".join(f"{stance}={stance_counts[stance]}" for stance in STANCES),
        f"マップ: {total}点 / 論点カード: {len(cards)}枚 / スタンス: {len(STANCES)}種",
    ]
    return lines, changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="書き換えず、差分があれば exit 1")
    args = parser.parse_args()
    try:
        lines, changed = build(check=args.check)
    except (IssueCountError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("\n".join(lines))
    print("UPDATE" if changed else "OK")
    if args.check and changed:
        print("NG  ページが正典から生成した内容と一致しません", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
