#!/usr/bin/env python3
"""Fetch vote counts from Supabase.

Reads SUPABASE_URL and SUPABASE_ANON_KEY from the environment or .env, then
prints counts grouped by topic_id and choice_idx.

The votes table itself is not readable with the anon key: the 2026-07-31
security migration (supabase/migrations/202607310001_secure_votes.sql) revoked
every direct grant on public.votes and moved reads behind
public.get_vote_counts(), which only service_role may execute. Reads therefore
go through the same public entry point the site uses — a GET to the cast-vote
Edge Function — instead of PostgREST. This script must stay free of the
service_role key so it can run wherever the site runs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGE_FUNCTION = "cast-vote"
# 投票を受け付けるトピックの正典。Edge Function 側の TOPIC_CHOICES と二重管理しない
TOPIC_SOURCE = ROOT / "supabase" / "functions" / EDGE_FUNCTION / "index.ts"


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


def known_topics() -> list[str]:
    """Edge Function の TOPIC_CHOICES から topic_id を読む。

    ここに無い topic_id は Edge Function が invalid_topic で弾くため、
    問い合わせる意味がない。
    """
    if not TOPIC_SOURCE.exists():
        raise SystemExit(f"topic の正典が見つからない: {TOPIC_SOURCE}")
    body = TOPIC_SOURCE.read_text(encoding="utf-8")
    block = re.search(r"const TOPIC_CHOICES[^{]*\{(.*?)\n\};", body, re.S)
    if not block:
        raise SystemExit(f"TOPIC_CHOICES を {TOPIC_SOURCE} から読み取れない")
    return re.findall(r'"([^"]+)"\s*:\s*\d+', block.group(1))


def fetch_counts(topic_id: str) -> dict[int, int]:
    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "")
    if not supabase_url or not anon_key:
        raise SystemExit("SUPABASE_URL and SUPABASE_ANON_KEY are required.")

    query = urllib.parse.urlencode({"topic_id": topic_id})
    request = urllib.request.Request(
        f"{supabase_url}/functions/v1/{EDGE_FUNCTION}?{query}",
        headers={
            "apikey": anon_key,
            "Authorization": f"Bearer {anon_key}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return {int(choice): int(count) for choice, count in (payload.get("counts") or {}).items()}


def fetch_votes(topic: str | None) -> dict[str, dict[int, int]]:
    topics = [topic] if topic else known_topics()
    summary: dict[str, dict[int, int]] = {}
    for topic_id in topics:
        counts = fetch_counts(topic_id)
        if counts:
            summary[topic_id] = dict(sorted(counts.items()))
    return dict(sorted(summary.items()))


def print_markdown(summary: dict[str, dict[int, int]]) -> None:
    print("| topic_id | total | choice counts |")
    print("|---|---:|---|")
    for topic, choices in summary.items():
        total = sum(choices.values())
        choice_text = ", ".join(f"{idx}: {count}" for idx, count in choices.items())
        print(f"| {topic} | {total} | {choice_text} |")
    print(f"| **合計** | **{sum(sum(c.values()) for c in summary.values())}** | |")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", help="Filter by topic_id")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    summary = fetch_votes(args.topic)
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
