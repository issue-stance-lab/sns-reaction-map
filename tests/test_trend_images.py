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

    def test_digest_changes_when_only_a_count_changes(self) -> None:
        """割合が同じでも件数が違えば、別のデータ（件数入りの画像が古いまま残らない）。"""
        a = [{"d": "2026-09-01", "n": 10, "v": [60.0, 40.0], "c": [6, 4]}]
        b = [{"d": "2026-09-01", "n": 20, "v": [60.0, 40.0], "c": [12, 8]}]
        self.assertNotEqual(images.series_digest(["賛成", "反対"], a), images.series_digest(["賛成", "反対"], b))

    def test_rounds_for_digest_carries_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            series = trend.load_rounds(write(synthetic_rows(), Path(tmp)), BASE, "stance")
        rounds = images.rounds_for_digest(series, STANCES)
        self.assertEqual(rounds[0]["c"], [series[0]["counts"][label] for label in STANCES])
        self.assertEqual(sum(rounds[0]["c"]), rounds[0]["n"])

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

    def test_detail_note_gives_the_latest_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            series = trend.load_rounds(write(synthetic_rows(), Path(tmp)), BASE, "stance")
        texts = images.image_texts(SLUG, "stance", series)
        self.assertIn(f"最新は{series[-1]['n']}件", texts["notes"][1])

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
            for variant in ("summary", "detail"):
                with self.assertRaises(images.FontNotFound):
                    images.render_image(SLUG, "stance", series, variant)

    def test_only_one_of_the_two_weights_is_not_enough(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            regular = Path(tmp) / "regular.ttc"
            regular.write_bytes(b"x")
            with mock.patch.object(images, "FONT_CANDIDATES", ((str(regular), "/nonexistent/bold.ttc"),)):
                self.assertFalse(images.fonts_available())


ALL = [(kind, variant) for kind in ("stance", "issue") for variant in ("summary", "detail")]


class SummaryHelpersTest(unittest.TestCase):
    def test_axis_always_starts_at_zero_with_a_few_ticks(self) -> None:
        self.assertEqual(images.summary_ceiling(51.4), (60, 20))
        self.assertEqual(images.summary_ceiling(44.1), (60, 20))
        self.assertEqual(images.summary_ceiling(40.0), (40, 10))
        self.assertEqual(images.summary_ceiling(29.0), (30, 10))
        self.assertEqual(images.summary_ceiling(3.0), (10, 10))
        for value in (3, 12.5, 29, 40, 41, 77, 99.9):
            ceiling, step = images.summary_ceiling(value)
            self.assertGreaterEqual(ceiling, value)
            self.assertLessEqual(ceiling / step, 6)

    def test_big_numbers_are_whole_percentages_rounded_half_up(self) -> None:
        self.assertEqual([images._half_up(v) for v in (37.9, 33.5, 48.9, 26.6, 0.4, 99.5)], [38, 34, 49, 27, 0, 100])


@NEEDS_FONT
class RenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = write(synthetic_rows(), Path(self.temp.name))

    def test_renders_both_variants_at_the_shareable_size_with_metadata(self) -> None:
        paths = images.render_for(SLUG, self.source, Path(self.temp.name) / "out")
        self.assertEqual(set(paths), set(ALL))
        for (kind, variant), path in paths.items():
            self.assertEqual(path.name, trend.image_filename(SLUG, kind, variant))
            with Image.open(path) as image:
                self.assertEqual(image.size, (1200, 675))
                self.assertEqual(image.mode, "P")  # 256色のPNG
                found = verify.DESCRIPTION_RE.fullmatch(image.info["Description"])
                self.assertIsNotNone(found)
                self.assertEqual(found.group(1), "2026-09-15")
                self.assertEqual(found.group(2), kind)
                self.assertEqual(found.group(3), variant)
                self.assertEqual(image.info["Author"], "SNS反応まっぷ")
                self.assertEqual(image.info["Source"], trend.page_url(SLUG))
                self.assertIn(trend.IMAGE_VARIANTS[variant]["name"], image.info["Title"])

    def test_both_variants_of_a_panel_carry_the_same_data_fingerprint(self) -> None:
        paths = images.render_for(SLUG, self.source, Path(self.temp.name) / "out")
        for kind in ("stance", "issue"):
            digests = set()
            for variant in ("summary", "detail"):
                with Image.open(paths[(kind, variant)]) as image:
                    digests.add(verify.DESCRIPTION_RE.fullmatch(image.info["Description"]).group(4))
            self.assertEqual(len(digests), 1, kind)

    def test_same_input_gives_the_same_bytes(self) -> None:
        a = images.render_for(SLUG, self.source, Path(self.temp.name) / "a")
        b = images.render_for(SLUG, self.source, Path(self.temp.name) / "b")
        for key in a:
            self.assertEqual(a[key].read_bytes(), b[key].read_bytes())

    def test_different_numbers_give_different_images(self) -> None:
        a = images.render_for(SLUG, self.source, Path(self.temp.name) / "a")
        rows = synthetic_rows()
        rows[0]["classification"]["stance"] = STANCES[2]
        other = Path(self.temp.name) / "other"
        other.mkdir()
        b = images.render_for(SLUG, write(rows, other), Path(self.temp.name) / "b")
        for variant in ("summary", "detail"):
            self.assertNotEqual(a[("stance", variant)].read_bytes(), b[("stance", variant)].read_bytes())

    def test_image_is_not_blank_and_uses_the_series_colors(self) -> None:
        paths = images.render_for(SLUG, self.source, Path(self.temp.name) / "out")
        green = trend.KINDS["stance"]["colors"][0].lstrip("#")
        target = tuple(int(green[i:i + 2], 16) for i in (0, 2, 4))
        for variant in ("summary", "detail"):
            path = paths[("stance", variant)]
            with Image.open(path) as image:
                colors = {color for _, color in image.convert("RGB").getcolors(maxcolors=200000)}
            self.assertLess(path.stat().st_size, 150_000, variant)  # RGBのままだと200KB超
            self.assertGreater(len(colors), 50)
            self.assertTrue(any(all(abs(a - b) <= 12 for a, b in zip(color, target)) for color in colors), variant)

    def test_summary_draws_only_the_two_picked_series(self) -> None:
        """合成データで動くのは「減税推進」と「減税反対・慎重」だけ。橙（条件付き賛成）は出ない。詳細版には出る。
        量子化（256色）の前の画像で、色が存在するかを見る。"""
        series = trend.load_rounds(self.source, BASE, "stance")
        orange = trend.KINDS["stance"]["colors"][1].lstrip("#")
        target = tuple(int(orange[i:i + 2], 16) for i in (0, 2, 4))

        def has_orange(variant: str) -> bool:
            colors = {color for _, color in images.render_image(SLUG, "stance", series, variant).getcolors(maxcolors=300000)}
            return target in colors

        self.assertFalse(has_orange("summary"))
        self.assertTrue(has_orange("detail"))

    def test_summary_text_stays_legible_when_shrunk_to_a_phone_timeline(self) -> None:
        """幅350pxに縮めても、見出しの行が読める太さで残る（暗い画素が、見出しの帯に十分ある）。"""
        path = images.render_for(SLUG, self.source, Path(self.temp.name) / "out")[("stance", "summary")]
        with Image.open(path) as image:
            small = image.convert("L").resize((350, 197), Image.LANCZOS)
        band = small.crop((10, 28, 340, 66))  # 見出し2行の帯（原寸の y 100〜230）
        dark = sum(1 for value in band.tobytes() if value < 110)
        self.assertGreater(dark / (band.width * band.height), 0.12)

    def test_longest_headlines_fit_at_the_minimum_font_size(self) -> None:
        """どの組み合わせの見出しも、最小の文字サイズで画像の幅に収まる（はみ出して切れない）。"""
        regular, bold = images.find_fonts()
        canvas = images.Canvas(regular, bold)
        for kind in ("stance", "issue"):
            labels = BASE[trend.KINDS[kind]["labels_key"]]
            for a in labels:
                for b in labels:
                    if a == b:
                        continue
                    for delta_b in (7.0, -7.0):
                        lines = trend.glance_lines(kind, [{"label": a, "delta": -9.0, "beyond": True}, {"label": b, "delta": delta_b, "beyond": True}])
                        for line in lines:
                            self.assertLessEqual(canvas.text_width(line, images.HEADLINE_MIN_SIZE, True), images.WIDTH - 56 * 2, line)

    def test_a_headline_that_cannot_fit_stops_instead_of_being_cut(self) -> None:
        series = trend.load_rounds(self.source, BASE, "stance")
        too_long = ["「" + "とても長い項目名" * 6 + "」の割合が下がった"]
        with mock.patch.object(trend, "glance_lines", return_value=too_long):
            with self.assertRaises(images.LayoutError):
                images.render_image(SLUG, "stance", series, "summary")

    def test_the_longest_realistic_headline_still_renders(self) -> None:
        series = trend.load_rounds(self.source, BASE, "stance")
        lines = [f"「{STANCES[1]}」と「{STANCES[2]}」の割合が、", "どちらも上がった"]
        with mock.patch.object(trend, "glance_lines", return_value=lines):
            image = images.render_image(SLUG, "stance", series, "summary")
        self.assertEqual(image.size, (1200, 675))

    def test_count_labels_stay_inside_the_image_even_for_large_numbers(self) -> None:
        """件数の桁が増えても（9999件）、右端の文字が画像の外へ出ない。現実の最大に近い割合（99%台）で見る。"""
        regular, bold = images.find_fonts()
        canvas = images.Canvas(regular, bold)
        label_x = 770 + 52  # ひと目版の右端の値の位置（px_last + 52）
        summary_right = label_x + 36 + canvas.text_width("99%", 54, True) + 12 + canvas.text_width("9999件", 26)
        self.assertLessEqual(summary_right, images.WIDTH - 40)
        detail_right = 1000 + 18 + canvas.text_width("99.9%", 21, True) + 9 + canvas.text_width("9999件", 16)
        self.assertLessEqual(detail_right, images.WIDTH - 24)

    def test_adapter_builds_images_as_public_targets_twice_identically(self) -> None:
        stage = Path(self.temp.name) / "stage"
        targets = adapter._build_images(stage, self.source)
        self.assertEqual(sorted(path.name for path in targets), sorted(trend.image_filename(SLUG, kind, variant) for kind, variant in ALL))
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
                path = result[("stance", "summary")]
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
            for variant in ("summary", "detail"):
                self.write_png(kind, images.png_metadata(SLUG, kind, series, variant), variant=variant)

    def write_png(self, kind: str, info: PngInfo, size: tuple[int, int] = trend.IMAGE_SIZE, variant: str = "detail") -> None:
        Image.new("RGB", size, "white").save(self.root / trend.IMAGE_DIR / trend.image_filename(SLUG, kind, variant), "PNG", pnginfo=info)

    def test_passes_when_images_match_the_page(self) -> None:
        self.assertEqual(verify.check_theme(SLUG, self.root), [])

    def test_missing_image_is_reported_for_each_variant(self) -> None:
        for variant in ("summary", "detail"):
            path = self.root / trend.IMAGE_DIR / trend.image_filename(SLUG, "issue", variant)
            path.unlink()
            problems = verify.check_theme(SLUG, self.root)
            self.assertEqual(len(problems), 1, variant)
            self.assertIn("画像がありません", problems[0])
            self.assertIn(variant, problems[0])
            self.write_png("issue", images.png_metadata(SLUG, "issue", self.issue, variant), variant=variant)
        self.assertEqual(verify.check_theme(SLUG, self.root), [])

    def test_stale_collection_date_is_reported(self) -> None:
        digest = images.series_digest(STANCES, images.rounds_for_digest(self.stance, STANCES))  # 同じ指紋のまま日付だけ古い
        for variant in ("summary", "detail"):
            info = PngInfo()
            info.add_text("Description", f"asof=2026-09-08; kind=stance; variant={variant}; sha256={digest}")
            self.write_png("stance", info, variant=variant)
            problems = verify.check_theme(SLUG, self.root)
            self.assertTrue(any("より古い" in p and variant in p for p in problems), variant)
            self.write_png("stance", images.png_metadata(SLUG, "stance", self.stance, variant), variant=variant)

    def test_changed_numbers_with_the_same_date_are_reported(self) -> None:
        info = PngInfo()
        info.add_text("Description", f"asof=2026-09-15; kind=stance; variant=summary; sha256={'0' * 64}")
        self.write_png("stance", info, variant="summary")
        self.assertTrue(any("数字がページの数字と一致しません" in p for p in verify.check_theme(SLUG, self.root)))

    def test_swapped_variants_are_reported(self) -> None:
        """ひと目版の場所に詳細版の画像を置いたら（種類の取り違え）、止める。"""
        self.write_png("stance", images.png_metadata(SLUG, "stance", self.stance, "detail"), variant="summary")
        self.assertTrue(any("画像の種類" in p for p in verify.check_theme(SLUG, self.root)))

    def test_wrong_size_and_missing_fingerprint_are_reported(self) -> None:
        self.write_png("stance", PngInfo(), size=(800, 400), variant="summary")
        problems = verify.check_theme(SLUG, self.root)
        self.assertTrue(any("実寸" in p for p in problems))
        self.assertTrue(any("指紋" in p for p in problems))

    def test_page_without_the_image_reference_or_alt_date_is_reported(self) -> None:
        html = self.page.read_text(encoding="utf-8")
        self.page.write_text(html.replace("images/trend/consumption-tax-cut-stance-trend-summary.png", "images/trend/other.png"), encoding="utf-8")
        self.assertTrue(any("<img>" in p for p in verify.check_theme(SLUG, self.root)))
        # alt の中の時点だけを消す（見出し・バッジなど他の場所の時点は残す）
        self.page.write_text(re.sub(r'(alt="[^"]*?)2026年9月15日時点', r"\1（時点なし", html), encoding="utf-8")
        self.assertTrue(any("alt" in p for p in verify.check_theme(SLUG, self.root)))

    def test_embed_code_must_point_at_the_image_url(self) -> None:
        html = self.page.read_text(encoding="utf-8")
        self.page.write_text(html.replace("https://sns-reaction-map.jp/images/trend/consumption-tax-cut-issue-trend-summary.png", "https://example.jp/x.png"), encoding="utf-8")
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
