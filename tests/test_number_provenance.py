"""ページ上の数字に出所があることを、テストからも押さえる。

`scripts/verify_number_provenance.py` が exit 0 であることを確かめる。
非公開の正典（sample_file）が無い環境では、検査そのものが成り立たないので skip する。
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sync_portal_stats import THEMES_YAML, parse_themes_yaml  # noqa: E402
import verify_number_provenance  # noqa: E402
from verify_number_provenance import (  # noqa: E402
    Derived,
    extract_numbers,
    nearest_label,
    selector_regions,
)

SCRIPT = ROOT / "scripts" / "verify_number_provenance.py"


def missing_sources() -> list[str]:
    missing = []
    for theme, data in parse_themes_yaml(THEMES_YAML).items():
        sample = data.get("sample_file")
        if not sample or not (ROOT / str(sample)).is_file():
            missing.append(theme)
            continue
        config = ROOT / "configs" / f"{theme}-reaction-map.json"
        if not config.is_file():
            missing.append(theme)
            continue
        block = json.loads(config.read_text(encoding="utf-8")).get("number_provenance") or {}
        for entry in block.get("sources") or []:
            path = entry if isinstance(entry, str) else entry.get("path")
            if not (ROOT / str(path)).is_file():
                missing.append(theme)
                break
    return sorted(set(missing))


class NumberProvenanceTest(unittest.TestCase):
    def test_all_themes_pass(self) -> None:
        missing = missing_sources()
        if missing:
            self.skipTest(f"非公開の正典が無いテーマがあります: {', '.join(missing)}")
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(
            result.returncode, 0, f"説明できない数字があります:\n{result.stdout}\n{result.stderr}"
        )

    def test_extracts_counts_even_when_a_tag_splits_the_number(self) -> None:
        """注目ポイントの `389<small>件</small>` を取りこぼさない。"""
        found = extract_numbers('<strong class="insight-value">389<small>件</small></strong>', "t")
        self.assertEqual([item.value for item in found], [389])

    def test_ignores_numbers_in_comments(self) -> None:
        self.assertEqual(extract_numbers("<!-- 999件 -->", "t"), [])

    def test_extracts_arena_sector_counts(self) -> None:
        found = extract_numbers("const ISSUES=[{k:'費用',n:54},{k:'その他',n:32}];", "t")
        self.assertEqual([item.value for item in found], [54, 32])

    def test_selector_regions_cover_the_element_body(self) -> None:
        html = '<p class="lead">A</p><p class="quote-block">B 12件</p>'
        regions = selector_regions(html, ["quote-block"])
        offset = html.index("12件")
        self.assertTrue(any(start <= offset < end for start, end in regions))

    def test_nearest_label_needs_the_label_to_be_adjacent(self) -> None:
        labels = {"禁止支持", "インフラ整備優先"}
        text = "インフラ整備優先派（27件）"
        self.assertEqual(nearest_label(text, text.index("27"), labels), "インフラ整備優先")
        # 別の数字の説明に紛れているだけのラベルは拾わない
        far = "禁止支持6件、中立・体験10件"
        self.assertIsNone(nearest_label(far, far.index("10"), labels))

    def test_nearest_label_reads_through_the_set_phrase_ronten_to_suru_toko(self) -> None:
        """「『論点名』を論点とする投稿は29件」の29は、その論点の件数を名乗っている。

        ラベルと数字のあいだが9文字あるためラベル無しの扱いになり、無関係な集計
        （検索語別の件数など）と偶然一致した 29 が「説明できた」ことになっていた
        （高齢者テーマ、2026-10-07。39件のはずが29件でも検査が通る）。
        """
        labels = {"地方の足・移動権", "義務化・事故防止"}
        text = "「地方の足・移動権」を論点とする投稿は29件で、義務化・事故防止（221件）に比べると"
        self.assertEqual(nearest_label(text, text.index("29"), labels), "地方の足・移動権")
        self.assertEqual(nearest_label(text, text.index("221"), labels), "義務化・事故防止")
        # 決まり文句以外が挟まれば、これまでどおり別の数字の説明として扱う
        far = "「地方の足・移動権」について、投稿は29件"
        self.assertIsNone(nearest_label(far, far.index("29"), labels))

    @staticmethod
    def _fixture() -> Derived:
        # main_issue: A=5 / B=4、stance: X=5 / Y=4、クロス: A×X=4 A×Y=1 B×X=1 B×Y=3
        pairs = [("A", "X")] * 4 + [("A", "Y")] + [("B", "X")] + [("B", "Y")] * 3
        return Derived(
            "t",
            [
                {"classification": {"main_issue": i, "stance": s, "is_opinion": True}}
                for i, s in pairs
            ],
        )

    def test_cross_tab_values_are_not_available_by_default(self) -> None:
        derived = self._fixture()
        # 3 は B×Y のクロス集計にしかない。既定（base）では説明できない
        self.assertIsNone(derived.lookup(3, ["base"], None))
        self.assertIsNotNone(derived.lookup(3, ["base", "cross_tab"], None))
        # 5 は main_issue=A の1次元件数なので base で説明できる
        self.assertIsNotNone(derived.lookup(5, ["base"], None))

    def test_label_must_match_the_tabulation(self) -> None:
        derived = self._fixture()
        self.assertIsNotNone(derived.lookup(5, ["base"], "A"))
        self.assertIsNone(derived.lookup(5, ["base"], "B"))


class ElderlyObservationProvenanceTest(unittest.TestCase):
    """高齢者ページの「収集・分類で分かったこと」の論点別件数も、検査が見ていること。

    `article-trust-observations` が exclude_selectors に入っていたため、この箇条書きの
    数字は検査されず、設定にべた書きされた古い 29／221 が 2026-09-30 と 2026-10-07 の
    2回、公開ページへ出かけた（どちらも検査は通っていた）。除外を外し、論点名に添えられた
    数字が**その論点の件数**でなければ落ちるようにした。
    """

    THEME = "elderly-license-revocation"

    def setUp(self) -> None:
        if self.THEME in missing_sources():
            self.skipTest("非公開の正典が無い環境では数字を導けない")
        self.theme_data = parse_themes_yaml(THEMES_YAML)[self.THEME]
        self.html_path = ROOT / str(self.theme_data["html"])
        public = json.loads((ROOT / f"data/public/themes/{self.THEME}.json").read_text(encoding="utf-8"))
        counts = {issue["label"]: issue["count"] for issue in public["issues"]}
        self.local = counts["地方の足・移動権"]
        self.duty = counts["義務化・事故防止"]
        self.page = self.html_path.read_text(encoding="utf-8")
        self.sentence = f"投稿は{self.local:,}件で、義務化・事故防止（{self.duty:,}件）"
        self.assertIn(self.sentence, self.page, "公開ページに論点比較の文が無い（テストの前提が崩れた）")

    def _problems(self, sentence: str) -> list[str]:
        text = self.page.replace(self.sentence, sentence, 1)
        documents = [(str(self.html_path.relative_to(ROOT)), text)]
        with mock.patch.object(verify_number_provenance, "_documents", return_value=documents):
            _, problems = verify_number_provenance.check_theme(self.THEME, self.theme_data)
        return problems

    def test_observations_are_not_excluded_from_the_check(self) -> None:
        config = json.loads((ROOT / f"configs/{self.THEME}-reaction-map.json").read_text(encoding="utf-8"))
        excludes = config["number_provenance"]["exclude_selectors"]
        self.assertNotIn("article-trust-observations", excludes)

    def test_the_published_numbers_pass(self) -> None:
        self.assertEqual(self._problems(self.sentence), [])

    def test_both_numbers_stale_is_caught(self) -> None:
        """2026-10-07 の事故そのもの（9/4時点の 29／221）。"""
        self.assertTrue(self._problems("投稿は29件で、義務化・事故防止（221件）"))

    def test_only_the_mobility_count_wrong_is_caught(self) -> None:
        """ラベルから離れた「投稿は29件」の側だけ誤っていても落ちる。

        29 は別の集計（検索語「免許返納 年齢制限」の意見件数）と偶然一致する値で、
        論点名との結びつきを見ないと「説明できた」ことになる。2026-10-07 に実際に
        見逃した数字そのもの（論点名のあとの決まり文句を読み飛ばす nearest_label の修正が要る）。
        """
        wrong = next(value for value in (29, 28, 30) if value != self.local)
        self.assertTrue(self._problems(f"投稿は{wrong:,}件で、義務化・事故防止（{self.duty:,}件）"))

    def test_only_the_duty_count_wrong_is_caught(self) -> None:
        wrong = self.duty + 1000
        self.assertTrue(self._problems(f"投稿は{self.local:,}件で、義務化・事故防止（{wrong:,}件）"))


if __name__ == "__main__":
    unittest.main()
