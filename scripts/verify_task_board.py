#!/usr/bin/env python3
"""TASK_BOARD.md（索引）が小さいまま保たれているかを検査する。

TASK_BOARD.md は毎セッション読まれるので、経緯や調査記録を書き足すと
その分だけ他の作業に使える余力が減る。2026-09-03 に索引と詳細を分けた。
索引には1課題あたり数行だけを置き、本文は tasks/task-{番号}.md に置く。

  python3 scripts/verify_task_board.py

NG が1件も無ければ exit 0。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / "TASK_BOARD.md"
TASKS = ROOT / "tasks"

# 索引の上限。今は約1.4万バイト。倍まで太ったら分割を見直す合図にする
MAX_BOARD_BYTES = 30_000
# 1つの欄の長さ。これを超える説明は詳細ファイルへ移す
MAX_FIELD_CHARS = 120
# 詳細ファイル1本の長さ。超えたら設計文書（quality/designs/）へ切り出す
MAX_DETAIL_LINES = 400

HEADING = re.compile(r"^###\s+課題(\d+)\s*[:：]\s*(.+?)\s*$")
FIELD = re.compile(r"^\*\*(.+?)\*\*\s*[:：]\s*(.*)$")

KNOWN_FIELDS = {"状態", "優先度", "期限", "次にすること", "判断待ち", "関連テーマ", "詳細"}
REQUIRED_FIELDS = {"状態", "次にすること", "詳細"}
PHASES = ("未着手", "進行中", "保留", "完了")


def parse_entries(text: str) -> list[dict]:
    entries: list[dict] = []
    current: dict | None = None
    for lineno, line in enumerate(text.splitlines(), 1):
        heading = HEADING.match(line)
        if heading:
            current = {
                "id": int(heading.group(1)),
                "title": heading.group(2),
                "line": lineno,
                "fields": {},
                "body": [],
            }
            entries.append(current)
            continue
        if line.startswith("## ") or line.strip() == "---":
            current = None  # 課題一覧の外（区切り線・連絡メモなど）に出た
            continue
        if current is None:
            continue
        field = FIELD.match(line.strip())
        if field and field.group(1) in KNOWN_FIELDS:
            current["fields"].setdefault(field.group(1), (lineno, field.group(2).strip()))
        elif line.strip():
            current["body"].append((lineno, line))
    return entries


def main() -> int:
    problems: list[str] = []
    text = BOARD.read_text(encoding="utf-8")

    size = len(text.encode("utf-8"))
    if size > MAX_BOARD_BYTES:
        problems.append(
            f"TASK_BOARD.md が {size:,} バイトある（上限 {MAX_BOARD_BYTES:,}）。"
            "経緯や調査記録を tasks/task-{番号}.md へ移すこと"
        )

    entries = parse_entries(text)
    if not entries:
        problems.append("TASK_BOARD.md に「### 課題N: タイトル」の行が1つも無い")

    seen: dict[int, int] = {}
    for entry in entries:
        tag = f"課題{entry['id']}（TASK_BOARD.md:{entry['line']}）"

        if entry["id"] in seen:
            problems.append(f"{tag}: 同じ番号が {seen[entry['id']]} 行目にもある")
        seen[entry["id"]] = entry["line"]

        missing = REQUIRED_FIELDS - set(entry["fields"])
        if missing:
            problems.append(f"{tag}: 必須の欄が無い → {'、'.join(sorted(missing))}")

        for name, (lineno, value) in entry["fields"].items():
            if len(value) > MAX_FIELD_CHARS:
                problems.append(
                    f"{tag}: 「{name}」が {len(value)} 文字（上限 {MAX_FIELD_CHARS}）。"
                    f"TASK_BOARD.md:{lineno} の説明を詳細ファイルへ移すこと"
                )

        status = entry["fields"].get("状態", (0, ""))[1].replace("*", "").strip()
        if status and not status.startswith(PHASES):
            problems.append(
                f"{tag}: 「状態」は {' / '.join(PHASES)} のどれかで書き出す（いまは「{status[:20]}…」）。"
                "管理ダッシュボードがこの書き出しで区分を判定している"
            )
        if status.startswith("完了"):
            problems.append(
                f"{tag}: 完了した課題は索引に残さない。"
                "tasks/task-N.md を archive/tasks/ へ移し、archive/TASK_BOARD_ARCHIVE.md に1行足すこと"
            )

        for lineno, line in entry["body"]:
            problems.append(
                f"{tag}: 欄以外の文章がある（TASK_BOARD.md:{lineno}「{line.strip()[:30]}…」）。"
                "詳細ファイルへ移すこと"
            )

        detail = ROOT / f"tasks/task-{entry['id']}.md"
        if not detail.exists():
            problems.append(f"{tag}: 詳細ファイル tasks/task-{entry['id']}.md が無い")
        elif entry["fields"].get("詳細") and f"task-{entry['id']}.md" not in entry["fields"]["詳細"][1]:
            problems.append(f"{tag}: 「詳細」の行が tasks/task-{entry['id']}.md を指していない")

    indexed = {entry["id"] for entry in entries}
    for path in sorted(TASKS.glob("task-*.md")):
        num = int(path.stem.split("-")[1])
        if num not in indexed:
            problems.append(f"{path.relative_to(ROOT)}: TASK_BOARD.md に行が無い（索引に足すか archive/tasks/ へ移す）")
        lines = len(path.read_text(encoding="utf-8").splitlines())
        if lines > MAX_DETAIL_LINES:
            problems.append(
                f"{path.relative_to(ROOT)}: {lines} 行ある（上限 {MAX_DETAIL_LINES}）。"
                "設計や調査の記録は quality/designs/・quality/reviews/ へ切り出すこと"
            )

    if problems:
        print(f"NG: {len(problems)} 件")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"OK: 索引 {size:,} バイト / 課題 {len(entries)} 件。すべての課題に詳細ファイルがあります")
    return 0


if __name__ == "__main__":
    sys.exit(main())
