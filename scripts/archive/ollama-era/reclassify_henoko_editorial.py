#!/usr/bin/env python3
"""Editorial reclassification for Henoko reaction samples.

Splits ambiguous education-law categories into clearer sides:
- 文科省判断支持・政治的中立性違反を指摘
- 文科省判断への反発・平和教育萎縮を懸念
"""

from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CATEGORIES = [
    "文科省判断支持・政治的中立性違反を指摘",
    "文科省判断への反発・平和教育萎縮を懸念",
    "安全管理・引率責任を問題視",
    "学校・教育委員会批判",
    "追悼・慰霊への共感",
    "政治利用・反基地運動批判",
    "事故原因・再発防止への関心",
    "報道・行政対応批判",
    "基地問題・反基地論への接続",
    "事実確認・情報共有",
    "未確認・過激表現",
    "その他・分類保留",
]


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def has_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def classify(row: dict) -> dict:
    old = row.get("classification") or {}
    text = row.get("text", "")
    combined = " ".join([text, old.get("summary", ""), old.get("reason", "")])

    anti_mext_markers = [
        "萎縮",
        "学ぶ機会を奪わないで",
        "米軍基地でのエアガン射撃訓練",
        "エアガン射撃訓練",
        "教育の｢中立性｣を定めた法に抵触",
        "教育の「中立性」を定めた法に抵触",
        "教育基本法に違反とはならないのか",
        "文科省が教育内容を教育基本法違反としたことは疑問",
        "違法認定は政治色",
        "文科省の違法認定に残る大きな疑問",
        "平和教育が委縮",
        "平和教育が萎縮",
        "踏み込みすぎ",
        "教育現場の萎縮",
        "撤回求める",
        "恣意的",
        "平和活動萎縮",
    ]
    mext_support_markers = [
        "何が萎縮させる危険",
        "寧ろ萎縮しろ",
        "明白な教育基本法違反",
        "どう考えても政治的中立性違反",
        "政治的中立性違反",
        "教育基本法第14条2項",
        "特定の政治活動に加担",
        "反基地教育",
        "偏向教育",
        "教育基本法違反なのに",
        "文科省の報告書を読め",
        "文科省は“教育基本法“違反だと断罪",
        "文科省判断",
    ]
    safety_markers = [
        "安全管理",
        "再発防止",
        "引率",
        "危険な現場",
        "危険性",
        "救助",
        "捜索",
        "転覆",
        "船長",
        "死亡事故",
    ]
    memorial_markers = ["偲ぶ会", "追悼", "慰霊", "黙祷", "亡くなった", "死を偲ぶ"]
    political_use_markers = ["政治利用", "反基地運動に利用", "活動家", "反基地活動家", "国外追放"]
    media_admin_markers = ["NHK", "マスコミ", "報道", "文春", "行政", "知事", "玉城デニー"]
    uncertainty_markers = ["闇", "陰謀", "断罪", "外国人犯罪者", "排除", "殺した"]

    new = dict(old)

    if has_any(combined, mext_support_markers):
        new.update(
            {
                "category": "文科省判断支持・政治的中立性違反を指摘",
                "stance": "文科省支持",
                "summary": "学校教育で特定の政治活動に関わらせたとして、政治的中立性違反を指摘する反応。",
                "reason": "教育基本法違反認定や政治的中立性違反を支持・主張しているため。",
                "confidence": max(float(old.get("confidence") or 0.0), 0.84),
                "article_usable": True,
                "risk": old.get("risk") if old.get("risk") in {"none", "low", "medium", "high"} else "low",
            }
        )
    elif has_any(combined, anti_mext_markers):
        new.update(
            {
                "category": "文科省判断への反発・平和教育萎縮を懸念",
                "stance": "反発",
                "summary": "文科省の教育基本法違反認定が行きすぎで、平和教育の萎縮につながると懸念する反応。",
                "reason": "文科省判断への疑問、教育現場や平和教育の萎縮懸念を示しているため。",
                "confidence": max(float(old.get("confidence") or 0.0), 0.82),
                "article_usable": True,
                "risk": old.get("risk") if old.get("risk") in {"none", "low", "medium", "high"} else "low",
            }
        )
    elif has_any(combined, political_use_markers):
        new.update(
            {
                "category": "政治利用・反基地運動批判",
                "stance": "批判",
                "summary": "死亡事故や高校生を政治運動に利用しているのではないかと批判する反応。",
                "reason": "政治利用や反基地運動側への批判が主眼のため。",
                "confidence": max(float(old.get("confidence") or 0.0), 0.78),
                "article_usable": old.get("risk") != "high",
            }
        )
    elif (
        has_any(combined, safety_markers)
        and not has_any(combined, ["教育基本法", "政治的中立性", "中立性"])
        and old.get("category") in {
        "事故原因・安全管理への関心",
        "学校・教育委員会批判",
        "その他・分類保留",
        "事実確認・情報共有",
        }
    ):
        new.update(
            {
                "category": "安全管理・引率責任を問題視",
                "stance": "批判",
                "summary": "未成年を危険な現場に連れて行った安全管理や引率責任を問う反応。",
                "reason": "事故原因、安全管理、引率責任が主眼のため。",
                "confidence": max(float(old.get("confidence") or 0.0), 0.76),
                "article_usable": True,
            }
        )
    elif has_any(combined, memorial_markers) and old.get("category") in {
        "追悼・慰霊への共感",
        "その他・分類保留",
        "事実確認・情報共有",
    }:
        new.update(
            {
                "category": "追悼・慰霊への共感",
                "stance": "追悼支持",
                "summary": "亡くなった高校生への追悼や慰霊に触れる反応。",
                "reason": "追悼・慰霊・黙祷が主眼のため。",
                "confidence": max(float(old.get("confidence") or 0.0), 0.72),
                "article_usable": True,
            }
        )
    elif has_any(combined, media_admin_markers) and old.get("category") in {
        "報道・行政対応批判",
        "その他・分類保留",
        "学校・教育委員会批判",
    }:
        new.update(
            {
                "category": "報道・行政対応批判",
                "stance": "批判",
                "summary": "報道機関、行政、政治家の対応を批判する反応。",
                "reason": "報道・行政対応への批判が中心のため。",
                "confidence": max(float(old.get("confidence") or 0.0), 0.72),
                "article_usable": old.get("risk") != "high",
            }
        )
    elif has_any(combined, uncertainty_markers) or old.get("category") == "未確認・過激表現":
        new.update(
            {
                "category": "未確認・過激表現",
                "stance": "未確認",
                "summary": old.get("summary") or "根拠確認が必要な強い断定や過激表現を含む反応。",
                "reason": "未確認情報や過激表現を含むため。",
                "confidence": max(float(old.get("confidence") or 0.0), 0.70),
                "article_usable": False,
                "risk": "high" if old.get("risk") == "high" else "medium",
            }
        )
    else:
        mapping = {
            "教育基本法違反視": "文科省判断支持・政治的中立性違反を指摘",
            "事故原因・安全管理への関心": "事故原因・再発防止への関心",
        }
        new["category"] = mapping.get(old.get("category"), old.get("category", "その他・分類保留"))
        if new["category"] == "文科省判断支持・政治的中立性違反を指摘":
            new["stance"] = "文科省支持"
        new.setdefault("stance", old.get("stance", "その他"))

    if new.get("category") not in CATEGORIES:
        new["category"] = "その他・分類保留"
    return new


def write_markdown(rows: list[dict], output: Path) -> None:
    buckets: OrderedDict[str, list[dict]] = OrderedDict((c, []) for c in CATEGORIES)
    for row in rows:
        buckets[row["classification"]["category"]].append(row)

    lines = [
        "# 辺野古高校生死亡事故 SNS反応 編集再分類版",
        "",
        f"総件数: {len(rows)}",
        "",
        "## 分類件数",
        "",
        "| 分類 | 件数 |",
        "| --- | ---: |",
    ]
    for category, items in buckets.items():
        lines.append(f"| {category} | {len(items)} |")
    lines += [
        "",
        "## 注意",
        "",
        "- 文科省判断支持と文科省判断への反発を分けるため、ルールベースで再分類した編集版です。",
        "- Yahooリアルタイム検索のサンプルであり、世論比率ではありません。",
        "",
    ]
    for category, items in buckets.items():
        lines += [f"## {category}", "", f"{len(items)}件", ""]
        for i, row in enumerate(items, 1):
            c = row["classification"]
            lines += [
                f"{i}. {c.get('summary') or row.get('text', '')[:160]}",
                f"   - 立場: {c.get('stance', '')} / 信頼度: {float(c.get('confidence') or 0.0):.2f} / リスク: {c.get('risk', '')} / 記事向き: {c.get('article_usable', False)}",
                f"   - 理由: {c.get('reason', '')}",
                f"   - 元投稿: {row.get('text', '').replace(chr(10), ' / ')}",
                f"   - URL: {row.get('url', '')}",
                f"   - 検索クエリ: `{row.get('query', '')}`",
                "",
            ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Editorial reclassify Henoko reactions")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--markdown", default="")
    args = parser.parse_args()

    rows = json.loads(resolve(args.input).read_text(encoding="utf-8"))
    for row in rows:
        row["classification"] = classify(row)
    resolve(args.output).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown:
        write_markdown(rows, resolve(args.markdown))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
