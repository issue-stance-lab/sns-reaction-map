#!/usr/bin/env python3
"""Structured Ollama classification for constitutional amendment reactions."""

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

TARGETS = [
    "改憲全般",
    "自民党改憲案",
    "9条・自衛隊明記",
    "緊急事態条項",
    "国民投票法",
    "広告規制",
    "政党・議員",
    "国会発議",
    "情報共有",
    "不明",
]

STANCES = ["評価する", "評価しない", "支持", "反対", "問題視", "慎重", "中立", "未確認", "その他"]
ISSUES = ["9条・自衛隊", "緊急事態条項", "国民投票法", "広告規制", "改憲全般", "手続き", "政党姿勢", "情報共有", "不明"]
QUOTE_STANCES = ["支持", "反対", "紹介", "皮肉", "引用なし", "判定不能"]
POST_TYPES = ["意見表明", "情報共有", "引用元への反論", "政党・議員批判", "疑問・問題提起", "感情的反応", "要確認・保留"]
CONFIDENCE_LEVELS = ["high", "medium", "low"]

PROMPT = """あなたはSNS投稿の構造化分類器です。説明や思考は不要です。
以下の投稿リストを分類し、JSON配列のみを返してください。Markdownは禁止。キーと文字列は必ずダブルクォートにしてください。

対象テーマ:
日本の憲法改正論議。改憲全般、9条・自衛隊明記、緊急事態条項、国民投票法・広告規制、国会発議、政党姿勢をめぐるX反応。

最重要ルール:
- Yahoo検索のハイライト文字列 START / END は無視する。
- 記事見出し・引用部分ではなく、投稿者本人が最後に何を評価/批判しているかで判定する。
- 「賛成」「反対」の両方が入る場合、投稿者本人が何に賛成/反対しているかを target と stance_to_target で分ける。
- 「憲法改正には賛成だが自民党草案には反対」は、target が自民党改憲案なら stance_to_target は評価しない。改憲全般への態度は summary/reason に残す。
- 「国民投票法改正に反対」は target を国民投票法または広告規制にし、issue は国民投票法/広告規制。
- 「自衛隊明記すべき」は target を9条・自衛隊明記、stance_to_target は評価する/支持。
- 「自衛隊明記不要」「9条改悪」は target を9条・自衛隊明記、stance_to_target は評価しない/反対。
- 「緊急事態条項が必要」は target を緊急事態条項、stance_to_target は評価する/支持。
- 「緊急事態条項は危険」は target を緊急事態条項、stance_to_target は評価しない/反対。
- 引用元の人物・媒体への態度と、引用元が示す主張内容への態度を分ける。
- 攻撃的表現や未確認断定は summary で中和し、risk を high にする。

カテゴリ:
{categories}

target候補: {targets}
stance_to_target候補: {stances}
issue候補: {issues}
stance_to_quoted_author候補: {quote_stances}
stance_to_quoted_claim候補: {quote_stances}
post_type候補: {post_types}

confidence_level:
- high: 投稿者本人の対象・賛否・論点が明確
- medium: 引用や複数論点はあるが主分類は可能
- low: 短文、リンク共有、皮肉、複数解釈で候補を残すべき

投稿リスト:
{items}

出力JSON配列。各要素は必ずこの形式:
[
  {{
    "id": 1,
    "topic_target": "憲法改正論議",
    "actor_target": "9条・自衛隊明記",
    "criticized_target": "自民党改憲案",
    "target": "9条・自衛隊明記",
    "stance_to_target": "評価する",
    "issue": "9条・自衛隊",
    "stance_to_quoted_author": "反対",
    "stance_to_quoted_claim": "支持",
    "post_type": "意見表明",
    "category": "9条・自衛隊明記に賛成",
    "alternate_categories": [
      {{"category": "改憲賛成・推進", "confidence": 0.22}}
    ],
    "summary": "投稿者本人の主張を中立的に要約",
    "reason": "どの表現から分類したかを短く説明",
    "confidence": 0.0,
    "confidence_level": "low / medium / high",
    "article_usable": true,
    "risk": "none / low / medium / high",
    "review_required": false,
    "review_reason": ""
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
            "options": {"temperature": 0.05, "num_predict": 3400},
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


def pick(item: dict[str, Any], key: str, allowed: list[str], default: str) -> str:
    value = str(item.get(key) or "")
    return value if value in allowed else default


def normalize(item: dict[str, Any]) -> dict[str, Any]:
    try:
        confidence = float(item.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))
    if confidence <= 0 and pick(item, "category", CATEGORIES, "その他・分類保留") != "その他・分類保留":
        confidence = 0.72
    confidence_level = item.get("confidence_level") if item.get("confidence_level") in CONFIDENCE_LEVELS else (
        "high" if confidence >= 0.85 else "medium" if confidence >= 0.68 else "low"
    )
    alternates = item.get("alternate_categories")
    normalized_alternates = []
    if isinstance(alternates, list):
        for alt in alternates[:3]:
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
    risk = item.get("risk") if item.get("risk") in {"none", "low", "medium", "high"} else "medium"
    summary = str(item.get("summary") or "").strip()
    if summary in {"中立的な1文要約", "投稿者本人の主張を中立的に要約"}:
        summary = ""
    reason = str(item.get("reason") or "").strip()
    if reason in {"分類理由を短く", "どの表現から分類したかを短く説明"}:
        reason = ""
    return harmonize(
        {
            "topic_target": str(item.get("topic_target") or "憲法改正論議").strip(),
            "actor_target": pick(item, "actor_target", TARGETS, "不明"),
            "criticized_target": pick(item, "criticized_target", TARGETS + ["引用元", "不特定"], "不明"),
            "target": pick(item, "target", TARGETS, "不明"),
            "stance_to_target": pick(item, "stance_to_target", STANCES, "その他"),
            "issue": pick(item, "issue", ISSUES, "不明"),
            "stance_to_quoted_author": pick(item, "stance_to_quoted_author", QUOTE_STANCES, "判定不能"),
            "stance_to_quoted_claim": pick(item, "stance_to_quoted_claim", QUOTE_STANCES, "判定不能"),
            "post_type": pick(item, "post_type", POST_TYPES, "要確認・保留"),
            "category": pick(item, "category", CATEGORIES, "その他・分類保留"),
            "alternate_categories": normalized_alternates,
            "summary": summary,
            "reason": reason,
            "confidence": confidence,
            "confidence_level": confidence_level,
            "article_usable": bool(item.get("article_usable", False)),
            "risk": risk,
            "review_required": bool(item.get("review_required", False)) or confidence_level == "low" or risk == "high",
            "review_reason": str(item.get("review_reason") or "").strip(),
        }
    )


def harmonize(result: dict[str, Any]) -> dict[str, Any]:
    fixed = dict(result)
    category = fixed.get("category")
    if category == "改憲賛成・推進":
        fixed["target"] = "改憲全般"
        fixed["issue"] = "改憲全般"
        if fixed.get("stance_to_target") not in {"評価する", "支持"}:
            fixed["stance_to_target"] = "支持"
    elif category == "改憲反対・護憲":
        fixed["target"] = "改憲全般"
        fixed["issue"] = "改憲全般"
        if fixed.get("stance_to_target") not in {"評価しない", "反対", "慎重"}:
            fixed["stance_to_target"] = "反対"
    elif category == "9条・自衛隊明記に賛成":
        fixed["target"] = "9条・自衛隊明記"
        fixed["issue"] = "9条・自衛隊"
        fixed["stance_to_target"] = "支持"
    elif category == "9条・自衛隊明記に反対":
        fixed["target"] = "9条・自衛隊明記"
        fixed["issue"] = "9条・自衛隊"
        fixed["stance_to_target"] = "反対"
    elif category == "緊急事態条項に賛成":
        fixed["target"] = "緊急事態条項"
        fixed["issue"] = "緊急事態条項"
        fixed["stance_to_target"] = "支持"
    elif category == "緊急事態条項に反対":
        fixed["target"] = "緊急事態条項"
        fixed["issue"] = "緊急事態条項"
        fixed["stance_to_target"] = "反対"
    elif category == "国民投票法・広告規制を重視":
        fixed["target"] = "国民投票法" if fixed.get("target") not in {"広告規制"} else fixed["target"]
        fixed["issue"] = "国民投票法" if fixed.get("issue") not in {"広告規制"} else fixed["issue"]
        fixed["stance_to_target"] = fixed.get("stance_to_target") if fixed.get("stance_to_target") in {"問題視", "慎重", "評価しない", "支持"} else "問題視"
    if fixed.get("risk") == "high" and not fixed.get("review_reason"):
        fixed["review_reason"] = "高リスク表現を含むため確認が必要"
    if fixed.get("confidence_level") == "low" and not fixed.get("review_reason"):
        fixed["review_reason"] = "低信頼分類のため確認が必要"
    return fixed


def apply_rule_override(text: str, result: dict[str, Any]) -> dict[str, Any]:
    fixed = dict(result)
    anti_emergency = ["緊急事態条項", "国会機能維持条項"]
    referendum = ["国民投票法", "広告規制", "CM規制", "有効投票", "運動資金", "外国人寄付", "附帯決議"]
    article9_support = ["自衛隊明記", "自衛隊を明記", "自衛隊の明記", "国防", "抑止力", "国防軍"]
    anti_amend = ["憲法改正反対", "改憲反対", "憲法改悪", "今ある憲法を守れ", "平和憲法をまもれ"]
    pro_amend = ["憲法改正賛成", "改憲賛成", "憲法改正は賛成", "憲法改正すべき"]
    party_attack = ["自民党", "中道", "有田芳生", "維新", "国民民主", "参政", "議員"]
    extreme = ["カルト", "狂ってる", "売国", "反日", "独裁", "ナチ", "陰謀"]

    if any(marker in text for marker in referendum):
        fixed.update(
            {
                "target": "国民投票法",
                "actor_target": "国民投票法",
                "issue": "国民投票法",
                "stance_to_target": "問題視" if any(m in text for m in ["反対", "問題", "危険", "少数"]) else "慎重",
                "category": "国民投票法・広告規制を重視",
                "post_type": "意見表明",
                "summary": "国民投票法や広告規制など、改憲手続きの公平性を問題視する反応。",
                "reason": "国民投票法・広告規制・有効投票など手続きへの言及が中心のため。",
                "confidence": max(float(fixed.get("confidence", 0.0)), 0.86),
                "confidence_level": "high",
                "article_usable": True,
            }
        )
    elif any(marker in text for marker in anti_emergency) and any(m in text for m in ["反対", "危険", "不要", "怖", "人権", "独裁"]):
        fixed.update(
            {
                "target": "緊急事態条項",
                "actor_target": "緊急事態条項",
                "issue": "緊急事態条項",
                "stance_to_target": "反対",
                "category": "緊急事態条項に反対",
                "summary": "緊急事態条項を権限集中や人権制限のリスクとして警戒する反応。",
                "reason": "緊急事態条項への反対・危険視が主眼のため。",
                "confidence": max(float(fixed.get("confidence", 0.0)), 0.84),
                "confidence_level": "high",
            }
        )
    elif any(marker in text for marker in article9_support) and not any(m in text for m in ["不要", "反対", "改悪"]):
        fixed.update(
            {
                "target": "9条・自衛隊明記",
                "actor_target": "9条・自衛隊明記",
                "issue": "9条・自衛隊",
                "stance_to_target": "支持",
                "category": "9条・自衛隊明記に賛成",
                "summary": "自衛隊明記や国防上の必要性から憲法改正を支持する反応。",
                "reason": "自衛隊明記・国防・抑止力への肯定的言及があるため。",
                "confidence": max(float(fixed.get("confidence", 0.0)), 0.82),
                "confidence_level": "high",
            }
        )
    elif any(marker in text for marker in anti_amend):
        fixed.update(
            {
                "target": "改憲全般",
                "actor_target": "改憲全般",
                "issue": "改憲全般",
                "stance_to_target": "反対",
                "category": "改憲反対・護憲",
                "summary": "憲法改正に反対し、現行憲法の維持を求める反応。",
                "reason": "改憲反対・護憲の表現が明示されているため。",
                "confidence": max(float(fixed.get("confidence", 0.0)), 0.86),
                "confidence_level": "high",
            }
        )
    elif any(marker in text for marker in pro_amend):
        fixed.update(
            {
                "target": "改憲全般",
                "actor_target": "改憲全般",
                "issue": "改憲全般",
                "stance_to_target": "支持",
                "category": "改憲賛成・推進",
                "summary": "憲法改正を進めるべきだとする反応。",
                "reason": "改憲賛成・推進の表現が明示されているため。",
                "confidence": max(float(fixed.get("confidence", 0.0)), 0.84),
                "confidence_level": "high",
            }
        )
    if any(marker in text for marker in extreme):
        fixed["risk"] = "high"
        fixed["review_required"] = True
        fixed["review_reason"] = fixed.get("review_reason") or "攻撃的・過激表現を含むため確認が必要"
    if fixed.get("category") not in {"政党・議員批判", "未確認・過激表現"} and any(marker in text for marker in party_attack) and fixed.get("confidence_level") != "high":
        fixed["alternate_categories"] = [{"category": "政党・議員批判", "confidence": 0.35}] + list(fixed.get("alternate_categories") or [])[:2]
    return harmonize(fixed)


def fallback(text: str, reason: str) -> dict[str, Any]:
    risk = "high" if any(word in text for word in ["売国", "反日", "独裁", "陰謀", "ナチ"]) else "medium"
    return {
        "topic_target": "憲法改正論議",
        "actor_target": "不明",
        "criticized_target": "不明",
        "target": "不明",
        "stance_to_target": "その他",
        "issue": "不明",
        "stance_to_quoted_author": "判定不能",
        "stance_to_quoted_claim": "判定不能",
        "post_type": "要確認・保留",
        "category": "その他・分類保留",
        "alternate_categories": [],
        "summary": "明確な対象・賛否・論点を判定しにくい反応。",
        "reason": reason,
        "confidence": 0.0,
        "confidence_level": "low",
        "article_usable": False,
        "risk": risk,
        "review_required": True,
        "review_reason": reason,
    }


def classify_batch(model: str, rows: list[dict[str, Any]], timeout: int) -> list[dict[str, Any]]:
    items = [{"id": i, "text": clean_text(row.get("text", ""))[:900]} for i, row in enumerate(rows, 1)]
    prompt = PROMPT.format(
        categories="\n".join(f"- {category}" for category in CATEGORIES),
        targets=", ".join(TARGETS),
        stances=", ".join(STANCES),
        issues=", ".join(ISSUES),
        quote_stances=", ".join(QUOTE_STANCES),
        post_types=", ".join(POST_TYPES),
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
            by_id[int(item.get("id"))] = normalize(item)
        except Exception:
            continue
    return [
        apply_rule_override(clean_text(row.get("text", "")), by_id.get(i, fallback(clean_text(row.get("text", "")), "missing batch result")))
        for i, row in enumerate(rows, 1)
    ]


def write_markdown(rows: list[dict[str, Any]], output: Path) -> None:
    buckets: OrderedDict[str, list[dict[str, Any]]] = OrderedDict((category, []) for category in CATEGORIES)
    for row in rows:
        buckets.setdefault(row["classification"]["category"], []).append(row)
    lines = ["# 憲法改正論議 構造化分類v2", "", f"総件数: {len(rows)}", "", "## 分類件数", "", "| 分類 | 件数 |", "| --- | ---: |"]
    for category, items in buckets.items():
        lines.append(f"| {category} | {len(items)} |")
    for category, items in buckets.items():
        lines += ["", f"## {category}", "", f"{len(items)}件", ""]
        for index, row in enumerate(items[:12], 1):
            c = row["classification"]
            text = clean_text(row.get("text", ""))
            lines += [
                f"{index}. {c['summary'] or text[:160]}",
                f"   - target: {c['target']} / stance_to_target: {c['stance_to_target']} / issue: {c['issue']}",
                f"   - actor: {c['actor_target']} / criticized: {c['criticized_target']} / type: {c['post_type']}",
                f"   - quoted_author: {c['stance_to_quoted_author']} / quoted_claim: {c['stance_to_quoted_claim']}",
                f"   - confidence: {c['confidence']:.2f} ({c['confidence_level']}) / review: {c['review_required']} / risk: {c['risk']}",
                f"   - 候補: {json.dumps(c.get('alternate_categories', []), ensure_ascii=False)}",
                f"   - 理由: {c['reason']}",
                f"   - 投稿要旨: {text[:260]}",
                f"   - URL: {row.get('url', '')}",
                "",
            ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Structured classify constitutional amendment reactions with Ollama")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--markdown", default="")
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=240)
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
