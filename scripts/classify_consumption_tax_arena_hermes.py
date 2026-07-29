#!/usr/bin/env python3
"""Classify consumption-tax-cut (消費税減税) reactions with Hermes for the issue arena."""

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
    "減税の対象範囲",
    "財源と社会保障",
    "減税の効果",
    "給付など他策との比較",
    "事業者の実務負担",
    "公約と政治不信",
    "その他",
}
STANCES = {"減税推進", "条件付き賛成・政府案に不満", "減税反対・慎重", "中立・情報"}
INTENSITIES = {"low", "medium", "high"}
RISKS = {"low", "medium", "high"}


def prompt_for(batch: list[dict[str, Any]]) -> str:
    payload = [{"id": i, "text": str(row.get("text") or "")[:1200]} for i, row in enumerate(batch)]
    return f"""あなたは「消費税減税」に関するX投稿の分類者です。
次の投稿を、投稿者自身の主張に基づいて1投稿1分類してください。

背景:
2026年7月、高市政権の下で食料品に対象を絞った限定的な消費税減税が決着に向かっている。
減税推進派は物価高対策として一律減税や消費税廃止まで求め、限定的な政府案を「中途半端」と批判する。
慎重・反対派は社会保障の財源、インフレ加速、価格転嫁されず事業者の利益になるだけという懸念を挙げる。
実務面ではレジ改修・インボイス対応など事業者負担、政局面では各党の公約と採決態度、財務省への不信も論点。

重要:
- 引用・批判対象の意見を投稿者本人の意見と混同しない。
- is_relevantは消費税・減税・増税・税率・財源に関係すればtrue。
- is_opinionは投稿者自身の評価・提案・懸念・体験が読み取れる場合だけtrue。
- ニュース共有・告知だけならis_relevant=true、is_opinion=false、stanceは「中立・情報」。
- 無関係ならis_relevant=false、is_opinion=false、main_issueは「その他」、stanceは「中立・情報」。
- raw本文をsummaryへ転載せず、攻撃的表現を中和して50字以内で要約する。
- 複数論点がある場合は、投稿の主眼をmain_issueにする。
- 政党・政治家への評価が主眼なら「公約と政治不信」にする。税制の中身が主眼ならそれぞれの論点にする。

main_issue（完全一致7択）:
1. 減税の対象範囲 ─ 食料品限定か一律か、税率（0%・5%・8%）、消費税廃止、期限付きか恒久か
2. 財源と社会保障 ─ 財源論、社会保障・年金・医療への影響、国債・財政規律
3. 減税の効果 ─ 物価高対策として効くか、インフレ加速、価格転嫁されるか、景気への影響
4. 給付など他策との比較 ─ 給付付き税額控除、現金給付、所得税・住民税減税との優劣
5. 事業者の実務負担 ─ レジ改修、インボイス、中小事業者・店舗の対応コスト、実施時期
6. 公約と政治不信 ─ 各党の公約と採決態度、高市政権への評価、財務省批判、政治への不信
7. その他 ─ 上記に当てはまらない、論点不明、無関係

stance（完全一致4択）:
- 減税推進 ─ 消費税減税・廃止を積極的に支持し、実現を求める
- 条件付き賛成・政府案に不満 ─ 減税自体は支持するが、食料品限定・期限付きなど政府案を不十分・中途半端と批判
- 減税反対・慎重 ─ 財源・効果・社会保障・実務負担の観点から減税に否定的
- 中立・情報 ─ ニュース・情報共有、または立場が不明

intensity: low / medium / high
risk: low / medium / high
confidence: 0から1

JSON配列だけを返してください。各要素は必ず次のキーを持ち、idは入力と一致させてください:
{{"id":0,"is_relevant":true,"is_opinion":true,"main_issue":"減税の対象範囲","stance":"条件付き賛成・政府案に不満","intensity":"high","summary":"食料品限定では不十分で一律減税を求める","reason":"...","confidence":0.85,"article_usable":true,"risk":"low"}}

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
        "# 消費税減税 Hermes 論点分類",
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
