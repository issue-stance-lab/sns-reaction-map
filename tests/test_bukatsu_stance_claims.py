"""部活動ページの立場の内訳セクション（見出し・本文の固定の主張）が、数字と食い違ったら止まること。

見出し「支持は最多でも過半数ではない」と本文の「全体の4割には届きません」「慎重・反対と条件付きを
合わせると、支持の件数を上回ります」は固定の文。数字だけ差し替わって主張が崩れても、黙って残らないようにする。
合成データで確かめる（公開CIでも回る）。
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build_bukatsu_arena as arena  # noqa: E402
from scripts.issue_card_counts import IssueCountError  # noqa: E402

KEYS = ["移行支持", "慎重・反対", "条件付き・改善要求", "中立・情報"]


def stances(support: int, caution: int, cond: int, neutral: int) -> list[dict]:
    return [{"key": key, "count": count, "color": "#000"} for key, count in zip(KEYS, (support, caution, cond, neutral))]


def check(support: int, caution: int, cond: int, neutral: int) -> None:
    items = stances(support, caution, cond, neutral)
    arena.check_stance_claims(items, sum(int(s["count"]) for s in items))


class StanceClaimsTest(unittest.TestCase):
    def test_current_shape_passes(self) -> None:
        check(494, 259, 284, 457)  # 賛否を数え直したあとの形（支持が最多で4割未満、慎重+条件付きが上回る）

    def test_support_not_the_largest_stops(self) -> None:
        with self.assertRaises(IssueCountError) as caught:
            check(400, 259, 284, 551)
        self.assertIn("移行支持が最も多い", str(caught.exception))

    def test_support_over_four_tenths_stops(self) -> None:
        with self.assertRaises(IssueCountError) as caught:
            check(600, 259, 284, 351)
        self.assertIn("4割に届かない", str(caught.exception))

    def test_support_over_half_stops(self) -> None:
        with self.assertRaises(IssueCountError):
            check(800, 100, 100, 94)

    def test_caution_plus_conditional_not_above_support_stops(self) -> None:
        with self.assertRaises(IssueCountError) as caught:
            check(450, 100, 100, 330)
        self.assertIn("支持を上回る", str(caught.exception))

    def test_equal_to_support_stops(self) -> None:
        with self.assertRaises(IssueCountError):
            check(400, 200, 200, 200)  # 慎重+条件付き = 400 = 支持（「上回る」は成り立たない）

    def test_no_opinions_stops(self) -> None:
        with self.assertRaises(IssueCountError):
            arena.check_stance_claims(stances(0, 0, 0, 0), 0)

    def test_stance_glance_builds_when_claims_hold(self) -> None:
        html = arena.stance_glance(
            [{**item, "color": "#123456"} for item in stances(494, 259, 284, 457)], 1494)
        self.assertIn("移行支持が494件で最も多いものの", html)


if __name__ == "__main__":
    unittest.main()
