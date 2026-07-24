#!/usr/bin/env python3
"""Classify takaichi X reactions with Hermes for the issue arena."""

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
    "中傷動画・説明責任",
    "文春報道の真偽",
    "サナエトークン疑惑",
    "松井健氏・工作の実態",
    "比較・政治倫理",
    "その他",
}
STANCES = {"批判・追及", "擁護・懐疑", "慎重・保留", "中立・情報"}
INTENSITIES = {"low", "medium", "high"}
RISKS = {"low", "medium", "high"}


def prompt_for(batch: list[dict[str, Any]]) -> str:
    payload = [
        {
            "id": index,
            "text": str(row.get("text") or "")[:1400],
            "summary": str(row.get("summary") or ""),
        }
        for index, row in enumerate(batch)
    ]
    return f"""あなたは「高市早苗・文春問題」に関するX投稿の分類者です。
次の投稿を、投稿者自身の主張に基づき1投稿1分類してください。

テーマ:
高市早苗氏をめぐる一連の騒動。①元参院議員・高市氏の陣営が対立候補への中傷動画制作を依頼した
疑惑と国会での説明責任、②週刊文春の報道の信憑性、③サナエトークン（仮想通貨）の暴落と詐欺疑惑、
④松井健氏を軸とした工作ネットワークの実態、⑤玉木氏・石丸氏ら他の政治家スキャンダルとの比較、
以上が主な論点です。高市氏に無関係な一般的な政治批判・芸能・スポーツはテーマ外です。

重要:
- 引用・批判対象の意見を投稿者自身の意見と混同しない。皮肉や二重否定も読む。
- is_relevantは高市問題（中傷動画・文春・トークン・松井健氏・比較）に直接関係する場合だけtrue。
- 高市氏の名前があっても、皇室・憲法・政策・選挙制度のみを論じているならis_relevant=false。
- is_opinionは投稿者自身の評価、提案、懸念、または事実整理を伴う具体的な主張が読み取れる場合だけtrue。
  ニュースURL貼り付けのみ・ただの感嘆符・意味不明テキストはfalse。
- 無関係ならmain_issueは「その他」、stanceは「中立・情報」。
- 関連するが意見のない情報共有は、最も近い論点に分類しstanceは「中立・情報」。
- 複数論点がある場合は投稿の主眼をmain_issueにする。
- summaryは攻撃的表現・固有名詞の過激な描写を中和し、投稿者の主張を50字以内で要約する。

main_issue（完全一致6択）:
1. 中傷動画・説明責任
   ─ 高市陣営が対立候補への中傷動画制作を依頼したか。本人に国会での説明責任はあるか。辞任要求。
2. 文春報道の真偽
   ─ 週刊文春の報道は正確か。証拠動画のタイムスタンプ矛盾など報道の信頼性・意図を問う論点。
3. サナエトークン疑惑
   ─ 仮想通貨「サナエトークン」の暴落と被害者補償。高市氏事務所のリポスト・関与の是非。
4. 松井健氏・工作の実態
   ─ 松井健氏を軸とした情報工作ネットワーク。高市陣営との接触・依頼の実態と証言の信憑性。
5. 比較・政治倫理
   ─ 玉木氏・石丸氏ら他の政治家スキャンダルとの比較。党派を超えた政治倫理・マスメディアの姿勢。
6. その他
   ─ テーマ外、論点不明

stance（完全一致4択）:
- 批判・追及   ─ 高市氏や陣営の行為を批判し、説明・謝罪・辞任を求める立場
- 擁護・懐疑   ─ 高市氏を擁護、または報道・追及側の主張を懐疑・批判する立場
- 慎重・保留   ─ 証拠や情報が不十分として断定を避ける立場。中立的分析も含む
- 中立・情報   ─ 投稿者自身の評価が読み取れない情報共有・拡散

intensity: low / medium / high
risk: low / medium / high
confidence: 0から1

article_usableは、記事の代表例として論点と立場が明確で安全に紹介できる場合だけtrue。
事実の正しさを保証する値ではありません。

JSON配列だけを返してください。各要素は必ず次のキーを持ち、idは入力と一致させてください:
{{"id":0,"is_relevant":true,"is_opinion":true,"main_issue":"中傷動画・説明責任","stance":"批判・追及","intensity":"medium","summary":"高市陣営の中傷動画関与を批判し説明責任を求める","reason":"...","confidence":0.9,"article_usable":true,"risk":"low"}}

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
        "# 高市早苗・文春問題 Hermes 論点アリーナ分類",
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
