"""学校でのあだ名禁止・新デザインの試作（冒頭、論点ごとの読書面、背景の開閉行）。docs/ は書き換えない。

高齢者免許返納（tests/test_elderly_redesign.py）の手順5・6に当たる検査。読書面は最初から部活動型の圧縮済みの型で作る。
読書面の生成は公開できる入力（公開JSON・再読データ・立場の対応表・設定・背景台帳）だけを読む。非公開の正典が要るのは、
立場の対応表と代表投稿の選定基準を確かめる検査（正典が無い環境ではスキップ）だけ。
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup

from scripts import nickname_opening as opening

ROOT = opening.ROOT
PUBLIC = json.loads((ROOT / "docs/data/themes/school-nickname-ban.json").read_text(encoding="utf-8"))
CANON = ROOT / "social-samples/school-nickname-ban_hermes_arena_classified.json"
REREAD = json.loads((ROOT / "data/school-nickname-ban_issues-reread.json").read_text(encoding="utf-8"))
STANCES = json.loads((ROOT / "data/school-nickname-ban_reread-stances.json").read_text(encoding="utf-8"))
OPENING_CONFIG = ROOT / "configs/school-nickname-ban-opening.json"
OTHER = "school-nickname-ban-other"
FIRST = "school-nickname-ban-uniform-rule"
SMALL = {"school-nickname-ban-gender-consideration", "school-nickname-ban-individual-choice"}


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def key(tweet_id: str) -> str:
    return hashlib.sha256(str(tweet_id).encode()).hexdigest()


class OpeningTests(unittest.TestCase):
    """冒頭：確認日は設定の1か所から。正本の見た目は scripts/nickname_redesign/。"""

    @classmethod
    def setUpClass(cls):
        cls.ctx = opening.load_inputs(OPENING_CONFIG)
        cls.config = cls.ctx["config"]

    def frag(self, config=None):
        ctx = dict(self.ctx)
        ctx["config"] = config or self.config
        return opening.render_fragment(ctx)

    def test_checked_on_single_source(self):
        when = opening.jp_date(self.config["checked_on"])
        frag = self.frag()
        self.assertIn(f"国の資料の本文は{when}に確かめました", frag)
        self.assertIn(f"{when}確認", frag)
        self.assertIn(f'data-checked-on="{self.config["checked_on"]}"', frag)
        self.assertNotIn("checked", self.config)
        cfg = copy.deepcopy(self.config)
        cfg["checked_on"] = "2026-12-01"
        self.assertIn("2026年12月1日に確かめました", self.frag(cfg))

    def test_old_dates_or_stale_checked_on_stop(self):
        for change in ({"checked": {"memo_checked_on": "2026-09-07"}}, {"checked_on": "2026-09-01"}):
            cfg = copy.deepcopy(self.config)
            cfg.update(change)
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "c.json"
                path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
                with self.assertRaises(SystemExit):
                    opening.load_inputs(path)

    def test_checked_on_backed_by_memo(self):
        memo = (ROOT / "quality/research/school-nickname-ban-primary-sources.md").read_text(encoding="utf-8")
        self.assertIn(f"【{self.config['checked_on']}追記】", memo)

    def test_opening_assets_live_in_redesign_folder(self):
        css = (ROOT / "scripts/nickname_redesign/opening.css").read_text(encoding="utf-8")
        self.assertEqual((ROOT / "quality/prototypes/school-nickname-ban-opening/opening.css").read_text(encoding="utf-8"), css)


class ReadingPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts import nickname_reading as reading

        cls.reading = reading
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        cls.page_path = reading.build(cls.out / "a")
        cls.html = cls.page_path.read_text(encoding="utf-8")
        cls.s = soup_of(cls.html)
        cls.d = reading.load()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def panel(self, iid):
        return self.s.find(id="issue-" + iid)

    def test_same_input_same_output(self):
        again = self.reading.build(self.out / "b").read_text(encoding="utf-8")
        self.assertEqual(self.html, again)

    def test_prototype_is_current(self):
        committed = (self.reading.OUT_DIR / "index.html").read_text(encoding="utf-8")
        self.assertEqual(committed, self.html)
        for name in ("reading.css", "reading.js", "opening.css"):
            self.assertEqual((self.reading.OUT_DIR / name).read_text(encoding="utf-8"),
                             (self.reading.ASSETS / name).read_text(encoding="utf-8"), name)

    def test_default_as_of_is_public_updated_on(self):
        self.assertEqual(self.reading.default_as_of(self.d), PUBLIC["updated_on"])
        self.assertIn(f'data-as-of="{PUBLIC["updated_on"]}"', self.html)

    def test_does_not_write_docs_or_read_canonical(self):
        self.assertNotIn("docs", str(self.page_path.relative_to(self.out)))
        src = (ROOT / "scripts/nickname_reading.py").read_text(encoding="utf-8")
        self.assertNotIn("social-samples", src)
        self.assertNotIn("social-samples", json.dumps(self.d["cfg"]["issues"], ensure_ascii=False))

    def test_no_static_mountains(self):
        self.assertEqual(self.s.select(".fr-mountains, .fr-hill, .fr-chip, #planet-block"), [])
        first = self.s.select_one("#school-nickname-ban-reading .fr-panels > *")
        self.assertEqual(first.name, "nav")

    def test_issue_order_and_zero_other_hidden(self):
        tabs = [a["data-issue-id"] for a in self.s.select(".fr-tab")]
        named = sorted((i for i in PUBLIC["issues"] if int(i["count"]) > 0 and i["id"] != OTHER),
                       key=lambda i: (-int(i["count"]), i["id"]))
        self.assertEqual(tabs, [i["id"] for i in named])
        self.assertIsNone(self.panel(OTHER))
        # 「その他」に件数が入れば、自動で最後に出る（理由区分が無いので「理由は未公開」）
        d = copy.deepcopy(self.d)
        other = next(i for i in d["public"]["issues"] if i["id"] == OTHER)
        other["count"] = 1
        other["stances"][3]["count"] = 1
        self.assertEqual(self.reading.ordered_issues(d)[-1]["id"], OTHER)
        html = self.reading.render_panel(d, other, FIRST, 7)
        self.assertIn("data-unpublished", html)

    def test_small_flag_follows_opening_threshold(self):
        th = int(self.d["ocfg"]["count"]["small_threshold"])
        flagged = {p["data-issue-panel"] for p in self.s.select(".fr-panel") if p.select_one("[data-small]")}
        self.assertEqual(flagged, {i["id"] for i in PUBLIC["issues"] if 0 < int(i["count"]) < th})
        self.assertEqual(flagged, SMALL)
        for iid in SMALL:
            self.assertIn(self.d["ocfg"]["count"]["small_tag"], self.s.select_one(f'.fr-tab[data-issue-id="{iid}"]').get_text())

    def test_note_says_few_and_uncollected(self):
        note = self.s.select_one(".fr-note").get_text()
        self.assertIn(f'{PUBLIC["opinion_count"]}件と少なめ', note)
        self.assertIn("9月21日以降の投稿はまだ集めていません", note)
        self.assertIn("10月18日", note)

    def test_counts_and_stances_match_public_json(self):
        order = [s["id"] for s in self.reading.stance_order(self.d)]
        for issue in PUBLIC["issues"]:
            if int(issue["count"]) == 0:
                continue
            panel = self.panel(issue["id"])
            self.assertEqual(panel.select_one(".fr-count b").get_text(), f'{int(issue["count"]):,}')
            by = {s["id"]: int(s["count"]) for s in issue["stances"]}
            for sel in (".fr-stance-mini b", ".fr-stance .fr-stance-list b"):
                self.assertEqual([b.get_text() for b in panel.select(sel)], [f"{by[sid]:,}" for sid in order], sel)
            self.assertIn("世論調査の結果ではありません", panel.select_one(".fr-head-stance .fr-caveat").get_text())

    def test_reasons_recounted_from_reread_details(self):
        for issue in PUBLIC["issues"]:
            if int(issue["count"]) == 0:
                continue
            panel = self.panel(issue["id"])
            items = [i for i in REREAD["items"] if i["main_issue"] == issue["label"]]
            self.assertEqual(len(items), int(issue["count"]), issue["label"])
            self.assertIsNone(panel.select_one("[data-unpublished]"))
            for bid in REREAD["buckets"][issue["label"]]:
                node = panel.select_one(f'li.fr-reason[data-reason="{bid}"] .fr-reason-n b')
                self.assertEqual(node.get_text(), str(sum(1 for it in items if it["bucket"] == bid)), (issue["label"], bid))

    def test_reason_stances_sum_to_public(self):
        for label, rr in self.d["reread"].items():
            issue = next(i for i in PUBLIC["issues"] if i["label"] == label)
            total = Counter(self.reading.item_stance(self.d, it) for it in rr["items"])
            self.assertEqual({s["id"]: total.get(s["id"], 0) for s in issue["stances"]},
                             {s["id"]: int(s["count"]) for s in issue["stances"]}, label)

    def test_stance_table_matches_reread_and_excludes_excluded(self):
        self.assertEqual(set(STANCES["stances"]), {i["post_key"] for i in REREAD["items"]})
        self.assertFalse({i["post_key"] for i in REREAD["excluded_items"]} & set(STANCES["stances"]))
        self.assertEqual(STANCES["public_mismatch"], 0)

    def test_stale_stance_table_stops(self):
        from scripts import nickname_reading as reading
        with tempfile.TemporaryDirectory() as tmp:
            table = copy.deepcopy(STANCES)
            table["stances"].popitem()
            tpath = Path(tmp) / "t.json"
            tpath.write_text(json.dumps(table, ensure_ascii=False), encoding="utf-8")
            cfg = json.loads(reading.CONFIG.read_text(encoding="utf-8"))
            cfg["reread_stances_json"] = str(tpath)
            cpath = Path(tmp) / "c.json"
            cpath.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(SystemExit):
                reading.load(cpath)
        d = copy.deepcopy(self.d)
        item = d["reread"]["一律禁止の実効性"]["items"][0]
        item["stance"] = next(s["key"] for s in d["planet"]["stances"] if s["key"] != item["stance"])
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では立場の対応表を確かめられない")
    def test_stance_table_matches_canonical(self):
        canon = json.loads(CANON.read_text(encoding="utf-8"))
        ops = [x for x in canon if x["classification"].get("is_opinion")]
        self.assertEqual(len(ops), int(PUBLIC["opinion_count"]))
        self.assertEqual(len(canon), int(PUBLIC["collected_count"]))
        by = {key(x["tweet_id"]): x["classification"] for x in canon}
        for it in REREAD["items"]:
            c = by[it["post_key"]]
            self.assertTrue(c["is_opinion"])
            self.assertEqual((c["main_issue"], c["stance"]), (it["main_issue"], STANCES["stances"][it["post_key"]]))
        for it in REREAD["excluded_items"]:
            self.assertFalse(by[it["post_key"]].get("is_opinion"))

    def test_first_panel_is_complete(self):
        panel = self.panel(FIRST)
        self.assertIn("is-complete", panel["class"])
        self.assertEqual(len(panel.select(".fr-voice")), len(REREAD["buckets"]["一律禁止の実効性"]))
        for cid in ("constitution", "rule-reason"):
            self.assertTrue(panel.select(f'.fr-claim[data-claim="{cid}"]'), cid)
        self.assertTrue(panel.select('[data-sunk="school-nickname-ban-review-rule"]'))
        self.assertTrue(panel.select('[data-vein="school-nickname-ban-vein-safety"]'))
        self.assertTrue(panel.select('.fr-check[data-check="reason"]'))
        for a in panel.select(".fr-see a"):
            self.assertIsNotNone(self.s.find(id=a["href"][1:]), a["href"])

    def test_national_rule_is_one_link_not_repeated(self):
        """国の定めがあるか（台帳の scope）は論点ごとに繰り返さず、背景への1行のリンクにする。"""
        for panel in self.s.select(".fr-panel.is-complete"):
            self.assertEqual(len(panel.select(".fr-national a")), 1)
            self.assertEqual(panel.select_one(".fr-national a")["href"], "#bg-national")
            self.assertEqual(panel.select('.fr-check[data-check="scope"]'), [])

    def test_compact_structure(self):
        top = self.d["cfg"]["compact"]["top_reasons"]
        for panel in self.s.select(".fr-panel"):
            iid = panel["data-issue-panel"]
            issue = next(i for i in PUBLIC["issues"] if i["id"] == iid)
            self.assertEqual(panel.select("details[open]"), [], iid)
            n_buckets = len(self.d["reread"][issue["label"]]["buckets"])
            first = panel.select_one(".fr-reasons > .fr-reason-list")
            self.assertEqual(len(first.select(".fr-reason")), min(top, n_buckets))
            if n_buckets <= top:
                self.assertIsNone(panel.select_one(".fr-reason-more"))
            else:
                self.assertIn(f"残り{n_buckets - top}分類", panel.select_one(".fr-reason-more").summary.get_text())
            if "is-complete" in panel["class"]:
                self.assertEqual(len(panel.select(".fr-panel-head > div > .fr-desc")), 1)
                on = panel.select(".fr-reason-detail[data-on]")
                self.assertEqual(len(on), 1)
                self.assertEqual(on[0]["data-reason"], panel.select_one(".fr-reasons li.fr-reason")["data-reason"])
                for sel in ("details.fr-posts", "details.fr-stance"):
                    self.assertTrue(panel.select(sel), (iid, sel))
                for claim in panel.select(".fr-claim"):
                    self.assertTrue(claim.summary.select_one(".fr-verdict"))

    def test_reason_links_resolve(self):
        for a in self.s.select("a[data-reason-pick]"):
            self.assertIsNotNone(self.s.find(id=a["href"][1:]), a["href"])
        js = (ROOT / "scripts/nickname_redesign/reading.js").read_text(encoding="utf-8")
        self.assertIn("ids.find(x => h.startsWith('fr-r-' + x + '-'))", js)
        self.assertIn("window.NicknameReading", js)

    def test_posts_at_most_two_with_lazy_embed_and_original_links(self):
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.html)
        for panel in self.s.select(".fr-panel"):
            embeds = panel.select(".x-embed")
            self.assertLessEqual(len(embeds), 2)
            for e in embeds:
                self.assertRegex(e.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")
            self.assertEqual(len(panel.select(".fr-post")), len(embeds))

    def test_posts_differ_in_stance_or_say_why(self):
        labels = {i["id"]: i for i in PUBLIC["issues"]}
        for iid, icfg in self.d["cfg"]["issues"].items():
            posts = icfg.get("posts", {}).get("items", [])
            if len(posts) == 1:
                self.assertTrue(icfg["posts"]["one_reason"], iid)
            if len(posts) != 2:
                continue
            st = {self.reading.post_stance(self.d, labels[iid], p) for p in posts}
            if len(st) == 1:
                self.assertEqual(self.panel(iid).select_one("[data-same-stance]").get_text(), icfg["posts"]["same_stance_reason"])
            else:
                self.assertIsNone(self.panel(iid).select_one("[data-same-stance]"), iid)

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では代表投稿の選定基準を確かめられない")
    def test_selected_posts_meet_canonical_criteria(self):
        canon = json.loads(CANON.read_text(encoding="utf-8"))
        norm = lambda t: re.sub(r"\s+", "", t)
        texts = Counter(norm(x["text"]) for x in canon)
        by_id = {str(x["tweet_id"]): x for x in canon}
        labels = {i["id"]: i["label"] for i in PUBLIC["issues"]}
        for iid, icfg in self.d["cfg"]["issues"].items():
            for p in icfg.get("posts", {}).get("items", []):
                x = by_id[p["id"]]
                c = x["classification"]
                self.assertTrue(c["is_opinion"], p["id"])
                self.assertEqual(c["main_issue"], labels[iid], p["id"])
                self.assertTrue(c["article_usable"], p["id"])
                self.assertEqual(c["risk"], "low", p["id"])
                self.assertNotEqual(c["intensity"], "high", p["id"])
                self.assertEqual(x["url"], p["url"], p["id"])
                self.assertEqual(texts[norm(x["text"])], 1, p["id"])
                self.assertNotIn("SNS反応まっぷ", x["text"], p["id"])
                self.assertNotIn("/grok/", x["url"], p["id"])

    def test_count_mismatch_stops(self):
        d = copy.deepcopy(self.d)
        d["reread"]["一律禁止の実効性"]["items"].pop()
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        d["public"]["issues"][0]["count"] += 1
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        d["public"]["issues"][0]["stances"][0]["count"] += 1
        d["public"]["issues"][0]["stances"][1]["count"] -= 1
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        d["public"]["trends"] = []
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        d["claim_posts"]["constitution"] = []
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_bad_posts_and_checks_stop(self):
        d = copy.deepcopy(self.d)
        posts = d["cfg"]["issues"][FIRST]["posts"]["items"]
        posts[0]["url"] = posts[0]["url"].replace(posts[0]["id"], "1")
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        posts = d["cfg"]["issues"][FIRST]["posts"]["items"]
        posts[0]["id"] = "1"
        posts[0]["url"] = posts[0]["url"].rsplit("/", 1)[0] + "/1"
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        d["cfg"]["issues"][FIRST]["checks"] = ["no-such-check"]
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_check_dates_come_from_ledger(self):
        node = self.panel(FIRST).select_one('.fr-check[data-check="reason"]')
        self.assertIn(f'確認日 {self.reading.jp_date(self.d["background"]["checked_on"])}', node.get_text())


class AllIssuesAndBackgroundTests(unittest.TestCase):
    """手順6：残りの論点と背景の開閉行。"""

    @classmethod
    def setUpClass(cls):
        from scripts import nickname_background as background
        from scripts import nickname_reading as reading

        cls.reading, cls.background = reading, background
        cls.tmp = tempfile.TemporaryDirectory()
        cls.html = reading.build(Path(cls.tmp.name) / "a").read_text(encoding="utf-8")
        cls.s = soup_of(cls.html)
        cls.d = reading.load()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def render_bg(self, d=None):
        d = d or self.d
        return self.background.render(d, PUBLIC["updated_on"], self.reading.ordered_issues(d))

    def row(self, d, rid):
        return next(r for g in d["bg"]["cfg"]["groups"] for r in g["rows"] if r["id"] == rid)

    def test_all_shown_issues_complete(self):
        labels = {i["id"]: i["label"] for i in PUBLIC["issues"]}
        for issue in self.reading.ordered_issues(self.d):
            icfg = self.d["cfg"]["issues"][issue["id"]]
            self.assertEqual(icfg["status"], "complete", issue["id"])
            self.assertEqual(len(icfg["description"]), 2, issue["id"])
            self.assertEqual(set(icfg["reasons"]), set(self.d["reread"][labels[issue["id"]]]["buckets"]), issue["id"])
            self.assertIn(len(icfg["posts"]["items"]), (1, 2), issue["id"])
            self.assertTrue(icfg["posts"]["selection_basis"], issue["id"])
        self.assertEqual(self.s.select(".fr-panel.is-pending"), [])
        self.assertEqual(len(self.s.select(".fr-panel")), 6)

    def test_posts_not_reused_across_issues(self):
        ids = [p["id"] for c in self.d["cfg"]["issues"].values() for p in c.get("posts", {}).get("items", [])]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 11)

    def test_in_page_links_resolve(self):
        for a in self.s.select('a[href^="#"]'):
            href = a["href"]
            if href in ("#", "#planet-block", "#school-nickname-ban-tide-widget"):
                continue  # 手順7で元HTMLから写す山なみ・潮目のカード
            self.assertIsNotNone(self.s.find(id=href[1:]), href)

    def test_rows_are_closed_details(self):
        rows = self.s.select("#school-nickname-ban-background details.fb-row")
        self.assertEqual([r["data-row"] for r in rows],
                         ["national", "school", "voices", "why", "timeline", "faq", "help", "classroom", "unverified"])
        self.assertTrue(all(not r.has_attr("open") for r in rows))
        self.assertEqual(self.s.select_one('[data-row="national"]')["id"], "bg-national")
        self.assertEqual(self.s.select_one('[data-row="faq"]')["id"], "school-nickname-faq")

    def test_national_row_keeps_three_layers(self):
        node = self.s.select_one("#bg-national")
        self.assertTrue(node.select_one(".fb-ok"))
        self.assertTrue(node.select_one(".fb-ng"))
        text = node.get_text()
        for word in ("「あだ名」「さん付け」の語はありませんでした", "第13条", "校長", "2021年6月8日の事務連絡"):
            self.assertIn(word, text)
        voices = self.s.select_one("#bg-voices")
        self.assertIn("ここからはSNSの意見", voices.select_one(".fb-opinion-label").get_text())
        cand = json.loads(OPENING_CONFIG.read_text(encoding="utf-8"))["background_candidates"]["items"]
        for k, v in cand.items():
            self.assertIn(v["expectation"], voices.get_text())
            self.assertIn(v["concern"], voices.get_text())

    def test_checked_on_drives_time_wording(self):
        when = opening.jp_date(self.d["ocfg"]["checked_on"])
        self.assertIn(f"{when}時点のいじめ防止対策推進法", self.s.select_one("#bg-national").get_text())
        self.assertIn(f"{when}時点で、あだ名や呼び方を全国一律に定める", self.s.select_one("#bg-timeline").get_text())
        d = copy.deepcopy(self.d)
        d["ocfg"]["checked_on"] = "2026-12-01"
        self.assertIn("2026年12月1日時点", self.render_bg(d))
        d["ocfg"]["checked_on"] = "2026-09-01"  # 背景台帳の確認日より古い
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_unverified_mentions_uncollected_and_next(self):
        text = self.s.select_one("#bg-unverified").get_text()
        self.assertIn("9月21日以降の投稿", text)
        self.assertIn("10月18日", text)
        self.assertIn("判例", text)

    def test_faq_moved_from_opening_without_overlap(self):
        oc = json.loads(OPENING_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(oc["faq"]["placement"], "background")
        self.assertNotIn("nop-faq", self.html)
        qs = [dt.get_text() for dt in self.s.select("#school-nickname-faq dt")]
        self.assertEqual(len(qs), 4)
        self.assertFalse(set(qs) & {a["q"] for a in oc["answers"]})
        for q in ("学校のあだ名禁止は法律で決まっていますか？", "あだ名禁止と、全員をさん付けで呼ぶことは同じですか？"):
            self.assertNotIn(q, qs)
        d = copy.deepcopy(self.d)
        d["ocfg"]["faq"]["placement"] = "opening"
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_help_row_once_and_linked_from_opening(self):
        self.assertEqual(len(self.s.select("#bg-help")), 1)
        self.assertEqual(self.s.select_one("#bg-help .fb-phone a")["href"], "tel:0120078310")
        self.assertTrue(self.s.select('#school-nickname-safety a[href="#bg-help"]'))
        # 番号は冒頭の「つらい場合」と背景の相談先の2か所に出るが、設定は冒頭の safety.phone の1か所だけ（2026-10-13 司令塔の決定）
        self.assertEqual(self.s.select_one("#school-nickname-safety .nop-phone a")["href"], "tel:0120078310")
        self.assertEqual(self.html.count("0120-0-78310"), 2)
        configs = [(ROOT / "configs" / n).read_text(encoding="utf-8") for n in
                   ("school-nickname-ban-opening.json", "school-nickname-ban-background.json", "school-nickname-ban-reading.json")]
        self.assertEqual(sum(c.count("0120-0-78310") for c in configs), 1)
        d = copy.deepcopy(self.d)
        del d["ocfg"]["safety"]["phone"]
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_timeline_adds_notice(self):
        node = self.s.select_one("#bg-timeline")
        self.assertEqual([li["data-event"] for li in node.select("li[data-event]")], ["law-2013", "policy-2017", "notice-2021", "guidance-2022"])
        d = copy.deepcopy(self.d)
        del self.row(d, "timeline")["extra"][0]["before_ledger_reason"]
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_classroom_is_read_from_shared_config(self):
        cr = json.loads((ROOT / "configs/classroom/school-nickname-ban.json").read_text(encoding="utf-8"))
        text = self.s.select_one("#bg-classroom").get_text()
        for r in cr["reasons_pro"] + cr["reasons_con"]:
            self.assertIn(r["text"], text)

    def test_themes_yaml_mismatch_stops(self):
        d = copy.deepcopy(self.d)
        d["bg"]["theme"]["updated_at"] = "2026-01-01"
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_opening_why_says_reason_unverified(self):
        self.assertIn("この理由は、国の資料と事務連絡には書かれていませんでした。", self.html)


# ---------------------------------------------------------------- 手順7：公開候補と更新経路（docs/ は書き換えない）

import shutil  # noqa: E402

from scripts import build_nickname_redesign as redesign  # noqa: E402
from scripts import nickname_layout as layout  # noqa: E402

AS_OF = PUBLIC["updated_on"]
INPUTS = (
    "THEMES.yaml",
    "docs/data/themes/school-nickname-ban.json",
    "data/public/themes/school-nickname-ban.json",
    "data/school-nickname-ban_issues-reread.json",
    "data/school-nickname-ban_reread-stances.json",
    "data/school-nickname-ban_claim_posts.json",
    "data/verification/school-nickname-ban-background.json",
)
# 旧ページの JS・CSS の内部用id（外から指す意味の無いもの）
LEGACY_IDS_INTERNAL = ("school-nickname-connected-data", "explainer-modal", "school-nickname-reason-count-",
                       "school-nickname-check-note-", "school-nickname-source-", "pseg", "pbar", "pnum", "c-", "s-")
SHOWN = [i for i in PUBLIC["issues"] if int(i["count"]) > 0]


def protected(text: str, name: str) -> str:
    return re.search(f"<!-- {name}_START -->.*?<!-- {name}_END -->", text, re.S).group()


def vote_defs(text: str) -> tuple[str, str]:
    """投票の論点（var issues=[…]。件数を含む）と立場（var stances=[…]）。元HTMLと1文字も変えない。"""
    issues = re.search(r"var issues=(\[[^\n]*?\]);\n\s*var TOPIC=", text).group(1)
    stances = re.search(r"var stances=\[(.*?)\];", text, re.S).group(1)
    return issues, stances


class RedesignCandidateTests(unittest.TestCase):
    """手順7：元HTMLの保護対象を継承した公開候補（release / preview）。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name)
        cls.source_path = layout.source_for_refresh(ROOT)
        cls.source = cls.source_path.read_text(encoding="utf-8")
        redesign.build(cls.source_path, out / "release", "release", as_of=AS_OF)
        redesign.build(cls.source_path, out / "preview", "preview", as_of=AS_OF)
        cls.release = (out / "release" / redesign.PAGE).read_text(encoding="utf-8")
        cls.preview = (out / "preview" / redesign.PAGE).read_text(encoding="utf-8")
        cls.s = soup_of(cls.release)
        cls.src = soup_of(cls.source)
        cls.out = out

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_same_input_same_output(self):
        redesign.build(self.source_path, self.out / "again", "release", as_of=AS_OF)
        self.assertEqual(self.release, (self.out / "again" / redesign.PAGE).read_text(encoding="utf-8"))

    def test_refuses_docs_and_new_page_input(self):
        with self.assertRaisesRegex(ValueError, "docs"):
            redesign.build(self.source_path, ROOT / "docs", "release", as_of=AS_OF)
        with self.assertRaisesRegex(ValueError, "docs"):
            redesign.build(self.source_path, ROOT / "docs" / "sub", "release", as_of=AS_OF)
        with tempfile.TemporaryDirectory() as temp:
            page = Path(temp) / "new.html"
            page.write_text(self.release, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "入力にできません"):
                redesign.build(page, Path(temp) / "out", "release", as_of=AS_OF)

    def test_title_seo_and_article_are_inherited_verbatim(self):
        for name in ("SEO_META", "ARTICLE_JSON_LD", "ARTICLE_TRUST"):
            self.assertEqual(self.release.count(protected(self.source, name)), 1, name)
        self.assertEqual(self.s.head.title.get_text(), self.src.head.title.get_text())
        self.assertEqual(self.s.select('link[rel="canonical"]')[0]["href"],
                         "https://sns-reaction-map.jp/school-nickname-ban-reaction-map.html")
        self.assertEqual(self.s.select_one('meta[property="og:image"]')["content"],
                         self.src.select_one('meta[property="og:image"]')["content"])
        self.assertEqual(len(self.s.select("h1")), 1)
        ids = Counter(t["id"] for t in self.s.find_all(id=True))
        self.assertEqual([k for k, v in ids.items() if v > 1], [])  # 同じidを2つ置かない

    def test_ga_and_adsense_only_in_release(self):
        for name in ("GA_TAG", "ADSENSE_TAG"):
            block = protected(self.source, name)
            self.assertIn(block, self.release)
            self.assertNotIn(block, self.preview)
        self.assertIn("G-K10S4YCZFH", self.release)
        self.assertNotIn("G-K10S4YCZFH", self.preview)
        self.assertIn("pagead2.googlesyndication.com", self.release)
        self.assertNotIn("pagead2.googlesyndication.com", self.preview)
        # google-adsense-account の meta は元HTMLにあるので両方に残す（広告の読み込みは release だけ）
        self.assertEqual(self.s.select_one('meta[name="google-adsense-account"]')["content"], "ca-pub-2542211932832864")
        self.assertIn('name="robots" content="noindex"', self.preview)
        self.assertNotIn('name="robots"', self.release)

    def test_vote_contract_is_unchanged(self):
        for text in (self.release, self.preview):
            self.assertIn(f'data-vote-topic="{redesign.VOTE_TOPIC}"', text)
            self.assertIn("var TOPIC='school-nickname-ban-issue-stance-v1'", text)
            self.assertEqual(vote_defs(self.source), vote_defs(text))  # 論点（件数を含む）と立場が元と完全一致
            self.assertIn("choiceIdx:issueIndex*stances.length+stanceIndex", text)
            self.assertIn("var STORAGE_KEY=window.SNS_REDESIGN_PRODUCTION?'nickname-arena-vote':'nickname-arena-vote-preview';", text)
            # 旧ページにも無い #issue-arena-section へ移ろうとして止まる1文は外す（その他の投票の処理は元のまま）
            self.assertNotIn("issue-arena-section", text)
        self.assertIn(redesign.VOTE_ARENA_SCROLL, self.source)
        issues, stances = vote_defs(self.release)
        self.assertEqual(len(json.loads(issues)), 6)  # 論点6×立場3＝18通り
        self.assertEqual(len(re.findall(r"\bkey:'", stances)), 3)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=location.hostname==='sns-reaction-map.jp'", self.release)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=false", self.preview)
        scripts = self.s.select("script")
        config = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-config.js"))
        client = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-store.js"))
        self.assertEqual(config + 2, client)
        # 投票の前置きの文も元HTMLのまま
        self.assertEqual(self.s.select_one("#vote-section > p").get_text(), self.src.select_one("#vote-section > p").get_text())

    def test_adapter_vote_fingerprint_matches_source(self):
        from scripts.refresh_adapters.nickname import vote_fingerprint
        self.assertEqual(vote_fingerprint(self.source), vote_fingerprint(self.release))
        self.assertEqual(vote_fingerprint(self.release)[3], 18)

    def test_faq_json_ld_matches_visible_faq(self):
        payloads = [json.loads(x.get_text()) for x in self.s.select('script[type="application/ld+json"]')]
        faq = [p for p in payloads if p.get("@type") == "FAQPage"]
        self.assertEqual(len(faq), 1)
        visible = redesign.faq_items(self.s)
        self.assertEqual(len(visible), 6)  # 冒頭の短答2問＋背景の「よくある質問」4問
        self.assertEqual([q for q, _a in visible[:2]], ["本当に禁止なの？", "なぜ始まったの？"])
        self.assertEqual([(q["name"], q["acceptedAnswer"]["text"]) for q in faq[0]["mainEntity"]], visible)
        texts = self.s.get_text()
        for q, a in visible:
            self.assertIn(q, texts)
            self.assertIn(a, texts)
        self.assertEqual(sum(1 for p in payloads if p.get("@type") == "Article"), 1)
        # 元HTMLのFAQの構造化データ（旧ページのFAQ10問）は使わない
        self.assertNotIn("SCHOOL_NICKNAME_FAQ_JSONLD", self.release)
        # 旧ページの検索入口・連動表示・テーマ共通の見た目・アリーナの点は読み込まない
        for name in ("school-nickname-connected.js", "school-nickname-connected-page.js", "school-nickname-connected.css",
                     "theme-design.js", "theme-design.css", "school-nickname-ban-arena-data.js"):
            self.assertNotIn(f'="{name}', self.release)

    def test_inherited_sections_and_links(self):
        self.assertEqual(len(self.s.select("#planet-data")), 1)
        self.assertEqual(self.s.select_one("#planet-data").string, self.src.select_one("#planet-data").string)
        self.assertIn("世論調査", self.s.select_one("#caution").get_text())
        for sel in ("#related-topics", "body > footer", "#related-theme-tracking"):
            self.assertEqual(self.s.select_one(sel).get_text(), self.src.select_one(sel).get_text(), sel)
        hrefs = {a["href"] for a in self.s.select("footer a[href]")}
        for href in ("about.html#operator", "about.html#method", "privacy.html", "disclaimer.html"):
            self.assertIn(href, hrefs)
        self.assertIn('<time datetime="2026-06-24">', self.release)
        self.assertIn(f'<time datetime="{PUBLIC["updated_on"]}">', self.release)
        self.assertIsNotNone(self.s.select_one('header.modern-site-header a[href="index.html"]'))

    def test_detail_data_is_kept_verbatim(self):
        """調査上の注意（#detail-data。あだ名禁止の元HTMLでは表を持たず「読み方」だけ）は元HTMLのまま。"""
        self.assertEqual([str(d) for d in self.s.select("#detail-data > details")],
                         [str(d) for d in self.src.select("#detail-data > details")])

    def test_tide_card_is_inherited_verbatim_inside_fold(self):
        block = re.search(r'<section class="update-dashboard"[^>]*><!-- TIDE_CARD_START -->.*?<!-- TIDE_CARD_END --></section>',
                          self.source, re.S).group()
        self.assertEqual(self.release.count(block), 1)
        self.assertIn("/* TIDE_CARD_START */", self.release)
        fold = self.s.select_one("#cap-trend-more")
        self.assertEqual(fold.name, "details")
        self.assertFalse(fold.has_attr("open"))
        self.assertIsNotNone(fold.select_one("#school-nickname-ban-tide-widget"))
        glance = self.s.select_one("#cap-trend .cap-trend-glance")
        data = json.loads(re.search(r"const datasets = (\{.*?\});\n", self.release, re.S).group(1))
        self.assertEqual(len(glance.select(".cap-trend-spark svg polyline")), len(data["stance"]["rows"]))
        self.assertIn(self.s.select_one("[data-tide-headline]").get_text(), glance.select_one(".cap-trend-lead").get_text())
        self.assertLess(self.release.index("TIDE_CARD_START -->"), self.release.index('id="vote-section"'))

    def test_issue_glance_from_tide(self):
        data = json.loads(re.search(r"const datasets = (\{.*?\});\n", self.release, re.S).group(1))
        rows = {r["label"]: r for r in data["issue"]["rows"]}
        for issue in SHOWN:
            box = self.s.find(id="issue-" + issue["id"]).select_one(".fr-glance")
            link = box.select_one(".fr-glance-link")
            # 設定の飛び先（trend.widget_id）が、引き継いだ潮目のカードの実際の id とつながっている
            self.assertEqual((link["href"], link["data-tide-mode"]), ("#school-nickname-ban-tide-widget", "issue"))
            self.assertIsNotNone(self.s.find(id=link["href"][1:]))
            cap = box.select_one(".fr-glance-cap")
            if issue["label"] not in rows:
                self.assertIsNone(cap, issue["id"])  # さん付け・ジェンダー配慮は潮目の論点に無い
                continue
            self.assertIn(f'{rows[issue["label"]]["previous"]:.1f}%', cap.get_text())
            self.assertIn(f'{rows[issue["label"]]["current"]:.1f}%', cap.get_text())
            self.assertNotIn("件", box.select_one(".fr-glance-chart").get_text())
        self.assertEqual({i["label"] for i in SHOWN} - set(rows), {"さん付け・ジェンダー配慮"})

    def test_method_fold_holds_trust_and_detail_data(self):
        method = self.s.select_one("#cap-method")
        self.assertEqual(method.name, "details")
        self.assertFalse(method.has_attr("open"))
        self.assertIsNotNone(method.select_one("#detail-data"))
        trust = protected(self.source, "ARTICLE_TRUST")
        self.assertLess(self.release.index('id="cap-method"'), self.release.index(trust))
        self.assertLess(self.release.index(trust), self.release.index('id="related-topics"'))

    def test_folds_start_closed(self):
        for sel in ("#school-nickname-ban-reading", "#school-nickname-ban-background", "#school-nickname-open",
                    "#cap-trend", "#cap-method"):
            # 調査上の注意の「読み方」は元HTMLで開いた状態のまま引き継ぐ（外側の「作り方と調査上の注意」が閉じている）
            opened = [d for d in self.s.select(sel + " details[open]") if not d.find_parent(id="detail-data")]
            self.assertEqual([d.get("class") for d in opened], [], sel)
        self.assertFalse(self.s.select_one("#cap-method").has_attr("open"))
        self.assertEqual(len(self.s.select("#school-nickname-ban-background details.fb-row")), 9)

    def test_small_issues_are_marked(self):
        """意見100件のうち件数が少ない論点（冒頭の設定 count.small_threshold 未満）に、タブ・欄とも「少数」の印。"""
        threshold = int(json.loads(OPENING_CONFIG.read_text(encoding="utf-8"))["count"]["small_threshold"])
        small = {i["id"] for i in SHOWN if int(i["count"]) < threshold}
        self.assertEqual(small, SMALL)
        for issue in SHOWN:
            panel = self.s.find(id="issue-" + issue["id"])
            tab = self.s.select_one(f'.fr-tab[data-issue-id="{issue["id"]}"]')
            marked = panel.select_one("h3 [data-small]") is not None
            self.assertEqual(marked, issue["id"] in small, issue["id"])
            self.assertEqual("少数" in tab.get_text(), issue["id"] in small, issue["id"])
            self.assertEqual(panel.select_one(".fr-small-note") is not None, issue["id"] in small, issue["id"])

    def test_other_issue_hidden_while_zero(self):
        """「その他」が0件のあいだはタブも欄も出さない（山なみの論点一覧からも0件の論点は外れている）。"""
        other = next(i for i in PUBLIC["issues"] if i["id"] == OTHER)
        self.assertEqual(int(other["count"]), 0)
        self.assertIsNone(self.s.find(id="issue-" + OTHER))
        self.assertIsNone(self.s.select_one(f'.fr-tab[data-issue-id="{OTHER}"]'))
        self.assertEqual(len(self.s.select(".fr-tab")), len(SHOWN))

    def test_classroom_section_contract(self):
        section = self.release[self.release.index("<!-- CLASSROOM_START -->"):self.release.index("<!-- CLASSROOM_END -->")]
        self.assertIn('class="classroom-print-btn"', section)
        self.assertIn("classroom-sources", section)
        self.assertIn("classroom-questions", section)
        self.assertEqual(self.release.count("<!-- CLASSROOM_START -->"), 1)
        self.assertLess(self.release.index("<!-- CLASSROOM_START -->"), self.release.index("<!-- ARTICLE_TRUST_START -->"))

    def test_help_phone_in_opening_and_background(self):
        """24時間こどもSOSダイヤルは、冒頭の「つらい場合」と背景の相談先の両方に出る（子どもがすぐ見つけられるように）。"""
        for sel in ("#school-nickname-safety .nop-phone a", "#bg-help .fb-phone a"):
            node = self.s.select_one(sel)
            self.assertEqual((node["href"], node.get_text()), ("tel:0120078310", "0120-0-78310"), sel)
        self.assertLess(self.release.index('id="school-nickname-safety"'), self.release.index('id="planet-block"'))

    def test_old_anchor_targets_exist(self):
        for target in set(redesign.ALIASES.values()):
            self.assertIsNotNone(self.s.find(id=target), target)
        for alias in redesign.ALIASES:
            if alias in redesign.HIDDEN_RECEIVERS:
                continue
            self.assertIsNone(self.s.find(id=alias), alias)
        for receiver in redesign.HIDDEN_RECEIVERS:
            self.assertIn(receiver, redesign.ALIASES)
        self.assertIsNotNone(self.s.find(id="planet-block"))
        self.assertNotIn("planet-block", redesign.ALIASES)
        # 旧ページで外から指せた節のidは、新ページにあるか、読み替え先があるか（JS・CSS の内部用idは除く）
        for node in self.src.find_all(id=True):
            old = node["id"]
            if self.s.find(id=old) is not None or old in redesign.ALIASES or old.startswith(LEGACY_IDS_INTERNAL):
                continue
            self.assertTrue(any(old.startswith(p) for p in redesign.ISSUE_PREFIXES), old)
        for issue in SHOWN:
            self.assertIsNotNone(self.src.find(id="issue-" + issue["id"]))
            self.assertEqual(self.s.find(id="issue-" + issue["id"])["data-issue-panel"], issue["id"])
        for kept in ("vote-section", "detail-data", "related-topics", "caution", "planet-data", "research-conditions",
                     "school-nickname-ban-tide-widget", "bg-classroom", "article-trust-title", "school-nickname-faq"):
            self.assertIsNotNone(self.s.find(id=kept), kept)
        # サイト内から旧アンカー付きで指すリンク（docs・scripts・configs）の飛び先も新ページにある
        targets = set()
        for base in ("docs", "scripts", "configs"):
            for path in (ROOT / base).rglob("*"):
                if path.suffix not in (".html", ".py", ".json", ".js", ".md", ".txt", ".xml") or path.name == redesign.PAGE:
                    continue
                if "page-sources" in path.parts:
                    continue
                targets |= set(re.findall(r"school-nickname-ban-reaction-map\.html#([A-Za-z0-9_-]+)",
                                          path.read_text(encoding="utf-8", errors="ignore")))
        for t in targets:
            self.assertTrue(self.s.find(id=t) is not None or t in redesign.ALIASES
                            or any(t.startswith(p) for p in redesign.ISSUE_PREFIXES), t)

    def test_planet_is_copied_from_source(self):
        """全体像の山なみは、元HTMLの対話式の山なみ（PLANET_SECTION）をそのまま写す（読み込み時の自動着地だけ置き換える）。"""
        src_section = re.search(r"<!-- PLANET_SECTION_START -->(.*?)<!-- PLANET_SECTION_END -->", self.source, re.S).group(1)
        src = soup_of(src_section)
        src_script = [x for x in src.find_all("script", recursive=False) if x.get("id") != "planet-data"][0].string
        self.assertEqual(src_script.count(redesign.AUTO_LAND), 1)
        self.assertEqual(self.release.count(src_script.replace(redesign.AUTO_LAND, redesign.AUTO_LAND_OFF)), 1)
        self.assertEqual(self.release.count(src.select_one("section.planet-panel > style").string), 1)
        self.assertEqual(self.release.count("window.PLANET_DATA="), 1)
        planet = self.s.select_one("#school-nickname-ban-reading .fr-map section.planet-panel #planet-block")
        self.assertIsNotNone(planet)
        self.assertLess(self.release.index('id="planet-block"'), self.release.index('class="fr-tabs"'))  # 山なみは論点タブの上
        for sel in ("#modes", ".stage", "#dotbox", "#list", "#meta"):
            self.assertEqual(str(planet.select_one(sel)), str(src.select_one("#planet-block " + sel)), sel)
        hrefs = [a["href"] for a in planet.select("#fallback-nav a")]
        self.assertEqual(sorted(hrefs), sorted("#issue-" + i["id"] for i in SHOWN))
        self.assertEqual(planet.select("section.landing-panel, #ocean, #editorial, span.issue-anchor"), [])
        for receiver in ("#guesses", "#quiz"):
            node = planet.select_one(receiver)
            self.assertTrue(node.has_attr("hidden") and not node.get_text(strip=True), receiver)
        self.assertTrue(self.s.select_one("#progress").has_attr("hidden"))
        self.assertIsNotNone(planet.select_one("#research-conditions > #caution"))
        # 旧ページの論点テンプレート（連動表示の読書面）は写さない（選択パネルは山なみ本来の表示になる）
        self.assertEqual(self.s.select("template[id^='school-nickname-ban-reading-']"), [])
        self.assertLess(self.release.index(src_script[:200]), self.release.index("window.NicknameReading"))
        self.assertLess(self.release.index("window.NicknameReading"), self.release.index("function goReading"))
        # 冒頭のリンク「…山なみで比べる」（#planet-block）の飛び先がある
        self.assertTrue(self.s.select('#school-nickname-open a[href="#planet-block"]'))

    def test_planet_follows_source_updates(self):
        changed = self.source.replace("このページの見かた", "このページの見かた（更新確認）", 1)
        self.assertNotEqual(changed, self.source)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.html"
            path.write_text(changed, encoding="utf-8")
            redesign.build(path, Path(temp) / "out", "release", as_of=AS_OF)
            page = (Path(temp) / "out" / redesign.PAGE).read_text(encoding="utf-8")
        self.assertIn("このページの見かた（更新確認）", page)
        broken = re.sub(r'<div class="dotbox" id="dotbox".*?<div class="waffle" id="waffle"></div>', "", self.source,
                        count=1, flags=re.S)
        self.assertNotEqual(broken, self.source)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.html"
            path.write_text(broken, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "山なみの部品"):
                redesign.build(path, Path(temp) / "out", "release", as_of=AS_OF)
        # 自動着地の処理・投票の後の移動が変わったら、黙って写さずに止まる
        for old, new, message in (
                (redesign.AUTO_LAND, redesign.AUTO_LAND.replace("landSilently(idIndex[top.id]);", "land(idIndex[top.id]);"), "自動着地"),
                (redesign.VOTE_ARENA_SCROLL, redesign.VOTE_ARENA_SCROLL.replace("450", "300"), "アリーナへの移動")):
            moved = self.source.replace(old, new, 1)
            self.assertNotEqual(moved, self.source)
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "source.html"
                path.write_text(moved, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    redesign.build(path, Path(temp) / "out", "release", as_of=AS_OF)

    def test_no_legacy_widgets(self):
        for marker in ("SCHOOL_NICKNAME_SEARCH_ENTRY_START", "THEME_DESIGN_START", "SCHOOL_NICKNAME_CONNECTED_START",
                       "SCHOOL_NICKNAME_CONNECTED_CONTENT_START", "STANCE_GLANCE_START", "THEME_COUNT_START",
                       "NICKNAME_ISSUE_MEDIA_START", "SCHOOL_NICKNAME_FAQ_START"):
            self.assertNotIn("<!-- " + marker, self.release)
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.release)
        self.assertNotIn("NICKNAME_ARENA_DATA=", self.release)
        for embed in self.s.select(".x-embed"):
            self.assertRegex(embed.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")

    def test_provenance_counts_and_detects_mismatch(self):
        from scripts.nickname_redesign_provenance import verified_selectors
        result = verified_selectors(self.release, ROOT)
        self.assertEqual(len(result), len(SHOWN) + 1)  # 論点の欄6つ＋冒頭の件数欄
        self.assertEqual(verified_selectors(self.source, ROOT), {})  # 旧ページでは照合しない
        node = self.s.select_one(f"#issue-{FIRST} li.fr-reason .fr-reason-n b")
        broken = self.release.replace(str(node), str(node).replace(node.get_text(), str(int(node.get_text().replace(",", "")) + 1)), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)
        mini = self.s.select_one(f"#issue-{FIRST} article.fr-reason-detail .fr-mini")
        label = mini["aria-label"]
        n = re.search(r"一律禁止に反対 (\d[\d,]*)件", label).group(1)
        broken = self.release.replace(label, label.replace(f"一律禁止に反対 {n}件", f"一律禁止に反対 {int(n.replace(',', '')) + 1}件"), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)
        count = self.s.select_one(f"#issue-{FIRST} .fr-count b")
        broken = self.release.replace(str(count), str(count).replace(count.get_text(), "37"), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)


class LayoutTests(unittest.TestCase):
    """手順7：更新経路（materialize → 旧形式の全処理 → finish）と、公開後の単独実行。"""

    def _root(self, temp: str) -> Path:
        root = Path(temp)
        shutil.copytree(ROOT / "configs", root / "configs")
        shutil.copytree(ROOT / "scripts/nickname_redesign", root / "scripts/nickname_redesign")
        for name in INPUTS:
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, root / name)
        (root / layout.PAGE).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(layout.source_for_refresh(ROOT), root / layout.PAGE)
        return root

    def test_disabled_has_no_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            (root / layout.CONFIG).write_text('{"enabled": false}')
            before = (root / layout.PAGE).read_bytes()
            self.assertEqual(layout.finish(root, as_of=AS_OF), {})
            layout.materialize(root)
            self.assertEqual(before, (root / layout.PAGE).read_bytes())
            self.assertFalse((root / layout.SOURCE).exists())

    def test_repository_layout_state_is_consistent(self):
        published = layout.MARKER in (ROOT / layout.PAGE).read_text(encoding="utf-8")
        if published:  # 公開後：設定が有効で、元HTMLがある
            self.assertTrue(layout.enabled(ROOT))
            self.assertTrue((ROOT / layout.SOURCE).is_file())
        else:  # 公開前：docs/ は旧形式のまま
            self.assertFalse(layout.enabled(ROOT))

    def test_new_page_without_source_stops(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "configs").mkdir()
            (root / layout.PAGE).write_text('<meta name="nickname-layout">')
            (root / layout.CONFIG).write_text('{"enabled": true}')
            with self.assertRaisesRegex(ValueError, "更新元HTML"):
                layout.source_for_refresh(root)
            (root / layout.CONFIG).write_text('{"enabled": false}')
            with self.assertRaisesRegex(ValueError, "更新設定が無効"):
                layout.source_for_refresh(root)

    def test_pipeline_finish_keeps_source_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            legacy = (root / layout.PAGE).read_text(encoding="utf-8")
            (root / layout.CONFIG).write_text('{"enabled": true}')
            targets = layout.finish(root, as_of=AS_OF)
            self.assertEqual(set(targets), {layout.SOURCE, layout.PAGE})
            first = (root / layout.PAGE).read_bytes()
            self.assertIn(b'name="nickname-layout"', first)
            self.assertEqual(legacy, (root / layout.SOURCE).read_text(encoding="utf-8"))
            self.assertEqual(layout.source_for_refresh(root), root / layout.SOURCE)
            # 次の更新：隔離コピーで元HTMLを戻し、旧形式の処理の後に再適用すると同じページになる
            layout.materialize(root)
            self.assertEqual(legacy, (root / layout.PAGE).read_text(encoding="utf-8"))
            layout.finish(root, as_of=AS_OF)
            self.assertEqual(first, (root / layout.PAGE).read_bytes())
            with self.assertRaisesRegex(ValueError, "再入力"):
                layout.finish(root, as_of=AS_OF)

    def test_count_mismatch_stops_before_writing(self):
        """新しい意見を追い読みしないまま、立場の対応表と再読データの明細が食い違った回と同じ形では止まる。"""
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            (root / layout.CONFIG).write_text('{"enabled": true}')
            path = root / "data/school-nickname-ban_issues-reread.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            gone = next(i for i in raw["items"] if i["main_issue"] == "一律禁止の実効性")
            raw["items"].remove(gone)
            raw["buckets"]["一律禁止の実効性"][gone["bucket"]]["count"] -= 1
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            before = (root / layout.PAGE).read_bytes()
            with self.assertRaisesRegex(ValueError, "照合で停止"):
                layout.finish(root, as_of=AS_OF)
            self.assertEqual(before, (root / layout.PAGE).read_bytes())
            self.assertFalse((root / layout.SOURCE).exists())

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では、更新経路の立場の対応表を作れない")
    def test_adapter_rebuilds_stance_table_and_stops_without_reread(self):
        """更新経路（refresh_adapters/nickname.py）は、累積候補から立場の対応表を作り直す（自転車と同じ）。
        新しい意見が再読データの明細に無ければ、何を直すかが分かる形で止まる。"""
        from scripts.refresh_adapters.nickname import build_reread_stances
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("THEMES.yaml", "data/school-nickname-ban_issues-reread.json"):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, root / name)
            candidate = root / "cumulative-candidate.json"
            shutil.copy2(CANON, candidate)
            data = build_reread_stances(root, candidate, root / "stances.json", "2026-10-18")
            self.assertEqual(data["stances"], STANCES["stances"])
            self.assertEqual((data["made_on"], data["public_mismatch"]), ("2026-10-18", 0))
            path = root / "data/school-nickname-ban_issues-reread.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw["items"].pop(0)
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "追い読み"):
                build_reread_stances(root, candidate, root / "stances.json", "2026-10-18")

    def test_refresh_path_is_wired(self):
        refresh = (ROOT / "scripts/refresh_topic.py").read_text(encoding="utf-8")
        self.assertEqual(refresh.count("finish_nickname_layout(candidate_root)"), 2)
        self.assertEqual(refresh.count("materialize_nickname(candidate_root)"), 1)
        self.assertIn("nickname_layout_enabled(root)", refresh)
        adapter = (ROOT / "scripts/refresh_adapters/nickname.py").read_text(encoding="utf-8")
        self.assertIn("current_page = source_for_refresh(root)", adapter)
        self.assertIn("build_reread_stances(root, candidate,", adapter)
        self.assertIn("REREAD_STANCES: first / REREAD_STANCES.name", adapter)
        self.assertIn("materialize_nickname(target)", (ROOT / "scripts/verify_builder_rebuildability.py").read_text(encoding="utf-8"))
        self.assertIn('"school-nickname-ban": "scripts.nickname_redesign_provenance"',
                      (ROOT / "scripts/verify_number_provenance.py").read_text(encoding="utf-8"))
        for path in ("scripts/apply_theme_design.py", "scripts/seo/apply_classroom_section.py", "scripts/seo/apply_theme_trust.py",
                     "scripts/refresh_planet_section.py", "scripts/verify_theme_page.py", "scripts/build_nickname_arena.py",
                     "scripts/nickname_issue_media.py"):
            self.assertIn("nickname-layout", (ROOT / path).read_text(encoding="utf-8"), path)


if __name__ == "__main__":
    unittest.main()
