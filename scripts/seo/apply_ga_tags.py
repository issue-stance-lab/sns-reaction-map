#!/usr/bin/env python3
"""Apply Google Analytics gtag.js snippet to generated HTML files."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MARKER_START = "<!-- GA_TAG_START -->"
MARKER_END = "<!-- GA_TAG_END -->"
DEFAULT_ALLOWED_HOSTS = ("issue-stance-lab.github.io",)


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def validate_measurement_id(measurement_id: str) -> str:
    cleaned = measurement_id.strip()
    if not re.fullmatch(r"G-[A-Z0-9]+", cleaned):
        raise ValueError("GA measurement ID must look like G-XXXXXXXXXX")
    return cleaned


def validate_host(host: str) -> str:
    cleaned = host.strip().lower()
    if not cleaned or not re.fullmatch(r"[a-z0-9.-]+", cleaned):
        raise ValueError(f"Invalid GA host: {host!r}")
    return cleaned


def ga_block(measurement_id: str, allowed_hosts: tuple[str, ...] = DEFAULT_ALLOWED_HOSTS) -> str:
    escaped_id = html.escape(measurement_id, quote=True)
    encoded_hosts = json.dumps(list(allowed_hosts), ensure_ascii=True)
    return "\n".join(
        [
            MARKER_START,
            "  <script>",
            "    (function(){",
            f"      var allowedHosts = {encoded_hosts};",
            "      if (allowedHosts.indexOf(window.location.hostname) === -1) return;",
            "      window.dataLayer = window.dataLayer || [];",
            "      window.gtag = window.gtag || function(){window.dataLayer.push(arguments);};",
            "      var script = document.createElement('script');",
            "      script.async = true;",
            f"      script.src = 'https://www.googletagmanager.com/gtag/js?id={escaped_id}';",
            "      document.head.appendChild(script);",
            "      window.gtag('js', new Date());",
            f"      window.gtag('config', '{escaped_id}');",
            "    })();",
            "  </script>",
            MARKER_END,
        ]
    )


def replace_or_insert_ga(content: str, block: str) -> str:
    pattern = re.compile(
        rf"\n?\s*{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}",
        flags=re.DOTALL,
    )
    if pattern.search(content):
        return pattern.sub("\n" + block, content, count=1)

    closing_head = re.search(r"</head>", content)
    if closing_head:
        return content[: closing_head.start()] + block + "\n" + content[closing_head.start() :]
    raise ValueError("HTML does not contain </head>")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply Google Analytics tags to docs/*.html")
    parser.add_argument("--measurement-id", required=True, help="Google Analytics measurement ID, e.g. G-XXXXXXXXXX")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument(
        "--allowed-host",
        action="append",
        default=[],
        help="Production hostname allowed to send GA4 events. Repeat for multiple hosts.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    measurement_id = validate_measurement_id(args.measurement_id)
    allowed_hosts = tuple(validate_host(host) for host in args.allowed_host) or DEFAULT_ALLOWED_HOSTS
    docs_dir = resolve(args.docs_dir)
    block = ga_block(measurement_id, allowed_hosts)

    changed: list[Path] = []
    for path in sorted(docs_dir.glob("*.html")):
        content = path.read_text(encoding="utf-8")
        updated = replace_or_insert_ga(content, block)
        if updated != content:
            changed.append(path)
            if not args.dry_run:
                path.write_text(updated, encoding="utf-8")

    action = "Would update" if args.dry_run else "Updated"
    print(f"{action}: {len(changed)} HTML files")
    for path in changed:
        print(f"- {path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
