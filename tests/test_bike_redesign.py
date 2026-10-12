"""自転車の青切符・新デザインの試作（冒頭、論点ごとの読書面、背景の開閉行）。docs/ は書き換えない。

憲法改正論議（tests/test_constitutional_redesign.py）の手順5・6に当たる検査。読書面は最初から部活動型の圧縮済みの型で作る。
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

from scripts import bike_opening as opening

ROOT = opening.ROOT
PUBLIC = json.loads((ROOT / "docs/data/themes/bike-blue-ticket.json").read_text(encoding="utf-8"))
CANON = ROOT / "social-samples/bike-blue-ticket_2d_classified.json"
OPENING_CONFIG = ROOT / "configs/bike-blue-ticket-opening.json"
OTHER = "bike-blue-ticket-other"
FIRST = "bike-blue-ticket-enforcement-support"


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class OpeningTests(unittest.TestCase):
    """冒頭：確認日は設定の1か所から。反則金は政令別表第六どおり。正本の見た目は scripts/bike_redesign/。"""

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
        self.assertIn(f"制度の記述は、{when}に一次資料で確かめました。", frag)
        self.assertIn(f"{when}時点で、警察庁はこれより新しい運用状況を公表していません。", frag)
        self.assertIn(f'data-checked-on="{self.config["checked_on"]}"', frag)
        cfg = copy.deepcopy(self.config)
        cfg["checked_on"] = "2026-12-01"
        self.assertIn("2026年12月1日に一次資料で確かめました", self.frag(cfg))

    def test_source_checked_after_checked_on_stops(self):
        cfg = copy.deepcopy(self.config)
        cfg["sources"]["npa_faq"]["checked_on"] = "2026-12-31"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "opening.json"
            path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(SystemExit):
                opening.load_inputs(path)
            cfg["sources"]["npa_faq"]["checked_on"] = None
            path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(SystemExit):
                opening.load_inputs(path)

    def test_fines_follow_cabinet_order_table6(self):
        """政令別表第六（原付等の欄）：並進禁止3,000円、乗車積載方法違反5,000円、軽車両乗車積載制限違反3,000円。"""
        fines = {i["name"]: i["amount"] for i in self.config["fines"]["items"]}
        self.assertEqual(fines["並進禁止違反"], 3000)
        self.assertEqual(fines["乗車積載方法違反"], 5000)
        self.assertEqual(fines["軽車両乗車積載制限違反（二人乗りなど）"], 3000)
        self.assertEqual(fines["歩道徐行等義務違反"], 3000)
        self.assertNotIn("並進禁止・乗車積載方法違反", self.frag())

    def test_opening_assets_live_in_redesign_folder(self):
        for name in ("opening.css", "opening.js"):
            self.assertTrue((opening.ASSETS / name).is_file(), name)
            for proto in ("bike-blue-ticket-opening", "bike-blue-ticket-reading"):
                copy_ = ROOT / "quality/prototypes" / proto / name
                self.assertEqual(copy_.read_text(encoding="utf-8"), (opening.ASSETS / name).read_text(encoding="utf-8"), (proto, name))


class ReadingPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts import bike_reading as reading

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
        first = self.s.select_one("#bike-blue-ticket-reading .fr-panels > *")
        self.assertEqual(first.name, "nav")
        self.assertIn("fr-tabs", first["class"])

    def test_issue_order_count_desc_other_last(self):
        tabs = [a["data-issue-id"] for a in self.s.select(".fr-tab")]
        named = sorted((i for i in PUBLIC["issues"] if i["id"] != OTHER), key=lambda i: (-int(i["count"]), i["id"]))
        self.assertEqual(tabs, [i["id"] for i in named] + [OTHER])
        self.assertIn("is-other", self.s.select_one(f'.fr-tab[data-issue-id="{OTHER}"]')["class"])

    def test_counts_and_stances_match_public_json(self):
        order = [s["id"] for s in self.reading.stance_order(self.d)]
        totals = Counter()
        for issue in PUBLIC["issues"]:
            for s in issue["stances"]:
                totals[s["id"]] += int(s["count"])
        self.assertEqual(order, sorted(totals, key=lambda k: (-totals[k], k)))
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
            self.assertIn("世論調査ではなく", note.get_text())

    def test_reasons_recounted_from_reread_details(self):
        raw = json.loads((ROOT / "data/bike-blue-ticket_issues-reread.json").read_text(encoding="utf-8"))
        for issue in PUBLIC["issues"]:
            panel = self.panel(issue["id"])
            items = raw[issue["label"]]["items"]
            self.assertEqual(len(items), int(issue["count"]), issue["label"])
            for bid in raw[issue["label"]]["buckets"]:
                node = panel.select_one(f'li.fr-reason[data-reason="{bid}"] .fr-reason-n b')
                n = sum(1 for it in items if it["bucket"] == bid)
                self.assertEqual(node.get_text(), f"{n:,}", (issue["label"], bid))

    def test_reason_stances_come_from_stance_table_and_sum_to_public(self):
        for label, rr in self.d["reread"].items():
            issue = next(i for i in PUBLIC["issues"] if i["label"] == label)
            total = Counter(self.reading.item_stance(self.d, it) for it in rr["items"])
            self.assertEqual({s["id"]: total.get(s["id"], 0) for s in issue["stances"]},
                             {s["id"]: int(s["count"]) for s in issue["stances"]}, label)
        table = json.loads((ROOT / "data/bike-blue-ticket_reread-stances.json").read_text(encoding="utf-8"))
        self.assertEqual(table["count"], len(table["stances"]))
        self.assertEqual(table["count"], int(PUBLIC["opinion_count"]))
        self.assertEqual(table["public_mismatch"], 0)
        self.assertNotIn("tweet_id", json.dumps(table["stances"]))

    def test_does_not_read_private_canonical(self):
        self.assertNotIn("social-samples", (ROOT / "scripts/bike_reading.py").read_text(encoding="utf-8"))
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
        labels = [s["label"] for s in d["planet"]["stances"]]
        d["stances"][key] = next(k for k in labels if k != d["stances"][key])
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        del d["stances"][key]
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_enforcement_panel_is_complete(self):
        panel = self.panel(FIRST)
        self.assertIn("is-complete", panel["class"])
        self.assertTrue(panel.select(".fr-desc"))
        self.assertEqual(len(panel.select(".fr-voice")), len(self.d["reread"]["取締り強化賛成"]["buckets"]))
        self.assertTrue(panel.select('.fr-claim[data-claim="accident"]'))
        self.assertTrue(panel.select('[data-sunk="bike-blue-ticket-sc-2"]'))
        self.assertTrue(panel.select('.fr-check[data-check="unyou"]'))
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
                descs = [p for p in panel.select(".fr-panel-head > div > .fr-desc") if "fr-other-note" not in p.get("class", [])]
                self.assertEqual(len(descs), 1)
                on = panel.select(".fr-reason-detail[data-on]")
                self.assertEqual(len(on), 1)
                counts = [int(b.get_text().replace(",", "")) for b in panel.select(".fr-reasons .fr-reason-n b")]
                self.assertEqual(on[0]["data-reason"], panel.select_one(".fr-reasons li.fr-reason")["data-reason"])
                self.assertEqual(counts, sorted(counts, reverse=True))
                for sel in ("details.fr-posts", "details.fr-stance", ".fr-evidence details.fr-fold"):
                    self.assertTrue(panel.select(sel), (issue["id"], sel))
                for claim in panel.select(".fr-claim"):
                    self.assertTrue(claim.summary.select_one(".fr-verdict"))

    def test_reason_links_survive_underscored_ids(self):
        """理由区分のIDに下線（s_enforcement_gap）が入っても、ページ内リンクの飛び先がある。"""
        for a in self.s.select("a[data-reason-pick]"):
            self.assertIsNotNone(self.s.find(id=a["href"][1:]), a["href"])
        js = (ROOT / "scripts/bike_redesign/reading.js").read_text(encoding="utf-8")
        self.assertIn("ids.find(x => h.startsWith('fr-r-' + x + '-'))", js)

    def test_other_shows_top_bucket(self):
        """「その他」は見出しの下に最も多い理由区分と割合を出す（冒頭の「その他」の中身と同じ数え方）。"""
        rr = self.d["reread"]["その他"]
        bid, b = sorted(rr["buckets"].items(), key=lambda kv: (-int(kv[1]["count"]), kv[0]))[0]
        note = self.panel(OTHER).select_one(".fr-other-note")
        self.assertEqual(note["data-other-top"], bid)
        share = round(int(b["count"]) / len(rr["items"]) * 100)
        self.assertIn(f"「{b['label']}」で、この論点の{share}%", note.get_text())

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
                reason = icfg["posts"]["same_stance_reason"]
                self.assertEqual(self.panel(iid).select_one("[data-same-stance]").get_text(), reason, iid)
            else:
                self.assertIsNone(self.panel(iid).select_one("[data-same-stance]"), iid)

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では代表投稿の選定基準を確かめられない")
    def test_selected_posts_meet_canonical_criteria(self):
        canon = json.loads(CANON.read_text(encoding="utf-8"))
        norm = lambda t: re.sub(r"\s+", "", t)
        texts = Counter(norm(x["text"]) for x in canon)
        by_id = {str(x["tweet_id"]): x for x in canon}
        labels = {i["id"]: i["label"] for i in PUBLIC["issues"]}
        ids = []
        for iid, icfg in self.d["cfg"]["issues"].items():
            for p in icfg.get("posts", {}).get("items", []):
                ids.append(p["id"])
                x = by_id[p["id"]]
                c = x["classification"]
                self.assertTrue(x["is_opinion"], p["id"])
                self.assertEqual(c["main_issue"], labels[iid], p["id"])
                self.assertTrue(c["article_usable"], p["id"])
                self.assertEqual(c["risk"], "low", p["id"])
                self.assertNotEqual(c["intensity"], "high", p["id"])
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
        d["public"]["issues"][0]["stances"][2]["count"] -= 1
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        d["public"]["trends"] = []
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
        del d["cfg"]["issues"][FIRST]["posts"]["same_stance_reason"]
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
        from scripts import bike_background as background
        from scripts import bike_reading as reading

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

    def test_all_issues_complete_with_voices_and_posts(self):
        labels = {i["id"]: i["label"] for i in PUBLIC["issues"]}
        for iid, icfg in self.d["cfg"]["issues"].items():
            self.assertEqual(icfg["status"], "complete", iid)
            self.assertEqual(len(icfg["description"]), 2, iid)
            buckets = self.d["reread"][labels[iid]]["buckets"]
            self.assertEqual(set(icfg["reasons"]), set(buckets), iid)
            self.assertEqual(len(icfg["posts"]["items"]), 2, iid)
            self.assertTrue(icfg["posts"]["selection_basis"], iid)
        self.assertEqual(self.s.select(".fr-panel.is-pending"), [])

    def test_see_also_targets_exist(self):
        for a in self.s.select(".fr-see a, .fb-issues a, .fb-to-issue"):
            self.assertIsNotNone(self.s.find(id=a["href"][1:]), a["href"])

    def test_rows_are_closed_details(self):
        rows = self.s.select("#bike-blue-ticket-background details.fb-row")
        self.assertEqual([r["id"] for r in rows], ["bg-system", "bg-why", "bg-timeline", "bg-faq", "bg-classroom", "bg-unverified"])
        self.assertTrue(all(not r.has_attr("open") for r in rows))

    def test_checked_on_drives_time_wording(self):
        """施行済み。「◯月◯日時点」は冒頭の設定 checked_on 1か所から作る。"""
        when = opening.jp_date(self.d["ocfg"]["checked_on"])
        self.assertIn(f"{when}時点で、警察庁が公表した全国の運用状況は", self.s.select_one("#bg-timeline").get_text())
        self.assertIn(f"{when}時点で、その後の全国の件数は公表されていません", self.s.select_one("#bg-unverified").get_text())
        d = copy.deepcopy(self.d)
        d["ocfg"]["checked_on"] = "2026-12-01"
        self.assertIn("2026年12月1日時点で", self.render_bg(d))
        d["ocfg"]["checked_on"] = "2026-09-01"  # 背景台帳の確認日より古い
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_system_row_covers_required_topics(self):
        labels = [dt.get_text() for dt in self.s.select("#bg-system dt")]
        self.assertEqual(labels, ["対象年齢", "反則金の額", "納め方", "前科と免許の点数", "指導警告票との関係"])
        text = self.s.select_one("#bg-system").get_text()
        for word in ("16歳", "原則7日以内", "10日以内", "前科", "点数", "指導警告票", "赤切符", "3,000円"):
            self.assertIn(word, text)

    def test_faq_does_not_repeat_opening(self):
        qs = [dt.get_text() for dt in self.s.select("#bg-faq dt")]
        self.assertEqual(len(qs), 4)
        oc = json.loads(OPENING_CONFIG.read_text(encoding="utf-8"))
        opening_qs = [i["q"] for i in oc["faq"]["items"]] + [oc[k]["question"] for k in ("age", "fines", "after", "warning")]
        self.assertFalse(set(qs) & set(opening_qs))

    def test_classroom_is_read_from_shared_config(self):
        cr = json.loads((ROOT / "configs/classroom/bike-blue-ticket.json").read_text(encoding="utf-8"))
        text = self.s.select_one("#bg-classroom").get_text()
        for r in cr["reasons_pro"] + cr["reasons_con"]:
            self.assertIn(r["text"], text)

    def test_why_row_follows_ledger_paragraph_count(self):
        ledger = self.d["background"]
        text = self.s.select_one("#bg-why").get_text()
        self.assertIn(ledger["definition"]["one_line"], text)
        d = copy.deepcopy(self.d)
        d["bg"]["ledger"]["cause"].append("段落を足した")
        d["background"] = d["bg"]["ledger"]
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_sidewalk_check_matches_npa_faq(self):
        """台帳の「子乗せ自転車は歩道を通行でき」は警察庁FAQと合わないので、読書面では言い換える。"""
        for iid in ("bike-blue-ticket-road-safety", "bike-blue-ticket-infrastructure-first"):
            body = self.s.find(id="issue-" + iid).select_one('.fr-check[data-check="basho"]').get_text()
            self.assertIn("70歳以上", body)
            self.assertNotIn("子乗せ自転車は歩道を通行でき", body)

    def test_unknown_check_rewrite_stops(self):
        d = copy.deepcopy(self.d)
        d["cfg"]["check_rewrites"]["nai"] = {"found": "x"}
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_themes_yaml_mismatch_stops(self):
        d = copy.deepcopy(self.d)
        d["bg"]["theme"]["updated_at"] = "2026-01-01"
        with self.assertRaises(SystemExit):
            self.render_bg(d)

    def test_unknown_memo_section_stops(self):
        d = copy.deepcopy(self.d)
        d["bg"]["cfg"]["groups"][0]["rows"][0]["points"][0]["memo_section"] = "存在しない見出し"
        with self.assertRaises(SystemExit):
            self.render_bg(d)


if __name__ == "__main__":
    unittest.main()
