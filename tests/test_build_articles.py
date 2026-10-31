"""サイト内記事の生成器（scripts/build_articles.py）の約束を押さえる（課題51）。

公開データ（data/public/）だけを読むので、非公開の正典が無い CI でも回る。
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_articles  # noqa: E402
from unify_site_chrome import FOOTER_LINKS  # noqa: E402

THEME = "bukatsu-chiiki"
PUBLIC = json.loads((ROOT / "data" / "public" / "themes" / f"{THEME}.json").read_text(encoding="utf-8"))
ISSUE = next(i for i in PUBLIC["issues"] if i["label"] == "費用・家庭負担")
CAUTIOUS = next(s["count"] for s in ISSUE["stances"] if s["id"].endswith("-cautious"))

BASE_META = """slug: {slug}
theme: bukatsu-chiiki
title: テスト用の記事
description: 費用の論点の意見は{{{{issue:費用・家庭負担}}}}件です。
published_on: 2026-10-17
updated_on: 2026-10-17
link_label: テストの問い？
link_answer: テストの答えです
sources:
  - name: テスト資料
    url: https://www.mext.go.jp/
    checked_on: 2026-10-14
"""


class ArticleBuildTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.src = root / "content" / "articles"
        (self.src / THEME).mkdir(parents=True)
        self.out = root / "docs" / "articles"
        patches = [
            mock.patch.object(build_articles, "SRC_DIR", self.src),
            mock.patch.object(build_articles, "OUT_DIR", self.out),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)

    def write(self, slug: str, body: str, extra_meta: str = "") -> None:
        text = "---\n" + BASE_META.format(slug=slug) + extra_meta + "---\n" + body
        (self.src / THEME / f"{slug}.md").write_text(text, encoding="utf-8")

    def build_one(self, slug: str) -> str:
        outputs = build_articles.build()
        return outputs[self.out / f"{slug}.html"]

    def test_related_issue_links_follow_answer_before_toc(self) -> None:
        self.write("a-test", "最初の回答。\n\n## 見出し1\n\n本文。\n\n## 見出し2\n\n本文。\n\n## 見出し3\n\n本文。\n",
                   "related_issues:\n  - bukatsu-chiiki-hiyo\n")
        page = self.build_one("a-test")
        self.assertLess(page.index("最初の回答。</p>"), page.index('class="issue-entry'))
        self.assertLess(page.index('class="issue-entry'), page.index('class="toc'))
        self.assertIn('href="../bukatsu-chiiki-reaction-map.html#issue-bukatsu-chiiki-hiyo"', page)
        self.assertIn('data-article-link="theme-issue"', page)

    def test_unknown_related_issue_stops_build(self) -> None:
        self.write("a-test", "最初の回答。\n", "related_issues:\n  - another-theme-missing\n")
        with self.assertRaisesRegex(build_articles.BuildError, "テーマに無い論点ID"):
            self.build_one("a-test")

    def test_numbers_come_from_public_data(self) -> None:
        self.write("a-test", "リードです。\n\n## 見出し\n\n慎重・反対は{{issue:費用・家庭負担:慎重・反対}}件でした。\n")
        page = self.build_one("a-test")
        self.assertIn(f"慎重・反対は{CAUTIOUS}件でした。", page)
        self.assertIn(f"費用の論点の意見は{ISSUE['count']}件です。", page)
        self.assertNotIn("{{", page)

    def test_assert_stops_when_data_contradicts_text(self) -> None:
        self.write(
            "a-test",
            "本文。\n",
            extra_meta='asserts:\n  - "{{issue:費用・家庭負担:慎重・反対}} > {{issue:費用・家庭負担}}"\n',
        )
        with self.assertRaises(build_articles.BuildError):
            build_articles.build()

    def test_unknown_issue_label_stops(self) -> None:
        self.write("a-test", "件数は{{issue:存在しない論点}}件。\n")
        with self.assertRaises(build_articles.BuildError):
            build_articles.build()

    def test_raw_html_in_body_stops(self) -> None:
        self.write("a-test", "<div>手書きのHTML</div>\n")
        with self.assertRaises(build_articles.BuildError):
            build_articles.build()

    def test_chart_lists_every_stance_with_counts(self) -> None:
        self.write("a-test", "本文。\n\n[[chart:費用・家庭負担]]\n")
        page = self.build_one("a-test")
        for stance in ("移行支持", "条件付き・改善要求", "中立・情報", "慎重・反対"):
            self.assertIn(stance, page)
        self.assertIn(f"慎重・反対 {CAUTIOUS}件", page)
        self.assertIn("社会全体の世論調査ではありません", page)

    def test_page_keeps_protected_tags_and_footer(self) -> None:
        self.write("a-test", "本文。\n")
        page = self.build_one("a-test")
        self.assertIn("G-K10S4YCZFH", page)
        self.assertIn("ca-pub-2542211932832864", page)
        self.assertIn('<link rel="canonical" href="https://sns-reaction-map.jp/articles/a-test.html">', page)
        for href, label in FOOTER_LINKS:
            expected = href if href.startswith("http") else f"../{href}"
            self.assertIn(f'href="{expected}"', page, label)
        self.assertIn('"@type": "Organization"', page)

    def test_markdown_subset(self) -> None:
        self.write(
            "a-test",
            "リード。\n\n## 表\n\n| 市 | 時期 |\n|---|---|\n| 神戸市 | 2026年9月 |\n\n"
            "- 一つめ\n- 二つめ\n\n1. 手順\n2. 次\n\n[資料](https://www.mext.go.jp/)と**強調**。\n",
        )
        page = self.build_one("a-test")
        self.assertIn("<td>神戸市</td>", page)
        self.assertIn("<ul><li>一つめ</li><li>二つめ</li></ul>", page)
        self.assertIn("<ol><li>手順</li><li>次</li></ol>", page)
        self.assertIn('<a href="https://www.mext.go.jp/" target="_blank" rel="noopener">資料</a>', page)
        self.assertIn("<strong>強調</strong>", page)

    def test_sitemap_pages_include_index(self) -> None:
        self.write("a-test", "本文。\n")
        pages = dict(build_articles.article_pages())
        self.assertEqual(pages["articles/a-test.html"], "2026-10-17")
        self.assertEqual(pages["articles/index.html"], "2026-10-17")

    def test_link_label_is_required_and_short(self) -> None:
        text = "---\n" + BASE_META.format(slug="a-test").replace("link_label: テストの問い？", "link_label: " + "長" * 19) + "---\n本文。\n"
        (self.src / THEME / "a-test.md").write_text(text, encoding="utf-8")
        with self.assertRaises(build_articles.BuildError):
            build_articles.build()

    def test_slug_must_match_file_name(self) -> None:
        text = "---\n" + BASE_META.format(slug="other") + "---\n本文。\n"
        (self.src / THEME / "a-test.md").write_text(text, encoding="utf-8")
        with self.assertRaises(build_articles.BuildError):
            build_articles.build()


class StanceLabelTest(unittest.TestCase):
    def test_every_public_theme_maps_stances_to_colors(self) -> None:
        """記事を書くテーマで、立場の表示名が公開データから取れ、色が s1〜s4 に決まること。
        記事を書くテーマを増やすときは、ここに足して STANCE_ROLES を確かめる。"""
        for theme_id in ("bukatsu-chiiki", "elderly-license-revocation", "bike-blue-ticket"):
            theme = build_articles.load_theme(theme_id)
            self.assertTrue(theme.stances, theme_id)
            self.assertEqual(len({label for label, _ in theme.stances}), len(theme.stances), theme_id)
            self.assertEqual([c for _, c in theme.stances], sorted(c for _, c in theme.stances), theme_id)


class PublishedArticlesTest(unittest.TestCase):
    def test_docs_articles_match_sources(self) -> None:
        """公開中の記事が、原稿と公開データから作り直した結果と一致すること。"""
        outputs = build_articles.build()
        for path, content in outputs.items():
            self.assertTrue(path.is_file(), f"未生成: {path}")
            self.assertEqual(path.read_text(encoding="utf-8"), content, f"作り直すと変わる: {path}")

    def test_top_and_theme_pages_link_every_article(self) -> None:
        """トップは全記事、テーマページはそのテーマの記事へ、原稿の order の順で張ってあること（入口が消えたら止める）。"""
        import re

        docs = ROOT / "docs"
        pages = {"index.html": build_articles.entry_articles()}
        for article in build_articles.entry_articles():
            page = build_articles.load_theme(article.theme).url
            pages.setdefault(page, build_articles.entry_articles(article.theme))
        for name, articles in pages.items():
            text = (docs / name).read_text(encoding="utf-8")
            linked = re.findall(r'<a href="(articles/[a-z0-9-]+\.html)" data-article-entry=', text)
            expected = [a.url for a in articles] + ["articles/index.html"]
            self.assertEqual(linked, expected, name)
            self.assertIn('id="article-entry-tracking"', text, name)


if __name__ == "__main__":
    unittest.main()
