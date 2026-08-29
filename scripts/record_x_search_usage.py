#!/usr/bin/env python3
"""Record count-only X search usage for future API cost planning."""

from __future__ import annotations

import argparse
import datetime as dt
import json

from admin_dashboard.x_api_usage import append_usage, build_usage, read_usage_ledger, summarize_usage


JST = dt.timezone(dt.timedelta(hours=9))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="X検索の件数とAPI換算費用だけをローカル台帳へ記録します")
    result.add_argument("--mode", choices=("chrome", "x_api", "mixed"), default="chrome")
    result.add_argument("--queries", type=int)
    result.add_argument("--results-loaded", type=int)
    result.add_argument("--unique-posts", type=int)
    result.add_argument("--post-details", type=int)
    result.add_argument("--unique-users", type=int)
    result.add_argument("--owned-posts", type=int)
    result.add_argument("--candidates", type=int)
    result.add_argument("--incomplete", action="store_true")
    result.add_argument("--note", default="")
    result.add_argument("--source-id")
    result.add_argument("--source", choices=("codex_app", "claude_app", "dashboard", "desktop_skill"), default="desktop_skill")
    result.add_argument("--summary", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    if args.summary:
        print(json.dumps(summarize_usage(read_usage_ledger()), ensure_ascii=False, indent=2))
        return 0
    raw = {
        "mode": args.mode,
        "queries_count": args.queries,
        "search_results_loaded": args.results_loaded,
        "unique_posts_read": args.unique_posts,
        "post_detail_reads": args.post_details,
        "unique_users_read": args.unique_users,
        "owned_posts_read": args.owned_posts,
        "candidates_shortlisted": args.candidates,
        "counts_complete": not args.incomplete,
        "note": args.note,
    }
    usage = build_usage(raw, recorded_at=dt.datetime.now(JST).isoformat(timespec="seconds"))
    if usage is None:
        raise SystemExit("記録形式が不正です")
    record = append_usage(usage, source_id=args.source_id, source=args.source)
    print(json.dumps({
        "recorded": True,
        "source_id": record["source_id"],
        "unique_posts_read": record.get("unique_posts_read"),
        "estimated_cost_usd": record.get("estimated_cost_usd"),
        "counts_complete": record.get("counts_complete"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
