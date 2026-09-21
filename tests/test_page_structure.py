"""公開ページの土台(チャートのデータ・画像/スクリプトの参照先)が壊れていないことを、テストからも押さえる(課題84)。

`scripts/verify_page_structure.py` が実データに対して exit 0 であることに加えて、
検査ロジック自体が壊れたときにちゃんと落ちること・JSの文字列結合の断片を
誤検知しないことを、テスト用のHTML断片で固定する。実装時に一度、
`'+aicImgPath+'` のようなJSコードの断片を `src="…"` と誤検知していた
(<script>の中身を空白化する前)ため、その回帰を防ぐ。
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "verify_page_structure.py"

sys.path.insert(0, str(ROOT / "scripts"))
import verify_page_structure as vps  # noqa: E402


class PageStructureLiveTest(unittest.TestCase):
    def test_all_published_pages_pass(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(
            result.returncode, 0,
            f"公開ページの構造が壊れています:\n{result.stdout}\n{result.stderr}",
        )


class PlanetDataTests(unittest.TestCase):
    def test_empty_stances_is_reported(self) -> None:
        with TemporaryDirectory() as d:
            page = Path(d) / "sample-reaction-map.html"
            page.write_text(
                '<script id="planet-data">window.PLANET_DATA='
                '{"stances": [], "modes": [{"id":"all"}]};</script>',
                encoding="utf-8",
            )
            failures = vps.check_chart_data("sample", page, page.read_text(encoding="utf-8"))
            self.assertTrue(any("stancesが空です" in f for f in failures), failures)

    def test_populated_data_passes(self) -> None:
        with TemporaryDirectory() as d:
            page = Path(d) / "sample-reaction-map.html"
            page.write_text(
                '<script id="planet-data">window.PLANET_DATA='
                '{"stances": [{"id":"a"}], "modes": [{"id":"all"}]};</script>',
                encoding="utf-8",
            )
            failures = vps.check_chart_data("sample", page, page.read_text(encoding="utf-8"))
            self.assertEqual(failures, [])

    def test_broken_json_is_reported(self) -> None:
        with TemporaryDirectory() as d:
            page = Path(d) / "sample-reaction-map.html"
            page.write_text(
                '<script id="planet-data">window.PLANET_DATA={"stances": [}</script>',
                encoding="utf-8",
            )
            failures = vps.check_chart_data("sample", page, page.read_text(encoding="utf-8"))
            self.assertTrue(any("JSONとして読めません" in f for f in failures), failures)

    def test_unknown_chart_technology_is_reported(self) -> None:
        with TemporaryDirectory() as d:
            page = Path(d) / "sample-reaction-map.html"
            page.write_text("<p>チャートなし</p>", encoding="utf-8")
            failures = vps.check_chart_data("sample", page, page.read_text(encoding="utf-8"))
            self.assertTrue(any("見つかりません" in f for f in failures), failures)


class BrokenReferenceTests(unittest.TestCase):
    def test_missing_local_image_is_reported(self) -> None:
        with TemporaryDirectory() as d:
            page = Path(d) / "sample-reaction-map.html"
            page.write_text('<img src="images/missing.webp">', encoding="utf-8")
            scrubbed = vps.blank_script_bodies(page.read_text(encoding="utf-8"))
            failures = vps.check_broken_references("sample", page, scrubbed)
            self.assertTrue(any("images/missing.webp" in f for f in failures), failures)

    def test_existing_local_image_with_query_string_passes(self) -> None:
        with TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "images").mkdir()
            (tmp / "images" / "ok.webp").write_bytes(b"x")
            page = tmp / "sample-reaction-map.html"
            page.write_text('<img src="images/ok.webp?v=1">', encoding="utf-8")
            scrubbed = vps.blank_script_bodies(page.read_text(encoding="utf-8"))
            failures = vps.check_broken_references("sample", page, scrubbed)
            self.assertEqual(failures, [])

    def test_js_string_concatenation_is_not_a_false_positive(self) -> None:
        with TemporaryDirectory() as d:
            page = Path(d) / "sample-reaction-map.html"
            page.write_text(
                "<script>const html = '<img src=\"'+imgPath+'\">';</script>",
                encoding="utf-8",
            )
            scrubbed = vps.blank_script_bodies(page.read_text(encoding="utf-8"))
            failures = vps.check_broken_references("sample", page, scrubbed)
            self.assertEqual(failures, [])

    def test_external_script_src_is_still_checked(self) -> None:
        with TemporaryDirectory() as d:
            page = Path(d) / "sample-reaction-map.html"
            page.write_text('<script src="missing.js">also ignored '+"'+x+'"+'</script>', encoding="utf-8")
            scrubbed = vps.blank_script_bodies(page.read_text(encoding="utf-8"))
            failures = vps.check_broken_references("sample", page, scrubbed)
            self.assertTrue(any("missing.js" in f for f in failures), failures)


class JsBuiltImageTests(unittest.TestCase):
    SNIPPET = (
        "<script>\n"
        'const xImgSlug = {"sample-a":"alpha"}[it.id];\n'
        "const xImgPath = xImgSlug ? ('images/topics/sample/sample-infographic-wide-'+xImgSlug+'.webp') : '';\n"
        "</script>"
    )

    def test_missing_slug_image_is_reported(self) -> None:
        with TemporaryDirectory() as d:
            page = Path(d) / "sample-reaction-map.html"
            page.write_text(self.SNIPPET, encoding="utf-8")
            failures = vps.check_js_built_images("sample", page, page.read_text(encoding="utf-8"))
            self.assertTrue(any("sample-a" in f for f in failures), failures)

    def test_existing_slug_image_passes(self) -> None:
        with TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "images" / "topics" / "sample").mkdir(parents=True)
            (tmp / "images" / "topics" / "sample" / "sample-infographic-wide-alpha.webp").write_bytes(b"x")
            page = tmp / "sample-reaction-map.html"
            page.write_text(self.SNIPPET, encoding="utf-8")
            failures = vps.check_js_built_images("sample", page, page.read_text(encoding="utf-8"))
            self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
