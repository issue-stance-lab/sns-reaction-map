from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "review_with_yomiyasu.py"
SPEC = importlib.util.spec_from_file_location("review_with_yomiyasu", SCRIPT)
assert SPEC and SPEC.loader
reviewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reviewer)

# 2026-10-03にnote第3回を書いていて見つけた穴。上流リンターだけでは、この3行が100点・指摘0件で通っていた。
# 1行目はダッシュ記号（U+2015）を2か所、2行目は107字で読点6個、3行目は読点5個。
EXPERIMENT_LINES = (
    "消費税の減税――つまり税率を下げること――をめぐって、賛成と反対の投稿が並びました。",
    "減税の効果について、減税に賛成する人は、値上げが続いても、減税がなければもっと高かったと考え、"
    "減税に反対する人は、値札が下がらないなら意味がないと考え、どちらも毎日の暮らしの負担が軽くなるかどうかを気にしています。",
    "今回の分類では、賛成が最も多く、次に条件付き賛成が、そのあとに反対と慎重が、最後に中立と情報が続きます、という並びでした。",
)
DASHES = {"U+2014": "—", "U+2015": "―", "U+2500": "─", "U+2013": "–"}


def review_text(text: str, medium: str = "seo", name: str = "sample.md") -> dict:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / name
        path.write_text(text, encoding="utf-8")
        return reviewer.review(path, medium)


def findings_for(result: dict, rule: str, severity: str | None = None) -> list[dict]:
    return [
        item
        for item in result["findings"]
        if item["rule"] == rule and (severity is None or item["severity"] == severity)
    ]


def sentence_with_commas(count: int) -> str:
    return "、".join(["果物"] * (count + 1)) + "を買いました。"


class YomiyasuReviewTests(unittest.TestCase):
    def test_note_checks_only_public_body(self) -> None:
        text = "内部メモ：\n👉 内部だけ\n\n---\n\n公開本文です。"
        self.assertEqual(reviewer.note_body(text), "公開本文です。")

    def test_frontmatter_is_removed_without_dropping_body(self) -> None:
        text = "---\ntitle: sample\n---\n\n本文です。"
        self.assertEqual(reviewer.note_body(text), "本文です。")

    def test_required_negative_comparison_is_non_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "article-FINAL.md"
            path.write_text("---\n\n世論調査ではなく、SNS投稿のサンプルです。", encoding="utf-8")
            result = reviewer.review(path, "note")
        self.assertTrue(result["passed"])
        self.assertTrue(any(item["rule"] == "negative_parallelism" for item in result["findings"]))

    def test_emoji_in_public_body_blocks_completion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "article-FINAL.md"
            path.write_text("---\n\n👉 詳細を見る", encoding="utf-8")
            result = reviewer.review(path, "note")
        self.assertFalse(result["passed"])
        self.assertGreater(result["blocking_count"], 0)

    def test_urls_and_numbers_are_protected(self) -> None:
        before = "2026年に100件、34.0兆円を確認。https://example.com/a"
        after = "2026年に99件、34.1兆円を確認。https://example.com/b"
        failures = reviewer.compare_protected(before, after, ["urls", "numbers"])
        self.assertEqual(len(failures), 2)

    def test_website_checks_visible_editorial_paragraphs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "article.html"
            path.write_text(
                "<main><h2>論点</h2><p>👉 これは公開本文に含まれる十分な長さの説明文です。</p></main>",
                encoding="utf-8",
            )
            result = reviewer.review(path, "website")
        self.assertFalse(result["passed"])
        self.assertGreater(result["blocking_count"], 0)


class MechanicalChecksTests(unittest.TestCase):
    """上流リンターが見ない項目（ダッシュ記号・1文の読点・文の長さ）をラッパーが止める。"""

    def test_three_line_experiment_fails_in_strict_mode(self) -> None:
        self.assertEqual(len(EXPERIMENT_LINES[1]), 107)
        self.assertEqual(EXPERIMENT_LINES[1].count("、"), 6)
        self.assertEqual(EXPERIMENT_LINES[2].count("、"), 5)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "experiment.md"
            path.write_text("\n".join(EXPERIMENT_LINES) + "\n", encoding="utf-8")
            command = [sys.executable, str(SCRIPT), str(path), "--medium", "seo"]
            strict = subprocess.run([*command, "--strict"], capture_output=True, text=True, encoding="utf-8")
            as_json = subprocess.run([*command, "--json", "--strict"], capture_output=True, text=True, encoding="utf-8")
            lenient = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
            result = reviewer.review(path, "seo")
        self.assertEqual(strict.returncode, 1, strict.stdout)
        self.assertIn("判定: 要修正", strict.stdout)
        self.assertEqual(as_json.returncode, 1)
        self.assertEqual(json.loads(as_json.stdout)["blocking_count"], result["blocking_count"])
        self.assertEqual(lenient.returncode, 0, "--strict を付けなければ終了コードは0")
        self.assertEqual([item["line"] for item in findings_for(result, "dash_prohibited", "warn")], [1])
        self.assertEqual([item["line"] for item in findings_for(result, "comma_count", "warn")], [2, 3])
        self.assertEqual([item["line"] for item in findings_for(result, "sentence_too_long", "warn")], [2])

    def test_each_dash_character_blocks_completion(self) -> None:
        for code_point, dash in DASHES.items():
            with self.subTest(code_point):
                result = review_text(f"減税{dash}{dash}税率を下げること{dash}{dash}をめぐる投稿です。")
                self.assertFalse(result["passed"])
                self.assertEqual(len(findings_for(result, "dash_prohibited", "warn")), 1)

    def test_long_vowel_mark_is_not_a_dash(self) -> None:
        result = review_text("コーヒーとサーバーの話です。長音記号のーーも、ダッシュではありません。")
        self.assertEqual(findings_for(result, "dash_prohibited"), [])

    def test_dash_in_frontmatter_and_code_is_ignored(self) -> None:
        text = (
            "---\ntitle: a――b\n---\n\n"
            "本文です。\n\n"
            "```\ncode — sample\n```\n\n"
            "`x—y`と書きます。\n"
        )
        self.assertEqual(findings_for(review_text(text), "dash_prohibited"), [])

    def test_dash_is_checked_even_on_lines_exempt_from_length(self) -> None:
        for line in ("## 見出し――です", "・箇条書き――です", "データについて：注記――です。",
                     "https://example.com/a–b"):
            with self.subTest(line=line):
                result = review_text(f"---\n\n本文です。\n\n{line}", "note", "a-FINAL.md")
                self.assertEqual(len(findings_for(result, "dash_prohibited", "warn")), 1)

    def test_note_checks_dash_only_after_the_separator(self) -> None:
        before = review_text("内部メモ――です。\n\n---\n\n公開本文です。", "note", "a-FINAL.md")
        after = review_text("内部メモです。\n\n---\n\n公開――本文です。", "note", "a-FINAL.md")
        self.assertEqual(findings_for(before, "dash_prohibited"), [])
        self.assertEqual(len(findings_for(after, "dash_prohibited", "warn")), 1)

    def test_website_body_is_checked_for_dashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "article.html"
            path.write_text(
                "<main><h2>論点</h2><p>賛成と反対――これは公開本文に含まれる十分な長さの説明文です。</p></main>",
                encoding="utf-8",
            )
            result = reviewer.review(path, "website")
        self.assertFalse(result["passed"])
        self.assertEqual(len(findings_for(result, "dash_prohibited", "warn")), 1)

    def test_comma_count_thresholds(self) -> None:
        expected = {0: None, 2: None, 3: "info", 4: "warn", 5: "warn"}
        for commas, severity in expected.items():
            with self.subTest(commas=commas):
                result = review_text(sentence_with_commas(commas))
                found = findings_for(result, "comma_count")
                self.assertEqual([item["severity"] for item in found], [severity] if severity else [])
                self.assertEqual(result["passed"], severity != "warn")

    def test_sentence_length_threshold(self) -> None:
        at_limit = review_text("あ" * 79 + "。")
        over_limit = review_text("あ" * 80 + "。")
        self.assertEqual(findings_for(at_limit, "sentence_too_long"), [])
        self.assertTrue(at_limit["passed"])
        self.assertEqual(len(findings_for(over_limit, "sentence_too_long", "warn")), 1)
        self.assertFalse(over_limit["passed"])

    def test_average_sentence_length_is_info_only(self) -> None:
        expected = {24: "info", 25: None, 40: None, 55: None, 56: "info"}
        for length, severity in expected.items():
            with self.subTest(length=length):
                result = review_text("\n".join(["あ" * (length - 1) + "。"] * 3))
                found = findings_for(result, "average_sentence_length")
                self.assertEqual([item["severity"] for item in found], [severity] if severity else [])
                self.assertTrue(result["passed"], "平均文長だけでは完成を止めない")

    def test_sentence_metrics_are_reported(self) -> None:
        result = review_text("\n".join(["あ" * 9 + "。", "い" * 19 + "。", "う" * 29 + "。"]))
        metrics = result["sentence_metrics"]
        self.assertEqual(metrics["sentences"], 3)
        self.assertEqual(metrics["average"], 20.0)
        self.assertEqual((metrics["longest"], metrics["longest_line"]), (30, 3))
        self.assertEqual(metrics["target"], [30, 45])

    def test_average_is_not_judged_for_x(self) -> None:
        text = "\n".join(["あ" * 9 + "。", "い" * 19 + "。", "う" * 29 + "。"])
        self.assertEqual(len(findings_for(review_text(text, "seo"), "average_sentence_length")), 1)
        self.assertEqual(findings_for(review_text(text, "x"), "average_sentence_length"), [])

    def test_commas_and_length_are_still_checked_for_x(self) -> None:
        self.assertEqual(len(findings_for(review_text(sentence_with_commas(4), "x"), "comma_count", "warn")), 1)
        self.assertEqual(len(findings_for(review_text("あ" * 80 + "。", "x"), "sentence_too_long", "warn")), 1)

    def test_text_without_countable_sentences(self) -> None:
        text = "## 見出しだけ\n\n- 箇条書きだけ\n"
        result = review_text(text)
        self.assertEqual(result["sentence_metrics"]["sentences"], 0)
        self.assertIsNone(result["sentence_metrics"]["average"])
        self.assertEqual(findings_for(result, "average_sentence_length"), [])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "headings-only.md"
            path.write_text(text, encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--medium", "seo", "--strict"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("数える文がありません", completed.stdout)

    def test_exempt_lines_are_not_counted(self) -> None:
        heavy = "、".join(["あいうえおかきくけこ"] * 12) + "。"  # 132字、読点11個
        exempt = [
            f"## {heavy}",
            f"- {heavy}",
            f"1. {heavy}",
            f"・{heavy}",
            "https://example.com/" + "a" * 120,
            f"▼［画像を挿入］{heavy}",
            f"データについて：{heavy}",
            f"制度についての記述と出典：{heavy}",
            f"> {heavy}",
            f"| {heavy} |",
        ]
        body = "\n\n".join([*exempt, "本文はここだけです。"])
        result = review_text("---\n\n" + body, "note", "a-FINAL.md")
        self.assertEqual(findings_for(result, "comma_count"), [])
        self.assertEqual(findings_for(result, "sentence_too_long"), [])
        self.assertEqual(result["sentence_metrics"]["sentences"], 1)
        control = review_text("---\n\n" + heavy, "note", "a-FINAL.md")
        self.assertEqual(len(findings_for(control, "comma_count", "warn")), 1)
        self.assertEqual(len(findings_for(control, "sentence_too_long", "warn")), 1)

    def test_inline_urls_do_not_count_toward_length(self) -> None:
        url = "https://example.com/" + "a" * 100
        result = review_text(f"詳しくは{url}を見てください。\n[リンク]({url})です。")
        self.assertEqual(findings_for(result, "sentence_too_long"), [])
        self.assertLess(result["sentence_metrics"]["longest"], 20)

    def test_closing_bracket_after_period_stays_in_the_sentence(self) -> None:
        settings = reviewer.mechanical_settings(reviewer.load_config())
        sentences = reviewer.split_sentences("「効果はない。」と言う人もいます。次の文です。", settings)
        self.assertEqual([text for _line, text in sentences], ["「効果はない。」と言う人もいます。", "次の文です。"])

    def test_thresholds_come_from_the_config(self) -> None:
        config = copy.deepcopy(reviewer.load_config())
        config["mechanical_checks"].update(comma_warn_at=2, sentence_warn_over=15, dash_chars=["〜"])
        with mock.patch.object(reviewer, "load_config", return_value=config):
            two_commas = review_text(sentence_with_commas(2))
            long_sentence = review_text("あ" * 15 + "。")
            wave_dash = review_text("東京〜大阪の話です。")
            default_dash = review_text("東京――大阪の話です。")
        self.assertEqual([item["severity"] for item in findings_for(two_commas, "comma_count")], ["warn"])
        self.assertEqual(len(findings_for(long_sentence, "sentence_too_long", "warn")), 1)
        self.assertEqual(len(findings_for(wave_dash, "dash_prohibited", "warn")), 1)
        self.assertEqual(findings_for(default_dash, "dash_prohibited"), [])

    def test_missing_settings_stop_with_a_clear_message(self) -> None:
        config = copy.deepcopy(reviewer.load_config())
        del config["mechanical_checks"]["comma_warn_at"]
        with self.assertRaises(SystemExit) as missing_key:
            reviewer.mechanical_settings(config)
        self.assertIn("comma_warn_at", str(missing_key.exception))
        del config["mechanical_checks"]
        with self.assertRaises(SystemExit) as missing_section:
            reviewer.mechanical_settings(config)
        self.assertIn("mechanical_checks", str(missing_section.exception))

    def test_score_includes_the_new_findings(self) -> None:
        for text in ("東京――大阪の話です。", "👉 東京――大阪の話です。"):
            with self.subTest(text=text):
                result = review_text(text)
                penalty = sum(5 if item["severity"] in ("warn", "error") else 2 for item in result["findings"])
                self.assertEqual(result["score"], 100 - penalty)
                self.assertLess(result["score"], 100)


if __name__ == "__main__":
    unittest.main()
