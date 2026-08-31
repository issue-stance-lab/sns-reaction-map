#!/usr/bin/env python3
"""課題57 段階3: 公開データJSONを検査する。

--public-only    : Schemaと公開データ内の整合だけを検査する（非公開正典は不要）
--against-private: 非公開正典から作り直し、コミット済み公開JSONと完全一致するか確認する

終了コード: 0=一致・検査成功 / 1=不一致・検査失敗 / 2=非公開正典なし
"""
from __future__ import annotations

import argparse
import json
import sys

from public_registry_common import (
    PUBLIC_CATALOG_PATH,
    PUBLIC_THEMES_DIR,
    ROOT,
    RegistryError,
    build_theme_json,
    check_catalog_invariants,
    check_theme_invariants,
    dumps_theme_json,
    load_theme_json_files,
    load_themes_yaml,
    validate_public_catalog,
    validate_public_theme,
)


def verify_public_only() -> int:
    if not PUBLIC_THEMES_DIR.exists() or not any(PUBLIC_THEMES_DIR.glob("*.json")):
        print("NG: data/public/themes/ に公開JSONがありません", file=sys.stderr)
        return 1

    theme_jsons = load_theme_json_files()
    ok = True
    for topic_id, data in sorted(theme_jsons.items()):
        errors = validate_public_theme(data) + check_theme_invariants(data)
        for error in errors:
            print(f"NG {topic_id}: {error}", file=sys.stderr)
            ok = False

    if not PUBLIC_CATALOG_PATH.exists():
        print("NG: data/public/catalog.json がありません", file=sys.stderr)
        return 1
    catalog = json.loads(PUBLIC_CATALOG_PATH.read_text(encoding="utf-8"))
    errors = validate_public_catalog(catalog) + check_catalog_invariants(catalog, theme_jsons)
    for error in errors:
        print(f"NG catalog: {error}", file=sys.stderr)
        ok = False

    if ok:
        print(f"OK public-only: {len(theme_jsons)}テーマ、catalog整合")
    return 0 if ok else 1


def verify_against_private() -> int:
    theme_jsons = load_theme_json_files()
    if not theme_jsons:
        print("NG: data/public/themes/ に公開JSONがありません", file=sys.stderr)
        return 1

    themes_yaml = load_themes_yaml()
    missing_private: list[str] = []
    mismatches: list[str] = []

    for topic_id, committed in sorted(theme_jsons.items()):
        sample_file = ROOT / themes_yaml.get(topic_id, {}).get("sample_file", "")
        if not sample_file.exists():
            missing_private.append(topic_id)
            continue
        try:
            rebuilt = build_theme_json(topic_id)
        except RegistryError as exc:
            print(f"NG {topic_id}: 非公開正典からの再生成に失敗: {exc}", file=sys.stderr)
            mismatches.append(topic_id)
            continue
        if dumps_theme_json(rebuilt) != dumps_theme_json(committed):
            print(f"NG {topic_id}: 非公開正典からの再生成とコミット済みJSONが一致しません", file=sys.stderr)
            mismatches.append(topic_id)

    if missing_private:
        print(f"非公開正典が無いテーマ（完全監査できません）: {missing_private}", file=sys.stderr)
        return 2
    if mismatches:
        return 1

    print(f"OK against-private: {len(theme_jsons)}テーマが非公開正典と完全一致")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--public-only", action="store_true")
    group.add_argument("--against-private", action="store_true")
    args = parser.parse_args()

    if args.public_only:
        return verify_public_only()
    return verify_against_private()


if __name__ == "__main__":
    raise SystemExit(main())
