#!/usr/bin/env python3
"""自転車青切符アリーナの論点・立場定義。"""

from __future__ import annotations

ISSUES = [
    "取締り強化賛成",
    "インフラ整備優先",
    "車道走行への不安",
    "免許制要求",
    "ルール曖昧・不信",
    "その他",
]

STANCES = [
    "賛成（取締り強化支持）",
    "どちらでもない",
    "反対（インフラ・制度優先）",
]

ISSUE_SET = set(ISSUES)
STANCE_SET = set(STANCES)

ISSUE_INDEX = {label: index for index, label in enumerate(ISSUES)}
STANCE_INDEX = {label: index for index, label in enumerate(STANCES)}
