#!/usr/bin/env python3
"""公開文章だけを抽出し、よみやすと保護トークンの検査を実行する。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "yomiyasu.json"
LINTER = ROOT / ".claude" / "skills" / "yomiyasu" / "upstream" / "scripts" / "yomiyasu_lint.py"
URL_RE = re.compile(r"https?://[^\s)>]+")
NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_])[0-9０-９]+(?:[,，.．][0-9０-９]+)*(?:兆円|億円|万円|[%％]|件|円|年|月|日)?")
NOTE_SEPARATOR_RE = re.compile(r"(?m)^---\s*$")


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def load_linter():
    if not LINTER.is_file():
        raise SystemExit(f"よみやす本体がありません: {LINTER}")
    spec = importlib.util.spec_from_file_location("project_yomiyasu_lint", LINTER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"よみやす本体を読み込めません: {LINTER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def infer_medium(path: Path) -> str:
    if path.suffix.lower() in {".html", ".htm"}:
        return "website"
    label = str(path).lower()
    if "/note/" in label or path.name.endswith(("-FINAL.md", "-CANDIDATE.md")):
        return "note"
    if "/x/" in label:
        return "x"
    return "seo"


def note_body(text: str) -> str:
    matches = list(NOTE_SEPARATOR_RE.finditer(text))
    if not matches:
        return text
    if text.lstrip().startswith("---") and len(matches) >= 2:
        return text[matches[1].end():].lstrip()
    return text[matches[0].end():].lstrip()


def website_body(path: Path) -> str:
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from verify_page_originality import load_config as load_originality
        from verify_page_originality import visible_parts
    finally:
        sys.path.pop(0)
    shared = load_originality().get("shared_selectors", [])
    headings, _leads, paragraphs = visible_parts(path, shared)
    lines = [*(f"## {heading}" for heading in headings), *paragraphs]
    return "\n\n".join(lines)


def public_text(path: Path, medium: str) -> str:
    if medium == "website":
        return website_body(path)
    text = path.read_text(encoding="utf-8")
    if medium == "note":
        return note_body(text)
    return text


def protected_tokens(text: str) -> dict[str, Counter[str]]:
    return {
        "urls": Counter(URL_RE.findall(text)),
        "numbers": Counter(NUMBER_RE.findall(text)),
    }


def compare_protected(before: str, after: str, enabled: list[str]) -> list[str]:
    old = protected_tokens(before)
    new = protected_tokens(after)
    failures = []
    for kind in enabled:
        if old[kind] == new[kind]:
            continue
        removed = list((old[kind] - new[kind]).elements())
        added = list((new[kind] - old[kind]).elements())
        failures.append(f"{kind}: 消えた値={removed or 'なし'} / 増えた値={added or 'なし'}")
    return failures


def review(path: Path, medium: str, original: Path | None = None) -> dict[str, Any]:
    config = load_config()
    text = public_text(path, medium)
    lint = load_linter().lint_text(text)
    protected_failures: list[str] = []
    if original is not None:
        before = public_text(original, medium)
        protected_failures = compare_protected(
            before, text, list(config.get("protected_tokens") or [])
        )
    strict = set(config.get("strict_severities") or ["warn", "error"])
    blocking = [finding for finding in lint["findings"] if finding["severity"] in strict]
    return {
        "file": str(path),
        "medium": medium,
        "score": lint["score"],
        "findings": lint["findings"],
        "blocking_count": len(blocking),
        "protected_failures": protected_failures,
        "passed": not blocking and not protected_failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--medium", choices=("auto", "note", "website", "seo", "x"), default="auto")
    parser.add_argument("--original", type=Path)
    parser.add_argument("--strict", action="store_true", help="warn/errorまたは保護値の変化で終了コード1")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not args.file.is_file():
        parser.error(f"対象ファイルがありません: {args.file}")
    if args.original is not None and not args.original.is_file():
        parser.error(f"変更前ファイルがありません: {args.original}")

    medium = infer_medium(args.file) if args.medium == "auto" else args.medium
    result = review(args.file, medium, args.original)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"よみやす検査: {result['file']} ({result['medium']})")
        print(f"スコア: {result['score']}/100 / 完成を止める指摘: {result['blocking_count']}件")
        for finding in result["findings"]:
            print(f"L{finding['line']} [{finding['severity']}] {finding['message']}")
        for failure in result["protected_failures"]:
            print(f"[protected] {failure}")
        print("判定: " + ("PASS" if result["passed"] else "要修正"))
    return 1 if args.strict and not result["passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
