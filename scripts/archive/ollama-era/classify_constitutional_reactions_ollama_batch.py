#!/usr/bin/env python3
"""Batch classify constitutional amendment reactions with Ollama."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import time
import urllib.request
from collections import OrderedDict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
TAGS_URL = "http://127.0.0.1:11434/api/tags"

CATEGORIES = [
    "改憲賛成・推進",
    "改憲反対・護憲",
    "9条・自衛隊明記に賛成",
    "9条・自衛隊明記に反対",
    "緊急事態条項に賛成",
    "緊急事態条項に反対",
    "国民投票法・広告規制を重視",
    "手続き・発議可能性への関心",
    "政党・議員批判",
    "事実確認・情報共有",
    "未確認・過激表現",
    "その他・分類保留",
]

STANCES = ["改憲支持", "改憲反対", "項目別賛成", "項目別反対", "手続き重視", "慎重", "中立", "未確認", "その他"]
ISSUES = ["9条・自衛隊", "緊急事態条項", "国民投票法", "改憲全般", "手続き", "政党姿勢", "情報共有", "不明"]

PROMPT = """あなたはSNS投稿の憲法改正論議分類器です。説明や思考は不要です。
以下の投稿リストを分類し、JSON配列のみを返してください。Markdownは禁止。キーと文字列は必ずダブルクォートにしてください。

対象テーマ:
日本の憲法改正論議。9条・自衛隊明記、緊急事態条項、国民投票法・広告規制、改憲発議、政党姿勢をめぐるX反応。

重要ルール:
- Yahoo検索のハイライト文字列 START / END は無視する。
- 投稿本文に「賛成」「反対」の両方が入る場合、投稿者本人が最後に何へ賛成/反対しているかで判定する。
- 「憲法改正には賛成だが自民党草案には反対」は、改憲全般は支持だが草案慎重。category は文脈に応じて「改憲賛成・推進」または「政党・議員批判」。
- 「改憲反対」「憲法改悪」「今ある憲法を守れ」は改憲反対・護憲。
- 「自衛隊明記すべき」「違憲論争を終わらせる」「国防の現実」は9条・自衛隊明記に賛成。
- 「自衛隊明記不要」「9条改悪」「平和憲法を壊す」は9条・自衛隊明記に反対。
- 「緊急事態条項が必要」「災害・有事に備える」は緊急事態条項に賛成。
- 「緊急事態条項は危険」「権限集中」「人権制限」「独裁」は緊急事態条項に反対。
- 「国民投票法」「広告規制」「CM規制」「ネット広告」「運動資金」「外国人寄付」が主眼なら国民投票法・広告規制を重視。
- 単なるニュース共有や動画紹介は事実確認・情報共有。
- 攻撃的表現や陰謀論は summary で中和し、risk を high にする。
- 件数を世論比率として扱わないため、summary は中立的な1文にする。

カテゴリ:
{categories}

stance候補: {stances}
issue候補: {issues}

投稿リスト:
{items}

出力JSON配列。各要素は必ずこの形式:
[
  {{
    "id": 1,
    "category": "カテゴリ名",
    "stance": "stance候補",
    "issue": "issue候補",
    "summary": "中立的な1文要約",
    "reason": "分類理由を短く",
    "confidence": 0.0,
    "article_usable": true,
    "risk": "none / low / medium / high"
  }}
]"""


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def clean_text(text: str) -> str:
    return (
        str(text or "")
        .replace("\tSTART\t", "")
        .replace("\tEND\t", "")
        .replace("START", "")
        .replace("END", "")
        .replace("\n", " ")
        .strip()
    )


def check_ollama() -> bool:
    try:
        with urllib.request.urlopen(TAGS_URL, timeout=5):
            return True
    except Exception:
        return False


def call_ollama(model: str, prompt: str, timeout: int) -> str:
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.05, "num_predict": 2800},
        }
    ).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("response", "")


def parse_array(text: str) -> list[dict[str, Any]]:
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
    if not match:
        raise ValueError(f"Could not parse JSON array: {text[:300]}")
    candidate = match.group()
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    try:
        parsed = ast.literal_eval(candidate)
        if isinstance(parsed, list):
            return parsed
    except (SyntaxError, ValueError):
        pass
    repaired = re.sub(r"([{\[,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', candidate)
    repaired = repaired.replace(": True", ": true").replace(": False", ": false").replace(": None", ": null")
    parsed = json.loads(repaired)
    if isinstance(parsed, list):
        return parsed
    raise ValueError(f"Could not parse JSON array: {text[:300]}")


def normalize(item: dict[str, Any]) -> dict[str, Any]:
    category = item.get("category") if item.get("category") in CATEGORIES else "その他・分類保留"
    stance = item.get("stance") if item.get("stance") in STANCES else "その他"
    issue = item.get("issue") if item.get("issue") in ISSUES else "不明"
    try:
        confidence = float(item.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    if confidence <= 0.0 and category != "その他・分類保留":
        confidence = 0.72
    risk = item.get("risk") if item.get("risk") in {"none", "low", "medium", "high"} else "medium"
    return {
        "category": category,
        "stance": stance,
        "issue": issue,
        "summary": str(item.get("summary") or "").strip(),
        "reason": str(item.get("reason") or "").strip(),
        "confidence": max(0.0, min(1.0, confidence)),
        "article_usable": bool(item.get("article_usable", False)),
        "risk": risk,
    }


def fallback(text: str, reason: str) -> dict[str, Any]:
    risk = "high" if any(word in text for word in ["売国", "反日", "独裁", "陰謀", "ナチ"]) else "medium"
    return {
        "category": "その他・分類保留",
        "stance": "その他",
        "issue": "不明",
        "summary": "明確な賛否や主論点を判定しにくい反応。",
        "reason": reason,
        "confidence": 0.0,
        "article_usable": False,
        "risk": risk,
    }


def harmonize(result: dict[str, Any]) -> dict[str, Any]:
    fixed = dict(result)
    category = fixed.get("category")
    if category in {"改憲賛成・推進", "9条・自衛隊明記に賛成", "緊急事態条項に賛成"} and fixed.get("stance") not in {"改憲支持", "項目別賛成"}:
        fixed["stance"] = "項目別賛成" if category != "改憲賛成・推進" else "改憲支持"
    elif category in {"改憲反対・護憲", "9条・自衛隊明記に反対", "緊急事態条項に反対"} and fixed.get("stance") not in {"改憲反対", "項目別反対", "慎重"}:
        fixed["stance"] = "項目別反対" if category != "改憲反対・護憲" else "改憲反対"
    elif category == "国民投票法・広告規制を重視":
        fixed["stance"] = "手続き重視"
        fixed["issue"] = "国民投票法"
    return fixed


def classify_batch(model: str, rows: list[dict[str, Any]], timeout: int) -> list[dict[str, Any]]:
    items = [{"id": i, "text": clean_text(row.get("text", ""))[:850]} for i, row in enumerate(rows, 1)]
    prompt = PROMPT.format(
        categories="\n".join(f"- {category}" for category in CATEGORIES),
        stances=", ".join(STANCES),
        issues=", ".join(ISSUES),
        items=json.dumps(items, ensure_ascii=False, indent=2),
    )
    response = call_ollama(model, prompt, timeout)
    try:
        parsed = parse_array(response)
    except Exception:
        if len(rows) > 1:
            results: list[dict[str, Any]] = []
            for row in rows:
                results.extend(classify_batch(model, [row], timeout))
            return results
        raise
    by_id = {}
    for item in parsed:
        try:
            by_id[int(item.get("id"))] = harmonize(normalize(item))
        except Exception:
            continue
    results = []
    for i, row in enumerate(rows, 1):
        results.append(by_id.get(i, fallback(clean_text(row.get("text", "")), "missing batch result")))
    return results


def write_markdown(rows: list[dict[str, Any]], output: Path) -> None:
    buckets: OrderedDict[str, list[dict[str, Any]]] = OrderedDict((category, []) for category in CATEGORIES)
    for row in rows:
        buckets.setdefault(row["classification"]["category"], []).append(row)
    lines = ["# 憲法改正論議 X反応 Ollama分類", "", f"総件数: {len(rows)}", "", "## 分類件数", "", "| 分類 | 件数 |", "| --- | ---: |"]
    for category, items in buckets.items():
        lines.append(f"| {category} | {len(items)} |")
    for category, items in buckets.items():
        lines += ["", f"## {category}", "", f"{len(items)}件", ""]
        for index, row in enumerate(items[:12], 1):
            c = row["classification"]
            text = clean_text(row.get("text", ""))
            lines += [
                f"{index}. {c['summary'] or text[:160]}",
                f"   - stance: {c['stance']} / issue: {c.get('issue', '')} / confidence: {c['confidence']:.2f} / risk: {c['risk']}",
                f"   - 理由: {c['reason']}",
                f"   - 投稿要旨: {text[:260]}",
                f"   - URL: {row.get('url', '')}",
                "",
            ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify constitutional amendment reactions with Ollama")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--markdown", default="")
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=220)
    parser.add_argument("--sleep", type=float, default=0.0)
    args = parser.parse_args()

    rows = json.loads(resolve(args.input).read_text(encoding="utf-8"))
    if args.limit:
        rows = rows[: args.limit]
    for row in rows:
        row["text"] = clean_text(row.get("text", ""))
    print(f"入力: {resolve(args.input)} ({len(rows)}件)", flush=True)
    if not check_ollama():
        print("Ollamaに接続できません。ollama serve を確認してください。", flush=True)
        return 1

    classified = []
    errors = 0
    for start in range(0, len(rows), args.batch_size):
        batch = rows[start : start + args.batch_size]
        print(f"[{start + 1}-{start + len(batch)}/{len(rows)}] classify", flush=True)
        try:
            results = classify_batch(args.model, batch, args.timeout)
        except Exception as exc:
            errors += len(batch)
            print(f"  ERROR: {exc}", flush=True)
            results = [fallback(clean_text(row.get("text", "")), f"classification_error: {exc}") for row in batch]
        for row, classification in zip(batch, results):
            new_row = dict(row)
            new_row["classification"] = classification
            classified.append(new_row)
        if args.sleep:
            time.sleep(args.sleep)

    output = resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(classified, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JSON保存: {output}", flush=True)
    if args.markdown:
        markdown = resolve(args.markdown)
        write_markdown(classified, markdown)
        print(f"Markdown保存: {markdown}", flush=True)
    print(f"完了: {len(classified)}件 / エラー {errors}件", flush=True)
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
