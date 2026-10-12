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


# ---------------------------------------------------------------- 手順7：公開候補と更新経路（docs/ は書き換えない）

import shutil  # noqa: E402

from scripts import bike_layout as layout  # noqa: E402
from scripts import build_bike_redesign as redesign  # noqa: E402

AS_OF = PUBLIC["updated_on"]
INPUTS = (
    "THEMES.yaml",
    "docs/data/themes/bike-blue-ticket.json",
    "data/public/themes/bike-blue-ticket.json",
    "data/bike-blue-ticket_issues-reread.json",
    "data/bike-blue-ticket_reread-stances.json",
    "data/verification/bike-blue-ticket-claims.json",
    "data/verification/bike-blue-ticket-background.json",
    "quality/research/bike-blue-ticket-primary-sources.md",
)


def protected(text: str, name: str) -> str:
    return re.search(f"<!-- {name}_START -->.*?<!-- {name}_END -->", text, re.S).group()


def vote_defs(text: str) -> tuple[str, str, str]:
    return tuple(re.search(rf"var {name}=\[(.*?)\];", text, re.S).group(1) for name in ("VOTE_ISSUES", "V2I", "STANCES"))


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
                         "https://sns-reaction-map.jp/bike-blue-ticket-reaction-map.html")
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
            self.assertIn("var TOPIC='bike-blue-ticket-issue-stance-v1'", text)
            self.assertEqual(vote_defs(self.source), vote_defs(text))  # VOTE_ISSUES・V2I・STANCES が元と完全一致
            self.assertIn("choiceIdx:selIssue*STANCES.length+stanceIdx", text)
            self.assertIn("var STORAGE_KEY=window.SNS_REDESIGN_PRODUCTION?'sns_vote_bike_blue_ticket_2step':"
                          "'sns_vote_preview_bike_blue_ticket_2step';", text)
        issues, _v2i, stances = vote_defs(self.release)
        self.assertEqual(len(re.findall(r"\bk:'", issues)), 6)  # 論点6×立場3＝18通り
        self.assertEqual(len(re.findall(r"\bk:'", stances)), 3)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=location.hostname==='sns-reaction-map.jp'", self.release)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=false", self.preview)
        scripts = self.s.select("script")
        config = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-config.js"))
        client = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-store.js"))
        self.assertEqual(config + 2, client)
        # 投票の前置きは施行済みの言い方に（元HTMLの未来形「導入されます」は出さない）
        lead = self.s.select_one("#vote-section > p").get_text()
        self.assertNotIn("導入されます", lead)
        self.assertIn("2026年4月から", lead)

    def test_adapter_vote_fingerprint_matches_source(self):
        from scripts.refresh_adapters.bike import vote_fingerprint
        self.assertEqual(vote_fingerprint(self.source), vote_fingerprint(self.release))
        self.assertEqual(vote_fingerprint(self.release)[3], 18)

    def test_faq_json_ld_matches_visible_faq(self):
        payloads = [json.loads(x.get_text()) for x in self.s.select('script[type="application/ld+json"]')]
        faq = [p for p in payloads if p.get("@type") == "FAQPage"]
        self.assertEqual(len(faq), 1)
        visible = redesign.faq_items(self.s)
        self.assertEqual(len(visible), 8)  # 冒頭の短答の問い4問＋背景の「よくある質問」4問
        self.assertEqual([(q["name"], q["acceptedAnswer"]["text"]) for q in faq[0]["mainEntity"]], visible)
        texts = self.s.get_text()
        for q, a in visible:
            self.assertIn(q, texts)
        self.assertEqual(sum(1 for p in payloads if p.get("@type") == "Article"), 1)
        # 旧ページの検索入口・連動表示・テーマ共通の見た目は読み込まない
        self.assertNotIn('id="bike-search-entry"', self.release)
        for name in ("bike-blue-ticket-search-entry.js", "bike-blue-ticket-search-entry.css", "bike-blue-ticket-connected.js",
                     "bike-blue-ticket-connected-page.js", "bike-blue-ticket-connected.css", "theme-design.js", "theme-design.css"):
            self.assertNotIn(f'="{name}', self.release)

    def test_inherited_sections_and_links(self):
        self.assertEqual(len(self.s.select("#planet-data")), 1)
        self.assertEqual(self.s.select_one("#planet-data").string, self.src.select_one("#planet-data").string)
        self.assertIn("社会全体の世論調査ではありません。", self.s.select_one("#caution").get_text())
        for sel in ("#related-topics", "body > footer", "#related-theme-tracking"):
            self.assertEqual(self.s.select_one(sel).get_text(), self.src.select_one(sel).get_text(), sel)
        hrefs = {a["href"] for a in self.s.select("footer a[href]")}
        for href in ("about.html#operator", "about.html#method", "privacy.html", "disclaimer.html"):
            self.assertIn(href, hrefs)
        self.assertIn('<time datetime="2026-06-28">', self.release)
        self.assertIn(f'<time datetime="{PUBLIC["updated_on"]}">', self.release)
        self.assertIsNotNone(self.s.select_one('header.modern-site-header a[href="index.html"]'))

    def test_detail_data_drops_only_old_tables(self):
        """詳細データは旧体系の3表（旧177件）を外し、「注意」だけを元HTMLのまま残す（内容対応表 36〜39）。"""
        new = [d.summary.get_text(strip=True) for d in self.s.select("#detail-data > details")]
        old = [d.summary.get_text(strip=True) for d in self.src.select("#detail-data > details")]
        self.assertEqual(new, [x for x in old if x not in redesign.DETAIL_DROP])
        self.assertEqual(new, ["注意"])
        kept = self.src.select("#detail-data > details")[-1]
        self.assertEqual(str(self.s.select("#detail-data > details")[-1]), str(kept))
        self.assertNotIn("heat-table", str(self.s.select_one("#detail-data")))

    def test_tide_card_is_inherited_verbatim_inside_fold(self):
        block = re.search(r'<section class="update-dashboard"[^>]*><!-- TIDE_CARD_START -->.*?<!-- TIDE_CARD_END --></section>',
                          self.source, re.S).group()
        self.assertEqual(self.release.count(block), 1)
        self.assertIn("/* TIDE_CARD_START */", self.release)
        fold = self.s.select_one("#cap-trend-more")
        self.assertEqual(fold.name, "details")
        self.assertFalse(fold.has_attr("open"))
        self.assertIsNotNone(fold.select_one("#bike-blue-ticket-tide-widget"))
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
            self.assertEqual((link["href"], link["data-tide-mode"]), ("#bike-blue-ticket-tide-widget", "issue"))
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
        for sel in ("#bike-blue-ticket-reading", "#bike-blue-ticket-background", "#bike-open", "#cap-trend", "#cap-method"):
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
        # 旧ページで外から指せた節のidは、新ページにあるか、読み替え先があるか（js・CSS の内部用idは除く）
        internal = ("bike-reason-count-", "bike-check-note-", "bike-source-", "explainer-modal", "bike-connected-data",
                    "pseg", "reread-basis-css", "insight-issue-breakdown-css", "c-", "s-")
        for node in self.src.find_all(id=True):
            old = node["id"]
            if self.s.find(id=old) is not None or old in redesign.ALIASES or old.startswith(internal):
                continue
            self.assertTrue(any(old.startswith(p) for p in redesign.ISSUE_PREFIXES), old)
        for issue in PUBLIC["issues"]:
            self.assertIsNotNone(self.src.find(id="issue-" + issue["id"]))
            self.assertEqual(self.s.find(id="issue-" + issue["id"])["data-issue-panel"], issue["id"])
        for kept in ("vote-section", "detail-data", "related-topics", "caution", "planet-data", "research-conditions",
                     "bike-blue-ticket-tide-widget", "bg-classroom"):
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
        planet = self.s.select_one("#bike-blue-ticket-reading .fr-map section.planet-panel #planet-block")
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
        self.assertLess(self.release.index(src_script[:200]), self.release.index("window.BikeReading"))
        self.assertLess(self.release.index("window.BikeReading"), self.release.index("function goReading"))

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
        for marker in ("BIKE_SEARCH_ENTRY_START", "THEME_DESIGN_START", "BIKE_CONNECTED_START", "BIKE_CONNECTED_CONTENT_START",
                       "STANCE_GLANCE_START", "THEME_COUNT_START", "BIKE_ISSUE_MEDIA_START", "REREAD_BASIS_START"):
            self.assertNotIn("<!-- " + marker, self.release)
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.release)
        self.assertNotIn("const SM_RAW", self.release)
        self.assertNotIn("並進禁止・乗車積載方法違反", self.release)
        for embed in self.s.select(".x-embed"):
            self.assertRegex(embed.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")

    def test_provenance_counts_and_detects_mismatch(self):
        from scripts.bike_blue_ticket_count_provenance import verified_selectors
        result = verified_selectors(self.release, ROOT)
        self.assertEqual(len(result), len(PUBLIC["issues"]) + 1)
        node = self.s.select_one(f"#issue-{FIRST} li.fr-reason .fr-reason-n b")
        broken = self.release.replace(str(node), str(node).replace(node.get_text(), str(int(node.get_text().replace(",", "")) + 1)), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)
        mini = self.s.select_one(f"#issue-{FIRST} article.fr-reason-detail .fr-mini")
        label = mini["aria-label"]
        n = re.search(r"賛成（取締り強化支持） (\d[\d,]*)件", label).group(1)
        broken = self.release.replace(label, label.replace(f"賛成（取締り強化支持） {n}件",
                                                           f"賛成（取締り強化支持） {int(n.replace(',', '')) + 1}件"), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)


class LayoutTests(unittest.TestCase):
    def _root(self, temp: str) -> Path:
        root = Path(temp)
        shutil.copytree(ROOT / "configs", root / "configs")
        shutil.copytree(ROOT / "scripts/bike_redesign", root / "scripts/bike_redesign")
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
            (root / layout.PAGE).write_text('<meta name="bike-layout">')
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
            self.assertIn(b'name="bike-layout"', first)
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
            path = root / "data/bike-blue-ticket_issues-reread.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw["取締り強化賛成"]["items"].pop()
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            before = (root / layout.PAGE).read_bytes()
            with self.assertRaisesRegex(ValueError, "照合で停止"):
                layout.finish(root, as_of=AS_OF)
            self.assertEqual(before, (root / layout.PAGE).read_bytes())
            self.assertFalse((root / layout.SOURCE).exists())

    def test_refresh_path_is_wired(self):
        refresh = (ROOT / "scripts/refresh_topic.py").read_text(encoding="utf-8")
        self.assertEqual(refresh.count("finish_bike_layout(candidate_root)"), 2)
        self.assertEqual(refresh.count("materialize_bike(candidate_root)"), 1)
        self.assertIn("bike_layout_enabled(root)", refresh)
        adapter = (ROOT / "scripts/refresh_adapters/bike.py").read_text(encoding="utf-8")
        self.assertIn("current_page = source_for_refresh(root)", adapter)
        self.assertIn("materialize_bike(target)", (ROOT / "scripts/verify_builder_rebuildability.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
