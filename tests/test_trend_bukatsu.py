"""部活動の地域移行の「意見の推移」（scripts/build_trend_section.py の bukatsu-chiiki 設定）の検査。

正典を使わず、合成データで挙動を固定する（公開CIでも回る）。
実データでの照合は tests/test_trend_provenance.py（非公開正典を読むので公開CIでは回さない）にある。

見たいことは3つ。
- 集計のしかたが変わる前の回を、並べない（立場は賛否の判定基準を見直した2026-09-15から、論点は検索語を増やした2026-07-23から）。
- 分類に使うAIを切り替えた回は、注意書きに出る（記録が無いまま公開しない）。
- 理由タブ・年表の縦線は、このテーマには出ない。
"""

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import build_trend_section as trend  # noqa: E402
from scripts.refresh_adapters import trend_support  # noqa: E402

SLUG = "bukatsu-chiiki"
BASE = trend._theme_base(SLUG)
STANCES = BASE["stance_labels"]
ISSUES = BASE["issue_labels"]
FRAME = '<style></style><section class="update-dashboard"><!-- TREND_CARD_START --><!-- TREND_CARD_END --></section>'


def row(day: str, stance: str, issue: str, tweet_id: str = "1") -> dict:
    return {
        "tweet_id": tweet_id,
        "fetched_at": f"{day}T03:00:00.000Z",  # 日本時間の昼12時
        "classification": {"is_relevant": True, "is_opinion": True, "stance": stance, "main_issue": issue},
    }


def rounds(days: list[str], per_round: int = 6) -> list[dict]:
    """各回、立場・論点を順に割り当てた投稿を作る（割合そのものは見ない）。"""
    rows = []
    for day in days:
        for i in range(per_round):
            rows.append(row(day, STANCES[i % len(STANCES)], ISSUES[i % len(ISSUES)], tweet_id=f"{day}-{i}"))
    return rows


def write(rows: list[dict], directory: Path) -> Path:
    path = directory / "classified.json"
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return path


DAYS = [
    "2026-06-27", "2026-07-12", "2026-07-23", "2026-09-02", "2026-09-15", "2026-09-22", "2026-10-01",
]


class BaseDefinitionTest(unittest.TestCase):
    def test_labels_come_from_the_taxonomy_and_issue_other_is_left_out(self) -> None:
        self.assertEqual(STANCES, ["移行支持", "条件付き・改善要求", "慎重・反対", "中立・情報"])
        self.assertEqual(len(ISSUES), 6)
        self.assertNotIn("その他", ISSUES)
        self.assertEqual(BASE["html"], "docs/bukatsu-chiiki-reaction-map.html")
        self.assertTrue(BASE["use_relevance_filter"])

    def test_short_labels_match_label_counts(self) -> None:
        theme = trend.TREND_THEMES[SLUG]
        self.assertEqual(len(theme["short_labels"]["stance"]), len(STANCES))
        self.assertEqual(len(theme["short_labels"]["issue"]), len(ISSUES))
        self.assertLessEqual(len(ISSUES), len(trend.KINDS["issue"]["colors"]))

    def test_page_url_points_at_the_theme_page(self) -> None:
        self.assertEqual(trend.page_url(SLUG), "https://sns-reaction-map.jp/bukatsu-chiiki-reaction-map.html")


class SeriesStartTest(unittest.TestCase):
    def test_each_axis_starts_at_its_own_date(self) -> None:
        self.assertEqual(trend.series_start(SLUG, "stance"), "2026-09-15")
        self.assertEqual(trend.series_start(SLUG, "issue"), "2026-07-23")

    def test_rounds_before_the_start_are_not_lined_up(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write(rounds(DAYS), Path(tmp))
            stance = [item["date"] for item in trend.rounds_for(SLUG, path, "stance")]
            issue = [item["date"] for item in trend.rounds_for(SLUG, path, "issue")]
        self.assertEqual(stance, ["2026-09-15", "2026-09-22", "2026-10-01"])
        self.assertEqual(issue, ["2026-07-23", "2026-09-02", "2026-09-15", "2026-09-22", "2026-10-01"])

    def test_the_start_date_itself_is_included(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write(rounds(["2026-09-14", "2026-09-15", "2026-09-22"]), Path(tmp))
            self.assertEqual(
                [item["date"] for item in trend.rounds_for(SLUG, path, "stance")],
                ["2026-09-15", "2026-09-22"],
            )

    def test_load_rounds_without_since_keeps_every_round(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write(rounds(DAYS), Path(tmp))
            self.assertEqual(len(trend.load_rounds(path, BASE, "stance")), len(DAYS))

    def test_other_theme_has_no_start_and_keeps_every_round(self) -> None:
        self.assertIsNone(trend.series_start("consumption-tax-cut", "stance"))


class ModelBreakNotesTest(unittest.TestCase):
    series = [{"date": "2026-09-22"}, {"date": "2026-10-01"}]

    def test_break_inside_the_series_is_noted(self) -> None:
        notes = trend.model_break_notes(SLUG, self.series)
        self.assertEqual(len(notes), 1)
        self.assertIn("2026年10月1日の回から、分類に使うAIを切り替えました", notes[0])

    def test_break_on_the_first_round_is_not_noted(self) -> None:
        # 最初の回より前との比較は無いので、注意書きは要らない
        self.assertEqual(trend.model_break_notes(SLUG, [{"date": "2026-10-01"}, {"date": "2026-10-08"}]), [])

    def test_break_after_the_latest_round_is_not_noted(self) -> None:
        self.assertEqual(trend.model_break_notes(SLUG, [{"date": "2026-09-15"}, {"date": "2026-09-22"}]), [])

    def test_theme_without_breaks_gets_no_note(self) -> None:
        self.assertEqual(trend.model_break_notes("consumption-tax-cut", self.series), [])


class RenderTest(unittest.TestCase):
    def render(self, rows: list[dict]) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            return trend.render_for(SLUG, FRAME, write(rows, Path(tmp)))

    def test_section_has_two_tabs_and_no_reason_tab(self) -> None:
        html = self.render(rounds(DAYS))
        self.assertEqual(html.count('data-trend-tab="'), 2)
        self.assertNotIn('data-trend-tab="reason"', html)
        self.assertNotIn("反対・慎重の理由", html)
        self.assertEqual(html.count('data-trend-panel="'), 2)

    def test_tables_list_only_the_rounds_after_each_start(self) -> None:
        html = self.render(rounds(DAYS))
        stance = re.findall(r'id="bukatsu-chiiki-trend-panel-stance-row-([\d-]+)"', html)
        issue = re.findall(r'id="bukatsu-chiiki-trend-panel-issue-row-([\d-]+)"', html)
        self.assertEqual(stance, ["2026-09-15", "2026-09-22", "2026-10-01"])
        self.assertEqual(issue, ["2026-07-23", "2026-09-02", "2026-09-15", "2026-09-22", "2026-10-01"])

    def test_notes_explain_why_earlier_rounds_are_left_out(self) -> None:
        html = self.render(rounds(DAYS))
        stance_panel = html.split('id="bukatsu-chiiki-trend-panel-issue"')[0]
        issue_panel = html.split('id="bukatsu-chiiki-trend-panel-issue"')[1]
        self.assertIn("賛否を判定する基準を見直しました", stance_panel)
        self.assertIn("最初の回（2026年9月15日）から並べています", stance_panel)
        self.assertIn("収集に使う検索語を増やしました", issue_panel)
        self.assertNotIn("賛否を判定する基準", issue_panel)
        for panel in (stance_panel, issue_panel):
            self.assertIn("2026年10月1日の回から、分類に使うAIを切り替えました", panel)

    def test_headings_and_theme_name(self) -> None:
        html = self.render(rounds(DAYS))
        self.assertIn("部活動の地域移行への賛否の割合は変わった？", html)
        self.assertIn("部活動の地域移行で語られる論点は変わった？", html)
        self.assertNotIn("消費税", html)
        self.assertNotIn("減税", html)

    def test_no_event_lines_for_this_theme(self) -> None:
        html = self.render(rounds(DAYS))
        self.assertNotIn('<li class="trend-event"', html)
        self.assertNotIn('<div class="trend-events">', html)
        self.assertIn('"events":[]', html)  # グラフに渡す縦線も空

    def test_two_runs_give_the_same_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write(rounds(DAYS), Path(tmp))
            first = trend.render_for(SLUG, FRAME, path)
            self.assertEqual(trend.render_for(SLUG, first, path), first)

    def test_needs_two_rounds_on_each_axis(self) -> None:
        # 立場は2026-09-15以降が1回しか無い → 並べられないので止める（黙って別の期間を出さない）
        with tempfile.TemporaryDirectory() as tmp:
            path = write(rounds(["2026-07-23", "2026-09-02", "2026-10-01"]), Path(tmp))
            with self.assertRaises(ValueError):
                trend.render_for(SLUG, FRAME, path)


class ModelBreakGuardTest(unittest.TestCase):
    def test_changed_model_without_a_record_stops(self) -> None:
        with self.assertRaises(ValueError) as caught:
            trend_support.check_model_break(ROOT, SLUG, "2026-10-08", "kimi-k2.7-code", "next-model")
        self.assertIn("model_breaks", str(caught.exception))
        self.assertIn("2026-10-08", str(caught.exception))

    def test_changed_model_with_a_record_passes(self) -> None:
        trend_support.check_model_break(ROOT, SLUG, "2026-10-01", "kimi-k2.6", "kimi-k2.7-code")

    def test_same_model_passes(self) -> None:
        trend_support.check_model_break(ROOT, SLUG, "2026-10-08", "kimi-k2.7-code", "kimi-k2.7-code")

    def test_unknown_model_does_not_stop_the_update(self) -> None:
        # 古い回は記録が無い。分かる範囲だけを見る（止めない）
        trend_support.check_model_break(ROOT, SLUG, "2026-10-08", None, "kimi-k2.7-code")
        trend_support.check_model_break(ROOT, SLUG, "2026-10-08", "kimi-k2.6", None)


if __name__ == "__main__":
    unittest.main()
