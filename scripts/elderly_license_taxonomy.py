#!/usr/bin/env python3
"""高齢者免許返納アリーナの論点・立場定義。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

ISSUES = [
    "義務化・事故防止",
    "地方の足・移動権",
    "適性検査強化",
    "代替交通整備",
    "自主返納支援",
    "その他",
]

STANCES = [
    "義務化賛成",
    "条件付き賛成",
    "義務化反対",
    "中立・情報",
]

ISSUE_SET = set(ISSUES)
STANCE_SET = set(STANCES)

ISSUE_INDEX = {label: index for index, label in enumerate(ISSUES)}
STANCE_INDEX = {label: index for index, label in enumerate(STANCES)}
