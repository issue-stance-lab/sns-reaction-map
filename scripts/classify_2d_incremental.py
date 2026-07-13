#!/usr/bin/env python3
"""Classify newly collected raw samples with an existing theme 2D classifier.

This wraps the theme-specific OpenCode Go classifiers so refresh batches can be
processed without overwriting the canonical 2D file.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]


THEMES: dict[str, dict[str, Any]] = {
    "ai-copyright": {
        "script": "scripts/classify_2d_opencodego.py",
        "axes": ("stance_regulation", "stance_beneficiary"),
    },
    "bukatsu-chiiki": {
        "script": "scripts/classify_2d_bukatsu_chiiki.py",
        "axes": ("stance_transfer", "stance_priority"),
    },
    "constitutional-amendment": {
        "script": "scripts/classify_2d_constitutional.py",
        "axes": ("stance_amendment", "stance_priority"),
    },
    "elderly-license-revocation": {
        "script": "scripts/classify_2d_elderly_license.py",
        "axes": ("stance_restriction", "stance_priority"),
    },
    "school-nickname-ban": {
        "script": "scripts/classify_2d_nickname_ban.py",
        "axes": ("stance_ban", "stance_culture"),
    },
    "henoko-student-accident": {
        "script": "scripts/classify_2d_henoko.py",
        "axes": ("stance_mext", "stance_focus"),
    },
    "takaichi": {
        "script": "scripts/classify_2d_takaichi.py",
        "axes": ("stance_accountability", "stance_focus"),
    },
}


def load_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise ValueError(f"{path} must be a JSON list of objects")
    return data


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_classifier(script_path: Path):
    spec = importlib.util.spec_from_file_location(f"_classifier_{script_path.stem}", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if not getattr(module, "API_KEY", ""):
        raise RuntimeError("OPENCODEGO_API_KEY is not configured")
    if not hasattr(module, "classify_one"):
        raise RuntimeError(f"{script_path} has no classify_one()")
    return module


def clamp_score(value: Any) -> float:
    try:
        score = round(float(value) * 2) / 2
    except (TypeError, ValueError):
        return 0.0
    return max(-2.0, min(2.0, score))


def confidence(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, score))


def clean_text(value: Any) -> str:
    text = str(value or "")
    text = text.replace("\tSTART\t", " ").replace("\tEND\t", " ")
    return re.sub(r"\s+", " ", text).strip()


def normalize_summary(value: Any) -> str:
    text = clean_text(value)
    replacements = {
        "唤起": "喚起",
        "活动": "活動",
        "强": "強",
        "优": "優",
        "罚": "罰",
        "问题": "問題",
        "信息": "情報",
        "相关": "関連",
        "停车": "駐停車",
        "征收": "徴収",
        "回收": "回収",
        "开始": "開始",
        "取缔": "取締り",
        "培训": "講習",
        "移动": "移動",
        "儿童": "子ども",
        "observe": "観察",
        "Bicycle": "自転車",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text[:80]


def row_key(row: dict[str, Any]) -> str:
    return str(row.get("tweet_id") or row.get("url") or clean_text(row.get("text"))).strip()


def classify_with_retries(classifier: Any, text: str, retries: int, sleep: float) -> dict[str, Any] | None:
    for attempt in range(retries + 1):
        result = classifier.classify_one(text)
        if result is not None:
            return result
        if attempt < retries and sleep:
            time.sleep(sleep)
    return None


def parse_json_object(content: str) -> dict[str, Any] | None:
    start = content.find("{")
    end = content.rfind("}") + 1
    if start == -1 or end == 0:
        return None
    raw = content[start:end]
    candidates = [
        raw,
        re.sub(r'(:\s*)\+(-?\d+(?:\.\d+)?)', r"\1\2", raw),
    ]
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def classify_with_api(classifier: Any, text: str) -> dict[str, Any] | None:
    prompt = classifier.USER_PROMPT_TEMPLATE.format(text=text[:400])
    try:
        resp = requests.post(
            classifier.BASE_URL,
            headers={
                "Authorization": f"Bearer {classifier.API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": classifier.MODEL,
                "messages": [
                    {"role": "system", "content": classifier.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 2000,
                "temperature": 0.0,
            },
            timeout=45,
        )
        resp.raise_for_status()
        data = resp.json()
        message = data["choices"][0]["message"]
        content = str(message.get("content", "") or message.get("reasoning_content", "")).strip()
        parsed = parse_json_object(content)
        if parsed is None:
            print(f"    ERROR: JSON repair failed. content={content[:120]!r}", flush=True)
        return parsed
    except Exception as exc:
        print(f"    ERROR: {type(exc).__name__}: {exc}", flush=True)
        return None


def classify_with_api_retries(classifier: Any, text: str, retries: int, sleep: float) -> dict[str, Any] | None:
    for attempt in range(retries + 1):
        result = classify_with_api(classifier, text)
        if result is not None:
            return result
        if attempt < retries and sleep:
            time.sleep(sleep)
    return None


def classify_row(
    classifier: Any,
    row: dict[str, Any],
    x_axis: str,
    y_axis: str,
    retries: int,
    sleep: float,
) -> tuple[bool, dict[str, Any], bool]:
    text = clean_text(row.get("text"))
    if not text:
        return False, {**row, "is_opinion": False, "summary": "本文なし"}, False
    if all(hasattr(classifier, name) for name in ("USER_PROMPT_TEMPLATE", "BASE_URL", "API_KEY", "MODEL", "SYSTEM_PROMPT")):
        result = classify_with_api_retries(classifier, text, retries, sleep)
    else:
        result = classify_with_retries(classifier, text, retries, sleep)
    if result is None:
        return False, {**row, "is_opinion": False, "summary": "APIエラー"}, True
    if not result.get("is_opinion", True):
        return False, {**row, **result, "summary": normalize_summary(result.get("summary"))}, False
    normalized = {
        **row,
        **result,
        "text": text[:400],
        x_axis: clamp_score(result.get(x_axis)),
        y_axis: clamp_score(result.get(y_axis)),
        "emotional_intensity": clamp_score(result.get("emotional_intensity")),
        "confidence": confidence(result.get("confidence")),
        "summary": normalize_summary(result.get("summary")),
    }
    return True, normalized, False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", required=True, choices=sorted(THEMES))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    config = THEMES[args.theme]
    x_axis, y_axis = config["axes"]
    classifier = load_classifier(PROJECT_ROOT / config["script"])
    rows = load_rows(args.input)
    if args.limit:
        rows = rows[: args.limit]

    results: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    rejected_path = args.output.with_name(f"{args.output.stem}_rejected{args.output.suffix}")
    done: set[str] = set()
    if args.resume:
        if args.output.exists():
            results = load_rows(args.output)
            done.update(row_key(row) for row in results)
        if rejected_path.exists():
            rejected = load_rows(rejected_path)
            done.update(row_key(row) for row in rejected)

    errors = 0
    total = len(rows)
    pending = [(index, row) for index, row in enumerate(rows, 1) if not (row_key(row) and row_key(row) in done)]
    print(f"Classifying {total} {args.theme} posts via OpenCode Go... pending={len(pending)}", flush=True)

    completed = 0
    if args.workers <= 1:
        for index, row in pending:
            is_valid, classified, is_error = classify_row(classifier, row, x_axis, y_axis, args.retries, args.sleep)
            errors += int(is_error)
            if is_valid:
                results.append(classified)
            else:
                rejected.append(classified)
            completed += 1
            write_rows(args.output, results)
            write_rows(rejected_path, rejected)
            if completed % 10 == 0:
                print(f"  {completed}/{len(pending)} done (valid={len(results)} rejected={len(rejected)} errors={errors})", flush=True)
            if args.sleep:
                time.sleep(args.sleep)
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(classify_row, classifier, row, x_axis, y_axis, args.retries, args.sleep): index
                for index, row in pending
            }
            for future in as_completed(futures):
                is_valid, classified, is_error = future.result()
                errors += int(is_error)
                if is_valid:
                    results.append(classified)
                else:
                    rejected.append(classified)
                completed += 1
                write_rows(args.output, results)
                write_rows(rejected_path, rejected)
                if completed % 10 == 0:
                    print(f"  {completed}/{len(pending)} done (valid={len(results)} rejected={len(rejected)} errors={errors})", flush=True)

    print(f"Done. valid={len(results)} rejected={len(rejected)} errors={errors}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
