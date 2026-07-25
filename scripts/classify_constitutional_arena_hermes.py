#!/usr/bin/env python3
"""Classify constitutional-amendment reactions in batches with Hermes CLI."""

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
    "改憲全般",
    "9条・自衛隊",
    "緊急事態条項",
    "国民投票・広告",
    "政党・発議手続き",
    "情報・議論の質",
}
STANCES = {"改正推進", "慎重・反対", "手続き重視", "中立"}
INTENSITIES = {"low", "medium", "high"}
RISKS = {"low", "medium", "high"}


def prompt_for(batch: list[dict[str, Any]]) -> str:
    payload = [
        {
            "id": i,
            "text": str(row.get("text") or "")[:1200],
            "query": str(row.get("query") or ""),
        }
        for i, row in enumerate(batch)
    ]
    return f"""あなたは日本の憲法改正論議に関するX投稿の分類者です。
次の投稿を、投稿者自身の主張に基づいて1投稿1分類してください。

重要:
- 引用先・批判対象・他人の発言への態度を、投稿者自身の改憲賛否と混同しない。
- 「Aに反対する人を批判」はAへの反対ではない。二重否定と皮肉を読む。
- 複数論点がある場合は、投稿の主眼をmain_issueにする。
- 情報共有だけ、文脈不足、論点判定不能は「情報・議論の質」「中立」。
- article_usableは記事の代表例として安全に使えるか。事実の正しさを保証する値ではない。
- raw本文をsummaryへ転載せず、短く中立的に要約する。

main_issue（完全一致6択）:
1. 改憲全般
2. 9条・自衛隊
3. 緊急事態条項
4. 国民投票・広告
5. 政党・発議手続き
6. 情報・議論の質

stance（完全一致4択）:
- 改正推進
- 慎重・反対
- 手続き重視
- 中立

intensity: low / medium / high
risk: low / medium / high
confidence: 0から1

JSON配列だけを返してください。各要素は必ず次のキーを持ち、idは入力と一致させてください:
{{"id":0,"main_issue":"改憲全般","stance":"中立","intensity":"low","summary":"...","reason":"...","confidence":0.8,"article_usable":true,"risk":"low"}}

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
        raise ValueError(f"expected {expected} classifications, got {len(rows) if isinstance(rows, list) else 'non-list'}")
    rows.sort(key=lambda row: int(row.get("id", -1)))
    for idx, row in enumerate(rows):
        if row.get("id") != idx:
            raise ValueError(f"missing or duplicate id around {idx}")
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
            last_error = RuntimeError(result.stderr.strip() or f"Hermes exited {result.returncode}")
            continue
        try:
            return parse_response(result.stdout, len(batch))
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            prompt += f"\n前回の出力エラー: {exc}。説明を付けず、正しいJSON配列だけを再出力してください。"
    raise RuntimeError(f"Hermes batch failed: {last_error}")


def write_markdown(rows: list[dict[str, Any]], path: Path) -> None:
    issue_counts = Counter(row["classification"]["main_issue"] for row in rows)
    stance_counts = Counter(row["classification"]["stance"] for row in rows)
    low_conf = [row for row in rows if float(row["classification"]["confidence"]) < 0.65]
    high_risk = [row for row in rows if row["classification"]["risk"] == "high"]
    unusable = [row for row in rows if not row["classification"]["article_usable"]]
    lines = [
        "# 憲法改正論議 Hermes 論点アリーナ分類",
        "",
        f"- 分類件数: {len(rows)}",
        "- 注意: 取得したSNS投稿サンプルの分類であり、世論比率ではありません。",
        "",
        "## 論点別件数",
        "",
        *[f"- {key}: {issue_counts[key]}" for key in sorted(ISSUES)],
        "",
        "## スタンス別件数",
        "",
        *[f"- {key}: {stance_counts[key]}" for key in sorted(STANCES)],
        "",
        "## 品質確認",
        "",
        f"- confidence 0.65未満: {len(low_conf)}",
        f"- risk high: {len(high_risk)}",
        f"- article_usable false: {len(unusable)}",
        "",
        "## 要レビュー例",
        "",
    ]
    review = sorted(rows, key=lambda row: float(row["classification"]["confidence"]))[:20]
    for row in review:
        c = row["classification"]
        lines.extend([
            f"### {c['main_issue']} / {c['stance']} / confidence {c['confidence']}",
            "",
            f"- 要約: {c['summary']}",
            f"- 理由: {c['reason']}",
            f"- URL: {row.get('url') or 'なし'}",
            "",
        ])
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--batch-size", type=int, default=12)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    source = json.loads(args.input.read_text())
    source = source[args.offset :]
    if args.limit:
        source = source[: args.limit]
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
        args.output.write_text(json.dumps(completed, ensure_ascii=False, indent=2) + "\n")
        print(f"classified {len(completed)}/{len(source)}", flush=True)

    write_markdown(completed, args.markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
