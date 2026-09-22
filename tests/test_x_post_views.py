"""X投稿の表示回数計測補助ツールの検査。"""

from unittest import mock
import json
import io
import datetime as dt
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import x_post_views  # noqa: E402


TABLE_ID = "2086768939602952690"
FOLLOW_ID = "2086282110659375202"
MEASURED_ID = "2086607662402457842"
PROVISIONAL_ID = "2086021725540778491"

SAMPLE = f"""## リプライ実績 2026-08-10

| # | リプライ先 | テーマ | タイプ | 元投稿views | 自リプライ表示 | 元投稿の返信数 | 元投稿からの経過 |
|---|---|---|---|---|---|---|---|
| 1 | @measured（既存値） | A | URLなし | 100 | **12**（計測済み） | 1 | 約1時間 |
| 2 | @missing（未計測） | B | URLなし | 200 | 未計測（投稿直後） | 0 | 約2時間 |
| 3 | @provisional（暫定値） | C | URLなし | 300 | 4（投稿7分後） | 0 | 約3時間 |

自リプライURL: 1 = https://x.com/sns_hannou_ma/status/{MEASURED_ID} ／ 2 = https://x.com/sns_hannou_ma/status/{TABLE_ID} ／ 3 = https://x.com/sns_hannou_ma/status/{PROVISIONAL_ID}

### 会話フォロー 2026-08-09

返信先: https://x.com/example/status/1

自リプライURL: https://x.com/sns_hannou_ma/status/{FOLLOW_ID}

投稿文:「会話の続き」

## 論点ポスト実績 2026-08-10

テーマ: テスト
投稿文:「問い」
投稿URL: https://x.com/sns_hannou_ma/status/{MEASURED_ID}
表示回数: **9**（計測済み）
"""


class XPostViewsTests(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime(2026, 8, 11, 21, 0, tzinfo=x_post_views.JST)

    def test_post_time_comes_from_snowflake_id(self):
        posted = x_post_views.post_datetime(TABLE_ID)
        self.assertEqual(posted.strftime("%Y-%m-%d %H:%M"), "2026-08-10 19:57")

    def test_lists_only_missing_values(self):
        pending = x_post_views.find_pending(SAMPLE, self.now)
        ids = {item.status_id for item in pending}
        self.assertEqual(ids, {TABLE_ID, FOLLOW_ID})
        self.assertNotIn(MEASURED_ID, ids)
        self.assertNotIn(PROVISIONAL_ID, ids, "数値のある暫定値も自動上書きしない")

    def test_timing_uses_snowflake_age(self):
        pending = {item.status_id: item for item in x_post_views.find_pending(SAMPLE, self.now)}
        self.assertEqual(pending[TABLE_ID].timing, "due")
        self.assertEqual(pending[FOLLOW_ID].timing, "overdue")

    def test_follow_heading_with_a_parenthesised_suffix_is_detected(self):
        """見出しの「（投稿済み）」で会話フォローが検出から漏れていた（課題76）。"""
        sample = f"""## リプライ実績 2026-08-10

### 会話フォロー 2026-08-09（投稿済み）

返信先: https://x.com/example/status/1

自リプライURL: https://x.com/sns_hannou_ma/status/{FOLLOW_ID}

投稿文:「会話の続き」
"""
        pending = x_post_views.find_pending(sample, self.now)
        self.assertEqual({item.status_id for item in pending}, {FOLLOW_ID})
        self.assertEqual(pending[0].kind, "会話フォロー")

    def test_follow_block_url_is_not_taken_as_a_table_row(self):
        """節の中の「### 会話フォロー」の自リプライURLを、上の表の行として数えない（課題76の続き）。

        数えると、計測済みの会話フォローが「返信先の表の行が未計測」として一覧に出て、
        apply で会話フォローの表示回数が返信先の表へ書き込まれる（2026-09-22に発覚）。
        """
        sample = f"""## リプライ実績 2026-08-10

| # | リプライ先 | テーマ | タイプ | 元投稿views | 自リプライ表示 | 元投稿の返信数 | 元投稿からの経過 |
|---|---|---|---|---|---|---|---|
| 1 | @parent（元の返信先） | A | URLなし | 100 | 未計測（投稿直後） | 1 | 1時間 |

### 会話フォロー 2026-08-10（投稿済み）

自リプライURL: https://x.com/sns_hannou_ma/status/{FOLLOW_ID}

表示回数: **19**（計測済み）
"""
        self.assertEqual(x_post_views.find_pending(sample, self.now), [])
        # 計測済みの会話フォローへの上書きは拒否され、表の行にも書き込まれない
        with self.assertRaises(ValueError):
            x_post_views.apply_measurements(sample, {FOLLOW_ID: 21}, self.now)

    def test_url_post_and_quote_rt_sections_are_listed(self):
        """URL付きの通常ポスト・流入投稿・引用RTも計測待ちに出る（課題67）。"""
        sample = f"""## 通常ポスト実績 2026-08-10（URL付き流入投稿・今週1本目）

投稿URL: https://x.com/sns_hannou_ma/status/{TABLE_ID}（投稿）

リンク先: https://sns-reaction-map.jp/example.html?utm_source=x

表示回数: 未計測（投稿直後）

## 引用RT実績 2026-08-09（昼枠）

投稿URL: https://x.com/sns_hannou_ma/status/{FOLLOW_ID}（投稿）

引用元: https://x.com/example/status/1

表示回数: 未計測（投稿直後）
"""
        pending = {item.status_id: item.kind for item in x_post_views.find_pending(sample, self.now)}
        self.assertEqual(pending, {TABLE_ID: "通常ポスト", FOLLOW_ID: "引用RT"})
        updated = x_post_views.apply_measurements(sample, {TABLE_ID: 31, FOLLOW_ID: 44}, self.now)
        self.assertIn("表示回数: **31**", updated)
        self.assertIn("表示回数: **44**", updated)
        self.assertEqual(x_post_views.find_pending(updated, self.now), [])

    def test_old_url_post_without_view_line_is_not_listed(self):
        """「表示回数:」行の無い旧形式の通常ポストは測り終えているので出さない（課題67）。"""
        sample = f"""## 通常ポスト実績 2026-08-10

投稿URL: https://x.com/sns_hannou_ma/status/{TABLE_ID}

計測: 185表示（2026-08-11）
"""
        self.assertEqual(x_post_views.find_pending(sample, self.now), [])

    def test_unknown_result_heading_with_unmeasured_post_is_reported(self):
        """知らない種類の「○○実績」見出しに未計測の投稿があれば、黙って落とさず報告する（課題67）。"""
        sample = f"""## 新しい形式実績 2026-08-10

投稿URL: https://x.com/sns_hannou_ma/status/{TABLE_ID}

表示回数: 未計測（投稿直後）
"""
        self.assertEqual(x_post_views.find_pending(sample, self.now), [])
        self.assertEqual(x_post_views.unrecognized_sections(sample), ["## 新しい形式実績 2026-08-10"])
        self.assertEqual(x_post_views.unrecognized_sections(SAMPLE), [])

    def test_follow_without_own_url_is_not_listed(self):
        """「（送信なし）」の節は自リプライURLが無いので計測対象にしない。"""
        sample = """## リプライ実績 2026-08-10

### 会話フォロー 2026-08-09（送信なし）

先方のコメント: https://x.com/example/status/1

判断: 返信しない。
"""
        self.assertEqual(x_post_views.find_pending(sample, self.now), [])

    def test_apply_preserves_headers_and_existing_values(self):
        updated = x_post_views.apply_measurements(
            SAMPLE,
            {TABLE_ID: 37, FOLLOW_ID: 51},
            self.now,
        )
        self.assertIn(
            "| # | リプライ先 | テーマ | タイプ | 元投稿views | 自リプライ表示 | 元投稿の返信数 | 元投稿からの経過 |",
            updated,
        )
        self.assertIn("@measured（既存値） | A | URLなし | 100 | **12**（計測済み）", updated)
        self.assertIn("@provisional（暫定値） | C | URLなし | 300 | 4（投稿7分後）", updated)
        self.assertIn("**37**（2026-08-11 21:00計測・投稿から約25時間後）", updated)
        self.assertIn("表示回数: **51**（2026-08-11 21:00計測・投稿から約57時間後）", updated)

    def test_refuses_to_overwrite_measured_value(self):
        with self.assertRaisesRegex(ValueError, "上書き禁止"):
            x_post_views.apply_measurements(SAMPLE, {MEASURED_ID: 999}, self.now)

    def test_refuses_whole_write_when_any_id_is_not_pending(self):
        with self.assertRaises(ValueError):
            x_post_views.apply_measurements(
                SAMPLE,
                {TABLE_ID: 37, MEASURED_ID: 999},
                self.now,
            )


NEW_FORMAT_ID_1 = "2093124499726299494"
NEW_FORMAT_ID_2 = "2093204337073996089"
NEW_FORMAT_ID_3 = "2093263576341655863"

SAMPLE_NEW_FORMAT = f"""## リプライ実績 2026-08-24

| # | リプライ先 | テーマ | タイプ | 元投稿views | 自リプライ表示 | 元投稿の返信数 | 元投稿からの経過 |
|---|---|---|---|---|---|---|---|
| 1 | @a（未計測） | A | URLなし | 100 | 未計測（投稿直後） | 0 | 約1時間 |
| 2 | @b（未計測） | B | URLなし | 200 | 未計測（投稿直後） | 0 | 約2時間 |
| 3 | @c（未計測） | C | URLなし | 300 | 未計測（投稿直後） | 0 | 約3時間 |

自リプライURL: https://x.com/sns_hannou_ma/status/{NEW_FORMAT_ID_1}（08:52投稿）
自リプライURL 2: https://x.com/sns_hannou_ma/status/{NEW_FORMAT_ID_2}（14:09投稿）
自リプライURL 3: https://x.com/sns_hannou_ma/status/{NEW_FORMAT_ID_3}（18:05投稿）
"""


class NewUrlFormatTest(unittest.TestCase):
    """2026-08-24以降の1行1件形式（自リプライURL: / 自リプライURL N:）の検出。"""

    def setUp(self):
        self.now = dt.datetime(2026, 8, 30, 21, 0, tzinfo=x_post_views.JST)

    def test_detects_all_rows_in_new_format(self):
        pending = x_post_views.find_pending(SAMPLE_NEW_FORMAT, self.now)
        ids = {item.status_id for item in pending}
        self.assertEqual(ids, {NEW_FORMAT_ID_1, NEW_FORMAT_ID_2, NEW_FORMAT_ID_3})

    def test_row_numbers_match_table_rows(self):
        pending = {item.status_id: item for item in x_post_views.find_pending(SAMPLE_NEW_FORMAT, self.now)}
        self.assertEqual(pending[NEW_FORMAT_ID_1].row_number, "1")
        self.assertEqual(pending[NEW_FORMAT_ID_2].row_number, "2")
        self.assertEqual(pending[NEW_FORMAT_ID_3].row_number, "3")

    def test_apply_measurements_writes_into_correct_row(self):
        updated = x_post_views.apply_measurements(
            SAMPLE_NEW_FORMAT,
            {NEW_FORMAT_ID_2: 42},
            self.now,
        )
        self.assertIn("@b（未計測） | B | URLなし | 200 | **42**", updated)
        self.assertIn("@a（未計測） | A | URLなし | 100 | 未計測（投稿直後）", updated)


if __name__ == "__main__":
    unittest.main()


class EngagementRecordingTest(unittest.TestCase):
    """いいね・リポストを列を増やさず注記に残せること。"""

    def test_view_arg_accepts_optional_likes_and_reposts(self):
        parsed = x_post_views._parse_views(["111=642,6,2", "222=59"])
        self.assertEqual(parsed["111"], x_post_views.Metric(642, 6, 2))
        self.assertEqual(parsed["222"], x_post_views.Metric(59, None, None))

    def test_view_arg_rejects_too_many_values(self):
        with self.assertRaises(ValueError):
            x_post_views._parse_views(["111=1,2,3,4"])

    def test_measurement_text_appends_engagement(self):
        posted = dt.datetime(2026, 8, 10, 19, 57, tzinfo=x_post_views.JST)
        measured = dt.datetime(2026, 8, 11, 12, 0, tzinfo=x_post_views.JST)
        text = x_post_views._measurement_text(642, measured, posted, 6, 2)
        self.assertIn("**642**", text)
        self.assertIn("いいね6", text)
        self.assertIn("リポスト2", text)

    def test_measurement_text_omits_engagement_when_absent(self):
        posted = dt.datetime(2026, 8, 10, 19, 57, tzinfo=x_post_views.JST)
        measured = dt.datetime(2026, 8, 11, 12, 0, tzinfo=x_post_views.JST)
        text = x_post_views._measurement_text(642, measured, posted)
        self.assertNotIn("いいね", text)
        self.assertNotIn("リポスト", text)

    def test_negative_engagement_is_rejected(self):
        with self.assertRaises(ValueError):
            x_post_views._parse_views(["111=642,-1"])


class ReplyListingTest(unittest.TestCase):
    """自投稿に付いた返信の検出。ネットワークには出ない。"""

    def test_all_status_ids_are_unique_and_newest_first(self):
        text = (
            "1 = https://x.com/sns_hannou_ma/status/100\n"
            "2 = https://x.com/sns_hannou_ma/status/300\n"
            "再掲 https://x.com/sns_hannou_ma/status/100\n"
            "3 = https://x.com/sns_hannou_ma/status/200\n"
        )
        self.assertEqual(x_post_views._all_status_ids(text), ["300", "200", "100"])

    def test_fetch_returns_none_on_unexpected_payload(self):
        with mock.patch.object(x_post_views.urllib.request, "urlopen") as opener:
            opener.return_value.__enter__.return_value = io.BytesIO(b'{"error":"x"}')
            self.assertIsNone(x_post_views.fetch_public_counts("123"))

    def test_fetch_maps_public_fields(self):
        payload = json.dumps(
            {"id_str": "123", "conversation_count": 2, "favorite_count": 5, "text": "本文"}
        ).encode()
        with mock.patch.object(x_post_views.urllib.request, "urlopen") as opener:
            opener.return_value.__enter__.return_value = io.BytesIO(payload)
            got = x_post_views.fetch_public_counts("123")
        self.assertEqual(got["replies"], 2)
        self.assertEqual(got["likes"], 5)
        self.assertEqual(got["url"], "https://x.com/sns_hannou_ma/status/123")
