#!/usr/bin/env python3
"""Judge whether a topic is suitable for SNS反応まっぷ before full collection.

This script is intentionally lightweight: it reads a small Yahoo realtime sample
JSON and scores whether the topic has enough opinion density and conflict to
justify a full collection/classification run.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

POSITIVE_MARKERS = [
    "賛成",
    "あり",
    "良い",
    "いい",
    "必要",
    "わかる",
    "支持",
    "賛同",
    "当然",
    "助かる",
]

NEGATIVE_MARKERS = [
    "反対",
    "なし",
    "嫌",
    "いや",
    "おかしい",
    "やりすぎ",
    "迷惑",
    "無理",
    "不要",
    "意味ない",
    "ひどい",
    "問題",
]

OPINION_MARKERS = [
    *POSITIVE_MARKERS,
    *NEGATIVE_MARKERS,
    "思う",
    "感じる",
    "べき",
    "では",
    "じゃない",
    "どうなの",
    "疑問",
    "なぜ",
    "必要ない",
    "時代遅れ",
    "許せない",
    "納得",
]

LOW_SIGNAL_MARKERS = [
    "発売",
    "予約",
    "配信",
    "出演",
    "告知",
    "キャンペーン",
    "プレゼント",
    "お知らせ",
    "ニュース",
    "記事",
]

AD_RISK_MARKERS = [
    "死亡",
    "自殺",
    "殺人",
    "逮捕",
    "容疑",
    "被害者",
    "未成年",
    "児童",
    "差別",
    "国籍",
    "病気",
    "障害",
    "性的",
]


def resolve_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def clean_text(text: str) -> str:
    text = re.sub(r"\s*(?:START|END)\s*", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def generate_queries(topic: str) -> list[str]:
    base = topic.strip()
    normalized = re.sub(r"[？?！!「」【】]", " ", base)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return [
        normalized,
        f"{normalized} 賛成",
        f"{normalized} 反対",
        f"{normalized} おかしい",
        f"{normalized} やりすぎ",
        f"{normalized} 迷惑",
        f"{normalized} 必要",
    ]


def score_post_volume(rows: list[dict[str, Any]], totals: dict[str, int]) -> int:
    max_total = max(totals.values(), default=0)
    if max_total >= 100 or len(rows) >= 50:
        return 2
    if max_total >= 30 or len(rows) >= 20:
        return 1
    return 0


def has_any(text: str, markers: list[str]) -> bool:
    return any(marker in text for marker in markers)


def classify_sample(text: str) -> str:
    if not text:
        return "empty"
    pos = has_any(text, POSITIVE_MARKERS)
    neg = has_any(text, NEGATIVE_MARKERS)
    opinion = has_any(text, OPINION_MARKERS)
    low_signal = has_any(text, LOW_SIGNAL_MARKERS)
    if opinion and pos and not neg:
        return "positive"
    if opinion and neg and not pos:
        return "negative"
    if opinion and pos and neg:
        return "mixed"
    if opinion:
        return "opinion"
    if low_signal:
        return "low_signal"
    return "other"


def score_opinion_ratio(counts: Counter[str], total: int) -> tuple[int, float]:
    opinion_count = sum(counts[k] for k in ["positive", "negative", "mixed", "opinion"])
    ratio = opinion_count / total if total else 0.0
    if ratio >= 0.30:
        return 2, ratio
    if ratio >= 0.15:
        return 1, ratio
    return 0, ratio


def score_conflict(counts: Counter[str]) -> int:
    positive = counts["positive"] + counts["mixed"]
    negative = counts["negative"] + counts["mixed"]
    if positive >= 3 and negative >= 3:
        return 2
    if positive >= 1 and negative >= 1:
        return 1
    return 0


def score_seo_demand(topic: str, queries: list[str], rows: list[dict[str, Any]]) -> int:
    # Proxy for searchability: clear main phrase plus actual samples containing it.
    terms = [t for t in re.split(r"\s+", re.sub(r"[？?！!「」【】]", " ", topic)) if len(t) >= 2]
    hit_count = 0
    for row in rows:
        text = clean_text(str(row.get("text", "")))
        if any(term in text for term in terms):
            hit_count += 1
    if len(queries) >= 5 and hit_count >= 10:
        return 2
    if terms and hit_count >= 3:
        return 1
    return 0


def score_ad_safety(rows: list[dict[str, Any]]) -> tuple[int, list[str]]:
    found = sorted({m for row in rows for m in AD_RISK_MARKERS if m in clean_text(str(row.get("text", "")))})
    if not found:
        return 2, found
    if len(found) <= 2:
        return 1, found
    return 0, found


def decision(total_score: int, scores: dict[str, int]) -> str:
    if scores["ad_safety"] == 0:
        return "NG"
    if total_score >= 7 and scores["opinion_ratio"] >= 1 and scores["conflict_strength"] >= 1:
        return "GO"
    if total_score >= 4:
        return "HOLD"
    return "NG"


def reason_for(decision_value: str, scores: dict[str, int], opinion_ratio: float, risk_markers: list[str]) -> str:
    if decision_value == "GO":
        return "投稿量、意見率、対立性が最低ラインを満たしているため、本収集に進めます。"
    if scores["ad_safety"] == 0:
        return f"広告リスク語が多く含まれるため、通常の広告向けページ化は避けるべきです: {', '.join(risk_markers)}"
    weak = []
    if scores["post_volume"] == 0:
        weak.append("投稿量が少ない")
    if scores["opinion_ratio"] == 0:
        weak.append(f"意見投稿率が低い（{opinion_ratio:.0%}）")
    if scores["conflict_strength"] == 0:
        weak.append("賛否の両側が十分に見えない")
    if scores["seo_demand"] == 0:
        weak.append("検索されやすい主語が弱い")
    if scores["ad_safety"] == 1:
        weak.append(f"広告リスク語が一部ある: {', '.join(risk_markers)}")
    return "、".join(weak) + "ため、クエリ変更または続報待ちが妥当です。"


def load_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("input JSON must be an array")
    return [row for row in data if isinstance(row, dict)]


def infer_totals(rows: list[dict[str, Any]]) -> dict[str, int]:
    # fetch_yahoo_realtime_node.mjs stores returned rows, not total_available.
    return dict(Counter(str(row.get("query", "")) for row in rows))


def build_report(topic: str, rows: list[dict[str, Any]], limit: int, slug: str) -> dict[str, Any]:
    sampled = rows[:limit] if limit > 0 else rows
    queries = sorted({str(row.get("query", "")) for row in rows if row.get("query")})
    totals = infer_totals(rows)
    counts: Counter[str] = Counter()
    examples: dict[str, list[str]] = {"positive": [], "negative": [], "mixed": [], "opinion": [], "low_signal": [], "other": []}

    for row in sampled:
        text = clean_text(str(row.get("text", "")))
        label = classify_sample(text)
        counts[label] += 1
        if label in examples and len(examples[label]) < 3:
            examples[label].append(text[:160])

    post_volume = score_post_volume(rows, totals)
    opinion_ratio_score, opinion_ratio = score_opinion_ratio(counts, len(sampled))
    conflict_strength = score_conflict(counts)
    seo_demand = score_seo_demand(topic, queries, sampled)
    ad_safety, risk_markers = score_ad_safety(sampled)
    scores = {
        "post_volume": post_volume,
        "opinion_ratio": opinion_ratio_score,
        "conflict_strength": conflict_strength,
        "seo_demand": seo_demand,
        "ad_safety": ad_safety,
    }
    total_score = sum(scores.values())
    decision_value = decision(total_score, scores)
    return {
        "topic": topic,
        "queries": queries or generate_queries(topic),
        "sample_size": len(sampled),
        "returned_rows": len(rows),
        "estimated_posts_by_query": totals,
        "counts": dict(counts),
        "opinion_ratio_value": round(opinion_ratio, 3),
        "scores": scores,
        "total_score": total_score,
        "decision": decision_value,
        "reason": reason_for(decision_value, scores, opinion_ratio, risk_markers),
        "risk_markers": risk_markers,
        "examples": examples,
        "recommended_fetch_command": build_fetch_command(slug, queries or generate_queries(topic)),
    }


def build_fetch_command(slug: str, queries: list[str]) -> str:
    safe_slug = re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-") or "topic"
    query_args = " \\\n  ".join(f'--query "{q}"' for q in queries[:7])
    return (
        "node scripts/fetch_yahoo_realtime_node.mjs \\\n"
        f"  {query_args} \\\n"
        "  --dedupe \\\n"
        f"  --output social-samples/{safe_slug}_samples.json \\\n"
        f"  --markdown social-samples/{safe_slug}_samples.md"
    )


def write_markdown(report: dict[str, Any], output: Path) -> None:
    lines = [
        f"# Trend Judge: {report['topic']}",
        "",
        f"判定: **{report['decision']}**",
        f"合計スコア: **{report['total_score']} / 10**",
        f"理由: {report['reason']}",
        "",
        "## スコア",
        "",
        "| 項目 | 点数 |",
        "| --- | ---: |",
    ]
    labels = {
        "post_volume": "投稿量",
        "opinion_ratio": "意見率",
        "conflict_strength": "対立性",
        "seo_demand": "検索需要 proxy",
        "ad_safety": "広告安全性",
    }
    for key, value in report["scores"].items():
        lines.append(f"| {labels.get(key, key)} | {value} / 2 |")
    lines += [
        "",
        f"意見投稿率: {report['opinion_ratio_value']:.1%}",
        f"サンプル件数: {report['sample_size']}",
        "",
        "## 検索クエリ",
        "",
    ]
    lines.extend(f"- `{q}`" for q in report["queries"])
    lines += ["", "## 分類カウント", ""]
    for key, value in report["counts"].items():
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## 代表サンプル", ""]
    for key, values in report["examples"].items():
        if not values:
            continue
        lines.append(f"### {key}")
        lines.extend(f"- {v}" for v in values)
        lines.append("")
    lines += [
        "## 本収集コマンド案",
        "",
        "```bash",
        report["recommended_fetch_command"],
        "```",
        "",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Score topic suitability before full SNS反応まっぷ collection")
    parser.add_argument("--topic", required=True, help="Topic name to judge")
    parser.add_argument("--slug", default="", help="ASCII slug used in recommended output paths")
    parser.add_argument("--input", help="Small Yahoo realtime sample JSON")
    parser.add_argument("--output", help="Write JSON report")
    parser.add_argument("--markdown", help="Write Markdown report")
    parser.add_argument("--limit", type=int, default=50, help="Max rows to judge from input")
    parser.add_argument("--print-queries", action="store_true", help="Only print suggested queries and exit")
    args = parser.parse_args()

    if args.print_queries:
        print(json.dumps({"topic": args.topic, "queries": generate_queries(args.topic)}, ensure_ascii=False, indent=2))
        return 0

    if not args.input:
        parser.error("--input is required unless --print-queries is used")

    rows = load_rows(resolve_path(args.input))
    slug = args.slug or "topic"
    report = build_report(args.topic, rows, args.limit, slug)

    if args.output:
        output = resolve_path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown:
        write_markdown(report, resolve_path(args.markdown))

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
