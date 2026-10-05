"""「意見の推移」の単体画像（scripts/build_trend_images.py）と、その検査（verify_trend_images.py）。

日本語フォントが無い環境（GitHub Actions）では、実際に描くテストを飛ばす。描かない部分
（指紋・図形・文言・検査・フォントが無いときに止まること）は常に回す。
"""

import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image
from PIL.PngImagePlugin import PngInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_trend_images as images  # noqa: E402
import build_trend_section as trend  # noqa: E402
import verify_trend_images as verify  # noqa: E402
from refresh_adapters import consumption_tax as adapter  # noqa: E402

SLUG = "consumption-tax-cut"
BASE = trend._theme_base(SLUG)
STANCES = BASE["stance_labels"]
ISSUES = BASE["issue_labels"]
NEEDS_FONT = unittest.skipUnless(images.fonts_available(), "日本語フォントが無い環境では描かない")


def row(day: str, stance: str, issue: str, index: int) -> dict:
    return {
        "tweet_id": str(1000 + index),
        "fetched_at": f"{day}T03:00:00.000Z",
        "classification": {"is_relevant": True, "is_opinion": True, "stance": stance, "main_issue": issue},
    }


def synthetic_rows() -> list[dict]:
    rows, index = [], 0
    for day, split in (("2026-09-01", 6), ("2026-09-08", 3), ("2026-09-15", 7)):
        for number in range(10):
            stance = STANCES[0] if number < split else STANCES[2]
            issue = ISSUES[number % len(ISSUES)]
            rows.append(row(day, stance, issue, index))
            index += 1
    return rows


def write(rows: list[dict], directory: Path) -> Path:
    path = directory / "classified.json"
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return path


class ShapesAndDigestTest(unittest.TestCase):
    def test_every_shape_becomes_points_matching_the_web_chart(self) -> None:
        self.assertIsNone(images.shape_points("circle"))
        self.assertEqual(len(images.shape_points("square")), 4)
        self.assertEqual(len(images.shape_points("diamond")), 4)
        self.assertEqual(len(images.shape_points("triangle")), 3)
        self.assertEqual(len(images.shape_points("triangle-down")), 3)
        self.assertEqual(len(images.shape_points("plus")), 12)
        for name in trend.SHAPE_PATHS:
            points = images.shape_points(name)
            if points:
                self.assertTrue(all(abs(x) <= 1.5 and abs(y) <= 1.5 for x, y in points), name)

    def test_square_points_are_the_unit_square(self) -> None:
        self.assertEqual(images.shape_points("square"), [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)])

    def test_digest_is_stable_and_changes_with_numbers_or_labels(self) -> None:
        rounds = [{"d": "2026-09-01", "n": 10, "v": [60.0, 40.0]}, {"d": "2026-09-08", "n": 10, "v": [30.0, 70.0]}]
        digest = images.series_digest(["賛成", "反対"], rounds)
        self.assertEqual(digest, images.series_digest(["賛成", "反対"], json.loads(json.dumps(rounds))))
        rounds[1]["v"] = [30.1, 69.9]
        self.assertNotEqual(digest, images.series_digest(["賛成", "反対"], rounds))
        self.assertNotEqual(digest, images.series_digest(["反対", "賛成"], rounds[:1] + rounds[1:]))

    def test_digest_matches_what_the_page_embeds(self) -> None:
        """ページの節に埋めるデータと、画像側の rounds_for_digest が同じ形になること。"""
        with tempfile.TemporaryDirectory() as tmp:
            path = write(synthetic_rows(), Path(tmp))
            series = trend.load_rounds(path, BASE, "stance")
            issue = trend.load_rounds(path, BASE, "issue")
            reason = trend.load_reasons(path, BASE, trend.TREND_THEMES[SLUG]["focus_stance"])
        section = trend.render_section(SLUG, series, issue, reason=reason, events=[])
        panels = verify.page_panels(section)
        mine = images.rounds_for_digest(series, STANCES)
        self.assertEqual(images.series_digest(panels["stance"]["labels"], panels["stance"]["rounds"]), images.series_digest(STANCES, mine))


class TextsTest(unittest.TestCase):
    def test_texts_reuse_the_page_headings_and_say_it_is_not_a_poll(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            series = trend.load_rounds(write(synthetic_rows(), Path(tmp)), BASE, "stance")
        texts = images.image_texts(SLUG, "stance", series)
        self.assertEqual(texts["title"], trend.TREND_THEMES[SLUG]["headings"]["stance"])
        self.assertEqual(texts["asof"], "2026年9月15日時点")
        self.assertIn("世論調査ではありません", texts["notes"][0])
        self.assertIn("9月1日〜9月15日の3回の収集", texts["period"])
        self.assertTrue(texts["notes"][1].startswith("各回の意見は"))

    def test_issue_image_says_other_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            series = trend.load_rounds(write(synthetic_rows(), Path(tmp)), BASE, "issue")
        texts = images.image_texts(SLUG, "issue", series)
        self.assertIn("「その他」を除く", texts["subtitle"])


class FontGuardTest(unittest.TestCase):
    def test_missing_fonts_stop_instead_of_drawing_boxes(self) -> None:
        with mock.patch.object(images, "FONT_CANDIDATES", (("/nonexistent/a.ttc", "/nonexistent/b.ttc"),)):
            with self.assertRaises(images.FontNotFound):
                images.find_fonts()
            self.assertFalse(images.fonts_available())
            with tempfile.TemporaryDirectory() as tmp:
                series = trend.load_rounds(write(synthetic_rows(), Path(tmp)), BASE, "stance")
            with self.assertRaises(images.FontNotFound):
                images.render_image(SLUG, "stance", series)

    def test_only_one_of_the_two_weights_is_not_enough(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            regular = Path(tmp) / "regular.ttc"
            regular.write_bytes(b"x")
            with mock.patch.object(images, "FONT_CANDIDATES", ((str(regular), "/nonexistent/bold.ttc"),)):
                self.assertFalse(images.fonts_available())


@NEEDS_FONT
class RenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = write(synthetic_rows(), Path(self.temp.name))

    def test_renders_the_shareable_size_with_metadata(self) -> None:
        paths = images.render_for(SLUG, self.source, Path(self.temp.name) / "out")
        self.assertEqual(set(paths), {"stance", "issue"})
        for kind, path in paths.items():
            self.assertEqual(path.name, trend.image_filename(SLUG, kind))
            with Image.open(path) as image:
                self.assertEqual(image.size, (1200, 675))
                self.assertEqual(image.mode, "P")  # 256色のPNG
                match = images.__dict__.get("DESCRIPTION_RE") or verify.DESCRIPTION_RE
                found = match.fullmatch(image.info["Description"])
                self.assertIsNotNone(found)
                self.assertEqual(found.group(1), "2026-09-15")
                self.assertEqual(found.group(2), kind)
                self.assertEqual(image.info["Author"], "SNS反応まっぷ")
                self.assertEqual(image.info["Source"], trend.page_url(SLUG))

    def test_same_input_gives_the_same_bytes(self) -> None:
        a = images.render_for(SLUG, self.source, Path(self.temp.name) / "a")
        b = images.render_for(SLUG, self.source, Path(self.temp.name) / "b")
        for kind in a:
            self.assertEqual(a[kind].read_bytes(), b[kind].read_bytes())

    def test_different_numbers_give_different_images(self) -> None:
        a = images.render_for(SLUG, self.source, Path(self.temp.name) / "a")
        rows = synthetic_rows()
        rows[0]["classification"]["stance"] = STANCES[2]
        other = Path(self.temp.name) / "other"
        other.mkdir()
        b = images.render_for(SLUG, write(rows, other), Path(self.temp.name) / "b")
        self.assertNotEqual(a["stance"].read_bytes(), b["stance"].read_bytes())

    def test_image_is_not_blank_and_uses_the_series_colors(self) -> None:
        path = images.render_for(SLUG, self.source, Path(self.temp.name) / "out")["stance"]
        with Image.open(path) as image:
            colors = {color for _, color in image.convert("RGB").getcolors(maxcolors=200000)}
        self.assertLess(path.stat().st_size, 150_000)  # 約3分の1に収める（RGBのままだと200KB超）
        self.assertGreater(len(colors), 50)
        green = trend.KINDS["stance"]["colors"][0].lstrip("#")
        target = tuple(int(green[i:i + 2], 16) for i in (0, 2, 4))
        self.assertTrue(any(all(abs(a - b) <= 12 for a, b in zip(color, target)) for color in colors))

    def test_adapter_builds_images_as_public_targets_twice_identically(self) -> None:
        stage = Path(self.temp.name) / "stage"
        targets = adapter._build_images(stage, self.source)
        self.assertEqual(sorted(path.name for path in targets), sorted(trend.image_filename(SLUG, kind) for kind in ("stance", "issue")))
        self.assertTrue(all(str(path).startswith("docs/images/trend/") for path in targets))
        self.assertTrue(all(source.is_file() for source in targets.values()))

    def test_adapter_stops_when_the_second_run_differs(self) -> None:
        stage = Path(self.temp.name) / "stage"
        original = images.render_for
        calls = {"n": 0}

        def flaky(slug: str, source: Path, outdir: Path) -> dict:
            result = original(slug, source, outdir)
            calls["n"] += 1
            if calls["n"] == 2:
                path = result["stance"]
                path.write_bytes(path.read_bytes() + b"x")
            return result

        with mock.patch.object(images, "render_for", flaky):
            with self.assertRaises(ValueError):
                adapter._build_images(stage, self.source)


class VerifyTest(unittest.TestCase):
    """verify_trend_images.check_theme を、合成のページと画像で動かす。"""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        with tempfile.TemporaryDirectory() as tmp:
            path = write(synthetic_rows(), Path(tmp))
            self.stance = trend.load_rounds(path, BASE, "stance")
            self.issue = trend.load_rounds(path, BASE, "issue")
            reason = trend.load_reasons(path, BASE, trend.TREND_THEMES[SLUG]["focus_stance"])
        section = trend.render_section(SLUG, self.stance, self.issue, reason=reason, events=[])
        self.page = self.root / BASE["html"]
        self.page.parent.mkdir(parents=True)
        self.page.write_text(f"<html><body>{section}</body></html>", encoding="utf-8")
        (self.root / trend.IMAGE_DIR).mkdir(parents=True)
        for kind, series in (("stance", self.stance), ("issue", self.issue)):
            self.write_png(kind, images.png_metadata(SLUG, kind, series))

    def write_png(self, kind: str, info: PngInfo, size: tuple[int, int] = trend.IMAGE_SIZE) -> None:
        Image.new("RGB", size, "white").save(self.root / trend.IMAGE_DIR / trend.image_filename(SLUG, kind), "PNG", pnginfo=info)

    def test_passes_when_images_match_the_page(self) -> None:
        self.assertEqual(verify.check_theme(SLUG, self.root), [])

    def test_missing_image_is_reported(self) -> None:
        (self.root / trend.IMAGE_DIR / trend.image_filename(SLUG, "issue")).unlink()
        problems = verify.check_theme(SLUG, self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("画像がありません", problems[0])

    def test_stale_collection_date_is_reported(self) -> None:
        info = PngInfo()
        description = images.png_metadata(SLUG, "stance", self.stance)  # 同じ指紋のまま日付だけ古い
        digest = images.series_digest(STANCES, images.rounds_for_digest(self.stance, STANCES))
        info.add_text("Description", f"asof=2026-09-08; kind=stance; sha256={digest}")
        self.write_png("stance", info)
        self.assertTrue(any("より古い" in p for p in verify.check_theme(SLUG, self.root)))
        self.assertIsNotNone(description)

    def test_changed_numbers_with_the_same_date_are_reported(self) -> None:
        info = PngInfo()
        info.add_text("Description", f"asof=2026-09-15; kind=stance; sha256={'0' * 64}")
        self.write_png("stance", info)
        self.assertTrue(any("数字がページの数字と一致しません" in p for p in verify.check_theme(SLUG, self.root)))

    def test_wrong_size_and_missing_fingerprint_are_reported(self) -> None:
        self.write_png("stance", PngInfo(), size=(800, 400))
        problems = verify.check_theme(SLUG, self.root)
        self.assertTrue(any("実寸" in p for p in problems))
        self.assertTrue(any("指紋" in p for p in problems))

    def test_page_without_the_image_reference_or_alt_date_is_reported(self) -> None:
        html = self.page.read_text(encoding="utf-8")
        self.page.write_text(html.replace("images/trend/consumption-tax-cut-stance-trend.png", "images/trend/other.png"), encoding="utf-8")
        self.assertTrue(any("<img>" in p for p in verify.check_theme(SLUG, self.root)))
        # alt の中の時点だけを消す（見出し・バッジなど他の場所の時点は残す）
        self.page.write_text(re.sub(r'(alt="[^"]*?)2026年9月15日時点', r"\1（時点なし", html), encoding="utf-8")
        self.assertTrue(any("alt" in p for p in verify.check_theme(SLUG, self.root)))

    def test_embed_code_must_point_at_the_image_url(self) -> None:
        html = self.page.read_text(encoding="utf-8")
        self.page.write_text(html.replace("https://sns-reaction-map.jp/images/trend/consumption-tax-cut-issue-trend.png", "https://example.jp/x.png"), encoding="utf-8")
        self.assertTrue(any("埋め込みコード" in p for p in verify.check_theme(SLUG, self.root)))

    def test_page_without_the_trend_data_is_reported(self) -> None:
        self.page.write_text("<html><body>節なし</body></html>", encoding="utf-8")
        self.assertTrue(verify.check_theme(SLUG, self.root))


class PublishedImagesTest(unittest.TestCase):
    """公開中のページと、docs/images/trend/ の画像が合っていること（公開CIでも回る）。"""

    def test_published_images_match_the_published_page(self) -> None:
        self.assertEqual(verify.check_theme(SLUG, ROOT), [])


if __name__ == "__main__":
    unittest.main()
