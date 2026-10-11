"""副首都・新デザインの試作（冒頭の時制、山なみと論点の読書面）。docs/ は書き換えない。

皇室典範改正（tests/test_koshitsu_redesign.py）の手順5・6に当たる検査。
"""
from __future__ import annotations

import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from scripts import fukushuto_reading as reading

ROOT = reading.ROOT
opening = reading.opening
PUBLIC = json.loads((ROOT / "docs/data/themes/fukushuto.json").read_text(encoding="utf-8"))
CANON = ROOT / "social-samples/fukushuto_hermes_classified.json"


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class ReadingPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        cls.page_path = reading.build(cls.out / "a")
        cls.html = cls.page_path.read_text(encoding="utf-8")
        cls.s = soup_of(cls.html)
        cls.d = reading.load()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_same_input_same_output(self):
        again = reading.build(self.out / "b").read_text(encoding="utf-8")
        self.assertEqual(self.html, again)

    def test_default_as_of_is_public_updated_on(self):
        self.assertEqual(reading.default_as_of(self.d), PUBLIC["updated_on"])
        self.assertIn(f'data-as-of="{PUBLIC["updated_on"]}"', self.html)

    def test_does_not_write_docs(self):
        self.assertNotIn("docs", str(self.page_path.relative_to(self.out)))
        self.assertNotIn("../../../docs/", self.html)

    def test_issue_order_count_desc_other_last(self):
        chips = [a["data-issue-id"] for a in self.s.select(".fr-chip")]
        other = [i for i in PUBLIC["issues"] if i["kind"] == "other"][0]["id"]
        named = sorted((i for i in PUBLIC["issues"] if i["id"] != other), key=lambda i: -int(i["count"]))
        self.assertEqual(chips, [i["id"] for i in named] + [other])
        self.assertEqual(len(self.s.select(".fr-mountains .fr-hill")), len(PUBLIC["issues"]))

    def test_counts_and_stances_match_public_json(self):
        for issue in PUBLIC["issues"]:
            panel = self.s.find(id="issue-" + issue["id"])
            self.assertIsNotNone(panel, issue["id"])
            self.assertEqual(panel.select_one(".fr-count b").get_text(), f'{int(issue["count"]):,}')
            shown = [b.get_text() for b in panel.select(".fr-stance-list b")]
            order = [s["id"] for s in self.d["planet"]["stances"]]
            by = {s["id"]: int(s["count"]) for s in issue["stances"]}
            self.assertEqual(shown, [f"{by[sid]:,}" for sid in order])

    def test_reasons_recounted_from_reread_details(self):
        for label, rr in self.d["reread"].items():
            issue = next(i for i in PUBLIC["issues"] if i["label"] == label)
            panel = self.s.find(id="issue-" + issue["id"])
            for bid, b in rr["buckets"].items():
                node = panel.select_one(f'li.fr-reason[data-reason="{bid}"] .fr-reason-n b')
                n = sum(1 for it in rr["items"] if it["bucket"] == bid)
                self.assertEqual(node.get_text(), f"{n:,}", (label, bid))

    def test_issues_without_reasons_say_unpublished(self):
        no_reason = [i for i in PUBLIC["issues"] if i["label"] not in self.d["reread"]]
        self.assertTrue(no_reason)  # 現在は都構想・維新と定義・中身
        for issue in no_reason:
            panel = self.s.find(id="issue-" + issue["id"])
            self.assertIsNotNone(panel.select_one("[data-unpublished]"), issue["id"])
        for label in self.d["reread"]:
            issue = next(i for i in PUBLIC["issues"] if i["label"] == label)
            self.assertIsNone(self.s.find(id="issue-" + issue["id"]).select_one("[data-unpublished]"))

    def test_unpublished_note_disappears_when_reread_is_added(self):
        d = copy.deepcopy(self.d)
        issue = next(i for i in PUBLIC["issues"] if i["label"] not in d["reread"])
        items = [{"tweet_id": str(k), "bucket": "A", "stance": d["planet"]["stances"][0]["key"]} for k in range(int(issue["count"]))]
        d["reread"][issue["label"]] = {"buckets": {"A": {"label": "仮の区分", "count": int(issue["count"])}}, "items": items}
        html = reading.render_reasons(d, issue, {})
        self.assertNotIn("data-unpublished", html)
        self.assertIn('data-reason="A"', html)

    def test_location_panel_is_complete(self):
        panel = self.s.find(id="issue-fukushuto-location")
        self.assertIn("is-complete", panel["class"])
        self.assertTrue(panel.select(".fr-desc"))
        self.assertTrue(panel.select(".fr-voice"))
        self.assertTrue(panel.select('.fr-check[data-check="selection"]'))
        self.assertTrue(panel.select('.fr-memo-check[data-memo-check="requirements-draft"]'))
        regions = len(self.d["ocfg"]["candidates"])
        self.assertIn(f"{regions}地域", panel.select_one(".fr-see").get_text())
        self.assertEqual(panel.select_one('.fr-see a')["href"], "#fuk-op-map")
        self.assertIsNotNone(self.s.find(id="fuk-op-map"))

    def test_posts_at_most_two_with_lazy_embed_and_original_links(self):
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.html)
        for panel in self.s.select(".fr-panel"):
            embeds = panel.select(".x-embed")
            self.assertLessEqual(len(embeds), 2)
            for e in embeds:
                self.assertRegex(e.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")
            self.assertEqual(len(panel.select(".fr-post")), len(embeds))

    def test_selected_posts_are_in_reread_and_not_reused(self):
        ids = []
        for iid, icfg in self.d["cfg"]["issues"].items():
            issue = next(i for i in PUBLIC["issues"] if i["id"] == iid)
            rr = self.d["reread"].get(issue["label"])
            for p in icfg.get("posts", {}).get("items", []):
                ids.append(p["id"])
                if rr:
                    self.assertIsNotNone(reading.post_record(rr, p["id"]), (iid, p["id"]))
        self.assertEqual(len(ids), len(set(ids)))

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では確かめない")
    def test_selected_posts_meet_canonical_criteria(self):
        canon = json.loads(CANON.read_text(encoding="utf-8"))
        norm = lambda t: re.sub(r"\s+", "", t.replace("\tSTART\t", "").replace("\tEND\t", ""))
        texts = [norm(x["text"]) for x in canon]
        by_id = {x["tweet_id"]: x for x in canon}
        labels = {i["id"]: i["label"] for i in PUBLIC["issues"]}
        stance_ids = {s["key"]: s["id"] for s in self.d["planet"]["stances"]}
        for iid, icfg in self.d["cfg"]["issues"].items():
            for p in icfg.get("posts", {}).get("items", []):
                x = by_id[p["id"]]
                c = x["classification"]
                self.assertTrue(c["is_opinion"], p["id"])
                self.assertEqual(c["main_issue"], labels[iid], p["id"])
                self.assertTrue(c["article_usable"], p["id"])
                self.assertEqual(c["risk"], "low", p["id"])
                self.assertEqual(x["url"], p["url"], p["id"])
                self.assertEqual(texts.count(norm(x["text"])), 1, p["id"])
                if p.get("stance_id"):
                    self.assertEqual(stance_ids[c["stance"]], p["stance_id"], p["id"])

    def test_count_mismatch_stops(self):
        d = copy.deepcopy(self.d)
        label = next(iter(d["reread"]))
        d["reread"][label]["items"].pop()
        with self.assertRaises(SystemExit):
            reading.check_all(d)
        d = copy.deepcopy(self.d)
        d["public"]["issues"][0]["count"] += 1
        with self.assertRaises(SystemExit):
            reading.check_all(d)
        d = copy.deepcopy(self.d)
        d["public"]["trends"] = []
        with self.assertRaises(SystemExit):
            reading.check_all(d)

    def test_three_posts_or_bad_url_stop(self):
        d = copy.deepcopy(self.d)
        posts = d["cfg"]["issues"]["fukushuto-location"]["posts"]["items"]
        posts[0]["url"] = posts[0]["url"].replace(posts[0]["id"], "1")
        with self.assertRaises(SystemExit):
            reading.check_all(d)


class OpeningPhaseTests(unittest.TestCase):
    """意見募集（募集中／締め切り済み・結果未確認／結果公表）と施行（施行前／施行日を過ぎた・未確認／施行後・確認済み）。"""

    @classmethod
    def setUpClass(cls):
        cls.data = opening.load_inputs(ROOT / "configs/fukushuto-opening.json")

    def frag(self, as_of, **law_or_comment):
        data = copy.deepcopy(self.data)
        for key, value in law_or_comment.items():
            group, field = key.split("__")
            data["config"][group][field] = value
        return opening.render_fragment(data, as_of)

    def test_phases_by_as_of(self):
        law, comment = self.data["config"]["law"], self.data["config"]["comment"]
        self.assertEqual(opening.phase_of(self.data["config"], comment["closes_on"]), ("before", "open"))
        self.assertEqual(opening.phase_of(self.data["config"], "2026-10-17"), ("before", "closed"))
        self.assertEqual(opening.phase_of(self.data["config"], law["enforcement_on"]), ("after_unconfirmed", "closed"))

    def test_texts_switch(self):
        before = self.frag("2026-10-10")
        self.assertIn("10月16日まで意見募集", before)
        self.assertIn("施行予定日として示されている", before)
        closed = self.frag("2026-10-17")
        self.assertIn("結果は編集部でまだ確かめていない", closed)
        after = self.frag("2026-10-31")
        self.assertIn("施行予定でした。施行後の条文は編集部で確かめていません", after)
        self.assertIn("fop-stop--unconfirmed", after)
        confirmed = self.frag("2026-11-02", law__enforcement_confirmed_on="2026-11-01", comment__result_published_on="2026-10-30")
        self.assertIn("施行されました（2026年11月1日に条文を確認）", confirmed)
        self.assertIn("意見募集の結果が公表された", confirmed)
        self.assertNotIn("施行予定", confirmed.split('id="fuk-op-route"')[1].split("</section>")[0])

    def test_impossible_dates_stop(self):
        with self.assertRaises(SystemExit):
            self.frag("2026-10-31", law__enforcement_confirmed_on="2026-10-29")
        with self.assertRaises(SystemExit):
            self.frag("2026-10-20", law__enforcement_confirmed_on="2026-10-31")
        with self.assertRaises(SystemExit):
            self.frag("2026-10-20", comment__result_published_on="2026-10-15")

    def test_default_uses_public_updated_on(self):
        self.assertIn(f'data-as-of="{self.data["public"]["updated_on"]}"', opening.render_fragment(self.data))


class BackgroundTests(unittest.TestCase):
    """手順6：残り6論点と背景の開閉行。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.d = reading.load()
        cls.html = reading.build(Path(cls.tmp.name) / "a").read_text(encoding="utf-8")
        cls.s = soup_of(cls.html)
        cls.bg = cls.s.select_one("#fukushuto-background")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def render_bg(self, as_of, edit=None):
        d = copy.deepcopy(self.d)
        if edit:
            edit(d)
        import fukushuto_background as bgmod
        return soup_of(bgmod.render(d, as_of, reading.ordered_issues(d))).select_one("#fukushuto-background")

    def test_all_issues_complete_with_posts(self):
        for iid, icfg in self.d["cfg"]["issues"].items():
            panel = self.s.find(id="issue-" + iid)
            self.assertIn("is-complete", panel["class"], iid)
            self.assertTrue(panel.select(".fr-desc"), iid)
            self.assertIn(len(panel.select(".fr-post")), (1, 2), iid)
            for post in panel.select(".fr-post"):
                self.assertIn("立場：", post.get_text(), iid)

    def test_rows_are_details_and_named_for_this_theme(self):
        rows = self.bg.select("details.fb-row")
        ids = [r["id"] for r in rows]
        self.assertEqual(ids, ["bg-definition", "bg-why", "bg-selection", "bg-candidates",
                               "bg-timeline", "bg-faq", "bg-classroom", "bg-unverified"])
        for r in rows:
            self.assertIsNone(r.get("open"))
        # 作り方・詳細データ・次に読むは手順7で継承する（背景には入れない）
        for absent in ("bg-method", "bg-table", "bg-related"):
            self.assertIsNone(self.bg.find(id=absent))

    def test_candidates_come_from_opening_config(self):
        cands = self.d["ocfg"]["candidates"]
        rows = self.bg.select("#bg-candidates tbody tr")
        self.assertEqual(len(rows), len(cands))
        self.assertEqual({r.th.get_text() for r in rows}, {c["name"] for c in cands})
        self.assertIn(f"{len(cands)}地域", self.bg.select_one("#bg-candidates .fb-title").get_text())
        hrefs = {a["href"] for a in self.bg.select("#bg-candidates tbody a")}
        self.assertEqual(hrefs, {c["url"] for c in cands})

    def test_faq_four_questions_without_opening_duplicates(self):
        qs = [dt.get_text() for dt in self.bg.select("#bg-faq dt")]
        self.assertEqual(len(qs), 4)
        for dup in ("副首都は大阪に決まったのですか？", "副首都は、いつ決まりますか？"):
            self.assertNotIn(dup, qs)

    def test_classroom_is_read_from_shared_config(self):
        cr = json.loads((ROOT / "configs/classroom/fukushuto.json").read_text(encoding="utf-8"))
        text = self.bg.select_one("#bg-classroom").get_text()
        for r in cr["reasons_pro"] + cr["reasons_con"]:
            self.assertIn(r["text"], text)
        for q in cr["questions"]:
            self.assertIn(q, text)

    def test_timeline_order_and_phase(self):
        events = [li["data-event"] for li in self.bg.select("#bg-timeline li")]
        self.assertEqual(events, ["referendum-2020", "enactment-2026", "draft", "comment-close", "enforce"])
        self.assertIn("（予定）", self.bg.select_one('#bg-timeline li[data-event="enforce"]').get_text())
        after = self.render_bg("2026-10-31")
        self.assertEqual(after["data-law-phase"], "after_unconfirmed")
        self.assertIn("施行予定でした。施行後の条文は編集部で確かめていません", after.get_text())
        self.assertIn("締め切られました", after.select_one("#bg-selection").get_text())

    def test_confirmed_phase_switches_and_hides_unverified(self):
        def edit(d):
            d["ocfg"]["law"]["enforcement_confirmed_on"] = "2026-11-01"
            d["ocfg"]["comment"]["result_published_on"] = "2026-10-30"
        bg = self.render_bg("2026-11-02", edit)
        self.assertIn("施行されました（2026年11月1日に条文を確認）", bg.get_text())
        self.assertIn("副首都法は、いつ施行されましたか？", bg.select_one("#bg-faq").get_text())
        unv = bg.select_one("#bg-unverified").get_text()
        self.assertNotIn("施行日を定める政令", unv)
        self.assertNotIn("意見募集の結果と", unv)

    def test_missing_phase_text_stops(self):
        def edit(d):
            row = next(r for g in d["bg"]["cfg"]["groups"] for r in g["rows"] if r["id"] == "definition")
            del row["phase_now"]["after_unconfirmed"]
        with self.assertRaises(SystemExit):
            self.render_bg("2026-10-10", edit)

    def test_themes_yaml_mismatch_stops(self):
        def edit(d):
            d["bg"]["theme"]["updated_at"] = "2026-01-01"
        with self.assertRaises(SystemExit):
            self.render_bg("2026-10-10", edit)



# ---------------------------------------------------------------- 手順7：公開候補と更新経路（docs/ は書き換えない）

import shutil  # noqa: E402

from scripts import fukushuto_layout as layout  # noqa: E402
from scripts import build_fukushuto_redesign as redesign  # noqa: E402

AS_OF = "2026-10-11"
INPUTS = (
    "THEMES.yaml",
    "docs/data/themes/fukushuto.json",
    "data/public/themes/fukushuto.json",
    "data/fukushuto_5issues-reread.json",
    "data/verification/fukushuto-claims.json",
    "data/verification/fukushuto-background.json",
    "quality/research/fukushuto-primary-sources.md",
)


def vote_block(text: str, name: str) -> str:
    return re.search(r"var " + name + r"=\[(.*?)\];", text, re.S).group(1)


def protected(text: str, name: str) -> str:
    return re.search(f"<!-- {name}_START -->.*?<!-- {name}_END -->", text, re.S).group()


class RedesignCandidateTests(unittest.TestCase):
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
                         "https://sns-reaction-map.jp/fukushuto-reaction-map.html")
        self.assertEqual(len(self.s.select("h1")), 1)

    def test_ga_and_adsense_only_in_release(self):
        for name in ("GA_TAG", "ADSENSE_TAG"):
            block = protected(self.source, name)
            self.assertIn(block, self.release)
            self.assertNotIn(block, self.preview)
        self.assertIn("G-K10S4YCZFH", self.release)
        self.assertIn('content="ca-pub-2542211932832864"', self.release)
        self.assertIn('name="robots" content="noindex"', self.preview)
        self.assertNotIn('name="robots"', self.release)

    def test_vote_contract_is_unchanged(self):
        for text in (self.release, self.preview):
            self.assertIn(f'data-vote-topic="{redesign.VOTE_TOPIC}"', text)
            self.assertIn("var TOPIC='fukushuto-issue-stance-v1'", text)
            for name in ("VOTE_ISSUES", "V2I", "STANCES"):
                if name == "V2I":
                    self.assertEqual(re.search(r"var V2I=\[[^\]]*\];", self.source).group(),
                                     re.search(r"var V2I=\[[^\]]*\];", text).group())
                else:
                    self.assertEqual(vote_block(self.source, name), vote_block(text, name), name)
            self.assertIn("choiceIdx:issueIdx*STANCES.length+stanceIdx", text)
            self.assertIn("(window.SNS_REDESIGN_PRODUCTION?'sns_vote_':'sns_vote_preview_')+TOPIC+'_my'", text)
        # 論点7×立場3＝21通り
        self.assertEqual(len(re.findall(r"\bk:'", vote_block(self.release, "VOTE_ISSUES"))), 7)
        self.assertEqual(len(re.findall(r"\bk:'", vote_block(self.release, "STANCES"))), 3)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=location.hostname==='sns-reaction-map.jp'", self.release)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=false", self.preview)
        scripts = self.s.select("script")
        config = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-config.js"))
        client = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-store.js"))
        self.assertEqual(config + 2, client)

    def test_adapter_vote_fingerprint_matches_source(self):
        from scripts.refresh_adapters.fukushuto import vote_fingerprint
        self.assertEqual(vote_fingerprint(self.source), vote_fingerprint(self.release))

    def test_faq_json_ld_matches_visible_faq(self):
        payloads = [json.loads(x.get_text()) for x in self.s.select('script[type="application/ld+json"]')]
        faq = [p for p in payloads if p.get("@type") == "FAQPage"]
        self.assertEqual(len(faq), 1)
        visible = redesign.faq_items(self.s)
        self.assertEqual(len(visible), 4)
        self.assertEqual([(q["name"], q["acceptedAnswer"]["text"]) for q in faq[0]["mainEntity"]], visible)
        self.assertEqual(sum(1 for p in payloads if p.get("@type") == "Article"), 1)
        # 旧ページの6問（fukushuto_search_entry.py）は使わない
        self.assertNotIn('id="fukushuto-faq-json-ld"', self.release)

    def test_inherited_sections_and_links(self):
        self.assertEqual(len(self.s.select("#planet-data")), 1)
        self.assertEqual(self.s.select_one("#planet-data").string, self.src.select_one("#planet-data").string)
        self.assertIn("社会全体の世論調査ではありません。", self.s.select_one("#caution").get_text())
        for sel in ("#detail-data", "#related-topics", "body > footer"):
            self.assertEqual(self.s.select_one(sel).get_text(), self.src.select_one(sel).get_text(), sel)
        self.assertNotIn("../../../docs/", self.release)
        hrefs = {a["href"] for a in self.s.select("footer a[href]")}
        for href in ("about.html#operator", "about.html#method", "privacy.html", "disclaimer.html"):
            self.assertIn(href, hrefs)
        self.assertIn('href="about.html#corrections"', self.release)
        self.assertIn('<time datetime="2026-07-15">', self.release)
        self.assertIn(f'<time datetime="{PUBLIC["updated_on"]}">', self.release)

    def test_classroom_section_contract(self):
        section = self.release[self.release.index("<!-- CLASSROOM_START -->"):self.release.index("<!-- CLASSROOM_END -->")]
        self.assertIn('class="classroom-print-btn"', section)
        self.assertEqual(len(re.findall(r'href="#issue-([^"]+)"', section)), 6)
        sources = section[section.index("classroom-sources"):section.index("classroom-questions")]
        self.assertEqual(len(re.findall(r'href="(https?://[^"]+)"', sources)), 3)
        self.assertLess(self.release.index("<!-- CLASSROOM_START -->"), self.release.index("<!-- ARTICLE_TRUST_START -->"))

    def test_planet_is_copied_from_source(self):
        """全体像の山なみは、元HTMLの対話式の山なみ（PLANET_SECTION）をそのまま写す（2026-10-11 に静的SVGから戻した）。"""
        src_section = re.search(r"<!-- PLANET_SECTION_START -->(.*?)<!-- PLANET_SECTION_END -->", self.source, re.S).group(1)
        src = soup_of(src_section)
        # 山なみのスクリプト・見た目・PLANET_DATA は1文字も変えない
        src_script = [x for x in src.find_all("script", recursive=False) if x.get("id") != "planet-data"][0].string
        self.assertEqual(self.release.count(src_script), 1)
        self.assertEqual(self.release.count(src.select_one("section.planet-panel > style").string), 1)
        self.assertEqual(self.release.count("window.PLANET_DATA="), 1)
        # 山なみは読書面の全体像の中。静的SVGと論点名リストは無い
        planet = self.s.select_one("#fukushuto-reading .fr-map section.planet-panel #planet-block")
        self.assertIsNotNone(planet)
        self.assertEqual(self.s.select(".fr-mountains, .fr-chip, .fr-map-shell"), [])
        # 立場モード・100マス・論点の一覧・見かた・図が使えないときの一覧は、元HTMLと同じ
        for sel in ("#modes", ".stage", "#dotbox", "#list", "#meta", ".floor-note", ".hint"):
            self.assertEqual(str(planet.select_one(sel)), str(src.select_one("#planet-block " + sel)), sel)
        self.assertEqual(planet.select_one("#fallback-nav").get_text(), src.select_one("#fallback-nav").get_text())
        # JSなしの論点一覧は新しい読書面へ直接つながる
        hrefs = [a["href"] for a in planet.select("#fallback-nav a")]
        self.assertEqual(sorted(hrefs), sorted("#issue-" + i["id"] for i in PUBLIC["issues"]))
        for href in hrefs:
            self.assertIsNotNone(self.s.find(id=href[1:]), href)
        # 新デザインで出さない部分（JSなし用の論点別本文・資料にしかない話・編集部整理）は外し、予想・クイズ・進捗は受け皿だけ
        self.assertEqual(planet.select("section.landing-panel, #ocean, #editorial"), [])
        for receiver in ("#guesses", "#quiz"):
            node = planet.select_one(receiver)
            self.assertTrue(node.has_attr("hidden") and not node.get_text(strip=True), receiver)
        self.assertTrue(self.s.select_one("#progress").has_attr("hidden"))
        # 調査条件は山なみの中（図の母数の位置）で、RESEARCH_CONDITIONS に囲まれている
        self.assertEqual(len(self.s.select("#caution")), 1)
        self.assertIsNotNone(planet.select_one("#research-conditions > #caution"))
        block = self.release[self.release.index("<!-- RESEARCH_CONDITIONS_START -->"):self.release.index("<!-- RESEARCH_CONDITIONS_END -->")]
        self.assertIn('id="caution"', block)
        # 山なみのスクリプトより後で、読書面（reading.js）と橋渡し（planet.js）が動く
        self.assertLess(self.release.index(src_script), self.release.index("window.FukushutoReading"))
        self.assertLess(self.release.index("window.FukushutoReading"), self.release.index("function goReading"))
        # 論点IDは PLANET_DATA・公開JSON・読書面で同じ（変換表は要らない）
        data = json.loads(re.search(r"window\.PLANET_DATA=(\{.*?\});?</script>", self.release, re.S).group(1))
        self.assertEqual(sorted(i["id"] for i in data["issues"]), sorted(i["id"] for i in PUBLIC["issues"]))
        for issue in data["issues"]:
            self.assertIsNotNone(self.s.select_one(f'[data-issue-panel="{issue["id"]}"]'), issue["id"])
        # 旧ページ用の部品は読み込まない（山なみの説明文には名前が出ることがある）
        for name in ('fukushuto-connected.js', 'fukushuto-connected-page.js', 'fukushuto-connected.css', 'theme-design.js', 'theme-design.css'):
            self.assertNotIn(f'="{name}', self.release)

    def test_planet_follows_source_updates(self):
        """定期更新で元HTMLの山なみが変われば、新ページにもそのまま載る（手入力なし）。"""
        changed = self.source.replace("このページの見かた", "このページの見かた（更新確認）", 1)
        self.assertNotEqual(changed, self.source)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.html"
            path.write_text(changed, encoding="utf-8")
            redesign.build(path, Path(temp) / "out", "release", as_of=AS_OF)
            page = (Path(temp) / "out" / redesign.PAGE).read_text(encoding="utf-8")
        self.assertIn("このページの見かた（更新確認）", page)
        broken = re.sub(r'<div class="dotbox" id="dotbox".*?<div class="waffle" id="waffle"></div>', "", self.source, count=1,
                        flags=re.S)
        self.assertNotEqual(broken, self.source)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.html"
            path.write_text(broken, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "山なみの部品"):
                redesign.build(path, Path(temp) / "out", "release", as_of=AS_OF)

    def test_old_anchor_targets_exist(self):
        for target in set(redesign.ALIASES.values()):
            self.assertIsNotNone(self.s.find(id=target), target)
        for alias in redesign.ALIASES:
            # 読み替えるのは、新ページに無いIDか、山なみのスクリプトのために隠して残した受け皿だけ
            if alias in redesign.HIDDEN_RECEIVERS:
                continue
            self.assertIsNone(self.s.find(id=alias), alias)
        for receiver in redesign.HIDDEN_RECEIVERS:
            self.assertIn(receiver, redesign.ALIASES)
            self.assertIsNotNone(self.s.find(id=receiver), receiver)
        # 受け皿は表示されていない（JSがあるとき）ので、旧アンカーは表示中の要素へ送る
        self.assertIn("cur.getClientRects().length", self.release)
        self.assertIsNotNone(self.s.find(id="planet-block"))
        self.assertNotIn("planet-block", redesign.ALIASES)
        for issue in PUBLIC["issues"]:
            self.assertIsNotNone(self.s.find(id="issue-" + issue["id"]))

    def test_no_tide_or_legacy_widgets(self):
        for marker in ("TIDE_CARD_START", "FUKUSHUTO_SEARCH_ENTRY_START", "THEME_DESIGN_START", "FUKUSHUTO_CONNECTED_START"):
            self.assertNotIn(marker, self.release)
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.release)
        for embed in self.s.select(".x-embed"):
            self.assertRegex(embed.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")

    def test_provenance_counts_and_detects_mismatch(self):
        from scripts.fukushuto_redesign_provenance import verified_selectors
        result = verified_selectors(self.release, ROOT)
        self.assertEqual(len(result), len(PUBLIC["issues"]) + 1)
        node = self.s.select_one('#issue-fukushuto-location li.fr-reason .fr-reason-n b')
        broken = self.release.replace(str(node), str(node).replace(node.get_text(), str(int(node.get_text().replace(",", "")) + 1)), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)

    def test_phase_switch_by_as_of(self):
        """基準日で時制が切り替わり、締切・施行日を過ぎても生成は止まらない。"""
        for as_of, law, comment in (("2026-10-17", "before", "closed"), ("2026-10-31", "after_unconfirmed", "closed")):
            with self.subTest(as_of=as_of):
                redesign.build(self.source_path, self.out / as_of, "release", as_of=as_of)
                s = soup_of((self.out / as_of / redesign.PAGE).read_text(encoding="utf-8"))
                self.assertEqual(s.select_one("#fukushuto-opening")["data-law-phase"], law)
                self.assertEqual(s.select_one("#fukushuto-opening")["data-comment-phase"], comment)
                self.assertEqual(s.select_one("#fukushuto-background")["data-law-phase"], law)


class LayoutTests(unittest.TestCase):
    def _root(self, temp: str) -> Path:
        root = Path(temp)
        shutil.copytree(ROOT / "configs", root / "configs")
        shutil.copytree(ROOT / "scripts/fukushuto_redesign", root / "scripts/fukushuto_redesign")
        for name in INPUTS:
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, root / name)
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
            (root / layout.PAGE).write_text('<meta name="fukushuto-layout">')
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
            self.assertIn(b'name="fukushuto-layout"', first)
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
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            (root / layout.CONFIG).write_text('{"enabled": true}')
            path = root / "data/fukushuto_5issues-reread.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            key = next(k for k, v in raw.items() if isinstance(v, dict) and v.get("items"))
            raw[key]["items"].pop()
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            before = (root / layout.PAGE).read_bytes()
            with self.assertRaisesRegex(ValueError, "照合で停止"):
                layout.finish(root, as_of=AS_OF)
            self.assertEqual(before, (root / layout.PAGE).read_bytes())
            self.assertFalse((root / layout.SOURCE).exists())

    def test_finish_without_as_of_after_deadlines_does_not_stop(self):
        """refresh_topic の公開候補生成は as_of を渡さずに finish を呼ぶ。
        公開JSONの更新日が締切・施行日を過ぎていても、他テーマの候補生成を止めない。"""
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            (root / layout.CONFIG).write_text('{"enabled": true}')
            for rel in ("docs/data/themes/fukushuto.json", "data/public/themes/fukushuto.json"):
                data = json.loads((root / rel).read_text(encoding="utf-8"))
                data["updated_on"] = "2026-11-02"
                (root / rel).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            themes = (root / "THEMES.yaml").read_text(encoding="utf-8")
            block = re.search(r"\n  fukushuto:\n(?:    .*\n)+", themes).group()
            fixed = re.sub(r"(\n    updated_at: )['\"]?[0-9-]+['\"]?", r"\g<1>2026-11-02", block, count=1)
            (root / "THEMES.yaml").write_text(themes.replace(block, fixed), encoding="utf-8")
            self.assertEqual(set(layout.finish(root)), {layout.SOURCE, layout.PAGE})
            s = soup_of((root / layout.PAGE).read_text(encoding="utf-8"))
            self.assertEqual(s.select_one("#fukushuto-opening")["data-law-phase"], "after_unconfirmed")
            self.assertEqual(s.select_one("#fukushuto-background")["data-comment-phase"], "closed")
        refresh = (ROOT / "scripts/refresh_topic.py").read_text(encoding="utf-8")
        self.assertEqual(refresh.count("finish_fukushuto_layout(candidate_root)"), 2)
        self.assertEqual(refresh.count("materialize_fukushuto(candidate_root)"), 1)


if __name__ == "__main__":
    unittest.main()
