#!/usr/bin/env python3
"""Run a non-canonical Jev quality observation for one collected wave.

The input is normally ``.staging/refresh/<topic>/<run-id>/new-only.json``.
Only structured answers and hashed record identities are written; the raw post
text is not copied into the Jev report.  A missing key is a recorded skip, not
an error that should stop the collection pipeline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import runpy
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml


ROOT = Path(__file__).resolve().parents[1]
API_URL = "https://api.typesafe.ai/v1/systemone"
INPUT_PRICE_USD_PER_MILLION = 0.042


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and value:
            os.environ.setdefault(key, value)


def record_key(row: dict[str, Any]) -> str:
    for field in ("tweet_id", "url"):
        value = str(row.get(field) or "").strip()
        if value:
            return f"{field}_sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()
    text = " ".join(str(row.get("text") or "").split())
    return "text_sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_taxonomy(topic: str) -> tuple[dict[str, str], dict[str, str]]:
    config = yaml.safe_load((ROOT / "configs" / "refresh-pipeline.yaml").read_text(encoding="utf-8"))
    classifier_name = config["topics"][topic]["classifier"]
    classifier = ROOT / classifier_name
    module_dir = str(classifier.parent)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)
        remove_path = True
    else:
        remove_path = False
    try:
        values = runpy.run_path(str(classifier), run_name=f"jev_shadow_{classifier.stem}")
    finally:
        if remove_path:
            sys.path.remove(module_dir)

    issues = values.get("ISSUES")
    stances = values.get("STANCES")
    if not isinstance(issues, (set, list, tuple)) or not isinstance(stances, (set, list, tuple)):
        raise ValueError(f"taxonomy is not exposed by classifier: {classifier_name}")

    issue_criteria: dict[str, str] = {}
    issue_defs = values.get("ISSUE_DEFS")
    if isinstance(issue_defs, (list, tuple)):
        for item in issue_defs:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                issue_criteria[str(item[0])] = str(item[1])
            elif isinstance(item, dict):
                name = item.get("name") or item.get("label")
                if name:
                    issue_criteria[str(name)] = str(item.get("description") or "")
    for label in issues:
        issue_criteria.setdefault(str(label), "このテーマで投稿が主に扱う論点")

    stance_criteria = {str(label): f"このテーマにおける「{label}」の立場" for label in stances}
    return dict(sorted(issue_criteria.items())), dict(sorted(stance_criteria.items()))


def build_questions(issue_criteria: dict[str, str], stance_criteria: dict[str, str]) -> dict[str, dict[str, Any]]:
    return {
        "main_issue": {
            "type": "choice",
            "instructions": (
                "投稿者本人の主張を基準に、中心的な論点を1つ選ぶ。ニュース共有・告知・"
                "論点不明・無関係は、用意された『その他』に相当する選択肢を選ぶ。"
            ),
            "criteria": issue_criteria,
        },
        "stance": {
            "type": "choice",
            "instructions": (
                "投稿者本人の評価・要求・賛否を読む。引用先やニュースの立場を投稿者本人の"
                "立場と取り違えず、明確な立場がなければ中立・情報に相当する選択肢を選ぶ。"
            ),
            "criteria": stance_criteria,
        },
        "is_opinion": {
            "type": "noul",
            "instructions": "投稿者本人の評価・提案・懸念・体験が読み取れる投稿である。",
            "criteria": {
                "true": "投稿者本人の意見、評価、要求、懸念、体験がある。",
                "false": "ニュース共有、公式告知、他人の意見の紹介、事実の転載だけである。",
            },
        },
        "review_required": {
            "type": "noul",
            "instructions": "既存の本番分類へ採用する前に、人が本文を確認すべき投稿である。",
            "criteria": {
                "true": "引用・皮肉・複数論点・公式情報・立場不明など、誤判定の恐れがあり本文確認が必要。",
                "false": "論点と投稿者本人の立場が本文から明確で、追加確認の必要が低い。",
            },
        },
    }


def call_jev(api_key: str, model: str, questions: dict[str, dict[str, Any]], text: str, timeout: float) -> dict[str, Any]:
    body = {"model": model, "state": {"text": text[:1200]}, "questions": questions}
    request = Request(
        API_URL,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"network error: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError("timeout") from exc
    payload["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
    return payload


def write_verification_summary(path: Path, report: dict[str, Any]) -> None:
    summary = {
        key: report.get(key)
        for key in (
            "schema_version",
            "status",
            "topic",
            "date",
            "model_requested",
            "models_returned",
            "requested",
            "completed",
            "errors",
            "usage",
            "estimated_input_cost_usd",
            "question_schema_sha256",
            "input_sha256",
        )
    }
    write_json(path, summary)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verification-output", type=Path)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--model", default="jev-latest")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    if args.env_file:
        load_dotenv(args.env_file)
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    rows = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"JSON array of objects required: {args.input}")

    base_report: dict[str, Any] = {
        "schema_version": 1,
        "topic": args.topic,
        "date": args.date,
        "model_requested": args.model,
        "input_sha256": sha256_file(args.input),
        "requested": len(rows),
        "completed": 0,
        "errors": 0,
        "models_returned": [],
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "estimated_input_cost_usd": 0.0,
        "results": [],
    }

    if not rows:
        base_report["status"] = "skipped_no_new_records"
        write_json(args.output, base_report)
        if args.verification_output:
            write_verification_summary(args.verification_output, base_report)
        return 0
    if not api_key:
        base_report["status"] = "skipped_no_key"
        write_json(args.output, base_report)
        if args.verification_output:
            write_verification_summary(args.verification_output, base_report)
        print("Jev shadow skipped: TYPESAFE_API_KEY is not available")
        return 0

    issue_criteria, stance_criteria = load_taxonomy(args.topic)
    questions = build_questions(issue_criteria, stance_criteria)
    schema_bytes = json.dumps(questions, ensure_ascii=False, sort_keys=True).encode("utf-8")
    base_report["question_schema_sha256"] = hashlib.sha256(schema_bytes).hexdigest()

    def evaluate(index: int, row: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        text = str(row.get("text") or "").strip()
        if not text:
            return index, {"record_key": record_key(row), "error": "empty text"}
        try:
            response = call_jev(api_key, args.model, questions, text, args.timeout)
        except RuntimeError as exc:
            return index, {"record_key": record_key(row), "error": str(exc)}
        usage = response.get("usage") or {}
        return index, {
            "record_key": record_key(row),
            "model": response.get("model"),
            "answers": response.get("answers"),
            "usage": {
                "input_tokens": int(usage.get("input_tokens") or 0),
                "output_tokens": int(usage.get("output_tokens") or 0),
            },
            "latency_ms": response.get("latency_ms"),
        }

    results: list[dict[str, Any] | None] = [None] * len(rows)
    worker_count = max(1, min(args.workers, len(rows)))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(evaluate, index, row) for index, row in enumerate(rows)]
        for future in as_completed(futures):
            index, result = future.result()
            results[index] = result

    final_results = [result for result in results if result is not None]
    for result in final_results:
        usage = result.get("usage") or {}
        base_report["usage"]["input_tokens"] += int(usage.get("input_tokens") or 0)
        base_report["usage"]["output_tokens"] += int(usage.get("output_tokens") or 0)
    base_report["completed"] = sum("answers" in result for result in final_results)
    base_report["errors"] = len(final_results) - base_report["completed"]
    base_report["models_returned"] = sorted({str(result["model"]) for result in final_results if result.get("model")})
    base_report["estimated_input_cost_usd"] = round(
        base_report["usage"]["input_tokens"] / 1_000_000 * INPUT_PRICE_USD_PER_MILLION,
        6,
    )
    base_report["input_price_usd_per_million"] = INPUT_PRICE_USD_PER_MILLION
    base_report["status"] = "completed" if not base_report["errors"] else "partial"
    base_report["results"] = final_results
    write_json(args.output, base_report)
    if args.verification_output:
        write_verification_summary(args.verification_output, base_report)
    print(
        f"Jev shadow: {base_report['completed']}/{base_report['requested']} completed; "
        f"errors={base_report['errors']}"
    )
    return 0 if not base_report["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
