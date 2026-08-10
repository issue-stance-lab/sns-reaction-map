"""X投稿の表示回数計測補助ツールの検査。"""

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


if __name__ == "__main__":
    unittest.main()
