#!/usr/bin/env python3
"""Classify Henoko accident reactions for the issue arena with Hermes CLI."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
ISSUES = {
    "政治的中立性",
    "安全管理・事故原因",
    "追悼・被害者の尊厳",
    "平和教育の萎縮",
    "政治利用・基地問題",
    "報道・行政対応",
}
STANCES = {
    "文科省判断を支持",
    "文科省判断に反発",
    "論点を切り分ける",
    "中立・情報共有",
}
INTENSITIES = {"low", "medium", "high"}
RISKS = {"low", "medium", "high"}


def prompt_for(batch: list[dict[str, Any]]) -> str:
    payload = [
        {
            "id": index,
            "text": str(row.get("text") or "")[:1400],
            "query": str(row.get("query") or ""),
        }
        for index, row in enumerate(batch)
    ]
    return f"""あなたは、沖縄・辺野古での修学旅行中の高校生死亡事故と、
文科省による教育基本法違反認定をめぐるX投稿の分類者です。
次の投稿を、投稿者自身の主張に基づいて1投稿1分類してください。

重要な判定ルール:
- 引用したニュース見出しや他人の発言を、投稿者自身の立場と混同しない。
- 「抗議声明を批判する」は文科省判断への反発ではない。二重否定・皮肉・批判対象を読む。
- 事故の安全管理や学校責任を批判していても、文科省判断を明示的に評価していなければ
  stanceは「論点を切り分ける」にする。
- 文科省の認定を妥当・当然・支持とする場合だけ「文科省判断を支持」。
- 文科省の認定を不当・行きすぎ・教育への圧力とする場合だけ「文科省判断に反発」。
- ニュース共有、事実確認、短い見出し、立場不明は「中立・情報共有」。
- main_issueは投稿の主眼を1つ選ぶ。複数の話題があっても主張の中心で決める。
- 追悼式のヤジ・政治的演出への批判は、追悼や遺族への配慮が主眼なら
  「追悼・被害者の尊厳」、運動批判が主眼なら「政治利用・基地問題」。
- article_usableは記事の代表例として要約を安全に使えるかであり、事実の正しさの保証ではない。
- 未確認の犯人断定、個人攻撃、差別表現、陰謀論はriskを上げ、原則article_usable=false。
- summaryは原文を転載せず、30〜70字程度の中立的な要約にする。

main_issue（完全一致6択）:
1. 政治的中立性
2. 安全管理・事故原因
3. 追悼・被害者の尊厳
4. 平和教育の萎縮
5. 政治利用・基地問題
6. 報道・行政対応

stance（完全一致4択）:
- 文科省判断を支持
- 文科省判断に反発
- 論点を切り分ける
- 中立・情報共有

intensity: low / medium / high
risk: low / medium / high
confidence: 0から1

JSON配列だけを返してください。各要素は必ず次のキーを持ち、idは入力と一致させてください:
{{"id":0,"main_issue":"安全管理・事故原因","stance":"論点を切り分ける","intensity":"medium","summary":"...","reason":"...","confidence":0.8,"article_usable":true,"risk":"low"}}

入力:
{json.dumps(payload, ensure_ascii=False)}
"""


def parse_response(text: str, expected: int) -> list[dict[str, Any]]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    match = re.search(r"\[[\s\S]*\]", cleaned)
    if not match:
        raise ValueError("Hermes response did not contain a JSON array")
    rows = json.loads(match.group(0))
    if not isinstance(rows, list) or len(rows) != expected:
        actual = len(rows) if isinstance(rows, list) else "non-list"
        raise ValueError(f"expected {expected} classifications, got {actual}")
    rows.sort(key=lambda row: int(row.get("id", -1)))
    for index, row in enumerate(rows):
        if row.get("id") != index:
            raise ValueError(f"missing or duplicate id around {index}")
        if row.get("main_issue") not in ISSUES:
            raise ValueError(f"invalid main_issue: {row.get('main_issue')}")
        if row.get("stance") not in STANCES:
            raise ValueError(f"invalid stance: {row.get('stance')}")
        if row.get("intensity") not in INTENSITIES:
            raise ValueError(f"invalid intensity: {row.get('intensity')}")
        if row.get("risk") not in RISKS:
            raise ValueError(f"invalid risk: {row.get('risk')}")
        row["confidence"] = max(0.0, min(1.0, float(row.get("confidence", 0))))
        row["article_usable"] = bool(row.get("article_usable"))
        row.pop("id", None)
    return rows


def classify(batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prompt = prompt_for(batch)
    last_error: Exception | None = None
    for _ in range(2):
        result = subprocess.run(
            ["hermes", "--oneshot", prompt],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            last_error = RuntimeError(
                result.stderr.strip() or f"Hermes exited {result.returncode}"
            )
            continue
        try:
            return parse_response(result.stdout, len(batch))
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            prompt += (
                f"\n前回の出力エラー: {exc}。説明を付けず、"
                "指定した完全一致ラベルの正しいJSON配列だけを返してください。"
            )
    raise RuntimeError(f"Hermes batch failed: {last_error}")


def normalized_text(row: dict[str, Any]) -> str:
    text = str(row.get("text") or "")
    text = re.sub(r"https?://\S+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def deduplicate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in rows:
        key = normalized_text(row)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def evenly_sample(
    rows: list[dict[str, Any]], limit: int
) -> list[dict[str, Any]]:
    if limit >= len(rows):
        return rows
    if limit == 1:
        return [rows[0]]
    indexes = [
        round(index * (len(rows) - 1) / (limit - 1))
        for index in range(limit)
    ]
    return [rows[index] for index in indexes]


def write_markdown(rows: list[dict[str, Any]], path: Path) -> None:
    issue_counts = Counter(row["classification"]["main_issue"] for row in rows)
    stance_counts = Counter(row["classification"]["stance"] for row in rows)
    intensity_counts = Counter(row["classification"]["intensity"] for row in rows)
    low_confidence = [
        row for row in rows if float(row["classification"]["confidence"]) < 0.65
    ]
    high_risk = [
        row for row in rows if row["classification"]["risk"] == "high"
    ]
    unusable = [
        row for row in rows if not row["classification"]["article_usable"]
    ]
    lines = [
        "# 辺野古高校生死亡事故 Hermes 論点アリーナ分類",
        "",
        f"- 分類件数: {len(rows)}",
        "- 注意: 取得したSNS投稿サンプルの分類であり、世論比率ではありません。",
        "",
        "## 論点別件数",
        "",
        *[f"- {key}: {issue_counts[key]}" for key in sorted(ISSUES)],
        "",
        "## 文科省判断への態度",
        "",
        *[f"- {key}: {stance_counts[key]}" for key in sorted(STANCES)],
        "",
        "## 反応強度",
        "",
        *[f"- {key}: {intensity_counts[key]}" for key in sorted(INTENSITIES)],
        "",
        "## 品質確認",
        "",
        f"- confidence 0.65未満: {len(low_confidence)}",
        f"- risk high: {len(high_risk)}",
        f"- article_usable false: {len(unusable)}",
        "",
        "## 要レビュー例",
        "",
    ]
    review = sorted(
        rows,
        key=lambda row: (
            float(row["classification"]["confidence"]),
            row["classification"]["risk"] != "high",
        ),
    )[:30]
    for row in review:
        classification = row["classification"]
        lines.extend(
            [
                "### "
                + f"{classification['main_issue']} / {classification['stance']} / "
                + f"confidence {classification['confidence']}",
                "",
                f"- 要約: {classification['summary']}",
                f"- 理由: {classification['reason']}",
                f"- risk: {classification['risk']}",
                f"- URL: {row.get('url') or 'なし'}",
                "",
            ]
        )
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--keep-duplicates", action="store_true")
    parser.add_argument("--sample-evenly", action="store_true")
    args = parser.parse_args()

    source = json.loads(args.input.read_text())
    if not args.keep_duplicates:
        original_count = len(source)
        source = deduplicate(source)
        print(
            f"deduplicated {original_count} -> {len(source)}",
            flush=True,
        )
    source = source[args.offset :]
    if args.limit:
        source = (
            evenly_sample(source, args.limit)
            if args.sample_evenly
            else source[: args.limit]
        )
    completed: list[dict[str, Any]] = []
    if args.resume and args.output.exists():
        completed = json.loads(args.output.read_text())
    start = len(completed)
    if start > len(source):
        raise ValueError("resume output is longer than input")

    for offset in range(start, len(source), args.batch_size):
        batch = source[offset : offset + args.batch_size]
        labels = classify(batch)
        for original, label in zip(batch, labels):
            row = dict(original)
            row["classification"] = label
            completed.append(row)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(completed, ensure_ascii=False, indent=2) + "\n"
        )
        print(f"classified {len(completed)}/{len(source)}", flush=True)

    write_markdown(completed, args.markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
