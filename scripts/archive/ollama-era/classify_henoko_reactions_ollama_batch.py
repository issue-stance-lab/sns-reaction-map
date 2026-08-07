#!/usr/bin/env python3
"""Classify Henoko high-school-student accident reactions with Ollama."""

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
    "追悼・慰霊への共感",
    "学校・教育委員会批判",
    "教育基本法違反視",
    "政治利用・反基地運動批判",
    "事故原因・安全管理への関心",
    "基地問題・反基地論への接続",
    "報道・行政対応批判",
    "事実確認・情報共有",
    "未確認・過激表現",
    "その他・分類保留",
]

STANCE_LABELS = ["追悼支持", "批判", "反発", "制度論", "中立", "未確認", "保留", "その他"]

PROMPT = """あなたはSNS投稿の論調分類器です。説明や思考は不要です。
以下の投稿リストを分類し、JSON配列のみを返してください。

対象テーマ:
辺野古の高校生死亡事故、および学校・教育現場での追悼/慰霊/黙祷や、教育基本法違反ではないかという反応。

カテゴリ:
{categories}

立場ラベル: {stance_labels}

分類ルール:
- 亡くなった高校生への追悼、黙祷、慰霊を支持・共感する投稿は「追悼・慰霊への共感」。
- 学校、教師、教育委員会、校長、県教委などの対応を批判する投稿は「学校・教育委員会批判」。
- 「教育基本法違反」「政治的中立性」「学校教育で扱うべきでない」が主眼なら「教育基本法違反視」。
- 「死亡事故を反基地運動に利用している」「政治利用だ」が主眼なら「政治利用・反基地運動批判」。
- 事故原因、警備、安全管理、道路、ダンプ、抗議現場の危険性が主眼なら「事故原因・安全管理への関心」。
- 米軍基地、辺野古移設、反基地/基地容認の大きな政治論に接続する投稿は「基地問題・反基地論への接続」。
- 報道機関、文科省、行政、政治家の対応への批判が主眼なら「報道・行政対応批判」。
- ニュース共有、事実確認、リンク紹介中心なら「事実確認・情報共有」。
- 根拠が薄い断定、陰謀論、強い個人攻撃、差別的/過激表現は「未確認・過激表現」。
- 投稿本文が短すぎる、意味不明、対象外なら「その他・分類保留」。
- 攻撃的表現はsummaryで中和する。
- confidence は 0.0 から 1.0。
- article_usable は代表意見として記事で使いやすい場合 true。

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
    return text.replace("\tSTART\t", "").replace("\tEND\t", "").strip()


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


def classify_batch(model: str, rows: list[dict], timeout: int) -> list[dict]:
    items = [{"id": i, "text": clean_text(row.get("text", ""))[:700]} for i, row in enumerate(rows, 1)]
    prompt = PROMPT.format(
        categories="\n".join(f"- {c}" for c in CATEGORIES),
        stance_labels=", ".join(STANCE_LABELS),
        items=json.dumps(items, ensure_ascii=False, indent=2),
    )
    parsed = parse_array(call_ollama(model, prompt, timeout))
    by_id = {}
    for item in parsed:
        try:
            by_id[int(item.get("id"))] = normalize(item)
        except Exception:
            continue
    return [
        by_id.get(
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
        for i in range(1, len(rows) + 1)
    ]


def write_markdown(rows: list[dict], output: Path) -> None:
    buckets: OrderedDict[str, list[dict]] = OrderedDict((c, []) for c in CATEGORIES)
    for row in rows:
        buckets[row["classification"]["category"]].append(row)
    lines = [
        "# 辺野古高校生死亡事故 SNS反応 Ollama分類",
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
    parser = argparse.ArgumentParser(description="Classify Henoko reactions with Ollama")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--markdown", default="")
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--sleep", type=float, default=0.0)
    args = parser.parse_args()

    input_path = resolve_path(args.input)
    rows = json.loads(input_path.read_text(encoding="utf-8"))
    if args.limit:
        rows = rows[: args.limit]
    for row in rows:
        row["text"] = clean_text(row.get("text", ""))
    print(f"入力: {input_path} ({len(rows)}件)", flush=True)
    if not check_ollama():
        print("Ollamaに接続できません。ollama serve を確認してください。", flush=True)
        return 1

    classified = []
    errors = 0
    for start in range(0, len(rows), args.batch_size):
        batch = rows[start : start + args.batch_size]
        print(f"[{start + 1}-{start + len(batch)}/{len(rows)}] batch classify", flush=True)
        try:
            results = classify_batch(args.model, batch, args.timeout)
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

    output_path = resolve_path(args.output)
    output_path.write_text(json.dumps(classified, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JSON保存: {output_path}", flush=True)
    if args.markdown:
        markdown_path = resolve_path(args.markdown)
        write_markdown(classified, markdown_path)
        print(f"Markdown保存: {markdown_path}", flush=True)
    print(f"完了: {len(classified)}件 / エラー {errors}件", flush=True)
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
