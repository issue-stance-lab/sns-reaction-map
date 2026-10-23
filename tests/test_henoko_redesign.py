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
import shutil
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
        self.assertIn("10月24日より前の投稿", note)
        self.assertIn("11月7日", note)

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
        # 正本の文から船名を外したので言い換えは要らない。言い換えを置くときは、公開JSONの文が変わると止まる
        self.assertEqual(self.d["cfg"]["claim_finding_overrides"], {})
        d = copy.deepcopy(self.d)
        d["cfg"]["claim_finding_overrides"] = {"unregistered-service": {"finding": "言い換え", "public_finding": "別の文"}}
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
        # 冒頭の確認日（checked_on）だけが動く。背景台帳の確認日（台帳の checked_on、2026-10-13）は台帳から別に出る
        ledger = self.reading.jp_date(self.d["background"]["checked_on"])
        for label in ("背景台帳の確認日 ", "背景台帳の確認 "):
            text = text.replace(label + ledger, "")
        self.assertNotIn("10月13日", text)

    def test_unverified_mentions_uncollected_and_next(self):
        text = self.s.find(id="bg-unverified").get_text()
        self.assertIn("10月24日以降の投稿", text)
        self.assertIn("11月7日", text)
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



# ---------------------------------------------------------------- 手順7：公開候補と更新経路

from scripts import build_henoko_redesign as redesign  # noqa: E402
from scripts import henoko_layout as layout  # noqa: E402

AS_OF = PUBLIC["updated_on"]
INPUTS = (
    "THEMES.yaml",
    "docs/data/themes/henoko-student-accident.json",
    "data/public/themes/henoko-student-accident.json",
    "data/henoko-student-accident_issues-reread.json",
    "data/henoko-student-accident_reread-stances.json",
    "data/henoko-student-accident_claim_posts.json",
    "data/verification/henoko-student-accident-background.json",
)
# 旧ページの JS・CSS の内部用id（外から指す意味の無いもの）
LEGACY_IDS_INTERNAL = ("henoko-reason-count-", "henoko-check-note-", "henoko-source-", "pseg", "pbar", "pnum", "c-", "s-",
                       "vote-related-themes", "henoko-tide-widget-slope-", "seafloor", "seacover", "spin", "dot-slot", "back",
                       "btn-'")
SHOWN = [i for i in PUBLIC["issues"] if int(i["count"]) > 0]


def protected(text: str, name: str) -> str:
    return re.search(f"<!-- {name}_START -->.*?<!-- {name}_END -->", text, re.S).group()


def vote_defs(text: str) -> tuple[str, str, str, str]:
    """投票の topic・保存キーの元の値・論点（var ISSUES=[…]）・立場（var STANCES=[…]）。論点と立場は元HTMLと1文字も変えない。"""
    topic = re.search(r"var TOPIC='([^']+)'", text).group(1)
    issues = re.search(r"var ISSUES=\[(.*?)\];", text, re.S).group(1)
    stances = re.search(r"var STANCES=\[(.*?)\];", text, re.S).group(1)
    return topic, "sns_vote_henoko_issue_arena_v1" if "sns_vote_henoko_issue_arena_v1" in text else "", issues, stances


def visible_text(html: str) -> str:
    soup = soup_of(html)
    for node in soup(["script", "style", "template"]):
        node.decompose()
    return soup.body.get_text()


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
                         "https://sns-reaction-map.jp/henoko-student-accident-reaction-map.html")
        self.assertEqual(self.s.select_one('meta[property="og:image"]')["content"],
                         self.src.select_one('meta[property="og:image"]')["content"])
        self.assertEqual(len(self.s.select("h1")), 1)
        ids = Counter(t["id"] for t in self.s.find_all(id=True))
        self.assertEqual([k for k, v in ids.items() if v > 1], [])  # 同じidを2つ置かない
        # サイト共通の見た目と共通ヘッダーのスクリプトは元HTMLの版のまま
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
        src_topic, src_key, src_issues, src_stances = vote_defs(self.source)
        self.assertEqual(src_key, redesign.VOTE_STORAGE_KEY)
        for text in (self.release, self.preview):
            self.assertIn(f'data-vote-topic="{redesign.VOTE_TOPIC}"', text)
            topic, _key, issues, stances = vote_defs(text)
            self.assertEqual((topic, issues, stances), (src_topic, src_issues, src_stances))  # 論点と立場が元と完全一致
            self.assertIn("choiceIdx:selected*STANCES.length+index", text)
            self.assertIn("var KEY=window.SNS_REDESIGN_PRODUCTION?'sns_vote_henoko_issue_arena_v1':'sns_vote_henoko_issue_arena_v1_preview';", text)
            self.assertNotIn("var KEY='sns_vote_henoko_issue_arena_v1';", text)
        self.assertEqual(len(re.findall(r"\bk:'", src_issues)), 6)  # 論点6×立場3＝18通り
        self.assertEqual(len(re.findall(r"\bk:'", src_stances)), 3)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=location.hostname==='sns-reaction-map.jp'", self.release)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=false", self.preview)
        scripts = self.s.select("script")
        config = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-config.js"))
        client = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-store.js"))
        self.assertEqual(config + 2, client)
        # 投票の前置きの文も元HTMLのまま。論点ボタンの絵文字は定義を変えずに表示だけ隠す
        self.assertEqual(self.s.select_one("#vote-section > p").get_text(), self.src.select_one("#vote-section > p").get_text())
        self.assertIn(".vote-issue-icon{display:none}", self.release)

    def test_adapter_vote_fingerprint_matches_source(self):
        from scripts.refresh_adapters.henoko import vote_fingerprint
        self.assertEqual(vote_fingerprint(self.source), vote_fingerprint(self.release))
        self.assertEqual(vote_fingerprint(self.release)[3], 18)

    def test_faq_json_ld_matches_visible_faq(self):
        payloads = [json.loads(x.get_text()) for x in self.s.select('script[type="application/ld+json"]')]
        faq = [p for p in payloads if p.get("@type") == "FAQPage"]
        self.assertEqual(len(faq), 1)
        visible = redesign.faq_items(self.s)
        self.assertEqual(len(visible), 7)  # 冒頭の短答3問＋背景の「よくある質問」4問
        self.assertEqual([q for q, _a in visible[:3]], ["何があった？", "原因は分かった？", "何が争点？"])
        self.assertEqual([(q["name"], q["acceptedAnswer"]["text"]) for q in faq[0]["mainEntity"]], visible)
        texts = re.sub(r"\s+", " ", self.s.get_text())
        for q, a in visible:
            self.assertIn(q, texts)
            self.assertIn(a, texts)
            self.assertNotIn("（PDF）", a)  # 出典リンクの名前は答えに入れない
        self.assertEqual(sum(1 for p in payloads if p.get("@type") == "Article"), 1)
        # 元HTMLのFAQの構造化データ（旧ページのFAQ6問。冒頭に学校名を含む答えがあった）は使わない
        self.assertNotEqual(protected(self.source, "FAQ_JSON_LD"), protected(self.release, "FAQ_JSON_LD"))
        # 旧ページの検索入口・連動表示・テーマ共通の見た目・アリーナの点は読み込まない
        for name in ("henoko-connected.js", "henoko-connected-page.js", "henoko-connected.css", "henoko-search-entry.js",
                     "henoko-search-entry.css", "theme-design.js", "theme-design.css", "henoko-arena-data.js", "manga-viewer.js"):
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

    def test_detail_data_uses_four_stances_and_keeps_notes(self):
        """詳細データの表は公開JSONの4立場・分類名で作り直す（元HTMLの「判断を保留・切り分ける448」は使わない）。注意は元のまま。"""
        detail = self.s.select_one("#detail-data")
        text = detail.get_text()
        self.assertNotIn("448", text)
        planet = {s["label"] for i in PUBLIC["issues"] for s in i["stances"]}
        for label in planet:
            self.assertIn(label, text)
        for issue in SHOWN:
            self.assertIn(issue["label"], text)
        rows = {r.th.get_text(): [int(td.get_text().replace(",", "")) for td in r.select("td")]
                for r in detail.select("table")[2].select("tbody tr")}
        for issue in SHOWN:
            self.assertEqual(sum(rows[issue["label"]][:-1]), int(issue["count"]))
        self.assertEqual(rows["合計"][-1], int(PUBLIC["opinion_count"]))
        src_notes = [d for d in self.src.select("#detail-data > details") if d.summary.get_text() == "注意"]
        self.assertEqual(len(src_notes), 1)
        new_notes = [d for d in detail.select(":scope > details") if d.summary.get_text() == "注意"]
        self.assertEqual([str(d) for d in new_notes], [str(d) for d in src_notes])  # 注意は元HTMLのまま
        self.assertEqual(detail.select("details[open]"), [])

    def test_tide_card_is_inherited_verbatim_inside_fold(self):
        block = re.search(r'<section class="update-dashboard"[^>]*><!-- TIDE_CARD_START -->.*?<!-- TIDE_CARD_END --></section>',
                          self.source, re.S).group()
        self.assertEqual(self.release.count(block), 1)
        self.assertIn("/* TIDE_CARD_START */", self.release)
        fold = self.s.select_one("#cap-trend-more")
        self.assertEqual(fold.name, "details")
        self.assertFalse(fold.has_attr("open"))
        self.assertIsNotNone(fold.select_one("#henoko-tide-widget"))
        glance = self.s.select_one("#cap-trend .cap-trend-glance")
        data = json.loads(re.search(r"const datasets = (\{.*?\});\n", self.release, re.S).group(1))
        self.assertEqual(len(glance.select(".cap-trend-spark svg polyline")), len(data["stance"]["rows"]))
        # 比べる意見がごく少ないので、要約の1文はカードの見出しではなく、何を比べているかの説明
        self.assertIn(self.d_compact()["trend_lead"], glance.select_one(".cap-trend-lead").get_text())
        self.assertIn(self.s.select_one(".tide-widget-period").get_text(), glance.select_one(".cap-trend-lead").get_text())
        self.assertNotIn("件", glance.select_one(".cap-trend-lead").get_text())
        self.assertLess(self.release.index("TIDE_CARD_START -->"), self.release.index('id="vote-section"'))

    def d_compact(self) -> dict:
        return json.loads((ROOT / "configs/henoko-student-accident-reading.json").read_text(encoding="utf-8"))["compact"]

    def test_issue_glance_from_tide(self):
        data = json.loads(re.search(r"const datasets = (\{.*?\});\n", self.release, re.S).group(1))
        rows = {r["label"]: r for r in data["issue"]["rows"]}
        for issue in SHOWN:
            box = self.s.find(id="issue-" + issue["id"]).select_one(".fr-glance")
            link = box.select_one(".fr-glance-link")
            # 設定の飛び先（trend.widget_id）が、引き継いだ潮目のカードの実際の id とつながっている
            self.assertEqual((link["href"], link["data-tide-mode"]), ("#henoko-tide-widget", "issue"))
            self.assertIsNotNone(self.s.find(id=link["href"][1:]))
            cap = box.select_one(".fr-glance-cap")
            if issue["label"] not in rows:
                # 潮目の論点に無い論点は、比較の対象に入っていないことだけを書く（数字・折れ線は出さない）
                self.assertIn("fr-glance-missing", cap["class"], issue["id"])
                self.assertIsNone(box.select_one(".fr-glance-chart svg"))
                continue
            self.assertIn(f'{rows[issue["label"]]["previous"]:.1f}%', cap.get_text())
            self.assertIn(f'{rows[issue["label"]]["current"]:.1f}%', cap.get_text())
            self.assertNotIn("件", box.select_one(".fr-glance-chart").get_text())
        self.assertEqual({i["label"] for i in SHOWN} - set(rows), {"政治利用・基地問題"})

    def test_method_fold_holds_trust_and_detail_data(self):
        method = self.s.select_one("#cap-method")
        self.assertEqual(method.name, "details")
        self.assertFalse(method.has_attr("open"))
        self.assertIsNotNone(method.select_one("#detail-data"))
        trust = protected(self.source, "ARTICLE_TRUST")
        self.assertLess(self.release.index('id="cap-method"'), self.release.index(trust))
        self.assertLess(self.release.index(trust), self.release.index('id="related-topics"'))

    def test_folds_start_closed(self):
        for sel in ("#henoko-student-accident-reading", "#henoko-student-accident-background", "#henoko-open",
                    "#cap-trend", "#cap-method"):
            self.assertEqual([d.get("class") for d in self.s.select(sel + " details[open]")], [], sel)
        self.assertFalse(self.s.select_one("#cap-method").has_attr("open"))
        self.assertEqual(len(self.s.select("#henoko-student-accident-background details.fb-row")), 7)

    def test_other_issue_hidden_while_zero(self):
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

    def test_victim_care_words_absent_in_page(self):
        """配慮に反する語（AVOID）が、新ページに見えている文字（本文・ボタン・山なみが描く文字の元）に無い。
        例外は保護対象として文字どおり引き継いだ部分だけ：SEOメタ・Article JSON-LD（学校名。オーナー判断待ち）、
        投票の定義（論点の絵文字と説明。表示は CSS で隠し、説明は投票後に出る。元HTMLと完全一致が条件）、PLANET_DATA（公開データの契約。
        理由区分の名前は山なみの選択パネルで表示しない）。"""
        text = visible_text(self.release)
        for word in AVOID:
            self.assertNotIn(word, text, word)
        stripped = self.release
        for name in ("SEO_META", "ARTICLE_JSON_LD"):
            stripped = stripped.replace(protected(self.source, name), "")
        vote = next(s.string for s in self.src.select("script:not([src])") if s.string and "var TOPIC=" in s.string)
        stripped = stripped.replace(self.s.select_one("#planet-data").string, "")
        stripped = stripped.replace(re.search(r"var ISSUES=\[.*?\];", vote, re.S).group(), "")
        for word in AVOID:
            self.assertNotIn(word, stripped, word)
        # 山なみの論点の絵文字は、PLANET_DATA を変えずに描く前に空にする。JSなしの論点一覧からも外す
        self.assertIn(redesign.NO_ICONS, self.release)
        self.assertLess(self.release.index('id="planet-data"'), self.release.index(redesign.NO_ICONS))
        for label in self.s.select("#fallback-nav .label"):
            self.assertNotRegex(label.get_text(), r"^[^\w（「]")

    def test_old_anchor_targets_exist(self):
        for target in set(redesign.ALIASES.values()):
            self.assertIsNotNone(self.s.find(id=target), target)
        hidden = ("progress", "fallback", "fallback-nav", "quiz")
        for alias in redesign.ALIASES:
            if alias in hidden:
                continue
            self.assertIsNone(self.s.find(id=alias), alias)
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
                     "henoko-tide-widget", "bg-classroom", "article-trust-title", "henoko-faq", "hop-count"):
            self.assertIsNotNone(self.s.find(id=kept), kept)
        # サイト内から旧アンカー付きで指すリンク（docs・scripts・configs・company）の飛び先も新ページにある
        targets = set()
        for base in ("docs", "scripts", "configs", "company"):
            for path in (ROOT / base).rglob("*"):
                if path.suffix not in (".html", ".py", ".json", ".js", ".md", ".txt", ".xml", ".yaml") or path.name == redesign.PAGE:
                    continue
                targets |= set(re.findall(r"henoko-student-accident-reaction-map\.html#([A-Za-z0-9_-]+)",
                                          path.read_text(encoding="utf-8", errors="ignore")))
        self.assertIn("correction-20260906", targets)
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
        self.assertEqual(self.release.count("window.PLANET_DATA="), 1)  # PLANET_DATA は1つだけ
        planet = self.s.select_one("#henoko-student-accident-reading .fr-map section.planet-panel #planet-block")
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
        self.assertEqual(self.s.select("template[id^='henoko-student-accident-reading-']"), [])
        self.assertLess(self.release.index(src_script[:200]), self.release.index("window.HenokoReading"))
        self.assertLess(self.release.index("window.HenokoReading"), self.release.index("function goReading"))

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
        # 自動着地の処理・投票の保存キーが変わったら、黙って写さずに止まる
        for old, new, message in (
                (redesign.AUTO_LAND, redesign.AUTO_LAND.replace("landSilently(idIndex[top.id]);", "land(idIndex[top.id]);"), "自動着地"),
                ("var KEY='sns_vote_henoko_issue_arena_v1';", "var KEY='sns_vote_henoko_issue_arena_v2';", "保存キー")):
            moved = self.source.replace(old, new, 1)
            self.assertNotEqual(moved, self.source)
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "source.html"
                path.write_text(moved, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    redesign.build(path, Path(temp) / "out", "release", as_of=AS_OF)

    def test_no_legacy_widgets(self):
        for marker in ("HENOKO_SEARCH_ENTRY_START", "THEME_DESIGN_START", "HENOKO_CONNECTED_START",
                       "HENOKO_CONNECTED_CONTENT_START", "STANCE_GLANCE_START", "HENOKO_SEARCH_OPINIONS_END"):
            self.assertNotIn("<!-- " + marker, self.release)
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.release)
        self.assertNotIn("HENOKO_ARENA_DATA", self.release)
        self.assertEqual(self.s.select("#bukatsu-background, #bukatsu-check, #stance-glance, #henoko-entry"), [])
        for embed in self.s.select(".x-embed"):
            self.assertRegex(embed.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")

    def test_report_publication_switches_wording(self):
        """運輸安全委員会の報告書の公表日（冒頭の設定 report.published_on）を仮に入れると、冒頭の短答・背景・構造化データの文が
        切り替わり、生成は止まらない（docs には入れない。隔離した root で作る）。"""
        with tempfile.TemporaryDirectory() as temp:
            root = LayoutTests._root(LayoutTests(), temp)
            path = root / "configs/henoko-student-accident-opening.json"
            cfg = json.loads(path.read_text(encoding="utf-8"))
            cfg["report"]["published_on"] = "2026-10-12"
            path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
            redesign.build(root / layout.PAGE, root / "out", "release", root=root, as_of=AS_OF)
            page = (root / "out" / redesign.PAGE).read_text(encoding="utf-8")
        s = soup_of(page)
        self.assertIn("2026年10月12日に公表されました", s.select("article.hop-answer")[1].get_text())
        self.assertIn("確認しているところです", s.find(id="bg-official").get_text())
        self.assertNotIn("まだ公表されていません", visible_text(page))
        faq = [p for p in (json.loads(x.get_text()) for x in s.select('script[type="application/ld+json"]')) if p.get("@type") == "FAQPage"][0]
        self.assertIn("2026年10月12日に公表されました", faq["mainEntity"][1]["acceptedAnswer"]["text"])
        self.assertIn("まだ公表されていません", visible_text(self.release))

    def test_provenance_counts_and_detects_mismatch(self):
        from scripts.henoko_count_provenance import verified_selectors
        result = verified_selectors(self.release, ROOT)
        self.assertEqual(len(result), len(SHOWN) + 2)  # 論点の欄6つ＋冒頭の件数欄＋短答
        node = self.s.select_one(f"#issue-{FIRST} li.fr-reason .fr-reason-n b")
        broken = self.release.replace(str(node), str(node).replace(node.get_text(), str(int(node.get_text().replace(",", "")) + 1)), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)
        line = self.s.select_one(f"#issue-{FIRST} article.fr-reason-detail .fr-reason-stance")
        n = re.search(r"論点を切り分ける(\d[\d,]*)件", line.get_text()).group(1)
        broken = self.release.replace(str(line), str(line).replace(f"論点を切り分ける{n}件", f"論点を切り分ける{int(n.replace(',', '')) + 1}件"), 1)
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
        shutil.copytree(ROOT / "scripts/henoko_redesign", root / "scripts/henoko_redesign")
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
            (root / layout.PAGE).write_text('<meta name="henoko-layout">')
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
            self.assertIn(b'name="henoko-layout"', first)
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
            path = root / "data/henoko-student-accident_issues-reread.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            gone = next(i for i in raw["items"] if i["main_issue"] == FIRST_LABEL)
            raw["items"].remove(gone)
            raw["buckets"][FIRST_LABEL][gone["bucket"]]["count"] -= 1
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            before = (root / layout.PAGE).read_bytes()
            with self.assertRaisesRegex(ValueError, "照合で停止"):
                layout.finish(root, as_of=AS_OF)
            self.assertEqual(before, (root / layout.PAGE).read_bytes())
            self.assertFalse((root / layout.SOURCE).exists())

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では、元HTMLの旧形式の生成（legacy_refresh）を動かせない")
    def test_rebuild_runs_planet_guard_on_source(self):
        """公開後の単独実行（build_henoko_arena.py → rebuild）でも、元HTMLに旧形式の生成を掛ける途中で
        山なみの入力の版の守り（henoko_planet_guard.verify_inputs）が働く。守りが止めたら何も書かない。"""
        from unittest import mock
        import scripts.henoko_planet_guard as guard
        calls = []
        real = guard.verify_inputs

        def spy(*args, **kwargs):
            calls.append(1)
            return real(*args, **kwargs)

        with tempfile.TemporaryDirectory() as temp:
            html = layout.source_for_refresh(ROOT).read_text(encoding="utf-8")
            with mock.patch.object(guard, "verify_inputs", spy):
                out = layout.legacy_refresh(ROOT, html, Path(temp) / "arena.js")
            self.assertTrue(calls)
            self.assertEqual(out.count("<!-- PLANET_SECTION_START -->"), 1)
            self.assertNotIn('name="henoko-layout"', out)

            def stop(*_args, **_kwargs):
                raise guard._modules()[0].IssueCountError("守りが止めた")

            with mock.patch.object(guard, "verify_inputs", stop):
                with self.assertRaisesRegex(Exception, "守りが止めた"):
                    layout.legacy_refresh(ROOT, html, Path(temp) / "arena2.js")
            self.assertFalse((Path(temp) / "arena2.js").exists())

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では、更新経路の立場の対応表を作れない")
    def test_adapter_rebuilds_stance_table_and_stops_without_reread(self):
        """更新経路（refresh_adapters/henoko.py）は、累積候補から立場の対応表を作り直す（あだ名禁止・自転車と同じ）。
        新しい意見が再読データの明細に無ければ、何を直すかが分かる形で止まる。"""
        from scripts.refresh_adapters.henoko import build_reread_stances
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("THEMES.yaml", "data/henoko-student-accident_issues-reread.json"):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, root / name)
            candidate = root / "cumulative-candidate.json"
            shutil.copy2(CANON, candidate)
            data = build_reread_stances(root, candidate, root / "stances.json", "2026-10-22")
            self.assertEqual(data["stances"], STANCES["stances"])
            self.assertEqual((data["made_on"], data["public_mismatch"]), ("2026-10-22", 0))
            path = root / "data/henoko-student-accident_issues-reread.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw["items"].pop(0)
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "追い読み"):
                build_reread_stances(root, candidate, root / "stances.json", "2026-10-22")

    def test_refresh_path_is_wired(self):
        refresh = (ROOT / "scripts/refresh_topic.py").read_text(encoding="utf-8")
        self.assertEqual(refresh.count("finish_henoko_layout(candidate_root)"), 2)
        self.assertEqual(refresh.count("materialize_henoko(candidate_root)"), 1)
        self.assertIn("henoko_layout_enabled(root)", refresh)
        adapter = (ROOT / "scripts/refresh_adapters/henoko.py").read_text(encoding="utf-8")
        self.assertIn("current_page = source_for_refresh(root)", adapter)
        self.assertIn("build_reread_stances(root, candidate,", adapter)
        self.assertIn("REREAD_STANCES: first_stances", adapter)
        self.assertIn("materialize_henoko(target)", (ROOT / "scripts/verify_builder_rebuildability.py").read_text(encoding="utf-8"))
        self.assertIn("henoko_redesign_provenance", (ROOT / "scripts/henoko_count_provenance.py").read_text(encoding="utf-8"))
        for path in ("scripts/apply_theme_design.py", "scripts/seo/apply_classroom_section.py", "scripts/seo/apply_theme_trust.py",
                     "scripts/refresh_planet_section.py", "scripts/verify_theme_page.py", "scripts/build_henoko_arena.py",
                     "scripts/henoko_count_provenance.py"):
            self.assertIn("henoko-layout", (ROOT / path).read_text(encoding="utf-8"), path)


if __name__ == "__main__":
    unittest.main()
