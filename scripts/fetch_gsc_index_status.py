#!/usr/bin/env python3
"""Read saved Google index status for every URL in the public sitemap.

Does not run live URL tests or request indexing. Run from the repository root;
uses the existing fetch_gsc_metrics OAuth credentials. A failed inspection is
reported separately from a Google indexing exclusion and exits nonzero.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import json
import os
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

import fetch_gsc_metrics as gsc


def inspect_url(url: str, token: str, site: str) -> dict:
    request = urllib.request.Request(
        'https://searchconsole.googleapis.com/v1/urlInspection/index:inspect',
        data=json.dumps({'inspectionUrl': url, 'siteUrl': site, 'languageCode': 'ja-JP'}).encode(),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            result = json.load(response)['inspectionResult']['indexStatusResult']
        if not result.get('verdict') or not result.get('coverageState'):
            raise ValueError('Missing verdict or coverageState')
        return {'url': url, 'indexStatusResult': result}
    except Exception as error:
        # Never print the token, request headers or OAuth response.
        return {'url': url, 'inspectionError': type(error).__name__}


def summarize(rows: list[dict]) -> dict:
    return {
        'total': len(rows),
        'inspection_errors': sum('inspectionError' in row for row in rows),
        'coverage_states': dict(Counter(
            row['indexStatusResult']['coverageState']
            for row in rows if 'indexStatusResult' in row
        )),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='New JSON snapshot file')
    parser.add_argument('--sitemap', default='https://sns-reaction-map.jp/sitemap.xml')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; choose a new snapshot filename.')
    gsc.load_dotenv(Path('.env'))
    # Do not start a second interactive login flow during an unattended review.
    if not gsc.TOKEN_PATH.exists():
        parser.error('Existing GSC OAuth token required; set up fetch_gsc_metrics first.')
    stored = json.loads(gsc.TOKEN_PATH.read_text())
    if not stored.get('refresh_token'):
        parser.error('Existing GSC OAuth refresh token required.')
    token = gsc.refresh_access_token(gsc.read_client_secret(), stored)['access_token']
    with urllib.request.urlopen(args.sitemap, timeout=35) as response:
        root = ET.fromstring(response.read())
    namespace = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    if root.tag != namespace + 'urlset':
        parser.error('Expected a URL sitemap (not a sitemap index).')
    urls = sorted({element.text.strip() for element in root.findall(f'{namespace}url/{namespace}loc') if element.text})
    if not urls:
        parser.error('Sitemap contains no URLs.')
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(lambda url: inspect_url(url, token, os.environ.get('GSC_SITE_URL', gsc.DEFAULT_SITE_URL)), urls))
    report = {'started_at': started, 'finished_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'sitemap': args.sitemap, 'summary': summarize(rows), 'urls': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report['summary'], ensure_ascii=False, indent=2))
    return 1 if report['summary']['inspection_errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
