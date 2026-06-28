#!/usr/bin/env python3
"""Unified batch classifier for SNS reactions with Ollama.

Replaces the topic-specific scripts (takaichi, constitutional, henoko) with a
single script driven by YAML topic configs in configs/topics/.

Usage:
    python scripts/classify_unified.py --topic takaichi --input data/input.json --output data/output.json
    python scripts/classify_unified.py --config configs/topics/custom.yaml --input data/input.json --output data/output.json
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
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

try:
    from two_stage_classifier import detect_post_types_batch
except ImportError:
    detect_post_types_batch = None  # type: ignore[assignment,misc]


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = PROJECT_ROOT / "configs" / "topics"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
TAGS_URL = "http://127.0.0.1:11434/api/tags"


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file. Uses PyYAML if available, otherwise a minimal parser."""
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text)
    # Minimal fallback: delegate to a subprocess call to python -c with yaml
    # or raise a clear error.
    raise ImportError(
        "PyYAML is required. Install it with: pip install pyyaml"
    )


def load_topic_config(topic: str | None = None, config_path: str | None = None) -> dict[str, Any]:
    """Load a topic config from --topic name or --config path."""
    if config_path:
        p = Path(config_path)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
    elif topic:
        p = TOPICS_DIR / f"{topic}.yaml"
    else:
        raise ValueError("Either --topic or --config is required.")
    if not p.exists():
        raise FileNotFoundError(f"Topic config not found: {p}")
    return _load_yaml(p)


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def build_prompt(config: dict[str, Any], items_json: str, avoid_hold: bool = False) -> str:
    """Build the classification prompt from a topic config and serialised items."""
    categories = config["categories"]
    stances = config["stances"]
    rules = config.get("classification_rules", "").strip()
    prompt_intro = config.get("prompt_intro", "あなたはSNS投稿の論調分類器です。説明や思考は不要です。")
    prompt_theme = config.get("prompt_theme", "").strip()

    extra_output_fields = config.get("extra_output_fields", [])

    # Build the output schema example
    example_obj: dict[str, Any] = OrderedDict()
    example_obj["id"] = 1
    example_obj["category"] = "カテゴリ名"
    example_obj["stance"] = "stance候補" if "issues" in config else "立場ラベル"
    for field in extra_output_fields:
        example_obj[field["name"]] = f"{field['name']}候補"
    example_obj["summary"] = "中立的な1文要約"
    example_obj["reason"] = "分類理由を短く"
    example_obj["confidence"] = 0.0
    example_obj["article_usable"] = True
    example_obj["risk"] = "none / low / medium / high"

    parts = [f"{prompt_intro}\n以下の投稿リストを分類し、JSON配列のみを返してください。"]

    # Markdown prohibition for constitutional-style prompts
    if extra_output_fields:
        parts[-1] += " Markdownは禁止。キーと文字列は必ずダブルクォートにしてください。"

    if prompt_theme:
        parts.append("")
        parts.append(prompt_theme.strip())

    # Rules section
    if rules:
        parts.append("")
        parts.append("重要な分類ルール:" if not prompt_theme else "重要ルール:")
        parts.append(rules.strip())

    # Categories
    parts.append("")
    parts.append("カテゴリ:")
    parts.append("\n".join(f"- {c}" for c in categories))

    # Stances
    stance_label = "stance候補" if "issues" in config else "立場ラベル"
    parts.append("")
    parts.append(f"{stance_label}: {', '.join(stances)}")

    # Extra dimensions (e.g. issue for constitutional)
    for field in extra_output_fields:
        values_key = field["values_key"]
        values = config.get(values_key, [])
        parts.append(f"{field['name']}候補: {', '.join(values)}")

    # Avoid-hold extra rules
    if avoid_hold:
        ah_rules = config.get("avoid_hold_rules", "").strip()
        if ah_rules:
            parts.append("")
            parts.append("保留再分類ルール:")
            parts.append(ah_rules)

    # Items
    parts.append("")
    parts.append("投稿リスト:")
    parts.append(items_json)

    # Output format
    parts.append("")
    parts.append("出力JSON配列。各要素は必ずこの形式:")
    example_json = json.dumps([example_obj], ensure_ascii=False, indent=2)
    # Escape braces for .format() safety — not needed here since we don't use .format()
    parts.append(example_json)

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Text utilities (from the takaichi base script)
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    text = re.sub(r'\s*(?:START|END)\s*', ' ', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def structure_rt(text: str) -> dict[str, str]:
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


# ---------------------------------------------------------------------------
# Ollama communication
# ---------------------------------------------------------------------------

def check_ollama() -> list[str] | None:
    try:
        with urllib.request.urlopen(TAGS_URL, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return None


def call_ollama(model: str, prompt: str, timeout: int, config: dict[str, Any]) -> str:
    opts = config.get("ollama_options", {})
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": opts.get("temperature", 0.1),
                "num_predict": opts.get("num_predict", 2500),
            },
        }
    ).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("response", "")


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

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
    # ast.literal_eval fallback
    try:
        parsed = ast.literal_eval(candidate)
        if isinstance(parsed, list):
            return parsed
    except (SyntaxError, ValueError):
        pass
    # Repair unquoted keys
    repaired = re.sub(r"([{\[,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', candidate)
    repaired = repaired.replace(": True", ": true").replace(": False", ": false").replace(": None", ": null")
    parsed = json.loads(repaired)
    if isinstance(parsed, list):
        return parsed
    raise ValueError(f"Could not parse JSON array: {text[:300]}")


# ---------------------------------------------------------------------------
# Normalize & post-process
# ---------------------------------------------------------------------------

def normalize(result: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    categories = config["categories"]
    stances = config["stances"]
    fallback_category = "その他・分類保留"
    fallback_stance = "その他"

    category = result.get("category") if result.get("category") in categories else fallback_category
    stance = result.get("stance") if result.get("stance") in stances else fallback_stance

    try:
        confidence = float(result.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    # Confidence floor (used by constitutional)
    confidence_floor = config.get("confidence_floor")
    if confidence_floor and confidence <= 0.0 and category != fallback_category:
        confidence = confidence_floor

    risk = result.get("risk") if result.get("risk") in {"none", "low", "medium", "high"} else "medium"

    normalized: dict[str, Any] = {
        "category": category,
        "stance": stance,
        "summary": str(result.get("summary") or "").strip(),
        "reason": str(result.get("reason") or "").strip(),
        "confidence": max(0.0, min(1.0, confidence)),
        "article_usable": bool(result.get("article_usable", False)),
        "risk": risk,
    }

    # Extra output fields (e.g. issue)
    for field in config.get("extra_output_fields", []):
        name = field["name"]
        values_key = field["values_key"]
        fallback_val = field.get("fallback", "")
        valid = config.get(values_key, [])
        normalized[name] = result.get(name) if result.get(name) in valid else fallback_val

    return normalized


def apply_harmonize(result: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Apply harmonize_rules from config (e.g. fix stance when it conflicts with category)."""
    rules = config.get("harmonize_rules", [])
    fixed = dict(result)
    category = fixed.get("category")
    if rules:
        for rule in rules:
            if category in rule.get("categories", []):
                valid = set(rule.get("valid_stances", []))
                if valid and fixed.get("stance") not in valid:
                    fixed["stance"] = rule["force_stance"]
                elif not valid:
                    fixed["stance"] = rule["force_stance"]
                if "force_issue" in rule:
                    fixed["issue"] = rule["force_issue"]
                break
    if category in set(config.get("article_unusable_categories", [])):
        fixed["article_usable"] = False
    return fixed


def apply_rule_overrides(text: str, result: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Apply rule_overrides from config."""
    overrides = config.get("rule_overrides", [])
    for override in overrides:
        markers = override.get("markers", [])
        if any(marker in text for marker in markers):
            fixed = dict(result)
            if "force_category" in override:
                fixed["category"] = override["force_category"]
            if "force_stance" in override:
                fixed["stance"] = override["force_stance"]
            if "force_summary" in override:
                if not fixed.get("summary") or any(m in fixed.get("summary", "") for m in markers[:3]):
                    fixed["summary"] = override["force_summary"]
            if "force_reason" in override:
                fixed["reason"] = override["force_reason"]
            if "force_article_usable" in override:
                fixed["article_usable"] = bool(override["force_article_usable"])
            if "force_risk" in override:
                fixed["risk"] = override["force_risk"]
            for field in config.get("extra_output_fields", []):
                key = f"force_{field['name']}"
                if key in override:
                    fixed[field["name"]] = override[key]
            if "min_confidence" in override:
                fixed["confidence"] = max(float(fixed.get("confidence", 0.0)), override["min_confidence"])
            return fixed
    return result


def make_fallback(text: str, reason: str, config: dict[str, Any]) -> dict[str, Any]:
    """Create a fallback classification result."""
    risk_words = config.get("fallback_high_risk_words", [])
    risk = "high" if any(w in text for w in risk_words) else "medium"
    result: dict[str, Any] = {
        "category": "その他・分類保留",
        "stance": "その他",
        "summary": "",
        "reason": reason,
        "confidence": 0.0,
        "article_usable": False,
        "risk": risk,
    }
    for field in config.get("extra_output_fields", []):
        result[field["name"]] = field.get("fallback", "")
    return result


# ---------------------------------------------------------------------------
# Batch classification
# ---------------------------------------------------------------------------

def classify_batch(
    model: str, rows: list[dict[str, Any]], timeout: int,
    config: dict[str, Any], avoid_hold: bool = False,
    hints: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    text_max = config.get("text_max_length", 700)
    items = []
    for i, row in enumerate(rows, 1):
        cleaned = clean_text(row.get("text", ""))
        parts = structure_rt(cleaned)
        if "quoted" in parts:
            display = f"[本文] {parts['main']} / [引用] {parts['quoted']}"
        else:
            display = parts["main"]
        # Append two-stage hint before truncation
        if hints and i - 1 < len(hints) and hints[i - 1].get("hint"):
            display = f"{display}\n[分類ヒント] {hints[i - 1]['hint']}"
        items.append({"id": i, "text": display[:text_max]})

    items_json = json.dumps(items, ensure_ascii=False, indent=2)
    prompt = build_prompt(config, items_json, avoid_hold)
    response = call_ollama(model, prompt, timeout, config)

    try:
        parsed = parse_array(response)
    except Exception:
        # If batch fails and has more than 1 row, try one-by-one
        if len(rows) > 1:
            results: list[dict[str, Any]] = []
            for j, row in enumerate(rows):
                row_hint = [hints[j]] if hints and j < len(hints) else None
                results.extend(classify_batch(model, [row], timeout, config, avoid_hold, row_hint))
            return results
        raise

    by_id: dict[int, dict[str, Any]] = {}
    for item in parsed:
        try:
            normalized = normalize(item, config)
            harmonized = apply_harmonize(normalized, config)
            by_id[int(item.get("id"))] = harmonized
        except Exception:
            continue

    results = []
    for i in range(1, len(rows) + 1):
        base = by_id.get(i, make_fallback(
            clean_text(rows[i - 1].get("text", "")), "missing batch result", config
        ))
        final = apply_rule_overrides(clean_text(rows[i - 1].get("text", "")), base, config)
        results.append(final)
    return results


def classify_batch_with_retry(
    model: str, rows: list[dict[str, Any]], timeout: int,
    config: dict[str, Any], avoid_hold: bool = False,
    hints: list[dict[str, str]] | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Call classify_batch and retry once if any expected IDs are missing."""
    expected_ids = set(range(1, len(rows) + 1))
    retries = 0

    results = classify_batch(model, rows, timeout, config, avoid_hold, hints)

    present_ids = {
        i + 1
        for i, r in enumerate(results)
        if r.get("reason") != "missing batch result"
    }
    missing_ids = expected_ids - present_ids

    if missing_ids:
        retries = 1
        print(f"  ID欠落 {sorted(missing_ids)} を検出、リトライ中...", flush=True)
        results = classify_batch(model, rows, timeout, config, avoid_hold, hints)

    return results, retries


# ---------------------------------------------------------------------------
# Markdown output
# ---------------------------------------------------------------------------

def write_markdown(rows: list[dict[str, Any]], output: Path, config: dict[str, Any]) -> None:
    categories = config["categories"]
    title = config.get("markdown_title", f"{config.get('title', '')} Ollama分類")
    extra_fields = config.get("extra_output_fields", [])

    buckets: OrderedDict[str, list[dict[str, Any]]] = OrderedDict((c, []) for c in categories)
    for row in rows:
        cat = row["classification"]["category"]
        buckets.setdefault(cat, []).append(row)

    lines = [f"# {title}", "", f"総件数: {len(rows)}", "", "## 分類件数", "", "| 分類 | 件数 |", "| --- | ---: |"]
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
        for i, row in enumerate(items[:12], 1):
            c = row["classification"]
            text = clean_text(row.get("text", ""))
            lines.append(f"{i}. {c['summary'] or text[:160]}")

            # Build detail line based on whether there are extra fields
            if extra_fields:
                extra_parts = " / ".join(
                    f"{f['name']}: {c.get(f['name'], '')}" for f in extra_fields
                )
                lines.append(
                    f"   - stance: {c['stance']} / {extra_parts}"
                    f" / confidence: {c['confidence']:.2f} / risk: {c['risk']}"
                )
            else:
                lines.append(
                    f"   - 立場: {c['stance']} / 信頼度: {c['confidence']:.2f}"
                    f" / リスク: {c['risk']} / 記事向き: {c['article_usable']}"
                )
            lines.append(f"   - 理由: {c['reason']}")
            lines.append(f"   - 元投稿: {text[:260]}")
            lines.append(f"   - URL: {row.get('url', '')}")
            if not extra_fields:
                lines.append(f"   - 検索クエリ: `{row.get('query', '')}`")
            lines.append("")

    output.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Unified batch classifier for SNS reactions with Ollama"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--topic", help="Topic slug (looks up configs/topics/{topic}.yaml)")
    group.add_argument("--config", help="Path to a topic YAML config file")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--markdown", default="")
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--batch-size", type=int, default=3)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument(
        "--avoid-hold", action="store_true",
        help="Treat hold/other as a last resort for reclassification",
    )
    parser.add_argument(
        "--two-stage", action="store_true",
        help="Run two-stage classification: detect post type first, then append hints",
    )
    args = parser.parse_args()

    # Load topic config
    config = load_topic_config(topic=args.topic, config_path=args.config)
    topic_name = config.get("name", args.topic or "unknown")
    print(f"トピック: {config.get('title', topic_name)}", flush=True)

    # Resolve paths
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = PROJECT_ROOT / input_path
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    markdown_path = None
    if args.markdown:
        markdown_path = Path(args.markdown)
        if not markdown_path.is_absolute():
            markdown_path = PROJECT_ROOT / markdown_path

    # Load input
    rows = json.loads(input_path.read_text(encoding="utf-8"))
    if args.limit:
        rows = rows[: args.limit]
    for row in rows:
        row["text"] = clean_text(row.get("text", ""))
    print(f"入力: {input_path} ({len(rows)}件)", flush=True)

    # Two-stage classification
    two_stage_hints: list[dict[str, str]] = []
    if args.two_stage:
        if detect_post_types_batch is None:
            print(
                "ERROR: --two-stage requires two_stage_classifier module. "
                "scripts/two_stage_classifier.py が見つかりません。",
                flush=True,
            )
            return 1
        print("2段階分類: ステージ1 実行中...", flush=True)
        texts = [row.get("text", "") for row in rows]
        two_stage_hints = detect_post_types_batch(
            texts, model=args.model, batch_size=5, timeout=args.timeout,
        )
        # Print summary
        from collections import Counter
        type_counts = Counter(h["type"] for h in two_stage_hints)
        summary_parts = ", ".join(f"{t}={c}" for t, c in sorted(type_counts.items()))
        print(f"2段階分類: {summary_parts}", flush=True)

    # Check Ollama
    if check_ollama() is None:
        print("Ollamaに接続できません。ollama serve を確認してください。", flush=True)
        return 1

    # Classify
    classified: list[dict[str, Any]] = []
    errors = 0
    total_retries = 0
    for start in range(0, len(rows), args.batch_size):
        batch = rows[start : start + args.batch_size]
        print(f"[{start + 1}-{start + len(batch)}/{len(rows)}] batch classify", flush=True)
        batch_hints = two_stage_hints[start : start + len(batch)] if two_stage_hints else None
        try:
            results, retries = classify_batch_with_retry(
                args.model, batch, args.timeout, config, args.avoid_hold, batch_hints
            )
            total_retries += retries
        except Exception as exc:
            errors += len(batch)
            print(f"  ERROR: {exc}", flush=True)
            results = [
                make_fallback(clean_text(row.get("text", "")), f"classification_error: {exc}", config)
                for row in batch
            ]
        for row, classification in zip(batch, results):
            new_row = dict(row)
            new_row["classification"] = classification
            classified.append(new_row)
        if args.sleep:
            time.sleep(args.sleep)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(classified, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JSON保存: {output_path}", flush=True)
    if markdown_path:
        write_markdown(classified, markdown_path, config)
        print(f"Markdown保存: {markdown_path}", flush=True)
    if total_retries:
        print(f"リトライ発生: {total_retries}回", flush=True)
    print(f"完了: {len(classified)}件 / エラー {errors}件", flush=True)
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
