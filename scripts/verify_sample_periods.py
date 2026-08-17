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


def stale_owner_period(actual: str, theme: dict[str, Any]) -> str:
    """オーナー確認済みの取得期間が、最後の公開更新より古いままでないかを見る。

    `owner_confirmed` のテーマは `--promote` で `sample_period` が自動更新されない。
    そのため台帳を直し忘れると、ページの取得期間が半月前のまま公開される
    （2026-08-17 の自転車青切符で実際に起きた。STEP1も調査条件ブロックもこの値から
    作るので、2か所が揃って古くなり、食い違いの検査では気づけない）。

    範囲で書かれているときだけ、終わりの日が `updated_at`（その回の収集日）と
    一致することを求める。開始日だけの表記は範囲を持たないので対象外。
    戻り値は理由の文字列。問題なければ空文字。
    """
    if "〜" not in actual:
        return ""
    updated_at = str(theme.get("updated_at") or "")
    if not DATE_RE.fullmatch(updated_at):
        return ""
    end = actual.split("〜", 1)[1]
    if end == updated_at:
        return ""
    return (
        f"取得期間の終わりが最終更新日と違う: 台帳={actual} / updated_at={updated_at}。"
        "収集した回まで期間を伸ばして sample_period を直してください"
        "（このテーマは sample_period_source: owner_confirmed のため自動では伸びません）"
    )


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
            if not OWNER_PERIOD_RE.fullmatch(actual):
                print(f"NG  {slug}: オーナー確認済みの sample_period が日付形式ではない: {actual}")
                failures += 1
                continue
            stale = stale_owner_period(actual, theme)
            if stale:
                print(f"NG  {slug}: {stale}")
                failures += 1
                continue
            print(f"OK  {slug}: {actual}（オーナー確認済み／取得日欠損{item['missing_records']}/{item['records']}件）")
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
