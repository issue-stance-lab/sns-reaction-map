#!/usr/bin/env python3
"""Fetch Yahoo realtime refresh rows for one configured topic."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_topic(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a YAML object")
    queries = data.get("fetch_queries")
    if not isinstance(queries, list) or not queries:
        raise ValueError(f"{path} has no fetch_queries")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--wait-ms", default="5000")
    args = parser.parse_args()

    topic_path = PROJECT_ROOT / "configs" / "topics" / f"{args.topic}.yaml"
    topic = load_topic(topic_path)
    queries = [str(query) for query in topic["fetch_queries"]]
    output = PROJECT_ROOT / "social-samples" / f"{args.topic}_samples_refresh_{args.date}.json"
    markdown = output.with_suffix(".md")

    cmd = [
        "node",
        str(PROJECT_ROOT / "scripts" / "fetch_yahoo_realtime_node.mjs"),
        "--output",
        str(output),
        "--markdown",
        str(markdown),
        "--dedupe",
        "--wait-ms",
        str(args.wait_ms),
    ]
    for query in queries:
        cmd.extend(["--query", query])

    print(json.dumps({"topic": args.topic, "queries": queries, "output": str(output)}, ensure_ascii=False))
    return subprocess.call(cmd, cwd=PROJECT_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
