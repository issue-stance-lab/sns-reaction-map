#!/usr/bin/env python3
"""部活動アリーナの論点・立場定義を読み込む。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "bukatsu-chiiki-reaction-map.json"


def load_taxonomy(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    taxonomy = config.get("arena_taxonomy")
    if not isinstance(taxonomy, dict):
        raise ValueError(f"arena_taxonomy is missing: {path}")
    issues = taxonomy.get("issues")
    stances = taxonomy.get("stances")
    vote_stances = taxonomy.get("vote_stances")
    if not isinstance(issues, list) or len(issues) != 7:
        raise ValueError("bukatsu arena_taxonomy must have 7 issues")
    if not isinstance(stances, list) or len(stances) != 4:
        raise ValueError("bukatsu arena_taxonomy must have 4 stances")
    if not isinstance(vote_stances, list) or len(vote_stances) != 3:
        raise ValueError("bukatsu arena_taxonomy must have 3 vote stances")
    labels = [item["label"] for item in issues]
    if len(labels) != len(set(labels)) or labels[-1] != "その他":
        raise ValueError("bukatsu issue labels must be unique and end with その他")
    vote_issues = [item for item in issues if item.get("vote_enabled")]
    if len(vote_issues) != 7 or vote_issues != issues:
        raise ValueError("bukatsu v1 compatibility requires all 7 vote issues")
    if taxonomy.get("topic_id") != "bukatsu-chiiki-issue-stance-v1":
        raise ValueError("bukatsu topic_id must remain v1")
    if len(vote_issues) * len(vote_stances) != 21:
        raise ValueError("bukatsu vote choice mapping changed")
    return taxonomy


TAXONOMY = load_taxonomy()
ISSUE_DEFS = TAXONOMY["issues"]
STANCE_DEFS = TAXONOMY["stances"]
ISSUES = [item["label"] for item in ISSUE_DEFS]
STANCES = [item["label"] for item in STANCE_DEFS]
ISSUE_INDEX = {label: index for index, label in enumerate(ISSUES)}
STANCE_BY_LABEL = {item["label"]: item for item in STANCE_DEFS}
VOTE_ISSUES = [item for item in ISSUE_DEFS if item["vote_enabled"]]
VOTE_STANCES = TAXONOMY["vote_stances"]
TOPIC_ID = TAXONOMY["topic_id"]
