#!/usr/bin/env python3
"""Batch classify SNS reactions with Ollama.

This is faster than one-request-per-post classification. It sends batches of
posts and expects a JSON array with one classification per post.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from collections import OrderedDict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
TAGS_URL = "http://127.0.0.1:11434/api/tags"

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

STANCE_LABELS = ["批判", "擁護", "比較", "保留", "未確認", "その他"]


PROMPT = """あなたはSNS投稿の論調分類器です。説明や思考は不要です。
以下の投稿リストを分類し、JSON配列のみを返してください。

カテゴリ:
{categories}

立場ラベル: {stance_labels}

重要な分類ルール:
- 「文春が捏造」「共同捏造」「事件はでっちあげ」「高市総理は無関係」「高市総理の指示ではない」は高市氏擁護・報道批判。
- 「高市氏は説明すべき」「公設秘書が関与なら重大」「辞任すべき」は高市氏批判・責任追及。
- 「玉木氏も同じでは」「玉木氏も説明すべき」は玉木氏比較・説明責任。
- 「玉木氏は巻き込まれ」「同列視は雑」は玉木氏擁護・貰い事故。
- 「サナエトークン」「暗号資産」「金融庁」「補償」はサナエトークン関連。
- 「AI、外注、広告、発信主体、拡散、選挙の透明性」が主眼ならネット選挙・透明性問題。
- 攻撃的表現はsummaryで中和する。
- confidence は 0.0 から 1.0。
- article_usable は代表意見として記事で使いやすい場合 true。
{extra_rules}

投稿リスト:
{items}

出力JSON配列。各要素は必ずこの形式:
[
  {{
    "id": 1,
    "category": "カテゴリ名",
    "stance": "立場ラベル",
    "summary": "中立的な1文要約",
    "reason": "分類理由を短く",
    "confidence": 0.0,
    "article_usable": true,
    "risk": "none / low / medium / high"
  }}
]"""


def resolve_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def clean_text(text: str) -> str:
    text = re.sub(r'\s*(?:START|END)\s*', ' ', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def structure_rt(text: str) -> dict:
    """Detect quote RT pattern and split into main and quoted portions."""
    match = re.search(r'RT\s+@[\w]+:', text)
    if match:
        main = text[:match.start()].strip()
        quoted = text[match.end():].strip()
        if main and quoted:
            return {"main": main, "quoted": quoted}
        if quoted and not main:
            return {"main": quoted}
    return {"main": text}


def check_ollama() -> list[str] | None:
    try:
        with urllib.request.urlopen(TAGS_URL, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return None


def call_ollama(model: str, prompt: str, timeout: int) -> str:
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 2500},
        }
    ).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("response", "")


def parse_array(text: str) -> list[dict]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        parsed = json.loads(match.group())
        if isinstance(parsed, list):
            return parsed
    raise ValueError(f"Could not parse JSON array: {text[:300]}")


def normalize(result: dict) -> dict:
    category = result.get("category") if result.get("category") in CATEGORIES else "その他・分類保留"
    stance = result.get("stance") if result.get("stance") in STANCE_LABELS else "その他"
    try:
        confidence = float(result.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    risk = result.get("risk") if result.get("risk") in {"none", "low", "medium", "high"} else "medium"
    return {
        "category": category,
        "stance": stance,
        "summary": str(result.get("summary") or "").strip(),
        "reason": str(result.get("reason") or "").strip(),
        "confidence": max(0.0, min(1.0, confidence)),
        "article_usable": bool(result.get("article_usable", False)),
        "risk": risk,
    }


def apply_rule_override(text: str, result: dict) -> dict:
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
        if not fixed.get("summary") or "指示が高市総理から出た" in fixed.get("summary", ""):
            fixed["summary"] = "報道や疑惑を疑い、高市氏本人の関与を否定する主張。"
        fixed["reason"] = "報道批判または高市氏本人の関与否定を明示しているため。"
        fixed["confidence"] = max(float(fixed.get("confidence", 0.0)), 0.85)
        return fixed
    return result


def classify_batch(model: str, rows: list[dict], timeout: int, avoid_hold: bool = False) -> list[dict]:
    items = []
    for i, row in enumerate(rows, 1):
        cleaned = clean_text(row.get("text", ""))
        parts = structure_rt(cleaned)
        if "quoted" in parts:
            display = f"[本文] {parts['main']} / [引用] {parts['quoted']}"
        else:
            display = parts["main"]
        items.append({"id": i, "text": display[:700]})
    prompt = PROMPT.format(
        categories="\n".join(f"- {c}" for c in CATEGORIES),
        stance_labels=", ".join(STANCE_LABELS),
        extra_rules=(
            "\n保留再分類ルール:\n"
            "- これは一度保留になった投稿の再分類です。文脈が少しでも読める場合は最も近いカテゴリへ寄せる。\n"
            "- ニュース共有だけでも、共有対象が高市氏責任追及なら高市氏批判、報道懐疑なら高市氏擁護、サナエトークンならサナエトークン関連にする。\n"
            "- 皮肉・揶揄は、攻撃対象を推定して分類する。\n"
            "- その他・分類保留は、本文が短すぎる、意味不明、分類対象外の場合だけ使う。\n"
            if avoid_hold
            else ""
        ),
        items=json.dumps(items, ensure_ascii=False, indent=2),
    )
    response = call_ollama(model, prompt, timeout)
    parsed = parse_array(response)
    by_id = {}
    for item in parsed:
        try:
            by_id[int(item.get("id"))] = normalize(item)
        except Exception:
            continue
    results = []
    for i in range(1, len(rows) + 1):
        base = by_id.get(
                i,
                {
                    "category": "その他・分類保留",
                    "stance": "その他",
                    "summary": "",
                    "reason": "missing batch result",
                    "confidence": 0.0,
                    "article_usable": False,
                    "risk": "medium",
                },
        )
        results.append(apply_rule_override(clean_text(rows[i - 1].get("text", "")), base))
    return results


def classify_batch_with_retry(
    model: str, rows: list[dict], timeout: int, avoid_hold: bool = False
) -> tuple[list[dict], int]:
    """Call classify_batch and retry once if any expected IDs are missing."""
    expected_ids = set(range(1, len(rows) + 1))
    retries = 0

    results = classify_batch(model, rows, timeout, avoid_hold)

    # Check which IDs came back with real results (not fallback "missing batch result")
    present_ids = {
        i + 1
        for i, r in enumerate(results)
        if r.get("reason") != "missing batch result"
    }
    missing_ids = expected_ids - present_ids

    if missing_ids:
        retries = 1
        print(f"  ID欠落 {sorted(missing_ids)} を検出、リトライ中...", flush=True)
        results = classify_batch(model, rows, timeout, avoid_hold)

    return results, retries


def write_markdown(rows: list[dict], output: Path) -> None:
    buckets: OrderedDict[str, list[dict]] = OrderedDict((c, []) for c in CATEGORIES)
    for row in rows:
        buckets[row["classification"]["category"]].append(row)
    lines = [
        "# SNS反応 Ollamaバッチ分類版",
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
        "- Ollamaによる自動分類です。代表投稿は公開前に人間が確認してください。",
        "- Yahooリアルタイム検索のサンプルであり、X全体の世論比率ではありません。",
        "",
    ]
    for category, items in buckets.items():
        lines += [f"## {category}", "", f"{len(items)}件", ""]
        for i, row in enumerate(items, 1):
            c = row["classification"]
            lines += [
                f"{i}. {c['summary'] or row.get('text', '')[:160]}",
                f"   - 立場: {c['stance']} / 信頼度: {c['confidence']:.2f} / リスク: {c['risk']} / 記事向き: {c['article_usable']}",
                f"   - 理由: {c['reason']}",
                f"   - 元投稿: {row.get('text', '').replace(chr(10), ' / ')}",
                f"   - URL: {row.get('url', '')}",
                f"   - 検索クエリ: `{row.get('query', '')}`",
                "",
            ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch classify SNS reactions with Ollama")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--markdown", default="")
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--batch-size", type=int, default=3)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--avoid-hold", action="store_true", help="Treat hold/other as a last resort for reclassification")
    args = parser.parse_args()

    input_path = resolve_path(args.input)
    output_path = resolve_path(args.output)
    markdown_path = resolve_path(args.markdown) if args.markdown else None
    rows = json.loads(input_path.read_text(encoding="utf-8"))
    if args.limit:
        rows = rows[: args.limit]
    for row in rows:
        row["text"] = clean_text(row.get("text", ""))
    print(f"入力: {input_path} ({len(rows)}件)", flush=True)
    if check_ollama() is None:
        print("Ollamaに接続できません。ollama serve を確認してください。", flush=True)
        return 1
    classified = []
    errors = 0
    total_retries = 0
    for start in range(0, len(rows), args.batch_size):
        batch = rows[start : start + args.batch_size]
        print(f"[{start + 1}-{start + len(batch)}/{len(rows)}] batch classify", flush=True)
        try:
            results, retries = classify_batch_with_retry(args.model, batch, args.timeout, args.avoid_hold)
            total_retries += retries
        except Exception as exc:
            errors += len(batch)
            print(f"  ERROR: {exc}", flush=True)
            results = [
                {
                    "category": "その他・分類保留",
                    "stance": "その他",
                    "summary": "",
                    "reason": f"classification_error: {exc}",
                    "confidence": 0.0,
                    "article_usable": False,
                    "risk": "medium",
                }
                for _ in batch
            ]
        for row, classification in zip(batch, results):
            new_row = dict(row)
            new_row["classification"] = classification
            classified.append(new_row)
        if args.sleep:
            time.sleep(args.sleep)
    output_path.write_text(json.dumps(classified, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JSON保存: {output_path}", flush=True)
    if markdown_path:
        write_markdown(classified, markdown_path)
        print(f"Markdown保存: {markdown_path}", flush=True)
    if total_retries:
        print(f"リトライ発生: {total_retries}回", flush=True)
    print(f"完了: {len(classified)}件 / エラー {errors}件", flush=True)
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
