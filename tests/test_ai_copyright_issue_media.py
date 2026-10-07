"""生成AIと著作権の「論点ごとのX投稿」（代表投稿 MEDIA）の検査。

2026-10-08、2026-09-05の回の判定を現行のAIで判定し直したとき、ページに固定で載せていた代表投稿14件のうち6件が、
新しい判定では別の論点・意見でない投稿になっていた（置き換え前は全件が一致していた）。数字の検査は、
このずれを検出しなかった。以後は、ここで次の3つを守る。

- 構造: 論点7つそれぞれに、重複のない2件。説明の一言が空でも長すぎもしない。
- ページとの同期: ページの該当セクションが、MEDIA から作った内容と一致する（MEDIAだけ直してページを直し忘れない）。
- 判定との一致（非公開の正典が要る。無い環境では飛ばす）: 載せた投稿は、いまの正典で、載せている論点の「意見」である。
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ai_copyright_issue_media as media  # noqa: E402

PAGE = ROOT / "docs" / "ai-copyright-reaction-map.html"
PUBLIC = json.loads((ROOT / "data" / "public" / "themes" / "ai-copyright.json").read_text(encoding="utf-8"))
LABEL_BY_KEY = {item["id"].removeprefix("ai-copyright-"): item["label"] for item in PUBLIC["issues"]}


class StructureTest(unittest.TestCase):
    def test_every_issue_has_exactly_two_distinct_posts(self) -> None:
        self.assertEqual(set(media.MEDIA), set(LABEL_BY_KEY))
        ids = [tweet_id for posts in media.MEDIA.values() for _, tweet_id, _ in posts]
        self.assertEqual(len(ids), 14)
        self.assertEqual(len(set(ids)), 14)
        for key, posts in media.MEDIA.items():
            self.assertEqual(len(posts), 2, key)

    def test_labels_and_users_are_filled_and_short(self) -> None:
        for key, posts in media.MEDIA.items():
            for user, tweet_id, label in posts:
                self.assertTrue(user and tweet_id.isdigit(), (key, user, tweet_id))
                self.assertTrue(label.strip(), (key, tweet_id))
                self.assertLessEqual(len(label), 24, f"{key}: 説明が長すぎます: {label}")


class PageSyncTest(unittest.TestCase):
    def test_the_page_section_matches_the_media_list(self) -> None:
        text = PAGE.read_text(encoding="utf-8")
        section = media.build_section(PUBLIC)
        self.assertEqual(media.inject(text, section), text, "ページの代表投稿が MEDIA と違います（--write-html で書き直す）")

    def test_every_listed_post_is_embedded_in_the_page(self) -> None:
        text = PAGE.read_text(encoding="utf-8")
        for posts in media.MEDIA.values():
            for user, tweet_id, _ in posts:
                self.assertIn(f"https://x.com/{user}/status/{tweet_id}", text)


class CurrentClassificationTest(unittest.TestCase):
    def setUp(self) -> None:
        import yaml

        themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
        canonical = ROOT / themes["ai-copyright"]["sample_file"]
        if not canonical.is_file():
            self.skipTest(f"非公開の正典がない環境: {canonical.name}")
        self.by_id = {str(row["tweet_id"]): row for row in json.loads(canonical.read_text(encoding="utf-8"))}

    def test_every_listed_post_is_an_opinion_in_the_issue_it_is_listed_under(self) -> None:
        for key, posts in media.MEDIA.items():
            for user, tweet_id, label in posts:
                row = self.by_id.get(tweet_id)
                self.assertIsNotNone(row, f"{key}: 正典に無い投稿です: {tweet_id}")
                classification = row["classification"]
                self.assertTrue(
                    classification.get("is_relevant") and classification.get("is_opinion"),
                    f"{key}: いまの判定では意見ではありません: {tweet_id}「{label}」",
                )
                self.assertEqual(
                    classification["main_issue"], LABEL_BY_KEY[key],
                    f"{key}: いまの判定では別の論点です: {tweet_id}「{label}」→ {classification['main_issue']}",
                )
                self.assertNotEqual(classification.get("risk"), "high", f"{key}: リスクが高い投稿です: {tweet_id}")

    def test_the_two_posts_of_an_issue_take_different_stances_where_possible(self) -> None:
        # 「考え方が分かれる2件」を載せる方針。同じ立場が2件並ぶ論点は、無いほうがよい（警告に留める）。
        same = [key for key, posts in media.MEDIA.items()
                if len({self.by_id[tweet_id]["classification"]["stance"] for _, tweet_id, _ in posts}) < 2]
        self.assertLessEqual(len(same), 1, f"立場が同じ2件になっている論点: {same}")


if __name__ == "__main__":
    unittest.main()
