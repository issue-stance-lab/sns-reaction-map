#!/usr/bin/env python3
"""sample_period が収集日集計と一致することを検証・集計する。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .sync_portal_stats import ROOT, parse_themes_yaml
except ImportError:
    from sync_portal_stats import ROOT, parse_themes_yaml  # type: ignore[no-redef]

EVIDENCE = ROOT / "data" / "verification" / "sample-periods.json"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# オーナー確認済みの取得期間は、1日だけのこともあれば範囲のこともある。
# 範囲を書けないと unknown に戻すしかなく、ページに「未記録」が出続ける。
OWNER_PERIOD_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(〜\d{4}-\d{2}-\d{2})?$")


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    dates = [
        str(row.get("fetched_at") or "")[:10]
        for row in rows
        if DATE_RE.fullmatch(str(row.get("fetched_at") or "")[:10])
    ]
    return {
        "records": len(rows),
        "dated_records": len(dates),
        "missing_records": len(rows) - len(dates),
        "min": min(dates, default=None),
        "max": max(dates, default=None),
    }


def expected_period(evidence: dict[str, Any]) -> str:
    if evidence["missing_records"] or not evidence["dated_records"]:
        return "unknown"
    return evidence["min"] if evidence["min"] == evidence["max"] else f'{evidence["min"]}〜{evidence["max"]}'


def generate() -> dict[str, dict[str, Any]]:
    result = {}
    for slug, theme in parse_themes_yaml().items():
        path = ROOT / str(theme["sample_file"])
        rows = json.loads(path.read_text(encoding="utf-8"))
        result[slug] = summarize(rows)
    return result


def verify(evidence: dict[str, dict[str, Any]]) -> int:
    failures = 0
    themes = parse_themes_yaml()
    for slug, theme in themes.items():
        item = evidence.get(slug)
        if not item:
            print(f"NG  {slug}: 収集日の検証メタデータがない")
            failures += 1
            continue
        expected = expected_period(item)
        actual = str(theme.get("sample_period") or "")
        if theme.get("sample_period_source") == "owner_confirmed":
            if OWNER_PERIOD_RE.fullmatch(actual):
                print(f"OK  {slug}: {actual}（オーナー確認済み／取得日欠損{item['missing_records']}/{item['records']}件）")
                continue
            print(f"NG  {slug}: オーナー確認済みの sample_period が日付形式ではない: {actual}")
            failures += 1
            continue
        if actual == expected:
            print(f"OK  {slug}: {actual}（欠損{item['missing_records']}/{item['records']}件）")
        else:
            print(f"NG  {slug}: 台帳={actual} / 実測={expected}")
            failures += 1
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", action="store_true", help="ローカル正典から検証メタデータを更新")
    args = parser.parse_args()
    if args.generate:
        evidence = generate()
        EVIDENCE.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    return verify(evidence)


if __name__ == "__main__":
    raise SystemExit(main())
