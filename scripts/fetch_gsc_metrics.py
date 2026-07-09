#!/usr/bin/env python3
"""Fetch Google Search Console metrics with local OAuth.

Required .env values:
- GOOGLE_OAUTH_CLIENT_SECRET

Optional .env values:
- GSC_SITE_URL

First run prints a Google authorization URL. Open it, approve access, and the
local callback saves a refresh token under secrets/.
"""

from __future__ import annotations

import argparse
import datetime as dt
import http.server
import json
import os
import sys
import threading
import urllib.parse
import urllib.request
from pathlib import Path


SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
TOKEN_PATH = Path("secrets/gsc-oauth-token.json")
DEFAULT_SITE_URL = "https://issue-stance-lab.github.io/sns-reaction-map/"


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
                self.wfile.write(b"GSC authorization complete. You can close this tab.")
            else:
                code_box["error"] = params.get("error", ["missing authorization code"])[0]
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"GSC authorization failed.")

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
    token = post_form(
        token_uri,
        {
            "client_id": client["client_id"],
            "client_secret": client["client_secret"],
            "code": code_box["code"],
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


def query_search_analytics(access_token: str, site_url: str, days: int, dimensions: list[str]) -> dict:
    end_date = dt.date.today() - dt.timedelta(days=1)
    start_date = end_date - dt.timedelta(days=days - 1)
    encoded_site = urllib.parse.quote(site_url, safe="")
    url = f"https://searchconsole.googleapis.com/webmasters/v3/sites/{encoded_site}/searchAnalytics/query"
    payload = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": dimensions,
        "rowLimit": 25,
    }
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


def summarize(report: dict) -> dict[str, float]:
    totals = {"clicks": 0.0, "impressions": 0.0, "ctr": 0.0, "position": 0.0}
    rows = report.get("rows", [])
    if not rows:
        return totals
    total_clicks = sum(float(row.get("clicks", 0)) for row in rows)
    total_impressions = sum(float(row.get("impressions", 0)) for row in rows)
    weighted_position = sum(
        float(row.get("position", 0)) * float(row.get("impressions", 0)) for row in rows
    )
    totals["clicks"] = total_clicks
    totals["impressions"] = total_impressions
    totals["ctr"] = total_clicks / total_impressions if total_impressions else 0.0
    totals["position"] = weighted_position / total_impressions if total_impressions else 0.0
    return totals


def print_markdown(summary: dict[str, float]) -> None:
    print("| metric | value |")
    print("|---|---:|")
    for key, value in summary.items():
        if key in {"clicks", "impressions"}:
            print(f"| {key} | {int(value)} |")
        else:
            print(f"| {key} | {value:.4f} |")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=28)
    parser.add_argument("--site-url", default="")
    parser.add_argument("--dimension", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    load_dotenv(Path(".env"))
    site_url = args.site_url or os.environ.get("GSC_SITE_URL", "") or DEFAULT_SITE_URL
    client = read_client_secret()
    token = get_token(client)
    report = query_search_analytics(token["access_token"], site_url, args.days, args.dimension)
    summary = summarize(report)
    if args.json:
        print(json.dumps({"site_url": site_url, "summary": summary, "rows": report.get("rows", [])}, ensure_ascii=False, indent=2))
    else:
        print(f"site_url: {site_url}")
        print_markdown(summary)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as exc:
        sys.stderr.write(f"GSC HTTP error {exc.code}: {exc.read().decode('utf-8')}\n")
        raise SystemExit(1)
