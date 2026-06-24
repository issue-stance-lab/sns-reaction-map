#!/usr/bin/env python3
"""Fetch Yahoo realtime search samples for arbitrary queries."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def clean_url(url: str) -> str:
    return url.split("?", 1)[0] if url and "?" in url else url


def extract_entries(html: str) -> tuple[int, list[dict]]:
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    if not match:
        return 0, []
    data = json.loads(match.group(1))
    timeline = (
        data.get("props", {})
        .get("pageProps", {})
        .get("pageData", {})
        .get("timeline", {})
    )
    total = int(timeline.get("head", {}).get("totalResultsAvailable", 0) or 0)
    return total, list(timeline.get("entry", []) or [])


def fetch_query(page, query: str, wait_ms: int) -> tuple[int, list[dict]]:
    url = f"https://search.yahoo.co.jp/realtime/search?p={quote(query)}"
    print(f"fetch: {query} -> {url}", flush=True)
    page.goto(url, timeout=60000, wait_until="networkidle")
    page.wait_for_timeout(wait_ms)
    total, entries = extract_entries(page.content())
    rows = []
    fetched_at = datetime.now(timezone.utc).isoformat()
    for entry in entries:
        text = entry.get("displayTextBody") or ""
        if not text:
            continue
        tweet_id = entry.get("tweetId") or entry.get("id") or ""
        url = clean_url(entry.get("url") or "")
        user_id = entry.get("thid") or entry.get("userId") or ""
        rows.append(
            {
                "query": query,
                "fetched_at": fetched_at,
                "text": text,
                "tweet_id": tweet_id,
                "url": url or (f"https://x.com/i/status/{tweet_id}" if tweet_id else ""),
                "user_id": user_id,
                "source": "yahoo_realtime",
            }
        )
    print(f"  total_available={total} returned={len(rows)}", flush=True)
    return total, rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Yahoo realtime search samples")
    parser.add_argument("--query", action="append", required=True, help="Search query. Repeatable.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--markdown", default="")
    parser.add_argument("--wait-ms", type=int, default=6000)
    parser.add_argument("--dedupe", action="store_true")
    args = parser.parse_args()

    all_rows = []
    totals = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
        )
        page = context.new_page()
        for query in args.query:
            total, rows = fetch_query(page, query, args.wait_ms)
            totals[query] = total
            all_rows.extend(rows)
        browser.close()

    if args.dedupe:
        seen = set()
        deduped = []
        for row in all_rows:
            key = row.get("tweet_id") or row.get("url") or row.get("text")
            if key in seen:
                continue
            seen.add(key)
            deduped.append(row)
        all_rows = deduped

    output = resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(all_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.markdown:
        md = resolve(args.markdown)
        lines = ["# Yahooリアルタイム検索 取得サンプル", "", f"取得件数: {len(all_rows)}", ""]
        lines += ["## 検索語別表示件数", ""]
        for query, total in totals.items():
            lines.append(f"- `{query}`: Yahoo表示 {total}件")
        lines += ["", "## サンプル", ""]
        for i, row in enumerate(all_rows, 1):
            lines += [
                f"### {i}. `{row['query']}`",
                "",
                row["text"].replace("\n", " / "),
                "",
                row.get("url", ""),
                "",
            ]
        md.write_text("\n".join(lines), encoding="utf-8")

    print(f"saved={output} rows={len(all_rows)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
