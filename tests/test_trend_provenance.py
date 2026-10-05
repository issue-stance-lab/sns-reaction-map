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

import consumption_tax_count_provenance as provenance  # noqa: E402
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
        j = self.source.index("%</td>", i)
        broken = self.source[:j - 1] + ("9" if self.source[j - 1] != "9" else "8") + self.source[j:]
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(broken, ROOT)

    def test_stale_table_missing_latest_round_is_rejected(self) -> None:
        stale = re.sub(r'<tr id="consumption-tax-cut-trend-panel-stance-row-[^"]+" class="is-latest">.*?</tr>', "", self.source, count=1, flags=re.S)
        self.assertNotEqual(stale, self.source)
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(stale, ROOT)

    def test_adapter_rebuilds_the_section_into_a_fresh_page(self) -> None:
        """adapter の潮目貼り直しで、潮目の枠の中の推移も（2回とも同じ形で）入り直す。"""
        updates = sorted((ROOT / "social-samples/updates/consumption-tax-cut").glob("*/classified.json"))
        latest = updates[-1]
        sample = ROOT / "social-samples/consumption-tax-cut_hermes_arena_classified.json"
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "page.html"
            shutil.copy(PAGE, page)
            adapter._apply_tide(ROOT, page, latest, latest.parent.name, sample)
            once = page.read_text(encoding="utf-8")
            adapter._apply_tide(ROOT, page, latest, latest.parent.name, sample)
            twice = page.read_text(encoding="utf-8")
        self.assertEqual(once, twice)
        self.assertEqual(once.count("<!-- TREND_CARD_START -->"), 1)
        self.assertEqual(once.count('data-trend-panel="'), 2)
        self.assertEqual(once.count("<!-- TIDE_CARD_START -->"), 1)


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
        updates = self.root / "social-samples/updates/consumption-tax-cut"
        latest = sorted((ROOT / "social-samples/updates/consumption-tax-cut").glob("*/classified.json"))[-1]
        (updates / latest.parent.name).mkdir(parents=True)
        shutil.copy(latest, updates / latest.parent.name / "classified.json")
        (updates / NEW_DAY).mkdir()
        self.current = updates / NEW_DAY / "classified.json"
        self.current.write_text(json.dumps(self.fresh, ensure_ascii=False), encoding="utf-8")
        self.page = self.root / "page.html"
        shutil.copy(PAGE, self.page)

    def rebuild(self) -> str:
        adapter._apply_tide(self.root, self.page, self.current, NEW_DAY, self.cumulative)
        return self.page.read_text(encoding="utf-8")

    def test_new_round_extends_both_tabs_and_updates_the_date(self) -> None:
        html = self.rebuild()
        for kind in ("stance", "issue"):
            panel = re.search(rf'<div class="trend-panel" id="consumption-tax-cut-trend-panel-{kind}".*?</table>', html, re.S).group(0)
            self.assertEqual(len(re.findall(r'<tr id="[^"]+-row-2026-', panel)), 10)
            self.assertIn(f"-row-{NEW_DAY}", panel)
        self.assertIn("2026年10月10日時点", html)
        # 見出し（H2）の末尾の日付も、右上のバッジと同じく最新の収集日になる。
        self.assertEqual(html.count('<span class="trend-h2-date">（2026年10月10日時点）</span>'), 2)
        self.assertNotIn("（2026年10月3日時点）", html)
        self.assertEqual(html.count("<!-- TREND_CARD_START -->"), 1)

    def test_extended_page_passes_recount_and_is_idempotent(self) -> None:
        first = self.rebuild()
        self.assertEqual(self.rebuild(), first)
        result = provenance.private_verified_selectors(first, ROOT, sample_file=self.cumulative)
        self.assertIn(f"#consumption-tax-cut-trend-panel-stance-row-{NEW_DAY}", result)
        self.assertIn(f"#consumption-tax-cut-trend-panel-issue-row-{NEW_DAY}", result)

    def test_old_page_is_rejected_once_data_has_advanced(self) -> None:
        """データだけ進んで節が古いままなら、検査が止める（貼り直し漏れ）。"""
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(PAGE.read_text(encoding="utf-8"), ROOT, sample_file=self.cumulative)

    def test_without_cumulative_it_rebuilds_from_the_canonical_file(self) -> None:
        shutil.copytree(ROOT / "social-samples", self.root / "social-samples", dirs_exist_ok=True, ignore=shutil.ignore_patterns("updates"))
        adapter._apply_tide(self.root, self.page, self.current, NEW_DAY)
        html = self.page.read_text(encoding="utf-8")
        self.assertEqual(html.count("<!-- TREND_CARD_START -->"), 1)
        self.assertNotIn(f"-row-{NEW_DAY}", html)  # 正典に新しい回は無いので、既存の9回のまま

    def test_without_any_source_the_existing_section_is_kept(self) -> None:
        adapter._apply_tide(self.root, self.page, self.current, NEW_DAY)  # 隔離環境: 正典も累積も無い
        html = self.page.read_text(encoding="utf-8")
        self.assertEqual(html.count("<!-- TREND_CARD_START -->"), 1)
        self.assertEqual(html.count('data-trend-panel="'), 2)

    def test_canonical_path_matches_themes_yaml(self) -> None:
        themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
        self.assertEqual(str(adapter.CANONICAL), themes["consumption-tax-cut"]["sample_file"])


class PresenceTest(unittest.TestCase):
    def test_tide_without_trend_is_rejected(self) -> None:
        source = PAGE.read_text(encoding="utf-8")
        gone = re.sub(r"<!-- TREND_CARD_START -->.*?<!-- TREND_CARD_END -->", "", source, count=1, flags=re.S)
        self.assertNotEqual(gone, source)
        with self.assertRaises(ValueError):
            provenance.private_verified_selectors(gone, ROOT)


if __name__ == "__main__":
    unittest.main()
