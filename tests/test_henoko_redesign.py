"""辺野古高校生死亡事故・新デザインの試作（冒頭、論点ごとの読書面、背景の開閉行）。docs/ は書き換えない。

学校でのあだ名禁止（tests/test_nickname_redesign.py）の手順5・6に当たる検査。読書面は最初から部活動型の圧縮済みの型で作る。
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

from scripts import henoko_opening as opening

ROOT = opening.ROOT
PUBLIC = json.loads((ROOT / "docs/data/themes/henoko-student-accident.json").read_text(encoding="utf-8"))
CANON = ROOT / "social-samples/henoko/henoko_hermes_arena_classified.json"
REREAD = json.loads((ROOT / "data/henoko-student-accident_issues-reread.json").read_text(encoding="utf-8"))
STANCES = json.loads((ROOT / "data/henoko-student-accident_reread-stances.json").read_text(encoding="utf-8"))
OPENING_CONFIG = ROOT / "configs/henoko-student-accident-opening.json"
OTHER = "henoko-student-accident-other"
FIRST = "henoko-student-accident-safety"
FIRST_LABEL = "安全管理・事故原因"
# 被害者への配慮で、読書面・背景に出さない語（冒頭の設計記録「被害者への配慮で避けた表現」）
AVOID = ("同志社", "平和丸", "不屈", "女子高", "女子生徒", "遺族", "🛟", "⚓", "🚢", "🌊")


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def key(tweet_id: str) -> str:
    return hashlib.sha256(str(tweet_id).encode()).hexdigest()


def write_json(tmp: str, name: str, data) -> Path:
    path = Path(tmp) / name
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


class OpeningTests(unittest.TestCase):
    """冒頭：確認日は設定の1か所から。報告書の公表は report の3段階。正本の見た目は scripts/henoko_redesign/。"""

    @classmethod
    def setUpClass(cls):
        cls.ctx = opening.load_inputs(OPENING_CONFIG)
        cls.config = cls.ctx["config"]

    def frag(self, config=None):
        ctx = dict(self.ctx)
        ctx["config"] = config or self.config
        return opening.render_fragment(ctx)

    def frag_with_timeline(self, config=None):
        """年表と未公表欄を冒頭に置く形（timeline.placement "opening"）。いまの設定は背景に置くので、文の作り方の確認に使う。"""
        cfg = copy.deepcopy(config or self.config)
        cfg["timeline"]["placement"] = "opening"
        return self.frag(cfg)

    def load_with(self, cfg):
        with tempfile.TemporaryDirectory() as tmp:
            return opening.load_inputs(write_json(tmp, "c.json", cfg))

    def test_checked_on_single_source(self):
        when = opening.jp_date(self.config["checked_on"])
        frag = self.frag_with_timeline()
        self.assertIn(f'data-checked-on="{self.config["checked_on"]}"', frag)
        self.assertIn(f"{when}時点で調査中", frag)
        self.assertNotIn("checked", self.config)
        cfg = copy.deepcopy(self.config)
        cfg["checked_on"] = "2026-12-01"
        self.assertIn("2026年12月1日時点で調査中", self.frag_with_timeline(cfg))

    def test_report_phases(self):
        frag = self.frag_with_timeline()
        self.assertIn('data-report-phase="unpublished"', frag)
        self.assertIn("事故の調査報告書は、まだ公表されていません。", frag)
        cfg = copy.deepcopy(self.config)
        cfg["report"]["published_on"] = "2026-10-10"
        frag = self.frag_with_timeline(cfg)
        self.assertIn('data-report-phase="published_unchecked"', frag)
        self.assertIn("2026年10月10日に公表されました", frag)
        self.assertIn("確認しているところです", frag)
        self.assertNotIn("まだ公表されていません", frag)
        cfg["report"]["content_checked_on"] = "2026-10-12"
        frag = self.frag_with_timeline(cfg)
        self.assertIn('data-report-phase="published_checked"', frag)
        self.assertIn("2026年10月12日に編集部が内容を確かめました", frag)

    def test_impossible_dates_stop(self):
        bad = []
        for change in ({"checked": "2026-09-07"}, {"checked_on": "2026-09-01"}):
            cfg = copy.deepcopy(self.config)
            cfg.update(change)
            bad.append(cfg)
        for report in ({"published_on": "2026-12-01"}, {"content_checked_on": "2026-10-01"},
                       {"published_on": "2026-10-10", "content_checked_on": "2026-10-09"}):
            cfg = copy.deepcopy(self.config)
            cfg["report"].update(report)
            bad.append(cfg)
        cfg = copy.deepcopy(self.config)
        cfg["timeline"]["entries"][0].pop("source")
        bad.append(cfg)
        for cfg in bad:
            with self.assertRaises(SystemExit):
                self.load_with(cfg)

    def test_checked_on_backed_by_memo(self):
        memo = (ROOT / "quality/research/henoko-student-accident-primary-sources.md").read_text(encoding="utf-8")
        self.assertIn(f"【{self.config['checked_on']}追記】", memo)

    def test_rechecked_sources_reflected(self):
        """2026-10-13 の取り直しで直した出典（県議会の404・3月16日の出典・告発の対象）。"""
        text = json.dumps(self.config, ensure_ascii=False)
        self.assertNotIn("r80819henokonittei.pdf", text)
        self.assertIn("2gou.r80819henoko.pdf", text)
        first = self.config["timeline"]["entries"][0]
        self.assertIn("jtsb.mlit.go.jp", first["source"]["url"])
        self.assertIn("1隻の船長", text)
        shown = soup_of(self.frag()).get_text()
        for word in AVOID:
            self.assertNotIn(word, shown, word)

    def test_opening_assets_live_in_redesign_folder(self):
        css = (ROOT / "scripts/henoko_redesign/opening.css").read_text(encoding="utf-8")
        self.assertEqual((ROOT / "quality/prototypes/henoko-student-accident-opening/opening.css").read_text(encoding="utf-8"), css)


class ReadingPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts import henoko_reading as reading

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

    def reading_text(self):
        node = self.s.select_one("#henoko-student-accident-reading")
        return node.get_text()

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
        src = (ROOT / "scripts/henoko_reading.py").read_text(encoding="utf-8")
        self.assertNotIn("social-samples", src)
        self.assertNotIn("social-samples", json.dumps(self.d["cfg"]["issues"], ensure_ascii=False))

    def test_no_static_mountains_and_no_tab_icons(self):
        self.assertEqual(self.s.select(".fr-mountains, .fr-hill, .fr-chip, #planet-block, .fr-tab-icon"), [])
        first = self.s.select_one("#henoko-student-accident-reading .fr-panels > *")
        self.assertEqual(first.name, "nav")

    def test_victim_care_words_absent(self):
        shown = [self.reading_text()]
        for icfg in self.d["cfg"]["issues"].values():
            shown += icfg.get("description", []) + [r.get("voice", "") for r in icfg.get("reasons", {}).values()]
            shown += [p["label"] + p["summary"] for p in icfg.get("posts", {}).get("items", [])]
        text = "".join(shown)
        for word in AVOID:
            self.assertNotIn(word, text, word)

    def test_issue_order_and_zero_other_hidden(self):
        tabs = [a["data-issue-id"] for a in self.s.select(".fr-tab")]
        named = sorted((i for i in PUBLIC["issues"] if int(i["count"]) > 0 and i["id"] != OTHER),
                       key=lambda i: (-int(i["count"]), i["id"]))
        self.assertEqual(tabs, [i["id"] for i in named])
        self.assertIsNone(self.panel(OTHER))
        d = copy.deepcopy(self.d)
        other = next(i for i in d["public"]["issues"] if i["id"] == OTHER)
        other["count"] = 1
        other["stances"][3]["count"] = 1
        self.assertEqual(self.reading.ordered_issues(d)[-1]["id"], OTHER)
        self.assertIn("data-unpublished", self.reading.render_panel(d, other, FIRST, 7))

    def test_note_says_uncollected_and_next(self):
        note = self.s.select_one(".fr-note").get_text()
        self.assertIn("10月8日より前の投稿", note)
        self.assertIn("10月22日", note)

    def test_counts_and_stances_match_public_json(self):
        order = [s["id"] for s in self.reading.stance_order(self.d)]
        for issue in PUBLIC["issues"]:
            if int(issue["count"]) == 0:
                continue
            panel = self.panel(issue["id"])
            self.assertEqual(panel.select_one(".fr-count b").get_text(), f'{int(issue["count"]):,}')
            by = {s["id"]: int(s["count"]) for s in issue["stances"]}
            self.assertEqual([b.get_text() for b in panel.select(".fr-stance .fr-stance-list b")], [f"{by[sid]:,}" for sid in order])
            note = panel.select_one("[data-stance-note]").get_text()
            self.assertIn(self.d["cfg"]["stance_common"]["caveat"], note)
            for s in self.reading.stance_order(self.d):
                if by[s["id"]] and by[s["id"]] != int(issue["count"]):
                    self.assertIn(f'{s["label"]}{by[s["id"]]:,}件', note)
            # 論点の見出しの下に帯を出さない（立場は1文）
            self.assertIsNone(panel.select_one(".fr-panel-head .fr-band"))

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

    def test_stance_table_matches_reread(self):
        self.assertEqual(set(STANCES["stances"]), {i["post_key"] for i in REREAD["items"]})
        self.assertEqual(STANCES["count"], int(PUBLIC["opinion_count"]))
        self.assertEqual(STANCES["public_mismatch"], 0)

    def test_stale_stance_table_stops(self):
        reading = self.reading
        with tempfile.TemporaryDirectory() as tmp:
            table = copy.deepcopy(STANCES)
            table["stances"].popitem()
            cfg = json.loads(reading.CONFIG.read_text(encoding="utf-8"))
            cfg["reread_stances_json"] = str(write_json(tmp, "t.json", table))
            with self.assertRaises(SystemExit):
                reading.load(write_json(tmp, "c.json", cfg))
        d = copy.deepcopy(self.d)
        item = d["reread"][FIRST_LABEL]["items"][0]
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
        tally = Counter((by[k]["main_issue"], v) for k, v in STANCES["stances"].items())
        for issue in PUBLIC["issues"]:
            for s in issue["stances"]:
                self.assertEqual(tally[(issue["label"], s["label"])], int(s["count"]), (issue["label"], s["label"]))

    def test_first_panel_is_complete(self):
        panel = self.panel(FIRST)
        self.assertIn("is-complete", panel["class"])
        self.assertEqual(len(panel.select(".fr-voice")), len(REREAD["buckets"][FIRST_LABEL]))
        for cid in ("school-escort", "weather-advisory", "unregistered-service"):
            self.assertTrue(panel.select(f'.fr-claim[data-claim="{cid}"]'), cid)
        self.assertEqual(len(panel.select("[data-sunk]")), 4)
        self.assertIsNotNone(panel.select_one("details[data-sunk-group]"))
        self.assertTrue(panel.select('[data-vein="henoko-student-accident-vein-safety"]'))
        self.assertTrue(panel.select('.fr-check[data-check="briefing"]'))

    def test_claim_override_hides_ship_name(self):
        node = self.panel(FIRST).select_one('.fr-claim[data-claim="unregistered-service"]')
        self.assertNotIn("不屈", node.get_text())
        self.assertIn("1隻の船長", node.get_text())
        d = copy.deepcopy(self.d)
        d["cfg"]["claim_finding_overrides"]["unregistered-service"]["public_finding"] = "別の文"
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_official_link_is_one_line(self):
        for panel in self.s.select(".fr-panel.is-complete"):
            self.assertEqual([a["href"] for a in panel.select(".fr-national a")], ["#bg-official"])

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
        js = (ROOT / "scripts/henoko_redesign/reading.js").read_text(encoding="utf-8")
        self.assertIn("ids.find(x => h.startsWith('fr-r-' + x + '-'))", js)
        self.assertIn("window.HenokoReading", js)
        self.assertIn("getElementById('henoko-student-accident-reading')", js)

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
                for word in ("女子", "知華", "殺"):
                    self.assertNotIn(word, x["text"], (p["id"], word))
                for word in AVOID:
                    self.assertNotIn(word, p["summary"] + p["label"], (p["id"], word))

    def test_count_mismatch_stops(self):
        cases = []
        d = copy.deepcopy(self.d)
        d["reread"][FIRST_LABEL]["items"].pop()
        cases.append(d)
        d = copy.deepcopy(self.d)
        d["public"]["issues"][0]["count"] += 1
        cases.append(d)
        d = copy.deepcopy(self.d)
        d["public"]["issues"][1]["stances"][0]["count"] += 1
        d["public"]["issues"][1]["stances"][1]["count"] -= 1
        cases.append(d)
        d = copy.deepcopy(self.d)
        d["public"]["trends"] = []
        cases.append(d)
        d = copy.deepcopy(self.d)
        d["claim_posts"]["school-escort"] = []
        cases.append(d)
        for d in cases:
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
        d = copy.deepcopy(self.d)
        d["cfg"]["issues"][FIRST]["posts"].pop("same_stance_reason")
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_check_dates_come_from_ledger(self):
        node = self.panel(FIRST).select_one('.fr-check[data-check="briefing"]')
        self.assertIn(f'確認日 {self.reading.jp_date(self.d["background"]["checked_on"])}', node.get_text())



class AllIssuesAndBackgroundTests(unittest.TestCase):
    """手順6：残りの論点と背景の開閉行。年表の正本は冒頭の設定。"""

    @classmethod
    def setUpClass(cls):
        from scripts import henoko_reading as reading
        from scripts import henoko_background as background

        cls.reading = reading
        cls.background = background
        cls.tmp = tempfile.TemporaryDirectory()
        cls.html = reading.build(Path(cls.tmp.name) / "a").read_text(encoding="utf-8")
        cls.s = soup_of(cls.html)
        cls.d = reading.load()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def render_bg(self, d):
        return soup_of(self.background.render(d, PUBLIC["updated_on"], self.reading.ordered_issues(d)))

    def test_all_shown_issues_complete(self):
        for issue in self.reading.ordered_issues(self.d):
            panel = self.s.find(id="issue-" + issue["id"])
            self.assertIn("is-complete", panel["class"], issue["id"])
            self.assertEqual(len(panel.select(".fr-voice")), len(REREAD["buckets"][issue["label"]]), issue["id"])
            self.assertEqual(len(panel.select(".fr-post")), 2, issue["id"])

    def test_posts_not_reused_across_issues(self):
        ids = [p["id"] for c in self.d["cfg"]["issues"].values() for p in c.get("posts", {}).get("items", [])]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 12)

    def test_in_page_links_resolve(self):
        for a in self.s.select('a[href^="#"]'):
            href = a["href"]
            if href in ("#", "#planet-block", "#henoko-tide-widget"):
                continue  # 山なみと潮目は手順7で写す
            self.assertIsNotNone(self.s.find(id=href[1:]), href)

    def test_rows_are_closed_details(self):
        rows = self.s.select("#henoko-student-accident-background details.fb-row")
        self.assertGreaterEqual(len(rows), 6)
        for row in rows:
            self.assertFalse(row.has_attr("open"), row["id"])

    def test_timeline_single_source_in_background(self):
        """年表は冒頭の設定が正本。冒頭には出さず、背景の行にだけ出す。背景台帳の年表は読まない。"""
        cfg = self.d["ocfg"]
        self.assertEqual(cfg["timeline"]["placement"], "background")
        self.assertIsNone(self.s.select_one(".hop .hop-timeline"))
        row = self.s.find(id="bg-timeline")
        events = row.select(".hop-event")
        self.assertEqual(len(events), len(cfg["timeline"]["entries"]))
        for e in cfg["timeline"]["entries"]:
            self.assertIn(e["title"], row.get_text())
        for t in self.d["background"]["timeline"]:
            self.assertNotIn(t["text"], self.html)
        # 冒頭の短答の「経緯を年表で見る」は背景の行へ飛ぶ
        hrefs = [a["href"] for a in self.s.select(".hop-answer .hop-more")]
        self.assertIn("#bg-timeline", hrefs)
        self.assertIn("#bg-official", hrefs)

    def test_timeline_in_both_places_stops(self):
        d = copy.deepcopy(self.d)
        d["ocfg"]["timeline"]["placement"] = "opening"
        with self.assertRaises(SystemExit):
            self.background.check(d)
        d = copy.deepcopy(self.d)
        d["ocfg"]["faq"]["placement"] = "opening"
        with self.assertRaises(SystemExit):
            self.background.check(d)

    def test_report_phase_reaches_background(self):
        row = self.s.find(id="bg-official")
        self.assertIn("まだ公表されていません", row.summary.get_text())
        self.assertIn('data-report-phase="unpublished"', str(row))
        d = copy.deepcopy(self.d)
        d["ocfg"]["report"]["published_on"] = "2026-10-12"
        bg = self.render_bg(d)
        self.assertIn("2026年10月12日に公表されました", bg.find(id="bg-official").get_text())
        self.assertIn("確認しているところです", bg.find(id="bg-unverified").get_text())
        d["ocfg"]["report"]["content_checked_on"] = "2026-10-13"
        bg = self.render_bg(d)
        self.assertIn("編集部が内容を確かめました", bg.find(id="bg-official").get_text())
        self.assertNotIn("運輸安全委員会", bg.find(id="bg-unverified").get_text())

    def test_checked_on_drives_time_wording(self):
        d = copy.deepcopy(self.d)
        d["ocfg"]["checked_on"] = "2026-11-20"
        bg = self.render_bg(d)
        text = bg.get_text()
        self.assertIn("2026年11月20日", text)
        self.assertNotIn("10月13日", text)

    def test_unverified_mentions_uncollected_and_next(self):
        text = self.s.find(id="bg-unverified").get_text()
        self.assertIn("10月8日以降の投稿", text)
        self.assertIn("10月22日", text)
        self.assertIn("404", (ROOT / "quality/research/henoko-student-accident-primary-sources.md").read_text(encoding="utf-8"))

    def test_faq_moved_from_opening_without_overlap(self):
        self.assertIsNone(self.s.select_one(".hop-faq"))
        row = self.s.find(id="henoko-faq")
        qs = [dt.get_text() for dt in row.select(".fb-faq dt")]
        self.assertEqual(qs, [i["q"] for i in self.d["ocfg"]["faq"]["items"]])
        self.assertFalse(set(qs) & {a["question"] for a in self.d["ocfg"]["answers"]})
        dump = next(dd for dt, dd in zip(row.select(".fb-faq dt"), row.select(".fb-faq dd")) if "ダンプカー" in dt.get_text())
        self.assertIn("報道", dump.get_text())
        self.assertIsNone(dump.select_one("a"))

    def test_terms_and_official_points_have_sources(self):
        for sel in ("#bg-terms .fb-terms > div", "#bg-official .fb-official > div"):
            items = self.s.select(sel)
            self.assertTrue(items, sel)
            for item in items:
                self.assertTrue(item.select("a[href^='https://']"), item.dt.get_text())

    def test_classroom_is_read_from_shared_config(self):
        cr = json.loads((ROOT / "configs/classroom/henoko-student-accident.json").read_text(encoding="utf-8"))
        text = self.s.find(id="bg-classroom").get_text()
        for q in cr["questions"]:
            self.assertIn(q, text)

    def test_missing_link_target_stops(self):
        d = copy.deepcopy(self.d)
        d["cfg"]["sources_common"]["official_href"] = "#bg-nothing"
        with self.assertRaises(SystemExit):
            self.background.check(d)

    def test_themes_yaml_mismatch_stops(self):
        d = copy.deepcopy(self.d)
        d["bg"]["theme"]["updated_at"] = "2026-01-01"
        with self.assertRaises(SystemExit):
            self.background.check(d)

    def test_victim_care_words_absent_in_background(self):
        text = self.s.find(id="henoko-student-accident-background").get_text()
        for word in AVOID:
            if word == "同志社":
                continue  # 授業向けの共有設定の出典名・国会会議録の題には出ない。下で個別に確かめる
            self.assertNotIn(word, text, word)
        self.assertNotIn("同志社", text)


if __name__ == "__main__":
    unittest.main()
