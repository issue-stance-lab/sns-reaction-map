"""公開データJSONをサイトへ置く経路の検査（課題77 案1、TASK_BOARD 課題77 A-1）。

data/public/ が正典、docs/data/ は build_public_registry.py が同じバイト列を書くだけの
配布先（手コピーしない）。ここでは非公開正典が無くても回せる範囲だけを確認する。
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path
from typing import Any

from scripts import public_registry_common as prc

ROOT = Path(__file__).resolve().parents[1]

# 投稿本文・投稿IDなど、SNS投稿そのものを特定・再現できるキー。
# public_registry_common.OCEAN_FORBIDDEN_KEYS と同じ考え方（ocean_layer限定ではなく全体に適用）。
RAW_POST_KEYS = {
    "tweet_id", "post_id", "post_ids", "excerpt", "representative_posts",
    "machine_hits", "match_rule", "body", "records", "raw_text", "full_text", "summary",
}
# 公開JSONで文字列として許容する最大長。2026-09-20時点の実測最長は277文字（編集部の横断整理の本文）。
# 生の投稿本文が紛れ込めば数百〜数千文字になるため、編集部の文章に十分な余裕を持たせつつ上限を置く。
MAX_STRING_LENGTH = 600


def _all_keys(node: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            keys.add(key)
            keys |= _all_keys(value)
    elif isinstance(node, list):
        for item in node:
            keys |= _all_keys(item)
    return keys


def _key_paths(node: Any, target: str, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child_path = f"{path}.{key}"
            if key == target:
                found.append(child_path)
            found.extend(_key_paths(value, target, child_path))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            found.extend(_key_paths(item, target, f"{path}[{index}]"))
    return found


def _max_string_length(node: Any) -> int:
    if isinstance(node, str):
        return len(node)
    if isinstance(node, dict):
        return max((_max_string_length(v) for v in node.values()), default=0)
    if isinstance(node, list):
        return max((_max_string_length(v) for v in node), default=0)
    return 0


class PublicDataDocsMirrorTests(unittest.TestCase):
    def setUp(self) -> None:
        if not prc.PUBLIC_THEMES_DIR.exists() or not any(prc.PUBLIC_THEMES_DIR.glob("*.json")):
            self.skipTest("data/public/themes/ が未生成（build_public_registry.py --all を先に実行する）")
        self.theme_jsons = prc.load_theme_json_files()

    def test_docs_mirror_exists_and_matches_byte_for_byte(self) -> None:
        for theme_id in self.theme_jsons:
            with self.subTest(theme=theme_id):
                source = prc.PUBLIC_THEMES_DIR / f"{theme_id}.json"
                mirror = prc.PUBLIC_DOCS_THEMES_DIR / f"{theme_id}.json"
                self.assertTrue(mirror.is_file(), f"{mirror} がありません")
                self.assertEqual(mirror.read_bytes(), source.read_bytes())

    def test_docs_catalog_mirror_matches_byte_for_byte(self) -> None:
        self.assertTrue(prc.PUBLIC_DOCS_CATALOG_PATH.is_file())
        self.assertTrue(prc.PUBLIC_CATALOG_PATH.is_file())
        self.assertEqual(
            prc.PUBLIC_DOCS_CATALOG_PATH.read_bytes(),
            prc.PUBLIC_CATALOG_PATH.read_bytes(),
        )

    def test_no_raw_post_fields(self) -> None:
        """投稿本文・投稿IDを特定できるキーを持ち込まない。"""
        for theme_id, data in self.theme_jsons.items():
            with self.subTest(theme=theme_id):
                leaked = _all_keys(data) & RAW_POST_KEYS
                self.assertEqual(leaked, set(), f"{theme_id}: 公開してはいけないキー: {leaked}")

    def test_text_key_appears_only_in_editorial_findings(self) -> None:
        """`text` というキー名自体は editorial_summary.findings[].text（編集部が書いた横断整理の
        本文、投稿本文ではない）にだけ許す。それ以外に出てきたら投稿本文の混入を疑う。"""
        for theme_id, data in self.theme_jsons.items():
            with self.subTest(theme=theme_id):
                for path in _key_paths(data, "text"):
                    self.assertRegex(path, r"^\$\.editorial_summary\.findings\[\d+\]\.text$")

    def test_string_length_is_bounded(self) -> None:
        for theme_id, data in self.theme_jsons.items():
            with self.subTest(theme=theme_id):
                longest = _max_string_length(data)
                self.assertLessEqual(
                    longest, MAX_STRING_LENGTH,
                    f"{theme_id}: {MAX_STRING_LENGTH}文字を超える文字列があります（投稿本文混入の疑い）",
                )

    def test_public_json_paths_are_not_in_sitemap(self) -> None:
        sitemap = (ROOT / "docs" / "sitemap.xml").read_text(encoding="utf-8")
        self.assertNotIn("/data/", sitemap)
        self.assertNotIn("llms.txt", sitemap)

    def test_llms_txt_is_not_in_sitemap_and_robots_allows_all(self) -> None:
        robots = (ROOT / "docs" / "robots.txt").read_text(encoding="utf-8")
        # AIクローラーを含め全許可のまま（塞ぐと引用される目的そのものが消える）。
        self.assertIn("User-agent: *", robots)
        self.assertIn("Allow: /", robots)
        self.assertNotIn("Disallow:", robots)


class LlmsTxtTests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = ROOT / "docs" / "llms.txt"
        if not self.path.is_file():
            self.skipTest("docs/llms.txt が未生成（generate_seo_assets.py を先に実行する）")
        self.text = self.path.read_text(encoding="utf-8")

    def test_starts_with_llmstxt_org_convention(self) -> None:
        lines = self.text.splitlines()
        self.assertEqual(lines[0], "# SNS反応まっぷ")
        self.assertTrue(lines[1] == "" and lines[2].startswith("> "))

    def test_lists_all_public_themes(self) -> None:
        theme_seo = prc.ROOT / "configs" / "theme-seo.json"
        import json
        themes = json.loads(theme_seo.read_text(encoding="utf-8"))["themes"]
        for theme in themes:
            with self.subTest(theme=theme["id"]):
                self.assertIn(theme["url"], self.text)

if __name__ == "__main__":
    unittest.main()
