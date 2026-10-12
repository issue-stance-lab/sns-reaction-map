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


if __name__ == "__main__":
    unittest.main()
