#!/usr/bin/env python3
"""Rule-based first pass classifier for constitutional amendment reactions."""

from __future__ import annotations

import argparse
import json
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CATEGORY_ORDER = [
    "改憲賛成・推進",
    "改憲反対・護憲",
    "9条・自衛隊明記に賛成",
    "9条・自衛隊明記に反対",
    "緊急事態条項に賛成",
    "緊急事態条項に反対",
    "国民投票法・広告規制を重視",
    "手続き・発議可能性への関心",
    "政党・議員批判",
    "事実確認・情報共有",
    "未確認・過激表現",
    "その他・分類保留",
]


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def clean_text(text: str) -> str:
    return " ".join(str(text or "").replace("\n", " ").split())


def contains_any(text: str, markers: list[str]) -> bool:
    return any(marker in text for marker in markers)


def classify(row: dict[str, Any]) -> dict[str, Any]:
    text = clean_text(row.get("text", ""))
    query = str(row.get("query") or "")

    extreme = ["売国", "反日", "独裁", "ナチ", "死ね", "滅びろ", "陰謀", "DS", "工作員"]
    if contains_any(text, extreme):
        return result("未確認・過激表現", "未確認", "強い断定や攻撃的表現があり、記事化には中和・確認が必要。", "過激・未確認表現を含むため。", 0.7, False, "high")

    referendum = ["国民投票法", "広告規制", "CM規制", "ネット広告", "外国人寄付", "運動資金", "公平性"]
    if contains_any(text, referendum):
        return result("国民投票法・広告規制を重視", "手続き重視", "国民投票時の広告・資金・情報環境の整備を重視する意見。", "国民投票法や広告規制への言及が中心のため。", 0.84, True, "low")

    emergency = ["緊急事態条項", "緊急事態", "議員任期延長"]
    emergency_oppose = ["反対", "危険", "独裁", "不要", "いらない", "権限集中", "人権制限", "ナチ", "白紙委任"]
    emergency_support = ["必要", "賛成", "備え", "災害", "有事", "国会機能", "任期延長すべき"]
    if contains_any(text, emergency):
        if contains_any(text, emergency_oppose):
            return result("緊急事態条項に反対", "改憲反対", "緊急事態条項は権限集中や人権制限につながるとして反対する意見。", "緊急事態条項への反対・危険視が主眼のため。", 0.86, True, "medium")
        if contains_any(text, emergency_support):
            return result("緊急事態条項に賛成", "改憲支持", "災害や有事に備えるため緊急事態条項が必要だとする意見。", "緊急事態条項の必要性を述べているため。", 0.82, True, "low")
        return result("緊急事態条項に反対", "慎重", "緊急事態条項を警戒・問題視する反応。", "検索語と本文から緊急事態条項への警戒が中心と判断。", 0.68, True, "medium")

    article9 = ["9条", "憲法9条", "自衛隊", "自衛隊明記", "明記"]
    article9_oppose = ["反対", "壊す", "戦争", "軍国", "違憲", "空文化", "専守防衛", "改悪", "守れ", "平和憲法"]
    article9_support = ["明記すべき", "明記", "違憲論争", "合憲", "必要", "賛成", "国防", "防衛", "現実に合わせる"]
    if contains_any(text, article9) or contains_any(query, article9):
        if contains_any(text, article9_oppose) and not contains_any(text, ["違憲論争を終わら"]):
            return result("9条・自衛隊明記に反対", "改憲反対", "9条改正や自衛隊明記が平和主義の後退につながると見る意見。", "9条改正・自衛隊明記への反対や警戒が中心のため。", 0.82, True, "medium")
        if contains_any(text, article9_support):
            return result("9条・自衛隊明記に賛成", "改憲支持", "自衛隊の存在や国防の現実を憲法に明記すべきだとする意見。", "自衛隊明記や国防上の必要性を述べているため。", 0.8, True, "low")

    oppose = ["改憲反対", "憲法改正反対", "護憲", "改憲阻止", "憲法を守", "改悪", "自民党改憲案に反対", "憲法を変えるな"]
    support = ["改憲賛成", "憲法改正賛成", "改憲すべき", "憲法改正すべき", "自主憲法", "新憲法", "憲法を変えるべき"]
    if contains_any(text, oppose):
        return result("改憲反対・護憲", "改憲反対", "憲法改正に反対し、現行憲法の維持や護憲を求める意見。", "改憲反対・護憲の表現が明示されているため。", 0.86, True, "low")
    if contains_any(text, support):
        return result("改憲賛成・推進", "改憲支持", "憲法改正そのものを進めるべきだとする意見。", "改憲賛成・推進の表現が明示されているため。", 0.84, True, "low")

    procedure = ["3分の2", "発議", "国会", "憲法審査会", "国民投票", "参院選", "議席", "公約"]
    if contains_any(text, procedure):
        return result("手続き・発議可能性への関心", "手続き重視", "改憲発議や国民投票、議席数など手続き面に関心を向ける反応。", "発議・国会・国民投票など手続きへの言及が中心のため。", 0.74, True, "low")

    party = ["自民", "立憲", "維新", "国民民主", "公明", "共産", "れいわ", "参政党", "社民", "議員", "政党"]
    if contains_any(text, party):
        return result("政党・議員批判", "その他", "憲法改正をめぐる政党や議員の姿勢を批判・評価する反応。", "政党・議員への言及が中心のため。", 0.68, True, "medium")

    if len(text) < 80 or text.startswith("http") or "YouTube" in text:
        return result("事実確認・情報共有", "中立", "憲法改正に関する記事・動画・情報を共有する反応。", "明確な賛否より情報共有が中心のため。", 0.62, False, "low")

    return result("その他・分類保留", "その他", "明確な賛否や主論点を判定しにくい反応。", "短文・複数論点・文脈不足のため。", 0.45, False, "medium")


def result(category: str, stance: str, summary: str, reason: str, confidence: float, article_usable: bool, risk: str) -> dict[str, Any]:
    return {
        "category": category,
        "stance": stance,
        "summary": summary,
        "reason": reason,
        "confidence": confidence,
        "article_usable": article_usable,
        "risk": risk,
    }


def write_markdown(rows: list[dict[str, Any]], output: Path) -> None:
    buckets: OrderedDict[str, list[dict[str, Any]]] = OrderedDict((category, []) for category in CATEGORY_ORDER)
    for row in rows:
        buckets.setdefault(row["classification"]["category"], []).append(row)
    lines = ["# 憲法改正論議 X反応 分類結果", "", f"総件数: {len(rows)}", "", "## 分類件数", "", "| 分類 | 件数 |", "| --- | ---: |"]
    for category, items in buckets.items():
        lines.append(f"| {category} | {len(items)} |")
    lines += ["", "## 賛成・反対の主な抽出", ""]
    for category, items in buckets.items():
        lines += [f"## {category}", "", f"{len(items)}件", ""]
        for index, row in enumerate(items[:10], 1):
            c = row["classification"]
            text = clean_text(row.get("text", ""))
            lines += [
                f"{index}. {c['summary']}",
                f"   - stance: {c['stance']} / confidence: {c['confidence']:.2f} / risk: {c['risk']}",
                f"   - 理由: {c['reason']}",
                f"   - 投稿要旨: {text[:260]}",
                f"   - URL: {row.get('url', '')}",
                "",
            ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify constitutional amendment reactions by rules")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--markdown", default="")
    args = parser.parse_args()

    rows = json.loads(resolve(args.input).read_text(encoding="utf-8"))
    classified = []
    for row in rows:
        new_row = dict(row)
        new_row["text"] = clean_text(row.get("text", ""))
        new_row["classification"] = classify(new_row)
        classified.append(new_row)

    output = resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(classified, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown:
        write_markdown(classified, resolve(args.markdown))
    counts = Counter(row["classification"]["category"] for row in classified)
    print(f"saved={output} rows={len(classified)}")
    for category, count in counts.most_common():
        print(f"{category}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
