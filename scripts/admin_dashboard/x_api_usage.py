"""Parse and summarize X research usage without storing post text."""

from __future__ import annotations

import datetime as dt
import json
import re
from typing import Any, Iterable

POST_READ_USD = 0.005
USER_READ_USD = 0.010
OWNED_POST_READ_USD = 0.001
PRICING_SOURCE = "https://docs.x.com/x-api/getting-started/pricing"
_BLOCK = re.compile(r"X_USAGE_JSON_BEGIN\s*(\{[\s\S]*?\})\s*X_USAGE_JSON_END")
_COUNT_KEYS = (
    "queries_count", "search_results_loaded", "unique_posts_read", "post_detail_reads",
    "unique_users_read", "owned_posts_read", "candidates_shortlisted",
)


def parse_usage(messages: Iterable[dict[str, Any]], *, recorded_at: str) -> dict[str, Any] | None:
    """Return the last valid usage block emitted by an x.prepare session."""
    text = "\n".join(str(item.get("text") or "") for item in messages if item.get("role") == "assistant")
    matches = list(_BLOCK.finditer(text))
    if not matches:
        return None
    try:
        raw = json.loads(matches[-1].group(1))
    except json.JSONDecodeError:
        return None
    if not isinstance(raw, dict) or raw.get("mode") not in {"chrome", "x_api", "mixed"}:
        return None
    usage: dict[str, Any] = {
        "recorded_at": recorded_at,
        "mode": raw["mode"],
        "counts_complete": bool(raw.get("counts_complete")),
    }
    for key in _COUNT_KEYS:
        value = raw.get(key)
        usage[key] = value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None
    usage["note"] = str(raw.get("note") or "")[:240]
    usage["pricing"] = {
        "post_read_usd": POST_READ_USD,
        "user_read_usd": USER_READ_USD,
        "owned_post_read_usd": OWNED_POST_READ_USD,
        "source": PRICING_SOURCE,
        "checked_at": "2026-08-29",
    }
    usage["estimated_cost_usd"] = estimate_cost(usage)
    return usage


def estimate_cost(usage: dict[str, Any]) -> dict[str, float] | None:
    """Estimate API cost from observed unique resources; never invent missing counts."""
    posts = usage.get("unique_posts_read")
    if not isinstance(posts, int):
        return None
    owned = usage.get("owned_posts_read")
    owned = owned if isinstance(owned, int) else 0
    owned = min(owned, posts)
    post_cost = (posts - owned) * POST_READ_USD + owned * OWNED_POST_READ_USD
    users = usage.get("unique_users_read")
    with_users = post_cost + (users * USER_READ_USD if isinstance(users, int) else 0)
    return {"posts_only": round(post_cost, 6), "posts_and_users": round(with_users, 6)}


def summarize_jobs(jobs: Iterable[dict[str, Any]], *, now: dt.datetime | None = None) -> dict[str, Any]:
    """Summarize measured x.prepare jobs for 7- and 30-day dashboard cards."""
    now = now or dt.datetime.now(dt.timezone.utc)
    rows = []
    for job in jobs:
        usage = (job.get("result") or {}).get("x_api_usage")
        if not usage:
            continue
        try:
            at = dt.datetime.fromisoformat(str(usage["recorded_at"]))
            if at.tzinfo is None:
                at = at.replace(tzinfo=dt.timezone.utc)
        except (KeyError, TypeError, ValueError):
            continue
        rows.append((at, usage))

    def period(days: int) -> dict[str, Any]:
        selected = [usage for at, usage in rows if now - at.astimezone(dt.timezone.utc) <= dt.timedelta(days=days)]
        known = [usage for usage in selected if usage.get("estimated_cost_usd")]
        return {
            "runs": len(selected),
            "complete_runs": sum(bool(item.get("counts_complete")) for item in selected),
            "unique_posts_read": sum(item.get("unique_posts_read") or 0 for item in known),
            "unique_users_read": sum(item.get("unique_users_read") or 0 for item in known),
            "posts_only_usd": round(sum(item["estimated_cost_usd"]["posts_only"] for item in known), 6),
            "posts_and_users_usd": round(sum(item["estimated_cost_usd"]["posts_and_users"] for item in known), 6),
        }

    return {"days_7": period(7), "days_30": period(30), "pricing_source": PRICING_SOURCE}
