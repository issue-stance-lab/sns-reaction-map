#!/usr/bin/env python3
"""Structured Ollama classification for Henoko reactions.

Adds multi-layer targets, separate quote/claim stances, issue, confidence level,
and alternate category candidates before assigning the final category. This is
designed to reduce mistakes where quoted news titles are confused with the
poster's own stance.
"""

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


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
TAGS_URL = "http://127.0.0.1:11434/api/tags"

CATEGORIES = [
    "安全管理・引率責任を問題視",
    "文科省判断支持・政治的中立性違反を指摘",
    "文科省判断への反発・平和教育萎縮を懸念",
    "政治利用・反基地運動批判",
    "追悼・慰霊への共感",
    "報道・行政対応批判",
    "基地問題・反基地論への接続",
    "学校・教育委員会批判",
    "事故原因・再発防止への関心",
    "事実確認・情報共有",
    "未確認・過激表現",
    "その他・分類保留",
]

TARGETS = [
    "文科省判断",
    "学校・引率",
    "安全管理",
    "反基地運動",
    "平和教育",
    "報道・行政",
    "追悼・慰霊",
    "基地問題",
    "不明",
]

STANCES = ["評価する", "評価しない", "問題視", "批判", "支持", "中立", "未確認", "保留", "その他"]
ISSUES = ["政治的中立性", "平和教育の萎縮", "安全管理", "引率責任", "政治利用", "報道姿勢", "追悼", "事故原因", "基地問題", "不明"]
QUOTE_DIRECTIONS = ["引用元に賛成", "引用元に反対", "引用元を紹介", "引用なし", "判定不能"]
QUOTE_STANCES = ["支持", "反対", "紹介", "皮肉", "引用なし", "判定不能"]
CONFIDENCE_LEVELS = ["high", "medium", "low"]

PROMPT = """あなたはSNS投稿の構造化分類器です。説明や思考は不要です。
以下の投稿リストを分類し、JSON配列のみを返してください。Markdown、説明文、コメントは禁止。JSONのキーと文字列は必ずダブルクォートで囲んでください。

対象テーマ:
辺野古沖の高校生ボート転覆死亡事故、学校・引率責任、文科省の教育基本法違反認定、平和教育の萎縮懸念、政治的中立性をめぐるSNS反応。

最重要ルール:
- 記事見出し・引用部分の立場ではなく、投稿者本人が最後に何を評価/批判しているかで判定する。
- 「何が〜だ」「むしろ〜」「〜やねん」「おかしい」「草」などは、引用元・記事見出しへの反発である可能性が高い。
- 「抗議声明…平和教育活動を萎縮させる危険」という見出しに対して「何が萎縮」「むしろ萎縮しろ」と言う投稿は、文科省判断支持側。
- 「文科省が教育内容を教育基本法違反としたことは疑問」「教育現場の萎縮を懸念」は、文科省判断への反発側。
- 「安全管理がずさん」「引率責任」「未成年を危険な現場」は、安全管理・引率責任。
- 複数論点がある場合は、topic_target / actor_target / criticized_target を分ける。
- 引用元の人物・媒体への態度と、引用元が示す主張内容への態度を分ける。
- review_required に逃げず、confidence_level と alternate_categories で曖昧さを表す。

カテゴリ:
{categories}

target候補: {targets}
stance_to_target候補: {stances}
issue候補: {issues}
quote_direction候補: {quote_directions}
stance_to_quoted_author候補: {quote_stances}
stance_to_quoted_claim候補: {quote_stances}

confidence_level:
- high: 投稿者本人の対象・賛否・論点が明確
- medium: 引用や複数論点はあるが、主分類はおおむね可能
- low: 短文、リンク共有、皮肉、複数解釈で候補を残すべき

review_required は、未確認の断定、強い個人攻撃、または confidence_level が low の場合だけ true。

投稿リスト:
{items}

出力JSON配列。各要素は必ずこの形式:
[
  {{
    "id": 1,
    "topic_target": "辺野古高校生死亡事故",
    "actor_target": "文科省判断",
    "criticized_target": "抗議声明側",
    "target": "文科省判断",
    "stance_to_target": "評価する",
    "issue": "政治的中立性",
    "quote_direction": "引用元に反対",
    "stance_to_quoted_author": "反対",
    "stance_to_quoted_claim": "反対",
    "category": "文科省判断支持・政治的中立性違反を指摘",
    "alternate_categories": [
      {{"category": "政治利用・反基地運動批判", "confidence": 0.22}}
    ],
    "summary": "中立的な1文要約",
    "reason": "分類理由を短く",
    "confidence": 0.0,
    "confidence_level": "low / medium / high",
    "article_usable": true,
    "risk": "none / low / medium / high",
    "review_required": true,
    "review_reason": "確認が必要な理由"
  }}
]"""


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def clean_text(text: str) -> str:
    return text.replace("\tSTART\t", "").replace("\tEND\t", "").replace("START", "").replace("END", "").strip()


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
            "options": {"temperature": 0.05, "num_predict": 3200},
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


def normalize(item: dict) -> dict:
    def pick(key: str, allowed: list[str], default: str) -> str:
        value = str(item.get(key) or "")
        return value if value in allowed else default

    try:
        confidence = float(item.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    risk = item.get("risk") if item.get("risk") in {"none", "low", "medium", "high"} else "medium"
    confidence_level = item.get("confidence_level") if item.get("confidence_level") in CONFIDENCE_LEVELS else (
        "high" if confidence >= 0.85 else "medium" if confidence >= 0.68 else "low"
    )
    review_required = bool(item.get("review_required", False)) or confidence_level == "low"

    alternate_categories = item.get("alternate_categories")
    if not isinstance(alternate_categories, list):
        alternate_categories = []
    normalized_alternates = []
    for alt in alternate_categories[:3]:
        if not isinstance(alt, dict):
            continue
        category = str(alt.get("category") or "")
        if category not in CATEGORIES:
            continue
        try:
            alt_confidence = float(alt.get("confidence", 0.0))
        except (TypeError, ValueError):
            alt_confidence = 0.0
        normalized_alternates.append({"category": category, "confidence": max(0.0, min(1.0, alt_confidence))})

    return {
        "topic_target": str(item.get("topic_target") or "辺野古高校生死亡事故").strip(),
        "actor_target": pick("actor_target", TARGETS, "不明"),
        "criticized_target": pick("criticized_target", TARGETS + ["抗議声明側", "引用元", "不特定"], "不明"),
        "target": pick("target", TARGETS, "不明"),
        "stance_to_target": pick("stance_to_target", STANCES, "その他"),
        "issue": pick("issue", ISSUES, "不明"),
        "quote_direction": pick("quote_direction", QUOTE_DIRECTIONS, "判定不能"),
        "stance_to_quoted_author": pick("stance_to_quoted_author", QUOTE_STANCES, "判定不能"),
        "stance_to_quoted_claim": pick("stance_to_quoted_claim", QUOTE_STANCES, "判定不能"),
        "category": pick("category", CATEGORIES, "その他・分類保留"),
        "alternate_categories": normalized_alternates,
        "summary": str(item.get("summary") or "").strip(),
        "reason": str(item.get("reason") or "").strip(),
        "confidence": confidence,
        "confidence_level": confidence_level,
        "article_usable": bool(item.get("article_usable", False)),
        "risk": risk,
        "review_required": review_required,
        "review_reason": str(item.get("review_reason") or ("confidence < 0.75" if confidence < 0.75 else "")).strip(),
    }


def apply_rule_override(text: str, result: dict) -> dict:
    support_markers = ["何が萎縮させる危険", "寧ろ萎縮しろ", "明白な教育基本法違反", "どう考えても政治的中立性違反", "教育基本法第14条2項", "特定の政治活動に加担"]
    oppose_markers = ["文科省が教育内容を教育基本法違反としたことは疑問", "違法認定は政治色", "教育現場の萎縮", "学ぶ機会を奪わないで", "平和教育活動を萎縮", "撤回求める"]
    safety_markers = ["安全管理", "引率", "ずさん", "再発防止", "危険な現場"]

    fixed = dict(result)
    if any(marker in text for marker in support_markers):
        fixed.update(
            {
                "target": "文科省判断",
                "actor_target": "文科省判断",
                "criticized_target": "抗議声明側" if "萎縮" in text else fixed.get("criticized_target", "不明"),
                "stance_to_target": "評価する",
                "issue": "政治的中立性",
                "quote_direction": "引用元に反対" if "萎縮" in text else fixed.get("quote_direction", "判定不能"),
                "stance_to_quoted_author": "反対" if "萎縮" in text else fixed.get("stance_to_quoted_author", "判定不能"),
                "stance_to_quoted_claim": "反対" if "萎縮" in text else fixed.get("stance_to_quoted_claim", "判定不能"),
                "category": "文科省判断支持・政治的中立性違反を指摘",
                "summary": "文科省判断を支持し、学校教育の政治的中立性違反を指摘する反応。",
                "reason": "政治的中立性違反や教育基本法違反認定を支持する表現があるため。",
                "confidence": max(float(fixed.get("confidence", 0.0)), 0.88),
                "confidence_level": "high",
                "review_required": False,
                "review_reason": "",
            }
        )
    elif any(marker in text for marker in oppose_markers):
        fixed.update(
            {
                "target": "文科省判断",
                "actor_target": "文科省判断",
                "criticized_target": "文科省判断",
                "stance_to_target": "評価しない",
                "issue": "平和教育の萎縮",
                "category": "文科省判断への反発・平和教育萎縮を懸念",
                "summary": "文科省の教育基本法違反認定が行きすぎで、教育現場の萎縮につながると懸念する反応。",
                "reason": "文科省判断への疑問や平和教育の萎縮懸念を示しているため。",
                "confidence": max(float(fixed.get("confidence", 0.0)), 0.86),
                "confidence_level": "high",
                "review_required": False,
                "review_reason": "",
            }
        )
    elif any(marker in text for marker in safety_markers) and "教育基本法" not in text:
        fixed.update(
            {
                "target": "安全管理",
                "actor_target": "安全管理",
                "criticized_target": "学校・引率",
                "stance_to_target": "問題視",
                "issue": "安全管理",
                "category": "安全管理・引率責任を問題視",
                "summary": "事故に至った安全管理や引率責任を問題視する反応。",
                "reason": "安全管理、引率、再発防止が主眼のため。",
                "confidence": max(float(fixed.get("confidence", 0.0)), 0.82),
                "confidence_level": "medium" if fixed.get("confidence", 0.0) < 0.85 else fixed.get("confidence_level", "medium"),
                "review_required": False,
                "review_reason": "",
            }
        )
    confidence = float(fixed.get("confidence", 0.0))
    fixed["confidence_level"] = fixed.get("confidence_level") or ("high" if confidence >= 0.85 else "medium" if confidence >= 0.68 else "low")
    fixed["review_required"] = bool(fixed.get("review_required")) or fixed.get("confidence_level") == "low" or fixed.get("risk") in {"high"}
    if fixed["review_required"] and not fixed.get("review_reason"):
        fixed["review_reason"] = "低信頼または高リスクのため確認が必要"
    return harmonize_classification(fixed)


def harmonize_classification(result: dict) -> dict:
    fixed = dict(result)
    category = fixed.get("category")
    if category == "文科省判断支持・政治的中立性違反を指摘":
        fixed["target"] = "文科省判断"
        fixed["actor_target"] = "文科省判断"
        if fixed.get("stance_to_target") not in {"評価する", "支持"}:
            fixed["stance_to_target"] = "評価する"
        fixed["issue"] = "政治的中立性"
    elif category == "文科省判断への反発・平和教育萎縮を懸念":
        fixed["target"] = "文科省判断"
        fixed["actor_target"] = "文科省判断"
        fixed["criticized_target"] = "文科省判断"
        if fixed.get("stance_to_target") not in {"評価しない", "批判", "問題視"}:
            fixed["stance_to_target"] = "評価しない"
        fixed["issue"] = "平和教育の萎縮"
    elif category == "安全管理・引率責任を問題視":
        fixed["target"] = "安全管理"
        fixed["actor_target"] = fixed.get("actor_target") if fixed.get("actor_target") in {"学校・引率", "安全管理"} else "安全管理"
        fixed["criticized_target"] = fixed.get("criticized_target") if fixed.get("criticized_target") != "不明" else "学校・引率"
        fixed["stance_to_target"] = "問題視"
        fixed["issue"] = "安全管理"
    return fixed


def classify_batch(model: str, rows: list[dict], timeout: int) -> list[dict]:
    items = [{"id": i, "text": clean_text(row.get("text", ""))[:900]} for i, row in enumerate(rows, 1)]
    prompt = PROMPT.format(
        categories="\n".join(f"- {c}" for c in CATEGORIES),
        targets=", ".join(TARGETS),
        stances=", ".join(STANCES),
        issues=", ".join(ISSUES),
        quote_directions=", ".join(QUOTE_DIRECTIONS),
        quote_stances=", ".join(QUOTE_STANCES),
        items=json.dumps(items, ensure_ascii=False, indent=2),
    )
    response = call_ollama(model, prompt, timeout)
    try:
        parsed = parse_array(response)
    except Exception:
        if len(rows) > 1:
            results: list[dict] = []
            for row in rows:
                results.extend(classify_batch(model, [row], timeout))
            return results
        raise
    by_id = {}
    for item in parsed:
        try:
            by_id[int(item.get("id"))] = normalize(item)
        except Exception:
            continue
    results = []
    for i, row in enumerate(rows, 1):
        base = by_id.get(
            i,
            {
                "target": "不明",
                "topic_target": "辺野古高校生死亡事故",
                "actor_target": "不明",
                "criticized_target": "不明",
                "stance_to_target": "その他",
                "issue": "不明",
                "quote_direction": "判定不能",
                "stance_to_quoted_author": "判定不能",
                "stance_to_quoted_claim": "判定不能",
                "category": "その他・分類保留",
                "alternate_categories": [],
                "summary": "",
                "reason": "missing batch result",
                "confidence": 0.0,
                "confidence_level": "low",
                "article_usable": False,
                "risk": "medium",
                "review_required": True,
                "review_reason": "missing batch result",
            },
        )
        results.append(apply_rule_override(clean_text(row.get("text", "")), base))
    return results


def write_markdown(rows: list[dict], output: Path) -> None:
    buckets: OrderedDict[str, list[dict]] = OrderedDict((c, []) for c in CATEGORIES)
    for row in rows:
        buckets[row["classification"]["category"]].append(row)
    lines = [
        "# 辺野古高校生死亡事故 構造化分類版",
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
    lines += ["", "## 要レビュー", ""]
    review_count = sum(1 for row in rows if row["classification"].get("review_required"))
    lines += [f"要レビュー: {review_count}件", ""]
    for category, items in buckets.items():
        lines += [f"## {category}", "", f"{len(items)}件", ""]
        for i, row in enumerate(items, 1):
            c = row["classification"]
            lines += [
                f"{i}. {c['summary'] or row.get('text', '')[:160]}",
                f"   - topic: {c.get('topic_target', '')} / actor: {c.get('actor_target', '')} / criticized: {c.get('criticized_target', '')}",
                f"   - target: {c['target']} / stance: {c['stance_to_target']} / issue: {c['issue']} / quote: {c['quote_direction']}",
                f"   - quoted_author: {c.get('stance_to_quoted_author', '')} / quoted_claim: {c.get('stance_to_quoted_claim', '')}",
                f"   - 信頼度: {c['confidence']:.2f} ({c.get('confidence_level', '')}) / 要レビュー: {c['review_required']} / リスク: {c['risk']} / 記事向き: {c['article_usable']}",
                f"   - 候補: {json.dumps(c.get('alternate_categories', []), ensure_ascii=False)}",
                f"   - 理由: {c['reason']}",
                f"   - レビュー理由: {c.get('review_reason', '')}",
                f"   - 元投稿: {row.get('text', '').replace(chr(10), ' / ')}",
                f"   - URL: {row.get('url', '')}",
                "",
            ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Structured classify Henoko reactions with Ollama")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--markdown", default="")
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--batch-size", type=int, default=8)
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
        print(f"[{start + 1}-{start + len(batch)}/{len(rows)}] structured classify", flush=True)
        try:
            results = classify_batch(args.model, batch, args.timeout)
        except Exception as exc:
            errors += len(batch)
            print(f"  ERROR: {exc}", flush=True)
            results = []
            for row in batch:
                fallback = {
                    "target": "不明",
                    "topic_target": "辺野古高校生死亡事故",
                    "actor_target": "不明",
                    "criticized_target": "不明",
                    "stance_to_target": "その他",
                    "issue": "不明",
                    "quote_direction": "判定不能",
                    "stance_to_quoted_author": "判定不能",
                    "stance_to_quoted_claim": "判定不能",
                    "category": "その他・分類保留",
                    "alternate_categories": [],
                    "summary": "",
                    "reason": f"classification_error: {exc}",
                    "confidence": 0.0,
                    "confidence_level": "low",
                    "article_usable": False,
                    "risk": "medium",
                    "review_required": True,
                    "review_reason": "classification_error",
                }
                results.append(apply_rule_override(clean_text(row.get("text", "")), fallback))
        for row, classification in zip(batch, results):
            new_row = dict(row)
            new_row["classification"] = classification
            classified.append(new_row)
        if args.sleep:
            time.sleep(args.sleep)

    output_path = resolve(args.output)
    output_path.write_text(json.dumps(classified, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JSON保存: {output_path}", flush=True)
    if args.markdown:
        markdown_path = resolve(args.markdown)
        write_markdown(classified, markdown_path)
        print(f"Markdown保存: {markdown_path}", flush=True)
    print(f"完了: {len(classified)}件 / エラー {errors}件", flush=True)
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
