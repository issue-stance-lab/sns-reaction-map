"""「意見の推移」の節が、非公開正典の数え直しと1行ずつ一致することの検査。

正典（social-samples/）を読むので、公開CIでは回さない（scripts/run_public_checks.py の
PRIVATE_DATA_TESTS に理由つきで登録してある）。
"""

import copy
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import consumption_tax_count_provenance as provenance  # noqa: E402
import trend_count_provenance as shared  # noqa: E402
import build_trend_section as trend  # noqa: E402
from scripts import bukatsu_count_provenance as bukatsu_provenance  # noqa: E402
from scripts.refresh_adapters import bukatsu as bukatsu_adapter  # noqa: E402
from refresh_adapters import consumption_tax as adapter  # noqa: E402

PAGE = ROOT / "docs/consumption-tax-cut-reaction-map.html"
CANON = ROOT / "social-samples/consumption-tax-cut_hermes_arena_classified.json"
NEW_DAY = "2026-10-10"


class TrendProvenanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = PAGE.read_text(encoding="utf-8")

    def test_published_page_matches_recount(self) -> None:
        result = provenance.private_verified_selectors(self.source, ROOT)
        rows = [key for key in result if "-row-" in key]
        self.assertTrue(any("panel-stance-row" in key for key in rows))
        self.assertTrue(any("panel-issue-row" in key for key in rows))
        self.assertIn("#consumption-tax-cut-trend-panel-issue-n-range", result)

    def test_tampered_cell_is_rejected(self) -> None:
        i = self.source.index("consumption-tax-cut-trend-panel-issue-row-")
        j = self.source.index('<span class="trend-c">', i)
        broken = self.source[:j - 1] + ("9" if self.source[j - 1] != "9" else "8") + self.source[j:]
        self.assertNotEqual(broken, self.source)
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(broken, ROOT)

    def test_tampered_count_in_a_cell_is_rejected(self) -> None:
        i = self.source.index("consumption-tax-cut-trend-panel-stance-row-")
        j = self.source.index("件）</span>", i)
        broken = self.source[:j - 1] + ("9" if self.source[j - 1] != "9" else "8") + self.source[j:]
        self.assertNotEqual(broken, self.source)
        with self.assertRaises(ValueError) as caught:
            provenance.private_verified_selectors(broken, ROOT)
        self.assertIn("数え直し", str(caught.exception))

    def test_every_cell_shows_its_count_and_the_recount_agrees(self) -> None:
        rows = re.findall(r'<tr id="consumption-tax-cut-trend-panel-stance-row-[^"]+".*?</tr>', self.source, re.S)
        self.assertGreaterEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(row.count('<span class="trend-c">'), 4)  # 立場4つ
        self.assertTrue(provenance.private_verified_selectors(self.source, ROOT))

    def test_stale_tooltip_data_is_rejected_even_when_the_table_is_right(self) -> None:
        """表の数字は合っていても、グラフ（ツールチップ・画像の指紋）が読む埋め込みデータの件数が古ければ止める。"""
        found = re.search(r'"c":\[(\d+)', self.source)
        self.assertIsNotNone(found)
        digit = int(found.group(1)) + 1
        broken = self.source[:found.start(1)] + str(digit) + self.source[found.end(1):]
        with self.assertRaises(ValueError) as caught:
            provenance.private_verified_selectors(broken, ROOT)
        self.assertIn("埋め込みデータ", str(caught.exception))

    def test_missing_chart_data_is_rejected(self) -> None:
        broken = self.source.replace("const panels = ", "const gone = ")
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(broken, ROOT)

    def test_stale_table_missing_latest_round_is_rejected(self) -> None:
        stale = re.sub(r'<tr id="consumption-tax-cut-trend-panel-stance-row-[^"]+" class="is-latest">.*?</tr>', "", self.source, count=1, flags=re.S)
        self.assertNotEqual(stale, self.source)
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(stale, ROOT)

    def test_adapter_rebuilds_the_section_into_a_fresh_page(self) -> None:
        """adapter の貼り直しで、推移の枠の中の節が（2回とも同じ形で）入り直す。潮目カードは戻らない。"""
        sample = ROOT / "social-samples/consumption-tax-cut_hermes_arena_classified.json"
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "page.html"
            shutil.copy(PAGE, page)
            adapter._apply_trend(ROOT, page, sample)
            once = page.read_text(encoding="utf-8")
            adapter._apply_trend(ROOT, page, sample)
            twice = page.read_text(encoding="utf-8")
        self.assertEqual(once, twice)
        self.assertEqual(once.count("<!-- TREND_CARD_START -->"), 1)
        self.assertEqual(once.count('data-trend-panel="'), 3)  # 立場・論点・反対慎重の理由
        self.assertEqual(once.count('<section class="update-dashboard">'), 1)
        self.assertNotIn("tide-widget", once)


class NextRoundTest(unittest.TestCase):
    """次の収集回が増えたとき、グラフが1回分伸びて、検査も通ること。"""

    @staticmethod
    def synthetic_round(count: int = 120) -> list[dict]:
        rows = json.loads(CANON.read_text(encoding="utf-8"))
        opinions = [r for r in rows if r["classification"].get("is_relevant") and r["classification"].get("is_opinion")]
        fresh = []
        for index, row in enumerate(opinions[:count]):
            row = copy.deepcopy(row)
            row["tweet_id"] = str(2_100_000_000_000_000_000 + index)
            row["url"] = f"https://x.com/synthetic/status/{row['tweet_id']}"
            row["fetched_at"] = f"{NEW_DAY}T03:00:00.000Z"  # 日本時間の12時
            if index < 40:
                row["classification"]["stance"] = "減税反対・慎重"
            fresh.append(row)
        return fresh

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.fresh = self.synthetic_round()
        self.cumulative = self.root / "cumulative.json"
        self.cumulative.write_text(json.dumps(json.loads(CANON.read_text(encoding="utf-8")) + self.fresh, ensure_ascii=False), encoding="utf-8")
        self.page = self.root / "page.html"
        shutil.copy(PAGE, self.page)

    def rebuild(self) -> str:
        adapter._apply_trend(self.root, self.page, self.cumulative)
        return self.page.read_text(encoding="utf-8")

    def test_new_round_extends_both_tabs_and_updates_the_date(self) -> None:
        html = self.rebuild()
        for kind in ("stance", "issue"):
            panel = re.search(rf'<div class="trend-panel" id="consumption-tax-cut-trend-panel-{kind}".*?</table>', html, re.S).group(0)
            self.assertEqual(len(re.findall(r'<tr id="[^"]+-row-2026-', panel)), 10)
            self.assertIn(f"-row-{NEW_DAY}", panel)
        self.assertIn("2026年10月10日時点", html)
        # 見出し（H2）の末尾の日付も、右上のバッジと同じく最新の収集日になる。
        self.assertEqual(html.count('<span class="trend-h2-date">（2026年10月10日時点）</span>'), 3)  # 3つのタブ
        self.assertNotIn("（2026年10月3日時点）", html)
        self.assertEqual(html.count("<!-- TREND_CARD_START -->"), 1)

    def test_extended_page_passes_recount_and_is_idempotent(self) -> None:
        first = self.rebuild()
        self.assertEqual(self.rebuild(), first)
        result = provenance.private_verified_selectors(first, ROOT, sample_file=self.cumulative)
        self.assertIn(f"#consumption-tax-cut-trend-panel-stance-row-{NEW_DAY}", result)
        self.assertIn(f"#consumption-tax-cut-trend-panel-issue-row-{NEW_DAY}", result)
        # 「反対・慎重の理由」の表も、新しい回を含めた数え直しで照合を通る。
        self.assertIn("#consumption-tax-cut-trend-panel-reason-row-0", result)
        self.assertIn("#consumption-tax-cut-trend-panel-reason-total", result)

    def test_old_page_is_rejected_once_data_has_advanced(self) -> None:
        """データだけ進んで節が古いままなら、検査が止める（貼り直し漏れ）。"""
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(PAGE.read_text(encoding="utf-8"), ROOT, sample_file=self.cumulative)

    def test_without_cumulative_it_rebuilds_from_the_canonical_file(self) -> None:
        shutil.copytree(ROOT / "social-samples", self.root / "social-samples", dirs_exist_ok=True, ignore=shutil.ignore_patterns("updates"))
        adapter._apply_trend(self.root, self.page)
        html = self.page.read_text(encoding="utf-8")
        self.assertEqual(html.count("<!-- TREND_CARD_START -->"), 1)
        self.assertNotIn(f"-row-{NEW_DAY}", html)  # 正典に新しい回は無いので、既存の9回のまま

    def test_without_any_source_the_existing_section_is_kept(self) -> None:
        adapter._apply_trend(self.root, self.page)  # 隔離環境: 正典も累積も無い
        html = self.page.read_text(encoding="utf-8")
        self.assertEqual(html.count("<!-- TREND_CARD_START -->"), 1)
        self.assertEqual(html.count('data-trend-panel="'), 3)

    def test_canonical_path_matches_themes_yaml(self) -> None:
        themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
        self.assertEqual(str(adapter.CANONICAL), themes["consumption-tax-cut"]["sample_file"])


class PresenceTest(unittest.TestCase):
    def test_frame_without_trend_is_rejected(self) -> None:
        source = PAGE.read_text(encoding="utf-8")
        gone = re.sub(r"<!-- TREND_CARD_START -->.*?<!-- TREND_CARD_END -->", "", source, count=1, flags=re.S)
        self.assertNotEqual(gone, source)
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(gone, ROOT)

    def test_a_returned_tide_card_is_rejected(self) -> None:
        """古い更新処理や単体スクリプトで、外したはずの潮目カードが戻ってきたら止める。"""
        source = PAGE.read_text(encoding="utf-8")
        returned = source.replace('<section class="update-dashboard">', '<section class="update-dashboard"><section class="tide-card" id="consumption-tax-cut-tide-widget"></section>', 1)
        self.assertNotEqual(returned, source)
        with self.assertRaises(ValueError) as caught:
            provenance.private_verified_selectors(returned, ROOT)
        self.assertIn("潮目カードが戻っています", str(caught.exception))

    def test_the_published_page_has_no_tide_card(self) -> None:
        source = PAGE.read_text(encoding="utf-8")
        self.assertNotIn("tide-widget", source)
        self.assertNotIn("TIDE_CARD", source)


class EventsAndReasonTamperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = PAGE.read_text(encoding="utf-8")

    def test_published_page_passes_events_and_reason_checks(self) -> None:
        result = provenance.private_verified_selectors(self.source, ROOT)
        self.assertTrue(any("-event-timeline-" in key for key in result))
        self.assertEqual(len([k for k in result if "panel-reason-row-" in k]), 6)

    def test_missing_event_item_is_rejected(self) -> None:
        gone = re.sub(r'<li class="trend-event" id="consumption-tax-cut-trend-panel-stance-event-timeline-2026-09-15">.*?</li>', "", self.source, count=1, flags=re.S)
        self.assertNotEqual(gone, self.source)
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(gone, ROOT)

    def test_changed_event_title_is_rejected(self) -> None:
        changed = self.source.replace("大綱を閣議決定、法案化する内容が具体化</p>", "大綱を閣議決定した</p>", 1)
        self.assertNotEqual(changed, self.source)
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(changed, ROOT)

    def test_tampered_reason_cell_is_rejected(self) -> None:
        i = self.source.index('id="consumption-tax-cut-trend-panel-reason-row-0"')
        j = self.source.index("件</td>", i)
        broken = self.source[:j - 1] + ("9" if self.source[j - 1] != "9" else "8") + self.source[j:]
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(broken, ROOT)

    def test_tampered_reason_total_is_rejected(self) -> None:
        match = re.search(r'(<span id="consumption-tax-cut-trend-panel-reason-total">)(\d+)(件</span>)', self.source)
        broken = self.source.replace(match.group(0), match.group(1) + str(int(match.group(2)) + 1) + match.group(3), 1)
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(broken, ROOT)

    def test_missing_reason_tab_is_rejected(self) -> None:
        gone = re.sub(r'<div class="trend-panel" id="consumption-tax-cut-trend-panel-reason".*?\n  </div>', "", self.source, count=1, flags=re.S)
        self.assertNotEqual(gone, self.source)
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(gone, ROOT)

    def test_unreadable_timeline_date_is_stopped_by_the_checker(self) -> None:
        config = json.loads((ROOT / "configs/consumption-tax-background.json").read_text(encoding="utf-8"))
        config["timeline"][0]["date"] = "2026年7月"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "configs").mkdir()
            (root / "configs/consumption-tax-background.json").write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError):
                shared._config_events(root, "configs/consumption-tax-background.json")


class PreviousSentenceProvenanceTest(unittest.TestCase):
    """推移の冒頭の「前回から今回にかけて…」の1行が、正典の数え直しと一致すること。"""

    def setUp(self) -> None:
        self.source = PAGE.read_text(encoding="utf-8")

    def sentence(self, kind: str) -> str:
        found = re.search(rf'<p class="trend-prev" id="consumption-tax-cut-trend-panel-{kind}-prev"><span[^>]*></span>(.*?)</p>', self.source, re.S)
        self.assertIsNotNone(found)
        return found.group(1)

    def test_published_sentences_pass(self) -> None:
        self.assertTrue(provenance.private_verified_selectors(self.source, ROOT))

    def reject(self, kind: str, change) -> str:
        """1行を change で書き換えたページを検査にかけ、止まること（ValueError）と、その理由の文を返す。"""
        text = self.sentence(kind)
        changed = change(text)
        self.assertNotEqual(changed, text)
        with self.assertRaises(ValueError) as caught:
            provenance.private_verified_selectors(self.source.replace(text, changed), ROOT)
        return str(caught.exception)

    def test_changed_percentage_is_rejected(self) -> None:
        number = re.search(r"から([\d.]+)%へ", self.sentence("stance")).group(1)
        reason = self.reject("stance", lambda text: text.replace(f"から{number}%へ", "から99.9%へ"))
        self.assertIn("前回との比較", reason)

    def test_swapped_direction_is_rejected(self) -> None:
        def swap(text: str) -> str:
            return text.replace("下がりました", "上がりました") if "下がりました" in text else text.replace("上がりました", "下がりました")

        self.assertIn("増減", self.reject("stance", swap))

    def test_wrong_noise_verdict_is_rejected(self) -> None:
        def flip(text: str) -> str:
            if "を超える差です。" in text:
                return text.replace("を超える差です。", "に収まる差です。")
            return text.replace("に収まる差です。", "を超える差です。")

        self.assertIn("ぶれの範囲", self.reject("issue", flip))

    def test_stale_dates_are_rejected(self) -> None:
        reason = self.reject("stance", lambda text: re.sub(r"今回（\d+月\d+日）", "今回（1月1日）", text))
        self.assertIn("日付", reason)

    def test_missing_sentence_is_rejected(self) -> None:
        broken = re.sub(r'<p class="trend-prev" id="consumption-tax-cut-trend-panel-stance-prev">.*?</p>', "", self.source, flags=re.S)
        self.assertNotEqual(broken, self.source)
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(broken, ROOT)

    def test_a_less_than_biggest_mover_is_rejected(self) -> None:
        """いちばん大きく動いた項目ではない項目を取り上げていたら止める。"""
        text = self.sentence("stance")
        labels = ["減税推進", "条件付き賛成・政府案に不満", "減税反対・慎重", "中立・情報"]
        current = re.search(r"「(.+?)」", text).group(1)
        other = next(label for label in labels if label != current)
        broken = self.source.replace(text, text.replace(f"「{current}」", f"「{other}」", 1))
        self.assertNotEqual(broken, self.source)
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(broken, ROOT)


if __name__ == "__main__":
    unittest.main()


BUKATSU_PAGE = ROOT / "docs/bukatsu-chiiki-reaction-map.html"
BUKATSU_CANON = ROOT / "social-samples/bukatsu-chiiki_hermes_classified.json"


class BukatsuTrendProvenanceTest(unittest.TestCase):
    """部活動の地域移行の「意見の推移」も、正典の数え直しと1行ずつ照合する（並べ始める日を適用したうえで）。"""

    def setUp(self) -> None:
        self.source = BUKATSU_PAGE.read_text(encoding="utf-8")

    def check(self, source: str) -> dict:
        return bukatsu_provenance.private_verified_selectors(source, ROOT)

    def test_published_page_matches_recount(self) -> None:
        result = self.check(self.source)
        stance_rows = [key for key in result if "-panel-stance-row-" in key]
        issue_rows = [key for key in result if "-panel-issue-row-" in key]
        # 立場は賛否の判定基準を見直した2026-09-15以降、論点は検索語を増やした2026-07-23以降の回だけ。
        self.assertTrue(stance_rows and all(key.rsplit("-row-", 1)[1] >= "2026-09-15" for key in stance_rows))
        self.assertTrue(issue_rows and all(key.rsplit("-row-", 1)[1] >= "2026-07-23" for key in issue_rows))
        self.assertIn("#bukatsu-chiiki-trend-panel-stance-n-range", result)
        self.assertIn("#bukatsu-chiiki-trend-panel-issue-n-range", result)

    def test_page_has_no_tide_card_and_no_reason_tab(self) -> None:
        self.assertNotIn("tide-widget", self.source)
        self.assertNotIn("TIDE_CARD", self.source)
        self.assertNotIn("bukatsu-chiiki-trend-panel-reason", self.source)
        self.assertEqual(self.source.count("<!-- TREND_CARD_START -->"), 1)

    def test_tampered_table_count_is_rejected(self) -> None:
        match = re.search(r'(id="bukatsu-chiiki-trend-panel-stance-row-2026-10-01".*?<td[^>]*>)(\d+)(件)', self.source, re.S)
        broken = self.source[:match.start(2)] + str(int(match.group(2)) + 1) + self.source[match.end(2):]
        with self.assertRaises(ValueError):
            self.check(broken)

    def test_tampered_embedded_data_is_rejected(self) -> None:
        broken = self.source.replace('"d":"2026-10-01","n":93,', '"d":"2026-10-01","n":94,', 1)
        self.assertNotEqual(broken, self.source)
        with self.assertRaises(ValueError):
            self.check(broken)

    def test_frame_without_trend_is_rejected(self) -> None:
        gone = re.sub(r"<!-- TREND_CARD_START -->.*?<!-- TREND_CARD_END -->", "", self.source, count=1, flags=re.S)
        self.assertNotEqual(gone, self.source)
        with self.assertRaises(ValueError):
            self.check(gone)

    def test_a_returned_tide_card_is_rejected(self) -> None:
        returned = self.source.replace('<section class="update-dashboard">', '<section class="update-dashboard"><section class="tide-card" id="bukatsu-tide-widget"></section>', 1)
        self.assertNotEqual(returned, self.source)
        with self.assertRaises(ValueError) as caught:
            self.check(returned)
        self.assertIn("潮目カードが戻っています", str(caught.exception))

    def test_a_page_that_lines_up_the_earlier_rounds_is_rejected(self) -> None:
        """並べ始める日を外して作ったページ（古い回まで並ぶ）は、設定どおりの数え直しと食い違うので止まる。"""
        saved = trend.TREND_THEMES["bukatsu-chiiki"]["series_from"]
        trend.TREND_THEMES["bukatsu-chiiki"]["series_from"] = {}
        try:
            wide = trend.render_for("bukatsu-chiiki", self.source, BUKATSU_CANON)
        finally:
            trend.TREND_THEMES["bukatsu-chiiki"]["series_from"] = saved
        self.assertIn("-row-2026-06-27", wide)
        with self.assertRaises(ValueError):
            self.check(wide)

    def test_rounds_before_the_start_are_not_in_the_recount(self) -> None:
        stance = shared._trend_rounds("bukatsu-chiiki", ROOT, "stance", shared._labels("bukatsu-chiiki")["stance"], "stance")
        issue = shared._trend_rounds("bukatsu-chiiki", ROOT, "main_issue", shared._labels("bukatsu-chiiki")["issue"], "issue")
        self.assertEqual(min(stance), "2026-09-15")
        self.assertEqual(min(issue), "2026-07-23")


class BukatsuBuildTest(unittest.TestCase):
    """更新処理（adapter）が、潮目なしの推移の枠を、同じ入力なら同じ結果で作ること。"""

    def test_build_is_idempotent_and_passes_recount(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            shutil.copy(BUKATSU_CANON, stage / "cumulative-candidate.json")
            first, second = stage / "first.html", stage / "second.html"
            bukatsu_adapter._build_once(ROOT, stage, "2026-10-01", BUKATSU_PAGE, first)
            bukatsu_adapter._build_once(ROOT, stage, "2026-10-01", first, second)
            html = first.read_text(encoding="utf-8")
            self.assertEqual(html, second.read_text(encoding="utf-8"))
        self.assertEqual(html.count("<!-- TREND_CARD_START -->"), 1)
        self.assertEqual(html.count('<section class="update-dashboard">'), 1)
        self.assertNotIn("tide-card", html)
        self.assertNotIn("bukatsu-tide-widget", html)
        self.assertEqual(html.count("/* HERMES_CARD_START */"), 1)
        self.assertNotIn("TIDE_CARD", html)
        self.assertTrue(bukatsu_provenance.private_verified_selectors(html, ROOT))

    def test_old_page_with_a_tide_card_is_turned_into_the_trend_frame(self) -> None:
        """潮目カード入りの古いページでも、同じ入口（update_bukatsu_tide.py）が推移の枠へ直す。"""
        old = BUKATSU_PAGE.read_text(encoding="utf-8")
        start = old.index('<section class="update-dashboard">')
        end = old.index("<!-- TREND_CARD_END --></section>") + len("<!-- TREND_CARD_END --></section>")
        tide_form = (
            old[:start]
            + '<section class="update-dashboard" aria-label="世論の潮目"><!-- TIDE_CARD_START -->'
            + '<section class="tide-card" id="bukatsu-tide-widget">x</section><!-- TIDE_CARD_END --></section>'
            + old[end:]
        ).replace("/* HERMES_CARD_START */", "/* TIDE_CARD_START */").replace("/* HERMES_CARD_END */", "/* TIDE_CARD_END */")
        self.assertIn("bukatsu-tide-widget", tide_form)
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            shutil.copy(BUKATSU_CANON, stage / "cumulative-candidate.json")
            template, out = stage / "old.html", stage / "out.html"
            template.write_text(tide_form, encoding="utf-8")
            bukatsu_adapter._build_once(ROOT, stage, "2026-10-01", template, out)
            html = out.read_text(encoding="utf-8")
        self.assertNotIn("bukatsu-tide-widget", html)
        self.assertNotIn("TIDE_CARD", html)
        self.assertEqual(html.count("<!-- TREND_CARD_START -->"), 1)
        self.assertEqual(html.count("/* HERMES_CARD_START */"), 1)
        self.assertTrue(bukatsu_provenance.private_verified_selectors(html, ROOT))
