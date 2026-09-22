"""公開ファイルだけで確認する連動表示の接続・欠落検査。"""
import copy
import json
import re
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_consumption_tax_page as builder
import consumption_tax_connected as connected
import consumption_tax_connected_content as content
import consumption_tax_connected_vote as vote
from consumption_tax_count_provenance import verified_selectors


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
        # 公開HTML自体が新表示になっても、未有効化の経路を独立して検査する。
        inactive = self.page.replace(connected.START, '<!-- TAX_CONNECTED_DISABLED -->')
        self.assertEqual(connected.apply(inactive), inactive)
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
        for before, after in [('consumption-tax-connected.js?v=8', 'missing.js'),
                              ('consumption-tax-connected-page.js?v=8', 'missing.js'),
                              ('class="sunk"', 'class="missing-source"'),
                              (connected.BRIDGE_START, '/* missing bridge */')]:
            with self.subTest(before=before):
                self.assertTrue(connected.validate(self.page.replace(before, after)))

    def test_reading_templates_have_local_sources_and_distinct_empty_states(self):
        soup = BeautifulSoup(self.page, "html.parser")
        self.assertEqual(len(soup.select('template[id^="tax-reading-"]')), 7)
        finance = soup.select_one('#tax-reading-consumption-tax-cut-finance-welfare')
        self.assertEqual(len(finance.select('[data-tax-claim]')), 3)
        self.assertIn('理由別に分ける再読をまだ行っていません', str(finance))
        effect = soup.select_one('#tax-reading-consumption-tax-cut-effect')
        self.assertIn('資料照合は、まだ登録されていません', str(effect))
        self.assertEqual(len(effect.select('[data-tax-reason]')), 5)
        source = finance.select_one('[data-tax-claim="refund"] a')
        source['href'] = 'https://example.invalid/missing'
        self.assertTrue(any('読書面の資料照合' in p for p in connected.validate(str(soup))))

    def test_reading_reason_loss_is_rejected(self):
        broken = self.page.replace('data-tax-reason="A"', 'data-missing-reason="A"')
        self.assertTrue(any('理由分類' in p for p in connected.validate(broken)))

    def test_all_reviewed_reasons_have_a_matching_post_and_lazy_embed(self):
        from consumption_tax_reason_posts import load
        examples = load(connected.planet_data(self.page))
        soup = BeautifulSoup(self.page, 'html.parser')
        self.assertEqual(sum(len(reasons) for reasons in examples.values()), 25)
        for iid, reasons in examples.items():
            for bid, posts in reasons.items():
                reason = soup.select_one(f'#tax-reading-{iid} [data-tax-reason="{bid}"]')
                self.assertEqual(reason.select_one('a')['href'], posts[0]['url'])
                self.assertEqual(reason.select_one('.tax-reason-post-summary').get_text(types=None), posts[0]['summary'])
                self.assertFalse(reason.select_one('details').has_attr('open'))
                self.assertIsNotNone(reason.select_one('template .twitter-tweet'))
        self.assertFalse(soup.select_one('#tax-reading-consumption-tax-cut-finance-welfare').select('[data-tax-reason-posts]'))

    def test_reason_post_swaps_summary_edits_and_missing_links_are_rejected(self):
        for mutation in ('reason', 'summary', 'link'):
            with self.subTest(mutation=mutation):
                soup = BeautifulSoup(self.page, 'html.parser')
                reading = soup.select_one('#tax-reading-consumption-tax-cut-effect')
                a = reading.select_one('[data-tax-reason="A"] > details')
                if mutation == 'reason':
                    b = reading.select_one('[data-tax-reason="B"] > details')
                    a.replace_with(b.extract())
                elif mutation == 'summary':
                    a.select_one('.tax-reason-post-summary').string = '異なる要旨'
                else:
                    a.select_one('a')['href'] = 'https://example.invalid/'
                self.assertTrue(any('理由の投稿例' in p for p in connected.validate(str(soup))))

    def test_selected_post_must_belong_to_its_reason(self):
        from consumption_tax_reason_posts import load
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('configs/consumption-tax-reason-posts.json', 'configs/planet/consumption-tax-cut.yaml',
                         'data/consumption-tax-cut_4issues-reread.json'):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, root / name)
            path = root / 'configs/consumption-tax-reason-posts.json'
            selection = json.loads(path.read_text())
            reasons = selection['issues']['consumption-tax-cut-effect']
            reasons['A'] = reasons['B']
            path.write_text(json.dumps(selection, ensure_ascii=False))
            with self.assertRaisesRegex(ValueError, '投稿が選んだ理由に属しません'):
                load(connected.planet_data(self.page), root)

    def test_reading_timeline_and_source_only_need_their_own_sources(self):
        for selector, label in [
            ('#tax-reading-consumption-tax-cut-political-trust [data-tax-timeline]', '年表'),
            ('#tax-reading-consumption-tax-cut-business-burden [data-tax-source-only]', '資料側'),
        ]:
            with self.subTest(label=label):
                soup = BeautifulSoup(self.page, 'html.parser')
                sources = soup.select_one(selector + ' .tax-sources')
                url = sources.select_one('a')['href']
                sources.decompose()
                self.assertIsNotNone(soup.find('a', href=url), '同じ出典が他の欄に残っていても拒否する')
                self.assertTrue(any('読書面の' + label + 'の出典' in p for p in connected.validate(str(soup))))

    def test_corrections_follow_changed_counts_and_keep_confirmation_dates(self):
        data = connected.planet_data(self.page)
        original_dates = (data['editorial']['checked_on'], data['ocean']['checked_on'])
        data['totals'].update(collected=5000, opinions=4000)
        next(s for s in data['stances'] if s['id'].endswith('-conditional'))['count'] = 800
        by_id = {i['id']: i for i in data['issues']}
        for suffix, count in [('political-trust', 1200), ('other', 80), ('business-burden', 160)]:
            by_id['consumption-tax-cut-' + suffix]['count'] = count
        texts = content.corrected_observations(data)
        for part, actual in zip(['80.0%', '800件（20.0%）', '1,200件', '80件（2.0%）'], texts):
            self.assertIn(part, actual)
        content.correct_editorial(data)
        finding = next(f for f in data['editorial']['findings'] if f['id'].endswith('-ed-4'))['text']
        self.assertIn('160件（全体の4.0%）', finding)
        self.assertNotIn('どの論点よりも少ない', finding)
        self.assertEqual((data['editorial']['checked_on'], data['ocean']['checked_on']), original_dates)
        self.assertEqual(content.pct(0, 0), '算出できません')

    def test_focus_follows_counts_by_id_without_changing_vote_order(self):
        data = connected.planet_data(self.page)
        finance = next(i for i in data['issues'] if i['id'].endswith('-finance-welfare'))
        finance.update(count=2000, label='表示名を変えても同じID')
        next(i for i in data['issues'] if i['id'].endswith('-other'))['count'] = 3000
        data['issues'].reverse()
        source = connected.DATA_PATTERN.sub(lambda m: m[1] + json.dumps(data, ensure_ascii=False) + m[3], self.page)
        page = connected.apply(source)
        focus = BeautifulSoup(page, 'html.parser').select_one('.thirty-summary')
        self.assertEqual(focus.select_one('b').get_text(), '2000')
        self.assertEqual(focus.select_one('strong').get_text(), builder.ISSUE_META['財源と社会保障']['headline'])
        from refresh_adapters.consumption_tax import vote_fingerprint
        self.assertEqual(vote_fingerprint(page), vote_fingerprint(self.page))

    def test_source_only_items_keep_their_checked_population(self):
        data = connected.planet_data(self.page)
        item = data['ocean']['sunk_continents'][0]
        item.update(base_stale=True, sns_base=2000)
        html = content.render_templates(data, self.page, connected.content_index(data))
        self.assertIn('確認時の意見2,000件では', html)
        self.assertIn(item['checked_on'], html)

    def test_bar_colors_match_the_mountains(self):
        soup = BeautifulSoup(self.page, 'html.parser')
        for stance in connected.planet_data(self.page)['stances']:
            selector = '#stance-glance .temp-seg[data-stance-id="' + stance['id'] + '"]'
            self.assertIn('background:' + stance['color'], soup.select_one(selector)['style'])

    def test_reading_counts_have_original_record_provenance(self):
        self.assertEqual(len(verified_selectors(self.page, ROOT)), 25 + 2 + 4)
        inactive = self.page.replace(connected.START, '<!-- TAX_CONNECTED_DISABLED -->')
        self.assertEqual(verified_selectors(inactive, ROOT), {})

    def test_wrong_reason_count_fails_even_when_another_bucket_has_that_number(self):
        broken = self.page.replace('tax-reason-count-consumption-tax-cut-scope-A">455',
                                   'tax-reason-count-consumption-tax-cut-scope-A">125')
        with self.assertRaisesRegex(ValueError, '数字が元記録'):
            verified_selectors(broken, ROOT)

    def test_selected_post_and_search_counts_cannot_drift(self):
        for element_id, before, after in [
            ('tax-concern-count-consumption-tax-cut-vein-1', '推進 2件', '推進 3件'),
            ('tax-source-note-consumption-tax-cut-sc-3', '10件', '11件'),
        ]:
            soup = BeautifulSoup(self.page, 'html.parser')
            node = soup.select_one('#' + element_id)
            self.assertIn(before, node.get_text(types=None))
            node.string = node.get_text(types=None).replace(before, after)
            with self.subTest(element_id=element_id), self.assertRaisesRegex(ValueError, '数字が元記録'):
                verified_selectors(str(soup), ROOT)

    def test_vote_ids_preserve_all_published_storage_numbers(self):
        contract = json.loads((ROOT / 'quality/designs/2026-09-22-task77-consumption-tax-content-contract.json').read_text())['vote']
        choices = json.loads(re.search(r'var CHOICES=(.*?);', self.page)[1])
        self.assertEqual(sum(len(v) for v in choices.values()), 28)
        for row in contract['choices']:
            self.assertEqual(choices[row['issue_id']][row['stance_id']], row['choice_idx'])

    def test_unregistered_vote_issue_is_rejected(self):
        data = connected.planet_data(self.page)
        data['issues'][0]['id'] = 'unregistered'
        with self.assertRaisesRegex(ValueError, '投票の固定ID'):
            vote.registry(data)

    def test_changed_vote_meaning_is_rejected(self):
        broken = self.page.replace("k:'公約・政治不信'", "k:'別の論点'")
        with self.assertRaisesRegex(ValueError, '投票の並び・意味'):
            vote.apply(broken, connected.planet_data(broken))


if __name__ == "__main__":
    unittest.main()
