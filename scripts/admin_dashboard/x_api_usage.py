"""Parse and summarize X research usage without storing post text."""

from __future__ import annotations

import datetime as dt
import json
import re
import uuid
from pathlib import Path
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
ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = ROOT / "company" / "dashboard" / "x-search-usage.json"


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
    return build_usage(raw, recorded_at=recorded_at)


def build_usage(raw: Any, *, recorded_at: str) -> dict[str, Any] | None:
    """Normalize one count-only record and attach the price snapshot."""
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
    unique = usage.get("unique_posts_read")
    for subset in ("post_detail_reads", "unique_users_read", "owned_posts_read", "candidates_shortlisted"):
        if isinstance(unique, int) and isinstance(usage.get(subset), int) and usage[subset] > unique:
            return None
    loaded = usage.get("search_results_loaded")
    if isinstance(loaded, int) and isinstance(unique, int) and unique > loaded:
        return None
    note = str(raw.get("note") or "")[:240]
    note = re.sub(r"https?://\S+", "[URL除去]", note)
    note = re.sub(r"(?<!\w)@[A-Za-z0-9_]+", "[アカウント除去]", note)
    usage["note"] = note
    usage["pricing"] = {
        "post_read_usd": POST_READ_USD,
        "user_read_usd": USER_READ_USD,
        "owned_post_read_usd": OWNED_POST_READ_USD,
        "source": PRICING_SOURCE,
        "checked_at": "2026-08-29",
    }
    usage["estimated_cost_usd"] = estimate_cost(usage)
    return usage


def read_usage_ledger(path: Path = LEDGER_PATH) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows = payload.get("runs") if isinstance(payload, dict) else None
    return rows if isinstance(rows, list) else []


def append_usage(
    usage: dict[str, Any], *, source_id: str | None = None, source: str = "desktop_skill", path: Path = LEDGER_PATH
) -> dict[str, Any]:
    """Atomically append a count-only run. Reusing source_id is idempotent."""
    source_id = source_id or uuid.uuid4().hex
    rows = read_usage_ledger(path)
    existing = next((item for item in rows if item.get("source_id") == source_id), None)
    if existing:
        return existing
    record = {"source_id": source_id, "source": source, **usage}
    rows.append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"version": 1, "runs": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
    return record


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
    return summarize_usage(
        [(job.get("result") or {}).get("x_api_usage") for job in jobs],
        now=now,
    )


def summarize_usage(usages: Iterable[dict[str, Any] | None], *, now: dt.datetime | None = None) -> dict[str, Any]:
    """Summarize count-only usage records from any desktop or dashboard session."""
    now = now or dt.datetime.now(dt.timezone.utc)
    rows = []
    for usage in usages:
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
