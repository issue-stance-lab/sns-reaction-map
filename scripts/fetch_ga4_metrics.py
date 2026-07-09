#!/usr/bin/env python3
"""Fetch GA4 metrics with local OAuth.

Required .env values:
- GA4_PROPERTY_ID
- GOOGLE_OAUTH_CLIENT_SECRET

First run prints a Google authorization URL. Open it, approve access, paste the
returned code into the terminal. A refresh token is saved under secrets/.
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import sys
import threading
import urllib.parse
import urllib.request
from pathlib import Path


SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
TOKEN_PATH = Path("secrets/ga4-oauth-token.json")


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def read_client_secret() -> dict:
    path = Path(os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", ""))
    if not path.exists():
        raise SystemExit("GOOGLE_OAUTH_CLIENT_SECRET must point to an OAuth client JSON file.")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("installed") or data.get("web") or data


def post_form(url: str, payload: dict) -> dict:
    body = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def oauth_authorize(client: dict) -> dict:
    auth_uri = client.get("auth_uri", "https://accounts.google.com/o/oauth2/auth")
    token_uri = client.get("token_uri", "https://oauth2.googleapis.com/token")
    code_box: dict[str, str] = {}

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib callback name
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            if "code" in params:
                code_box["code"] = params["code"][0]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"GA4 authorization complete. You can close this tab.")
            else:
                code_box["error"] = params.get("error", ["missing authorization code"])[0]
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"GA4 authorization failed.")

        def log_message(self, fmt: str, *args: object) -> None:
            return

    server = http.server.HTTPServer(("127.0.0.1", 0), CallbackHandler)
    port = server.server_address[1]
    redirect_uri = f"http://127.0.0.1:{port}/"
    params = {
        "client_id": client["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    print("Open this URL and approve access:")
    print(auth_uri + "?" + urllib.parse.urlencode(params))
    print("Waiting for browser authorization callback...")
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    thread.join(timeout=600)
    server.server_close()
    if "error" in code_box:
        raise SystemExit(f"OAuth authorization failed: {code_box['error']}")
    if "code" not in code_box:
        raise SystemExit("OAuth authorization timed out.")
    code = code_box["code"]
    token = post_form(
        token_uri,
        {
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
    )
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(token, indent=2), encoding="utf-8")
    return token


def refresh_access_token(client: dict, token: dict) -> dict:
    if "refresh_token" not in token:
        return oauth_authorize(client)
    refreshed = post_form(
        client.get("token_uri", "https://oauth2.googleapis.com/token"),
        {
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "refresh_token": token["refresh_token"],
            "grant_type": "refresh_token",
        },
    )
    token.update(refreshed)
    TOKEN_PATH.write_text(json.dumps(token, indent=2), encoding="utf-8")
    return token


def get_token(client: dict) -> dict:
    if not TOKEN_PATH.exists():
        return oauth_authorize(client)
    token = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    return refresh_access_token(client, token)


def call_run_report(access_token: str, property_id: str, payload: dict) -> dict:
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode("utf-8"))


def run_report(access_token: str, property_id: str, days: int) -> dict:
    payload = {
        "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "yesterday"}],
        "metrics": [
            {"name": "activeUsers"},
            {"name": "screenPageViews"},
            {"name": "sessions"},
            {"name": "eventCount"},
        ],
    }
    return call_run_report(access_token, property_id, payload)


def run_page_path_report(access_token: str, property_id: str, days: int, limit: int) -> dict:
    payload = {
        "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "yesterday"}],
        "dimensions": [{"name": "pagePath"}],
        "metrics": [{"name": "screenPageViews"}, {"name": "activeUsers"}],
        "orderBys": [{"metric": {"metricName": "screenPageViews"}, "desc": True}],
        "limit": limit,
    }
    return call_run_report(access_token, property_id, payload)


def run_event_report(access_token: str, property_id: str, days: int, event_name: str) -> dict:
    payload = {
        "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "yesterday"}],
        "dimensions": [{"name": "eventName"}],
        "metrics": [{"name": "eventCount"}],
        "dimensionFilter": {
            "filter": {
                "fieldName": "eventName",
                "stringFilter": {"matchType": "EXACT", "value": event_name},
            }
        },
    }
    return call_run_report(access_token, property_id, payload)


def run_share_source_report(access_token: str, property_id: str, days: int) -> dict:
    payload = {
        "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "yesterday"}],
        "dimensions": [{"name": "sessionSource"}, {"name": "sessionMedium"}],
        "metrics": [{"name": "sessions"}, {"name": "activeUsers"}, {"name": "screenPageViews"}],
        "dimensionFilter": {
            "filter": {
                "fieldName": "sessionSource",
                "stringFilter": {"matchType": "EXACT", "value": "share_button"},
            }
        },
        "limit": 25,
    }
    return call_run_report(access_token, property_id, payload)


def summarize(report: dict) -> dict[str, str]:
    headers = [h["name"] for h in report.get("metricHeaders", [])]
    values = []
    rows = report.get("rows", [])
    if rows:
        values = [v["value"] for v in rows[0].get("metricValues", [])]
    return dict(zip(headers, values))


def report_rows(report: dict) -> list[dict]:
    dimensions = [h["name"] for h in report.get("dimensionHeaders", [])]
    metrics = [h["name"] for h in report.get("metricHeaders", [])]
    rows = []
    for row in report.get("rows", []):
        item = {}
        for key, value in zip(dimensions, row.get("dimensionValues", [])):
            item[key] = value.get("value", "")
        for key, value in zip(metrics, row.get("metricValues", [])):
            item[key] = value.get("value", "")
        rows.append(item)
    return rows


def detail_bundle(access_token: str, property_id: str, days: int, limit: int) -> dict:
    summary = summarize(run_report(access_token, property_id, days))
    page_paths = report_rows(run_page_path_report(access_token, property_id, days, limit))
    related_theme_click = summarize(run_event_report(access_token, property_id, days, "related_theme_click"))
    if "eventCount" not in related_theme_click:
        related_theme_click["eventCount"] = "0"
    share_button = report_rows(run_share_source_report(access_token, property_id, days))
    return {
        "summary": summary,
        "page_paths": page_paths,
        "events": {"related_theme_click": related_theme_click},
        "share_button": share_button,
    }


def print_markdown(summary: dict[str, str]) -> None:
    print("| metric | value |")
    print("|---|---:|")
    for key, value in summary.items():
        print(f"| {key} | {value} |")


def print_details(details: dict) -> None:
    print("## Summary")
    print_markdown(details["summary"])
    print()
    print("## Page paths")
    print("| pagePath | screenPageViews | activeUsers |")
    print("|---|---:|---:|")
    for row in details["page_paths"]:
        print(f"| {row.get('pagePath', '')} | {row.get('screenPageViews', '0')} | {row.get('activeUsers', '0')} |")
    print()
    print("## Events")
    print("| eventName | eventCount |")
    print("|---|---:|")
    event_count = details["events"]["related_theme_click"].get("eventCount", "0")
    print(f"| related_theme_click | {event_count} |")
    print()
    print("## Share button traffic")
    print("| sessionSource | sessionMedium | sessions | activeUsers | screenPageViews |")
    print("|---|---|---:|---:|---:|")
    if not details["share_button"]:
        print("| share_button |  | 0 | 0 | 0 |")
    for row in details["share_button"]:
        print(
            f"| {row.get('sessionSource', '')} | {row.get('sessionMedium', '')} | "
            f"{row.get('sessions', '0')} | {row.get('activeUsers', '0')} | "
            f"{row.get('screenPageViews', '0')} |"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--details", action="store_true", help="Fetch pagePath, related_theme_click, and share_button reports")
    parser.add_argument("--limit", type=int, default=20, help="Row limit for detail reports")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    load_dotenv(Path(".env"))
    property_id = os.environ.get("GA4_PROPERTY_ID", "")
    if not property_id:
        raise SystemExit("GA4_PROPERTY_ID is required.")

    client = read_client_secret()
    token = get_token(client)
    if args.details:
        details = detail_bundle(token["access_token"], property_id, args.days, args.limit)
        if args.json:
            print(json.dumps(details, ensure_ascii=False, indent=2))
        else:
            print_details(details)
        return 0
    report = run_report(token["access_token"], property_id, args.days)
    summary = summarize(report)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print_markdown(summary)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as exc:
        sys.stderr.write(f"GA4 HTTP error {exc.code}: {exc.read().decode('utf-8')}\n")
        raise SystemExit(1)
