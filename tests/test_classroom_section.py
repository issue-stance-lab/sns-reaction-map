"""「授業・ディベートで使うとき」節（課題77 案2 Part B）の受け皿を固定する。

apply_classroom_section.py が生成した節が、次の3点を満たすことを守る。
1. 公開10テーマ（takaichi を除く）すべてにあり、ARTICLE_TRUST_START の直前にある
   （相対順序は共有アンカーへの後付けなので、テストで固定しないと次の更新で崩れうる）
2. 各理由の内部リンク（#issue-{id}）が、同じページに実在するアンカーへ向いている
3. 印刷ボタンとGA4イベント（classroom_print / classroom_link_click）が共有JSにある
"""

import json
import re
import unittest
from pathlib import Path

from scripts.seo.apply_classroom_section import public_theme_data, validate_config

ROOT = Path(__file__).resolve().parents[1]
SEO_CONFIG = json.loads((ROOT / "configs" / "theme-seo.json").read_text(encoding="utf-8"))
THEME_IDS = [str(theme["id"]) for theme in SEO_CONFIG["themes"]]
THEME_URLS = {str(theme["id"]): "docs/" + str(theme["url"]) for theme in SEO_CONFIG["themes"]}

CANONICAL_JS = ROOT / "docs" / "topic-modern.js"
CANONICAL_CSS = ROOT / "docs" / "topic-modern.css"
CLASSROOM_START = "<!-- CLASSROOM_START -->"
CLASSROOM_END = "<!-- CLASSROOM_END -->"
TRUST_START = "<!-- ARTICLE_TRUST_START -->"
ISSUE_LINK_RE = re.compile(r'href="#issue-([^"]+)"')
ISSUE_ID_RE = re.compile(r'id="issue-([^"]+)"')


class ClassroomConfigTests(unittest.TestCase):
    """設定ファイル（configs/classroom/*.json）そのものを固定する。"""

    def test_published_themes_all_have_config(self):
        """公開テーマ全10件に configs/classroom/{id}.json があること。"""
        self.assertGreaterEqual(len(THEME_IDS), 10)
        for theme_id in THEME_IDS:
            with self.subTest(theme=theme_id):
                path = ROOT / "configs" / "classroom" / f"{theme_id}.json"
                self.assertTrue(path.is_file(), f"{theme_id}: configがありません")

    def test_takaichi_is_out_of_scope(self):
        """takaichi は非掲載のため対象外（発注書 B-1）。"""
        self.assertNotIn("takaichi", THEME_IDS, "takaichiが公開テーマ台帳に含まれている(想定外)")
        self.assertFalse(
            (ROOT / "configs" / "classroom" / "takaichi.json").is_file(),
            "takaichi用のclassroom設定を作らないこと",
        )

    def test_configs_pass_validation(self):
        """理由・一次資料・問いの件数と issue_id の実在を検査する（apply_classroom_section.pyと同じ規則）。"""
        for theme_id in THEME_IDS:
            with self.subTest(theme=theme_id):
                config_path = ROOT / "configs" / "classroom" / f"{theme_id}.json"
                config = json.loads(config_path.read_text(encoding="utf-8"))
                theme_data = public_theme_data(theme_id)
                valid_issue_ids = {str(issue["id"]) for issue in theme_data.get("issues") or []}
                validate_config(theme_id, config, valid_issue_ids)  # raises on failure

    def test_reasons_are_not_duplicated_across_themes(self):
        """理由テキストがテーマ間でコピペされていないこと（発注書「理由・問い・一次資料はテーマごとに書き分ける」）。"""
        seen: dict[str, str] = {}
        for theme_id in THEME_IDS:
            config = json.loads((ROOT / "configs" / "classroom" / f"{theme_id}.json").read_text(encoding="utf-8"))
            for reason in config["reasons_pro"] + config["reasons_con"]:
                text = str(reason["text"])
                if text in seen:
                    self.fail(f"理由テキストが{seen[text]}と{theme_id}で重複: {text!r}")
                seen[text] = theme_id

    def test_questions_are_not_duplicated_across_themes(self):
        seen: dict[str, str] = {}
        for theme_id in THEME_IDS:
            config = json.loads((ROOT / "configs" / "classroom" / f"{theme_id}.json").read_text(encoding="utf-8"))
            for question in config["questions"]:
                if question in seen:
                    self.fail(f"問いが{seen[question]}と{theme_id}で重複: {question!r}")
                seen[question] = theme_id


class ClassroomPageTests(unittest.TestCase):
    """生成後の公開ページ（docs/*.html）を固定する。"""

    def test_pages_contain_classroom_section(self):
        for theme_id, url in THEME_URLS.items():
            with self.subTest(theme=theme_id):
                text = (ROOT / url).read_text(encoding="utf-8")
                self.assertIn(CLASSROOM_START, text, f"{theme_id}: 節が見つかりません")
                self.assertIn(CLASSROOM_END, text)
                self.assertIn('class="classroom-section"', text)
                self.assertIn('class="classroom-print-btn"', text)

    def test_classroom_precedes_article_trust(self):
        """相手（ARTICLE_TRUST_START）のマーカーの直前にあること（後付けブロックの相対順序）。"""
        for theme_id, url in THEME_URLS.items():
            with self.subTest(theme=theme_id):
                text = (ROOT / url).read_text(encoding="utf-8")
                classroom_index = text.index(CLASSROOM_START)
                trust_index = text.index(TRUST_START)
                self.assertLess(classroom_index, trust_index, f"{theme_id}: 節がARTICLE_TRUST_STARTより後ろにある")

    def test_takaichi_page_has_no_classroom_section(self):
        takaichi_path = ROOT / "docs" / "takaichi-reaction-map-standard.html"
        if takaichi_path.is_file():
            self.assertNotIn(CLASSROOM_START, takaichi_path.read_text(encoding="utf-8"))

    def test_internal_links_point_to_anchors_that_exist(self):
        """各理由の内部リンク先（#issue-{id}）が、同じページに実在すること。

        賛成側と反対側が同じ論点を指すことは許容する（同じ論点に賛否が分かれるのは自然）。
        固定するのはリンクの本数（賛成3+反対3=6）と、リンク先アンカーの実在。
        """
        for theme_id, url in THEME_URLS.items():
            with self.subTest(theme=theme_id):
                text = (ROOT / url).read_text(encoding="utf-8")
                section = text[text.index(CLASSROOM_START): text.index(CLASSROOM_END)]
                linked_ids = ISSUE_LINK_RE.findall(section)
                self.assertEqual(len(linked_ids), 6, f"{theme_id}: 賛成3+反対3=6件のリンク先があるはず")
                existing_ids = set(ISSUE_ID_RE.findall(text))
                missing = set(linked_ids) - existing_ids
                self.assertFalse(missing, f"{theme_id}: リンク先アンカーが実在しません: {missing}")

    def test_sources_link_to_http_urls(self):
        for theme_id, url in THEME_URLS.items():
            with self.subTest(theme=theme_id):
                text = (ROOT / url).read_text(encoding="utf-8")
                section = text[text.index(CLASSROOM_START): text.index(CLASSROOM_END)]
                source_block = section[section.index('classroom-sources'): section.index('classroom-questions')]
                hrefs = re.findall(r'href="(https?://[^"]+)"', source_block)
                self.assertEqual(len(hrefs), 3, f"{theme_id}: 一次資料は3件のはず")


class ClassroomAssetTests(unittest.TestCase):
    """共有JS/CSS（正典1本ずつ）を固定する。"""

    def test_js_has_hashchange_restore(self):
        """品質監査の推奨修正: 同一ページ内のhashchangeでも論点を選び直す。"""
        text = CANONICAL_JS.read_text(encoding="utf-8")
        self.assertIn("addEventListener('hashchange', citeRestoreFromHash)", text)

    def test_js_has_classroom_events(self):
        text = CANONICAL_JS.read_text(encoding="utf-8")
        self.assertIn("classroom-print-btn", text)
        self.assertIn("classroom_print", text)
        self.assertIn("classroom_link_click", text)

    def test_css_has_classroom_and_print_styles(self):
        text = CANONICAL_CSS.read_text(encoding="utf-8")
        self.assertIn(".classroom-section", text)
        self.assertIn("@media print", text)

    def test_css_link_rule_does_not_force_nowrap(self):
        """品質監査 2026-09-21: 375pxで一次資料の長いリンク文字が nowrap のため画面外へ切れていた。

        `.classroom-reasons a, .classroom-sources a` のルールに `white-space: nowrap` を
        戻さないことをテキストレベルで固定する（レイアウト検査は自動化できないため）。
        """
        text = CANONICAL_CSS.read_text(encoding="utf-8")
        match = re.search(
            r"\.classroom-reasons a,\s*\.classroom-sources a\s*\{([^}]*)\}", text
        )
        self.assertIsNotNone(match, "対象のCSSルールが見つかりません")
        rule_body = match.group(1)
        self.assertNotIn("white-space: nowrap", rule_body, "一次資料リンクのnowrapが復活しています")
        self.assertIn("overflow-wrap", rule_body)


if __name__ == "__main__":
    unittest.main()
