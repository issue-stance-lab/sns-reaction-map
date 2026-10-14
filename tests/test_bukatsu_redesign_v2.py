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
        # 選び直す前のページ（初期型の公開ページ）と同じ投稿を使っていない。最新の型に切り替えた後の公開ページは、
        # 選び直した投稿そのものを載せているので比べられない（切替前の 2026-10-14 に初期型のページに対して確かめた）
        published = (ROOT / "docs/bukatsu-chiiki-reaction-map.html").read_text(encoding="utf-8")
        if 'content="redesign-v2"' in published:
            self.skipTest("公開ページが最新の型に切り替わった後は、初期型のページと比べられない（切替前に確認済み）")
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




# ---------------------------------------------------------------- 手順7：公開候補（scripts/build_bukatsu_redesign_v2.py）と更新経路

import re  # noqa: E402
import shutil  # noqa: E402
from collections import Counter  # noqa: E402

from scripts import build_bukatsu_redesign_v2 as redesign  # noqa: E402
from scripts import bukatsu_layout as layout  # noqa: E402

AS_OF = PUBLIC["updated_on"]
INPUTS = (
    "THEMES.yaml", "docs/data/themes/bukatsu-chiiki.json", "data/public/themes/bukatsu-chiiki.json",
    "data/bukatsu-chiiki_teacher-reread.json", "data/bukatsu-chiiki_cost-receiver-reread.json",
    "data/verification/bukatsu-chiiki-plan-child-subissues.json", "data/bukatsu-chiiki_reread-stances.json",
    "data/bukatsu-chiiki_claim_posts.json", "quality/research/bukatsu-chiiki-primary-sources.md",
    "quality/research/bukatsu-chiiki-municipal-plans.md", "data/page-sources/bukatsu-chiiki.html",
)
ISSUES = [i for i in PUBLIC["issues"]]
UNPUBLISHED = {"bukatsu-chiiki-kakusa", "bukatsu-chiiki-sonota"}
# 元HTML・初期型の内部用id（JS・CSS の書き込み先や、表の行）。外から指される場所ではない
LEGACY_IDS_INTERNAL = ("bkt-", "pseg", "pbar", "pnum", "c-", "s-", "ro-", "vote-", "share-x", "explainer-modal", "dot-", "divenote",
                       "chartdesc", "floor-note", "bukatsu-chiiki-trend-panel-", "public-data", "bukatsu-planet-style",
                       "related-theme-tracking", "q")


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def protected(text: str, name: str) -> str:
    return re.search(r"<!-- " + name + r"_START -->.*?<!-- " + name + r"_END -->", text, re.S).group()


def vote_defs(text: str) -> tuple:
    return tuple(re.search(pattern, text, re.S).group(1) for pattern in
                 (r"var TOPIC='([^']+)'", r"var VOTE_ISSUES=(\[.*?\]);", r"var V2I=(\[.*?\]);", r"var STANCES=(\[.*?\]);"))


def make_root(temp: str, version: str = "redesign-v2") -> Path:
    """公開候補の隔離コピーと同じ入力だけを持つ root（設定・公開JSON・再読データ・立場の対応表・一次資料メモ・自治体カタログ・元HTML）。"""
    root = Path(temp)
    shutil.copytree(ROOT / "configs", root / "configs")
    shutil.copytree(ROOT / "scripts/bukatsu_redesign", root / "scripts/bukatsu_redesign",
                    ignore=shutil.ignore_patterns("__pycache__"))
    for name in INPUTS:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, root / name)
    (root / layout.PAGE).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(layout.source_for_refresh(ROOT), root / layout.PAGE)
    (root / layout.CONFIG).write_text(json.dumps({"enabled": True, "version": version}), encoding="utf-8")
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
        cls.full = (out / "release" / redesign.READ_PAGE).read_text(encoding="utf-8")
        cls.s = soup_of(cls.release)
        cls.src = soup_of(cls.source)
        cls.out = out

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_same_input_same_output(self):
        redesign.build(self.source_path, self.out / "again", "release", as_of=AS_OF)
        self.assertEqual(self.release, (self.out / "again" / redesign.PAGE).read_text(encoding="utf-8"))
        self.assertEqual(self.full, (self.out / "again" / redesign.READ_PAGE).read_text(encoding="utf-8"))

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

    def test_protected_parts_are_inherited_verbatim(self):
        for name in ("SEO_META", "ARTICLE_JSON_LD", "ARTICLE_TRUST"):
            self.assertEqual(self.release.count(protected(self.source, name)), 1, name)
        self.assertEqual(self.s.head.title.get_text(), self.src.head.title.get_text())
        self.assertEqual(self.s.select_one('meta[name="description"]')["content"],
                         self.src.select_one('meta[name="description"]')["content"])
        seo = json.loads((ROOT / "configs/theme-seo.json").read_text(encoding="utf-8"))
        entry = next(t for t in seo["themes"] if t["id"] == "bukatsu-chiiki")
        self.assertEqual(self.s.select_one("h1").get_text(), entry["display_headline"])
        self.assertEqual(self.s.select('link[rel="canonical"]')[0]["href"],
                         "https://sns-reaction-map.jp/bukatsu-chiiki-reaction-map.html")
        self.assertEqual(len(self.s.select("h1")), 1)
        ids = Counter(t["id"] for t in self.s.find_all(id=True))
        self.assertEqual([k for k, v in ids.items() if v > 1], [])
        for sel in ('link[href^="site-tokens.css"]', 'link[href^="topic-modern.css"]', 'script[src^="topic-modern.js"]'):
            self.assertEqual(str(self.s.select_one(sel)), str(self.src.select_one(sel)), sel)
        for sel in ("#related-topics", "body > footer", "#related-theme-tracking"):
            self.assertEqual(self.s.select_one(sel).get_text(), self.src.select_one(sel).get_text(), sel)
        self.assertEqual(self.s.select_one("#planet-data").string, self.src.select_one("#planet-data").string)
        self.assertIsNotNone(self.s.select_one('header.modern-site-header a[href="index.html"]'))

    def test_ga_and_adsense_only_in_release(self):
        for name in ("GA_TAG", "ADSENSE_TAG"):
            block = protected(self.source, name)
            self.assertIn(block, self.release)
            self.assertNotIn(block, self.preview)
        self.assertIn('name="robots" content="noindex"', self.preview)
        self.assertNotIn('name="robots"', self.release)
        self.assertIn("ca-pub-2542211932832864", self.release)

    def test_vote_contract_is_unchanged(self):
        """投票は topic・論点7つ・V2I・立場3つを元HTMLと完全一致。保存キーは本番ホストだけ既存キー。保存の注記は送信される旨の元の文。"""
        src = vote_defs(self.source)
        self.assertEqual(src[0], "bukatsu-chiiki-issue-stance-v1")
        for text in (self.release, self.preview):
            self.assertEqual(vote_defs(text), src)
            self.assertIn(redesign.VOTE_CHOICE, text)
            self.assertIn("var STORAGE_KEY=window.SNS_REDESIGN_PRODUCTION?'sns_vote_'+TOPIC+'_my':'sns_vote_'+TOPIC+'_my_preview';", text)
            self.assertIn("window.voteMsg = function", text)
        self.assertEqual(len(re.findall(r"\bk:'", src[1])), 7)
        self.assertEqual(len(re.findall(r"\bk:'", src[3])), 3)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=location.hostname==='sns-reaction-map.jp'", self.release)
        scripts = self.s.select("script")
        config = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-config.js"))
        client = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-store.js"))
        self.assertEqual(config + 2, client)
        self.assertEqual(self.s.select_one("#vote-section").get("data-vote-topic"), src[0])
        self.assertEqual(self.s.select_one("#vote-section .vote-storage-note").get_text(),
                         self.src.select_one("#vote-section .vote-storage-note").get_text())

    def test_faq_json_ld_matches_visible_faq(self):
        payloads = [json.loads(x.get_text()) for x in self.s.select('script[type="application/ld+json"]')]
        faq = [p for p in payloads if p.get("@type") == "FAQPage"]
        self.assertEqual(len(faq), 1)
        visible = redesign.faq_items(self.s)
        bg = json.loads((ROOT / "configs/bukatsu-chiiki-background.json").read_text(encoding="utf-8"))
        rows = [r for g in bg["groups"] for r in g["rows"] if r["kind"] == "faq"]
        self.assertEqual(len(visible), len(rows[0]["items"]))
        self.assertEqual([(q["name"], q["acceptedAnswer"]["text"]) for q in faq[0]["mainEntity"]], visible)
        self.assertEqual(sum(1 for p in payloads if p.get("@type") == "Article"), 1)
        # 元HTMLの検索入口の FAQ（build_bukatsu_arena.py の SEARCH_FAQ_JSONLD）は引き継がない
        self.assertNotIn("BUKATSU_SEARCH_FAQ_JSONLD", self.release)

    def test_no_trial_wording(self):
        """公開ページにも全文・印刷版にも「試作」の語を出さない（初期型の投票注記・JSなし案内の誤り）。"""
        for html in (self.release, self.full):
            soup = soup_of(html)
            for node in soup.select("script, style"):
                node.decompose()
            self.assertNotIn("試作", soup.get_text())
        self.assertNotIn("本番の投票集計には送信しません", self.release)

    def test_trend_card_is_inherited_verbatim_inside_fold(self):
        block = re.search(r'<section class="update-dashboard"><!-- TREND_CARD_START -->.*?<!-- TREND_CARD_END --></section>',
                          self.source, re.S).group()
        self.assertEqual(self.release.count(block), 1)
        fold = self.s.select_one("#cap-trend-more")
        self.assertEqual(fold.name, "details")
        self.assertFalse(fold.has_attr("open"))
        for panel in redesign.TREND_PANELS:
            self.assertIsNotNone(fold.find(id=panel), panel)
        panels = redesign._trend_rounds(block)
        glance = self.s.select_one("#cap-trend .cap-trend-glance")
        self.assertEqual(len(glance.select(".cap-trend-spark svg polyline")), len(panels["stance"]["labels"]))
        rounds = panels["stance"]["rounds"]
        note = glance.select_one(".cap-trend-note").get_text()
        self.assertIn(f'{min(r["n"] for r in rounds)}〜{max(r["n"] for r in rounds)}件', note)
        # 論点だけの分類AIの切替（10/1）は、立場の要約には出さない（立場は全回を同じAIで判定し直している）
        self.assertNotIn("分類のAI", note)
        self.assertLess(self.release.index("TREND_CARD_START -->"), self.release.index('id="vote-section"'))

    def test_issue_glance_charts_come_from_the_same_trend(self):
        panels = redesign._trend_rounds(self.release)
        from scripts.bukatsu_redesign.glance_chart import annotated_graph
        for issue in ISSUES:
            box = self.s.find(id="issue-" + issue["id"]).select_one(".fr-glance")
            if issue["label"] not in panels["issue"]["labels"]:
                self.assertIsNone(box.select_one("svg"), issue["id"])
                continue
            j = panels["issue"]["labels"].index(issue["label"])
            self.assertEqual(str(box.select_one("svg.glance-chart-desktop")),
                             str(soup_of(annotated_graph(issue["label"], panels["issue"]["rounds"], j)).svg))

    def test_method_fold_and_folds_start_closed(self):
        method = self.s.select_one("#cap-method")
        self.assertEqual(method.name, "details")
        self.assertIsNotNone(method.select_one("#detail-data"))
        self.assertEqual(method.select("details[open]"), [])
        for sel in ("#bukatsu-chiiki-reading", "#bukatsu-chiiki-background", "#bukatsu-open", "#cap-trend", "#cap-method"):
            opened = [d.get("class") for d in self.s.select(sel + " details[open]") if not d.find_parent(id="cap-trend-more")]
            self.assertEqual(opened, [], sel)
        self.assertEqual(len(self.s.select("#bukatsu-chiiki-background details.fb-row")), 7)

    def test_default_issue_and_unpublished_reasons(self):
        top = max(ISSUES, key=lambda i: int(i["count"]))
        self.assertEqual(self.s.select_one("#bukatsu-chiiki-reading")["data-default-issue"], top["id"])
        for issue in ISSUES:
            panel = self.s.find(id="issue-" + issue["id"])
            self.assertEqual(panel.select_one("[data-unpublished]") is not None, issue["id"] in UNPUBLISHED, issue["id"])

    def test_classroom_section_contract(self):
        section = self.release[self.release.index("<!-- CLASSROOM_START -->"):self.release.index("<!-- CLASSROOM_END -->")]
        for token in ('class="classroom-print-btn"', "classroom-sources", "classroom-questions", 'href="bukatsu-chiiki-classroom.html"'):
            self.assertIn(token, section)
        self.assertEqual(self.release.count("<!-- CLASSROOM_START -->"), 1)

    def test_old_anchor_targets_exist(self):
        for target in set(redesign.ALIASES.values()):
            self.assertIsNotNone(self.s.find(id=target), target)
        hidden = ("progress", "fallback", "fallback-nav", "quiz", "guesses")
        for alias in redesign.ALIASES:
            if alias not in hidden:
                self.assertIsNone(self.s.find(id=alias), alias)
        published = soup_of((ROOT / "docs/bukatsu-chiiki-reaction-map.html").read_text(encoding="utf-8"))
        for page in (self.src, published):  # 元HTML（旧形式）と、公開中のページ（初期型か最新の型）
            for node in page.find_all(id=True):
                old = node["id"]
                if self.s.find(id=old) is not None or old in redesign.ALIASES or old.startswith(LEGACY_IDS_INTERNAL):
                    continue
                if any(old.startswith(p) for p in redesign.ISSUE_PREFIXES):
                    continue
                two = re.match(r"^(bukatsu-chiiki-[a-z]+)--(.+)$", old)
                if two:  # 初期型の理由の欄 → 新しい理由の説明（無ければ論点の欄）
                    self.assertIsNotNone(self.s.find(id="issue-" + two.group(1)), old)
                    continue
                self.assertIsNotNone(self.s.find(id="issue-" + old), old)  # 論点の素のID → 論点の欄
        targets = set()
        for base in ("docs", "scripts", "configs", "company"):
            for path in (ROOT / base).rglob("*"):
                if path.suffix not in (".html", ".py", ".json", ".js", ".md", ".txt", ".xml", ".yaml") or path.name == redesign.PAGE:
                    continue
                targets |= set(re.findall(r"bukatsu-chiiki-reaction-map\.html#([A-Za-z0-9_-]+)",
                                          path.read_text(encoding="utf-8", errors="ignore")))
        for t in targets:
            self.assertTrue(self.s.find(id=t) is not None or t in redesign.ALIASES or self.s.find(id="issue-" + t) is not None
                            or any(t.startswith(p) for p in redesign.ISSUE_PREFIXES), t)

    def test_planet_is_copied_from_source(self):
        src_section = re.search(r"<!-- PLANET_SECTION_START -->(.*?)<!-- PLANET_SECTION_END -->", self.source, re.S).group(1)
        src = soup_of(src_section)
        script = [x for x in src.find_all("script", recursive=False) if x.get("id") != "planet-data"][0].string
        for old, new in redesign.PLANET_PATCHES:
            self.assertEqual(script.count(old), 1)
            script = script.replace(old, new)
        self.assertEqual(self.release.count(script), 1)
        self.assertEqual(self.release.count("window.PLANET_DATA="), 1)
        planet = self.s.select_one("#bukatsu-chiiki-reading .fr-map section.planet-panel #planet-block")
        self.assertIsNotNone(planet)
        self.assertLess(self.release.index('id="planet-block"'), self.release.index('class="fr-tabs"'))
        for sel in ("#modes", ".stage", "#list"):
            self.assertEqual(str(planet.select_one(sel)), str(src.select_one("#planet-block " + sel)), sel)
        self.assertEqual(sorted(a["href"] for a in planet.select("#fallback-nav a")),
                         sorted("#issue-" + i["id"] for i in ISSUES))
        self.assertEqual(planet.select("section.landing-panel, #ocean, #editorial, span.issue-anchor"), [])
        self.assertIsNotNone(planet.select_one("#research-conditions > #caution"))
        self.assertNotIn("location.hash=issues[i].id;", self.release)
        self.assertIn("window.BukatsuReading", self.release)
        self.assertLess(self.release.index("window.BukatsuReading = Object.freeze"), self.release.index("function goReading"))

    def test_source_changes_stop_or_follow(self):
        changed = self.source.replace("このページの見かた", "このページの見かた（更新確認）", 1)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.html"
            path.write_text(changed, encoding="utf-8")
            redesign.build(path, Path(temp) / "out", "release", as_of=AS_OF)
            self.assertIn("このページの見かた（更新確認）", (Path(temp) / "out" / redesign.PAGE).read_text(encoding="utf-8"))
        for old, new, message in (
                ("  location.hash=issues[i].id;\n", "  location.hash = issues[i].id;\n", "書き換える箇所"),
                (redesign.VOTE_STORAGE, "var STORAGE_KEY='sns_vote_'+TOPIC+'_v2';", "保存キー"),
                ('id="bukatsu-chiiki-trend-panel-issue"', 'id="bukatsu-chiiki-trend-panel-issues"', "trend-panel-issue")):
            moved = self.source.replace(old, new, 1)
            self.assertNotEqual(moved, self.source)
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "source.html"
                path.write_text(moved, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    redesign.build(path, Path(temp) / "out", "release", as_of=AS_OF)

    def test_does_not_use_frozen_initial_parts(self):
        code = (ROOT / "scripts/build_bukatsu_redesign_v2.py").read_text(encoding="utf-8")
        for name in ("editorial-review.json", "editorial-source.html", "template.html", "parity.py", "refresh_inputs.py", "app.js"):
            self.assertNotIn(f'"{name}"', code)
            self.assertNotIn(f"'{name}'", code)
        self.assertNotIn("site-chrome", self.release)
        self.assertNotIn("bukatsu-connected.js", self.release)
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.release)

    def test_full_reading_page_is_made_from_the_same_page(self):
        full = soup_of(self.full)
        self.assertEqual(full.select("script"), [])
        self.assertIn("noindex", full.select_one('meta[name="robots"]')["content"])
        self.assertEqual(len(full.select(".fr-panel")), len(ISSUES))
        self.assertEqual(len(full.select(".fr-reason-detail")), len(self.s.select(".fr-reason-detail")))
        self.assertIsNone(full.select_one("#planet-block"))
        self.assertIsNotNone(full.select_one("#research-conditions"))
        self.assertIsNone(full.select_one("#vote-section"))
        self.assertEqual(full.select("details"), [])
        for a in full.select('a[href^="#"]'):
            self.assertIsNotNone(full.find(id=a["href"][1:]), a["href"])
        self.assertIn('href="bukatsu-chiiki-full.html"', self.release)

    def test_phase_switch_by_as_of(self):
        """基準日を後期（2029-04-01、中間評価は未確認）にすると冒頭・背景の段階の文が切り替わり、生成は止まらない（docs には入れない）。"""
        with tempfile.TemporaryDirectory() as temp:
            redesign.build(self.source_path, Path(temp), "release", as_of="2029-04-01")
            later = soup_of((Path(temp) / redesign.PAGE).read_text(encoding="utf-8"))
        self.assertEqual(self.s.select_one("section.bko")["data-phase"], "zenki")
        self.assertEqual(later.select_one("section.bko")["data-phase"], "kouki_unchecked")
        self.assertEqual(later.select_one("#bukatsu-chiiki-background")["data-phase"], "kouki_unchecked")
        self.assertNotEqual(later.select_one(".bko-status").get_text(), self.s.select_one(".bko-status").get_text())

    def test_provenance_counts_and_detects_mismatch(self):
        from scripts.bukatsu_count_provenance import verified_selectors
        result = verified_selectors(self.release, ROOT)
        self.assertEqual(len(result), len(ISSUES) + 2)  # 論点の欄7つ＋冒頭の件数欄＋推移の要約の注記
        first = "bukatsu-chiiki-kyoin"
        node = self.s.select_one(f"#issue-{first} li.fr-reason .fr-reason-n b")
        broken = self.release.replace(str(node), str(node).replace(node.get_text(), str(int(node.get_text()) + 1)), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)
        count = self.s.select_one(f"#issue-{first} .fr-count b")
        broken = self.release.replace(str(count), str(count).replace(count.get_text(), "37"), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)

    def test_theme_page_check_reads_new_reason_rows(self):
        from scripts.verify_theme_page import _planet_data, verify_planet_breakdowns
        data = _planet_data(self.release)
        self.assertEqual(verify_planet_breakdowns("bukatsu-chiiki", self.release, data)[1], 0)
        node = self.s.select_one("#issue-bukatsu-chiiki-seido [data-excluded]")
        broken = self.release.replace(f'data-excluded="{node["data-excluded"]}"', 'data-excluded="1"', 1)
        self.assertGreater(verify_planet_breakdowns("bukatsu-chiiki", broken, data)[1], 0)


class LayoutV2Tests(unittest.TestCase):
    """手順7：更新経路（materialize → 旧形式の全処理 → finish）を最新の型（version: redesign-v2）で通す。"""

    def test_version_selects_builder(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "configs").mkdir()
            (root / layout.CONFIG).write_text('{"enabled": true}')
            self.assertEqual(layout.version(root), "redesign-v1")
            (root / layout.CONFIG).write_text('{"enabled": true, "version": "redesign-v2"}')
            self.assertEqual(layout.version(root), "redesign-v2")

    def test_pipeline_finish_keeps_source_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = make_root(temp)
            legacy = (root / layout.PAGE).read_text(encoding="utf-8")
            targets = layout.finish(root, as_of=AS_OF)
            self.assertEqual(set(targets), {layout.SOURCE, layout.PAGE, Path("docs") / redesign.READ_PAGE})
            first = (root / layout.PAGE).read_bytes()
            self.assertIn(b'<meta name="bukatsu-layout" content="redesign-v2">', first)
            self.assertEqual(legacy, (root / layout.SOURCE).read_text(encoding="utf-8"))
            self.assertEqual(layout.source_for_refresh(root), root / layout.SOURCE)
            layout.materialize(root)
            self.assertEqual(legacy, (root / layout.PAGE).read_text(encoding="utf-8"))
            layout.finish(root, as_of=AS_OF)
            self.assertEqual(first, (root / layout.PAGE).read_bytes())
            with self.assertRaisesRegex(ValueError, "再入力"):
                layout.finish(root, as_of=AS_OF)

    def test_data_change_does_not_need_a_fingerprint(self):
        """初期型は元HTMLの集計が1件変わると editorial-review.json の指紋で止まった。最新の型は指紋を持たず、照合が合えば作れる。"""
        with tempfile.TemporaryDirectory() as temp:
            root = make_root(temp)
            page = root / layout.PAGE
            page.write_text(page.read_text(encoding="utf-8").replace("このページの見かた", "このページの見かた（10/17）", 1),
                            encoding="utf-8")
            layout.finish(root, as_of=AS_OF)
            self.assertIn("このページの見かた（10/17）", (root / layout.PAGE).read_text(encoding="utf-8"))
            self.assertFalse((root / "scripts/bukatsu_redesign/editorial-review.json").read_text(encoding="utf-8") in
                             (root / layout.PAGE).read_text(encoding="utf-8"))

    def test_count_mismatch_stops_before_writing(self):
        """新しい意見を追い読みしないまま、再読データの明細と立場の対応表が食い違った回と同じ形では止まる。"""
        with tempfile.TemporaryDirectory() as temp:
            root = make_root(temp)
            path = root / "data/bukatsu-chiiki_teacher-reread.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            text = json.dumps(raw, ensure_ascii=False)
            node = raw
            import yaml
            planet = yaml.safe_load((ROOT / "configs/planet/bukatsu-chiiki.yaml").read_text(encoding="utf-8"))
            for key in planet["sub_issues"]["教員の働き方"]["path"][:-1]:
                node = node[key]
            gone = node["items"].pop(0)
            node["buckets"][gone["bucket"]]["count"] -= 1
            self.assertNotEqual(text, json.dumps(raw, ensure_ascii=False))
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            before = (root / layout.PAGE).read_bytes()
            saved = (root / layout.SOURCE).read_bytes()
            with self.assertRaisesRegex(ValueError, "照合で停止"):
                layout.finish(root, as_of=AS_OF)
            self.assertEqual(before, (root / layout.PAGE).read_bytes())
            self.assertEqual(saved, (root / layout.SOURCE).read_bytes())

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では、更新経路の立場の対応表を作れない")
    def test_adapter_rebuilds_stance_table_and_stops_without_reread(self):
        from scripts.refresh_adapters.bukatsu import build_reread_stances
        table = json.loads((ROOT / "data/bukatsu-chiiki_reread-stances.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("THEMES.yaml", "configs/planet/bukatsu-chiiki.yaml", "data/bukatsu-chiiki_teacher-reread.json",
                         "data/bukatsu-chiiki_cost-receiver-reread.json", "data/verification/bukatsu-chiiki-plan-child-subissues.json"):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, root / name)
            candidate = root / "cumulative-candidate.json"
            shutil.copy2(CANON, candidate)
            data = build_reread_stances(root, candidate, root / "stances.json", "2026-10-17")
            self.assertEqual(data["stances"], table["stances"])
            self.assertEqual((data["made_on"], data["public_mismatch"]), ("2026-10-17", 0))
            path = root / "data/bukatsu-chiiki_teacher-reread.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            text = json.dumps(raw, ensure_ascii=False)
            import yaml
            planet = yaml.safe_load((ROOT / "configs/planet/bukatsu-chiiki.yaml").read_text(encoding="utf-8"))
            node = raw
            for key in planet["sub_issues"]["教員の働き方"]["path"][:-1]:
                node = node[key]
            node["items"].pop(0)
            self.assertNotEqual(text, json.dumps(raw, ensure_ascii=False))
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "追い読み"):
                build_reread_stances(root, candidate, root / "stances.json", "2026-10-17")

    def test_refresh_path_is_wired(self):
        refresh = (ROOT / "scripts/refresh_topic.py").read_text(encoding="utf-8")
        self.assertEqual(refresh.count("from scripts.bukatsu_layout import finish"), 2)
        self.assertIn("from scripts.bukatsu_layout import materialize", refresh)
        adapter = (ROOT / "scripts/refresh_adapters/bukatsu.py").read_text(encoding="utf-8")
        self.assertIn("source_for_refresh(root)", adapter)
        self.assertIn("REREAD_STANCES: first_stances", adapter)
        self.assertIn("check_model_break(", adapter)
        self.assertIn("verified_selectors_v2", (ROOT / "scripts/bukatsu_count_provenance.py").read_text(encoding="utf-8"))
        for path in ("scripts/seo/apply_classroom_section.py", "scripts/seo/apply_theme_trust.py", "scripts/verify_theme_page.py",
                     "scripts/seo/validate_theme_seo.py"):
            self.assertIn("redesign-v2", (ROOT / path).read_text(encoding="utf-8"), path)
        self.assertIn('"bukatsu-chiiki" and \'name="bukatsu-layout"\'', (ROOT / "scripts/refresh_planet_section.py").read_text(encoding="utf-8"))

    def test_repository_layout_state_is_consistent(self):
        page = (ROOT / layout.PAGE).read_text(encoding="utf-8")
        self.assertTrue(layout.enabled(ROOT))
        self.assertTrue((ROOT / layout.SOURCE).is_file())
        published_v2 = '<meta name="bukatsu-layout" content="redesign-v2">' in page
        self.assertEqual(published_v2, layout.version(ROOT) == "redesign-v2")


if __name__ == "__main__":
    unittest.main()
