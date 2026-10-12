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
        self.assertEqual(self.html.count("0120-0-78310"), 1)

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
