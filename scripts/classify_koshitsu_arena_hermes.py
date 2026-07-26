#!/usr/bin/env python3
"""Classify koshitsu-tenpakai (皇室典範改正) reactions with Hermes for the issue arena."""

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
    "男系vs女系",
    "旧宮家養子縁組",
    "立法手続き・民主主義",
    "女性天皇・女系天皇",
    "愛子さま・皇族の地位",
    "その他",
}
STANCES = {"改正反対（男系維持）", "改正賛成（女系容認）", "中立・情報"}
INTENSITIES = {"low", "medium", "high"}
RISKS = {"low", "medium", "high"}


def prompt_for(batch: list[dict[str, Any]]) -> str:
    payload = [{"id": i, "text": str(row.get("text") or "")[:1200]} for i, row in enumerate(batch)]
    return f"""あなたは「皇室典範改正」に関するX投稿の分類者です。
次の投稿を、投稿者自身の主張に基づいて1投稿1分類してください。

背景:
2026年7月に皇室典範改正が参院で可決・成立した。主な内容は女性皇族の皇籍維持と旧宮家からの養子縁組容認。
男系継承を重視する保守派は改正に強く反対し、女系天皇・女性天皇容認を求める立場は賛成している。
立法プロセスの拙速さや愛子さまの扱いも論点となっている。

重要:
- 引用・批判対象の意見を投稿者本人の意見と混同しない。
- is_relevantは皇室典範改正・皇族・皇位継承に関係すればtrue。
- is_opinionは投稿者自身の評価・提案・懸念・感情が読み取れる場合だけtrue。
- ニュース共有・告知だけならis_relevant=true、is_opinion=false、stanceは「中立・情報」。
- 無関係ならis_relevant=false、is_opinion=false、main_issueは「その他」、stanceは「中立・情報」。
- raw本文をsummaryへ転載せず、攻撃的表現を中和して50字以内で要約する。
- 複数論点がある場合は、投稿の主眼をmain_issueにする。

main_issue（完全一致6択）:
1. 男系vs女系 ─ 男系継承の維持か女系継承の容認か、正統性・歴史・伝統の議論
2. 旧宮家養子縁組 ─ 旧宮家から皇族への養子縁組制度の是非・実効性
3. 立法手続き・民主主義 ─ 審議の拙速さ・国民の合意なし・手続き的問題
4. 女性天皇・女系天皇 ─ 女性が天皇になることの是非（男系女性天皇と女系天皇の区別含む）
5. 愛子さま・皇族の地位 ─ 愛子内親王や現皇族の具体的な地位・処遇
6. その他 ─ 上記に当てはまらない、論点不明、無関係

stance（完全一致3択）:
- 改正反対（男系維持） ─ 皇室典範改正に反対、男系継承の維持を支持
- 改正賛成（女系容認） ─ 皇室典範改正を支持、女系・旧宮家養子縁組を容認
- 中立・情報 ─ ニュース・情報共有、または立場が不明

intensity: low / medium / high
risk: low / medium / high
confidence: 0から1

JSON配列だけを返してください。各要素は必ず次のキーを持ち、idは入力と一致させてください:
{{"id":0,"is_relevant":true,"is_opinion":true,"main_issue":"男系vs女系","stance":"改正反対（男系維持）","intensity":"high","summary":"男系継承維持が日本の伝統として重要","reason":"...","confidence":0.85,"article_usable":true,"risk":"low"}}

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
        raise ValueError(f"expected {expected} classifications, got {len(rows) if isinstance(rows, list) else type(rows)}")
    rows.sort(key=lambda row: int(row.get("id", -1)))
    for idx, row in enumerate(rows):
        if row.get("id") != idx:
            raise ValueError(f"missing or duplicate id around {idx}")
        if row.get("main_issue") not in ISSUES:
            raise ValueError(f"invalid main_issue: {row.get('main_issue')!r}")
        if row.get("stance") not in STANCES:
            raise ValueError(f"invalid stance: {row.get('stance')!r}")
        if row.get("intensity") not in INTENSITIES:
            raise ValueError(f"invalid intensity: {row.get('intensity')!r}")
        if row.get("risk") not in RISKS:
            raise ValueError(f"invalid risk: {row.get('risk')!r}")
        row["is_relevant"] = bool(row.get("is_relevant"))
        row["is_opinion"] = bool(row.get("is_opinion"))
        row["article_usable"] = bool(row.get("article_usable"))
        if not row["is_relevant"]:
            row["is_opinion"] = False
            row["main_issue"] = "その他"
            row["stance"] = "中立・情報"
            row["article_usable"] = False
        elif not row["is_opinion"]:
            row["stance"] = "中立・情報"
        row["confidence"] = max(0.0, min(1.0, float(row.get("confidence", 0))))
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
            prompt += f"\n前回の出力エラー: {exc}。説明なしの正しいJSON配列だけを再出力してください。"
    raise RuntimeError(f"Hermes batch failed: {last_error}")


def write_markdown(rows: list[dict[str, Any]], path: Path) -> None:
    relevant = [row for row in rows if row["classification"]["is_relevant"]]
    opinions = [row for row in relevant if row["classification"]["is_opinion"]]
    issue_counts = Counter(row["classification"]["main_issue"] for row in opinions)
    stance_counts = Counter(row["classification"]["stance"] for row in opinions)
    lines = [
        "# 皇室典範改正 Hermes 論点分類",
        "",
        f"- 分類件数: {len(rows)}",
        f"- 関連投稿: {len(relevant)}",
        f"- 意見投稿: {len(opinions)}",
        "- 注意: 取得したSNS投稿サンプルの分類であり、世論調査ではありません。",
        "",
        "## 論点別件数（意見投稿）",
        "",
        *[f"- {key}: {issue_counts.get(key, 0)}" for key in sorted(ISSUES)],
        "",
        "## スタンス別件数（意見投稿）",
        "",
        *[f"- {key}: {stance_counts.get(key, 0)}" for key in sorted(STANCES)],
        "",
        "## 要レビュー例（confidence低い順）",
        "",
    ]
    for row in sorted(rows, key=lambda item: float(item["classification"]["confidence"]))[:20]:
        c = row["classification"]
        lines.extend([
            f"### {c['main_issue']} / {c['stance']} / confidence {c['confidence']}",
            "",
            f"- 要約: {c['summary']}",
            f"- 理由: {c['reason']}",
            f"- URL: {row.get('url') or 'なし'}",
            "",
        ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--batch-size", type=int, default=12)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    source = json.loads(args.input.read_text(encoding="utf-8"))
    if args.limit:
        source = source[: args.limit]
    completed: list[dict[str, Any]] = []
    if args.resume and args.output.exists():
        completed = json.loads(args.output.read_text(encoding="utf-8"))
    start = len(completed)
    if start > len(source):
        raise ValueError("resume output is longer than input")

    for offset in range(start, len(source), args.batch_size):
        batch = source[offset: offset + args.batch_size]
        labels = classify(batch)
        for original, label in zip(batch, labels):
            row = dict(original)
            row["classification"] = label
            completed.append(row)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(completed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"classified {len(completed)}/{len(source)}", flush=True)

    if args.markdown:
        write_markdown(completed, args.markdown)
        print(f"Markdown written to {args.markdown}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
