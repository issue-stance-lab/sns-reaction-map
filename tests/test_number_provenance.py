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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sync_portal_stats import THEMES_YAML, parse_themes_yaml  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
