"""消費税減税・新デザインの試作（冒頭、論点ごとの読書面、背景の開閉行）。docs/ は書き換えない。

高齢者免許返納（tests/test_elderly_redesign.py）・辺野古（tests/test_henoko_redesign.py）の手順5・6に当たる検査。
読書面は最初から部活動型の圧縮済みの型で作る。読書面の生成は公開できる入力（公開JSON・再読データ・立場の対応表・設定・
一次資料メモ）だけを読む。非公開の正典が要るのは、立場の対応表と代表投稿の選定基準を確かめる検査（正典が無い環境ではスキップ）だけ。
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup

from scripts import consumption_tax_opening as opening

ROOT = opening.ROOT
PUBLIC = json.loads((ROOT / "docs/data/themes/consumption-tax-cut.json").read_text(encoding="utf-8"))
CANON = ROOT / "social-samples/consumption-tax-cut_hermes_arena_classified.json"
REREAD = json.loads((ROOT / "data/consumption-tax-cut_4issues-reread.json").read_text(encoding="utf-8"))
STANCES = json.loads((ROOT / "data/consumption-tax-cut_reread-stances.json").read_text(encoding="utf-8"))
OPENING_CONFIG = ROOT / "configs/consumption-tax-cut-opening.json"
OTHER = "consumption-tax-cut-other"
FIRST = "consumption-tax-cut-scope"
WITH_REASONS = {"減税の対象範囲": "hani", "減税の効果": "kouka", "給付など他策との比較": "kyufu", "事業者の実務負担": "jigyosha"}
PARTIES = ("自民", "立憲", "維新", "国民民主", "参政", "共産", "れいわ", "公明")


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def key_of(tweet_id) -> str:
    return hashlib.sha256(str(tweet_id).encode()).hexdigest()


class OpeningTests(unittest.TestCase):
    """冒頭：段階は基準日で切り替わる（背景も同じ判定関数を使う）。"""

    @classmethod
    def setUpClass(cls):
        cls.ctx = opening.load_inputs(OPENING_CONFIG)
        cls.config = cls.ctx["config"]

    def test_phase_by_as_of(self):
        self.assertEqual(opening.phase_of(self.config, "2026-10-11"), "bill")
        self.assertEqual(opening.phase_of(self.config, "2027-05-01"), "overdue")
        cfg = copy.deepcopy(self.config)
        cfg["law"]["enacted_on"] = "2026-11-20"
        self.assertEqual(opening.phase_of(cfg, "2026-12-01"), "enacted")
        self.assertEqual(opening.phase_of(cfg, "2028-01-01"), "in_effect")
        self.assertEqual(opening.phase_of(cfg, "2029-04-01"), "ended")

    def test_title_and_meta_untouched(self):
        """課題96（10/27判定）のため、冒頭は H1 だけを変える。title・meta は公開ページのまま（この試作では触らない）。"""
        seo = json.loads((ROOT / "configs/theme-seo.json").read_text(encoding="utf-8"))
        self.assertNotIn("display_headline", json.dumps(seo.get("consumption-tax-cut", {}), ensure_ascii=False))


class ReadingPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts import consumption_tax_reading as reading

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
        """リポジトリの試作が、いまの入力から作り直したものと同じ（生成し忘れを止める）。"""
        committed = (self.reading.OUT_DIR / "index.html").read_text(encoding="utf-8")
        self.assertEqual(committed, self.html)
        for name in ("reading.css", "reading.js", "opening.css", "opening.js"):
            self.assertEqual((self.reading.OUT_DIR / name).read_text(encoding="utf-8"),
                             (self.reading.ASSETS / name).read_text(encoding="utf-8"), name)

    def test_default_as_of_is_public_updated_on(self):
        self.assertEqual(self.reading.default_as_of(self.d), PUBLIC["updated_on"])
        self.assertIn(f'data-as-of="{PUBLIC["updated_on"]}"', self.html)

    def test_does_not_write_docs(self):
        self.assertNotIn("docs", str(self.page_path.relative_to(self.out)))
        self.assertNotIn("../../../docs/", self.html)

    def test_no_static_mountains(self):
        """山なみは手順7で元HTMLの対話式の図を写す。読書面は論点タブから始める。"""
        self.assertEqual(self.s.select(".fr-mountains, .fr-hill, .fr-chip, #planet-block, svg.planet"), [])
        first = self.s.select_one("#consumption-tax-cut-reading .fr-panels > *")
        self.assertEqual(first.name, "nav")
        self.assertIn("fr-tabs", first["class"])

    def test_issue_order_count_desc_other_last(self):
        tabs = [a["data-issue-id"] for a in self.s.select(".fr-tab")]
        named = sorted((i for i in PUBLIC["issues"] if i["id"] != OTHER), key=lambda i: (-int(i["count"]), i["id"]))
        self.assertEqual(tabs, [i["id"] for i in named] + [OTHER])

    def test_counts_and_stances_match_public_json(self):
        order = [s["id"] for s in self.reading.stance_order(self.d)]
        self.assertEqual(order, [s["id"] for s in self.d["planet"]["stances"]])
        for issue in PUBLIC["issues"]:
            panel = self.panel(issue["id"])
            self.assertEqual(panel.select_one(".fr-count b").get_text(), f'{int(issue["count"]):,}')
            by = {s["id"]: int(s["count"]) for s in issue["stances"]}
            for sel in (".fr-stance-mini b", ".fr-stance .fr-stance-list b"):
                self.assertEqual([b.get_text() for b in panel.select(sel)], [f"{by[sid]:,}" for sid in order], sel)
            self.assertIn("世論調査の結果ではありません", panel.select_one(".fr-head-stance .fr-caveat").get_text())

    def test_reasons_recounted_from_reread_details(self):
        """区分の件数は明細から数え直す。区分の合計＋除いた明細＝論点の件数。再読の無い3論点は「理由は未公開」。"""
        self.assertEqual(set(self.d["reread"]), set(WITH_REASONS))
        for issue in PUBLIC["issues"]:
            panel = self.panel(issue["id"])
            if issue["label"] not in WITH_REASONS:
                self.assertIsNotNone(panel.select_one("[data-unpublished]"), issue["label"])
                self.assertEqual(panel.select(".fr-reason"), [])
                continue
            node = REREAD[WITH_REASONS[issue["label"]]]
            self.assertEqual(len(node["items"]) + len(node["excluded_items"]), int(issue["count"]), issue["label"])
            self.assertIsNone(panel.select_one("[data-unpublished]"))
            for bid in node["buckets"]:
                got = panel.select_one(f'li.fr-reason[data-reason="{bid}"] .fr-reason-n b').get_text()
                self.assertEqual(got, f'{sum(1 for it in node["items"] if it["bucket"] == bid):,}', (issue["label"], bid))
            ex = panel.select_one("[data-excluded]")
            self.assertEqual(int(ex["data-excluded"]), len(node["excluded_items"]))

    def test_unpublished_disappears_when_reread_grows(self):
        d = copy.deepcopy(self.d)
        issue = next(i for i in d["public"]["issues"] if i["id"] == "consumption-tax-cut-political-trust")
        n = int(issue["count"])
        d["reread"][issue["label"]] = {"buckets": {"X": {"label": "仮の区分", "count": n}}, "excluded": [],
                                      "items": [{"tweet_id": str(k), "post_key": str(k), "bucket": "X", "main_issue": issue["label"],
                                                 "stance": None} for k in range(n)]}
        html = self.reading.render_reasons(d, issue, {})
        self.assertNotIn("data-unpublished", html)
        self.assertIn("仮の区分", html)

    def test_reason_stances_come_from_stance_table(self):
        """区分ごとの立場は対応表から。論点×立場の合計は公開JSONと一致し、明細の古い stance は使わない。"""
        for label, rr in self.d["reread"].items():
            issue = next(i for i in PUBLIC["issues"] if i["label"] == label)
            total = Counter(self.reading.item_stance(self.d, it) for it in rr["items"] + rr["excluded"])
            self.assertEqual({s["id"]: total.get(s["id"], 0) for s in issue["stances"]},
                             {s["id"]: int(s["count"]) for s in issue["stances"]}, label)
        self.assertEqual(STANCES["public_mismatch"], 0)
        self.assertEqual(STANCES["count"], sum(len(REREAD[k]["items"]) + len(REREAD[k]["excluded_items"]) for k in WITH_REASONS.values()))
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", k) for k in STANCES["stances"]))  # tweet_id は書かない（post_key だけ）

    def test_stance_table_out_of_date_stops(self):
        d = copy.deepcopy(self.d)
        it = d["reread"]["減税の対象範囲"]["items"][0]
        it["stance"] = next(s["key"] for s in d["planet"]["stances"] if s["key"] != it["stance"])
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        with tempfile.TemporaryDirectory() as tmp:
            cfg = copy.deepcopy(self.d["cfg"])
            table = copy.deepcopy(STANCES)
            table["stances"].pop(next(iter(table["stances"])))
            tpath = Path(tmp) / "stances.json"
            tpath.write_text(json.dumps(table, ensure_ascii=False), encoding="utf-8")
            cfg["reread_stances_json"] = str(tpath)
            cpath = Path(tmp) / "cfg.json"
            cpath.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(SystemExit):
                self.reading.load(cpath)

    def test_does_not_read_private_canonical(self):
        self.assertNotIn("social-samples", (ROOT / "scripts/consumption_tax_reading.py").read_text(encoding="utf-8"))
        self.assertNotIn("social-samples", json.dumps(self.d["cfg"]["issues"], ensure_ascii=False))

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では立場の対応表を確かめられない")
    def test_stance_table_matches_canonical(self):
        canon = json.loads(CANON.read_text(encoding="utf-8"))
        by = {key_of(x["tweet_id"]): x["classification"] for x in canon}
        for k, st in STANCES["stances"].items():
            self.assertEqual(by[k]["stance"], st)
            self.assertTrue(by[k]["is_opinion"])
        ops = [x for x in canon if x["classification"].get("is_opinion")]
        self.assertEqual(len(ops), int(PUBLIC["opinion_count"]))

    def test_scope_panel_is_complete(self):
        panel = self.panel(FIRST)
        self.assertIn("is-complete", panel["class"])
        self.assertEqual(len(panel.select(".fr-voice")), len(REREAD["hani"]["buckets"]))
        self.assertTrue(panel.select('.fr-claim[data-claim="rate10"]'))
        self.assertTrue(panel.select('.fr-check[data-check="scope-items"]'))
        labels = [p.get_text() for p in panel.select(".fr-side-label")]
        self.assertEqual(labels, ["SNSの意見を、資料と照らす", "政府の方針（法律案）で確かめる"])

    def test_compact_structure(self):
        """説明は1段落＋「くわしく」、理由は上位4件＋折りたたみ、説明は1位だけ data-on、照合・投稿・立場は閉じた折りたたみ。"""
        top = self.d["cfg"]["compact"]["top_reasons"]
        for issue in PUBLIC["issues"]:
            panel = self.panel(issue["id"])
            self.assertEqual(panel.select("details[open]"), [], issue["id"])
            rr = self.d["reread"].get(issue["label"])
            if rr:
                k = len(rr["buckets"])
                self.assertEqual(len(panel.select_one(".fr-reasons > .fr-reason-list").select(".fr-reason")), min(top, k))
                if k > top:
                    self.assertIn(f"残り{k - top}分類", panel.select_one(".fr-reason-more").summary.get_text())
            if "is-complete" in panel["class"]:
                self.assertEqual(len(panel.select(".fr-panel-head > div > .fr-desc")), 1)
                if rr:
                    on = panel.select(".fr-reason-detail[data-on]")
                    self.assertEqual(len(on), 1)
                    self.assertEqual(on[0]["data-reason"], panel.select_one(".fr-reasons li.fr-reason")["data-reason"])
                    counts = [int(b.get_text().replace(",", "")) for b in panel.select(".fr-reasons .fr-reason-n b")]
                    self.assertEqual(counts, sorted(counts, reverse=True))
                for sel in ("details.fr-posts", "details.fr-stance"):
                    self.assertTrue(panel.select(sel), (issue["id"], sel))
                for claim in panel.select(".fr-claim"):
                    self.assertTrue(claim.summary.select_one(".fr-verdict"))

    def test_reason_links_resolve(self):
        for a in self.s.select("a[data-reason-pick]"):
            self.assertIsNotNone(self.s.find(id=a["href"][1:]), a["href"])
        js = (ROOT / "scripts/consumption_tax_redesign/reading.js").read_text(encoding="utf-8")
        self.assertIn("ids.find(x => h.startsWith('fr-r-' + x + '-'))", js)
        self.assertIn("window.ConsumptionTaxReading", js)

    def test_posts_at_most_two_with_lazy_embed_and_original_links(self):
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.html)
        for panel in self.s.select(".fr-panel"):
            embeds = panel.select(".x-embed")
            self.assertLessEqual(len(embeds), 2)
            for e in embeds:
                self.assertRegex(e.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")
            self.assertEqual(len(panel.select(".fr-post")), len(embeds))

    def test_posts_not_reused_from_current_page(self):
        """代表投稿は正典から選び直した。現行ページの代表投稿（reason-posts）は使い回さない。"""
        old = set(re.findall(r"status/(\d+)", (ROOT / "configs/consumption-tax-reason-posts.json").read_text(encoding="utf-8")))
        mine = {p["id"] for c in self.d["cfg"]["issues"].values() for p in c.get("posts", {}).get("items", [])}
        self.assertEqual(old & mine, set())

    def test_posts_differ_in_stance_or_say_why(self):
        labels = {i["id"]: i for i in PUBLIC["issues"]}
        for iid, icfg in self.d["cfg"]["issues"].items():
            posts = icfg.get("posts", {}).get("items", [])
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
        stance_of = {s["id"]: s["key"] for s in self.d["planet"]["stances"]}
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
                self.assertNotIn("grok", x["url"].lower(), p["id"])
                for w in PARTIES:
                    self.assertNotIn(w, x["text"], (p["id"], w))
                if p.get("stance_id"):
                    self.assertEqual(stance_of[p["stance_id"]], c["stance"], p["id"])

    def test_no_party_names_in_reading_texts(self):
        """0%案と各党の案は背景でだけ扱う。読書面の手書きの文に政党名があれば止まる。"""
        reading = self.s.select_one("#consumption-tax-cut-reading")
        for node in reading.select(".fr-desc, .fr-voice, .fr-post, .fr-check, h3, .fr-tab"):
            for w in PARTIES:
                self.assertNotIn(w, node.get_text(), w)
        d = copy.deepcopy(self.d)
        d["cfg"]["issues"][FIRST]["description"][0] += "立憲民主党の案もあります。"
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_count_mismatch_stops(self):
        d = copy.deepcopy(self.d)
        d["reread"]["減税の対象範囲"]["items"].pop()
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        d["reread"]["減税の対象範囲"]["excluded"].pop()
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        d["public"]["issues"][0]["count"] += 1
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        scope = next(i for i in d["public"]["issues"] if i["id"] == FIRST)  # 理由区分のある論点は明細の立場と照合する
        scope["stances"][0]["count"] += 1
        scope["stances"][1]["count"] -= 1
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        d["public"]["trends"] = []
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        d["claim_posts"]["rate10"] = d["claim_posts"]["rate10"][:-1]
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_bad_posts_stop(self):
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
        posts = d["cfg"]["issues"][FIRST]["posts"]["items"]
        posts[1] = copy.deepcopy(posts[0])
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_memo_checks_use_bill_era_sections(self):
        node = self.panel(FIRST).select_one('.fr-check[data-check="scope-items"]')
        when = self.d["memo"].checked_on("資料W-2（")
        self.assertIn(f"確認日 {self.reading.jp_date(when)}", node.get_text())
        d = copy.deepcopy(self.d)
        d["cfg"]["issues"][FIRST]["memo_checks"][0]["memo_section"] = "資料N（"  # 大綱（法律案の前）の節
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d["cfg"]["issues"][FIRST]["memo_checks"][0]["memo_section"] = "存在しない見出し"
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_sunk_notes_split_rechecks(self):
        for sc in PUBLIC["ocean_layer"]["sunk_continents"]:
            iid = self.reading.sunk_issue(self.d, sc)
            node = self.panel(iid).select_one(f'[data-sunk="{sc["id"]}"]')
            if node is None:
                continue
            n = len(self.reading.RECHECK.findall(sc["sns_note"]))
            self.assertEqual(len(node.select(".fr-rechecks li")), n, sc["id"])


class AllIssuesAndBackgroundTests(unittest.TestCase):
    """手順6：全論点の完成と背景の開閉行。時制は冒頭の law と同じ判定で切り替わる。"""

    @classmethod
    def setUpClass(cls):
        from scripts import consumption_tax_reading as reading
        import consumption_tax_background as background  # 読書面の生成器と同じモジュール（scripts/ を import 経路に足した後）

        cls.reading, cls.background = reading, background
        cls.tmp = tempfile.TemporaryDirectory()
        cls.html = reading.build(Path(cls.tmp.name) / "a").read_text(encoding="utf-8")
        cls.s = soup_of(cls.html)
        cls.d = reading.load()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def bg_at(self, as_of, enacted=None):
        d = copy.deepcopy(self.d)
        if enacted:
            d["ocfg"]["law"]["enacted_on"] = enacted
            d["ocfg"]["checked_on"] = enacted
        return soup_of(self.background.render(d, as_of, []))

    def test_all_issues_complete_with_two_posts(self):
        for issue in PUBLIC["issues"]:
            icfg = self.d["cfg"]["issues"][issue["id"]]
            self.assertEqual(icfg["status"], "complete", issue["id"])
            self.assertEqual(len(icfg["posts"]["items"]), 2, issue["id"])
            self.assertTrue(icfg["posts"]["selection_basis"])
        ids = [p["id"] for c in self.d["cfg"]["issues"].values() for p in c["posts"]["items"]]
        self.assertEqual(len(ids), 14)
        self.assertEqual(len(set(ids)), 14)

    def test_unpublished_only_where_reread_is_missing(self):
        for issue in PUBLIC["issues"]:
            node = self.s.find(id="issue-" + issue["id"]).select_one("[data-unpublished]")
            self.assertEqual(node is None, issue["label"] in WITH_REASONS, issue["label"])

    def test_rows_are_closed_details_and_links_resolve(self):
        rows = self.s.select("#consumption-tax-cut-background details.fb-row")
        self.assertEqual(len(rows), 8)
        self.assertEqual([r for r in rows if r.has_attr("open")], [])
        tide = "#" + self.d["cfg"]["trend"]["widget_id"]  # 潮目のカードは手順7で元HTMLから写す（試作には無い）
        for a in self.s.select('a[href^="#"]:not([href="#"])'):  # "#" はサイトの簡易ヘッダーのロゴ
            if a["href"] != tide:
                self.assertIsNotNone(self.s.find(id=a["href"][1:]), a["href"])

    def test_old_faq_anchor_and_no_overlap_with_opening(self):
        faq = self.s.find(id="tax-faq")
        self.assertIsNotNone(faq)
        qs = [dt.get_text() for dt in faq.select("dt")]
        self.assertIn("財源は決まっていますか？", qs)
        opening_qs = {a["question"] for a in self.d["ocfg"]["answers"]}
        self.assertEqual(set(qs) & opening_qs, set())

    def test_party_names_only_in_background(self):
        reading_text = self.s.select_one("#consumption-tax-cut-reading")
        for node in reading_text.select(".fr-desc, .fr-voice, .fr-post, .fr-check"):
            for w in PARTIES:
                self.assertNotIn(w, node.get_text())
        parties = self.s.find(id="bg-parties").get_text()
        self.assertIn("立憲民主党", parties)
        self.assertIn("0%", self.s.find(id="bg-parties").summary.get_text())

    def test_rates_come_from_opening_config(self):
        text = self.s.find(id="bg-rate").get_text()
        r = self.d["ocfg"]["rates"]["special"]
        self.assertIn(f'国税{r["national"]}%と地方消費税{r["local"]}%', text)

    def test_tense_switches_with_law_phase(self):
        bill = self.bg_at(PUBLIC["updated_on"])
        self.assertEqual(bill.section["data-phase"], "bill")
        self.assertIn("まだ成立していません", bill.find(id="bg-status").h4.get_text())
        self.assertIn("国会の審議日程", bill.find(id="bg-unverified").get_text())
        overdue = self.bg_at("2027-05-01")
        self.assertEqual(overdue.section["data-phase"], "overdue")
        self.assertIn("成立したかどうかは未確認", overdue.find(id="bg-status").h4.get_text())
        states = [li["data-state"] for li in overdue.select("ol.fb-timeline > li[data-step]")]
        self.assertIn("unconfirmed", states)
        for as_of, phase in (("2026-12-01", "enacted"), ("2028-01-01", "in_effect"), ("2029-04-02", "ended")):
            s = self.bg_at(as_of, enacted="2026-11-20")
            self.assertEqual(s.section["data-phase"], phase)
            self.assertIn("法律で決まったこと", s.find(id="bg-status").h4.get_text())
            self.assertNotIn("国会の審議日程", s.find(id="bg-unverified").get_text())
            self.assertNotIn("法律案", s.find(id="bg-status").h4.get_text())

    def test_timeline_uses_opening_steps(self):
        steps = [li["data-step"] for li in self.s.select("#bg-timeline ol.fb-timeline > li[data-step]")]
        self.assertEqual(steps, [st["key"] for st in self.d["ocfg"]["steps"]["items"]])
        states = [li["data-state"] for li in self.s.select("#bg-timeline ol.fb-timeline > li[data-step]")]
        self.assertEqual(states, self.reading.opening.step_states(self.d["ocfg"], PUBLIC["updated_on"]))

    def test_trust_check_follows_phase_and_requires_new_memo_after_enactment(self):
        node = self.s.select_one('[data-check="trust-status"]').get_text()
        self.assertIn("成立していません", node)
        d = copy.deepcopy(self.d)
        d["ocfg"]["law"]["enacted_on"] = "2026-11-20"
        d["ocfg"]["checked_on"] = "2026-11-20"
        with self.assertRaises(SystemExit):  # 成立を確かめた一次資料メモの節を指していない
            self.reading.check_all(d)

    def test_background_memo_sections_after_bill(self):
        d = copy.deepcopy(self.d)
        d["bg"]["cfg"]["groups"][0]["rows"][0]["items"][0]["memo_section"] = "資料N（"
        with self.assertRaises(SystemExit):
            self.background.check(d)

    def test_classroom_is_read_from_shared_config(self):
        cr = json.loads((ROOT / "configs/classroom/consumption-tax-cut.json").read_text(encoding="utf-8"))
        text = self.s.find(id="bg-classroom").get_text()
        for q in cr["questions"]:
            self.assertIn(q, text)

    def test_panel_height_budget_inputs(self):
        """375pxの高さは Playwright で測る（設計記録）。ここでは理由の名前が長すぎないことだけ見る（3行に折り返すと欄が伸びる）。"""
        for iid, icfg in self.d["cfg"]["issues"].items():
            issue = next(i for i in PUBLIC["issues"] if i["id"] == iid)
            rr = self.d["reread"].get(issue["label"])
            for bid, b in (rr["buckets"].items() if rr else []):
                self.assertLessEqual(len(self.reading.reason_label(self.d, icfg, bid, b)), 34, (iid, bid))



# ---------------------------------------------------------------- 手順7：公開候補と更新経路

from scripts import build_consumption_tax_redesign as redesign  # noqa: E402
from scripts import consumption_tax_layout as layout  # noqa: E402

AS_OF = PUBLIC["updated_on"]
INPUTS = (
    "THEMES.yaml",
    "docs/data/themes/consumption-tax-cut.json",
    "data/public/themes/consumption-tax-cut.json",
    "data/consumption-tax-cut_4issues-reread.json",
    "data/consumption-tax-cut_reread-stances.json",
    "data/consumption-tax-cut_claim_posts.json",
    "quality/research/consumption-tax-cut-primary-sources.md",
)
# 旧ページの JS・CSS の内部用id（外から指す意味の無いもの）
LEGACY_IDS_INTERNAL = ("tax-reason-", "tax-concern-count-", "tax-source-note-", "pseg", "pbar", "pnum", "c-", "s-", "ro-",
                       "vote-", "share-x", "seafloor", "seacover", "spin", "dot-", "back", "btn-'", "explainer-modal",
                       "chartdesc", "floor-note", "dive", "divenote", "q", "consumption-tax-cut-trend-panel-")
SHOWN = [i for i in PUBLIC["issues"] if int(i["count"]) > 0]
TREND_PANEL_ISSUE = "consumption-tax-cut-trend-panel-issue"


def protected(text: str, name: str) -> str:
    return re.search(f"<!-- {name}_START -->.*?<!-- {name}_END -->", text, re.S).group()


def vote_defs(text: str) -> tuple[str, str, str, str]:
    """投票の topic・論点（VOTE_ISSUES）・立場（STANCES）・番号の対応（CHOICES）。どれも元HTMLと1文字も変えない。"""
    topic = re.search(r"var TOPIC='([^']+)'", text).group(1)
    issues = re.search(r"var VOTE_ISSUES=\[(.*?)\];", text, re.S).group(1)
    stances = re.search(r"var STANCES=\[(.*?)\];", text, re.S).group(1)
    choices = re.search(r"var CHOICES=(\{.*?\});", text, re.S).group(1)
    return topic, issues, stances, choices


def visible_text(html: str) -> str:
    soup = soup_of(html)
    for node in soup(["script", "style", "template"]):
        node.decompose()
    return soup.body.get_text()


def make_root(temp: str) -> Path:
    """公開候補の隔離コピーと同じ入力だけを持つ root（設定・公開JSON・再読データ・立場の対応表・一次資料メモ・元HTML）。"""
    root = Path(temp)
    shutil.copytree(ROOT / "configs", root / "configs")
    shutil.copytree(ROOT / "scripts/consumption_tax_redesign", root / "scripts/consumption_tax_redesign")
    for name in INPUTS:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, root / name)
    (root / layout.PAGE).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(layout.source_for_refresh(ROOT), root / layout.PAGE)
    return root


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
        cls.cfg = json.loads((ROOT / "configs/consumption-tax-cut-reading.json").read_text(encoding="utf-8"))

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

    def test_title_description_seo_and_article_are_inherited_verbatim(self):
        """title と meta description は元HTMLと1文字も変えない（ビルドで崩さない）。

        2026-10-16/17、オーナー判断で題名・説明文を変更した。課題96の10/27判定に混ざる（tasks/task-96.md）。
        """
        for name in ("SEO_META", "ARTICLE_JSON_LD", "ARTICLE_TRUST"):
            self.assertEqual(self.release.count(protected(self.source, name)), 1, name)
        self.assertEqual(self.s.head.title.get_text(), self.src.head.title.get_text())
        self.assertEqual(self.s.head.title.get_text(), "消費税減税はいつから？食料品1％・財源と賛成・反対の理由｜SNS反応まっぷ")
        self.assertEqual(self.s.select_one('meta[name="description"]')["content"],
                         self.src.select_one('meta[name="description"]')["content"])
        seo = json.loads((ROOT / "configs/theme-seo.json").read_text(encoding="utf-8"))
        entry = next(t for t in seo["themes"] if t["id"] == "consumption-tax-cut")
        self.assertEqual(self.s.select_one('meta[name="description"]')["content"], entry["description"])
        self.assertEqual(self.s.select('link[rel="canonical"]')[0]["href"],
                         "https://sns-reaction-map.jp/consumption-tax-cut-reaction-map.html")
        self.assertEqual(self.s.select_one('meta[property="og:image"]')["content"],
                         self.src.select_one('meta[property="og:image"]')["content"])
        self.assertEqual(len(self.s.select("h1")), 1)
        ids = Counter(t["id"] for t in self.s.find_all(id=True))
        self.assertEqual([k for k, v in ids.items() if v > 1], [])  # 同じidを2つ置かない
        for sel in ('link[href^="site-tokens.css"]', 'link[href^="topic-modern.css"]', 'script[src^="topic-modern.js"]'):
            self.assertEqual(str(self.s.select_one(sel)), str(self.src.select_one(sel)), sel)

    def test_ga_and_adsense_only_in_release(self):
        for name in ("GA_TAG", "ADSENSE_TAG"):
            block = protected(self.source, name)
            self.assertIn(block, self.release)
            self.assertNotIn(block, self.preview)
        self.assertIn("G-K10S4YCZFH", self.release)
        self.assertNotIn("G-K10S4YCZFH", self.preview)
        self.assertIn("pagead2.googlesyndication.com", self.release)
        self.assertNotIn("pagead2.googlesyndication.com", self.preview)
        self.assertEqual(self.s.select_one('meta[name="google-adsense-account"]')["content"], "ca-pub-2542211932832864")
        self.assertIn('name="robots" content="noindex"', self.preview)
        self.assertNotIn('name="robots"', self.release)

    def test_vote_contract_is_unchanged(self):
        """投票は 7論点×4立場＝28択。VOTE_ISSUES・STANCES・CHOICES を元と完全一致（並べ替え禁止）。保存キーは本番ホストだけ既存キー。"""
        src = vote_defs(self.source)
        self.assertEqual(src[0], "consumption-tax-cut-issue-stance-v1")
        for text in (self.release, self.preview):
            self.assertIn(f'data-vote-topic="{redesign.VOTE_TOPIC}"', text)
            self.assertEqual(vote_defs(text), src)
            self.assertIn("choiceIdx:CHOICES[issue.id][stance.id]", text)
            self.assertIn("var STORAGE_KEY=window.SNS_REDESIGN_PRODUCTION?'sns_vote_'+TOPIC+'_my':'sns_vote_'+TOPIC+'_my_preview';", text)
            self.assertNotIn(redesign.VOTE_STORAGE, text)
        self.assertEqual(len(re.findall(r"\bk:'", src[1])), 7)
        self.assertEqual(len(re.findall(r"\bk:'", src[2])), 4)
        choices = json.loads(src[3])
        self.assertEqual(sorted(v for row in choices.values() for v in row.values()), list(range(28)))
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=location.hostname==='sns-reaction-map.jp'", self.release)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=false", self.preview)
        scripts = self.s.select("script")
        config = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-config.js"))
        client = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-store.js"))
        self.assertEqual(config + 2, client)
        self.assertEqual(self.s.select_one("#vote-section > p").get_text(), self.src.select_one("#vote-section > p").get_text())

    def test_adapter_vote_fingerprint_matches_source(self):
        from scripts.refresh_adapters.consumption_tax import vote_fingerprint
        self.assertEqual(vote_fingerprint(self.source), vote_fingerprint(self.release))
        self.assertEqual(vote_fingerprint(self.release)[3], 28)

    def test_faq_json_ld_matches_visible_faq(self):
        payloads = [json.loads(x.get_text()) for x in self.s.select('script[type="application/ld+json"]')]
        faq = [p for p in payloads if p.get("@type") == "FAQPage"]
        self.assertEqual(len(faq), 1)
        visible = redesign.faq_items(self.s)
        bg = json.loads((ROOT / "configs/consumption-tax-cut-background.json").read_text(encoding="utf-8"))
        rows = [r for g in bg["groups"] for r in g["rows"] if r["kind"] == "faq"]
        self.assertEqual(len(visible), 3 + len(rows[0]["items"]))  # 冒頭の短答3問＋背景の「よくある質問」
        self.assertEqual([q for q, _a in visible[:3]], ["いつから・何%・いつまで？", "1%と給付付き税額控除とは？", "何が1%になる？"])
        self.assertEqual([(q["name"], q["acceptedAnswer"]["text"]) for q in faq[0]["mainEntity"]], visible)
        texts = re.sub(r"\s+", " ", self.s.get_text())
        for q, a in visible:
            self.assertIn(q, texts)
            self.assertIn(a, texts)
        self.assertEqual(sum(1 for p in payloads if p.get("@type") == "Article"), 1)
        self.assertNotIn("FAQ_JSON_LD", self.source)  # 現行ページには FAQPage が無かった
        # 旧ページの検索入口・連動表示・テーマ共通の見た目は読み込まない（計算部品の税率は冒頭の設定だけが正）
        for name in ("consumption-tax-connected.js", "consumption-tax-connected-page.js", "consumption-tax-connected.css",
                     "consumption-tax-search-entry.js", "consumption-tax-search-entry.css", "theme-design.js", "theme-design.css"):
            self.assertNotIn(f'="{name}', self.release)
        self.assertIsNone(self.s.select_one("#tax-connected-data"))

    def test_inherited_sections_and_links(self):
        self.assertEqual(len(self.s.select("#planet-data")), 1)
        self.assertEqual(self.s.select_one("#planet-data").string, self.src.select_one("#planet-data").string)
        self.assertIn("世論調査", self.s.select_one("#caution").get_text())
        for sel in ("#related-topics", "body > footer", "#related-theme-tracking"):
            self.assertEqual(self.s.select_one(sel).get_text(), self.src.select_one(sel).get_text(), sel)
        hrefs = {a["href"] for a in self.s.select("footer a[href]")}
        for href in ("about.html#operator", "about.html#method", "privacy.html", "disclaimer.html"):
            self.assertIn(href, hrefs)
        self.assertIn(f'<time datetime="{PUBLIC["updated_on"]}">', self.release)
        self.assertIsNotNone(self.s.select_one('header.modern-site-header a[href="index.html"]'))

    def test_detail_data_kept_and_closed(self):
        detail = self.s.select_one("#detail-data")
        src = self.src.select_one("#detail-data")
        self.assertEqual([d.summary.get_text() for d in detail.select(":scope > details")],
                         [d.summary.get_text() for d in src.select(":scope > details")])
        self.assertEqual(detail.select("details[open]"), [])
        self.assertIn("注意", [d.summary.get_text() for d in detail.select(":scope > details")])

    def test_trend_card_is_inherited_verbatim_inside_fold(self):
        """意見の推移（10回分）は枠ごと1文字も変えずに折りたたみへ。外部の埋め込みコードが指す2つの id を残す。"""
        block = re.search(r'<section class="update-dashboard"><!-- TREND_CARD_START -->.*?<!-- TREND_CARD_END --></section>',
                          self.source, re.S).group()
        self.assertEqual(self.release.count(block), 1)
        self.assertIn("/* TREND_CARD_START */", self.release)
        fold = self.s.select_one("#cap-trend-more")
        self.assertEqual(fold.name, "details")
        self.assertFalse(fold.has_attr("open"))
        for panel in redesign.TREND_PANELS:
            self.assertIsNotNone(fold.find(id=panel), panel)
        panels = redesign._trend_rounds(block)
        glance = self.s.select_one("#cap-trend .cap-trend-glance")
        self.assertEqual(len(glance.select(".cap-trend-spark svg polyline")), len(panels["stance"]["labels"]))
        self.assertIn(f'{len(panels["stance"]["rounds"])}回', glance.select_one("h2").get_text())
        self.assertLess(self.release.index("TREND_CARD_START -->"), self.release.index('id="vote-section"'))

    def test_trend_note_mentions_small_sample_old_posts_and_model_switch(self):
        """ひと目の注記1行：1回あたりの件数とぶれ・古い投稿の混入・分類AIの切替（10/3）。数字は推移の注意書きから写す。"""
        note = self.s.select_one("#cap-trend .cap-trend-note").get_text()
        rounds = redesign._trend_rounds(self.release)["stance"]["rounds"]
        self.assertIn(f'{min(r["n"] for r in rounds)}〜{max(r["n"] for r in rounds)}件', note)
        self.assertIn("ポイント前後のぶれ", note)
        self.assertRegex(note, r"古い投稿の混入は、回ごとに最大\d+%")
        self.assertIn("2026年10月3日の回から分類に使うAIが替わった", note)
        card = self.s.select_one("#cap-trend-more").get_text()
        self.assertIn("2026年10月3日の回から、分類に使うAIを切り替えました", card)

    def test_issue_glance_from_trend(self):
        panels = redesign._trend_rounds(self.release)
        issue = panels["issue"]
        for i in SHOWN:
            box = self.s.find(id="issue-" + i["id"]).select_one(".fr-glance")
            link = box.select_one(".fr-glance-link")
            # 飛び先は引き継いだ推移の「論点の変化」のタブ（外部の埋め込みコードと同じ id）
            self.assertEqual((link["href"], link["data-tide-mode"]), ("#" + TREND_PANEL_ISSUE, "issue"))
            self.assertIsNotNone(self.s.find(id=TREND_PANEL_ISSUE))
            cap = box.select_one(".fr-glance-cap")
            if i["label"] not in issue["labels"]:
                self.assertIn("fr-glance-missing", cap["class"], i["id"])
                self.assertIsNone(box.select_one(".fr-glance-chart svg"))
                continue
            j = issue["labels"].index(i["label"])
            self.assertIn(f'{issue["rounds"][0]["v"][j]:.1f}%', cap.get_text())
            self.assertIn(f'{issue["rounds"][-1]["v"][j]:.1f}%', cap.get_text())
            self.assertNotIn("件", box.select_one(".fr-glance-chart").get_text())
        self.assertEqual({i["label"] for i in SHOWN} - set(issue["labels"]), {"その他"})

    def test_method_fold_holds_trust_and_detail_data(self):
        method = self.s.select_one("#cap-method")
        self.assertEqual(method.name, "details")
        self.assertFalse(method.has_attr("open"))
        self.assertIsNotNone(method.select_one("#detail-data"))
        trust = protected(self.source, "ARTICLE_TRUST")
        self.assertLess(self.release.index('id="cap-method"'), self.release.index(trust))
        self.assertLess(self.release.index(trust), self.release.index('id="related-topics"'))

    def test_folds_start_closed(self):
        for sel in ("#consumption-tax-cut-reading", "#consumption-tax-cut-background", "#tax-open", "#cap-trend", "#cap-method"):
            # 推移のカードの中（画像の使い方の欄）は元HTMLのまま。外側の折りたたみ #cap-trend-more が閉じている
            opened = [d.get("class") for d in self.s.select(sel + " details[open]") if not d.find_parent(id="cap-trend-more")]
            self.assertEqual(opened, [], sel)
        self.assertEqual(len(self.s.select("#consumption-tax-cut-background details.fb-row")), 8)

    def test_default_issue_is_top_count_and_unpublished_reasons(self):
        """最初に開く論点は件数1位（山なみの自動選択と同じ）。再読の無い3論点は「理由は未公開」。"""
        top = max(SHOWN, key=lambda i: int(i["count"]))
        self.assertEqual(self.s.select_one("#consumption-tax-cut-reading")["data-default-issue"], top["id"])
        self.assertIn("data-default-issue", redesign.AUTO_LAND_OFF)
        for i in SHOWN:
            panel = self.s.find(id="issue-" + i["id"])
            has = i["label"] in WITH_REASONS
            self.assertEqual(panel.select_one("[data-unpublished]") is None, has, i["id"])

    def test_classroom_section_contract(self):
        section = self.release[self.release.index("<!-- CLASSROOM_START -->"):self.release.index("<!-- CLASSROOM_END -->")]
        self.assertIn('class="classroom-print-btn"', section)
        self.assertIn("classroom-sources", section)
        self.assertIn("classroom-questions", section)
        self.assertIn("sankou15.pdf", section)  # 授業の資料は法律案の概要
        self.assertNotIn("法律はまだ成立していない", section)
        self.assertEqual(self.release.count("<!-- CLASSROOM_START -->"), 1)
        self.assertLess(self.release.index("<!-- CLASSROOM_START -->"), self.release.index("<!-- ARTICLE_TRUST_START -->"))

    def test_party_names_only_in_parties_row_and_inherited_parts(self):
        """読書面の文には政党名を書かない（0%案と各党の案は背景の行だけ）。"""
        reading = self.s.select_one("#consumption-tax-cut-reading .fr-panels")
        for node in reading.select(".x-embed, script, template, #planet-block"):
            node.decompose()
        for word in PARTIES:
            self.assertNotIn(word, reading.get_text(), word)

    def test_old_anchor_targets_exist(self):
        for target in set(redesign.ALIASES.values()):
            self.assertIsNotNone(self.s.find(id=target), target)
        hidden = ("progress", "fallback", "fallback-nav", "quiz")
        for alias in redesign.ALIASES:
            if alias in hidden:
                continue
            self.assertIsNone(self.s.find(id=alias), alias)
        for kept in ("planet-block", "modes", "tax-faq"):
            self.assertIsNotNone(self.s.find(id=kept), kept)
            self.assertNotIn(kept, redesign.ALIASES)
        # 旧ページで外から指せた節のidは、新ページにあるか、読み替え先があるか（JS・CSS の内部用idは除く）
        for node in self.src.find_all(id=True):
            old = node["id"]
            if self.s.find(id=old) is not None or old in redesign.ALIASES or old.startswith(LEGACY_IDS_INTERNAL):
                continue
            self.assertTrue(any(old.startswith(p) for p in redesign.ISSUE_PREFIXES), old)
        for i in SHOWN:
            self.assertIsNotNone(self.src.find(id="issue-" + i["id"]))
            self.assertEqual(self.s.find(id="issue-" + i["id"])["data-issue-panel"], i["id"])
        for kept in ("vote-section", "detail-data", "related-topics", "caution", "planet-data", "research-conditions",
                     "consumption-tax-cut-trend", *redesign.TREND_PANELS, "bg-classroom", "article-trust-title", "tax-faq", "cto-count"):
            self.assertIsNotNone(self.s.find(id=kept), kept)
        targets = set()
        for base in ("docs", "scripts", "configs", "company"):
            for path in (ROOT / base).rglob("*"):
                if path.suffix not in (".html", ".py", ".json", ".js", ".md", ".txt", ".xml", ".yaml") or path.name == redesign.PAGE:
                    continue
                targets |= set(re.findall(r"consumption-tax-cut-reaction-map\.html#([A-Za-z0-9_-]+)",
                                          path.read_text(encoding="utf-8", errors="ignore")))
        for t in targets:
            self.assertTrue(self.s.find(id=t) is not None or t in redesign.ALIASES
                            or any(t.startswith(p) for p in redesign.ISSUE_PREFIXES), t)

    def test_planet_is_copied_from_source(self):
        """全体像の山なみは、元HTMLの対話式の山なみ（PLANET_SECTION）をそのまま写す（読み込み時の論点の選び方だけ置き換える）。"""
        src_section = re.search(r"<!-- PLANET_SECTION_START -->(.*?)<!-- PLANET_SECTION_END -->", self.source, re.S).group(1)
        src = soup_of(src_section)
        src_script = [x for x in src.find_all("script", recursive=False) if x.get("id") != "planet-data"][0].string
        self.assertEqual(src_script.count(redesign.AUTO_LAND), 1)
        self.assertEqual(self.release.count(src_script.replace(redesign.AUTO_LAND, redesign.AUTO_LAND_OFF)), 1)
        self.assertEqual(self.release.count(src.select_one("section.planet-panel > style").string), 1)
        self.assertEqual(self.release.count("window.PLANET_DATA="), 1)  # PLANET_DATA は1つだけ
        planet = self.s.select_one("#consumption-tax-cut-reading .fr-map section.planet-panel #planet-block")
        self.assertIsNotNone(planet)
        self.assertLess(self.release.index('id="planet-block"'), self.release.index('class="fr-tabs"'))
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
        self.assertLess(self.release.index(src_script[:200]), self.release.index("window.ConsumptionTaxReading"))
        self.assertLess(self.release.index("window.ConsumptionTaxReading"), self.release.index("function goReading"))

    def test_planet_follows_source_updates_and_stops_on_changes(self):
        changed = self.source.replace("このページの見かた", "このページの見かた（更新確認）", 1)
        self.assertNotEqual(changed, self.source)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.html"
            path.write_text(changed, encoding="utf-8")
            redesign.build(path, Path(temp) / "out", "release", as_of=AS_OF)
            self.assertIn("このページの見かた（更新確認）", (Path(temp) / "out" / redesign.PAGE).read_text(encoding="utf-8"))
        for old, new, message in (
                (redesign.AUTO_LAND, redesign.AUTO_LAND.replace("land(idIndex[h]);", "land(idIndex[h], {});"), "自動着地"),
                (redesign.VOTE_STORAGE, "var STORAGE_KEY='sns_vote_'+TOPIC+'_v2';", "保存キー"),
                ('id="consumption-tax-cut-trend-panel-issue"', 'id="consumption-tax-cut-trend-panel-issues"', "trend-panel-issue")):
            moved = self.source.replace(old, new, 1)
            self.assertNotEqual(moved, self.source)
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "source.html"
                path.write_text(moved, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    redesign.build(path, Path(temp) / "out", "release", as_of=AS_OF)

    def test_no_legacy_widgets(self):
        for marker in ("TAX_SEARCH_ENTRY_START", "THEME_DESIGN_START", "TAX_CONNECTED_START", "TAX_CONNECTED_CONTENT_START",
                       "STANCE_GLANCE_START", "ISSUE_CARDS_START", "CLAIM_AUDIT_START", "BACKGROUND_CONTEXT_START"):
            self.assertNotIn("<!-- " + marker, self.release)
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.release)
        self.assertEqual(self.s.select("#bukatsu-background, #bukatsu-check, #stance-glance, #tax-brief, #claim-audit"), [])
        for embed in self.s.select(".x-embed"):
            self.assertRegex(embed.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")
        # レシートの税率は冒頭の設定から（JS は税率を持たない）
        self.assertIsNotNone(self.s.select_one("#cto-calc-data"))

    def test_phase_switch_after_enactment(self):
        """成立日を仮に入れ、一次資料メモに成立を確かめた節を足すと、--as-of で成立後・引下げ中・終了の文に切り替わり、生成は止まらない。
        成立を確かめないまま引下げ開始日を過ぎた基準日（overdue）でも止まらない（docs には入れない。隔離した root で作る）。"""
        with tempfile.TemporaryDirectory() as temp:
            root = make_root(temp)
            redesign.build(root / layout.PAGE, root / "overdue", "release", root=root, as_of="2027-05-01")
            page = soup_of((root / "overdue" / redesign.PAGE).read_text(encoding="utf-8"))
            self.assertEqual(page.select_one("section.cto")["data-phase"], "overdue")
            path = root / "configs/consumption-tax-cut-opening.json"
            cfg = json.loads(path.read_text(encoding="utf-8"))
            cfg["law"].update({"enacted_on": "2026-11-20", "promulgated_on": "2026-11-27"})
            cfg["checked_on"] = "2026-11-30"
            path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
            memo = root / "quality/research/consumption-tax-cut-primary-sources.md"
            memo.write_text(memo.read_text(encoding="utf-8") + "\n### 資料Z（成立の確認・試験用）【2026-11-30追記】\n- 確認日: 2026-11-30\n",
                            encoding="utf-8")
            rpath = root / "configs/consumption-tax-cut-reading.json"
            rcfg = json.loads(rpath.read_text(encoding="utf-8"))
            rcfg["issues"]["consumption-tax-cut-political-trust"]["memo_checks"][0]["memo_section"] = "資料Z（成立の確認・試験用）"
            rpath.write_text(json.dumps(rcfg, ensure_ascii=False), encoding="utf-8")
            texts = {}
            for when, phase in (("2026-12-01", "enacted"), ("2027-05-01", "in_effect"), ("2029-04-02", "ended")):
                redesign.build(root / layout.PAGE, root / phase, "release", root=root, as_of=when)
                page = soup_of((root / phase / redesign.PAGE).read_text(encoding="utf-8"))
                self.assertEqual(page.select_one("section.cto")["data-phase"], phase)
                texts[phase] = page.select_one('[data-check="trust-status"]').get_text()
            self.assertIn("2026年11月20日に成立", texts["enacted"])
            self.assertIn("まで続きます", texts["in_effect"])
            self.assertIn("終わりました", texts["ended"])

    def test_provenance_counts_and_detects_mismatch(self):
        from scripts.consumption_tax_count_provenance import verified_selectors
        result = verified_selectors(self.release, ROOT)
        self.assertEqual(len(result), len(SHOWN) + 2)  # 論点の欄7つ＋冒頭の件数欄＋推移の要約の注記
        node = self.s.select_one(f"#issue-{FIRST} li.fr-reason .fr-reason-n b")
        broken = self.release.replace(str(node), str(node).replace(node.get_text(), str(int(node.get_text().replace(",", "")) + 1)), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)
        count = self.s.select_one(f"#issue-{FIRST} .fr-count b")
        broken = self.release.replace(str(count), str(count).replace(count.get_text(), "37"), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)
        line = self.s.select_one(f"#issue-{FIRST} article.fr-reason-detail .fr-reason-stance span")
        label = line["aria-label"]
        n = re.search(r"減税推進 (\d[\d,]*)件", label).group(1)
        broken = self.release.replace(label, label.replace(f"減税推進 {n}件", f"減税推進 {int(n.replace(',', '')) + 1}件"), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)


class LayoutTests(unittest.TestCase):
    """手順7：更新経路（materialize → 旧形式の全処理 → finish）と、公開後の単独実行。"""

    def test_disabled_has_no_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            root = make_root(temp)
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
            (root / layout.PAGE).write_text('<meta name="consumption-tax-layout">')
            (root / layout.CONFIG).write_text('{"enabled": true}')
            with self.assertRaisesRegex(ValueError, "更新元HTML"):
                layout.source_for_refresh(root)
            (root / layout.CONFIG).write_text('{"enabled": false}')
            with self.assertRaisesRegex(ValueError, "更新設定が無効"):
                layout.source_for_refresh(root)

    def test_pipeline_finish_keeps_source_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = make_root(temp)
            legacy = (root / layout.PAGE).read_text(encoding="utf-8")
            (root / layout.CONFIG).write_text('{"enabled": true}')
            targets = layout.finish(root, as_of=AS_OF)
            self.assertEqual(set(targets), {layout.SOURCE, layout.PAGE})
            first = (root / layout.PAGE).read_bytes()
            self.assertIn(b'name="consumption-tax-layout"', first)
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
            root = make_root(temp)
            (root / layout.CONFIG).write_text('{"enabled": true}')
            path = root / "data/consumption-tax-cut_4issues-reread.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            node = raw[WITH_REASONS["減税の対象範囲"]]
            gone = node["items"].pop(0)
            node["buckets"][gone["bucket"]]["count"] -= 1
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            before = (root / layout.PAGE).read_bytes()
            with self.assertRaisesRegex(ValueError, "照合で停止"):
                layout.finish(root, as_of=AS_OF)
            self.assertEqual(before, (root / layout.PAGE).read_bytes())
            self.assertFalse((root / layout.SOURCE).exists())

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では、更新経路の立場の対応表を作れない")
    def test_adapter_rebuilds_stance_table_and_stops_without_reread(self):
        """更新経路（refresh_adapters/consumption_tax.py）は、累積候補から立場の対応表を作り直す（辺野古・自転車と同じ）。
        新しい意見が再読データの明細に無ければ、何を直すかが分かる形で止まる。"""
        from scripts.refresh_adapters.consumption_tax import build_reread_stances
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("THEMES.yaml", "data/consumption-tax-cut_4issues-reread.json", "configs/planet/consumption-tax-cut.yaml"):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, root / name)
            candidate = root / "cumulative-candidate.json"
            shutil.copy2(CANON, candidate)
            data = build_reread_stances(root, candidate, root / "stances.json", "2026-10-20")
            self.assertEqual(data["stances"], STANCES["stances"])
            self.assertEqual((data["made_on"], data["public_mismatch"]), ("2026-10-20", 0))
            path = root / "data/consumption-tax-cut_4issues-reread.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw[WITH_REASONS["減税の効果"]]["items"].pop(0)
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "追い読み"):
                build_reread_stances(root, candidate, root / "stances.json", "2026-10-20")

    def test_model_switch_is_recorded_for_trend(self):
        """分類AIの切替（10/3 kimi-k2.7-code）が推移の注意書きの記録にある。次にAIが変わった回は adapter が止まる。"""
        from scripts import build_trend_section as trend
        from scripts.refresh_adapters import trend_support
        self.assertEqual(trend.TREND_THEMES["consumption-tax-cut"]["model_breaks"],
                         {"stance": ["2026-10-03"], "issue": ["2026-10-03"]})
        trend_support.check_model_break(ROOT, "consumption-tax-cut", "2026-10-03", "kimi-k2.6", "kimi-k2.7-code")
        with self.assertRaisesRegex(ValueError, "model_breaks"):
            trend_support.check_model_break(ROOT, "consumption-tax-cut", "2026-10-20", "kimi-k2.7-code", "next-model")

    def test_refresh_path_is_wired(self):
        refresh = (ROOT / "scripts/refresh_topic.py").read_text(encoding="utf-8")
        self.assertEqual(refresh.count("finish_consumption_tax_layout(candidate_root)"), 2)
        self.assertEqual(refresh.count("materialize_consumption_tax(candidate_root)"), 1)
        self.assertIn("consumption_tax_layout_enabled(root)", refresh)
        adapter = (ROOT / "scripts/refresh_adapters/consumption_tax.py").read_text(encoding="utf-8")
        self.assertIn("current_page = source_for_refresh(root)", adapter)
        self.assertIn("build_reread_stances(root, candidate,", adapter)
        self.assertIn("REREAD_STANCES: first_stances", adapter)
        self.assertIn("check_model_break(", adapter)
        self.assertIn("materialize_consumption_tax(target)", (ROOT / "scripts/verify_builder_rebuildability.py").read_text(encoding="utf-8"))
        self.assertIn("consumption_tax_redesign_provenance", (ROOT / "scripts/consumption_tax_count_provenance.py").read_text(encoding="utf-8"))
        for path in ("scripts/apply_theme_design.py", "scripts/seo/apply_classroom_section.py", "scripts/seo/apply_theme_trust.py",
                     "scripts/refresh_planet_section.py", "scripts/verify_theme_page.py", "scripts/build_consumption_tax_page.py",
                     "scripts/consumption_tax_count_provenance.py"):
            self.assertIn("consumption-tax-layout", (ROOT / path).read_text(encoding="utf-8"), path)
        self.assertNotIn("MODIFIED_AT = ", (ROOT / "scripts/build_consumption_tax_page.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
