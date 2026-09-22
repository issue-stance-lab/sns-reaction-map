"""論点ごとの固定リンク（課題77 案1、TASK_BOARD 課題77 A-3）の検査。

公開JSONの issues[].id（kind=named）と、公開ページの id="issue-{id}" が
全テーマ・全論点で一致し、かつページ内で重複しないことを確かめる。

6テーマ（ai-copyright / bike-blue-ticket / bukatsu-chiiki / consumption-tax-cut /
koshitsu-tenpakai / fukushuto）は #issue-cards（画像＋X投稿、*_issue_media.py 等が生成）が
既にこの id を使っているため、scripts/build_planet_data.py の「論点の一覧」
（static_fallback）側では新規に付けない（付けると同一ページでの id 重複になる）。
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# build_planet_data.py は `from public_registry_common import ...` という
# パッケージ相対でない書き方をしているため、scripts/ 自体を sys.path に足す
# （tests/test_planet_reread_registry.py 等と同じ既存の作法）。
sys.path.insert(0, str(ROOT / "scripts"))

from scripts import public_registry_common as prc
from scripts.build_planet_data import ISSUE_CARDS_OWNS_ANCHOR_ID
ANCHOR_RE = re.compile(r'id="(issue-[a-z0-9-]+)"')


class IssueAnchorTests(unittest.TestCase):
    def setUp(self) -> None:
        if not prc.PUBLIC_THEMES_DIR.exists() or not any(prc.PUBLIC_THEMES_DIR.glob("*.json")):
            self.skipTest("data/public/themes/ が未生成（build_public_registry.py --all を先に実行する）")
        self.theme_jsons = prc.load_theme_json_files()

    def _page_for(self, theme_id: str) -> Path:
        for candidate in (
            ROOT / "docs" / f"{theme_id}-reaction-map.html",
            ROOT / "docs" / f"{theme_id}-reaction-map-standard.html",
        ):
            if candidate.is_file():
                return candidate
        raise FileNotFoundError(f"{theme_id}: 公開ページが見つかりません")

    def test_every_named_issue_has_a_matching_anchor(self) -> None:
        for theme_id, data in self.theme_jsons.items():
            with self.subTest(theme=theme_id):
                html = self._page_for(theme_id).read_text(encoding="utf-8")
                present = set(ANCHOR_RE.findall(html))
                named_ids = {i["id"] for i in data["issues"] if i["kind"] == "named"}
                expected = {f"issue-{i}" for i in named_ids}
                missing = expected - present
                self.assertEqual(missing, set(), f"{theme_id}: アンカーが無い論点: {missing}")

    def test_no_duplicate_issue_anchor_ids(self) -> None:
        for theme_id in self.theme_jsons:
            with self.subTest(theme=theme_id):
                html = self._page_for(theme_id).read_text(encoding="utf-8")
                ids = ANCHOR_RE.findall(html)
                dupes = sorted({x for x in ids if ids.count(x) > 1})
                self.assertEqual(dupes, [], f"{theme_id}: id が重複しています: {dupes}")

    def test_issue_cards_themes_reuse_the_existing_anchor_not_a_new_one(self) -> None:
        """issue-cardsを持つ6テーマでは、論点の一覧側が新規にidを付けていないこと。

        静的フォールバックの生成器 static_fallback() 自体は非公開正典が要るため
        ここでは呼ばない。既に生成済みの公開ページから、issue-anchor要素が
        無いことだけを確認する（付けていれば重複IDになり、上のtestで検出される）。
        """
        for theme_id in ISSUE_CARDS_OWNS_ANCHOR_ID & set(self.theme_jsons):
            with self.subTest(theme=theme_id):
                html = self._page_for(theme_id).read_text(encoding="utf-8")
                self.assertNotIn('class="issue-anchor"', html)


if __name__ == "__main__":
    unittest.main()
