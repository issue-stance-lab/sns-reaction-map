#!/usr/bin/env python3
"""課題57 段階3: 非公開正典から公開データJSON（テーマ／catalog）を生成する。

使い方:
    python3 scripts/build_public_registry.py --topic bukatsu-chiiki
    python3 scripts/build_public_registry.py --all

data/public/themes/*.json と data/public/catalog.json は生成専用。手編集しない。
同じ入力からは必ず同じバイト列を出す（生成時刻を含めない）。
"""
from __future__ import annotations

import argparse
import sys

from public_registry_common import (
    ROOT,
    PUBLIC_CATALOG_PATH,
    PUBLIC_THEMES_DIR,
    RegistryError,
    build_catalog,
    build_theme_json,
    check_catalog_invariants,
    check_theme_invariants,
    dumps_catalog_json,
    dumps_theme_json,
    load_theme_json_files,
    load_themes_yaml,
    validate_public_catalog,
    validate_public_theme,
)


def build_one(topic_id: str) -> bool:
    try:
        theme_json = build_theme_json(topic_id)
    except RegistryError as exc:
        print(f"NG {topic_id}: {exc}", file=sys.stderr)
        return False

    errors = validate_public_theme(theme_json) + check_theme_invariants(theme_json)
    if errors:
        for error in errors:
            print(f"NG {topic_id}: {error}", file=sys.stderr)
        return False

    out_path = PUBLIC_THEMES_DIR / f"{topic_id}.json"
    out_path.write_bytes(dumps_theme_json(theme_json))
    print(
        f"OK {topic_id}: collected={theme_json['collected_count']} "
        f"opinion={theme_json['opinion_count']} issues={len(theme_json['issues'])} "
        f"-> {out_path.relative_to(ROOT)}"
    )
    return True


def rebuild_catalog() -> bool:
    try:
        catalog = build_catalog()
    except RegistryError as exc:
        print(f"NG catalog: {exc}", file=sys.stderr)
        return False

    theme_jsons = load_theme_json_files()
    errors = validate_public_catalog(catalog) + check_catalog_invariants(catalog, theme_jsons)
    if errors:
        for error in errors:
            print(f"NG catalog: {error}", file=sys.stderr)
        return False

    PUBLIC_CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_CATALOG_PATH.write_bytes(dumps_catalog_json(catalog))
    print(
        f"OK catalog: theme_count={catalog['totals']['theme_count']} "
        f"opinion_count={catalog['totals']['opinion_count']} -> {PUBLIC_CATALOG_PATH.relative_to(ROOT)}"
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--topic", help="生成する1テーマのID")
    group.add_argument("--all", action="store_true", help="published: done の全テーマを生成する")
    args = parser.parse_args()

    themes_yaml = load_themes_yaml()
    if args.all:
        topic_ids = sorted(tid for tid, meta in themes_yaml.items() if meta.get("published") == "done")
    else:
        if args.topic not in themes_yaml:
            print(f"NG: THEMES.yaml に無いテーマID: {args.topic}", file=sys.stderr)
            return 1
        topic_ids = [args.topic]

    PUBLIC_THEMES_DIR.mkdir(parents=True, exist_ok=True)

    ok = True
    for topic_id in topic_ids:
        ok = build_one(topic_id) and ok
    if not ok:
        return 1

    return 0 if rebuild_catalog() else 1


if __name__ == "__main__":
    raise SystemExit(main())
