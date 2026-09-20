"""「この論点を引用」ボタン（課題77 案1、TASK_BOARD 課題77 A-4）の検査。

tests/test_share_utm.py と同じ考え方: 挙動の正典は docs/topic-modern.js の
1箇所（citeButtonMarkup / cite_copy のイベント委譲）で、テーマごとのHTMLには
書かない。ここでは、正典にその実装がある・公開ページ側に受け皿（アンカー）が
あることだけを機械的に確かめる（実クリックの確認はブラウザでの手動確認）。
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "docs" / "topic-modern.js"
sys.path.insert(0, str(ROOT / "scripts"))


def _public_pages() -> list[Path]:
    """公開10テーマのページだけを返す（takaichiは非掲載のため対象外）。"""
    from scripts import public_registry_common as prc

    if not prc.PUBLIC_THEMES_DIR.exists() or not any(prc.PUBLIC_THEMES_DIR.glob("*.json")):
        return []
    return [
        ROOT / "docs" / data["page_path"]
        for data in prc.load_theme_json_files().values()
    ]


class CiteButtonJsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = CANONICAL.read_text(encoding="utf-8")

    def test_cite_copy_ga4_event_exists(self) -> None:
        self.assertIn("'cite_copy'", self.text)
        self.assertIn("theme_id", self.text)
        self.assertIn("issue_id", self.text)

    def test_button_markup_and_delegation_exist(self) -> None:
        self.assertIn("cite-copy-btn", self.text)
        self.assertIn("cite-copy-wrap", self.text)
        self.assertIn("cite-copy-toast", self.text)
        self.assertIn("data-cite-issue", self.text)

    def test_fetches_docs_data_themes_json(self) -> None:
        """テーマ名・論点名・更新年月・意見件数はdocs/data/themes/{id}.jsonから取る。"""
        self.assertIn("data/themes/", self.text)
        self.assertIn("updated_on", self.text)
        self.assertIn("opinion_count", self.text)

    def test_has_fallback_template_without_numbers(self) -> None:
        """fetch失敗時に数字なしの定型文へ落ちる経路があること。"""
        self.assertIn("catch", self.text)
        self.assertIn("SNS公開投稿サンプルの整理。社会全体の世論調査ではありません", self.text)

    def test_restores_selection_from_prefixed_hash_for_live_mode(self) -> None:
        """canvasが描ける環境（#fallbackが非表示）でも#issue-{id}が機能すること。"""
        self.assertIn("citeRestoreFromHash", self.text)
        self.assertIn("btn-", self.text)


class CiteAnchorReceptorTests(unittest.TestCase):
    """公開ページ側に、JSが引用ボタンを差し込める受け皿があることを確かめる。"""

    def test_public_pages_have_an_anchor_receptor(self) -> None:
        pages = _public_pages()
        if not pages:
            self.skipTest("data/public/themes/ が未生成（build_public_registry.py --all を先に実行する）")
        self.assertGreaterEqual(len(pages), 10)
        for page in pages:
            with self.subTest(page=page.name):
                text = page.read_text(encoding="utf-8")
                has_landing_anchor = 'class="issue-anchor"' in text
                has_issue_cards = re.search(r'<article class="ic" id="issue-', text) is not None
                self.assertTrue(
                    has_landing_anchor or has_issue_cards,
                    f"{page.name}: 引用ボタンの受け皿（issue-anchor / issue-cards）が無い",
                )

    def test_live_panel_container_exists_for_mutation_observer(self) -> None:
        """topic-modern.jsのMutationObserverが監視するdiv#panelが実在すること。"""
        pages = _public_pages()
        if not pages:
            self.skipTest("data/public/themes/ が未生成（build_public_registry.py --all を先に実行する）")
        for page in pages:
            text = page.read_text(encoding="utf-8")
            if 'class="issue-anchor"' not in text:
                continue  # issue-cardsのみのテーマはpanel監視の対象外
            with self.subTest(page=page.name):
                self.assertIn('id="panel"', text)
                self.assertIn('id="list"', text)


if __name__ == "__main__":
    unittest.main()
