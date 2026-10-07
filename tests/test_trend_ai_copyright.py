"""生成AIと著作権の「意見の推移」（scripts/build_trend_section.py の ai-copyright 設定）の検査。

正典を使わず、合成データで挙動を固定する（公開CIでも回る）。
実データでの照合は tests/test_trend_provenance.py（非公開正典を読むので公開CIでは回さない）にある。

見たいことは次のとおり。
- 立場は「規制・推進・中立」の3つ、論点は「その他」を除く6つ。並びはページと同じ単一ソース
  （scripts/ai_copyright_taxonomy.py）から導く。潮目の定義（立場2つ）は使わない。
- 2026-07-26までの回（分類のしかたが今と違う）は並べない。起点の2026-08-03は含める。
- 色は意味に合わせる（規制＝赤、推進＝緑、中立＝灰）。ほかのテーマの色は変わらない。
- 分類に使うAIを切り替えた回は注意書きに出る。記録が無いまま公開しない。
- 更新処理（adapter）が、前回の回のモデルを保存済みの記録から読める。
"""

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import build_trend_section as trend  # noqa: E402
from scripts.refresh_adapters import ai_copyright as adapter  # noqa: E402
from scripts.refresh_adapters import trend_support  # noqa: E402

SLUG = "ai-copyright"
BASE = trend._theme_base(SLUG)
STANCES = BASE["stance_labels"]
ISSUES = BASE["issue_labels"]
FRAME = '<style></style><section class="update-dashboard"><!-- TREND_CARD_START --><!-- TREND_CARD_END --></section>'

DAYS = ["2026-07-12", "2026-07-26", "2026-08-03", "2026-09-05", "2026-09-20", "2026-09-29", "2026-10-06"]
LINED_UP = ["2026-08-03", "2026-09-05", "2026-09-20", "2026-09-29", "2026-10-06"]


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


class BaseDefinitionTest(unittest.TestCase):
    def test_labels_come_from_the_taxonomy_with_neutral_last_and_issue_other_left_out(self) -> None:
        self.assertEqual(STANCES, ["規制・制限強化支持", "推進・活用支持", "中立・情報"])
        self.assertEqual(len(ISSUES), 6)
        self.assertNotIn("その他", ISSUES)
        self.assertEqual(BASE["html"], "docs/ai-copyright-reaction-map.html")
        self.assertTrue(BASE["use_relevance_filter"])

    def test_every_label_is_a_label_the_page_and_the_vote_use(self) -> None:
        from ai_copyright_taxonomy import ISSUE_ORDER, STANCE_ORDER  # type: ignore[import-not-found]

        self.assertEqual(set(STANCES), set(STANCE_ORDER))
        self.assertTrue(set(ISSUES) <= set(ISSUE_ORDER))
        self.assertEqual(set(ISSUE_ORDER) - set(ISSUES), {"その他"})

    def test_short_labels_match_label_counts(self) -> None:
        theme = trend.TREND_THEMES[SLUG]
        self.assertEqual(len(theme["short_labels"]["stance"]), len(STANCES))
        self.assertEqual(len(theme["short_labels"]["issue"]), len(ISSUES))
        self.assertLessEqual(len(ISSUES), len(trend.KINDS["issue"]["colors"]))

    def test_page_url_points_at_the_theme_page(self) -> None:
        self.assertEqual(trend.page_url(SLUG), "https://sns-reaction-map.jp/ai-copyright-reaction-map.html")

    def test_tide_injection_is_off_so_a_standalone_run_cannot_bring_the_tide_back(self) -> None:
        import inject_tide_widget as tide  # type: ignore[import-not-found]

        entry = next(item for item in tide.THEMES if item["slug"] == SLUG)
        self.assertIsNone(entry["prev_file"])
        self.assertIsNone(entry["cur_file"])


class PaletteTest(unittest.TestCase):
    def test_stance_colors_fit_the_meaning(self) -> None:
        colors, shapes = trend.palette_for(SLUG, "stance", len(STANCES))
        spec = trend.KINDS["stance"]
        # 規制＝赤・ひし形、推進＝緑・丸、中立＝灰・三角
        self.assertEqual(colors, [spec["colors"][2], spec["colors"][0], spec["colors"][3]])
        self.assertEqual(shapes, ["diamond", "circle", "triangle"])
        self.assertEqual(len(set(colors)), 3)

    def test_issue_colors_are_the_first_six(self) -> None:
        colors, shapes = trend.palette_for(SLUG, "issue", len(ISSUES))
        self.assertEqual(colors, trend.KINDS["issue"]["colors"][:6])
        self.assertEqual(shapes, trend.KINDS["issue"]["shapes"][:6])

    def test_other_themes_keep_the_first_n_colors(self) -> None:
        colors, shapes = trend.palette_for("consumption-tax-cut", "stance", 4)
        self.assertEqual(colors, trend.KINDS["stance"]["colors"][:4])
        self.assertEqual(shapes, trend.KINDS["stance"]["shapes"][:4])

    def test_a_palette_that_does_not_match_the_label_count_stops(self) -> None:
        with self.assertRaises(ValueError):
            trend.palette_for(SLUG, "stance", 4)


class HeadlineNameTest(unittest.TestCase):
    def test_long_issue_names_are_shortened_only_inside_the_headline(self) -> None:
        self.assertEqual(trend.headline_name(SLUG, "issue", "学習データ・無断利用"), "学習データ")
        self.assertEqual(trend.headline_name(SLUG, "issue", "クリエイター保護・権利"), "クリエイター保護")
        # 指定が無い名前・立場は、そのまま
        self.assertEqual(trend.headline_name(SLUG, "issue", "法制度・規制整備"), "法制度・規制整備")
        self.assertEqual(trend.headline_name(SLUG, "stance", "規制・制限強化支持"), "規制・制限強化支持")

    def test_other_themes_are_not_changed(self) -> None:
        self.assertEqual(trend.headline_name("consumption-tax-cut", "issue", "減税の対象範囲"), "減税の対象範囲")

    def test_every_short_name_belongs_to_a_real_label_and_stays_distinct(self) -> None:
        names = trend.TREND_THEMES[SLUG]["headline_labels"]["issue"]
        self.assertTrue(set(names) <= set(ISSUES))
        shown = [trend.headline_name(SLUG, "issue", label) for label in ISSUES]
        self.assertEqual(len(set(shown)), len(ISSUES))  # 呼び名が重なって、どの論点か分からなくならない

    def test_glance_headline_uses_the_short_names_but_the_items_keep_the_full_labels(self) -> None:
        series = [
            {"date": "2026-08-03", "n": 300, "counts": {l: 0 for l in ISSUES}, "shares": {l: 0.0 for l in ISSUES}, "recent_share": None},
            {"date": "2026-10-06", "n": 300, "counts": {l: 0 for l in ISSUES}, "shares": {l: 0.0 for l in ISSUES}, "recent_share": None},
        ]
        series[0]["shares"].update({"学習データ・無断利用": 40.0, "クリエイター保護・権利": 10.0})
        series[1]["shares"].update({"学習データ・無断利用": 20.0, "クリエイター保護・権利": 30.0})
        series[0]["counts"].update({"学習データ・無断利用": 120, "クリエイター保護・権利": 30})
        series[1]["counts"].update({"学習データ・無断利用": 60, "クリエイター保護・権利": 90})
        info = trend.glance(SLUG, "issue", series, ISSUES)
        self.assertEqual({item["label"] for item in info["items"]}, {"学習データ・無断利用", "クリエイター保護・権利"})
        self.assertIn("学習データ", info["headline"])
        self.assertNotIn("学習データ・無断利用", info["headline"])
        self.assertNotIn("クリエイター保護・権利", info["headline"])


class SeriesStartTest(unittest.TestCase):
    def test_both_axes_start_on_the_same_day(self) -> None:
        self.assertEqual(trend.series_start(SLUG, "stance"), "2026-08-03")
        self.assertEqual(trend.series_start(SLUG, "issue"), "2026-08-03")

    def test_rounds_before_the_start_are_not_lined_up_and_the_start_day_is_included(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write(rounds(DAYS), Path(tmp))
            for kind in ("stance", "issue"):
                self.assertEqual([item["date"] for item in trend.rounds_for(SLUG, path, kind)], LINED_UP)

    def test_load_rounds_without_since_keeps_every_round(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write(rounds(DAYS), Path(tmp))
            self.assertEqual(len(trend.load_rounds(path, BASE, "stance")), len(DAYS))

    def test_the_three_stances_all_count_in_the_denominator(self) -> None:
        # 潮目の定義は立場が2つだけだった。中立・情報を分母に入れないと、ページの内訳と割合が合わない。
        rows = [row("2026-08-03", "規制・制限強化支持", ISSUES[0], "a"), row("2026-08-03", "中立・情報", ISSUES[0], "b")]
        with tempfile.TemporaryDirectory() as tmp:
            item = trend.rounds_for(SLUG, write(rows, Path(tmp)), "stance")[0]
        self.assertEqual(item["n"], 2)
        self.assertEqual(item["shares"]["中立・情報"], 50.0)


class ModelBreakNotesTest(unittest.TestCase):
    def test_break_inside_the_series_is_noted_on_both_axes(self) -> None:
        series = [{"date": "2026-09-20"}, {"date": "2026-09-29"}, {"date": "2026-10-06"}]
        for kind in ("stance", "issue"):
            notes = trend.model_break_notes(SLUG, series, kind)
            self.assertEqual(len(notes), 1)
            self.assertIn("2026年9月29日の回から、分類に使うAIを切り替えました", notes[0])

    def test_break_on_the_first_round_or_after_the_latest_is_not_noted(self) -> None:
        self.assertEqual(trend.model_break_notes(SLUG, [{"date": "2026-09-29"}, {"date": "2026-10-06"}], "stance"), [])
        self.assertEqual(trend.model_break_notes(SLUG, [{"date": "2026-09-05"}, {"date": "2026-09-20"}], "stance"), [])


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

    def test_tables_list_only_the_rounds_from_the_start(self) -> None:
        html = self.render(rounds(DAYS))
        for kind in ("stance", "issue"):
            self.assertEqual(
                re.findall(rf'id="ai-copyright-trend-panel-{kind}-row-([\d-]+)"', html), LINED_UP,
            )

    def test_notes_explain_why_earlier_rounds_are_left_out_and_the_ai_switch(self) -> None:
        html = self.render(rounds(DAYS))
        stance_panel, issue_panel = html.split('id="ai-copyright-trend-panel-issue"')
        for panel in (stance_panel, issue_panel):
            self.assertIn("2026年7月26日までの回は、分類のしかたが今と違うため、この図には並べていません", panel)
            self.assertIn("2026年9月29日の回から、分類に使うAIを切り替えました", panel)
            # 9/5の回だけ判定し直したこと、ほかの回は判定し直していないことを、日付つきで正直に書く
            self.assertIn("2026年9月5日の回は、分類の傾向が他の回と違っていたため、2026年10月7日に現在と同じAIで判定し直しました", panel)
            self.assertIn("判定し直したのは9月5日の回だけで、ほかの回は判定し直していません", panel)

    def test_headings_and_theme_name(self) -> None:
        html = self.render(rounds(DAYS))
        self.assertIn("生成AIと著作権への賛否の割合は変わった？", html)
        self.assertIn("生成AIと著作権で語られる論点は変わった？", html)
        self.assertNotIn("消費税", html)
        self.assertNotIn("減税", html)

    def test_chart_uses_the_meaningful_colors(self) -> None:
        html = self.render(rounds(DAYS))
        spec = trend.KINDS["stance"]
        self.assertIn(json.dumps([spec["colors"][2], spec["colors"][0], spec["colors"][3]]).replace(" ", ""), html.replace(" ", ""))

    def test_no_event_lines_for_this_theme(self) -> None:
        html = self.render(rounds(DAYS))
        self.assertNotIn('<li class="trend-event"', html)
        self.assertIn('"events":[]', html)

    def test_two_runs_give_the_same_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write(rounds(DAYS), Path(tmp))
            first = trend.render_for(SLUG, FRAME, path)
            self.assertEqual(trend.render_for(SLUG, first, path), first)

    def test_needs_two_rounds_from_the_start(self) -> None:
        # 2026-08-03以降が1回しか無い → 並べられないので止める（黙って別の期間を出さない）
        with tempfile.TemporaryDirectory() as tmp:
            path = write(rounds(["2026-07-12", "2026-07-26", "2026-08-03"]), Path(tmp))
            with self.assertRaises(ValueError):
                trend.render_for(SLUG, FRAME, path)


class ModelBreakGuardTest(unittest.TestCase):
    """AIが変わった回は、両方の軸の注意書きに記録が要る（賛否も論点も、新しい回は新しいAIで判定されるため）。"""

    def with_breaks(self, breaks: dict):
        return mock.patch.dict(trend.TREND_THEMES[SLUG], {"model_breaks": breaks})

    def test_changed_model_without_a_record_stops(self) -> None:
        with self.assertRaises(ValueError) as caught:
            trend_support.check_model_break(ROOT, SLUG, "2026-10-16", "kimi-k2.7-code", "next-model")
        self.assertIn("model_breaks", str(caught.exception))
        self.assertIn("2026-10-16", str(caught.exception))
        self.assertIn("stance・issue", str(caught.exception))

    def test_changed_model_with_both_records_passes(self) -> None:
        with self.with_breaks({"stance": ["2026-10-16"], "issue": ["2026-10-16"]}):
            trend_support.check_model_break(ROOT, SLUG, "2026-10-16", "a", "b")

    def test_same_model_and_unknown_model_do_not_stop(self) -> None:
        trend_support.check_model_break(ROOT, SLUG, "2026-10-16", "kimi-k2.7-code", "kimi-k2.7-code")
        trend_support.check_model_break(ROOT, SLUG, "2026-10-16", None, "kimi-k2.7-code")


class AdapterModelLookupTest(unittest.TestCase):
    def make_root(self, models: dict[str, str | None]) -> Path:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        for date, model in models.items():
            directory = tmp / "social-samples" / "updates" / SLUG / date
            directory.mkdir(parents=True)
            provenance = {"model": {"name": model}} if model else {}
            (directory / "report.json").write_text(json.dumps({"provenance": provenance}), encoding="utf-8")
        return tmp

    def test_previous_wave_model_is_the_latest_wave_before_the_current_date(self) -> None:
        root = self.make_root({"2026-09-05": None, "2026-09-20": "kimi-k2.6", "2026-09-29": "kimi-k2.7-code", "2026-10-06": "later"})
        self.assertEqual(adapter._previous_wave_model(root, "2026-10-06"), "kimi-k2.7-code")
        self.assertEqual(adapter._previous_wave_model(root, "2026-09-29"), "kimi-k2.6")

    def test_wave_without_a_model_record_gives_none(self) -> None:
        root = self.make_root({"2026-09-05": None})
        self.assertIsNone(adapter._previous_wave_model(root, "2026-09-20"))

    def test_no_saved_waves_gives_none(self) -> None:
        self.assertIsNone(adapter._previous_wave_model(Path(tempfile.mkdtemp()), "2026-10-16"))

    def test_current_wave_model_reads_the_staged_report(self) -> None:
        stage = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(stage, ignore_errors=True))
        self.assertIsNone(adapter._current_wave_model(stage))
        (stage / "report.json").write_text(json.dumps({"provenance": {"model": {"name": "kimi-k2.7-code"}}}), encoding="utf-8")
        self.assertEqual(adapter._current_wave_model(stage), "kimi-k2.7-code")


if __name__ == "__main__":
    unittest.main()
