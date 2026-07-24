#!/usr/bin/env python3
"""Classify elderly-license-revocation reactions with Hermes for the issue arena."""

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
    "義務化・事故防止",
    "地方の足・移動権",
    "適性検査強化",
    "代替交通整備",
    "自主返納支援",
    "その他",
}
STANCES = {"義務化賛成", "条件付き賛成", "義務化反対", "中立・情報"}
INTENSITIES = {"low", "medium", "high"}
RISKS = {"low", "medium", "high"}

ISSUE_INDEX = {
    "義務化・事故防止": 0,
    "地方の足・移動権": 1,
    "適性検査強化": 2,
    "代替交通整備": 3,
    "自主返納支援": 4,
    "その他": 5,
}


def prompt_for(batch: list[dict[str, Any]]) -> str:
    payload = [{"id": i, "text": str(row.get("text") or "")[:1200]} for i, row in enumerate(batch)]
    return f"""あなたは「高齢者の運転免許返納」に関するX投稿の分類者です。
次の投稿を、投稿者自身の主張に基づいて1投稿1分類してください。

背景:
高齢ドライバーによる死亡事故が社会問題となり、年齢による免許返納の義務化を求める声がある。
一方、地方では車が生活の足であり一律の義務化に強い反対意見も存在する。
適性検査の強化、代替交通の整備、自主返納の支援なども論点となっている。

重要:
- 引用・批判対象の意見を投稿者本人の意見と混同しない。
- is_relevantは高齢者の免許返納・返納義務化・高齢ドライバー問題・交通事故に関係すればtrue。
- is_opinionは投稿者自身の評価・提案・懸念・体験が読み取れる場合だけtrue。
- ニュース共有・告知だけならis_relevant=true、is_opinion=false、stanceは「中立・情報」。
- 無関係ならis_relevant=false、is_opinion=false、main_issueは「その他」、stanceは「中立・情報」。
- raw本文をsummaryへ転載せず、攻撃的表現を中和して50字以内で要約する。
- 複数論点がある場合は、投稿の主眼をmain_issueにする。

main_issue（完全一致6択）:
1. 義務化・事故防止 ─ 年齢制限、法的義務化、事故件数、被害者保護、強制返納
2. 地方の足・移動権 ─ 地方交通、買い物難民、通院手段、生活維持、一律規制反対
3. 適性検査強化 ─ 認知機能検査、技術評価、年齢一律の問題、個人差
4. 代替交通整備 ─ 公共交通整備、バス・タクシー充実、移動支援、インフラ先決
5. 自主返納支援 ─ 特典・インセンティブ、助成金、自発的返納促進
6. その他 ─ 上記に当てはまらない、論点不明、無関係

stance（完全一致4択）:
- 義務化賛成 ─ 法的・年齢による義務化を支持
- 条件付き賛成 ─ 適性検査・段階的な義務化など条件付きで賛成
- 義務化反対 ─ 一律の義務化に反対（理由は問わない）
- 中立・情報 ─ ニュース・情報共有、または立場が不明

intensity: low / medium / high
risk: low / medium / high
confidence: 0から1

JSON配列だけを返してください。各要素は必ず次のキーを持ち、idは入力と一致させてください:
{{"id":0,"is_relevant":true,"is_opinion":true,"main_issue":"義務化・事故防止","stance":"義務化賛成","intensity":"high","summary":"高齢ドライバーの事故が多く義務化が必要","reason":"...","confidence":0.85,"article_usable":true,"risk":"low"}}

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
        "# 高齢者免許返納 Hermes 論点分類",
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


def build_sm_raw(rows: list[dict[str, Any]]) -> str:
    """Generate SM_RAW JS snippet with i: field from Hermes classification."""
    lines = []
    for row in rows:
        c = row.get("classification", {})
        if not c.get("is_relevant"):
            continue
        issue = c.get("main_issue", "その他")
        i = ISSUE_INDEX.get(issue, 5)
        x = float(row.get("stance_restriction") or 0)
        y = float(row.get("stance_priority") or 0)
        e = float(row.get("emotional_intensity") or 0)
        conf = float(row.get("confidence") or c.get("confidence") or 0.7)
        s = str(c.get("summary") or row.get("summary") or "")[:60].replace('"', '\\"')
        u = str(row.get("url") or "")
        lines.append(f'  {{x:{x},y:{y},e:{e},c:{conf},s:"{s}",u:"{u}",i:{i}}}')
    return "const SM_RAW = [\n" + ",\n".join(lines) + "\n];"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "social-samples/elderly-license_2d_classified.json")
    parser.add_argument("--output", type=Path, default=ROOT / "social-samples/elderly-license_hermes_classified.json")
    parser.add_argument("--markdown", type=Path, default=ROOT / "social-samples/elderly-license_hermes_classified.md")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--batch-size", type=int, default=12)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--sm-raw", action="store_true", help="Print SM_RAW JS snippet to stdout after completion")
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

    write_markdown(completed, args.markdown)
    print(f"Markdown written to {args.markdown}")

    if args.sm_raw:
        print("\n=== SM_RAW ===")
        print(build_sm_raw(completed))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
