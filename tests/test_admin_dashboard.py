"""管理画面ビルダーの検査。

守りたいのは3点。
  1. 実際のリポジトリの中身で最後まで組み上がること（落ちない）
  2. 出力が公開物に混ざらないこと（docs/ の外・robots で拒否・Git 管理外）
  3. x-posts.md の実績記録を取りこぼさないこと
"""

import datetime as dt
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from admin_dashboard import actions, collect, render  # noqa: E402


TODAY = dt.date(2026, 8, 10)


def build_data(today: dt.date = TODAY) -> dict:
    data = {
        "today": today,
        "built_at": dt.datetime(2026, 8, 10, 9, 0),
        "themes": collect.collect_themes(today),
        "kpi": collect.collect_kpi(),
        "x_posts": collect.collect_x_posts(),
        "commits": collect.collect_commits(20),
        "data_updates": collect.collect_data_updates(),
        "tasks": collect.collect_tasks(),
        "health": collect.collect_source_health(today),
        "live": None,
        "sample_files": collect.collect_sample_files(),
    }
    data["next"] = actions.next_action(data)
    return data


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build_data()
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


class AlertTests(unittest.TestCase):
    @staticmethod
    def _data(today: dt.date, last_run: dt.date | None, post_date: dt.date) -> dict:
        return {
            "today": today,
            "themes": [],
            "kpi": {
                "snapshots": [],
                "recurring": [
                    {"key": "x-posting", "last_run": last_run},
                ],
            },
            "x_posts": [{"date": post_date}],
            "health": [],
            "live": None,
        }

    def test_x_alert_uses_candidate_check_not_latest_post(self):
        data = self._data(
            today=dt.date(2026, 8, 14),
            last_run=dt.date(2026, 8, 10),
            post_date=dt.date(2026, 8, 14),
        )
        html = render.section_alerts(data)
        self.assertIn("X の候補確認が 4 日前で止まっています", html)
        self.assertNotIn("毎日1〜3件", html)

    def test_fresh_candidate_check_allows_no_recent_posts(self):
        data = self._data(
            today=dt.date(2026, 8, 14),
            last_run=dt.date(2026, 8, 14),
            post_date=dt.date(2026, 8, 1),
        )
        html = render.section_alerts(data)
        self.assertNotIn("X の候補確認", html)
        self.assertNotIn("X の投稿記録", html)

    def test_missing_candidate_check_date_is_reported(self):
        data = self._data(
            today=dt.date(2026, 8, 14),
            last_run=None,
            post_date=dt.date(2026, 8, 14),
        )
        html = render.section_alerts(data)
        self.assertIn("X の候補確認日が記録されていません", html)

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
        cls.source = (ROOT / "x-posts.md").read_text(encoding="utf-8")

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
        """実際に x-posts.md に現れる表記をすべて読めること。

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

    def test_conversation_follow_is_collected_as_own_post(self):
        follow = next(
            p for p in self.posts
            if p["kind"] == "会話フォロー" and p["date"] == dt.date(2026, 8, 9)
        )
        self.assertIn("FPXLej8w7O61326", follow["target"])
        self.assertEqual(follow["own_views_status"], "measured")
        self.assertEqual(follow["own_views"], 8)

    def test_has_url_is_derived_from_type_column(self):
        self.assertFalse(collect._has_url("URLなし・tokoso画像付き", "リプライ"))
        self.assertTrue(collect._has_url("型C（反対側の最も強い論拠）", "流入投稿（URL付き）"))

    def test_posts_are_newest_first(self):
        dates = [p["date"] for p in self.posts]
        self.assertEqual(dates, sorted(dates, reverse=True))


class NextActionTests(unittest.TestCase):
    """「次の一手」とコマンド組み立て。3つの不変条件を固定する。

    どれも実際に事故った、あるいは事故りうる箇所なので、
    ここが落ちたら実装ではなくテストの前提を疑うこと。
    """

    @classmethod
    def setUpClass(cls):
        cls.themes = collect.collect_themes(TODAY)
        cls.by_key = {theme["key"]: theme for theme in cls.themes}

    def _adapter_theme(self) -> dict:
        for theme in self.themes:
            if theme["update_mode"] == "adapter":
                return theme
        self.skipTest("adapter のテーマが THEMES.yaml に無い")

    def test_date_is_the_run_day_not_the_scheduled_day(self):
        """--date は実行日。予定日を渡すと次回更新日がずれて更新が静かに止まる。"""
        theme = self._adapter_theme()
        run_day = TODAY + dt.timedelta(days=3)
        block = actions.command_block(theme, run_day, promote=False)
        self.assertIn("--date 2026-08-13", block["script"])
        if theme["collect_at"] and theme["collect_at"] != run_day:
            self.assertNotIn(f"--date {theme['collect_at']:%Y-%m-%d}", block["script"])

    def test_commands_start_by_making_a_worktree(self):
        """共有ツリーでの実行を促さない（LOOP.md ⓪）。"""
        theme = self._adapter_theme()
        block = actions.command_block(theme, TODAY, promote=False)
        self.assertTrue(
            block["script"].startswith("git worktree add "),
            f"1行目が worktree の作成になっていない: {block['script'].splitlines()[0]}",
        )

    def test_promote_is_offered_only_for_adapter_themes(self):
        for theme in self.themes:
            block = actions.command_block(theme, TODAY, promote=True)
            if theme["update_mode"] == "adapter":
                self.assertIsNotNone(block, f"{theme['key']} は公開まで進められるはず")
                self.assertIn("--promote", block["script"])
            else:
                self.assertIsNone(block, f"{theme['key']} に --promote を出してはいけない")

    def test_collect_only_command_has_no_promote(self):
        theme = self._adapter_theme()
        self.assertNotIn("--promote", actions.command_block(theme, TODAY, promote=False)["script"])

    def test_backup_destination_matches_the_canonical_location(self):
        theme = self._adapter_theme()
        self.assertIn(f"--backup-dest {collect.backup_root()}", actions.command_block(theme, TODAY, promote=False)["script"])

    def test_next_action_returns_at_most_one(self):
        """予定が何件あっても、示すのは1件だけ。"""
        data = build_data()
        action = data["next"]
        if action is None:
            self.skipTest("この日に予定が無い")
        self.assertIsInstance(action["title"], str)
        self.assertLessEqual(len(action["blocks"]), 2, "収集だけ / 公開まで の2つを超えている")

    def test_overdue_theme_is_chosen_first(self):
        """期限超過があれば、今日明日の予定より先に出す。"""
        future = max(t["collect_at"] for t in self.themes if t["collect_at"]) + dt.timedelta(days=1)
        data = build_data(future)
        action = data["next"]
        self.assertIsNotNone(action, "全テーマ超過なのに次の一手が出ていない")
        self.assertEqual(action["kind"], "refresh")
        self.assertIn("過ぎています", action["why"])

    def test_same_day_collect_and_refresh_are_one_item(self):
        """収集と公開更新が同じ日なら1件にまとめる（--promote は収集も行うため）。"""
        items = actions.due_items(self.themes, TODAY, within=60)
        seen = set()
        for item in items:
            key = (item["theme"]["key"], item["date"])
            self.assertNotIn(key, seen, f"{item['theme']['key']} の {item['date']} が2行に割れている")
            seen.add(key)

    def test_pending_measurements_skip_today_and_old_posts(self):
        """当日は測る時期ではなく、8日以上前は追いかけない。"""
        posts = [
            {"date": TODAY, "own_views_status": "missing"},
            {"date": TODAY - dt.timedelta(days=2), "own_views_status": "provisional"},
            {"date": TODAY - dt.timedelta(days=2), "own_views_status": "measured"},
            {"date": TODAY - dt.timedelta(days=30), "own_views_status": "missing"},
        ]
        pending = actions.pending_measurements(posts, TODAY)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["own_views_status"], "provisional")

    def test_readiness_flags_the_shared_worktree(self):
        """共有ツリーで作ったときは「作業用コピー: 未作成」になること。"""
        main = actions.main_worktree()
        if main is None:
            self.skipTest("git の情報が読めない")
        checks = actions.readiness(None, root=main)
        worktree_check = next(c for c in checks if c["name"].startswith("作業用コピー"))
        self.assertIs(worktree_check["ok"], False)


class PostBreakdownTests(unittest.TestCase):
    """X投稿の型別まとめ。少ない実測を根拠に見せないことを固定する。"""

    def _post(self, **kwargs):
        base = {
            "date": TODAY,
            "kind": "リプライ",
            "own_views": 100,
            "own_views_status": "measured",
            "parent_views": 10_000,
            "has_url": False,
        }
        base.update(kwargs)
        return base

    def test_group_with_few_measurements_is_marked_reference_only(self):
        axes = actions.post_breakdown([self._post(), self._post()], TODAY)
        for axis in axes:
            for row in axis["rows"]:
                self.assertTrue(row["reference_only"], f'{row["group"]} が参考値になっていない')

    def test_three_measurements_are_enough_to_be_a_real_number(self):
        axes = actions.post_breakdown([self._post() for _ in range(3)], TODAY)
        reply = next(r for r in axes[2]["rows"] if r["group"] == "リプライ")
        self.assertFalse(reply["reference_only"])
        self.assertEqual(reply["measured"], 3)

    def test_provisional_views_are_excluded_from_the_numbers(self):
        posts = [self._post(), self._post(own_views_status="provisional", own_views=9999)]
        axes = actions.post_breakdown(posts, TODAY)
        reply = next(r for r in axes[2]["rows"] if r["group"] == "リプライ")
        self.assertEqual(reply["posts"], 2)
        self.assertEqual(reply["measured"], 1, "暫定値が集計に入っている")
        self.assertEqual(reply["views_max"], 100)

    def test_reach_and_views_are_both_reported(self):
        """到達率だけ見て「良い」と判断できないよう、必ず両方を返す。"""
        axes = actions.post_breakdown([self._post(own_views=5, parent_views=100) for _ in range(3)], TODAY)
        row = axes[0]["rows"][0]
        self.assertEqual(row["reach_median"], 5.0)
        self.assertEqual(row["views_median"], 5)

    def test_parent_bands_are_bucketed_by_size(self):
        self.assertEqual(actions.parent_band(None), "記録なし")
        self.assertEqual(actions.parent_band(999), "〜1千")
        self.assertEqual(actions.parent_band(1_000), "1千〜1万")
        self.assertEqual(actions.parent_band(50_000), "1万〜10万")
        self.assertEqual(actions.parent_band(2_000_000), "10万〜")

    def test_old_posts_are_out_of_scope(self):
        old = self._post(date=TODAY - dt.timedelta(days=90))
        axes = actions.post_breakdown([old], TODAY, days=60)
        self.assertEqual(sum(len(axis["rows"]) for axis in axes), 0)


class AnomalyTests(unittest.TestCase):
    """気になる変化。多く出しすぎると読まれなくなるので、鳴る条件を固定する。"""

    def _data(self, **overrides):
        data = {
            "today": TODAY,
            "themes": [],
            "x_posts": [],
            "data_updates": [],
            "live_cache": {},
        }
        data.update(overrides)
        return data

    def _update(self, **kwargs):
        base = {
            "theme": "takaichi",
            "date": TODAY,
            "raw": 100,
            "duplicates": 0,
            "new": 100,
            "opinions": 80,
            "errors": 0,
            "status": "validated",
            "checks_ok": True,
            "next_collect_at": None,
            "minutes": 20,
        }
        base.update(kwargs)
        return base

    def test_opinions_halving_is_reported(self):
        found = actions.anomalies(
            self._data(
                data_updates=[
                    self._update(opinions=30),
                    self._update(date=TODAY - dt.timedelta(days=7), opinions=100),
                ]
            )
        )
        self.assertTrue(any("半分以下" in item["title"] for item in found))

    def test_small_drop_is_not_reported(self):
        found = actions.anomalies(
            self._data(
                data_updates=[
                    self._update(opinions=80),
                    self._update(date=TODAY - dt.timedelta(days=7), opinions=100),
                ]
            )
        )
        self.assertFalse(any("半分以下" in item["title"] for item in found))

    def test_two_empty_runs_in_a_row_are_reported(self):
        found = actions.anomalies(
            self._data(
                data_updates=[
                    self._update(new=0),
                    self._update(date=TODAY - dt.timedelta(days=7), new=0),
                ]
            )
        )
        self.assertTrue(any("新規0件が2回" in item["title"] for item in found))

    def test_one_empty_run_is_not_reported(self):
        found = actions.anomalies(
            self._data(
                data_updates=[
                    self._update(new=0),
                    self._update(date=TODAY - dt.timedelta(days=7), new=50),
                ]
            )
        )
        self.assertFalse(any("新規0件" in item["title"] for item in found))

    def test_repeated_fetch_failures_are_reported(self):
        found = actions.anomalies(
            self._data(live_cache={"ga4": {"consecutive_failures": 3, "last_error": "認証が失効"}})
        )
        self.assertTrue(any("3 回続けて失敗" in item["title"] for item in found))

    def test_single_fetch_failure_is_not_reported(self):
        found = actions.anomalies(
            self._data(live_cache={"ga4": {"consecutive_failures": 1, "last_error": "一時的な失敗"}})
        )
        self.assertFalse(any("失敗" in item["title"] for item in found))

    def test_page_newer_than_ledger_is_not_an_anomaly(self):
        """共有パーツの変更で全ページが一斉に変わるのは通常の運用。ここで鳴らさない。"""
        theme = next(t for t in collect.collect_themes(TODAY) if t["html"] and t["updated_at"])
        found = actions.anomalies(self._data(themes=[dict(theme, updated_at=dt.date(2026, 1, 1))]))
        self.assertFalse(
            any("ずれています" in item["title"] or "変わっていません" in item["title"] for item in found),
            "ページのほうが新しいだけで警告が出ている",
        )

    def test_ledger_ahead_of_the_page_is_an_anomaly(self):
        """台帳だけ進んでページが変わっていないのは、公開し忘れの疑い。"""
        theme = next(t for t in collect.collect_themes(TODAY) if t["html"] and t["updated_at"])
        found = actions.anomalies(self._data(themes=[dict(theme, updated_at=dt.date(2027, 1, 1))]))
        self.assertTrue(any("変わっていません" in item["title"] for item in found))


class TaskFieldTests(unittest.TestCase):
    """TASK_BOARD.md の任意欄。未記入でも従来どおり動くこと。"""

    @classmethod
    def setUpClass(cls):
        cls.tasks = collect.collect_tasks()

    def test_every_task_has_all_fields_even_when_blank(self):
        for task in self.tasks:
            for field in collect.TASK_FIELDS.values():
                self.assertIn(field, task, f'課題{task["id"]} に {field} が無い')

    def test_status_is_still_read(self):
        self.assertTrue(all(task["status"] for task in self.tasks), "状態欄が読めていない課題がある")

    def test_optional_fields_are_read_when_present(self):
        filled = [task for task in self.tasks if task["next_step"]]
        self.assertTrue(filled, "任意欄を書いた課題が1件も読めていない")
        waiting = [task for task in self.tasks if task["waiting_on"]]
        self.assertTrue(waiting, "判断待ち欄が読めていない")


class LiveCacheTests(unittest.TestCase):
    """実測値キャッシュ。失敗が前回の正常値を消さないことを固定する。"""

    NOW = dt.datetime(2026, 8, 10, 9, 0)
    LATER = dt.datetime(2026, 8, 12, 9, 0)

    def test_success_records_both_timestamps(self):
        entry = collect.merge_live_result(None, {"activeUsers": 120}, "", self.NOW)
        self.assertEqual(entry["value"], {"activeUsers": 120})
        self.assertEqual(entry["last_success_at"], "2026-08-10T09:00:00")
        self.assertEqual(entry["last_attempt_at"], "2026-08-10T09:00:00")
        self.assertEqual(entry["consecutive_failures"], 0)

    def test_failure_keeps_the_previous_good_value(self):
        good = collect.merge_live_result(None, {"activeUsers": 120}, "", self.NOW)
        failed = collect.merge_live_result(good, None, "認証が失効しています", self.LATER)
        self.assertEqual(failed["value"], {"activeUsers": 120}, "失敗で前回の数字が消えた")
        self.assertEqual(failed["last_success_at"], "2026-08-10T09:00:00", "成功日時が上書きされた")
        self.assertEqual(failed["last_attempt_at"], "2026-08-12T09:00:00")
        self.assertEqual(failed["last_error"], "認証が失効しています")

    def test_consecutive_failures_accumulate_and_reset(self):
        entry = collect.merge_live_result(None, None, "1回目", self.NOW)
        entry = collect.merge_live_result(entry, None, "2回目", self.LATER)
        self.assertEqual(entry["consecutive_failures"], 2)
        entry = collect.merge_live_result(entry, {"ok": 1}, "", self.LATER)
        self.assertEqual(entry["consecutive_failures"], 0)
        self.assertEqual(entry["last_error"], "")

    def test_cache_lives_outside_git(self):
        relative = collect.LIVE_CACHE.relative_to(ROOT)
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(relative)], cwd=ROOT, capture_output=True
        )
        self.assertEqual(result.returncode, 0, f"{relative} が .gitignore に入っていない")

    def test_broken_cache_file_is_treated_as_empty(self):
        original = collect.LIVE_CACHE
        try:
            collect.LIVE_CACHE = ROOT / "tests" / "__nonexistent_cache__.json"
            self.assertEqual(collect.read_live_cache(), {})
        finally:
            collect.LIVE_CACHE = original


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
