"""生成AIと著作権・新デザインの試作（冒頭、山なみと論点の読書面）。docs/ は書き換えない。

副首都（tests/test_fukushuto_redesign.py）・皇室典範改正の手順5・6に当たる検査。
読書面の生成は非公開の正典（理由区分ごとの立場と代表投稿の検査）を読むので、正典が無い環境では読書面の検査をスキップする。
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


@unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では読書面を生成できない")
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

    def test_reason_stances_come_from_canonical_and_sum_to_public(self):
        """再読データの明細の立場は古い（11件ずれ）。正典の立場で数えた内訳が公開JSONと一致する。"""
        for label, rr in self.d["reread"].items():
            issue = next(i for i in PUBLIC["issues"] if i["label"] == label)
            total = {s["id"]: 0 for s in self.d["planet"]["stances"]}
            for it in rr["items"]:
                total[self.reading.item_stance(self.d, it["tweet_id"])] += 1
            self.assertEqual(total, {s["id"]: int(s["count"]) for s in issue["stances"]}, label)

    def test_stale_reread_stance_would_stop(self):
        d = copy.deepcopy(self.d)
        label = next(iter(d["reread"]))
        tid = d["reread"][label]["items"][0]["tweet_id"]
        keys = [s["key"] for s in d["planet"]["stances"]]
        d["canon"][tid]["stance"] = next(k for k in keys if k != d["canon"][tid]["stance"])
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
        ids = [t for t, c in d["canon"].items() if c["main_issue"] == issue["label"] and c["is_opinion"]]
        items = [{"tweet_id": t, "bucket": "A"} for t in ids]
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
        pid = d["cfg"]["issues"]["ai-copyright-learning-data"]["posts"]["items"][0]["id"]
        d["canon"][pid]["risk"] = "medium"
        with self.assertRaises(SystemExit):
            self.reading.check_all(d)


if __name__ == "__main__":
    unittest.main()
