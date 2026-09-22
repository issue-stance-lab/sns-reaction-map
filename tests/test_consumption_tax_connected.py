"""公開ファイルだけで確認する連動表示の接続・欠落検査。"""
import copy
import json
import re
import sys
import unittest
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_consumption_tax_page as builder
import consumption_tax_connected as connected


class ConnectedContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (ROOT / "docs/consumption-tax-cut-reaction-map.html").read_text()
        # 本文なしの公開検査用記録だけで資料欄を生成する。
        rows = json.loads((ROOT / "data/verification/consumption-tax-cut-claims.json").read_text())
        source = re.sub(re.escape(builder.CLAIM_START) + r".*?" + re.escape(builder.CLAIM_END),
                        lambda _: builder.claim_audit(rows), cls.original, flags=re.S)
        cls.page = connected.apply(source, activate=True)

    def test_activation_is_explicit_and_other_themes_are_unchanged(self):
        self.assertEqual(connected.apply(self.original), self.original)
        for path in (ROOT / "docs").glob("*-reaction-map.html"):
            if path.name.startswith("consumption-tax-cut-"):
                continue
            text = path.read_text()
            self.assertEqual(connected.apply(text, activate=True, topic=path.stem), text)

    def test_same_input_does_not_accumulate_assets_or_bridges(self):
        self.assertEqual(connected.apply(self.page), self.page)
        self.assertEqual(self.page.count(connected.START), 1)
        self.assertEqual(self.page.count(connected.BRIDGE_START), 1)
        self.assertEqual(connected.validate(self.page), [])

    def test_relationships_do_not_depend_on_rank_or_display_labels(self):
        data = connected.planet_data(self.page)
        expected = connected.content_index(data)
        changed = copy.deepcopy(data)
        changed["issues"].reverse()
        for issue in changed["issues"]:
            issue["label"] = "表示名を変更"
        self.assertEqual(connected.content_index(changed), expected)
        claims = [len(x["claim_ids"]) for x in expected["issues"].values()]
        self.assertEqual(claims, [1, 1, 0, 3, 0, 1, 0])

    def test_missing_post_in_its_issue_fails_even_if_url_exists_elsewhere(self):
        url = builder.ISSUE_CARDS_POSTS["consumption-tax-cut-scope"][0][0]
        broken = self.page.replace('href="' + url + '"', 'href="#"')
        broken = broken.replace("</body>", '<a href="' + url + '">別の場所</a></body>')
        self.assertTrue(any("所属論点" in p for p in connected.validate(broken)))

    def test_stance_ids_do_not_depend_on_data_order(self):
        data = connected.planet_data(self.page)
        data["stances"].reverse()
        source = connected.DATA_PATTERN.sub(lambda m: m[1] + json.dumps(data, ensure_ascii=False) + m[3], self.page)
        rebuilt = connected.apply(source)
        before = BeautifulSoup(self.page, "html.parser")
        after = BeautifulSoup(rebuilt, "html.parser")
        buttons = lambda doc: {b.get_text(): b["data-stance-id"] for b in doc.select("#stance-glance .sg-pick-btn")}
        self.assertEqual(buttons(before), buttons(after))
        self.assertTrue(connected.validate(rebuilt.replace('data-stance-id="consumption-tax-cut-support"',
                                                         'data-stance-id="unknown"')))

    def test_missing_claim_source_fails_even_if_url_exists_in_other_sections(self):
        source = self.page
        start = source.index('data-claim-id="rate10"')
        end = source.index("</article>", start)
        card = source[start:end]
        url = builder.CLAIM_AUDIT[0]["links"][0][0]
        broken = source[:start] + card.replace(url, "https://example.invalid/") + source[end:]
        self.assertTrue(any("rate10" in p for p in connected.validate(broken)))

    def test_missing_static_issue_fails(self):
        broken = self.page.replace('id="fb-consumption-tax-cut-scope"', 'id="missing-fallback"')
        self.assertTrue(any("fb-consumption-tax-cut-scope" in p for p in connected.validate(broken)))

    def test_content_can_move_without_weakening_its_checks(self):
        pattern = re.escape(builder.BACKGROUND_START) + r".*?" + re.escape(builder.BACKGROUND_END)
        block = re.search(pattern, self.page, re.S)[0]
        moved = re.sub(pattern, "", self.page, flags=re.S).replace("</main>", block + "</main>")
        self.assertIn(block, moved)
        builder.verify(moved, 3890)
        self.assertEqual(connected.validate(moved), [])
        self.assertTrue(connected.validate(moved.replace('class="bg-tl"', 'class="missing-timeline"')))

    def test_mismatched_index_is_rejected(self):
        source = self.page.replace('"posts_id":"issue-consumption-tax-cut-scope"',
                                   '"posts_id":"issue-consumption-tax-cut-effect"')
        self.assertTrue(any("接続表" in p for p in connected.validate(source)))

    def test_missing_runtime_or_source_only_content_is_rejected(self):
        for before, after in [('consumption-tax-connected.js?v=1', 'missing.js'),
                              ('class="sunk"', 'class="missing-source"'),
                              (connected.BRIDGE_START, '/* missing bridge */')]:
            with self.subTest(before=before):
                self.assertTrue(connected.validate(self.page.replace(before, after)))


if __name__ == "__main__":
    unittest.main()
