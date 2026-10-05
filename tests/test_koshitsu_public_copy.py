"""皇室典範ページに制作工程の説明が再生成されないことを守る。"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from bs4 import BeautifulSoup

from scripts import build_planet_data as planet
from scripts import koshitsu_connected as connected
from scripts.koshitsu_connected_content import reasons
from scripts.research_conditions import research_conditions_html
from scripts.seo import apply_theme_trust as trust

PAGE = ROOT / "docs/koshitsu-tenpakai-reaction-map.html"

UNWANTED_COPY = (
    "まだ編集部が投稿を1件ずつ読み直していません",
    "AIが自動でつけた区分",
    "人が読んだ結果だけ",
    "この論点の中身（編集部が本文を読んで分けたもの）",
    "ここから下は集計ではありません",
    "論点をまたいで言えることを、編集部がまとめています",
    "AIの下読みを含む",
    "AI分類。代表投稿は編集部が選定",
    "AIを使用した工程",
    "2026年8月まで、論点カードの一部",
    "図解には件数やパーセントを入れない方針",
)


class KoshitsuPublicCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.data = connected.planet_data(cls.html)

    def test_unwanted_process_copy_is_absent_from_public_html_and_templates(self):
        for text in UNWANTED_COPY:
            self.assertNotIn(text, self.html, text)

    def test_planet_generators_honor_the_theme_display_policy(self):
        self.assertTrue(self.data["hide_process_copy"])
        generated = "\n".join(
            (
                planet.static_caution(self.data),
                planet.static_fallback(self.data),
                planet.static_ocean(self.data),
                planet.static_editorial(self.data),
            )
        )
        for text in UNWANTED_COPY[:8]:
            self.assertNotIn(text, generated, text)

    def test_connected_reader_does_not_fill_an_unreviewed_issue_with_process_copy(self):
        self.assertEqual(reasons({"sub": {"status": "not_reviewed"}}), "")

    def test_regeneration_is_idempotent(self):
        config = json.loads((ROOT / "configs/theme-seo.json").read_text(encoding="utf-8"))
        theme = next(item for item in config["themes"] if item["id"] == "koshitsu-tenpakai")
        self.assertEqual(connected.apply(self.html), self.html)
        if not trust.sample_file_for(theme["id"]).is_file():
            self.skipTest("非公開正典がない環境ではSEO全体の再生成を行わない")
        self.assertEqual(trust.apply_theme(self.html, theme, config), self.html)

    def test_counts_review_state_posts_sources_and_storage_notice_remain(self):
        self.assertEqual(self.data["totals"], {"collected": 2565, "opinions": 2016})
        self.assertIn("収集した2,565件のうち意見と判定した2,016件", self.html)
        self.assertEqual(
            {item["label"]: item["count"] for item in self.data["issues"]},
            {
                "男系vs女系": 570,
                "旧宮家養子縁組": 347,
                "その他": 299,
                "立法手続き・民主主義": 281,
                "愛子さま・皇族の地位": 260,
                "女性天皇・女系天皇": 259,
            },
        )
        self.assertTrue(all(item["sub"]["status"] == "reread" for item in self.data["issues"]))
        self.assertEqual(
            [
                next(reason["count"] for reason in item["sub"]["items"] if reason["id"] == "__unread__")
                for item in self.data["issues"]
            ],
            [215, 120, 86, 80, 92, 74],
        )
        soup = BeautifulSoup(self.html, "html.parser")
        self.assertEqual(len(soup.select('template[id^="koshitsu-tenpakai-reading-"]')), 6)
        self.assertEqual(len(soup.select("[data-aic-post-url]")), 12)
        self.assertTrue(soup.select(".aic-sources a[href]"))
        self.assertIn("回答と、24時間の重複防止用に一方向変換した接続元情報をサーバーに保存します。", self.html)

    def test_other_themes_keep_the_shared_review_note_by_default(self):
        default = research_conditions_html("10", "2026-09-01〜2026-09-02")
        hidden = research_conditions_html(
            "10", "2026-09-01〜2026-09-02", show_review_note=False
        )
        self.assertIn("AI分類。代表投稿は編集部が選定", default)
        self.assertNotIn("AI分類。代表投稿は編集部が選定", hidden)


if __name__ == "__main__":
    unittest.main()
