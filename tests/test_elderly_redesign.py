"""高齢者免許返納・新デザインの試作（冒頭、論点ごとの読書面、背景の開閉行）。docs/ は書き換えない。

自転車の青切符（tests/test_bike_redesign.py）の手順5・6に当たる検査。読書面は最初から部活動型の圧縮済みの型で作る。
読書面の生成は公開できる入力（公開JSON・再読データ・設定・一次資料メモ）だけを読む。非公開の正典が要るのは、
再読データの立場と代表投稿の選定基準を確かめる検査（正典が無い環境ではスキップ）だけ。
"""
from __future__ import annotations

import copy
import json
import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup

from scripts import elderly_opening as opening

ROOT = opening.ROOT
PUBLIC = json.loads((ROOT / "docs/data/themes/elderly-license-revocation.json").read_text(encoding="utf-8"))
CANON = ROOT / "social-samples/elderly-license_2d_classified.json"
REREAD = json.loads((ROOT / "data/elderly-license_issues-reread.json").read_text(encoding="utf-8"))
OPENING_CONFIG = ROOT / "configs/elderly-license-revocation-opening.json"
OTHER = "elderly-license-revocation-other"
FIRST = "elderly-license-revocation-safety"
WITH_REASONS = {"義務化・事故防止", "地方の足・移動権"}


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class OpeningTests(unittest.TestCase):
    """冒頭：確認日は設定の1か所から。正本の見た目は scripts/elderly_redesign/。"""

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
        self.assertIn(f"年齢の節目と返納の手続きは、{when}に条文と警察庁の案内で確かめました。", frag)
        self.assertIn(f'data-checked-on="{self.config["checked_on"]}"', frag)
        self.assertNotIn("dates", self.config)
        cfg = copy.deepcopy(self.config)
        cfg["checked_on"] = "2026-12-01"
        self.assertIn("2026年12月1日に条文と警察庁の案内で確かめました", self.frag(cfg))

    def test_old_dates_or_stale_checked_on_stop(self):
        cfg = copy.deepcopy(self.config)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "opening.json"
            cfg["dates"] = {"memo_checked_from": "2026-08-30"}
            path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(SystemExit):
                opening.load_inputs(path)
            del cfg["dates"]
            cfg["checked_on"] = "2026-09-01"  # 主張の照合日（2026-09-30）より古い
            path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(SystemExit):
                opening.load_inputs(path)

    def test_statistics_match_r07(self):
        """自主返納と運転経歴証明書の件数は運転免許統計 令和7年版（2026-10-12 時点で最新）。"""
        st = self.config["steps"]["stat"]
        self.assertEqual((st["returned"], st["cards"]), (435067, 297359))
        self.assertTrue(st["source"]["url"].endswith("/r07main.pdf"))

    def test_opening_assets_live_in_redesign_folder(self):
        src = (opening.ASSETS / "opening.css").read_text(encoding="utf-8")
        for proto in ("elderly-license-revocation-opening", "elderly-license-revocation-reading"):
            self.assertEqual((ROOT / "quality/prototypes" / proto / "opening.css").read_text(encoding="utf-8"), src, proto)


class ReadingPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts import elderly_reading as reading

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
        for name in ("reading.css", "reading.js"):
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
        self.assertEqual(self.s.select(".fr-mountains, .fr-hill, .fr-chip, #planet-block"), [])
        first = self.s.select_one("#elderly-license-revocation-reading .fr-panels > *")
        self.assertEqual(first.name, "nav")
        self.assertIn("fr-tabs", first["class"])

    def test_headings_avoid_mandate_word(self):
        """冒頭の方針どおり、見出し（読書面の題・論点名・タブ）に「義務化」を出さない。分類名・立場名はラベルのまま。"""
        for node in self.s.select("#elderly-license-revocation-reading h2, #elderly-license-revocation-reading h3, .fr-tab"):
            self.assertNotIn("義務化", node.get_text(), node.get_text())
        d = copy.deepcopy(self.d)
        d["cfg"]["issues"][FIRST]["name"] = "義務化と事故防止"
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_issue_order_count_desc_other_last(self):
        tabs = [a["data-issue-id"] for a in self.s.select(".fr-tab")]
        named = sorted((i for i in PUBLIC["issues"] if i["id"] != OTHER), key=lambda i: (-int(i["count"]), i["id"]))
        self.assertEqual(tabs, [i["id"] for i in named] + [OTHER])
        self.assertIn("is-other", self.s.select_one(f'.fr-tab[data-issue-id="{OTHER}"]')["class"])

    def test_stance_order_follows_planet_like_opening(self):
        planet = [s["id"] for s in self.d["planet"]["stances"]]
        self.assertEqual([s["id"] for s in self.reading.stance_order(self.d)], planet)
        self.assertEqual(len(planet), 4)

    def test_counts_and_stances_match_public_json(self):
        order = [s["id"] for s in self.reading.stance_order(self.d)]
        for issue in PUBLIC["issues"]:
            panel = self.panel(issue["id"])
            self.assertIsNotNone(panel, issue["id"])
            self.assertEqual(panel.select_one(".fr-count b").get_text(), f'{int(issue["count"]):,}')
            by = {s["id"]: int(s["count"]) for s in issue["stances"]}
            for sel in (".fr-stance-mini b", ".fr-stance .fr-stance-list b"):
                self.assertEqual([b.get_text() for b in panel.select(sel)], [f"{by[sid]:,}" for sid in order], sel)
        self.assertEqual(sum(int(i["count"]) for i in PUBLIC["issues"]), int(PUBLIC["opinion_count"]))

    def test_stance_band_keeps_not_a_poll_note(self):
        for issue in PUBLIC["issues"]:
            note = self.panel(issue["id"]).select_one(".fr-head-stance .fr-caveat")
            self.assertIn("世論調査の結果ではありません", note.get_text())

    def test_reasons_recounted_from_reread_details(self):
        self.assertEqual(set(self.d["reread"]), WITH_REASONS)
        for issue in PUBLIC["issues"]:
            panel = self.panel(issue["id"])
            items = [i for i in REREAD["items"] if i["main_issue"] == issue["label"]]
            if issue["label"] not in WITH_REASONS:
                self.assertEqual(items, [])
                self.assertIsNotNone(panel.select_one("[data-unpublished]"), issue["label"])
                self.assertEqual(panel.select(".fr-reason"), [])
                continue
            self.assertEqual(len(items), int(issue["count"]), issue["label"])
            self.assertIsNone(panel.select_one("[data-unpublished]"))
            for bid in REREAD["buckets"][issue["label"]]:
                node = panel.select_one(f'li.fr-reason[data-reason="{bid}"] .fr-reason-n b')
                n = sum(1 for it in items if it["bucket"] == bid)
                self.assertEqual(node.get_text(), f"{n:,}", (issue["label"], bid))

    def test_unpublished_disappears_when_reread_grows(self):
        """再読データに論点が加われば「理由は未公開」は自動で消え、理由一覧に変わる。"""
        d = copy.deepcopy(self.d)
        issue = next(i for i in d["public"]["issues"] if i["id"] == "elderly-license-revocation-other")
        n = int(issue["count"])
        d["reread"]["その他"] = {"buckets": {"X": {"label": "仮の区分", "count": n}},
                                  "items": [{"tweet_id": str(k), "bucket": "X", "main_issue": "その他", "stance": None} for k in range(n)]}
        by = {s["id"]: int(s["count"]) for s in issue["stances"]}
        labels = {s["id"]: s["key"] for s in d["planet"]["stances"]}
        stances = [labels[sid] for sid, c in by.items() for _ in range(c)]
        for it, st in zip(d["reread"]["その他"]["items"], stances):
            it["stance"] = st
        html = self.reading.render_reasons(d, issue, {})
        self.assertNotIn("data-unpublished", html)
        self.assertIn("仮の区分", html)

    def test_reason_stances_sum_to_public(self):
        for label, rr in self.d["reread"].items():
            issue = next(i for i in PUBLIC["issues"] if i["label"] == label)
            total = Counter(self.reading.item_stance(self.d, it) for it in rr["items"])
            self.assertEqual({s["id"]: total.get(s["id"], 0) for s in issue["stances"]},
                             {s["id"]: int(s["count"]) for s in issue["stances"]}, label)

    def test_does_not_read_private_canonical(self):
        self.assertNotIn("social-samples", (ROOT / "scripts/elderly_reading.py").read_text(encoding="utf-8"))
        self.assertNotIn("social-samples", json.dumps(self.d["cfg"]["issues"], ensure_ascii=False))

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では再読データの立場を確かめられない")
    def test_reread_stance_and_opinions_match_canonical(self):
        """正典の classification.is_opinion=true が公開JSONの意見（455件・論点・立場）に当たる。再読データの立場も正典どおり。"""
        canon = json.loads(CANON.read_text(encoding="utf-8"))
        ops = [x for x in canon if x["classification"].get("is_opinion")]
        self.assertEqual(len(ops), int(PUBLIC["opinion_count"]))
        self.assertEqual(len(canon), int(PUBLIC["collected_count"]))
        cell = Counter((x["classification"]["main_issue"], x["classification"]["stance"]) for x in ops)
        key = {s["id"]: s["key"] for s in self.d["planet"]["stances"]}
        for issue in PUBLIC["issues"]:
            for s in issue["stances"]:
                self.assertEqual(cell[(issue["label"], key[s["id"]])], int(s["count"]), (issue["label"], s["id"]))
        by = {str(x["tweet_id"]): x["classification"] for x in canon}
        for it in REREAD["items"]:
            c = by[str(it["tweet_id"])]
            self.assertTrue(c["is_opinion"])
            self.assertEqual((c["main_issue"], c["stance"]), (it["main_issue"], it["stance"]), it["tweet_id"])

    def test_stale_reread_stance_would_stop(self):
        d = copy.deepcopy(self.d)
        item = d["reread"]["義務化・事故防止"]["items"][0]
        item["stance"] = next(s["key"] for s in d["planet"]["stances"] if s["key"] != item["stance"])
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_safety_panel_is_complete(self):
        panel = self.panel(FIRST)
        self.assertIn("is-complete", panel["class"])
        self.assertEqual(len(panel.select(".fr-voice")), len(self.d["reread"]["義務化・事故防止"]["buckets"]))
        self.assertTrue(panel.select('.fr-claim[data-claim="increase"]'))
        self.assertTrue(panel.select('[data-sunk="elderly-license-revocation-sc-1"]'))
        self.assertTrue(panel.select('.fr-check[data-check="age-rule"]'))
        self.assertIn("第101条の4", panel.select_one('.fr-check[data-check="age-rule"]').get_text())
        for a in panel.select(".fr-see a"):
            self.assertIsNotNone(self.s.find(id=a["href"][1:]), a["href"])

    def test_compact_structure(self):
        """説明は1段落＋「くわしく」、理由は上位4件＋折りたたみ、説明は1位だけ data-on、照合・投稿・立場は閉じた折りたたみ。"""
        top = self.d["cfg"]["compact"]["top_reasons"]
        for issue in PUBLIC["issues"]:
            panel = self.panel(issue["id"])
            self.assertEqual(panel.select("details[open]"), [], issue["id"])
            rr = self.d["reread"].get(issue["label"])
            if rr:
                n_buckets = len(rr["buckets"])
                first = panel.select_one(".fr-reasons > .fr-reason-list")
                self.assertEqual(len(first.select(".fr-reason")), min(top, n_buckets))
                if n_buckets > top:
                    self.assertIn(f"残り{n_buckets - top}つ", panel.select_one(".fr-reason-more").summary.get_text())
            if "is-complete" in panel["class"]:
                descs = panel.select(".fr-panel-head > div > .fr-desc")
                self.assertEqual(len(descs), 1)
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
        js = (ROOT / "scripts/elderly_redesign/reading.js").read_text(encoding="utf-8")
        self.assertIn("ids.find(x => h.startsWith('fr-r-' + x + '-'))", js)
        self.assertIn("window.ElderlyReading", js)

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
                if p.get("stance_id"):
                    self.assertEqual(stance_of[p["stance_id"]], c["stance"], p["id"])

    def test_count_mismatch_stops(self):
        d = copy.deepcopy(self.d)
        d["reread"]["義務化・事故防止"]["items"].pop()
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
        d["claim_posts"]["increase"] = d["claim_posts"]["increase"][:-1]
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
        posts[0]["id"] = "1"  # 再読データに無い投稿
        posts[0]["url"] = posts[0]["url"].rsplit("/", 1)[0] + "/1"
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        posts = d["cfg"]["issues"][FIRST]["posts"]["items"]
        posts[1] = copy.deepcopy(posts[0])
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_memo_check_dates_come_from_memo(self):
        node = self.panel(FIRST).select_one('.fr-check[data-check="age-rule"]')
        when = self.d["memo"].checked_on("資料S")
        self.assertIn(f"確認日 {self.reading.jp_date(when)}", node.get_text())
        d = copy.deepcopy(self.d)
        d["cfg"]["issues"][FIRST]["memo_checks"][0]["memo_section"] = "存在しない見出し"
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_sunk_notes_split_rechecks(self):
        """公開JSONの sns_note の再確認の履歴は、表示だけ本文と分けて並べる（中身は残す）。"""
        for sc in PUBLIC["ocean_layer"]["sunk_continents"]:
            iid = self.reading.sunk_issue(self.d, sc)
            node = self.panel(iid).select_one(f'[data-sunk="{sc["id"]}"]')
            if node is None:
                continue
            n = len(self.reading.RECHECK.findall(sc["sns_note"]))
            self.assertEqual(len(node.select(".fr-rechecks li")), n, sc["id"])


class AllIssuesAndBackgroundTests(unittest.TestCase):
    """手順6：残りの論点と背景の開閉行。"""

    @classmethod
    def setUpClass(cls):
        from scripts import elderly_background as background
        from scripts import elderly_reading as reading

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

    def test_all_issues_complete_with_posts(self):
        labels = {i["id"]: i["label"] for i in PUBLIC["issues"]}
        for iid, icfg in self.d["cfg"]["issues"].items():
            self.assertEqual(icfg["status"], "complete", iid)
            self.assertEqual(len(icfg["description"]), 2, iid)
            rr = self.d["reread"].get(labels[iid])
            self.assertEqual(set(icfg.get("reasons", {})), set(rr["buckets"]) if rr else set(), iid)
            self.assertEqual(len(icfg["posts"]["items"]), 2, iid)
            self.assertTrue(icfg["posts"]["selection_basis"], iid)
        self.assertEqual(self.s.select(".fr-panel.is-pending"), [])

    def test_unpublished_only_where_reread_is_missing(self):
        marked = {p["data-issue-panel"] for p in self.s.select(".fr-panel") if p.select_one("[data-unpublished]")}
        labels = {i["id"]: i["label"] for i in PUBLIC["issues"]}
        self.assertEqual(marked, {iid for iid, lab in labels.items() if lab not in WITH_REASONS})
        self.assertEqual(len(marked), 4)

    def test_see_also_and_issue_links_exist(self):
        for a in self.s.select(".fr-see a, .fb-issues a, .fb-to-issue"):
            self.assertIsNotNone(self.s.find(id=a["href"][1:]), a["href"])

    def test_rows_are_closed_details(self):
        rows = self.s.select("#elderly-license-revocation-background details.fb-row")
        self.assertEqual([r["id"] for r in rows],
                         ["bg-renewal", "bg-options", "bg-family", "bg-why", "bg-stats", "bg-timeline", "bg-faq", "bg-classroom", "bg-unverified"])
        self.assertTrue(all(not r.has_attr("open") for r in rows))
        for r in rows:
            self.assertNotIn("義務化", r.select_one(".fb-title").get_text())

    def test_checked_on_drives_time_wording(self):
        """期限付きの制度イベントは無い。「◯月◯日時点」は冒頭の設定 checked_on 1か所から作る。"""
        when = opening.jp_date(self.d["ocfg"]["checked_on"])
        self.assertIn(f"{when}時点で、運転技能検査の見直しは府令案の段階", self.s.select_one("#bg-timeline").get_text())
        self.assertIn(f"{when}時点で、警察庁は2025年までの件数しか", self.s.select_one("#bg-unverified").get_text())
        self.assertIn(f"{when}時点で最新の令和7年版", self.s.select_one("#bg-stats").get_text())
        d = copy.deepcopy(self.d)
        d["ocfg"]["checked_on"] = "2026-12-01"
        self.assertIn("2026年12月1日時点で", self.render_bg(d))
        d["ocfg"]["checked_on"] = "2026-09-01"  # 背景台帳の確認日より古い
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_system_rows_cover_required_topics(self):
        text = self.s.select_one("#bg-renewal").get_text() + self.s.select_one("#bg-options").get_text()
        for word in ("高齢者講習", "認知機能検査", "運転技能検査", "第101条の4第1項", "同第2項", "運転経歴証明書",
                     "本人確認書類", "サポートカー", "第91条の2", "＃8080", "第104条の4"):
            self.assertIn(word, text)

    def test_stats_latest_row_matches_opening(self):
        text = self.s.select_one("#bg-stats").get_text()
        self.assertIn("435,067", text)
        self.assertIn("297,359", text)
        d = copy.deepcopy(self.d)
        self.row(d, "stats")["rows"][-1]["returned"] = 1
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_timeline_adds_events_after_ledger(self):
        node = self.s.select_one("#bg-timeline")
        added = [li["data-event"] for li in node.select("li[data-added]")]
        self.assertEqual(added, ["report202609", "rule2027"])
        self.assertNotIn("8月を目途", node.get_text())
        self.assertIn("2027年6月1日", node.get_text())
        d = copy.deepcopy(self.d)
        del self.row(d, "timeline")["extra"][0]["before_ledger_reason"]
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_faq_does_not_repeat_opening(self):
        qs = [dt.get_text() for dt in self.s.select("#bg-faq dt")]
        self.assertEqual(len(qs), 3)
        oc = json.loads(OPENING_CONFIG.read_text(encoding="utf-8"))
        opening_qs = [i["q"] for i in oc["faq"]["items"]] + [a["question"] for a in oc["answers"]]
        self.assertFalse(set(qs) & set(opening_qs))

    def test_classroom_is_read_from_shared_config(self):
        cr = json.loads((ROOT / "configs/classroom/elderly-license-revocation.json").read_text(encoding="utf-8"))
        text = self.s.select_one("#bg-classroom").get_text()
        for r in cr["reasons_pro"] + cr["reasons_con"]:
            self.assertIn(r["text"], text)

    def test_why_row_follows_ledger_paragraph_count(self):
        ledger = self.d["background"]
        self.assertIn(ledger["definition"]["one_line"], self.s.select_one("#bg-why").get_text())
        d = copy.deepcopy(self.d)
        d["bg"]["ledger"]["cause"].append("段落を足した")
        d["background"] = d["bg"]["ledger"]
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_themes_yaml_mismatch_stops(self):
        d = copy.deepcopy(self.d)
        d["bg"]["theme"]["updated_at"] = "2026-01-01"
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_unknown_memo_section_stops(self):
        d = copy.deepcopy(self.d)
        self.row(d, "renewal")["points"][0]["memo_section"] = "存在しない見出し"
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_assessment_shows_skill_test_review(self):
        panel = self.s.find(id="issue-elderly-license-revocation-assessment")
        self.assertIn("方向変換", panel.select_one('.fr-check[data-check="skilltest-review"]').get_text())
        self.assertTrue(panel.select('.fr-claim[data-claim="skilltest"]'))



# ---------------------------------------------------------------- 手順7：公開候補と更新経路（docs/ は書き換えない）

import shutil  # noqa: E402

from scripts import build_elderly_redesign as redesign  # noqa: E402
from scripts import elderly_layout as layout  # noqa: E402

AS_OF = PUBLIC["updated_on"]
INPUTS = (
    "THEMES.yaml",
    "docs/data/themes/elderly-license-revocation.json",
    "data/public/themes/elderly-license-revocation.json",
    "data/elderly-license_issues-reread.json",
    "data/elderly-license-revocation_claim_posts.json",
    "data/verification/elderly-license-revocation-background.json",
    "quality/research/elderly-license-revocation-primary-sources.md",
)
LEGACY_IDS_INTERNAL = ("elc-", "explainer-modal", "elderly-connected-data", "pseg", "pbar", "pnum", "c-", "s-")


def protected(text: str, name: str) -> str:
    return re.search(f"<!-- {name}_START -->.*?<!-- {name}_END -->", text, re.S).group()


def vote_defs(text: str) -> tuple[str, str, str]:
    return tuple(re.search(rf"var {name}=\[(.*?)\];", text, re.S).group(1) for name in ("VOTE_ISSUES", "V2I", "STANCES"))


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
                         "https://sns-reaction-map.jp/elderly-license-revocation-reaction-map.html")
        self.assertEqual(self.s.select_one('meta[property="og:image"]')["content"],
                         self.src.select_one('meta[property="og:image"]')["content"])
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
            self.assertIn("var TOPIC='elderly-license-revocation-issue-stance-v1'", text)
            self.assertEqual(vote_defs(self.source), vote_defs(text))  # VOTE_ISSUES・V2I・STANCES が元と完全一致
            self.assertIn("choiceIdx:selIssue*STANCES.length+stanceIdx", text)
            self.assertIn("var STORAGE_KEY=window.SNS_REDESIGN_PRODUCTION?'sns_vote_elderly_license_revocation_2step':"
                          "'sns_vote_preview_elderly_license_revocation_2step';", text)
        issues, _v2i, stances = vote_defs(self.release)
        self.assertEqual(len(re.findall(r"\bk:'", issues)), 6)  # 論点6×立場3＝18通り
        self.assertEqual(len(re.findall(r"\bk:'", stances)), 3)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=location.hostname==='sns-reaction-map.jp'", self.release)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=false", self.preview)
        scripts = self.s.select("script")
        config = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-config.js"))
        client = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-store.js"))
        self.assertEqual(config + 2, client)
        # 投票の前置きの文も元HTMLのまま
        self.assertEqual(self.s.select_one("#vote-section > p").get_text(), self.src.select_one("#vote-section > p").get_text())

    def test_adapter_vote_fingerprint_matches_source(self):
        from scripts.refresh_adapters.elderly import vote_fingerprint
        self.assertEqual(vote_fingerprint(self.source), vote_fingerprint(self.release))
        self.assertEqual(vote_fingerprint(self.release)[3], 18)

    def test_faq_json_ld_matches_visible_faq(self):
        payloads = [json.loads(x.get_text()) for x in self.s.select('script[type="application/ld+json"]')]
        faq = [p for p in payloads if p.get("@type") == "FAQPage"]
        self.assertEqual(len(faq), 1)
        visible = redesign.faq_items(self.s)
        self.assertEqual(len(visible), 9)  # 冒頭の「よく検索される疑問」6問＋背景の「よくある質問」3問
        self.assertEqual([(q["name"], q["acceptedAnswer"]["text"]) for q in faq[0]["mainEntity"]], visible)
        texts = self.s.get_text()
        for q, a in visible:
            self.assertIn(q, texts)
            self.assertIn(a, texts)
            self.assertNotIn("一次資料メモの確認日", a)  # 背景の行末の確認日の注記は答えに入れない
        self.assertEqual(sum(1 for p in payloads if p.get("@type") == "Article"), 1)
        # 旧ページの検索入口・連動表示・テーマ共通の見た目は読み込まない
        for name in ("elderly-search-entry.js", "elderly-search-entry.css", "elderly-connected.js",
                     "elderly-connected-page.js", "elderly-connected.css", "theme-design.js", "theme-design.css"):
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
        self.assertIn('<time datetime="2026-06-28">', self.release)
        self.assertIn(f'<time datetime="{PUBLIC["updated_on"]}">', self.release)
        self.assertIsNotNone(self.s.select_one('header.modern-site-header a[href="index.html"]'))

    def test_detail_data_is_kept_verbatim(self):
        """詳細データの3表（論点別・スタンス別・表現強度別。公開JSONと同じ455件の集計）は元HTMLのまま。"""
        new = [str(d) for d in self.s.select("#detail-data > details")]
        old = [str(d) for d in self.src.select("#detail-data > details")]
        self.assertEqual(new, old)
        self.assertEqual([d.summary.get_text(strip=True) for d in self.s.select("#detail-data > details")],
                         ["論点別件数", "スタンス別件数", "表現強度別件数"])

    def test_tide_card_is_inherited_verbatim_inside_fold(self):
        block = re.search(r'<section class="update-dashboard"[^>]*><!-- TIDE_CARD_START -->.*?<!-- TIDE_CARD_END --></section>',
                          self.source, re.S).group()
        self.assertEqual(self.release.count(block), 1)
        self.assertIn("/* TIDE_CARD_START */", self.release)
        fold = self.s.select_one("#cap-trend-more")
        self.assertEqual(fold.name, "details")
        self.assertFalse(fold.has_attr("open"))
        self.assertIsNotNone(fold.select_one("#elderly-license-revocation-tide-widget"))
        glance = self.s.select_one("#cap-trend .cap-trend-glance")
        data = json.loads(re.search(r"const datasets = (\{.*?\});\n", self.release, re.S).group(1))
        self.assertEqual(len(glance.select(".cap-trend-spark svg polyline")), len(data["stance"]["rows"]))
        self.assertIn(self.s.select_one("[data-tide-headline]").get_text(), glance.select_one(".cap-trend-lead").get_text())
        self.assertLess(self.release.index("TIDE_CARD_START -->"), self.release.index('id="vote-section"'))

    def test_issue_glance_from_tide(self):
        data = json.loads(re.search(r"const datasets = (\{.*?\});\n", self.release, re.S).group(1))
        rows = {r["label"]: r for r in data["issue"]["rows"]}
        for issue in PUBLIC["issues"]:
            box = self.s.find(id="issue-" + issue["id"]).select_one(".fr-glance")
            link = box.select_one(".fr-glance-link")
            # 設定の飛び先（trend.widget_id）が、引き継いだ潮目のカードの実際の id とつながっている
            self.assertEqual((link["href"], link["data-tide-mode"]), ("#elderly-license-revocation-tide-widget", "issue"))
            self.assertIsNotNone(self.s.find(id=link["href"][1:]))
            cap = box.select_one(".fr-glance-cap")
            if issue["label"] not in rows:
                self.assertIsNone(cap, issue["id"])  # 代替交通整備と「その他」は潮目の論点に無い
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
        for sel in ("#elderly-license-revocation-reading", "#elderly-license-revocation-background", "#elderly-open",
                    "#cap-trend", "#cap-method"):
            # 詳細データの「論点別件数」は元HTMLで開いた状態のまま引き継ぐ（外側の「作り方と詳細データ」が閉じている）
            opened = [d for d in self.s.select(sel + " details[open]") if not d.find_parent(id="detail-data")]
            self.assertEqual([d.get("class") for d in opened], [], sel)
        self.assertFalse(self.s.select_one("#cap-method").has_attr("open"))

    def test_unpublished_reasons_are_shown(self):
        """理由区分の無い4論点は「理由は未公開」の1行を出す（追い読みで再読データに加われば自動で消える）。"""
        labels = {i["id"]: i["label"] for i in PUBLIC["issues"]}
        marked = {p["data-issue-panel"] for p in self.s.select(".fr-panel") if p.select_one("[data-unpublished]")}
        self.assertEqual(marked, {iid for iid, lab in labels.items() if lab not in WITH_REASONS})
        for iid in marked:
            self.assertTrue(self.s.find(id="issue-" + iid).select_one("[data-unpublished]").get_text(strip=True))

    def test_classroom_section_contract(self):
        section = self.release[self.release.index("<!-- CLASSROOM_START -->"):self.release.index("<!-- CLASSROOM_END -->")]
        self.assertIn('class="classroom-print-btn"', section)
        self.assertIn("classroom-sources", section)
        self.assertIn("classroom-questions", section)
        self.assertLess(self.release.index("<!-- CLASSROOM_START -->"), self.release.index("<!-- ARTICLE_TRUST_START -->"))

    def test_family_check_row_and_no_merit_demerit(self):
        """家族で話す前の確認（4項目）は背景の1行に。メリット・デメリットは載せない（司令塔の決定）。"""
        row = self.s.select_one("#bg-family")
        self.assertEqual(row.name, "details")
        self.assertEqual(len(row.select("dl.fb-checklist > div")), 4)
        self.assertNotIn("主なメリット", self.release)
        self.assertNotIn("主なデメリット", self.release)

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
        # 旧ページで外から指せた節のidは、新ページにあるか、読み替え先があるか（js・CSS の内部用idは除く）
        for node in self.src.find_all(id=True):
            old = node["id"]
            if self.s.find(id=old) is not None or old in redesign.ALIASES or old.startswith(LEGACY_IDS_INTERNAL):
                continue
            self.assertTrue(any(old.startswith(p) for p in redesign.ISSUE_PREFIXES), old)
        for issue in PUBLIC["issues"]:
            self.assertIsNotNone(self.src.find(id="issue-" + issue["id"]))
            self.assertEqual(self.s.find(id="issue-" + issue["id"])["data-issue-panel"], issue["id"])
        for kept in ("vote-section", "detail-data", "related-topics", "caution", "planet-data", "research-conditions",
                     "elderly-license-revocation-tide-widget", "bg-classroom", "article-trust-title"):
            self.assertIsNotNone(self.s.find(id=kept), kept)

    def test_planet_is_copied_from_source(self):
        """全体像の山なみは、元HTMLの対話式の山なみ（PLANET_SECTION）をそのまま写す（読み込み時の自動着地だけ置き換える）。"""
        src_section = re.search(r"<!-- PLANET_SECTION_START -->(.*?)<!-- PLANET_SECTION_END -->", self.source, re.S).group(1)
        src = soup_of(src_section)
        src_script = [x for x in src.find_all("script", recursive=False) if x.get("id") != "planet-data"][0].string
        self.assertEqual(src_script.count(redesign.AUTO_LAND), 1)
        self.assertEqual(self.release.count(src_script.replace(redesign.AUTO_LAND, redesign.AUTO_LAND_OFF)), 1)
        self.assertEqual(self.release.count(src.select_one("section.planet-panel > style").string), 1)
        self.assertEqual(self.release.count("window.PLANET_DATA="), 1)
        planet = self.s.select_one("#elderly-license-revocation-reading .fr-map section.planet-panel #planet-block")
        self.assertIsNotNone(planet)
        self.assertLess(self.release.index('id="planet-block"'), self.release.index('class="fr-tabs"'))  # 山なみは論点タブの上
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
        self.assertLess(self.release.index(src_script[:200]), self.release.index("window.ElderlyReading"))
        self.assertLess(self.release.index("window.ElderlyReading"), self.release.index("function goReading"))

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
        # 自動着地の処理が変わったら、黙って写さずに止まる
        moved = self.source.replace(redesign.AUTO_LAND, redesign.AUTO_LAND.replace("landSilently(idIndex[top.id]);", "land(idIndex[top.id]);"), 1)
        self.assertNotEqual(moved, self.source)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.html"
            path.write_text(moved, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "自動着地"):
                redesign.build(path, Path(temp) / "out", "release", as_of=AS_OF)

    def test_no_legacy_widgets(self):
        for marker in ("SEARCH_ENTRY_START", "THEME_DESIGN_START", "ELDERLY_CONNECTED_START", "ELDERLY_CONNECTED_CONTENT_START",
                       "STANCE_GLANCE_START", "THEME_COUNT_START", "ELDERLY_ISSUE_MEDIA_START"):
            self.assertNotIn("<!-- " + marker, self.release)
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.release)
        self.assertNotIn("const SM_RAW", self.release)
        for embed in self.s.select(".x-embed"):
            self.assertRegex(embed.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")

    def test_provenance_counts_and_detects_mismatch(self):
        from scripts.elderly_license_count_provenance import verified_selectors
        result = verified_selectors(self.release, ROOT)
        self.assertEqual(len(result), len(PUBLIC["issues"]) + 2)  # 論点の欄6つ＋冒頭の件数欄＋冒頭の統計
        stat = self.s.select_one("#elo-steps .elo-stat").get_text()
        n = re.search(r"自主返納は(\d[\d,]*)件", stat).group(1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(self.release.replace(f"自主返納は{n}件", "自主返納は435,068件", 1), ROOT)
        node = self.s.select_one(f"#issue-{FIRST} li.fr-reason .fr-reason-n b")
        broken = self.release.replace(str(node), str(node).replace(node.get_text(), str(int(node.get_text().replace(",", "")) + 1)), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)
        mini = self.s.select_one(f"#issue-{FIRST} article.fr-reason-detail .fr-mini")
        label = mini["aria-label"]
        n = re.search(r"義務化賛成 (\d[\d,]*)件", label).group(1)
        broken = self.release.replace(label, label.replace(f"義務化賛成 {n}件", f"義務化賛成 {int(n.replace(',', '')) + 1}件"), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)


class LayoutTests(unittest.TestCase):
    """手順7：更新経路（materialize → 旧形式の全処理 → finish）と、公開後の単独実行。"""

    def _root(self, temp: str) -> Path:
        root = Path(temp)
        shutil.copytree(ROOT / "configs", root / "configs")
        shutil.copytree(ROOT / "scripts/elderly_redesign", root / "scripts/elderly_redesign")
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
            (root / layout.PAGE).write_text('<meta name="elderly-layout">')
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
            self.assertIn(b'name="elderly-layout"', first)
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
        """新しい意見を追い読みしないまま公開JSONの件数が増えた回と同じ形（明細が論点の件数より少ない）では止まる。"""
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            (root / layout.CONFIG).write_text('{"enabled": true}')
            path = root / "data/elderly-license_issues-reread.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            gone = next(i for i in raw["items"] if i["main_issue"] == "義務化・事故防止")
            raw["items"].remove(gone)
            raw["buckets"]["義務化・事故防止"][gone["bucket"]]["count"] -= 1
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            before = (root / layout.PAGE).read_bytes()
            with self.assertRaisesRegex(ValueError, "照合で停止"):
                layout.finish(root, as_of=AS_OF)
            self.assertEqual(before, (root / layout.PAGE).read_bytes())
            self.assertFalse((root / layout.SOURCE).exists())

    def test_adapter_stops_when_reread_item_has_no_stance(self):
        from scripts.refresh_adapters.elderly import check_reread_stances
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            self.assertEqual(check_reread_stances(root), len(REREAD["items"]))
            path = root / "data/elderly-license_issues-reread.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw["items"][0].pop("stance")
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "立場（stance）がありません"):
                check_reread_stances(root)

    def test_refresh_path_is_wired(self):
        refresh = (ROOT / "scripts/refresh_topic.py").read_text(encoding="utf-8")
        self.assertEqual(refresh.count("finish_elderly_layout(candidate_root)"), 2)
        self.assertEqual(refresh.count("materialize_elderly(candidate_root)"), 1)
        self.assertIn("elderly_layout_enabled(root)", refresh)
        adapter = (ROOT / "scripts/refresh_adapters/elderly.py").read_text(encoding="utf-8")
        self.assertIn("current_page = source_for_refresh(root)", adapter)
        self.assertIn("check_reread_stances(root)", adapter)
        self.assertIn("materialize_elderly(target)", (ROOT / "scripts/verify_builder_rebuildability.py").read_text(encoding="utf-8"))
        for path in ("scripts/apply_theme_design.py", "scripts/seo/apply_classroom_section.py", "scripts/seo/apply_theme_trust.py",
                     "scripts/refresh_planet_section.py", "scripts/verify_theme_page.py", "scripts/build_elderly_arena.py",
                     "scripts/elderly_issue_media.py", "scripts/elderly_license_count_provenance.py"):
            self.assertIn("elderly-layout", (ROOT / path).read_text(encoding="utf-8"), path)


if __name__ == "__main__":
    unittest.main()
