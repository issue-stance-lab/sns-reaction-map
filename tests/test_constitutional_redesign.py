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


if __name__ == "__main__":
    unittest.main()
