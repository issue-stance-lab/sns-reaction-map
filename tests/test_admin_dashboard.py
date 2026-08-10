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
        self.assertTrue(any(p["parent_views"] for p in replies), "元投稿views を1件も読めていない")

    def test_views_suffix_is_expanded(self):
        self.assertEqual(collect._parse_views("923K"), 923_000)
        self.assertEqual(collect._parse_views("1.2M"), 1_200_000)
        self.assertEqual(collect._parse_views("10"), 10)
        self.assertIsNone(collect._parse_views("—"))

    def test_views_accept_comma_man_bold_and_trailing_note(self):
        """実際に docs/x-posts.md に現れる表記をすべて読めること。

        いずれか1つでも読めないと、その投稿は「表示回数なし」として静かに
        集計から落ちる。2026-08-06〜08-10 が5日ぶん消えていたのがこれ。
        """
        self.assertEqual(collect._parse_views("4,916（8/8 18:50時点）"), 4_916)
        self.assertEqual(collect._parse_views("2.5万（8/8 18:35時点）"), 25_000)
        self.assertEqual(collect._parse_views("1,368K"), 1_368_000)
        self.assertEqual(collect._parse_views("**101**"), 101)
        self.assertEqual(collect._parse_views("10**"), 10)

    def test_provisional_and_missing_views_are_distinguished(self):
        """投稿直後の暫定値を実測と混ぜない。8/8は 4→51、2→37 と10倍以上動いた。"""
        self.assertEqual(collect._views_status("4（投稿7分後）"), "provisional")
        self.assertEqual(collect._views_status("2（投稿直後）"), "provisional")
        self.assertEqual(collect._views_status("未計測（投稿直後）"), "missing")
        self.assertEqual(collect._views_status("未取得"), "missing")
        self.assertEqual(collect._views_status(""), "missing")
        self.assertEqual(collect._views_status("**101**"), "measured")
        # 注記が旧状態に言及していても、本計測なら実測として扱う
        self.assertEqual(collect._views_status("**74**（8/10計測。旧記録は「未取得」）"), "measured")
        self.assertEqual(collect._views_status("**51**（8/10計測。旧記録の「4」は投稿7分後の暫定値）"), "measured")

    def test_parent_and_own_views_are_separate_fields(self):
        """元投稿の表示回数と自分の到達を1つの数値に混ぜない。

        混ぜていたために「30日で7.6M」が自分のリーチとして GROWTH.yaml に
        記録され、PV 90 と比較して「変換できていない」という誤った所見になった。
        """
        row = next(p for p in self.posts if p["target"].startswith("@bunshun_online"))
        self.assertEqual(row["parent_views"], 11_070)
        self.assertEqual(row["own_views"], 642)
        self.assertEqual(row["own_views_status"], "measured")

    def test_new_two_column_tables_are_not_dropped(self):
        """『元投稿views ｜ 自リプライ表示』形式の表が空扱いにならないこと。"""
        rows = collect._table_rows(
            [
                "| # | リプライ先 | テーマ | タイプ | 元投稿views | 自リプライ表示 | 元投稿の返信数 |",
                "|---|---|---|---|---|---|---|",
                "| 1 | @a（x） | t | URLなし | 11,070 | **642** | 4 |",
                "| 2 | @b（y） | t | URLなし | 3,623 | 未計測（投稿直後） | 3 |",
            ],
            "テスト",
        )
        self.assertEqual(len(rows), 2, "2列形式の表が1行ずつに展開されていない")
        self.assertEqual(rows[0]["自リプライ表示"], "**642**")

    def test_unknown_view_column_raises_instead_of_dropping(self):
        """表示回数の列名を変えたら、黙って捨てずに落ちること。

        これが無かったため、2026-08-06 の見出し変更に誰も気づかないまま
        既存テストが通り続け、実測値が5日ぶんダッシュボードから消えていた。
        """
        with self.assertRaises(ValueError) as ctx:
            collect._table_rows(
                [
                    "| # | リプライ先 | テーマ | インプレッション数 |",
                    "|---|---|---|---|",
                    "| 1 | @a（x） | t | 100 |",
                ],
                "リプライ実績 2026-09-01",
            )
        self.assertIn("インプレッション数", str(ctx.exception))
        self.assertIn("リプライ実績 2026-09-01", str(ctx.exception))

    def test_non_post_tables_are_ignored_without_raising(self):
        """実績節に混ざるGA4の参照元表などは投稿表として扱わない。"""
        rows = collect._table_rows(
            [
                "| 参照元 / メディア | セッション | エンゲージメント率 |",
                "|---|---|---|",
                "| t.co / referral | 3 | 33.3% |",
            ],
            "通常ポスト実績 2026-08-01",
        )
        self.assertEqual(rows, [])

    def test_measured_own_views_are_recorded_for_every_recent_day(self):
        """8/6〜8/10 の実測値がすべて拾えていること（欠けたら0本になる日が出る）。"""
        measured = {
            p["date"].isoformat()
            for p in self.posts
            if p["own_views_status"] == "measured" and p["own_views"] is not None
        }
        for day in ("2026-08-06", "2026-08-07", "2026-08-08", "2026-08-09", "2026-08-10"):
            self.assertIn(day, measured, f"{day} の自リプライ表示が1件も読めていない")

    def test_has_url_is_derived_from_type_column(self):
        self.assertFalse(collect._has_url("URLなし・tokoso画像付き", "リプライ"))
        self.assertTrue(collect._has_url("型C（反対側の最も強い論拠）", "流入投稿（URL付き）"))

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
