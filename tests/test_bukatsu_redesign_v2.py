"""部活動の地域移行の新しい型（冒頭・読書面・背景の設定JSON化）の検査。

既存の tests/test_bukatsu_*.py（公開中の仕組み）は触らない。正典を読む検査は、正典が無い環境ではスキップする。
"""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from scripts import bukatsu_opening as opening
from scripts import bukatsu_reading as reading

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "social-samples/bukatsu-chiiki_hermes_classified.json"
PUBLIC = json.loads((ROOT / "docs/data/themes/bukatsu-chiiki.json").read_text(encoding="utf-8"))


def write_config(cfg: dict) -> Path:
    tmp = Path(tempfile.mkdtemp()) / "opening.json"
    tmp.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    return tmp


class OpeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads(opening.DEFAULT_CONFIG.read_text(encoding="utf-8"))
        cls.data = opening.load_inputs()
        cls.html = opening.render_fragment(cls.data)
        cls.soup = BeautifulSoup(cls.html, "html.parser")

    def test_same_input_same_output(self):
        self.assertEqual(self.html, opening.render_fragment(opening.load_inputs()))

    def test_prototype_is_current(self):
        out = ROOT / "quality/prototypes/bukatsu-chiiki-opening/opening-fragment.html"
        self.assertEqual(out.read_text(encoding="utf-8"), self.html)

    def test_default_as_of_is_public_updated_on(self):
        self.assertEqual(self.soup.select_one(".bko")["data-as-of"], PUBLIC["updated_on"])

    def test_phase_by_as_of(self):
        cases = {"2025-06-01": "suishin", "2026-10-08": "zenki", "2029-03-31": "zenki",
                 "2029-04-01": "kouki_unchecked", "2032-04-01": "ended"}
        for as_of, phase in cases.items():
            self.assertEqual(opening.phase_of(self.cfg, as_of), phase, as_of)
        cfg = copy.deepcopy(self.cfg)
        cfg["period"]["midterm_checked_on"] = "2029-05-01"
        self.assertEqual(opening.phase_of(cfg, "2029-04-15"), "kouki_unchecked")
        self.assertEqual(opening.phase_of(cfg, "2029-06-01"), "kouki")

    def test_texts_switch_with_phase(self):
        for as_of in ("2025-06-01", "2028-05-01", "2029-06-01", "2033-01-01"):
            html = opening.render_fragment(self.data, as_of)
            phase = opening.phase_of(self.cfg, as_of)
            self.assertIn(f'data-phase="{phase}"', html)
            self.assertIn(self.cfg["phase_text"]["status_label"][phase], html)
        self.assertIn("前期の3年目", opening.render_fragment(self.data, "2028-05-01"))

    def test_h1_matches_display_headline(self):
        seo = json.loads((ROOT / "configs/theme-seo.json").read_text(encoding="utf-8"))
        entry = next(t for t in seo["themes"] if t["id"] == "bukatsu-chiiki")
        self.assertEqual(self.soup.select_one("h1").get_text(), entry["display_headline"])
        cfg = copy.deepcopy(self.cfg)
        cfg["title"]["sub"] = ["別の副題"]
        with self.assertRaises(SystemExit):
            opening.load_inputs(write_config(cfg))

    def test_checked_on_is_single_and_matches_memo(self):
        nodes = self.soup.select("[data-checked-on]")
        self.assertTrue(nodes)
        self.assertEqual({n["data-checked-on"] for n in nodes}, {self.cfg["checked_on"]})
        cfg = copy.deepcopy(self.cfg)
        cfg["checked_on"] = "2026-10-20"
        with self.assertRaises(SystemExit):
            opening.load_inputs(write_config(cfg))

    def test_period_order_stops(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["period"]["kouki_from"] = "2029-05-01"
        with self.assertRaises(SystemExit):
            opening.load_inputs(write_config(cfg))

    def test_counts_from_public_json(self):
        self.assertIn(f'{PUBLIC["opinion_count"]:,}', self.soup.select_one(".bko-poster").get_text())
        rows = self.soup.select(".bko-issue")
        self.assertEqual(len(rows), len(PUBLIC["issues"]))
        self.assertEqual(sum(int(r.select_one("b").get_text().replace("件", "").replace(",", "")) for r in rows),
                         PUBLIC["opinion_count"])
        self.assertEqual(rows[-1]["data-issue"], "bukatsu-chiiki-sonota")

    def test_no_reason_flags_only_where_reread_is_missing(self):
        flagged = {r["data-issue"] for r in self.soup.select(".bko-issue") if r.select_one(".bko-flag")}
        self.assertEqual(flagged, {"bukatsu-chiiki-kakusa", "bukatsu-chiiki-sonota"})

    def test_three_answers_keep_search_skeleton(self):
        self.assertEqual([h.get_text() for h in self.soup.select(".bko-answer h2")], ["いつから？", "費用はいくら？", "何が問題？"])
        self.assertIn("2026〜2031年度", self.soup.select_one(".bko-answer--when").get_text())
        self.assertIn("地域展開", self.soup.select_one(".bko-name-note").get_text())

    def test_midterm_shown_as_target_and_unconfirmed_after(self):
        before = BeautifulSoup(opening.render_fragment(self.data), "html.parser")
        self.assertEqual(len(before.select(".bko-step--target")), 1)
        after = BeautifulSoup(opening.render_fragment(self.data, "2029-06-01"), "html.parser")
        self.assertEqual(len(after.select(".bko-step--unconfirmed")), 1)

    def test_no_trial_wording(self):
        self.assertNotIn("試作", self.soup.get_text())


def reading_config(mutate) -> Path:
    cfg = json.loads(reading.CONFIG.read_text(encoding="utf-8"))
    mutate(cfg)
    tmp = Path(tempfile.mkdtemp()) / "reading.json"
    tmp.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    return tmp


class ReadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = reading.load()
        reading.check_all(cls.d)
        cls.html = reading.render_page(cls.d, reading.default_as_of(cls.d))
        cls.soup = BeautifulSoup(cls.html, "html.parser")
        cls.cfg = cls.d["cfg"]

    def panel(self, iid):
        return self.soup.select_one(f'[data-issue-panel="{iid}"]')

    def test_same_input_same_output(self):
        d = reading.load()
        self.assertEqual(self.html, reading.render_page(d, reading.default_as_of(d)))

    def test_prototype_is_current(self):
        out = ROOT / "quality/prototypes/bukatsu-chiiki-reading/index.html"
        self.assertEqual(out.read_text(encoding="utf-8"), self.html)

    def test_issue_order_count_desc_other_last(self):
        tabs = [a["data-issue-id"] for a in self.soup.select(".fr-tab")]
        self.assertEqual(tabs[-1], "bukatsu-chiiki-sonota")
        counts = {i["id"]: i["count"] for i in PUBLIC["issues"]}
        self.assertEqual(tabs[:-1], sorted(tabs[:-1], key=lambda i: -counts[i]))

    def test_counts_and_stances_match_public_json(self):
        for issue in PUBLIC["issues"]:
            p = self.panel(issue["id"])
            self.assertEqual(p.select_one(".fr-count b").get_text(), f'{issue["count"]:,}')
            legend = [int(b.get_text().replace(",", "")) for b in p.select(".fr-head-stance .fr-stance-mini b")]
            self.assertEqual(sum(legend), issue["count"])

    def test_reasons_recounted_and_excluded_not_listed(self):
        rr = self.d["reread"]["教員の働き方"]
        p = self.panel("bukatsu-chiiki-kyoin")
        listed = [li["data-reason"] for li in p.select(".fr-reasons .fr-reason")]
        self.assertNotIn("F", listed)
        self.assertNotIn("N", listed)
        self.assertEqual(listed[:4], ["B", "G", "L", "J"])
        self.assertEqual(int(p.select_one("[data-excluded]")["data-excluded"]), len(rr["excluded"]))

    def test_top_reasons_have_voice_in_complete_issues(self):
        for iid, icfg in self.cfg["issues"].items():
            if icfg.get("status") != "complete":
                continue
            issue = next(i for i in PUBLIC["issues"] if i["id"] == iid)
            for bid in reading.top_reason_ids(self.d, issue, icfg):
                self.assertTrue(icfg["reasons"][bid]["voice"], (iid, bid))

    def test_missing_voice_in_top_stops(self):
        def drop(cfg):
            cfg["issues"]["bukatsu-chiiki-kyoin"]["reasons"]["L"].pop("voice")
        d = reading.load(reading_config(drop))
        with self.assertRaises(SystemExit):
            reading.check_all(d)

    def test_reason_stances_come_from_stance_table(self):
        table = json.loads((ROOT / "data/bukatsu-chiiki_reread-stances.json").read_text(encoding="utf-8"))
        self.assertEqual(table["public_mismatch"], 0)
        self.assertEqual(sum(table["reread_stance_differs"].values()), 308)

    def test_stance_table_out_of_date_stops(self):
        d = reading.load()
        d["reread_items"] = d["reread_items"][:-1]
        table_path = ROOT / self.cfg["reread_stances_json"]
        table = json.loads(table_path.read_text(encoding="utf-8"))
        table["stances"].pop(next(iter(table["stances"])))
        tmp = Path(tempfile.mkdtemp()) / "t.json"
        tmp.write_text(json.dumps(table), encoding="utf-8")
        with self.assertRaises(SystemExit):
            reading.load(reading_config(lambda c: c.update(reread_stances_json=str(tmp))))

    def test_does_not_read_private_canonical(self):
        src = (ROOT / "scripts/bukatsu_reading.py").read_text(encoding="utf-8")
        self.assertNotIn("social-samples", src)
        self.assertNotIn("hermes_classified", src)

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では立場の対応表を確かめられない")
    def test_stance_table_matches_canonical(self):
        from scripts import bukatsu_reread_stances as rs
        built = rs.build("2026-10-14")
        stored = json.loads((ROOT / "data/bukatsu-chiiki_reread-stances.json").read_text(encoding="utf-8"))
        self.assertEqual(built["stances"], stored["stances"])

    def test_glance_chart_from_trend_source(self):
        p = self.panel("bukatsu-chiiki-kyoin")
        self.assertEqual(len(p.select(".fr-glance-chart svg")), 2)
        self.assertIsNone(self.panel("bukatsu-chiiki-sonota").select_one(".fr-glance-chart svg"))

    def test_posts_at_most_two_with_original_links(self):
        for iid, icfg in self.cfg["issues"].items():
            posts = icfg.get("posts", {}).get("items", [])
            self.assertLessEqual(len(posts), 2)
            p = self.panel(iid)
            for post in posts:
                self.assertIsNotNone(p.select_one(f'.x-embed[data-tweet-id="{post["id"]}"] a.x-original-link'))

    def test_posts_not_reused_from_current_page(self):
        published = (ROOT / "docs/bukatsu-chiiki-reaction-map.html").read_text(encoding="utf-8")
        for icfg in self.cfg["issues"].values():
            for post in icfg.get("posts", {}).get("items", []):
                self.assertNotIn(post["id"], published, post["id"])

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では代表投稿の選定基準を確かめられない")
    def test_selected_posts_meet_canonical_criteria(self):
        import re
        canon = json.loads(CANON.read_text(encoding="utf-8"))
        by_id = {str(r["tweet_id"]): r for r in canon}
        norm = lambda s: re.sub(r"\s+", "", s)
        texts = {}
        for r in canon:
            texts[norm(r["text"])] = texts.get(norm(r["text"]), 0) + 1
        labels = {i["id"]: i["label"] for i in PUBLIC["issues"]}
        for iid, icfg in self.cfg["issues"].items():
            for post in icfg.get("posts", {}).get("items", []):
                r = by_id[post["id"]]
                c = r["classification"]
                self.assertTrue(c["is_opinion"], post["id"])
                self.assertEqual(c["main_issue"], labels[iid], post["id"])
                self.assertTrue(c["article_usable"], post["id"])
                self.assertEqual(c["risk"], "low", post["id"])
                self.assertNotEqual(c["intensity"], "high", post["id"])
                self.assertEqual(texts[norm(r["text"])], 1, post["id"])
                self.assertEqual(r["url"], post["url"])
                self.assertNotIn("grok", r["url"].lower())
                if post.get("stance_id"):
                    sid = next(s["id"] for s in self.d["planet"]["stances"] if s["label"] == c["stance"])
                    self.assertEqual(sid, post["stance_id"], post["id"])

    def test_bad_posts_stop(self):
        def same(cfg):
            items = cfg["issues"]["bukatsu-chiiki-kyoin"]["posts"]["items"]
            items[1]["url"] = items[1]["url"].replace(items[1]["id"], "123")
        d = reading.load(reading_config(same))
        with self.assertRaises(SystemExit):
            reading.check_all(d)

    def test_memo_checks_after_current_guideline(self):
        for iid, icfg in self.cfg["issues"].items():
            for mc in icfg.get("memo_checks", []):
                self.assertGreaterEqual(self.d["memo"].checked_on(mc["memo_section"]), "2025-12-22", mc["id"])

    def test_js_entry_matches_published_app(self):
        js = (ROOT / "scripts/bukatsu_redesign/reading.js").read_text(encoding="utf-8")
        self.assertIn("window.BukatsuReading", js)
        self.assertIn("select(id, scroll)", js)

    def test_no_trial_wording_in_reading(self):
        self.assertNotIn("試作", self.soup.select_one("#bukatsu-chiiki-reading").get_text())


class AllIssuesAndBackgroundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts import bukatsu_background as bg
        cls.bg = bg
        cls.d = reading.load()
        reading.check_all(cls.d)
        cls.html = reading.render_page(cls.d, reading.default_as_of(cls.d))
        cls.soup = BeautifulSoup(cls.html, "html.parser")

    def test_all_issues_complete_with_two_posts_of_different_stances(self):
        for iid, icfg in self.d["cfg"]["issues"].items():
            self.assertEqual(icfg["status"], "complete", iid)
            posts = icfg["posts"]["items"]
            self.assertEqual(len(posts), 2, iid)
            issue = next(i for i in PUBLIC["issues"] if i["id"] == iid)
            self.assertEqual(len({reading.post_stance(self.d, issue, p) for p in posts}), 2, iid)

    def test_new_voices_and_read_counts(self):
        new = 0
        for iid, icfg in self.d["cfg"]["issues"].items():
            issue = next(i for i in PUBLIC["issues"] if i["id"] == iid)
            top = reading.top_reason_ids(self.d, issue, icfg)
            for bid in top:
                self.assertIn(bid, icfg["reasons_read"], (iid, bid))
                self.assertGreater(icfg["reasons_read"][bid], 0)
            new += len(top)
        self.assertEqual(new, 20)

    def test_unpublished_only_where_reread_is_missing(self):
        un = {p["data-issue-panel"] for p in self.soup.select("[data-issue-panel]") if p.select_one("[data-unpublished]")}
        self.assertEqual(un, {"bukatsu-chiiki-kakusa", "bukatsu-chiiki-sonota"})

    def test_rows_are_closed_details_and_links_resolve(self):
        rows = self.soup.select("#bukatsu-chiiki-background details.fb-row")
        self.assertGreaterEqual(len(rows), 6)
        self.assertTrue(all(not r.has_attr("open") for r in rows))
        ids = {e["id"] for e in self.soup.select("[id]")}
        for a in self.soup.select('a[href^="#"]'):
            if a["href"] != "#":
                self.assertIn(a["href"][1:], ids, a["href"])

    def test_faq_jsonld_matches_visible_faq_and_not_opening(self):
        ld = self.bg.faq_jsonld(self.d, reading.default_as_of(self.d))
        visible = [(dt.get_text(), dd.find(string=True)) for dt, dd in
                   zip(self.soup.select("#bg-faq .fb-faq dt"), self.soup.select("#bg-faq .fb-faq dd"))]
        self.assertEqual([(q["name"], q["acceptedAnswer"]["text"]) for q in ld["mainEntity"]], visible)
        opening_q = {a["question"] for a in self.d["ocfg"]["answers"]}
        self.assertFalse(opening_q & {q for q, _ in visible})

    def test_municipal_rows_come_from_catalog(self):
        rows = self.soup.select("#bg-municipal [data-muni-row]")
        self.assertEqual(len(rows), len(self.d["bg"]["municipal"]["rows"]))
        self.assertGreaterEqual(len(rows), 50)
        self.assertEqual(self.d["bg"]["municipal"]["checked_on"], "2026-09-23")
        self.assertTrue(self.soup.select_one("[data-muni-filter]").has_attr("hidden"))

    def test_timeline_uses_opening_steps(self):
        steps = [li["data-step"] for li in self.soup.select("#bg-timeline [data-step]")]
        self.assertEqual(steps, [s["key"] for s in self.d["ocfg"]["steps"]["items"]])

    def test_tense_switches_in_background(self):
        late = BeautifulSoup(reading.render_page(reading.load(), "2029-06-01"), "html.parser")
        self.assertEqual(late.select_one("#bukatsu-chiiki-background")["data-phase"], "kouki_unchecked")
        self.assertIn("中間評価の結果", late.select_one("#bg-unverified").get_text())
        # 中間評価の結果を確かめるまでは、平日の取組方針は「まだ決まっていないこと」に残る
        self.assertIn("平日の部活動の取組方針", late.select_one("#bg-status").get_text())
        self.assertEqual(len(late.select("#bg-timeline [data-state=unconfirmed]")), 1)

    def test_classroom_is_read_from_shared_config(self):
        cr = json.loads((ROOT / "configs/classroom/bukatsu-chiiki.json").read_text(encoding="utf-8"))
        text = self.soup.select_one("#bg-classroom").get_text()
        for r in cr["reasons_pro"] + cr["reasons_con"]:
            self.assertIn(r["text"], text)

    def test_background_memo_sections_after_guideline(self):
        for g in self.d["bg"]["cfg"]["groups"]:
            for row in g["rows"]:
                if row["kind"] == "timeline":
                    continue
                for item in self.bg.memo_items(row):
                    self.assertGreaterEqual(self.d["memo"].checked_on(item["memo_section"]), "2025-12-22")

    def test_does_not_read_frozen_editorial_source(self):
        for name in ("bukatsu_reading.py", "bukatsu_background.py", "bukatsu_opening.py"):
            src = (ROOT / "scripts" / name).read_text(encoding="utf-8")
            self.assertNotIn("editorial-source.html", src.split('"""', 2)[-1])
            self.assertNotIn("editorial-review.json", src.split('"""', 2)[-1])


if __name__ == "__main__":
    unittest.main()
