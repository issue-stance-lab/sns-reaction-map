"""部活動の賛否の数え直し（scripts/rejudge_bukatsu_stance.py）の検査。

分類器は呼ばない（有料で時間がかかるため）。対象の選び方、新旧の比べ方、正典を書き換えるときの安全装置を、
合成データで固定する。公開CIでも回る（非公開データを読まない）。
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import rejudge_bukatsu_stance as rejudge  # noqa: E402

CUTOFF = "2026-09-15"
SUPPORT, COND, CAUTION, NEUTRAL = "移行支持", "条件付き・改善要求", "慎重・反対", "中立・情報"


def row(day: str, tweet_id: str, stance: str, *, relevant: bool = True, opinion: bool = True) -> dict:
    return {
        "tweet_id": tweet_id,
        "fetched_at": f"{day}T03:00:00.000Z",  # 日本時間の昼12時
        "text": f"本文{tweet_id}",
        "classification": {
            "is_relevant": relevant, "is_opinion": opinion, "main_issue": "教員の働き方",
            "stance": stance, "confidence": 0.8,
        },
    }


ROWS = [
    row("2026-06-27", "1", CAUTION),
    row("2026-09-02", "2", SUPPORT),
    row("2026-09-02", "3", NEUTRAL, opinion=False),  # 意見でない → 対象外
    row("2026-09-02", "4", NEUTRAL, relevant=False, opinion=False),  # 無関係 → 対象外
    row("2026-09-15", "5", NEUTRAL),  # 見直し後の回 → 対象外
    row("2026-10-01", "6", COND),
]


class SelectRowsTest(unittest.TestCase):
    def test_only_opinions_before_the_cutoff(self) -> None:
        self.assertEqual([r["tweet_id"] for r in rejudge.select_rows(ROWS, CUTOFF)], ["1", "2"])

    def test_the_cutoff_day_itself_is_not_rejudged(self) -> None:
        self.assertNotIn("5", [r["tweet_id"] for r in rejudge.select_rows(ROWS, CUTOFF)])

    def test_collected_day_is_japan_time(self) -> None:
        late = row("2026-09-14", "7", SUPPORT)
        late["fetched_at"] = "2026-09-14T16:30:00.000Z"  # 日本時間では9/15 01:30 → 見直し後の回
        self.assertEqual(rejudge.collected_day(late), "2026-09-15")
        self.assertEqual(rejudge.select_rows([late], CUTOFF), [])

    def test_order_is_stable(self) -> None:
        shuffled = list(reversed(ROWS))
        self.assertEqual(
            [r["tweet_id"] for r in rejudge.select_rows(shuffled, CUTOFF)],
            [r["tweet_id"] for r in rejudge.select_rows(ROWS, CUTOFF)],
        )


class CompareTest(unittest.TestCase):
    def test_counts_by_round_and_changes(self) -> None:
        rejudged = [
            {"tweet_id": "1", "fetched_at": ROWS[0]["fetched_at"], "classification": {"stance": NEUTRAL}},
            {"tweet_id": "2", "fetched_at": ROWS[1]["fetched_at"], "classification": {"stance": SUPPORT}},
        ]
        result = rejudge.compare(ROWS, rejudged)
        self.assertEqual(result["rows"], 2)
        self.assertEqual(result["same"], 1)
        self.assertEqual(result["per_round"]["2026-06-27"]["old"], [0, 0, 1, 0])
        self.assertEqual(result["per_round"]["2026-06-27"]["new"], [0, 0, 0, 1])
        self.assertEqual(result["changes"], {f"{CAUTION}→{NEUTRAL}": 1})
        self.assertNotIn("本文", json.dumps(result, ensure_ascii=False))  # 本文は出さない


class ApplyTest(unittest.TestCase):
    """正典を書き換えるのは賛否（stance）だけ。それ以外は1文字も変えない。"""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name) / "work"
        self.dir.mkdir()
        self.canonical = Path(self.temp.name) / "canonical.json"
        self.canonical.write_text(json.dumps(ROWS, ensure_ascii=False), encoding="utf-8")
        patch = mock.patch.object(rejudge, "canonical_path", return_value=self.canonical)
        patch.start()
        self.addCleanup(patch.stop)
        plan = {"cutoff": CUTOFF, "canonical_sha256": rejudge.sha256(self.canonical)}
        (self.dir / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    def write_rejudged(self, rows: list[dict]) -> None:
        (self.dir / "rejudged.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")

    def rejudged_row(self, source: dict, stance: str) -> dict:
        new = json.loads(json.dumps(source))
        new["classification"].update({"stance": stance, "main_issue": "費用・家庭負担", "is_opinion": False, "confidence": 0.1})
        return new

    def test_only_the_stance_changes(self) -> None:
        self.write_rejudged([self.rejudged_row(ROWS[0], NEUTRAL), self.rejudged_row(ROWS[1], SUPPORT)])
        result = rejudge.apply(self.dir)
        self.assertEqual(result, {"rows": 2, "changed": 1})
        after = json.loads(self.canonical.read_text(encoding="utf-8"))
        expected = json.loads(json.dumps(ROWS))
        expected[0]["classification"]["stance"] = NEUTRAL
        self.assertEqual(after, expected)  # 論点・意見か・確信度・本文は元のまま

    def test_the_canonical_before_is_kept(self) -> None:
        self.write_rejudged([self.rejudged_row(ROWS[0], NEUTRAL)])
        rejudge.apply(self.dir)
        self.assertEqual(json.loads((self.dir / "canonical-before.json").read_text(encoding="utf-8")), ROWS)

    def test_a_second_apply_is_refused(self) -> None:
        self.write_rejudged([self.rejudged_row(ROWS[0], NEUTRAL)])
        rejudge.apply(self.dir)
        # 正典が変わったので、準備のときの指紋とも合わなくなる。どちらで止まっても、二重には適用されない。
        with self.assertRaises(ValueError):
            rejudge.apply(self.dir)

    def test_a_canonical_that_changed_after_prepare_is_refused(self) -> None:
        self.write_rejudged([self.rejudged_row(ROWS[0], NEUTRAL)])
        self.canonical.write_text(json.dumps(ROWS + [row("2026-10-08", "9", SUPPORT)], ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(ValueError):
            rejudge.apply(self.dir)

    def test_a_row_after_the_cutoff_is_refused(self) -> None:
        self.write_rejudged([self.rejudged_row(ROWS[4], SUPPORT)])  # 見直し後の回
        with self.assertRaises(ValueError):
            rejudge.apply(self.dir)
        # 検証で止まったときは、控えも書き換えも半端に残らない
        self.assertFalse((self.dir / "canonical-before.json").exists())
        self.assertEqual(json.loads(self.canonical.read_text(encoding="utf-8")), ROWS)

    def test_a_non_opinion_row_is_refused(self) -> None:
        self.write_rejudged([self.rejudged_row(ROWS[2], SUPPORT)])
        with self.assertRaises(ValueError):
            rejudge.apply(self.dir)


class MergeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.model = {"name": "m", "provider": "p", "config_source": "c"}
        patch = mock.patch.object(rejudge, "model_settings", return_value=self.model)
        patch.start()
        self.addCleanup(patch.stop)
        part = [ROWS[0], ROWS[1]]
        (self.dir / "in0.json").write_text(json.dumps(part, ensure_ascii=False), encoding="utf-8")
        (self.dir / "plan.json").write_text(json.dumps({"inputs": [{"file": "in0.json"}], "model": self.model}), encoding="utf-8")

    def write_out(self, rows: list[dict]) -> None:
        (self.dir / "out0.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")

    def test_complete_output_is_merged(self) -> None:
        self.write_out([ROWS[0], ROWS[1]])
        self.assertEqual(len(rejudge.merge(self.dir)), 2)
        self.assertTrue((self.dir / "rejudged.json").exists())

    def test_missing_rows_are_refused(self) -> None:
        self.write_out([ROWS[0]])
        with self.assertRaises(ValueError):
            rejudge.merge(self.dir)

    def test_a_refused_post_is_not_silently_adopted(self) -> None:
        refused = json.loads(json.dumps(ROWS[1]))
        refused["classification"] = {"error": "upstream_refused: x"}
        self.write_out([ROWS[0], refused])
        with self.assertRaises(ValueError):
            rejudge.merge(self.dir)

    def test_a_model_change_during_the_run_is_refused(self) -> None:
        self.write_out([ROWS[0], ROWS[1]])
        with mock.patch.object(rejudge, "model_settings", return_value={"name": "other", "provider": "p", "config_source": "c"}):
            with self.assertRaises(ValueError):
                rejudge.merge(self.dir)


if __name__ == "__main__":
    unittest.main()
