#!/usr/bin/env python3
"""Classify school nickname-ban reactions with Hermes for the issue arena."""

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
    "いじめ・心理的安全",
    "親しさ・呼称文化",
    "一律禁止の実効性",
    "本人意思・柔軟運用",
    "さん付け・ジェンダー配慮",
    "学校運用・現場体験",
    "その他",
}
STANCES = {"禁止支持", "条件付き・個別対応", "一律禁止に反対", "中立・情報"}
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
    return f"""あなたは「学校でのあだ名禁止・さん付け指導」に関するX投稿の分類者です。
次の投稿を、投稿者自身の主張に基づき1投稿1分類してください。

テーマ:
小中学校などで、いじめ防止やジェンダー配慮を目的に「あだ名・呼び捨てを禁止」
「名字＋さんで統一」する指導の是非。学校外の職場、芸能人、配信者、ゲーム、
単なる呼び方相談はテーマ外です。

重要:
- 引用・批判対象の意見を投稿者自身の意見と混同しない。皮肉や二重否定も読む。
- is_relevantは学校・児童生徒・教員・保護者の呼称ルールに直接関係する場合だけtrue。
- 「あだ名」「さん付け」があっても、職場、研究室、芸能、ゲーム、ファン同士、
  日常の呼び方相談だけならis_relevant=false。
- is_opinionは投稿者自身の評価、提案、懸念、または制度評価につながる具体的体験が
  読み取れる場合だけtrue。見出し・URL・ニュース共有だけならfalse。
- 無関係ならmain_issueは「その他」、stanceは「中立・情報」。
- 関連するが意見のない情報共有は、最も近い論点に分類しstanceは「中立・情報」。
- 複数論点がある場合は投稿の主眼をmain_issueにする。
- summaryは攻撃的表現を中和し、投稿者の主張を50字以内で要約する。

main_issue（完全一致7択）:
1. いじめ・心理的安全
   ─ 嫌なあだ名、からかい、被害予防、傷つき、安心して過ごせる環境
2. 親しさ・呼称文化
   ─ 愛称、親近感、個性、距離感、子ども同士の自然な交流
3. 一律禁止の実効性
   ─ 禁止でいじめが減るか、表面的対策、学校の過剰管理、言葉狩り
4. 本人意思・柔軟運用
   ─ 本人が嫌かどうか、同意、ケースバイケース、嫌な呼び方だけ止める
5. さん付け・ジェンダー配慮
   ─ くん・ちゃんの性差、名字＋さん統一、敬称、男女平等
6. 学校運用・現場体験
   ─ 自分や子どもの学校での実態、教員・保護者視点、導入状況、世代差
7. その他
   ─ テーマ外、論点不明

stance（完全一致4択）:
- 禁止支持
- 条件付き・個別対応
- 一律禁止に反対
- 中立・情報

intensity: low / medium / high
risk: low / medium / high
confidence: 0から1

article_usableは、記事の代表例として論点と立場が明確で安全に紹介できる場合だけtrue。
事実の正しさを保証する値ではありません。

JSON配列だけを返してください。各要素は必ず次のキーを持ち、idは入力と一致させてください:
{{"id":0,"is_relevant":true,"is_opinion":true,"main_issue":"本人意思・柔軟運用","stance":"条件付き・個別対応","intensity":"medium","summary":"嫌な呼び方だけを本人の意思に沿って止めるべき","reason":"...","confidence":0.9,"article_usable":true,"risk":"low"}}

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
        found = len(rows) if isinstance(rows, list) else "non-list"
        raise ValueError(f"expected {expected} classifications, got {found}")
    rows.sort(key=lambda row: int(row.get("id", -1)))
    for index, row in enumerate(rows):
        if row.get("id") != index:
            raise ValueError(f"missing or duplicate id around {index}")
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
        row["confidence"] = max(0.0, min(1.0, float(row.get("confidence", 0))))
        if not row["is_relevant"]:
            row["is_opinion"] = False
            row["main_issue"] = "その他"
            row["stance"] = "中立・情報"
            row["article_usable"] = False
        elif not row["is_opinion"]:
            row["stance"] = "中立・情報"
            row["article_usable"] = False
        row.pop("id", None)
    return rows


def classify(batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prompt = prompt_for(batch)
    last_error: Exception | None = None
    for _ in range(3):
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
    intensity_counts = Counter(row["classification"]["intensity"] for row in opinions)
    low_conf = [row for row in rows if row["classification"]["confidence"] < 0.65]
    lines = [
        "# 学校でのあだ名禁止 Hermes 論点アリーナ分類",
        "",
        f"- 分類件数: {len(rows)}",
        f"- 関連投稿: {len(relevant)}",
        f"- 意見投稿: {len(opinions)}",
        f"- テーマ外・非意見: {len(rows) - len(opinions)}",
        "- 注意: 取得したSNS投稿サンプルの分類であり、世論調査ではありません。",
        "",
        "## 論点別件数（関連する意見投稿）",
        "",
        *[f"- {key}: {issue_counts[key]}" for key in sorted(ISSUES - {"その他"})],
        "",
        "## スタンス別件数（関連する意見投稿）",
        "",
        *[f"- {key}: {stance_counts[key]}" for key in sorted(STANCES)],
        "",
        "## 熱量",
        "",
        *[f"- {key}: {intensity_counts[key]}" for key in sorted(INTENSITIES)],
        "",
        "## 品質確認",
        "",
        f"- confidence 0.65未満: {len(low_conf)}",
        f"- article_usable true: {sum(bool(row['classification']['article_usable']) for row in opinions)}",
        "",
        "## 要レビュー例",
        "",
    ]
    review = sorted(rows, key=lambda row: row["classification"]["confidence"])[:30]
    for row in review:
        c = row["classification"]
        lines.extend([
            f"### {c['main_issue']} / {c['stance']} / confidence {c['confidence']}",
            "",
            f"- relevant/opinion: {c['is_relevant']} / {c['is_opinion']}",
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
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--batch-size", type=int, default=10)
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
        batch = source[offset : offset + args.batch_size]
        labels = classify(batch)
        for original, label in zip(batch, labels):
            row = dict(original)
            row["classification"] = label
            completed.append(row)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(completed, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"classified {len(completed)}/{len(source)}", flush=True)

    write_markdown(completed, args.markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
