import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/koshitsu-tenpakai-reaction-map.html"


class _VisibleFaqParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_guide = False
        self.in_summary = False
        self.questions = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "section" and attrs.get("id") == "koshitsu-quick-guide":
            self.in_guide = True
        if self.in_guide and tag == "summary":
            self.in_summary = True
            self.questions.append("")

    def handle_endtag(self, tag):
        if tag == "summary":
            self.in_summary = False
        if tag == "section" and self.in_guide:
            self.in_guide = False

    def handle_data(self, data):
        if self.in_summary:
            self.questions[-1] += data


class KoshitsuQuickGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")

    def test_quick_guide_is_immediately_after_main(self):
        self.assertEqual(self.html.count("<!-- KOSHITSU_QUICK_GUIDE_START -->"), 1)
        self.assertEqual(self.html.count("<!-- KOSHITSU_QUICK_GUIDE_END -->"), 1)
        self.assertRegex(
            self.html,
            r"<main>\s*<!-- KOSHITSU_QUICK_GUIDE_START -->",
        )

    def test_three_takeaways_are_present(self):
        self.assertEqual(self.html.count('<button type="button" class="kq-card'), 3)
        self.assertIn("女性皇族は、結婚後も皇族に", self.html)
        self.assertIn("旧11宮家の男系男子を養子に", self.html)
        self.assertIn("天皇になれる資格は現行のまま", self.html)

    def test_takeaway_buttons_connect_to_three_mountain_issues(self):
        mappings = {
            "marriage": "koshitsu-tenpakai-princess-aiko",
            "adoption": "koshitsu-tenpakai-former-royal-adoption",
            "succession": "koshitsu-tenpakai-patrilineal-matrilineal",
        }
        for key, issue_id in mappings.items():
            self.assertIn(f'data-kq-key="{key}"', self.html)
            self.assertIn(f'data-kq-issue="{issue_id}"', self.html)
        self.assertIn("window.KoshitsuConnectedMap.selectIssue(issueId)", self.html)
        self.assertIn("quick_guide_topic_select", self.html)
        self.assertIn("quick_guide_map_jump", self.html)

    def test_visible_faq_matches_structured_data(self):
        parser = _VisibleFaqParser()
        parser.feed(self.html)
        visible = [question.strip() for question in parser.questions]
        self.assertEqual(len(visible), 6)

        match = re.search(
            r"<!-- FAQ_JSON_LD_START -->\s*<script[^>]+>(.*?)</script>",
            self.html,
            re.S,
        )
        self.assertIsNotNone(match)
        schema = json.loads(match.group(1))
        structured = [item["name"] for item in schema["mainEntity"]]
        self.assertEqual(visible, structured)

    def test_date_status_is_explicit(self):
        for text in ("2026年9月30日時点", "7月17日", "7月24日", "10月24日"):
            self.assertIn(text, self.html)


if __name__ == "__main__":
    unittest.main()
