"""シェア導線のUTMが全経路で付いていることを守る。

2026-08-10 まで、サイト上のシェアボタンが作るURLにUTMが1つも付いていなかった。
そのためGA4では t.co / referral にまとまり、どの導線からの流入か区別できず、
GROWTH.yaml の share-after-vote 施策は「流入0件」のまま永久に判定できない状態だった。
（0件は施策の失敗ではなく、計測が存在しなかったということ）

共有URL生成は次の4か所に分かれている。正典は docs/topic-modern.js の
window.buildShareUrl で、他はそれを呼ぶか、同等のUTMを持つ保険を置く。
1か所だけ直すと、新しいテーマページを作ったときだけ挙動が変わる。
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CANONICAL = ROOT / "docs" / "topic-modern.js"
FAB = ROOT / "docs" / "share-x-btn.js"
LEGACY_VOTE2D = ROOT / "docs" / "vote2d.js"
BUILDER = ROOT / "scripts" / "build_reaction_map.py"

# 共有URLを組み立てている全ファイル。増やしたらここにも足すこと
SHARE_URL_SITES = (CANONICAL, FAB, LEGACY_VOTE2D, BUILDER)

EXPECTED_CAMPAIGNS = {"fab_share", "vote_share"}


class ShareUtmTest(unittest.TestCase):
    def test_canonical_helper_exists(self):
        """正典の window.buildShareUrl が topic-modern.js にあること。"""
        text = CANONICAL.read_text(encoding="utf-8")
        self.assertIn("window.buildShareUrl", text)
        self.assertIn("utm_source", text)
        self.assertIn("share_button", text)
        self.assertIn("window.trackShareClick", text)

    def test_canonical_helper_strips_hash_and_keeps_query(self):
        """ハッシュを落とし、既存クエリを壊さない実装であること。"""
        text = CANONICAL.read_text(encoding="utf-8")
        helper = text[text.index("window.buildShareUrl") : text.index("window.trackShareClick")]
        self.assertIn("new URL(", helper, "URL APIを使わないと既存クエリを壊す")
        self.assertIn("url.hash = ''", helper, "ハッシュを落としていない")
        self.assertIn("searchParams.set", helper)

    def test_every_share_url_site_carries_utm(self):
        """intent/tweet を組み立てる全箇所がUTMを持つこと。

        どれか1つでもUTMなしだと、その導線の流入は t.co にまとまって識別できない。
        """
        for path in SHARE_URL_SITES:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn("intent/tweet", text, "共有URL生成が消えている")
                self.assertIn(
                    "utm_source=share_button" if path is not CANONICAL else "utm_source",
                    text,
                    f"{path.name} の共有URLにUTMが無い",
                )

    def test_campaign_names_are_distinguishable(self):
        """FAB経由と投票後経由をGA4で分けられること。"""
        fab = FAB.read_text(encoding="utf-8")
        canonical = CANONICAL.read_text(encoding="utf-8")
        self.assertIn("fab_share", fab)
        self.assertIn("vote_share", canonical)
        self.assertNotIn("fab_share", canonical.replace("window.buildShareUrl", ""),
                         "投票後シェアがFAB用のcampaignを使っている")

    def test_click_events_are_sent_for_both_paths(self):
        """『押されていない』と『押されたが流入しない』を区別できること。

        UTMは流入しか測れない。Xの投稿画面は別サイトなので、クリック自体を
        GA4へ送らないと、ボタンが無視されているのか離脱しているのか分からない。
        """
        self.assertIn("trackShareClick('fab_share')", FAB.read_text(encoding="utf-8"))
        self.assertIn("trackShareClick('vote_share')", CANONICAL.read_text(encoding="utf-8"))

    def test_fab_has_fallback_when_canonical_missing(self):
        """topic-modern.js が読めなかった場合もUTMが付くこと。"""
        text = FAB.read_text(encoding="utf-8")
        self.assertIn("window.buildShareUrl||", text.replace(" ", ""),
                      "正典を参照していない、または保険が無い")

    def test_no_share_site_uses_bare_url(self):
        """og:url や location.href をそのまま渡している箇所が残っていないこと。"""
        bare = re.compile(r"encodeURIComponent\(\s*(ogUrl|location\.href)\s*\)")
        for path in (CANONICAL, FAB, LEGACY_VOTE2D):
            with self.subTest(path=path.name):
                hits = bare.findall(path.read_text(encoding="utf-8"))
                self.assertEqual(hits, [], f"{path.name} がUTMなしのURLを共有している")

    def test_published_pages_load_the_canonical_helper(self):
        """公開ページが topic-modern.js を読み込んでいること（正典の配布経路）。"""
        pages = sorted((ROOT / "docs").glob("*-reaction-map*.html"))
        self.assertGreaterEqual(len(pages), 10)
        for page in pages:
            with self.subTest(page=page.name):
                self.assertRegex(
                    page.read_text(encoding="utf-8"),
                    r'<script[^>]+src="topic-modern\.js',
                    "正典が届かないページがある",
                )

    def test_fab_pages_load_canonical_first(self):
        """share-x-btn.js より topic-modern.js を先に読むこと（保険に頼らないため）。"""
        for page in sorted((ROOT / "docs").glob("*-reaction-map*.html")):
            text = page.read_text(encoding="utf-8")
            if "share-x-btn.js" not in text:
                continue
            with self.subTest(page=page.name):
                self.assertLess(
                    text.index("topic-modern.js"),
                    text.index("share-x-btn.js"),
                    "読み込み順が逆で、FABが毎回フォールバックを使う",
                )


if __name__ == "__main__":
    unittest.main()
