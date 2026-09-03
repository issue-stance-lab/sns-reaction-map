"""TASK_BOARD.md（索引）が小さいまま保たれることを確かめる。

索引は毎セッション読まれるので、経緯を書き足すと他の作業に使える余力が減る。
2026-09-03 に索引と詳細（tasks/task-{番号}.md）を分けた。
"""

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TaskBoardTests(unittest.TestCase):
    def test_verify_task_board_passes(self):
        result = subprocess.run(
            [sys.executable, "scripts/verify_task_board.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_index_stays_small(self):
        size = len((ROOT / "TASK_BOARD.md").read_bytes())
        self.assertLess(size, 30_000, f"TASK_BOARD.md が {size:,} バイト。詳細は tasks/ へ移すこと")

    def test_admin_dashboard_still_reads_every_task(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from admin_dashboard import collect

        tasks = collect.collect_tasks()
        indexed = sorted(int(p.stem.split("-")[1]) for p in (ROOT / "tasks").glob("task-*.md"))
        self.assertEqual(sorted(task["id"] for task in tasks), indexed)
        for task in tasks:
            self.assertTrue(task["status"], f"課題{task['id']}: 状態が読めていない")
            self.assertTrue(task["next_step"], f"課題{task['id']}: 次にすることが読めていない")


if __name__ == "__main__":
    unittest.main()
