#!/usr/bin/env python3
"""Fetch vote counts from Supabase.

Reads SUPABASE_URL and SUPABASE_ANON_KEY from the environment or .env, then
prints counts grouped by topic_id and choice_idx.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def supabase_get(path: str) -> list[dict]:
    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "")
    if not supabase_url or not anon_key:
        raise SystemExit("SUPABASE_URL and SUPABASE_ANON_KEY are required.")

    url = f"{supabase_url}/rest/v1/{path}"
    req = urllib.request.Request(
        url,
        headers={
            "apikey": anon_key,
            "Authorization": f"Bearer {anon_key}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def fetch_votes(topic: str | None) -> list[dict]:
    query = "select=topic_id,choice_idx,created_at&order=created_at.desc"
    if topic:
        query += "&topic_id=eq." + urllib.parse.quote(topic, safe="")
    return supabase_get("votes?" + query)


def summarize(rows: list[dict]) -> dict[str, dict[int, int]]:
    counts: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        topic_id = str(row.get("topic_id", ""))
        choice_idx = int(row.get("choice_idx", 0))
        counts[topic_id][choice_idx] += 1
    return {topic: dict(sorted(choices.items())) for topic, choices in sorted(counts.items())}


def print_markdown(summary: dict[str, dict[int, int]]) -> None:
    print("| topic_id | total | choice counts |")
    print("|---|---:|---|")
    for topic, choices in summary.items():
        total = sum(choices.values())
        choice_text = ", ".join(f"{idx}: {count}" for idx, count in choices.items())
        print(f"| {topic} | {total} | {choice_text} |")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", help="Filter by topic_id")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    args = parser.parse_args()

    load_dotenv(Path(".env"))
    rows = fetch_votes(args.topic)
    summary = summarize(rows)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print_markdown(summary)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as exc:
        sys.stderr.write(f"Supabase HTTP error {exc.code}: {exc.read().decode('utf-8')}\n")
        raise SystemExit(1)
