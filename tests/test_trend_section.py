"""収集回ごとの「意見の推移」（scripts/build_trend_section.py）の検査。

正典を使わず、合成データで挙動を固定する。件数や割合の期待値を実データから焼き込むと、
データ更新のたびにテストが落ちて更新が止まるため、実データとの突き合わせは
「潮目と同じ計算になること」だけを見る。
"""

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_trend_section as trend  # noqa: E402
import inject_tide_widget as tide  # noqa: E402

SLUG = "consumption-tax-cut"
BASE = trend._theme_base(SLUG)
LABELS = BASE["stance_labels"]
PRO, COND, CON, NEUTRAL = LABELS
ISSUES = BASE["issue_labels"]
SCOPE, FINANCE, EFFECT, ALT, BUSINESS, TRUST = ISSUES


def row(fetched_at: str, stance: str, *, relevant: bool = True, opinion: bool = True, tweet_id: str = "1", issue: str = SCOPE) -> dict:
    return {
        "tweet_id": tweet_id,
        "fetched_at": fetched_at,
        "classification": {"is_relevant": relevant, "is_opinion": opinion, "stance": stance, "main_issue": issue},
    }


def wave(day: str, counts: dict[str, int]) -> list[dict]:
    """日本時間の昼12時（UTC 03時）に収集した回を作る。"""
    rows = []
    for stance, n in counts.items():
        rows += [row(f"{day}T03:00:00.000Z", stance) for _ in range(n)]
    return rows


def write(rows: list[dict], directory: Path) -> Path:
    path = directory / "classified.json"
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return path


class RoundGroupingTest(unittest.TestCase):
    def test_collected_date_is_japan_time(self) -> None:
        # 8/9 の 16:00 UTC は 日本時間では 8/10 の 01:00。更新回のフォルダ名（日本時間）と揃える。
        self.assertEqual(trend.collected_date("2026-08-09T16:00:00.000Z"), "2026-08-10")
        self.assertEqual(trend.collected_date("2026-08-09T14:59:59.000Z"), "2026-08-09")

    def test_filters_and_counts(self) -> None:
        rows = (
            wave("2026-08-01", {PRO: 3, CON: 1})
            + [row("2026-08-01T03:00:00Z", PRO, relevant=False)]
            + [row("2026-08-01T03:00:00Z", PRO, opinion=False)]
            + [row("2026-08-01T03:00:00Z", "その他")]
            + [row("2026-08-01T03:00:00Z", None)]
            + wave("2026-08-08", {PRO: 1, CON: 1})
        )
        with tempfile.TemporaryDirectory() as tmp:
            series = trend.load_rounds(write(rows, Path(tmp)), BASE)
        self.assertEqual([item["date"] for item in series], ["2026-08-01", "2026-08-08"])
        self.assertEqual(series[0]["n"], 4)
        self.assertEqual(series[0]["shares"][PRO], 75.0)
        self.assertEqual(series[0]["shares"][NEUTRAL], 0.0)
        self.assertEqual(series[1]["shares"][CON], 50.0)

    def test_rows_without_fetched_at_are_skipped(self) -> None:
        rows = wave("2026-08-01", {PRO: 2}) + [{"tweet_id": "9", "classification": {"is_relevant": True, "is_opinion": True, "stance": PRO}}]
        with tempfile.TemporaryDirectory() as tmp:
            series = trend.load_rounds(write(rows, Path(tmp)), BASE)
        self.assertEqual(series[0]["n"], 2)

    def test_matches_tide_calculation(self) -> None:
        rows = wave("2026-09-24", {PRO: 45, COND: 16, CON: 29, NEUTRAL: 10}) + wave("2026-10-03", {PRO: 38, COND: 16, CON: 34, NEUTRAL: 12})
        with tempfile.TemporaryDirectory() as tmp:
            path = write(rows, Path(tmp))
            series = trend.load_rounds(path, BASE)
        for item in series:
            only = [r["classification"] for r in rows if trend.collected_date(r["fetched_at"]) == item["date"]]
            shares, n = tide.calc_pcts(only, LABELS, "stance")
            self.assertEqual(item["shares"], shares)
            self.assertEqual(item["n"], n)


class WordingTest(unittest.TestCase):
    def series(self, *rounds: dict[str, int], start: int = 1) -> list[dict]:
        rows: list[dict] = []
        for index, counts in enumerate(rounds):
            rows += wave(f"2026-09-{start + index * 7:02d}", counts)
        with tempfile.TemporaryDirectory() as tmp:
            return trend.load_rounds(write(rows, Path(tmp)), BASE)

    def test_latest_shares_lead_the_text(self) -> None:
        series = self.series({PRO: 50, COND: 20, CON: 20, NEUTRAL: 10}, {PRO: 30, COND: 20, CON: 40, NEUTRAL: 10})
        first = trend.lead_paragraphs(series, LABELS, "消費税減税")[0]
        self.assertIn("9月8日", first)
        self.assertIn("減税推進が30.0%でした", first)
        self.assertIn("減税反対・慎重は40.0%", first)
        self.assertLess(max(len(sentence) for sentence in first.split("。")), 80)

    def test_direction_and_noise_verdict(self) -> None:
        series = self.series({PRO: 500, COND: 200, CON: 200, NEUTRAL: 100}, {PRO: 300, COND: 200, CON: 400, NEUTRAL: 100})
        text = "".join(trend.lead_paragraphs(series, LABELS, "消費税減税"))
        self.assertIn("「減税推進」は9月1日の50.0%から30.0%へ、20.0ポイント下がりました", text)
        self.assertIn("「減税反対・慎重」は9月1日の20.0%から40.0%へ、20.0ポイント上がりました", text)
        self.assertIn("どちらも、ぶれの範囲を超える差です", text)

    def test_small_difference_is_called_within_noise(self) -> None:
        series = self.series({PRO: 51, COND: 20, CON: 19, NEUTRAL: 10}, {PRO: 47, COND: 20, CON: 23, NEUTRAL: 10})
        text = "".join(trend.lead_paragraphs(series, LABELS, "消費税減税"))
        self.assertIn("ぶれの範囲に収まる差です", text)
        self.assertNotIn("ぶれの範囲を超える", text)

    def test_reversal_is_mentioned_only_when_a_round_moves_against_the_trend(self) -> None:
        down = {PRO: 500, COND: 200, CON: 200, NEUTRAL: 100}
        dip = {PRO: 300, COND: 200, CON: 400, NEUTRAL: 100}
        bounce = {PRO: 500, COND: 200, CON: 200, NEUTRAL: 100}
        end = {PRO: 300, COND: 200, CON: 400, NEUTRAL: 100}
        with_reversal = "".join(trend.lead_paragraphs(self.series(down, dip, bounce, end), LABELS, "消費税減税"))
        self.assertIn("一直線の変化ではありません", with_reversal)
        # 4回は 9/1・9/8・9/15・9/22。2回目の谷（9/8）から3回目（9/15）で逆向きに動く。
        self.assertIn("9月8日から9月15日にかけて「減税推進」が20.0ポイント上がった回もあり", with_reversal)
        straight = "".join(trend.lead_paragraphs(self.series(down, {PRO: 400, COND: 200, CON: 300, NEUTRAL: 100}, end), LABELS, "消費税減税"))
        self.assertNotIn("一直線の変化ではありません", straight)

    def test_window_note_says_days_before_collection(self) -> None:
        # 「7日前までに」は「7日以上前」と読めて意味が逆になる。収集日の前の7日間、と書く。
        rows = wave("2026-09-01", {PRO: 5, CON: 5}) + wave("2026-09-08", {PRO: 5, CON: 5})
        for item in rows:
            item["tweet_id"] = "2000000000000000000"
        with tempfile.TemporaryDirectory() as tmp:
            series = trend.load_rounds(write(rows, Path(tmp)), BASE)
        notes = "".join(trend.note_lines(series, LABELS, "消費税減税"))
        self.assertNotIn("日前までに", notes)
        self.assertIn("世論調査ではありません", notes)


class InsertTest(unittest.TestCase):
    PAGE = (
        "<html><head><style>body{}</style></head><body>"
        '<section class="update-dashboard"><!-- TIDE_CARD_START --><div>潮目</div><!-- TIDE_CARD_END --></section>'
        "</body></html>"
    )

    def series(self) -> list[dict]:
        rows = wave("2026-09-01", {PRO: 5, CON: 5}) + wave("2026-09-08", {PRO: 4, CON: 6})
        with tempfile.TemporaryDirectory() as tmp:
            return trend.load_rounds(write(rows, Path(tmp)), BASE)

    def test_inserts_inside_tide_frame_once_and_is_idempotent(self) -> None:
        section = trend.render_section(SLUG, self.series())
        once = trend.insert_into_html(self.PAGE, section, trend.trend_css())
        twice = trend.insert_into_html(once, section, trend.trend_css())
        self.assertEqual(once, twice)
        self.assertEqual(once.count(trend.START), 1)
        self.assertEqual(once.count(trend.CSS_START), 1)
        self.assertLess(once.index(trend.END), once.index("<!-- TIDE_CARD_END -->"))
        self.assertGreater(once.index(trend.START), once.index("<!-- TIDE_CARD_START -->"))

    def test_replaces_old_section_with_new_numbers(self) -> None:
        section = trend.render_section(SLUG, self.series())
        once = trend.insert_into_html(self.PAGE, section, trend.trend_css())
        newer = section.replace("2026年9月8日時点", "2026年9月15日時点")
        updated = trend.insert_into_html(once, newer, trend.trend_css())
        self.assertIn("2026年9月15日時点", updated)
        self.assertNotIn("2026年9月8日時点", updated)
        self.assertEqual(updated.count(trend.START), 1)

    def test_requires_tide_frame(self) -> None:
        with self.assertRaises(ValueError):
            trend.insert_into_html("<html><style></style></html>", "x", "y")

    def test_needs_two_rounds(self) -> None:
        with self.assertRaises(ValueError):
            trend.render_section(SLUG, self.series()[:1])

    def test_section_contains_table_twin_and_no_world_opinion_claim(self) -> None:
        section = trend.render_section(SLUG, self.series())
        self.assertIn("<table", section)
        self.assertIn('<th scope="row">9月8日</th>', section)
        self.assertIn("世論調査ではありません", section)
        self.assertIn("2026年9月8日時点", section)


def issue_wave(day: str, counts: dict[str, int]) -> list[dict]:
    rows = []
    for issue, n in counts.items():
        rows += [row(f"{day}T03:00:00.000Z", PRO, issue=issue) for _ in range(n)]
    return rows


class IssueTest(unittest.TestCase):
    def series(self, *rounds: dict[str, int]) -> list[dict]:
        rows: list[dict] = []
        for index, counts in enumerate(rounds):
            rows += issue_wave(f"2026-09-{1 + index * 7:02d}", counts)
        with tempfile.TemporaryDirectory() as tmp:
            return trend.load_rounds(write(rows, Path(tmp)), BASE, "issue")

    def test_other_is_excluded_from_denominator(self) -> None:
        series = self.series({SCOPE: 6, TRUST: 4, "その他": 10}, {SCOPE: 5, TRUST: 5})
        self.assertEqual(series[0]["n"], 10)
        self.assertEqual(series[0]["shares"][SCOPE], 60.0)
        self.assertNotIn("その他", series[0]["shares"])

    def test_matches_tide_calculation_for_issues(self) -> None:
        rows = issue_wave("2026-09-24", {SCOPE: 27, TRUST: 33, EFFECT: 14, "その他": 3}) + issue_wave("2026-10-03", {SCOPE: 29, TRUST: 28, FINANCE: 7})
        with tempfile.TemporaryDirectory() as tmp:
            series = trend.load_rounds(write(rows, Path(tmp)), BASE, "issue")
        for item in series:
            only = [r["classification"] for r in rows if trend.collected_date(r["fetched_at"]) == item["date"]]
            shares, n = tide.calc_pcts(only, ISSUES, "main_issue")
            self.assertEqual(item["shares"], shares)
            self.assertEqual(item["n"], n)

    def test_wording_names_the_issue_not_just_the_label(self) -> None:
        series = self.series(
            {SCOPE: 160, TRUST: 440, EFFECT: 200, FINANCE: 100, ALT: 60, BUSINESS: 40},
            {SCOPE: 290, TRUST: 275, EFFECT: 210, FINANCE: 100, ALT: 75, BUSINESS: 50},
        )
        first, second = trend.lead_paragraphs(series, ISSUES, "消費税減税", "issue")
        self.assertIn("主な論点が最も多いのは「減税の対象範囲」の29.0%でした", first)
        self.assertIn("続いて「公約と政治不信」が27.5%、「減税の効果」が21.0%です", first)
        self.assertLess(max(len(sentence) for sentence in first.split("。")), 80)
        self.assertIn("主な論点が「公約と政治不信」の投稿は、9月1日の44.0%から27.5%へ、16.5ポイント下がりました", second)
        self.assertIn("主な論点が「減税の対象範囲」の投稿は、9月1日の16.0%から29.0%へ、13.0ポイント上がりました", second)
        self.assertIn("どちらも、ぶれの範囲を超える差です", second)

    def test_notes_explain_single_issue_and_exclusion(self) -> None:
        series = self.series({SCOPE: 6, TRUST: 4}, {SCOPE: 5, TRUST: 5})
        notes = "".join(trend.note_lines(series, ISSUES, "消費税減税", "issue"))
        self.assertIn("主な論点を1つに分類", notes)
        self.assertIn("「その他」は除いて", notes)
        self.assertIn("世論調査ではありません", notes)

    def test_emphasis_picks_only_big_movers_when_many_lines(self) -> None:
        series = self.series(
            {SCOPE: 160, TRUST: 440, EFFECT: 200, FINANCE: 100, ALT: 60, BUSINESS: 40},
            {SCOPE: 290, TRUST: 275, EFFECT: 210, FINANCE: 100, ALT: 75, BUSINESS: 50},
        )
        self.assertEqual(sorted(trend.emphasized(series, ISSUES)), sorted([ISSUES.index(SCOPE), ISSUES.index(TRUST)]))
        stance = [{"date": "2026-09-01", "n": 10, "counts": {l: 1 for l in LABELS}, "shares": {l: 10.0 for l in LABELS}, "recent_share": None}] * 2
        self.assertEqual(trend.emphasized(stance, LABELS), [])

    def test_no_emphasis_when_nothing_moves_beyond_noise(self) -> None:
        series = self.series({SCOPE: 30, TRUST: 30, EFFECT: 20, FINANCE: 10, ALT: 5, BUSINESS: 5}, {SCOPE: 31, TRUST: 29, EFFECT: 20, FINANCE: 10, ALT: 5, BUSINESS: 5})
        self.assertEqual(trend.emphasized(series, ISSUES), [])


class TabsTest(unittest.TestCase):
    def render(self, with_issue: bool) -> str:
        rows = wave("2026-09-01", {PRO: 5, CON: 5}) + wave("2026-09-08", {PRO: 4, CON: 6})
        with tempfile.TemporaryDirectory() as tmp:
            path = write(rows, Path(tmp))
            stance = trend.load_rounds(path, BASE, "stance")
            issue = trend.load_rounds(path, BASE, "issue") if with_issue else None
        return trend.render_section(SLUG, stance, issue)

    def test_two_panels_with_tabs_and_only_stance_visible(self) -> None:
        section = self.render(True)
        self.assertEqual(section.count('data-trend-panel="'), 2)
        self.assertEqual(section.count("data-trend-tab="), 2)
        self.assertIn('data-trend-panel="issue" hidden', section)
        self.assertNotIn('data-trend-panel="stance" hidden', section)
        self.assertIn("消費税減税の賛成・反対の割合は変わった？", section)
        self.assertIn("消費税減税で語られる論点は変わった？", section)
        # 見出しの末尾にも最新の収集日を出す（検索結果に読まれる場所）。
        self.assertEqual(section.count('<span class="trend-h2-date">（2026年9月8日時点）</span>'), 2)
        self.assertIn(">立場の変化<", section)
        self.assertIn(">論点の変化<", section)
        self.assertEqual(section.count("<table"), 2)


    def test_label_count_mismatch_is_rejected(self) -> None:
        rows = wave("2026-09-01", {PRO: 5, CON: 5}) + wave("2026-09-08", {PRO: 4, CON: 6})
        with tempfile.TemporaryDirectory() as tmp:
            stance = trend.load_rounds(write(rows, Path(tmp)), BASE, "stance")
        original = trend.TREND_THEMES[SLUG]["short_labels"]["stance"]
        trend.TREND_THEMES[SLUG]["short_labels"]["stance"] = original[:-1]
        try:
            with self.assertRaises(ValueError):
                trend.render_section(SLUG, stance)
        finally:
            trend.TREND_THEMES[SLUG]["short_labels"]["stance"] = original

    def test_heading_date_follows_the_latest_round_and_is_plain_text(self) -> None:
        section = self.render(False)
        match = re.search(r'<h2 id="[^"]+">(.*?)</h2>', section)
        text = re.sub(r"<[^>]+>", "", match.group(1))
        self.assertEqual(text, "消費税減税の賛成・反対の割合は変わった？（2026年9月8日時点）")

    def test_stance_only_has_no_tabs(self) -> None:
        section = self.render(False)
        self.assertEqual(section.count("data-trend-panel="), 1)
        self.assertNotIn("data-trend-tab=", section)

    def test_issue_chart_uses_validated_six_colors_and_distinct_shapes(self) -> None:
        spec = trend.KINDS["issue"]
        self.assertEqual(len(set(spec["colors"])), 6)
        self.assertEqual(len(set(spec["shapes"])), 6)
        self.assertEqual(len(set(trend.KINDS["stance"]["shapes"])), 4)
        self.assertTrue(set(spec["shapes"]) <= set(trend.SHAPE_PATHS))
        # 潮目の論点タブの色（青#3b82f6と紫#8b5cf6）は検証に落ちたため使わない。
        self.assertNotIn("#3b82f6", spec["colors"])
        self.assertNotIn("#8b5cf6", spec["colors"])

    def test_insert_twice_with_tabs_is_idempotent(self) -> None:
        page = InsertTest.PAGE
        section = self.render(True)
        once = trend.insert_into_html(page, section, trend.trend_css())
        self.assertEqual(once, trend.insert_into_html(once, section, trend.trend_css()))
        self.assertEqual(once.count(trend.START), 1)


def stance_wave(day: str, counts: dict[str, int], issue: str = SCOPE) -> list[dict]:
    rows = []
    for stance, n in counts.items():
        rows += [row(f"{day}T03:00:00.000Z", stance, issue=issue) for _ in range(n)]
    return rows


class EventsTest(unittest.TestCase):
    def series(self, *rounds: tuple[str, dict[str, int]]) -> list[dict]:
        rows: list[dict] = []
        for day, counts in rounds:
            rows += wave(day, counts)
        with tempfile.TemporaryDirectory() as tmp:
            return trend.load_rounds(write(rows, Path(tmp)), BASE, "stance")

    def test_load_events_reads_the_page_timeline_in_date_order(self) -> None:
        events = trend.load_events(SLUG)
        self.assertEqual([e["date"] for e in events], sorted(e["date"] for e in events))
        self.assertIn("2026-09-15", [e["date"] for e in events])
        self.assertTrue(all(e["title"] and isinstance(e["links"], list) for e in events))

    def test_events_with_unreadable_dates_are_skipped_not_fatal(self) -> None:
        config = {"timeline": [
            {"id": "ok", "date": "2026年9月15日", "title": "出来事", "links": [["https://example.jp/", "資料"]]},
            {"id": "ng", "date": "2026年9月", "title": "日付が月までしかない"},
        ]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.json"
            path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
            original = trend.TREND_THEMES[SLUG]["events_file"]
            trend.TREND_THEMES[SLUG]["events_file"] = str(path)  # 絶対パスは ROOT を上書きする
            try:
                events = trend.load_events(SLUG)
            finally:
                trend.TREND_THEMES[SLUG]["events_file"] = original
        self.assertEqual([e["id"] for e in events], ["ok"])

    def test_events_in_range_is_inclusive_of_both_ends(self) -> None:
        events = [{"date": d} for d in ("2026-07-27", "2026-07-28", "2026-08-05", "2026-10-03", "2026-10-04")]
        picked = trend.events_in_range(events, "2026-07-28", "2026-10-03")
        self.assertEqual([e["date"] for e in picked], ["2026-07-28", "2026-08-05", "2026-10-03"])

    def test_moves_compare_the_round_before_with_the_round_after(self) -> None:
        series = self.series(
            ("2026-09-01", {PRO: 500, COND: 200, CON: 200, NEUTRAL: 100}),
            ("2026-09-17", {PRO: 300, COND: 300, CON: 300, NEUTRAL: 100}),
            ("2026-09-24", {PRO: 300, COND: 300, CON: 300, NEUTRAL: 100}),
        )
        moves = trend.event_moves(series, LABELS, "2026-09-15")
        self.assertEqual((moves["before"]["date"], moves["after"]["date"], moves["gap"]), ("2026-09-01", "2026-09-17", 16))
        self.assertEqual([(label, delta) for label, delta in moves["moved"]], [(PRO, -20.0), (COND, 10.0), (CON, 10.0)])

    def test_round_on_the_event_day_counts_as_after(self) -> None:
        series = self.series(("2026-09-01", {PRO: 5, CON: 5}), ("2026-09-15", {PRO: 5, CON: 5}))
        moves = trend.event_moves(series, LABELS, "2026-09-15")
        self.assertEqual(moves["after"]["date"], "2026-09-15")

    def test_no_moves_when_the_event_has_no_round_on_one_side(self) -> None:
        series = self.series(("2026-09-01", {PRO: 5, CON: 5}), ("2026-09-08", {PRO: 5, CON: 5}))
        self.assertIsNone(trend.event_moves(series, LABELS, "2026-08-01"))
        self.assertIsNone(trend.event_moves(series, LABELS, "2026-09-20"))

    def test_small_changes_are_not_reported_as_moves(self) -> None:
        series = self.series(("2026-09-01", {PRO: 51, CON: 49}), ("2026-09-08", {PRO: 47, CON: 53}))
        moves = trend.event_moves(series, LABELS, "2026-09-05")
        self.assertEqual(moves["moved"], [])
        sentences = trend.event_sentences(moves, "stance")
        self.assertIn("ぶれの範囲を超える動きはありませんでした。", sentences)

    def test_sentences_state_facts_and_never_a_cause(self) -> None:
        series = self.series(
            ("2026-09-01", {PRO: 500, COND: 200, CON: 200, NEUTRAL: 100}),
            ("2026-09-17", {PRO: 300, COND: 300, CON: 300, NEUTRAL: 100}),
        )
        moves = trend.event_moves(series, LABELS, "2026-09-15")
        sentences = trend.event_sentences(moves, "stance")
        text = "".join(sentences)
        self.assertIn("直後の9月17日の回を、直前の9月1日の回と比べました。", text)
        self.assertIn("下がったのは「減税推進」の20.0ポイントです。", text)
        self.assertIn("上がったのは「条件付き賛成・政府案に不満」の10.0ポイントと「減税反対・慎重」の10.0ポイントです。", text)
        self.assertIn("どれもぶれの範囲を超える差です。", text)
        self.assertIn("回の間隔は16日あります。", text)
        for word in ("影響", "原因", "せいで", "のため", "によって", "により"):
            self.assertNotIn(word, text)
        self.assertLess(max(len(s) for s in sentences), 80)

    def test_single_move_uses_singular_wording(self) -> None:
        series = self.series(
            ("2026-09-01", {PRO: 500, COND: 100, CON: 300, NEUTRAL: 100}),
            ("2026-09-17", {PRO: 300, COND: 100, CON: 300, NEUTRAL: 300}),
        )
        moves = trend.event_moves(series, LABELS, "2026-09-15")
        sentences = trend.event_sentences(moves, "stance")
        self.assertEqual(len(moves["moved"]), 2)
        one = {"before": moves["before"], "after": moves["after"], "gap": 16, "moved": moves["moved"][:1]}
        self.assertIn("この差はぶれの範囲を超えています。", trend.event_sentences(one, "stance"))
        self.assertIn("どれもぶれの範囲を超える差です。", sentences)

    def test_issue_wording_names_the_axis(self) -> None:
        series = self.series(("2026-09-01", {PRO: 5, CON: 5}), ("2026-09-08", {PRO: 5, CON: 5}))
        moves = {"before": series[0], "after": series[1], "gap": 7, "moved": [(TRUST, -6.5), (BUSINESS, 2.2)]}
        text = "".join(trend.event_sentences(moves, "issue"))
        self.assertIn("主な論点の割合で、下がったのは「公約と政治不信」の6.5ポイントです。", text)
        self.assertIn("上がったのは「事業者の実務負担」の2.2ポイントです。", text)


class ReasonTest(unittest.TestCase):
    def reasons(self, *rounds: tuple[str, dict[str, int]]) -> dict:
        rows: list[dict] = []
        for day, counts in rounds:
            rows += issue_wave_for_stance(day, CON, counts)
            rows += issue_wave_for_stance(day, PRO, {SCOPE: 40})  # 別の立場は数えない
        rows += [row("2026-09-01T03:00:00Z", CON, relevant=False, issue=EFFECT)]  # 関連なしは数えない
        with tempfile.TemporaryDirectory() as tmp:
            return trend.load_reasons(write(rows, Path(tmp)), BASE, CON)

    def test_counts_only_the_focus_stance_and_excludes_other(self) -> None:
        info = self.reasons(
            ("2026-09-01", {EFFECT: 6, FINANCE: 3, "その他": 5}),
            ("2026-09-08", {EFFECT: 2, FINANCE: 2, TRUST: 1}),
        )
        self.assertEqual(info["n"], 14)
        self.assertEqual((info["rounds"], info["n_min"], info["n_max"]), (2, 5, 9))
        self.assertEqual([item["label"] for item in info["items"]][:2], [EFFECT, FINANCE])
        self.assertEqual(info["items"][0]["count"], 8)
        self.assertEqual(info["items"][0]["share"], 57.1)
        self.assertEqual(sum(item["count"] for item in info["items"]), 14)

    def test_range_is_the_min_and_max_round_share_rounded_half_up(self) -> None:
        info = self.reasons(("2026-09-01", {EFFECT: 1, FINANCE: 1}), ("2026-09-08", {EFFECT: 3, FINANCE: 1}))
        effect = next(item for item in info["items"] if item["label"] == EFFECT)
        self.assertEqual((effect["lo"], effect["hi"]), (50, 75))  # 50% と 75%
        finance = next(item for item in info["items"] if item["label"] == FINANCE)
        self.assertEqual((finance["lo"], finance["hi"]), (25, 50))

    def test_issues_without_posts_still_appear_with_zero(self) -> None:
        info = self.reasons(("2026-09-01", {EFFECT: 2}), ("2026-09-08", {EFFECT: 2}))
        self.assertEqual(len(info["items"]), len(ISSUES))
        self.assertEqual(info["items"][-1]["count"], 0)

    def test_text_says_the_stance_in_quotes_and_each_sentence_is_short(self) -> None:
        info = self.reasons(
            ("2026-09-01", {EFFECT: 60, FINANCE: 30, TRUST: 20}),
            ("2026-09-08", {EFFECT: 40, FINANCE: 40, TRUST: 30}),
        )
        paragraphs = trend.reason_paragraphs(info, "消費税減税")
        text = "".join(p for p, _ in paragraphs)
        self.assertIn("立場が「減税反対・慎重」の投稿は220件ありました。", text)
        self.assertIn("全期間でまとめました。", text)
        notes = "".join(n for n, _ in trend.reason_notes(info, "消費税減税"))
        self.assertIn("論点は話題の分類で、賛否の理由そのものではありません。", notes)
        self.assertIn("世論調査ではありません", notes)
        for paragraph, _ in paragraphs + trend.reason_notes(info, "消費税減税"):
            for sentence in paragraph.split("。"):
                self.assertLess(len(sentence), 80)

    def test_wrap_marks_exactly_one_fragment(self) -> None:
        wrapped = trend._wrap_once("1回は120〜162件で、別の回は120〜162件です。", "120〜162件", "x-id")
        self.assertEqual(wrapped.count('<span id="x-id">'), 1)


def issue_wave_for_stance(day: str, stance: str, counts: dict[str, int]) -> list[dict]:
    rows = []
    for issue, n in counts.items():
        rows += [row(f"{day}T03:00:00.000Z", stance, issue=issue) for _ in range(n)]
    return rows


class SectionWithEventsTest(unittest.TestCase):
    def render(self) -> str:
        rows = wave("2026-09-01", {PRO: 5, CON: 5}) + wave("2026-09-17", {PRO: 3, CON: 7})
        with tempfile.TemporaryDirectory() as tmp:
            path = write(rows, Path(tmp))
            stance = trend.load_rounds(path, BASE, "stance")
            issue = trend.load_rounds(path, BASE, "issue")
            reason = trend.load_reasons(path, BASE, CON)
        events = [e for e in trend.load_events(SLUG)]
        return trend.render_section(SLUG, stance, issue, reason=reason, events=events)

    def test_three_tabs_and_events_on_both_charts(self) -> None:
        section = self.render()
        self.assertEqual(section.count("data-trend-tab="), 3)
        self.assertIn(">反対・慎重の理由<", section)
        self.assertEqual(section.count('data-trend-panel="'), 3)
        self.assertIn('data-trend-panel="reason" hidden', section)
        # 9/1〜9/17 の間にある出来事は 9/15 の1件だけ（7/30・8/5 はグラフの期間の外）
        self.assertEqual(section.count('class="trend-event"'), 2)  # 立場と論点に1件ずつ
        self.assertIn('"events":[{"d":"2026-09-15","n":1,', section)

    def test_events_only_inside_the_chart_period(self) -> None:
        section = self.render()
        self.assertNotIn("2026-07-30", section)
        self.assertNotIn("検討を表明", section)

    def test_event_list_links_open_in_new_tab_safely(self) -> None:
        section = self.render()
        self.assertIn('target="_blank" rel="noopener"', section)

    def test_every_event_item_carries_a_checkable_id(self) -> None:
        section = self.render()
        self.assertIn('id="consumption-tax-cut-trend-panel-stance-event-timeline-2026-09-15"', section)
        self.assertIn('id="consumption-tax-cut-trend-panel-issue-event-timeline-2026-09-15"', section)

    def test_reason_panel_has_rows_for_every_issue_and_marked_numbers(self) -> None:
        section = self.render()
        panel = section[section.index('data-trend-panel="reason"'):]
        self.assertEqual(panel.count('<tr id="consumption-tax-cut-trend-panel-reason-row-'), len(ISSUES))
        self.assertIn('id="consumption-tax-cut-trend-panel-reason-total"', panel)
        self.assertIn('id="consumption-tax-cut-trend-panel-reason-n-range-lead"', panel)
        self.assertIn('id="consumption-tax-cut-trend-panel-reason-n-range-note"', panel)

    def test_reason_heading_has_the_date_too(self) -> None:
        section = self.render()
        self.assertEqual(section.count('<span class="trend-h2-date">（2026年9月17日時点）</span>'), 3)

    def test_without_reason_or_events_the_old_layout_is_unchanged(self) -> None:
        rows = wave("2026-09-01", {PRO: 5, CON: 5}) + wave("2026-09-08", {PRO: 4, CON: 6})
        with tempfile.TemporaryDirectory() as tmp:
            stance = trend.load_rounds(write(rows, Path(tmp)), BASE, "stance")
        section = trend.render_section(SLUG, stance)
        self.assertNotIn('class="trend-events"', section)
        self.assertNotIn("data-trend-tab=", section)
        self.assertIn('"events":[]', section)


class ShareBlockTest(unittest.TestCase):
    def render(self) -> str:
        rows = wave("2026-09-01", {PRO: 5, CON: 5}) + wave("2026-09-17", {PRO: 3, CON: 7})
        with tempfile.TemporaryDirectory() as tmp:
            path = write(rows, Path(tmp))
            stance = trend.load_rounds(path, BASE, "stance")
            issue = trend.load_rounds(path, BASE, "issue")
            reason = trend.load_reasons(path, BASE, CON)
        return trend.render_section(SLUG, stance, issue, reason=reason, events=[])

    def test_stance_and_issue_panels_have_a_share_block_but_not_the_reason_panel(self) -> None:
        section = self.render()
        self.assertEqual(section.count('<details class="trend-share">'), 2)
        reason_panel = section[section.index('data-trend-panel="reason"'):section.index("<script>")]
        self.assertNotIn("<details", reason_panel)

    def test_image_is_referenced_relative_to_the_page_and_downloadable(self) -> None:
        section = self.render()
        self.assertIn('<img src="images/trend/consumption-tax-cut-stance-trend.png" width="1200" height="675"', section)
        self.assertIn('href="images/trend/consumption-tax-cut-issue-trend.png" download data-trend-download="issue"', section)
        self.assertIn('data-trend-copy="stance"', section)

    def test_alt_text_has_the_title_as_of_date_and_latest_numbers(self) -> None:
        section = self.render()
        alt = re.search(r'<img src="images/trend/consumption-tax-cut-stance-trend.png"[^>]*alt="([^"]*)"', section).group(1)
        self.assertIn("消費税減税の賛成・反対の割合は変わった？", alt)
        self.assertIn("2026年9月17日時点", alt)
        self.assertIn("減税推進30.0%", alt)
        self.assertIn("減税反対・慎重70.0%", alt)
        self.assertIn("世論調査ではありません", alt)

    def test_embed_code_points_at_the_public_image_with_a_credit_link(self) -> None:
        import html as htmllib
        section = self.render()
        code = htmllib.unescape(re.search(r'<textarea class="trend-share-code"[^>]*>(.*?)</textarea>', section, re.S).group(1))
        page = "https://sns-reaction-map.jp/consumption-tax-cut-reaction-map.html"
        self.assertIn(f'<a href="{page}#consumption-tax-cut-trend-panel-stance">', code)
        self.assertIn('<img src="https://sns-reaction-map.jp/images/trend/consumption-tax-cut-stance-trend.png"', code)
        self.assertIn('width="600" height="338"', code)
        self.assertIn(f'出典：<a href="{page}">SNS反応まっぷ</a>', code)
        self.assertIn("世論調査ではありません", code)

    def test_embed_code_alt_is_attribute_safe(self) -> None:
        code = trend.embed_code(SLUG, "stance", 'a"b<c>', "panel")
        self.assertIn('alt="a&quot;b&lt;c&gt;"', code)

    def test_terms_are_shown_next_to_the_download(self) -> None:
        section = self.render()
        self.assertIn(trend.EMBED_TERMS, section)
        self.assertIn("出典", trend.EMBED_TERMS)

    def test_no_share_block_when_the_theme_does_not_distribute_images(self) -> None:
        original = trend.TREND_THEMES[SLUG]["share_images"]
        trend.TREND_THEMES[SLUG]["share_images"] = False
        try:
            self.assertNotIn("trend-share", self.render().replace(".trend-share", ""))
        finally:
            trend.TREND_THEMES[SLUG]["share_images"] = original

    def test_analytics_calls_are_guarded(self) -> None:
        section = self.render()
        self.assertIn('typeof gtag === "function"', section)
        self.assertIn('"trend_image_copy"', section)
        self.assertIn('"trend_image_download"', section)


if __name__ == "__main__":
    unittest.main()
