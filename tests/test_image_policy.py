import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
POLICY = DOCS / "image-policy.html"


class ImagePolicyTests(unittest.TestCase):
    def test_policy_has_required_content_and_protected_tags(self):
        source = POLICY.read_text(encoding="utf-8")
        required = (
            "AI生成画像を使用しています",
            "トップページ（index）のイメージ画像",
            "ヘッダー・ヒーロー画像",
            "インフォグラフィック",
            "投票画像・漫画画像",
            "特定の作家・イラストレーター",
            "確認・対応期限は設けていません",
            "画像・著作権等に関するご指摘",
            "https://www.bunka.go.jp/seisaku/chosakuken/aiandcopyright.html",
            "https://openai.com/policies/row-terms-of-use/",
            "G-K10S4YCZFH",
            "ca-pub-2542211932832864",
        )
        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, source)

    def test_every_public_html_links_to_policy(self):
        missing = []
        for page in sorted(DOCS.glob("*.html")):
            source = page.read_text(encoding="utf-8")
            if page.name != POLICY.name and 'href="image-policy.html"' not in source:
                missing.append(page.name)
        self.assertEqual([], missing, f"画像制作方針へのリンクがありません: {missing}")

    def test_policy_is_in_sitemap(self):
        sitemap = (DOCS / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn(
            "https://issue-stance-lab.github.io/sns-reaction-map/image-policy.html",
            sitemap,
        )


if __name__ == "__main__":
    unittest.main()
