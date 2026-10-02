from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "review_with_yomiyasu.py"
SPEC = importlib.util.spec_from_file_location("review_with_yomiyasu", SCRIPT)
assert SPEC and SPEC.loader
reviewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reviewer)


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


if __name__ == "__main__":
    unittest.main()
