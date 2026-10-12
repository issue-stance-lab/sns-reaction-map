"""憲法改正論議・新デザインの試作（冒頭、論点ごとの読書面、背景の開閉行）。docs/ は書き換えない。

生成AI（tests/test_ai_copyright_redesign.py）の手順5・6に当たる検査。読書面は最初から部活動型の圧縮済みの型で作る。
読書面の生成は公開できる入力（公開JSON・再読データ・立場の対応表・設定）だけを読む。非公開の正典が要るのは、
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

from scripts import constitutional_opening as opening

ROOT = opening.ROOT
PUBLIC = json.loads((ROOT / "docs/data/themes/constitutional-amendment.json").read_text(encoding="utf-8"))
CANON = ROOT / "social-samples/constitutional_amendment_hermes_arena_classified.json"
OPENING_CONFIG = ROOT / "configs/constitutional-amendment-opening.json"


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class OpeningTests(unittest.TestCase):
    """冒頭：確認日は設定の1か所から、国民投票法の改正の施行は基準日で3段階に切り替える。"""

    @classmethod
    def setUpClass(cls):
        cls.config, cls.public, cls.planet, cls.background = opening.load_inputs(OPENING_CONFIG)
        cls.data = opening.summarize(cls.public, cls.planet)

    def frag(self, config=None, as_of=None):
        return opening.render_fragment(config or self.config, self.data, self.background, "検索", as_of)

    def test_checked_on_single_source(self):
        when = opening.jp_date(self.config["checked_on"])
        frag = self.frag()
        self.assertIn(f"{when}確認", frag)  # いまの段階
        self.assertIn(f"{when}時点", frag)  # FAQ
        self.assertIn(f'data-checked-on="{self.config["checked_on"]}"', frag)
        cfg = copy.deepcopy(self.config)
        cfg["checked_on"] = "2026-12-01"
        self.assertIn("2026年12月1日確認", self.frag(cfg))
        cfg["checked_on"] = "2026-09-01"  # 背景台帳の確認日より古い
        with self.assertRaises(opening.OpeningError):
            self.frag(cfg)

    def test_default_as_of_is_public_updated_on(self):
        self.assertIn(f'data-as-of="{PUBLIC["updated_on"]}"', self.frag())
        self.assertEqual(opening.default_as_of(PUBLIC), PUBLIC["updated_on"])

    def test_law_phase_switches(self):
        law = self.config["law"]
        self.assertEqual(law["enforcement_on"], "2026-10-31")
        before = self.frag(as_of="2026-10-30")
        self.assertIn('data-law-phase="before"', before)
        self.assertIn("2026年10月31日に施行される予定です", before)
        after = self.frag(as_of="2026-10-31")
        self.assertIn('data-law-phase="after_unconfirmed"', after)
        self.assertIn("施行される予定でした。施行後の条文は編集部で確かめていません", after)
        cfg = copy.deepcopy(self.config)
        cfg["law"]["enforcement_confirmed_on"] = "2026-11-02"
        done = self.frag(cfg, as_of="2026-11-05")
        self.assertIn('data-law-phase="after_confirmed"', done)
        self.assertIn("2026年10月31日に施行されました（2026年11月2日に条文を確認）", done)

    def test_impossible_law_dates_stop(self):
        cfg = copy.deepcopy(self.config)
        cfg["law"]["enforcement_confirmed_on"] = "2026-10-20"  # 施行日より前
        with self.assertRaises(opening.OpeningError):
            self.frag(cfg, as_of="2026-11-05")
        cfg["law"]["enforcement_confirmed_on"] = "2026-11-02"
        with self.assertRaises(opening.OpeningError):  # 基準日が施行日より前
            self.frag(cfg, as_of="2026-10-12")
        cfg = copy.deepcopy(self.config)
        del cfg["procedure"]["footnote_phase"]["after_unconfirmed"]
        with self.assertRaises(opening.OpeningError):
            self.frag(cfg)

    def test_short_answer_does_not_call_221_ordinary_session(self):
        self.assertNotIn("通常国会", self.frag())
        self.assertIn("第221回", self.frag())

    def test_opening_css_lives_in_redesign_folder(self):
        self.assertTrue((opening.ASSETS / "opening.css").is_file())
        proto = ROOT / "quality/prototypes/constitutional-amendment-opening/opening.css"
        self.assertEqual(proto.read_text(encoding="utf-8"), (opening.ASSETS / "opening.css").read_text(encoding="utf-8"))


class ReadingPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts import constitutional_reading as reading

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

    def test_default_as_of_is_public_updated_on(self):
        self.assertEqual(self.reading.default_as_of(self.d), PUBLIC["updated_on"])
        self.assertIn(f'data-as-of="{PUBLIC["updated_on"]}"', self.html)

    def test_does_not_write_docs(self):
        self.assertNotIn("docs", str(self.page_path.relative_to(self.out)))
        self.assertNotIn("../../../docs/", self.html)

    def test_no_static_mountains(self):
        """山なみは手順7で元HTMLの対話式の図を写す。読書面は論点タブから始める。"""
        self.assertEqual(self.s.select(".fr-mountains, .fr-hill, .fr-chip, #planet-block"), [])
        first = self.s.select_one("#constitutional-amendment-reading .fr-panels > *")
        self.assertEqual(first.name, "nav")
        self.assertIn("fr-tabs", first["class"])

    def test_issue_order_count_desc_other_last(self):
        tabs = [a["data-issue-id"] for a in self.s.select(".fr-tab")]
        other = "constitutional-amendment-other"
        named = sorted((i for i in PUBLIC["issues"] if i["id"] != other), key=lambda i: -int(i["count"]))
        self.assertEqual(tabs, [i["id"] for i in named] + [other])

    def test_counts_and_stances_match_public_json(self):
        order = [s["id"] for s in self.reading.stance_order(self.d)]
        totals = Counter()
        for issue in PUBLIC["issues"]:
            for s in issue["stances"]:
                totals[s["id"]] += int(s["count"])
        self.assertEqual(order, sorted(totals, key=lambda k: -totals[k]))  # 慎重・反対→改正推進→中立→手続き重視
        for issue in PUBLIC["issues"]:
            panel = self.panel(issue["id"])
            self.assertIsNotNone(panel, issue["id"])
            self.assertEqual(panel.select_one(".fr-count b").get_text(), f'{int(issue["count"]):,}')
            by = {s["id"]: int(s["count"]) for s in issue["stances"]}
            for sel in (".fr-stance-mini b", ".fr-stance .fr-stance-list b"):
                self.assertEqual([b.get_text() for b in panel.select(sel)], [f"{by[sid]:,}" for sid in order], sel)

    def test_stance_band_keeps_not_a_poll_note(self):
        for issue in PUBLIC["issues"]:
            note = self.panel(issue["id"]).select_one(".fr-head-stance .fr-caveat")
            self.assertIn("世論調査ではありません", note.get_text())

    def test_reasons_recounted_from_reread_details(self):
        for label, rr in self.d["reread"].items():
            issue = next(i for i in PUBLIC["issues"] if i["label"] == label)
            panel = self.panel(issue["id"])
            for bid in rr["buckets"]:
                node = panel.select_one(f'li.fr-reason[data-reason="{bid}"] .fr-reason-n b')
                n = sum(1 for it in rr["items"] if it["bucket"] == bid)
                self.assertEqual(node.get_text(), f"{n:,}", (label, bid))

    def test_reason_stances_come_from_stance_table_and_sum_to_public(self):
        for label, rr in self.d["reread"].items():
            issue = next(i for i in PUBLIC["issues"] if i["label"] == label)
            total = Counter(self.reading.item_stance(self.d, it) for it in rr["items"])
            self.assertEqual({s["id"]: total.get(s["id"], 0) for s in issue["stances"]},
                             {s["id"]: int(s["count"]) for s in issue["stances"]}, label)
        table = json.loads((ROOT / "data/constitutional-amendment_reread-stances.json").read_text(encoding="utf-8"))
        self.assertEqual(table["count"], len(table["stances"]))
        self.assertEqual(table["public_mismatch"], 0)

    def test_does_not_read_private_canonical(self):
        self.assertNotIn("social-samples", (ROOT / "scripts/constitutional_reading.py").read_text(encoding="utf-8"))
        self.assertNotIn("social-samples", json.dumps(self.d["cfg"]["issues"], ensure_ascii=False))

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では立場の対応表を確かめられない")
    def test_stance_table_matches_canonical(self):
        canon = json.loads(CANON.read_text(encoding="utf-8"))
        by = {hashlib.sha256(str(r["tweet_id"]).encode()).hexdigest(): r["classification"]["stance"] for r in canon}
        for k, v in self.d["stances"].items():
            self.assertEqual(by[k], v)

    def test_stale_stance_table_would_stop(self):
        d = copy.deepcopy(self.d)
        key = d["reread_items"][0]["post_key"]
        keys = [s["key"] for s in d["planet"]["stances"]]
        d["stances"][key] = next(k for k in keys if k != d["stances"][key])
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        del d["stances"][key]
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_general_panel_is_complete(self):
        panel = self.panel("constitutional-amendment-general")
        self.assertIn("is-complete", panel["class"])
        self.assertTrue(panel.select(".fr-desc"))
        self.assertEqual(len(panel.select(".fr-voice")), len(self.d["reread"]["改憲全般"]["buckets"]))
        self.assertTrue(panel.select('.fr-memo-check[data-memo-check="article-96"]'))
        self.assertTrue(panel.select('.fr-vein[data-vein="constitutional-amendment-avoid-war"]'))
        self.assertTrue(panel.select('.fr-check[data-check="document"]'))
        for a in panel.select(".fr-see a"):
            self.assertIsNotNone(self.s.find(id=a["href"][1:]), a["href"])

    def test_compact_structure(self):
        """説明は1段落＋「くわしく」、理由は上位4件＋折りたたみ、説明は1位だけ data-on、照合・投稿・立場は閉じた折りたたみ。"""
        top = self.d["cfg"]["compact"]["top_reasons"]
        for issue in PUBLIC["issues"]:
            panel = self.panel(issue["id"])
            self.assertEqual(panel.select("details[open]"), [], issue["id"])
            first = panel.select_one(".fr-reasons > .fr-reason-list")
            n_buckets = len(self.d["reread"][issue["label"]]["buckets"])
            self.assertEqual(len(first.select(".fr-reason")), min(top, n_buckets))
            more = panel.select_one(".fr-reason-more")
            if n_buckets > top:
                self.assertIn(f"残り{n_buckets - top}分類", more.summary.get_text())
            if "is-complete" in panel["class"]:
                self.assertEqual(len(panel.select(".fr-header .fr-desc, .fr-panel-head > div > .fr-desc")), 1)
                on = panel.select(".fr-reason-detail[data-on]")
                self.assertEqual(len(on), 1)
                counts = [int(b.get_text().replace(",", "")) for b in panel.select(".fr-reasons .fr-reason-n b")]
                self.assertEqual(on[0]["data-reason"], panel.select_one(".fr-reasons li.fr-reason")["data-reason"])
                self.assertEqual(counts, sorted(counts, reverse=True))
                for sel in ("details.fr-posts", "details.fr-stance", ".fr-evidence details.fr-fold"):
                    self.assertTrue(panel.select(sel), (issue["id"], sel))
                for claim in panel.select(".fr-claim"):
                    self.assertTrue(claim.summary.select_one(".fr-verdict"))

    def test_posts_at_most_two_with_lazy_embed_and_original_links(self):
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.html)
        for panel in self.s.select(".fr-panel"):
            embeds = panel.select(".x-embed")
            self.assertLessEqual(len(embeds), 2)
            for e in embeds:
                self.assertRegex(e.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")
            self.assertEqual(len(panel.select(".fr-post")), len(embeds))

    def test_posts_differ_in_stance(self):
        labels = {i["id"]: i for i in PUBLIC["issues"]}
        for iid, icfg in self.d["cfg"]["issues"].items():
            posts = icfg.get("posts", {}).get("items", [])
            if len(posts) == 2 and not icfg["posts"].get("same_stance_reason"):
                st = {self.reading.post_stance(self.d, labels[iid], p) for p in posts}
                self.assertEqual(len(st), 2, iid)

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では代表投稿の選定基準を確かめられない")
    def test_selected_posts_meet_canonical_criteria(self):
        canon = json.loads(CANON.read_text(encoding="utf-8"))
        norm = lambda t: re.sub(r"\s+", "", t)
        texts = Counter(norm(x["text"]) for x in canon)
        by_id = {x["tweet_id"]: x for x in canon}
        labels = {i["id"]: i["label"] for i in PUBLIC["issues"]}
        ids = []
        for iid, icfg in self.d["cfg"]["issues"].items():
            for p in icfg.get("posts", {}).get("items", []):
                ids.append(p["id"])
                x = by_id[p["id"]]
                c = x["classification"]
                self.assertTrue(c["is_opinion"], p["id"])
                self.assertEqual(c["main_issue"], labels[iid], p["id"])
                self.assertTrue(c["article_usable"], p["id"])
                self.assertEqual(c["risk"], "low", p["id"])
                self.assertEqual(x["url"], p["url"], p["id"])
                self.assertEqual(texts[norm(x["text"])], 1, p["id"])
        self.assertEqual(len(ids), len(set(ids)))

    def test_count_mismatch_stops(self):
        d = copy.deepcopy(self.d)
        label = next(iter(d["reread"]))
        d["reread"][label]["items"].pop()
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

    def test_bad_posts_stop(self):
        d = copy.deepcopy(self.d)
        posts = d["cfg"]["issues"]["constitutional-amendment-general"]["posts"]["items"]
        posts[0]["url"] = posts[0]["url"].replace(posts[0]["id"], "1")
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        posts = d["cfg"]["issues"]["constitutional-amendment-general"]["posts"]["items"]
        posts[0]["id"] = "1"  # 再読データに無い投稿
        posts[0]["url"] = posts[0]["url"].rsplit("/", 1)[0] + "/1"
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_sunk_without_issue_needs_override(self):
        d = copy.deepcopy(self.d)
        d["cfg"]["sunk_issue_overrides"] = {}
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        for sc in PUBLIC["ocean_layer"]["sunk_continents"]:
            iid = self.reading.sunk_issue(self.d, sc)
            self.assertTrue(self.panel(iid).select(f'[data-sunk="{sc["id"]}"]') or
                            "is-pending" in self.panel(iid)["class"], sc["id"])


class AllIssuesAndBackgroundTests(unittest.TestCase):
    """手順6：残りの論点と背景の開閉行。"""

    @classmethod
    def setUpClass(cls):
        from scripts import constitutional_reading as reading
        from scripts import constitutional_background as background

        cls.reading, cls.background = reading, background
        cls.tmp = tempfile.TemporaryDirectory()
        cls.html = reading.build(Path(cls.tmp.name) / "a").read_text(encoding="utf-8")
        cls.s = soup_of(cls.html)
        cls.d = reading.load()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def render_bg(self, d=None, as_of=None):
        d = d or self.d
        return self.background.render(d, as_of or PUBLIC["updated_on"], self.reading.ordered_issues(d))

    def test_all_issues_complete_with_voices_and_posts(self):
        labels = {i["id"]: i["label"] for i in PUBLIC["issues"]}
        for iid, icfg in self.d["cfg"]["issues"].items():
            self.assertEqual(icfg["status"], "complete", iid)
            self.assertEqual(len(icfg["description"]), 2, iid)
            buckets = self.d["reread"][labels[iid]]["buckets"]
            self.assertEqual(set(icfg["reasons"]), set(buckets), iid)
            posts = icfg["posts"]["items"]
            self.assertIn(len(posts), (1, 2), iid)
            if len(posts) == 1:
                self.assertTrue(icfg["posts"]["one_reason"], iid)
                self.assertLess(int(next(i for i in PUBLIC["issues"] if i["id"] == iid)["count"]), 50, iid)
        self.assertEqual(self.s.select(".fr-panel.is-pending"), [])

    def test_see_also_targets_exist(self):
        for a in self.s.select(".fr-see a, .fb-issues a, .fb-to-issue"):
            self.assertIsNotNone(self.s.find(id=a["href"][1:]), a["href"])

    def test_rows_are_closed_details(self):
        rows = self.s.select("#constitutional-amendment-background details.fb-row")
        ids = [r["id"] for r in rows]
        self.assertEqual(ids, ["bg-article96", "bg-referendum-law", "bg-issues-map", "bg-why",
                               "bg-timeline", "bg-faq", "bg-classroom", "bg-unverified"])
        self.assertTrue(all(not r.has_attr("open") for r in rows))

    def test_law_phase_in_background(self):
        before = soup_of(self.render_bg(as_of="2026-10-30"))
        self.assertIn("施行される予定です", before.select_one("#bg-referendum-law [data-phase]").get_text())
        self.assertIn("（予定）", before.select_one('[data-event="law-enforcement"]').get_text())
        after = soup_of(self.render_bg(as_of="2026-11-02"))
        self.assertIn("施行される予定でした", after.select_one("#bg-referendum-law [data-phase]").get_text())
        self.assertIn("施行後の条文は、まだ確かめていません", after.select_one(".fb-unverified").get_text())
        d = copy.deepcopy(self.d)
        d["ocfg"]["law"]["enforcement_confirmed_on"] = "2026-11-02"
        done = soup_of(self.render_bg(d, as_of="2026-11-05"))
        self.assertIn("施行されました", done.select_one("#bg-referendum-law [data-phase]").get_text())
        self.assertNotIn("施行後の条文は、まだ確かめていません", done.select_one(".fb-unverified").get_text())
        d = copy.deepcopy(self.d)
        del d["bg"]["cfg"]["groups"][0]["rows"][1]["phase_law"]["after_confirmed"]
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_timeline_overrides_ledger_wording(self):
        tl = self.s.select_one("#bg-timeline")
        text = tl.get_text()
        self.assertNotIn("通常国会", text)
        self.assertNotIn("9月13日時点では施行前", text)
        self.assertIn("第222回国会（臨時会）", text)
        events = [li["data-event"] for li in tl.select("li[data-event]")]
        self.assertEqual(events[-2:], ["current-stage", "law-enforcement"])

    def test_faq_four_questions_without_opening_duplicates(self):
        qs = [dt.get_text() for dt in self.s.select("#bg-faq dt")]
        self.assertEqual(len(qs), 4)
        opening_qs = [i["q"] for i in json.loads(OPENING_CONFIG.read_text(encoding="utf-8"))["faq"]["items"]]
        self.assertFalse(set(qs) & set(opening_qs))

    def test_classroom_is_read_from_shared_config(self):
        cr = json.loads((ROOT / "configs/classroom/constitutional-amendment.json").read_text(encoding="utf-8"))
        text = self.s.select_one("#bg-classroom").get_text()
        for r in cr["reasons_pro"] + cr["reasons_con"]:
            self.assertIn(r["text"], text)

    def test_why_row_is_ledger_text(self):
        ledger = self.d["background"]
        text = self.s.select_one("#bg-why").get_text()
        for para in ledger["cause"]:
            self.assertIn(para, text)

    def test_themes_yaml_mismatch_stops(self):
        d = copy.deepcopy(self.d)
        d["bg"]["theme"]["updated_at"] = "2026-01-01"
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_unknown_memo_section_stops(self):
        d = copy.deepcopy(self.d)
        d["bg"]["cfg"]["groups"][1]["rows"][1]["items"][0]["memo_section"] = "存在しない見出し"
        with self.assertRaises(SystemExit):
            self.render_bg(d)



# ---------------------------------------------------------------- 手順7：公開候補と更新経路（docs/ は書き換えない）

import shutil  # noqa: E402

from scripts import build_constitutional_redesign as redesign  # noqa: E402
from scripts import constitutional_layout as layout  # noqa: E402

AS_OF = "2026-10-12"
INPUTS = (
    "THEMES.yaml",
    "docs/data/themes/constitutional-amendment.json",
    "data/public/themes/constitutional-amendment.json",
    "data/constitutional-amendment_issues-reread.json",
    "data/constitutional-amendment_reread-stances.json",
    "data/verification/constitutional-amendment-claims.json",
    "data/verification/constitutional-amendment-background.json",
    "quality/research/constitutional-amendment-primary-sources.md",
)


def protected(text: str, name: str) -> str:
    return re.search(f"<!-- {name}_START -->.*?<!-- {name}_END -->", text, re.S).group()


def vote_defs(text: str) -> tuple[str, str]:
    issues = re.search(r"const issues=\[(.*?)\];", text, re.S).group(1)
    stances = re.search(r"const stances=\[(.*?)\];", text, re.S).group(1)
    return issues, stances


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
                         "https://sns-reaction-map.jp/constitutional-amendment-reaction-map.html")
        self.assertEqual(len(self.s.select("h1")), 1)
        ids = Counter(t["id"] for t in self.s.find_all(id=True))
        self.assertEqual([k for k, v in ids.items() if v > 1], [])  # 同じidを2つ置かない

    def test_ga_and_adsense_only_in_release(self):
        for name in ("GA_TAG", "ADSENSE_TAG"):
            block = protected(self.source, name)
            self.assertIn(block, self.release)
            self.assertNotIn(block, self.preview)
        self.assertIn("G-K10S4YCZFH", self.release)
        self.assertIn("ca-pub-2542211932832864", self.release)
        self.assertNotIn("ca-pub-2542211932832864", self.preview)
        self.assertNotIn("G-K10S4YCZFH", self.preview)
        self.assertIn('name="robots" content="noindex"', self.preview)
        self.assertNotIn('name="robots"', self.release)

    def test_vote_contract_is_unchanged(self):
        for text in (self.release, self.preview):
            self.assertIn(f'data-vote-topic="{redesign.VOTE_TOPIC}"', text)
            self.assertIn("const TOPIC='constitutional-amendment-issue-stance-v1'", text)
            self.assertEqual(vote_defs(self.source), vote_defs(text))
            self.assertIn("choiceIdx:selected*stances.length+stanceIndex", text)
            self.assertIn("const STORAGE_KEY=window.SNS_REDESIGN_PRODUCTION?'sns_vote_constitutional_amendment_2step':"
                          "'sns_vote_preview_constitutional_amendment_2step';", text)
        issues, stances = vote_defs(self.release)
        self.assertEqual(len(re.findall(r'"k":', issues)), 6)  # 論点6×立場4＝24通り
        self.assertEqual(len(re.findall(r"\bk:'", stances)), 4)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=location.hostname==='sns-reaction-map.jp'", self.release)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=false", self.preview)
        scripts = self.s.select("script")
        config = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-config.js"))
        client = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-store.js"))
        self.assertEqual(config + 2, client)

    def test_adapter_vote_fingerprint_matches_source(self):
        from scripts.refresh_adapters.constitutional import vote_fingerprint
        self.assertEqual(vote_fingerprint(self.source), vote_fingerprint(self.release))
        self.assertEqual(vote_fingerprint(self.release)[3], 24)

    def test_faq_json_ld_matches_visible_faq(self):
        payloads = [json.loads(x.get_text()) for x in self.s.select('script[type="application/ld+json"]')]
        faq = [p for p in payloads if p.get("@type") == "FAQPage"]
        self.assertEqual(len(faq), 1)
        visible = redesign.faq_items(self.s)
        self.assertEqual(len(visible), 8)  # 冒頭の「よく聞かれること」4問＋背景の「よくある質問」4問
        self.assertEqual([(q["name"], q["acceptedAnswer"]["text"]) for q in faq[0]["mainEntity"]], visible)
        texts = self.s.get_text()
        for q, a in visible:
            self.assertIn(q, texts)
        self.assertEqual(sum(1 for p in payloads if p.get("@type") == "Article"), 1)
        # 旧ページの検索入口・連動表示・テーマ共通の見た目は読み込まない
        self.assertNotIn('id="change-lens"', self.release)
        for name in ("constitutional-search-entry.js", "constitutional-search-entry.css", "constitutional-connected.js",
                     "constitutional-connected-page.js", "constitutional-connected.css", "theme-design.js", "theme-design.css"):
            self.assertNotIn(f'="{name}', self.release)

    def test_inherited_sections_and_links(self):
        self.assertEqual(len(self.s.select("#planet-data")), 1)
        self.assertEqual(self.s.select_one("#planet-data").string, self.src.select_one("#planet-data").string)
        self.assertIn("社会全体の世論調査ではありません。", self.s.select_one("#caution").get_text())
        for sel in ("#detail-data", "#related-topics", "body > footer", "#related-theme-tracking"):
            self.assertEqual(self.s.select_one(sel).get_text(), self.src.select_one(sel).get_text(), sel)
        hrefs = {a["href"] for a in self.s.select("footer a[href]")}
        for href in ("about.html#operator", "about.html#method", "privacy.html", "disclaimer.html"):
            self.assertIn(href, hrefs)
        self.assertIn('<time datetime="2026-06-24">', self.release)
        self.assertIn(f'<time datetime="{PUBLIC["updated_on"]}">', self.release)
        self.assertIsNotNone(self.s.select_one('header.modern-site-header a[href="index.html"]'))

    def test_tide_card_is_inherited_verbatim_inside_fold(self):
        block = re.search(r'<section class="update-dashboard"[^>]*><!-- TIDE_CARD_START -->.*?<!-- TIDE_CARD_END --></section>',
                          self.source, re.S).group()
        self.assertEqual(self.release.count(block), 1)
        self.assertIn("/* TIDE_CARD_START */", self.release)
        fold = self.s.select_one("#cap-trend-more")
        self.assertEqual(fold.name, "details")
        self.assertFalse(fold.has_attr("open"))
        self.assertIsNotNone(fold.select_one("#constitutional-tide-widget"))
        glance = self.s.select_one("#cap-trend .cap-trend-glance")
        self.assertEqual(len(glance.select(".cap-trend-spark svg polyline")), 4)
        self.assertIn(self.s.select_one("[data-tide-headline]").get_text(), glance.select_one(".cap-trend-lead").get_text())
        self.assertLess(self.release.index("TIDE_CARD_START -->"), self.release.index('id="vote-section"'))

    def test_issue_glance_from_tide(self):
        data = json.loads(re.search(r"const datasets = (\{.*?\});\n", self.release, re.S).group(1))
        rows = {r["label"]: r for r in data["issue"]["rows"]}
        for issue in PUBLIC["issues"]:
            box = self.s.find(id="issue-" + issue["id"]).select_one(".fr-glance")
            link = box.select_one(".fr-glance-link")
            self.assertEqual((link["href"], link["data-tide-mode"]), ("#constitutional-tide-widget", "issue"))
            cap = box.select_one(".fr-glance-cap")
            if issue["label"] not in rows:
                self.assertIsNone(cap, issue["id"])  # 「その他」は潮目の論点に無い
                continue
            self.assertIn(f'{rows[issue["label"]]["previous"]:.1f}%', cap.get_text())
            self.assertIn(f'{rows[issue["label"]]["current"]:.1f}%', cap.get_text())
            self.assertNotIn("件", box.select_one(".fr-glance-chart").get_text())

    def test_method_fold_holds_trust_and_detail_data(self):
        method = self.s.select_one("#cap-method")
        self.assertEqual(method.name, "details")
        self.assertFalse(method.has_attr("open"))
        self.assertIsNotNone(method.select_one("#detail-data"))
        trust = protected(self.source, "ARTICLE_TRUST")
        self.assertLess(self.release.index('id="cap-method"'), self.release.index(trust))
        self.assertLess(self.release.index(trust), self.release.index('id="related-topics"'))

    def test_folds_start_closed(self):
        for sel in ("#constitutional-amendment-reading", "#constitutional-amendment-background", "#ca-open"):
            self.assertEqual([d.get("class") for d in self.s.select(sel + " details[open]")], [], sel)

    def test_classroom_section_contract(self):
        section = self.release[self.release.index("<!-- CLASSROOM_START -->"):self.release.index("<!-- CLASSROOM_END -->")]
        self.assertIn('class="classroom-print-btn"', section)
        self.assertIn("classroom-sources", section)
        self.assertIn("classroom-questions", section)
        self.assertLess(self.release.index("<!-- CLASSROOM_START -->"), self.release.index("<!-- ARTICLE_TRUST_START -->"))

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
        # 旧ページで外から指せた節のidは、新ページにあるか、読み替え先があるか（js の内部用idは除く）
        internal = ("ca-reason-count-", "ca-check-note-", "ca-concern-count-", "ca-source-note-", "issue-count-",
                    "explainer-modal", "constitutional-connected-data", "pseg", "stance-glance-result-text")
        for node in self.src.find_all(id=True):
            old = node["id"]
            if self.s.find(id=old) is not None or old in redesign.ALIASES or old.startswith(internal):
                continue
            self.assertTrue(any(old.startswith(p) for p in redesign.ISSUE_PREFIXES), old)
        for issue in PUBLIC["issues"]:
            self.assertIsNotNone(self.src.find(id="issue-" + issue["id"]))
            self.assertEqual(self.s.find(id="issue-" + issue["id"])["data-issue-panel"], issue["id"])
        for kept in ("vote-section", "detail-data", "related-topics", "caution", "planet-data", "research-conditions",
                     "constitutional-tide-widget"):
            self.assertIsNotNone(self.s.find(id=kept), kept)

    def test_planet_is_copied_from_source(self):
        """全体像の山なみは、元HTMLの対話式の山なみ（PLANET_SECTION）をそのまま写す（生成AIの10節と同じ）。"""
        src_section = re.search(r"<!-- PLANET_SECTION_START -->(.*?)<!-- PLANET_SECTION_END -->", self.source, re.S).group(1)
        src = soup_of(src_section)
        src_script = [x for x in src.find_all("script", recursive=False) if x.get("id") != "planet-data"][0].string
        self.assertEqual(self.release.count(src_script), 1)
        self.assertEqual(self.release.count(src.select_one("section.planet-panel > style").string), 1)
        self.assertEqual(self.release.count("window.PLANET_DATA="), 1)
        planet = self.s.select_one("#constitutional-amendment-reading .fr-map section.planet-panel #planet-block")
        self.assertIsNotNone(planet)
        # 山なみは論点タブの上
        self.assertLess(self.release.index('id="planet-block"'), self.release.index('class="fr-tabs"'))
        for sel in ("#modes", ".stage", "#dotbox", "#list", "#meta"):
            self.assertEqual(str(planet.select_one(sel)), str(src.select_one("#planet-block " + sel)), sel)
        hrefs = [a["href"] for a in planet.select("#fallback-nav a")]
        self.assertEqual(sorted(hrefs), sorted("#issue-" + i["id"] for i in PUBLIC["issues"]))
        self.assertEqual(planet.select("section.landing-panel, #ocean, #editorial, span.issue-anchor"), [])
        for receiver in ("#guesses", "#quiz"):
            node = planet.select_one(receiver)
            self.assertTrue(node.has_attr("hidden") and not node.get_text(strip=True), receiver)
        self.assertTrue(self.s.select_one("#progress").has_attr("hidden"))
        self.assertIsNotNone(planet.select_one("#research-conditions > #caution"))
        self.assertLess(self.release.index(src_script), self.release.index("window.ConstitutionalReading"))
        self.assertLess(self.release.index("window.ConstitutionalReading"), self.release.index("function goReading"))

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

    def test_no_legacy_widgets(self):
        for marker in ("SEARCH_ENTRY_START", "THEME_DESIGN_START", "CONSTITUTIONAL_CONNECTED_START",
                       "STANCE_GLANCE_START", "THEME_COUNT_START", "FEATURED_POSTS_START"):
            self.assertNotIn("<!-- " + marker, self.release)
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.release)
        for embed in self.s.select(".x-embed"):
            self.assertRegex(embed.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")

    def test_provenance_counts_and_detects_mismatch(self):
        from scripts.constitutional_count_provenance import verified_selectors
        result = verified_selectors(self.release, ROOT)
        self.assertEqual(len(result), len(PUBLIC["issues"]) + 1)
        node = self.s.select_one("#issue-constitutional-amendment-general li.fr-reason .fr-reason-n b")
        broken = self.release.replace(str(node), str(node).replace(node.get_text(), str(int(node.get_text().replace(",", "")) + 1)), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)
        mini = self.s.select_one("#issue-constitutional-amendment-general article.fr-reason-detail .fr-mini")
        label = mini["aria-label"]
        n = re.search(r"慎重・反対 (\d[\d,]*)件", label).group(1)
        broken = self.release.replace(label, label.replace(f"慎重・反対 {n}件", f"慎重・反対 {int(n.replace(',', '')) + 1}件"), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)

    def test_law_phase_switch_by_as_of(self):
        """基準日で国民投票法の改正の施行の段階が切り替わり、施行日（10/31）を過ぎても生成は止まらない。"""
        self.assertEqual(self.s.select_one("#ca-open")["data-law-phase"], "before")
        redesign.build(self.source_path, self.out / "after", "release", as_of="2026-11-01")
        s = soup_of((self.out / "after" / redesign.PAGE).read_text(encoding="utf-8"))
        self.assertEqual(s.select_one("#ca-open")["data-law-phase"], "after_unconfirmed")
        self.assertIn("まだ確かめていません", s.select_one("#bg-unverified").get_text())


class LayoutTests(unittest.TestCase):
    def _root(self, temp: str) -> Path:
        root = Path(temp)
        shutil.copytree(ROOT / "configs", root / "configs")
        shutil.copytree(ROOT / "scripts/constitutional_redesign", root / "scripts/constitutional_redesign")
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
            (root / layout.PAGE).write_text('<meta name="constitutional-layout">')
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
            self.assertIn(b'name="constitutional-layout"', first)
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
            path = root / "data/constitutional-amendment_issues-reread.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw["items"].pop()
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            before = (root / layout.PAGE).read_bytes()
            with self.assertRaisesRegex(ValueError, "照合で停止"):
                layout.finish(root, as_of=AS_OF)
            self.assertEqual(before, (root / layout.PAGE).read_bytes())
            self.assertFalse((root / layout.SOURCE).exists())

    def test_finish_without_as_of_after_enforcement_does_not_stop(self):
        """refresh_topic の公開候補生成は as_of を渡さずに finish を呼ぶ。
        公開JSONの更新日が国民投票法の改正の施行日（10/31）を過ぎていても、他テーマの候補生成を止めない。"""
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            (root / layout.CONFIG).write_text('{"enabled": true}')
            for rel in ("docs/data/themes/constitutional-amendment.json", "data/public/themes/constitutional-amendment.json"):
                data = json.loads((root / rel).read_text(encoding="utf-8"))
                data["updated_on"] = "2026-11-02"
                (root / rel).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            themes = (root / "THEMES.yaml").read_text(encoding="utf-8")
            block = re.search(r"\n  constitutional-amendment:\n(?:    .*\n)+", themes).group()
            fixed = re.sub(r"(\n    updated_at: )['\"]?[0-9-]+['\"]?", r"\g<1>2026-11-02", block, count=1)
            (root / "THEMES.yaml").write_text(themes.replace(block, fixed), encoding="utf-8")
            self.assertEqual(set(layout.finish(root)), {layout.SOURCE, layout.PAGE})
            s = soup_of((root / layout.PAGE).read_text(encoding="utf-8"))
            self.assertEqual(s.select_one("#ca-open")["data-law-phase"], "after_unconfirmed")
        refresh = (ROOT / "scripts/refresh_topic.py").read_text(encoding="utf-8")
        self.assertEqual(refresh.count("finish_constitutional_layout(candidate_root)"), 2)
        self.assertEqual(refresh.count("materialize_constitutional(candidate_root)"), 1)
        adapter = (ROOT / "scripts/refresh_adapters/constitutional.py").read_text(encoding="utf-8")
        self.assertIn("current_page = source_for_refresh(root)", adapter)


if __name__ == "__main__":
    unittest.main()
