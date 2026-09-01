#!/usr/bin/env python3
"""一次資料照合の内部判定語が全テーマで統一されているか検査する。"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"fact", "gap", "miss"}
LEGACY_CONSTITUTIONAL = {
    "原典にある": "fact",
    "原典とずれる": "gap",
    "原典にたどり着けず": "miss",
}
SOURCES = {
    "bike-blue-ticket": ("scripts/build_bike_process_sections.py", "FACT_CHECKS"),
    "constitutional-amendment": ("scripts/build_constitutional_process_sections.py", "FACT_CHECKS"),
    "consumption-tax-cut": ("scripts/build_consumption_tax_page.py", "CLAIM_AUDIT"),
    "elderly-license-revocation": ("scripts/build_elderly_process_sections.py", "FACT_CHECKS"),
    "fukushuto": ("scripts/build_fukushuto_process_sections.py", "FACT_CHECKS"),
    "koshitsu-tenpakai": ("scripts/build_koshitsu_process_sections.py", "FACT_CHECKS"),
}


def read_literal(path: Path, variable: str):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == variable for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ValueError(f"{path}: {variable} がリテラルとして見つかりません")


def read_checks(path: Path, variable: str) -> list[dict]:
    value = read_literal(path, variable)
    if isinstance(value, list):
        return value
    raise ValueError(f"{path}: {variable} がリテラルのリストではありません")


def audit() -> tuple[dict[str, int], list[str]]:
    counts: dict[str, int] = {}
    errors: list[str] = []
    for theme, (relative, variable) in SOURCES.items():
        checks = read_checks(ROOT / relative, variable)
        counts[theme] = len(checks)
        for index, check in enumerate(checks, start=1):
            verdict = check.get("verdict")
            if verdict not in ALLOWED:
                errors.append(f"{theme} #{index}: 不正な判定語 {verdict!r}")
    constitutional_labels = read_literal(
        ROOT / "scripts/build_constitutional_process_sections.py", "VERDICT_LABEL"
    )
    if constitutional_labels != {code: label for label, code in LEGACY_CONSTITUTIONAL.items()}:
        errors.append("constitutional-amendment: 既存の日本語表示ラベルとの写像が一致しません")
    return counts, errors


def main() -> int:
    counts, errors = audit()
    total = sum(counts.values())
    for theme, count in counts.items():
        print(f"{theme}: {count}主張")
    print(f"合計: {total}主張")
    if errors:
        print("NG")
        print("\n".join(errors))
        return 1
    print("OK: 6テーマすべてが fact / gap / miss のみを使用")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
