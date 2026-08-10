"""管理画面ビルダーの検査。

守りたいのは3点。
  1. 実際のリポジトリの中身で最後まで組み上がること（落ちない）
  2. 出力が公開物に混ざらないこと（docs/ の外・robots で拒否・Git 管理外）
  3. docs/x-posts.md の実績記録を取りこぼさないこと
"""

import datetime as dt
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from admin_dashboard import collect, render  # noqa: E402


TODAY = dt.date(2026, 8, 10)


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {
            "today": TODAY,
            "built_at": dt.datetime(2026, 8, 10, 9, 0),
            "themes": collect.collect_themes(TODAY),
            "kpi": collect.collect_kpi(),
            "x_posts": collect.collect_x_posts(),
            "commits": collect.collect_commits(20),
            "data_updates": collect.collect_data_updates(),
            "tasks": collect.collect_tasks(),
            "health": collect.collect_source_health(TODAY),
            "live": None,
        }
        cls.html = render.render(cls.data)

    def test_all_sections_render(self):
        for anchor, _ in render.NAV:
            self.assertIn(f'id="{anchor}"', self.html, f"{anchor} セクションが出ていない")

    def test_no_unrendered_placeholders(self):
        self.assertNotIn("None", self.html)
        self.assertNotIn("{'", self.html)

    def test_marked_noindex_and_self_contained(self):
        self.assertIn('name="robots" content="noindex,nofollow"', self.html)
        # 外部CDNに依存しない（オフラインでも開ける）
        self.assertNotRegex(self.html, r'<(script|link)[^>]+(src|href)="https?://')

    def test_every_theme_appears(self):
        for theme in self.data["themes"]:
            self.assertIn(theme["title"], self.html)


class ThemeScheduleTests(unittest.TestCase):
    def test_days_until_deadline_is_signed(self):
        themes = collect.collect_themes(TODAY)
        self.assertTrue(themes, "THEMES.yaml が読めていない")
        for theme in themes:
            if theme["collect_at"]:
                self.assertEqual(theme["collect_in"], (theme["collect_at"] - TODAY).days)

    def test_sorted_by_nearest_deadline(self):
        pending = [t["collect_in"] for t in collect.collect_themes(TODAY) if t["collect_in"] is not None]
        self.assertEqual(pending, sorted(pending))

    def test_update_mode_is_translated(self):
        for theme in collect.collect_themes(TODAY):
            self.assertIn(theme["update_mode_label"], {"自動", "準自動", "手動", "不明"})


class XPostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.posts = collect.collect_x_posts()
        cls.source = (ROOT / "docs" / "x-posts.md").read_text(encoding="utf-8")

    def test_every_result_section_is_captured(self):
        """『◯◯実績 YYYY-MM-DD』の見出しが1つでも欠けたら気づけるようにする。"""
        dates = {m.group(1) for m in re.finditer(r"^##\s+.+?実績\s+(\d{4}-\d{2}-\d{2})", self.source, re.M)}
        captured = {p["date"].isoformat() for p in self.posts}
        self.assertEqual(dates - captured, set(), "実績の節を取りこぼしている")

    def test_reply_tables_expand_to_one_row_each(self):
        replies = [p for p in self.posts if p["kind"] == "リプライ"]
        self.assertGreater(len(replies), 20, "リプライ表が1件も展開できていない")
        self.assertTrue(any(p["views"] for p in replies), "views を1件も読めていない")

    def test_views_suffix_is_expanded(self):
        self.assertEqual(collect._parse_views("923K"), 923_000)
        self.assertEqual(collect._parse_views("1.2M"), 1_200_000)
        self.assertEqual(collect._parse_views("10"), 10)
        self.assertIsNone(collect._parse_views("—"))

    def test_posts_are_newest_first(self):
        dates = [p["date"] for p in self.posts]
        self.assertEqual(dates, sorted(dates, reverse=True))


class OutputLocationTests(unittest.TestCase):
    def test_output_is_outside_docs(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import build_admin_dashboard

        relative = build_admin_dashboard.DEFAULT_OUTPUT.relative_to(ROOT)
        self.assertNotEqual(relative.parts[0], "docs", "公開ディレクトリに書き出している")

    def test_output_directory_is_git_ignored(self):
        result = subprocess.run(
            ["git", "check-ignore", "-q", "admin/dashboard.html"],
            cwd=ROOT,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, "admin/ が .gitignore に入っていない")


if __name__ == "__main__":
    unittest.main()
