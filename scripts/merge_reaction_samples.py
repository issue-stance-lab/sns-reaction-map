#!/usr/bin/env python3
"""Merge a dated reaction refresh into an existing sample list.

Rows are considered duplicates when they share a non-empty tweet ID, canonical
URL, or normalized full text. Existing rows always win so editorial metadata is
not replaced by a later fetch of the same post.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


HIGHLIGHT_MARKERS = ("\tSTART\t", "\tEND\t")


def load_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise ValueError(f"{path} must contain a JSON list of objects")
    return data


def canonical_url(value: Any) -> str:
    url = str(value or "").strip()
    if not url:
        return ""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def normalized_text(value: Any) -> str:
    text = str(value or "")
    for marker in HIGHLIGHT_MARKERS:
        text = text.replace(marker, " ")
    return re.sub(r"\s+", " ", text).strip()


def identity_keys(row: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    tweet_id = str(row.get("tweet_id") or "").strip()
    if tweet_id:
        keys.add(f"tweet:{tweet_id}")
    url = canonical_url(row.get("url"))
    if url:
        keys.add(f"url:{url}")
    text = normalized_text(row.get("text"))
    if text:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        keys.add(f"text:{digest}")
    return keys


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge a reaction refresh without overwriting existing rows")
    parser.add_argument("--existing", required=True)
    parser.add_argument("--refresh", required=True)
    parser.add_argument("--new-only", required=True)
    parser.add_argument("--merged", required=True)
    args = parser.parse_args()

    existing_path = Path(args.existing)
    refresh_path = Path(args.refresh)
    existing = load_rows(existing_path)
    refresh = load_rows(refresh_path)

    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for row in existing:
        keys = identity_keys(row)
        if keys and keys & seen:
            continue
        merged.append(row)
        seen.update(keys)

    new_rows: list[dict[str, Any]] = []
    duplicates = 0
    for row in refresh:
        keys = identity_keys(row)
        if keys and keys & seen:
            duplicates += 1
            continue
        new_rows.append(row)
        merged.append(row)
        seen.update(keys)

    write_rows(Path(args.new_only), new_rows)
    write_rows(Path(args.merged), merged)
    print(f"existing={len(existing)} refresh={len(refresh)} duplicates={duplicates} new={len(new_rows)} merged={len(merged)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
