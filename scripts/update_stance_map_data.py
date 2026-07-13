#!/usr/bin/env python3
"""Update embedded 2D stance-map data in an HTML page."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


THEMES: dict[str, dict[str, str]] = {
    "ai-copyright": {"x": "stance_regulation", "y": "stance_beneficiary", "kind": "raw_var"},
    "bukatsu-chiiki": {"x": "stance_transfer", "y": "stance_priority", "kind": "raw"},
    "constitutional-amendment": {"x": "stance_amendment", "y": "stance_priority", "kind": "raw"},
    "elderly-license-revocation": {"x": "stance_restriction", "y": "stance_priority", "kind": "raw"},
    "school-nickname-ban": {"x": "stance_ban", "y": "stance_culture", "kind": "points"},
    "henoko-student-accident": {"x": "stance_mext", "y": "stance_focus", "kind": "points"},
    "takaichi": {"x": "stance_accountability", "y": "stance_focus", "kind": "points"},
}


def js_string(value: Any) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")


def score(row: dict[str, Any], key: str) -> float:
    return round(float(row.get(key, 0.0)) * 2) / 2


def point_rows(rows: list[dict[str, Any]], x_key: str, y_key: str) -> str:
    points = []
    for row in rows:
        points.append(
            {
                "x": score(row, x_key),
                "y": score(row, y_key),
                "e": score(row, "emotional_intensity"),
                "summary": str(row.get("summary") or ""),
                "url": str(row.get("url") or ""),
                "confidence": round(float(row.get("confidence", 0.5)), 2),
            }
        )
    return "const STANCE_POINTS=" + json.dumps(points, ensure_ascii=False, separators=(",", ":")) + ";"


def raw_rows(rows: list[dict[str, Any]], x_key: str, y_key: str) -> str:
    lines = ["const SM_RAW = ["]
    for row in rows:
        lines.append(
            "  {"
            f"x:{score(row, x_key):.1f},"
            f"y:{score(row, y_key):.1f},"
            f"e:{score(row, 'emotional_intensity'):.1f},"
            f"c:{float(row.get('confidence', 0.5)):.2f},"
            f"s:{js_string(row.get('summary'))},"
            f"u:{js_string(row.get('url'))}"
            "},"
        )
    lines.append("];")
    return "\n".join(lines)


def raw_json_rows(rows: list[dict[str, Any]], x_key: str, y_key: str) -> str:
    raw = []
    for row in rows:
        raw.append(
            {
                "x": score(row, x_key),
                "y": score(row, y_key),
                "e": score(row, "emotional_intensity"),
                "c": round(float(row.get("confidence", 0.5)), 2),
                "s": str(row.get("summary") or ""),
                "u": str(row.get("url") or ""),
            }
        )
    return "const RAW = " + json.dumps(raw, ensure_ascii=False, separators=(",", ":")) + ";"


def counts(rows: list[dict[str, Any]], x_key: str, y_key: str) -> dict[str, int]:
    values = {"all": len(rows), "q1": 0, "q2": 0, "q3": 0, "q4": 0, "calm": 0, "neutral": 0}
    for row in rows:
        x = score(row, x_key)
        y = score(row, y_key)
        e = score(row, "emotional_intensity")
        if x > 0 and y > 0:
            values["q1"] += 1
        if x < 0 and y < 0:
            values["q2"] += 1
        if x < 0 and y > 0:
            values["q3"] += 1
        if e >= 1.5:
            values["q4"] += 1
        if e <= 0:
            values["calm"] += 1
        if x == 0 or y == 0:
            values["neutral"] += 1
    return values


def replace_once(text: str, pattern: str, replacement: str, label: str, flags: int = 0) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise ValueError(f"{label}: expected one match, found {count}")
    return updated


def update_counts(text: str, total: int, count_values: dict[str, int]) -> str:
    text = re.sub(r"(<h2>SNS意見スタンスマップ</h2><span>)\d+件", rf"\g<1>{total}件", text, count=1)
    text = re.sub(r"(<h2>2Dスタンスマップ</h2><span>)\d+件", rf"\g<1>{total}件", text, count=1)
    text = re.sub(r"全件 \(\d+\)", f"全件 ({total})", text, count=1)
    for key in ["q1", "q2", "q3", "q4", "calm"]:
        value = count_values[key]
        text = re.sub(
            rf'(<button[^>]+data-q="{key}"[^>]*>[^<]*?)\(\d+\)',
            rf"\g<1>({value})",
            text,
            count=1,
        )
    stat_values = [count_values["q1"], count_values["q2"], count_values["q3"], count_values["q4"]]
    for value in stat_values:
        text = re.sub(r'(<div class="sm-sval"[^>]*>)\d+件', rf"\g<1>{value}件", text, count=1)
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", required=True, choices=sorted(THEMES))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--html", type=Path, required=True)
    args = parser.parse_args()

    config = THEMES[args.theme]
    rows = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("input must be a non-empty JSON list")

    html = args.html.read_text(encoding="utf-8")
    if config["kind"] == "points":
        html = replace_once(
            html,
            r"const STANCE_POINTS=\[.*?\];",
            point_rows(rows, config["x"], config["y"]),
            "STANCE_POINTS",
            flags=re.DOTALL,
        )
    elif config["kind"] == "raw_var":
        html = replace_once(
            html,
            r"const RAW = \[.*?\];(?=\nconst TOUR)",
            raw_json_rows(rows, config["x"], config["y"]),
            "RAW",
            flags=re.DOTALL,
        )
    else:
        html = replace_once(
            html,
            r"const SM_RAW = \[.*?\n?\];",
            raw_rows(rows, config["x"], config["y"]),
            "SM_RAW",
            flags=re.DOTALL,
        )

    html = update_counts(html, len(rows), counts(rows, config["x"], config["y"]))
    args.html.write_text(html, encoding="utf-8")
    print(f"updated {args.html}: total={len(rows)} kind={config['kind']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
