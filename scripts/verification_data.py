#!/usr/bin/env python3
"""非公開の投稿データから、公開可能な検証用サマリを生成する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


CLASSIFICATION_FIELDS = (
    "main_issue",
    "stance",
    "is_opinion",
    "is_relevant",
    "confidence",
)


def _classification(record: dict[str, Any]) -> dict[str, Any]:
    nested = record.get("classification")
    return nested if isinstance(nested, dict) else record


def record_identity(record: dict[str, Any]) -> str:
    """tweet_id とXのURLを同じ非公開識別子へ正規化する。"""
    tweet_id = str(record.get("tweet_id") or "").strip()
    if tweet_id:
        return f"tweet:{tweet_id}"

    source = _classification(record)
    url = str(record.get("url") or source.get("url") or "").strip()
    if url:
        match = re.search(r"/(?:status|statuses)/(\d+)(?:[/?#]|$)", url)
        if match:
            return f"tweet:{match.group(1)}"
        parts = urlsplit(url)
        canonical = urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))
        return f"url:{canonical}"

    text = re.sub(r"\s+", " ", str(record.get("text") or "")).strip()
    if text:
        return "text:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
    raise ValueError("record has no tweet_id, URL, or text")


def record_id_hash(record: dict[str, Any]) -> str:
    identity = record.get("record_id_hash")
    if isinstance(identity, str) and identity.startswith("sha256:"):
        return identity
    digest = hashlib.sha256(record_identity(record).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def make_verification_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    safe = []
    for record in records:
        identity = record_identity(record)
        if "synthetic" in identity.lower() or "synthetic" in str(record.get("source") or "").lower():
            raise ValueError("synthetic records cannot be published as verification data")
        classification = _classification(record)
        safe.append(
            {
                "record_id_hash": record_id_hash(record),
                "classification": {
                    field: classification.get(field)
                    for field in CLASSIFICATION_FIELDS
                },
            }
        )
    safe.sort(key=lambda record: record["record_id_hash"])
    hashes = [record["record_id_hash"] for record in safe]
    if len(hashes) != len(set(hashes)):
        raise ValueError("verification data contains duplicate record IDs")
    return safe


def read_records(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(record, dict) for record in value):
        raise ValueError(f"JSON array of objects required: {path}")
    return value


def write_verification_file(source: Path, output: Path) -> None:
    records = make_verification_records(read_records(source))
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False, separators=(",", ":")) for record in records]
    output.write_text("[\n" + ",\n".join(lines) + "\n]\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="本文を含まない検証用分類サマリを生成する")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_verification_file(args.input, args.output)
    print(f"generated: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
