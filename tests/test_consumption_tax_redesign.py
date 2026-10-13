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


if __name__ == "__main__":
    unittest.main()
