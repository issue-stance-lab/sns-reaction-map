"""公開ページの論点件数が、分類結果とずれたまま残らないことを確かめる。

2026-08-09、生成AIのページは論点カードだけが更新され、論点ナビ・論点見出し・
アリーナのセクターは7月22日に捨てた旧分類の数字（126件）を表示し続けていた。
同じ論点に「126件」と「340件」が並んで出ていたが、既存の検査は
どれも気づけなかった（件数の網羅検査はトップページにしか掛かっていない）。
"""

import subprocess
import sys
import unittest
from pathlib import Path

from scripts.issue_card_counts import IssueCountError
from scripts.sync_issue_counts import apply_arena, apply_conclusion, apply_nav


ROOT = Path(__file__).resolve().parent.parent


class IssueCountSyncTest(unittest.TestCase):
    def test_published_pages_have_no_stale_issue_counts(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/sync_issue_counts.py", "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_nav_number_follows_the_anchor_not_the_order(self) -> None:
        page = '<nav class="quadrant-nav"><a href="#issue-a">論点A 11</a>' '<a href="#issue-b">論点B 22</a></nav>'
        cards = [
            {"slug": "a", "anchor": "issue-a", "count": 33, "arena_label": ""},
            {"slug": "b", "anchor": "issue-b", "count": 44, "arena_label": ""},
        ]

        self.assertEqual(
            apply_nav(page, "t", cards),
            '<nav class="quadrant-nav"><a href="#issue-a">論点A 33</a>'
            '<a href="#issue-b">論点B 44</a></nav>',
        )

    def test_conclusion_refuses_to_update_when_the_top_issue_changed(self) -> None:
        page = '<span class="conclusion-count"><b>11</b>件</span>'
        cards = [
            {"slug": "a", "anchor": "issue-a", "count": 11, "arena_label": ""},
            {"slug": "b", "anchor": "issue-b", "count": 99, "arena_label": ""},
        ]

        # 見出しの文章は人が書いているので、数字だけ差し替えると
        # 「最大勢力」と中身が食い違う。書き換えずに止める。
        with self.assertRaises(IssueCountError) as caught:
            apply_conclusion(page, "t", cards, "a")
        self.assertIn("入れ替わりました", str(caught.exception))

    def test_arena_sector_without_a_card_takes_the_remainder(self) -> None:
        page = "const ISSUES=[{k:'論点A', n:1},{k:'その他', n:2}];"
        cards = [{"slug": "a", "anchor": "issue-a", "count": 30, "arena_label": "論点A"}]

        self.assertEqual(
            apply_arena(page, "t", cards, other=7),
            "const ISSUES=[{k:'論点A', n:30},{k:'その他', n:7}];",
        )

    def test_arena_fails_when_a_card_has_no_matching_sector(self) -> None:
        page = "const ISSUES=[{k:'論点A', n:1}];"
        cards = [{"slug": "b", "anchor": "issue-b", "count": 5, "arena_label": "論点B"}]

        with self.assertRaises(IssueCountError):
            apply_arena(page, "t", cards, other=0)


if __name__ == "__main__":
    unittest.main()
