"""生成AIと著作権・新デザインの試作（冒頭、山なみと論点の読書面）。docs/ は書き換えない。

副首都（tests/test_fukushuto_redesign.py）・皇室典範改正の手順5・6に当たる検査。
読書面の生成は公開できる入力（公開JSON・再読データ・設定）だけを読む。非公開の正典が要るのは、
代表投稿の選定基準を確かめる1件（正典が無い環境ではスキップ）だけ。
"""
from __future__ import annotations

import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from scripts import ai_copyright_opening as opening

ROOT = opening.ROOT
PUBLIC = json.loads((ROOT / "docs/data/themes/ai-copyright.json").read_text(encoding="utf-8"))
CANON = ROOT / "social-samples/ai-copyright_hermes_classified.json"
FORBIDDEN = ("違法", "合法")


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class OpeningTests(unittest.TestCase):
    """冒頭：確認日は設定の1か所から、手書きの文言に違法・合法を使わない。"""

    @classmethod
    def setUpClass(cls):
        cls.data = opening.load_inputs(ROOT / "configs/ai-copyright-opening.json")

    def test_checked_on_single_source(self):
        cfg = self.data["config"]
        frag = opening.render_fragment(self.data)
        when = opening.jp_date(cfg["checked_on"])
        self.assertIn(f"{when}時点", frag)
        for sid in cfg["sources"]:
            self.assertNotIn("checked_on", cfg["sources"][sid])  # 1か所に寄せた
        self.assertEqual(frag.count(f"資料の確認日 {when}"), sum(len(q["sources"]) for q in cfg["entry_questions"]))
        d = copy.deepcopy(self.data)
        d["config"]["checked_on"] = "2026-12-01"
        self.assertIn("2026年12月1日時点", opening.render_fragment(d))

    def test_default_as_of_is_public_updated_on(self):
        self.assertIn(f'data-as-of="{PUBLIC["updated_on"]}"', opening.render_fragment(self.data))

    def test_forbidden_words_stop(self):
        cfg = copy.deepcopy(self.data["config"])
        cfg["lead"] = "無断学習は違法です。"
        with self.assertRaises(SystemExit):
            opening.check_words(cfg, "test")
        for w in FORBIDDEN:
            self.assertNotIn(w, opening.render_fragment(self.data))

    def test_opening_css_lives_in_redesign_folder(self):
        self.assertTrue((opening.ASSETS / "opening.css").is_file())
        self.assertFalse((ROOT / "quality/prototypes/ai-copyright-opening/opening.css").exists()
                         and (ROOT / "quality/prototypes/ai-copyright-opening/opening.css").read_text(encoding="utf-8")
                         != (opening.ASSETS / "opening.css").read_text(encoding="utf-8"))


class ReadingPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts import ai_copyright_reading as reading

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

    def test_same_input_same_output(self):
        again = self.reading.build(self.out / "b").read_text(encoding="utf-8")
        self.assertEqual(self.html, again)

    def test_default_as_of_is_public_updated_on(self):
        self.assertEqual(self.reading.default_as_of(self.d), PUBLIC["updated_on"])
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
        order = [s["id"] for s in self.d["planet"]["stances"]]
        for issue in PUBLIC["issues"]:
            panel = self.s.find(id="issue-" + issue["id"])
            self.assertIsNotNone(panel, issue["id"])
            self.assertEqual(panel.select_one(".fr-count b").get_text(), f'{int(issue["count"]):,}')
            shown = [b.get_text() for b in panel.select(".fr-stance-list b")]
            by = {s["id"]: int(s["count"]) for s in issue["stances"]}
            self.assertEqual(shown, [f"{by[sid]:,}" for sid in order])

    def test_reasons_recounted_from_reread_details(self):
        for label, rr in self.d["reread"].items():
            issue = next(i for i in PUBLIC["issues"] if i["label"] == label)
            panel = self.s.find(id="issue-" + issue["id"])
            for bid in rr["buckets"]:
                node = panel.select_one(f'li.fr-reason[data-reason="{bid}"] .fr-reason-n b')
                n = sum(1 for it in rr["items"] if it["bucket"] == bid)
                self.assertEqual(node.get_text(), f"{n:,}", (label, bid))

    def test_reason_stances_come_from_reread_details_and_sum_to_public(self):
        """区分ごとの立場は再読データの明細から数える（2026-10-11 に正典の立場へ11件合わせた）。"""
        for label, rr in self.d["reread"].items():
            issue = next(i for i in PUBLIC["issues"] if i["label"] == label)
            total = {s["id"]: 0 for s in self.d["planet"]["stances"]}
            for it in rr["items"]:
                total[self.reading.stance_id(self.d, it["stance"])] += 1
            self.assertEqual(total, {s["id"]: int(s["count"]) for s in issue["stances"]}, label)
        resync = json.loads((ROOT / "data/ai-copyright_issues-reread.json").read_text(encoding="utf-8"))["stance_resync_2026_10_11"]
        self.assertEqual(resync["count"], len(resync["items"]))

    def test_does_not_read_private_canonical(self):
        self.assertNotIn("canonical_json", self.d["cfg"])
        self.assertNotIn("canon", self.d)
        self.assertNotIn("social-samples", (ROOT / "scripts/ai_copyright_reading.py").read_text(encoding="utf-8"))

    def test_stale_reread_stance_would_stop(self):
        d = copy.deepcopy(self.d)
        label = next(iter(d["reread"]))
        item = d["reread"][label]["items"][0]
        keys = [s["key"] for s in d["planet"]["stances"]]
        item["stance"] = next(k for k in keys if k != item["stance"])
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)

    def test_issues_without_reasons_say_unpublished(self):
        no_reason = [i for i in PUBLIC["issues"] if i["label"] not in self.d["reread"]]
        self.assertTrue(no_reason)  # 現在は法制度・規制整備と利用者モラル・倫理
        for issue in no_reason:
            panel = self.s.find(id="issue-" + issue["id"])
            self.assertIsNotNone(panel.select_one("[data-unpublished]"), issue["id"])
        for label in self.d["reread"]:
            issue = next(i for i in PUBLIC["issues"] if i["label"] == label)
            self.assertIsNone(self.s.find(id="issue-" + issue["id"]).select_one("[data-unpublished]"))

    def test_unpublished_note_disappears_when_reread_is_added(self):
        d = copy.deepcopy(self.d)
        issue = next(i for i in PUBLIC["issues"] if i["label"] not in d["reread"])
        items = [{"tweet_id": str(n), "bucket": "A", "stance": "中立・情報"} for n in range(int(issue["count"]))]
        d["reread"][issue["label"]] = {"buckets": {"A": {"label": "仮の区分", "count": len(items)}}, "items": items}
        html = self.reading.render_reasons(d, issue, {})
        self.assertNotIn("data-unpublished", html)
        self.assertIn('data-reason="A"', html)

    def test_learning_data_panel_is_complete(self):
        panel = self.s.find(id="issue-ai-copyright-learning-data")
        self.assertIn("is-complete", panel["class"])
        self.assertTrue(panel.select(".fr-desc"))
        self.assertEqual(len(panel.select(".fr-voice")), len(self.d["reread"]["学習データ・無断利用"]["buckets"]))
        self.assertTrue(panel.select('.fr-check[data-check="gakushu"]'))
        self.assertTrue(panel.select('.fr-memo-check[data-memo-check="article-30-4"]'))
        self.assertTrue(panel.select('.fr-claim[data-claim="unauthorized_learning_infringement"]'))
        self.assertTrue(panel.select('.fr-sunk-item[data-sunk="ai-copyright-sc-1"]'))
        for a in panel.select(".fr-see a"):
            self.assertIsNotNone(self.s.find(id=a["href"][1:]), a["href"])

    def test_no_forbidden_words_in_handwritten_reading_text(self):
        """違法・合法は手書きの文言に使わない（共有の入力に残る分は設計記録に記録）。"""
        for issue in PUBLIC["issues"]:
            panel = self.s.find(id="issue-" + issue["id"])
            for node in panel.select(".fr-desc,.fr-reason-name,.fr-voice,.fr-post,.fr-memo-check,.fr-check h5"):
                for w in FORBIDDEN:
                    self.assertNotIn(w, node.get_text(), (issue["id"], node.get_text()[:30]))

    def test_posts_at_most_two_with_lazy_embed_and_original_links(self):
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.html)
        for panel in self.s.select(".fr-panel"):
            embeds = panel.select(".x-embed")
            self.assertLessEqual(len(embeds), 2)
            for e in embeds:
                self.assertRegex(e.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")
            self.assertEqual(len(panel.select(".fr-post")), len(embeds))

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では代表投稿の選定基準を確かめられない")
    def test_selected_posts_meet_canonical_criteria(self):
        canon = json.loads(CANON.read_text(encoding="utf-8"))
        texts = [self.reading.norm_text(x["text"]) for x in canon]
        by_id = {x["tweet_id"]: x for x in canon}
        labels = {i["id"]: i["label"] for i in PUBLIC["issues"]}
        ids = []
        for iid, icfg in self.d["cfg"]["issues"].items():
            rr = self.d["reread"].get(labels[iid])
            for p in icfg.get("posts", {}).get("items", []):
                ids.append(p["id"])
                x = by_id[p["id"]]
                c = x["classification"]
                self.assertTrue(c["is_opinion"], p["id"])
                self.assertEqual(c["main_issue"], labels[iid], p["id"])
                self.assertTrue(c["article_usable"], p["id"])
                self.assertEqual(c["risk"], "low", p["id"])
                self.assertEqual(x["url"], p["url"], p["id"])
                self.assertEqual(texts.count(self.reading.norm_text(x["text"])), 1, p["id"])
                if rr:
                    self.assertIsNotNone(self.reading.post_record(rr, p["id"]), (iid, p["id"]))
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
        posts = d["cfg"]["issues"]["ai-copyright-learning-data"]["posts"]["items"]
        posts[0]["url"] = posts[0]["url"].replace(posts[0]["id"], "1")
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)
        d = copy.deepcopy(self.d)
        posts = d["cfg"]["issues"]["ai-copyright-learning-data"]["posts"]["items"]
        posts[0]["id"] = "1"  # 再読データに無い投稿
        posts[0]["url"] = posts[0]["url"].rsplit("/", 1)[0] + "/1"
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)


class BackgroundTests(unittest.TestCase):
    """手順6：残り6論点と背景の開閉行。"""

    @classmethod
    def setUpClass(cls):
        from scripts import ai_copyright_reading as reading

        cls.reading = reading
        cls.tmp = tempfile.TemporaryDirectory()
        cls.d = reading.load()
        cls.html = reading.build(Path(cls.tmp.name) / "a").read_text(encoding="utf-8")
        cls.s = soup_of(cls.html)
        cls.bg = cls.s.select_one("#ai-copyright-background")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def render_bg(self, as_of, edit=None):
        d = copy.deepcopy(self.d)
        if edit:
            edit(d)
        import ai_copyright_background as bgmod
        return soup_of(bgmod.render(d, as_of, self.reading.ordered_issues(d))).select_one("#ai-copyright-background")

    def test_all_issues_complete_with_two_posts_of_different_stances(self):
        for iid in self.d["cfg"]["issues"]:
            panel = self.s.find(id="issue-" + iid)
            self.assertIn("is-complete", panel["class"], iid)
            self.assertTrue(panel.select(".fr-desc"), iid)
            posts = panel.select(".fr-post")
            self.assertEqual(len(posts), 2, iid)
            stances = [re.search(r"立場：([^／]+)$", p.select(".fr-fine")[-1].get_text()).group(1) for p in posts]
            self.assertEqual(len(set(stances)), 2, (iid, stances))

    def test_every_reason_bucket_has_voice(self):
        for label, rr in self.d["reread"].items():
            issue = next(i for i in PUBLIC["issues"] if i["label"] == label)
            panel = self.s.find(id="issue-" + issue["id"])
            self.assertEqual(len(panel.select(".fr-voice")), len(rr["buckets"]), label)

    def test_veins_shown_on_their_issues(self):
        for v in PUBLIC["ocean_layer"]["veins"]:
            for iid in v["issue_ids"]:
                self.assertTrue(self.s.find(id="issue-" + iid).select(f'.fr-vein[data-vein="{v["id"]}"]'), (iid, v["id"]))

    def test_rows_are_details_and_named_for_this_theme(self):
        rows = self.bg.select("details.fb-row")
        self.assertEqual([r["id"] for r in rows], ["bg-article", "bg-kangaekata", "bg-rules", "bg-timeline",
                                                   "bg-faq", "bg-classroom", "bg-unverified"])
        for r in rows:
            self.assertIsNone(r.get("open"))
        # 作り方・詳細データ・次に読む・意見の推移は手順7で継承する（背景には入れない）
        for absent in ("bg-method", "bg-table", "bg-related", "bg-trend"):
            self.assertIsNone(self.bg.find(id=absent))

    def test_checked_on_drives_time_phrases(self):
        when = opening.jp_date(self.d["ocfg"]["checked_on"])
        self.assertIn(f"{when}時点", self.bg.select_one("#bg-article").get_text())
        self.assertIn(f"{when}時点", self.bg.select_one(".fr-footer").get_text())
        d_edit = lambda d: d["ocfg"].__setitem__("checked_on", "2026-12-01")
        self.assertIn("2026年12月1日時点", self.render_bg(PUBLIC["updated_on"], d_edit).get_text())

    def test_filing_phase_switches(self):
        start = self.d["ocfg"]["principle_code"]["filing_starts_on"]
        before = self.render_bg(PUBLIC["updated_on"])
        self.assertEqual(before["data-filing-phase"], "before")
        self.assertIn("始まる予定です", before.select_one("#bg-rules").get_text())
        after = self.render_bg(start)
        self.assertEqual(after["data-filing-phase"], "after_unconfirmed")
        self.assertIn("まだ確かめていません", after.select_one('[data-event="filing"]').get_text())

        def confirm(d):
            d["ocfg"]["principle_code"]["filing_confirmed_on"] = "2026-10-27"
        done = self.render_bg("2026-10-28", confirm)
        self.assertEqual(done["data-filing-phase"], "after_confirmed")
        self.assertIn("始まりました（2026年10月27日に確認）", done.select_one("#bg-rules").get_text())
        self.assertNotIn("届出が始まったかどうか", done.select_one("#bg-unverified").get_text())
        self.assertIn("届出が始まったかどうか", before.select_one("#bg-unverified").get_text())

    def test_impossible_filing_dates_stop(self):
        def early(d):
            d["ocfg"]["principle_code"]["filing_confirmed_on"] = "2026-10-01"
        with self.assertRaises(SystemExit):
            self.render_bg("2026-10-28", early)

    def test_missing_phase_text_stops(self):
        def drop(d):
            row = next(r for g in d["bg"]["cfg"]["groups"] for r in g["rows"] if r["id"] == "rules")
            del row["phase_filing"]["after_confirmed"]
        with self.assertRaises(SystemExit):
            self.render_bg(PUBLIC["updated_on"], drop)

    def test_timeline_has_new_events_after_ledger(self):
        events = [li["data-event"] for li in self.bg.select(".fb-timeline li")]
        ledger_ids = [t["id"] for t in self.d["background"]["timeline"]]
        self.assertEqual(events[: len(ledger_ids)], ledger_ids)
        self.assertEqual(events[len(ledger_ids):], ["code-revised", "filing"])
        self.assertNotIn("最も新しい動き", self.bg.select_one("#bg-timeline").get_text())

    def test_faq_four_questions_without_opening_duplicates(self):
        qs = [dt.get_text() for dt in self.bg.select("#bg-faq dt")]
        self.assertEqual(len(qs), 4)
        for q in qs:
            self.assertNotIn("作風", q)
            self.assertNotIn("30条の4", q)

    def test_classroom_is_read_from_shared_config(self):
        cr = json.loads((ROOT / "configs/classroom/ai-copyright.json").read_text(encoding="utf-8"))
        text = self.bg.select_one("#bg-classroom").get_text()
        for r in cr["reasons_pro"] + cr["reasons_con"]:
            self.assertIn(r["text"], text)

    def test_no_forbidden_words_in_background_rows(self):
        """背景の行（共有の授業設定から読む行も含む）に違法・合法を使わない（2026-10-11 に授業の設定も言い換えた）。"""
        for row in self.bg.select("details.fb-row"):
            for w in FORBIDDEN:
                self.assertNotIn(w, row.get_text(), row["id"])

    def test_themes_yaml_mismatch_stops(self):
        def edit(d):
            d["bg"]["theme"]["updated_at"] = "2000-01-01"
        with self.assertRaises(SystemExit):
            self.render_bg(PUBLIC["updated_on"], edit)


# ---------------------------------------------------------------- 手順7：公開候補と更新経路（docs/ は書き換えない）

import shutil  # noqa: E402

from scripts import ai_copyright_layout as layout  # noqa: E402
from scripts import build_ai_copyright_redesign as redesign  # noqa: E402

AS_OF = "2026-10-11"
INPUTS = (
    "THEMES.yaml",
    "docs/data/themes/ai-copyright.json",
    "data/public/themes/ai-copyright.json",
    "data/ai-copyright_issues-reread.json",
    "data/verification/ai-copyright-claims.json",
    "data/verification/ai-copyright-background.json",
    "quality/research/ai-copyright-primary-sources.md",
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
                         "https://sns-reaction-map.jp/ai-copyright-reaction-map.html")
        self.assertEqual(len(self.s.select("h1")), 1)

    def test_ga_and_adsense_only_in_release(self):
        for name in ("GA_TAG", "ADSENSE_TAG"):
            block = protected(self.source, name)
            self.assertIn(block, self.release)
            self.assertNotIn(block, self.preview)
        self.assertIn("G-K10S4YCZFH", self.release)
        self.assertIn("ca-pub-2542211932832864", self.release)
        self.assertNotIn("ca-pub-2542211932832864", self.preview)
        self.assertIn('name="robots" content="noindex"', self.preview)
        self.assertNotIn('name="robots"', self.release)

    def test_vote_contract_is_unchanged(self):
        for text in (self.release, self.preview):
            self.assertIn(f'data-vote-topic="{redesign.VOTE_TOPIC}"', text)
            self.assertIn("var TOPIC='ai-copyright-issue-stance-v1'", text)
            for name in ("VOTE_ISSUES", "STANCES"):
                self.assertEqual(vote_block(self.source, name), vote_block(text, name), name)
            self.assertEqual(re.search(r"var V2I=\[[^\]]*\];", self.source).group(),
                             re.search(r"var V2I=\[[^\]]*\];", text).group())
            self.assertIn("choiceIdx:selIssue*STANCES.length+stanceIdx", text)
            self.assertIn("var STORAGE_KEY=window.SNS_REDESIGN_PRODUCTION?'sns_vote_ai_copyright_2step':"
                          "'sns_vote_preview_ai_copyright_2step';", text)
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
        from scripts.refresh_adapters.ai_copyright import vote_fingerprint
        self.assertEqual(vote_fingerprint(self.source), vote_fingerprint(self.release))
        self.assertEqual(vote_fingerprint(self.release)[3], 21)

    def test_faq_json_ld_matches_visible_faq(self):
        payloads = [json.loads(x.get_text()) for x in self.s.select('script[type="application/ld+json"]')]
        faq = [p for p in payloads if p.get("@type") == "FAQPage"]
        self.assertEqual(len(faq), 1)
        visible = redesign.faq_items(self.s)
        self.assertEqual(len(visible), 4)
        self.assertEqual([(q["name"], q["acceptedAnswer"]["text"]) for q in faq[0]["mainEntity"]], visible)
        self.assertEqual(sum(1 for p in payloads if p.get("@type") == "Article"), 1)
        # 旧ページの検索入口の問いは使わない
        self.assertNotIn("aic-search-entry", str(self.s.main))
        self.assertNotIn("ai-copyright-connected-page.js", self.release)

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
        self.assertIn('<time datetime="2026-06-24">', self.release)
        self.assertIn(f'<time datetime="{PUBLIC["updated_on"]}">', self.release)

    def test_trend_section_is_inherited_verbatim(self):
        block = re.search(r'<section class="update-dashboard"><!-- TREND_CARD_START -->.*?<!-- TREND_CARD_END --></section>',
                          self.source, re.S).group()
        self.assertEqual(self.release.count(block), 1)
        images = self.s.select('.trend-card img[src^="images/trend/ai-copyright-"]')
        self.assertEqual(len(images), 4)
        for img in images:
            self.assertTrue((ROOT / "docs" / img["src"]).is_file(), img["src"])
        # 埋め込みコードが外部から指す #ai-copyright-trend-panel-* はそのまま残る
        for target in ("ai-copyright-trend-panel-stance", "ai-copyright-trend-panel-issue"):
            self.assertIsNotNone(self.s.find(id=target))
        self.assertIn("/* TREND_CARD_START */", self.release)
        self.assertLess(self.release.index("TREND_CARD_START -->"), self.release.index('id="vote-section"'))

    def test_classroom_section_contract(self):
        section = self.release[self.release.index("<!-- CLASSROOM_START -->"):self.release.index("<!-- CLASSROOM_END -->")]
        self.assertIn('class="classroom-print-btn"', section)
        self.assertEqual(len(re.findall(r'href="#issue-([^"]+)"', section)), 6)
        sources = section[section.index("classroom-sources"):section.index("classroom-questions")]
        self.assertEqual(len(re.findall(r'href="(https?://[^"]+)"', sources)), 3)
        self.assertLess(self.release.index("<!-- CLASSROOM_START -->"), self.release.index("<!-- ARTICLE_TRUST_START -->"))
        for w in FORBIDDEN:
            self.assertNotIn(w, section)

    def test_old_anchor_targets_exist(self):
        for target in set(redesign.ALIASES.values()):
            self.assertIsNotNone(self.s.find(id=target), target)
        for alias in redesign.ALIASES:
            self.assertIsNone(self.s.find(id=alias), alias)  # 読み替えるのは、新ページに無いIDだけ
        for issue in PUBLIC["issues"]:
            # #issue-{論点ID} は旧ページ（論点ごとのX投稿）でも新ページ（投稿を含む読書面）でも、その論点の欄
            self.assertIsNotNone(self.src.find(id="issue-" + issue["id"]))
            self.assertEqual(self.s.find(id="issue-" + issue["id"])["data-issue-panel"], issue["id"])
            self.assertIsNotNone(self.src.find(id="fb-" + issue["id"]))
        for kept in ("vote-section", "detail-data", "related-topics", "article-trust-title", "caution", "planet-data",
                     "ai-copyright-trend"):
            self.assertIsNotNone(self.s.find(id=kept), kept)

    def test_no_legacy_widgets(self):
        for marker in ("TIDE_CARD_START", "AI_COPYRIGHT_SEARCH_ENTRY_START", "THEME_DESIGN_START",
                       "AI_COPYRIGHT_CONNECTED_START", "AI_COPYRIGHT_ISSUE_MEDIA_START", "STANCE_GLANCE_START"):
            self.assertNotIn(marker, self.release)
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.release)
        self.assertNotIn("ai-copyright-arena-data.js", self.release)
        for embed in self.s.select(".x-embed"):
            self.assertRegex(embed.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")

    def test_provenance_counts_and_detects_mismatch(self):
        from scripts.ai_copyright_redesign_provenance import verified_selectors
        result = verified_selectors(self.release, ROOT)
        self.assertEqual(len(result), len(PUBLIC["issues"]) + 1)
        node = self.s.select_one('#issue-ai-copyright-learning-data li.fr-reason .fr-reason-n b')
        broken = self.release.replace(str(node), str(node).replace(node.get_text(), str(int(node.get_text().replace(",", "")) + 1)), 1)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)

    def test_filing_phase_switch_by_as_of(self):
        """基準日で届出の段階が切り替わり、届出開始日（10/26）を過ぎても生成は止まらない。"""
        start = json.loads((ROOT / "configs/ai-copyright-opening.json").read_text(encoding="utf-8"))["principle_code"]["filing_starts_on"]
        self.assertEqual(self.s.select_one("#ai-copyright-background")["data-filing-phase"], "before")
        redesign.build(self.source_path, self.out / "after", "release", as_of="2026-10-27")
        s = soup_of((self.out / "after" / redesign.PAGE).read_text(encoding="utf-8"))
        self.assertLess(start, "2026-10-27")
        self.assertEqual(s.select_one("#ai-copyright-background")["data-filing-phase"], "after_unconfirmed")
        self.assertIn("まだ確かめていません", s.select_one('[data-event="filing"]').get_text())


class LayoutTests(unittest.TestCase):
    def _root(self, temp: str) -> Path:
        root = Path(temp)
        shutil.copytree(ROOT / "configs", root / "configs")
        shutil.copytree(ROOT / "scripts/ai_copyright_redesign", root / "scripts/ai_copyright_redesign")
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
            (root / layout.PAGE).write_text('<meta name="ai-copyright-layout">')
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
            self.assertIn(b'name="ai-copyright-layout"', first)
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
            path = root / "data/ai-copyright_issues-reread.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw["learning_data"]["items"].pop()
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            before = (root / layout.PAGE).read_bytes()
            with self.assertRaisesRegex(ValueError, "照合で停止"):
                layout.finish(root, as_of=AS_OF)
            self.assertEqual(before, (root / layout.PAGE).read_bytes())
            self.assertFalse((root / layout.SOURCE).exists())

    def test_finish_without_as_of_after_filing_start_does_not_stop(self):
        """refresh_topic の公開候補生成は as_of を渡さずに finish を呼ぶ。
        公開JSONの更新日が届出開始日（10/26）を過ぎていても、他テーマの候補生成を止めない。"""
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            (root / layout.CONFIG).write_text('{"enabled": true}')
            for rel in ("docs/data/themes/ai-copyright.json", "data/public/themes/ai-copyright.json"):
                data = json.loads((root / rel).read_text(encoding="utf-8"))
                data["updated_on"] = "2026-10-27"
                (root / rel).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            themes = (root / "THEMES.yaml").read_text(encoding="utf-8")
            block = re.search(r"\n  ai-copyright:\n(?:    .*\n)+", themes).group()
            fixed = re.sub(r"(\n    updated_at: )['\"]?[0-9-]+['\"]?", r"\g<1>2026-10-27", block, count=1)
            (root / "THEMES.yaml").write_text(themes.replace(block, fixed), encoding="utf-8")
            # 「意見の推移」の時点（保存した収集回の最新日）は更新日より前のままでも止まらない
            self.assertEqual(set(layout.finish(root)), {layout.SOURCE, layout.PAGE})
            s = soup_of((root / layout.PAGE).read_text(encoding="utf-8"))
            self.assertEqual(s.select_one("#ai-copyright-background")["data-filing-phase"], "after_unconfirmed")
        refresh = (ROOT / "scripts/refresh_topic.py").read_text(encoding="utf-8")
        self.assertEqual(refresh.count("finish_ai_copyright_layout(candidate_root)"), 2)
        self.assertEqual(refresh.count("materialize_ai_copyright(candidate_root)"), 1)
        adapter = (ROOT / "scripts/refresh_adapters/ai_copyright.py").read_text(encoding="utf-8")
        self.assertIn("current_page = source_for_refresh(root)", adapter)


if __name__ == "__main__":
    unittest.main()
