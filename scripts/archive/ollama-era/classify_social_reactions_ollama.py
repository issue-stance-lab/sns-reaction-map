#!/usr/bin/env python3
"""Classify collected SNS reactions with Ollama.

Usage:
    ollama serve
    python scripts/classify_social_reactions_ollama.py \
      --input social-samples/takaichi_realtime_samples.json \
      --output social-samples/takaichi_realtime_ollama_classified.json \
      --markdown social-samples/takaichi_realtime_ollama_classified.md

This script is intentionally generic. It accepts any JSON list with at least
`text`, `url`, and optional `query` fields.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import OrderedDict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

CATEGORIES = [
    "高市氏批判・責任追及",
    "高市氏擁護・報道批判",
    "玉木氏比較・説明責任",
    "玉木氏擁護・貰い事故",
    "サナエトークン関連",
    "松井健氏を軸にした拡張",
    "ネット選挙・透明性問題",
    "未確認・陰謀寄り",
    "その他・分類保留",
]

STANCE_LABELS = [
    "批判",
    "擁護",
    "比較",
    "保留",
    "未確認",
    "その他",
]

PROMPT = """あなたはSNS投稿の論調分類器です。説明や思考は不要です。
以下の投稿を、指定カテゴリのどれか1つに分類してください。

カテゴリ:
{categories}

立場ラベル:
{stance_labels}

分類基準:
- 高市氏批判・責任追及: 高市氏、陣営、秘書の責任や説明責任を問う
- 高市氏擁護・報道批判: 高市氏本人の関与を否定、文春/共同/メディア/野党を批判
- 玉木氏比較・説明責任: 玉木氏も松井氏関連で説明すべき、同じではないかと見る
- 玉木氏擁護・貰い事故: 玉木氏を同列視すべきでない、巻き込まれと見る
- サナエトークン関連: サナエトークン、暗号資産、補償、金融庁等に主眼
- 松井健氏を軸にした拡張: 松井氏を起点に他政治家、団体、人物へ広げる
- ネット選挙・透明性問題: 政治動画、AI、外注、発信主体、広告、拡散の透明性を問題視
- 未確認・陰謀寄り: 根拠不明の断定、外国勢力、陰謀、売国など
- その他・分類保留: どれにも明確に当てはまらない

注意:
- 投稿の文脈を読んで分類してください。単語だけで判断しないでください。
- 「文春が捏造」「高市総理は無関係」は高市氏擁護・報道批判です。
- 「中傷動画を作った本人が高市総理の指示ではないと言っている」は高市氏擁護・報道批判です。
- 「文春、共同捏造判明」「事件はでっちあげ」は高市氏擁護・報道批判です。
- 「高市氏は説明すべき」「公設秘書が関与なら重大」は高市氏批判・責任追及です。
- 投稿内に「虚偽答弁」「問題」「中傷動画」があっても、主張の方向が報道批判なら高市氏擁護・報道批判にしてください。
- 攻撃的表現は要約で中和してください。
- confidence は 0.0 から 1.0。
- article_usable は記事内の代表意見として使いやすい場合 true。

投稿:
{text}

出力はJSONのみ:
{{
  "category": "カテゴリ名",
  "stance": "立場ラベル",
  "summary": "中立的な1文要約",
  "reason": "分類理由を短く",
  "confidence": 0.0,
  "article_usable": true,
  "risk": "none / low / medium / high"
}}"""


def resolve_path(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p


def check_ollama() -> list[str] | None:
    try:
        with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return None


def call_ollama(model: str, prompt: str, timeout: int = 120) -> str:
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 500,
            },
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("response", "")


def parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"Could not parse JSON: {text[:200]}")


def normalize_result(result: dict) -> dict:
    category = result.get("category") or "その他・分類保留"
    if category not in CATEGORIES:
        category = "その他・分類保留"

    stance = result.get("stance") or "その他"
    if stance not in STANCE_LABELS:
        stance = "その他"

    try:
        confidence = float(result.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    risk = result.get("risk") or "none"
    if risk not in {"none", "low", "medium", "high"}:
        risk = "medium"

    return {
        "category": category,
        "stance": stance,
        "summary": str(result.get("summary") or "").strip(),
        "reason": str(result.get("reason") or "").strip(),
        "confidence": confidence,
        "article_usable": bool(result.get("article_usable", False)),
        "risk": risk,
    }


def clean_text(text: str) -> str:
    return (
        text.replace("\tSTART\t", "")
        .replace("\tEND\t", "")
        .replace("START", "")
        .replace("END", "")
        .strip()
    )


def apply_rule_override(text: str, result: dict) -> dict:
    """Correct common, high-confidence patterns before saving.

    LLMs often over-weight words like "虚偽答弁" or "中傷動画" and miss that
    the post is actually attacking the media report. These overrides are narrow
    and only handle repeated patterns seen in Yahoo realtime samples.
    """
    defense_markers = [
        "高市総理は無関係",
        "高市氏は無関係",
        "高市総理の指示ではない",
        "高市首相の指示ではない",
        "高市さんの指示ではない",
        "文春、共同捏造",
        "文春と共同",
        "共同捏造",
        "文春の捏造",
        "事件はでっちあげ",
        "疑惑は晴れ",
        "捏造だった",
        "でっちあげ",
        "文春のあやふや証拠",
        "高市政権追い詰める前に",
        "立憲は今別の件",
    ]
    if any(marker in text for marker in defense_markers):
        fixed = dict(result)
        fixed["category"] = "高市氏擁護・報道批判"
        fixed["stance"] = "擁護"
        if not fixed.get("summary"):
            fixed["summary"] = "報道や疑惑を疑い、高市氏本人の関与を否定する主張。"
        fixed["reason"] = "報道批判または高市氏本人の関与否定を明示しているため。"
        fixed["confidence"] = max(float(fixed.get("confidence", 0.0)), 0.85)
        return fixed
    return result


def classify_post(model: str, text: str) -> dict:
    text = clean_text(text)
    prompt = PROMPT.format(
        categories="\n".join(f"- {c}" for c in CATEGORIES),
        stance_labels=", ".join(STANCE_LABELS),
        text=text[:1200],
    )
    response = call_ollama(model, prompt)
    result = normalize_result(parse_json_response(response))
    return apply_rule_override(text, result)


def write_markdown(rows: list[dict], output: Path) -> None:
    buckets: OrderedDict[str, list[dict]] = OrderedDict((c, []) for c in CATEGORIES)
    for row in rows:
        buckets.setdefault(row["classification"]["category"], []).append(row)

    lines = [
        "# SNS反応 Ollama分類版",
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
        "- Ollamaによる自動分類です。公開前に代表投稿は人間が確認してください。",
        "- Yahooリアルタイム検索のサンプルであり、X全体の世論比率ではありません。",
        "- 攻撃的表現や未確認情報は記事本文では要約して扱ってください。",
        "",
    ]

    for category, items in buckets.items():
        lines += [f"## {category}", "", f"{len(items)}件", ""]
        for i, row in enumerate(items, 1):
            c = row["classification"]
            text = row.get("text", "").replace("\n", " / ")
            lines += [
                f"{i}. {c['summary'] or text[:160]}",
                f"   - 立場: {c['stance']} / 信頼度: {c['confidence']:.2f} / リスク: {c['risk']} / 記事向き: {c['article_usable']}",
                f"   - 理由: {c['reason']}",
                f"   - 元投稿: {text}",
                f"   - URL: {row.get('url', '')}",
                f"   - 検索クエリ: `{row.get('query', '')}`",
                "",
            ]

    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify SNS reactions with Ollama")
    parser.add_argument("--input", required=True, help="Input JSON list")
    parser.add_argument("--output", required=True, help="Output classified JSON")
    parser.add_argument("--markdown", default="", help="Output Markdown")
    parser.add_argument("--model", default="qwen2.5:7b", help="Ollama model")
    parser.add_argument("--limit", type=int, default=0, help="Limit rows for testing")
    parser.add_argument("--sleep", type=float, default=0.0, help="Sleep between calls")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    input_path = resolve_path(args.input)
    output_path = resolve_path(args.output)
    markdown_path = resolve_path(args.markdown) if args.markdown else None

    rows = json.loads(input_path.read_text(encoding="utf-8"))
    if args.limit:
        rows = rows[: args.limit]

    print(f"入力: {input_path} ({len(rows)}件)")

    if args.dry_run:
        print("Dry run. Ollamaは呼びません。")
        print(rows[0].get("text", "")[:300] if rows else "no rows")
        return 0

    models = check_ollama()
    if models is None:
        print("Ollamaに接続できません。別ターミナルで起動してください:")
        print("  ollama serve")
        return 1
    if args.model not in models and args.model.split(":")[0] not in [m.split(":")[0] for m in models]:
        print(f"モデル '{args.model}' が見つかりません。利用可能: {', '.join(models)}")
        print(f"必要なら実行: ollama pull {args.model}")
        return 1

    classified = []
    errors = 0
    for idx, row in enumerate(rows, 1):
        print(f"[{idx}/{len(rows)}] classify", (row.get("url") or "")[-30:])
        try:
            classification = classify_post(args.model, row.get("text", ""))
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            errors += 1
            classification = {
                "category": "その他・分類保留",
                "stance": "その他",
                "summary": "",
                "reason": f"classification_error: {exc}",
                "confidence": 0.0,
                "article_usable": False,
                "risk": "medium",
            }
        new_row = dict(row)
        new_row["text"] = clean_text(new_row.get("text", ""))
        new_row["classification"] = classification
        classified.append(new_row)
        if args.sleep:
            time.sleep(args.sleep)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(classified, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JSON保存: {output_path}")

    if markdown_path:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        write_markdown(classified, markdown_path)
        print(f"Markdown保存: {markdown_path}")

    print(f"完了: {len(classified)}件 / エラー {errors}件")
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
