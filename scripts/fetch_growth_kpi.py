#!/usr/bin/env python3
"""Fetch growth KPI sources and print a GROWTH.yaml-ready snapshot."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_json(command: list[str]) -> dict:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return json.loads(proc.stdout)


def fetch_all(ga4_days: int, gsc_days: int) -> dict:
    python = sys.executable
    ga4 = run_json([python, "scripts/fetch_ga4_metrics.py", "--days", str(ga4_days), "--json"])
    gsc = run_json([python, "scripts/fetch_gsc_metrics.py", "--days", str(gsc_days), "--json"])
    votes = run_json([python, "scripts/fetch_supabase_votes.py", "--json"])
    return {"ga4": ga4, "gsc": gsc, "votes": votes}


def count_votes(votes: dict) -> int:
    total = 0
    for topic, choices in votes.items():
        if topic.lower().startswith("test"):
            continue
        total += sum(int(value) for value in choices.values())
    return total


def build_snapshot(data: dict, date: str) -> dict:
    ga4 = data["ga4"]
    gsc_summary = data["gsc"]["summary"]
    votes_total = count_votes(data["votes"])
    sessions = float(ga4.get("sessions", 0) or 0)
    pageviews = float(ga4.get("screenPageViews", 0) or 0)
    pages_per_session = pageviews / sessions if sessions else None
    return {
        "date": date,
        "weekly_users": int(float(ga4.get("activeUsers", 0) or 0)),
        "pageviews": int(pageviews),
        "pages_per_session": pages_per_session,
        "votes_total": votes_total,
        "votes_week": None,
        "gsc_impressions": int(float(gsc_summary.get("impressions", 0) or 0)),
        "gsc_clicks": int(float(gsc_summary.get("clicks", 0) or 0)),
        "x_followers": None,
        "notes": "Auto: GA4/Supabase/GSC fetched. X followers remain manual.",
    }


def print_markdown(data: dict, snapshot: dict) -> None:
    print("| source | metric | value |")
    print("|---|---|---:|")
    print(f"| GA4 | activeUsers | {snapshot['weekly_users']} |")
    print(f"| GA4 | screenPageViews | {snapshot['pageviews']} |")
    pages = snapshot["pages_per_session"]
    print(f"| GA4 | pages_per_session | {pages:.3f} |" if pages is not None else "| GA4 | pages_per_session | null |")
    print(f"| Supabase | votes_total | {snapshot['votes_total']} |")
    print(f"| GSC | impressions | {snapshot['gsc_impressions']} |")
    print(f"| GSC | clicks | {snapshot['gsc_clicks']} |")
    print(f"| GSC | ctr | {float(data['gsc']['summary'].get('ctr', 0)):.4f} |")
    print(f"| GSC | position | {float(data['gsc']['summary'].get('position', 0)):.4f} |")


def print_growth_yaml(snapshot: dict) -> None:
    pages = snapshot["pages_per_session"]
    pages_text = f"{pages:.3f}" if pages is not None else "null"
    print("GROWTH.yaml snapshot:")
    print("```yaml")
    print(f"    - date: {snapshot['date']}")
    print(f"      weekly_users: {snapshot['weekly_users']}")
    print(f"      pageviews: {snapshot['pageviews']}")
    print(f"      pages_per_session: {pages_text}")
    print(f"      votes_total: {snapshot['votes_total']}")
    print("      votes_week: null")
    print(f"      gsc_impressions: {snapshot['gsc_impressions']}")
    print(f"      gsc_clicks: {snapshot['gsc_clicks']}")
    print("      x_followers: null")
    print(f"      notes: {snapshot['notes']}")
    print("```")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--ga4-days", type=int, default=7)
    parser.add_argument("--gsc-days", type=int, default=28)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    data = fetch_all(args.ga4_days, args.gsc_days)
    snapshot = build_snapshot(data, args.date)
    if args.json:
        print(json.dumps({"snapshot": snapshot, "sources": data}, ensure_ascii=False, indent=2))
        return 0
    print_markdown(data, snapshot)
    print()
    print_growth_yaml(snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
