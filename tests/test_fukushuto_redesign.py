"""副首都・新デザインの試作（冒頭の時制、山なみと論点の読書面）。docs/ は書き換えない。

皇室典範改正（tests/test_koshitsu_redesign.py）の手順5・6に当たる検査。
"""
from __future__ import annotations

import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from scripts import fukushuto_reading as reading

ROOT = reading.ROOT
opening = reading.opening
PUBLIC = json.loads((ROOT / "docs/data/themes/fukushuto.json").read_text(encoding="utf-8"))
CANON = ROOT / "social-samples/fukushuto_hermes_classified.json"


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


class ReadingPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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
        again = reading.build(self.out / "b").read_text(encoding="utf-8")
        self.assertEqual(self.html, again)

    def test_default_as_of_is_public_updated_on(self):
        self.assertEqual(reading.default_as_of(self.d), PUBLIC["updated_on"])
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
        for issue in PUBLIC["issues"]:
            panel = self.s.find(id="issue-" + issue["id"])
            self.assertIsNotNone(panel, issue["id"])
            self.assertEqual(panel.select_one(".fr-count b").get_text(), f'{int(issue["count"]):,}')
            shown = [b.get_text() for b in panel.select(".fr-stance-list b")]
            order = [s["id"] for s in self.d["planet"]["stances"]]
            by = {s["id"]: int(s["count"]) for s in issue["stances"]}
            self.assertEqual(shown, [f"{by[sid]:,}" for sid in order])

    def test_reasons_recounted_from_reread_details(self):
        for label, rr in self.d["reread"].items():
            issue = next(i for i in PUBLIC["issues"] if i["label"] == label)
            panel = self.s.find(id="issue-" + issue["id"])
            for bid, b in rr["buckets"].items():
                node = panel.select_one(f'li.fr-reason[data-reason="{bid}"] .fr-reason-n b')
                n = sum(1 for it in rr["items"] if it["bucket"] == bid)
                self.assertEqual(node.get_text(), f"{n:,}", (label, bid))

    def test_issues_without_reasons_say_unpublished(self):
        no_reason = [i for i in PUBLIC["issues"] if i["label"] not in self.d["reread"]]
        self.assertTrue(no_reason)  # 現在は都構想・維新と定義・中身
        for issue in no_reason:
            panel = self.s.find(id="issue-" + issue["id"])
            self.assertIsNotNone(panel.select_one("[data-unpublished]"), issue["id"])
        for label in self.d["reread"]:
            issue = next(i for i in PUBLIC["issues"] if i["label"] == label)
            self.assertIsNone(self.s.find(id="issue-" + issue["id"]).select_one("[data-unpublished]"))

    def test_unpublished_note_disappears_when_reread_is_added(self):
        d = copy.deepcopy(self.d)
        issue = next(i for i in PUBLIC["issues"] if i["label"] not in d["reread"])
        items = [{"tweet_id": str(k), "bucket": "A", "stance": d["planet"]["stances"][0]["key"]} for k in range(int(issue["count"]))]
        d["reread"][issue["label"]] = {"buckets": {"A": {"label": "仮の区分", "count": int(issue["count"])}}, "items": items}
        html = reading.render_reasons(d, issue, {})
        self.assertNotIn("data-unpublished", html)
        self.assertIn('data-reason="A"', html)

    def test_location_panel_is_complete(self):
        panel = self.s.find(id="issue-fukushuto-location")
        self.assertIn("is-complete", panel["class"])
        self.assertTrue(panel.select(".fr-desc"))
        self.assertTrue(panel.select(".fr-voice"))
        self.assertTrue(panel.select('.fr-check[data-check="selection"]'))
        self.assertTrue(panel.select('.fr-memo-check[data-memo-check="requirements-draft"]'))
        regions = len(self.d["ocfg"]["candidates"])
        self.assertIn(f"{regions}地域", panel.select_one(".fr-see").get_text())
        self.assertEqual(panel.select_one('.fr-see a')["href"], "#fuk-op-map")
        self.assertIsNotNone(self.s.find(id="fuk-op-map"))

    def test_posts_at_most_two_with_lazy_embed_and_original_links(self):
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.html)
        for panel in self.s.select(".fr-panel"):
            embeds = panel.select(".x-embed")
            self.assertLessEqual(len(embeds), 2)
            for e in embeds:
                self.assertRegex(e.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")
            self.assertEqual(len(panel.select(".fr-post")), len(embeds))

    def test_selected_posts_are_in_reread_and_not_reused(self):
        ids = []
        for iid, icfg in self.d["cfg"]["issues"].items():
            issue = next(i for i in PUBLIC["issues"] if i["id"] == iid)
            rr = self.d["reread"].get(issue["label"])
            for p in icfg.get("posts", {}).get("items", []):
                ids.append(p["id"])
                if rr:
                    self.assertIsNotNone(reading.post_record(rr, p["id"]), (iid, p["id"]))
        self.assertEqual(len(ids), len(set(ids)))

    @unittest.skipUnless(CANON.is_file(), "非公開の正典が無い環境では確かめない")
    def test_selected_posts_meet_canonical_criteria(self):
        canon = json.loads(CANON.read_text(encoding="utf-8"))
        norm = lambda t: re.sub(r"\s+", "", t.replace("\tSTART\t", "").replace("\tEND\t", ""))
        texts = [norm(x["text"]) for x in canon]
        by_id = {x["tweet_id"]: x for x in canon}
        labels = {i["id"]: i["label"] for i in PUBLIC["issues"]}
        stance_ids = {s["key"]: s["id"] for s in self.d["planet"]["stances"]}
        for iid, icfg in self.d["cfg"]["issues"].items():
            for p in icfg.get("posts", {}).get("items", []):
                x = by_id[p["id"]]
                c = x["classification"]
                self.assertTrue(c["is_opinion"], p["id"])
                self.assertEqual(c["main_issue"], labels[iid], p["id"])
                self.assertTrue(c["article_usable"], p["id"])
                self.assertEqual(c["risk"], "low", p["id"])
                self.assertEqual(x["url"], p["url"], p["id"])
                self.assertEqual(texts.count(norm(x["text"])), 1, p["id"])
                if p.get("stance_id"):
                    self.assertEqual(stance_ids[c["stance"]], p["stance_id"], p["id"])

    def test_count_mismatch_stops(self):
        d = copy.deepcopy(self.d)
        label = next(iter(d["reread"]))
        d["reread"][label]["items"].pop()
        with self.assertRaises(SystemExit):
            reading.check_all(d)
        d = copy.deepcopy(self.d)
        d["public"]["issues"][0]["count"] += 1
        with self.assertRaises(SystemExit):
            reading.check_all(d)
        d = copy.deepcopy(self.d)
        d["public"]["trends"] = []
        with self.assertRaises(SystemExit):
            reading.check_all(d)

    def test_three_posts_or_bad_url_stop(self):
        d = copy.deepcopy(self.d)
        posts = d["cfg"]["issues"]["fukushuto-location"]["posts"]["items"]
        posts[0]["url"] = posts[0]["url"].replace(posts[0]["id"], "1")
        with self.assertRaises(SystemExit):
            reading.check_all(d)


class OpeningPhaseTests(unittest.TestCase):
    """意見募集（募集中／締め切り済み・結果未確認／結果公表）と施行（施行前／施行日を過ぎた・未確認／施行後・確認済み）。"""

    @classmethod
    def setUpClass(cls):
        cls.data = opening.load_inputs(ROOT / "configs/fukushuto-opening.json")

    def frag(self, as_of, **law_or_comment):
        data = copy.deepcopy(self.data)
        for key, value in law_or_comment.items():
            group, field = key.split("__")
            data["config"][group][field] = value
        return opening.render_fragment(data, as_of)

    def test_phases_by_as_of(self):
        law, comment = self.data["config"]["law"], self.data["config"]["comment"]
        self.assertEqual(opening.phase_of(self.data["config"], comment["closes_on"]), ("before", "open"))
        self.assertEqual(opening.phase_of(self.data["config"], "2026-10-17"), ("before", "closed"))
        self.assertEqual(opening.phase_of(self.data["config"], law["enforcement_on"]), ("after_unconfirmed", "closed"))

    def test_texts_switch(self):
        before = self.frag("2026-10-10")
        self.assertIn("10月16日まで意見募集", before)
        self.assertIn("施行予定日として示されている", before)
        closed = self.frag("2026-10-17")
        self.assertIn("結果は編集部でまだ確かめていない", closed)
        after = self.frag("2026-10-31")
        self.assertIn("施行予定でした。施行後の条文は編集部で確かめていません", after)
        self.assertIn("fop-stop--unconfirmed", after)
        confirmed = self.frag("2026-11-02", law__enforcement_confirmed_on="2026-11-01", comment__result_published_on="2026-10-30")
        self.assertIn("施行されました（2026年11月1日に条文を確認）", confirmed)
        self.assertIn("意見募集の結果が公表された", confirmed)
        self.assertNotIn("施行予定", confirmed.split('id="fuk-op-route"')[1].split("</section>")[0])

    def test_impossible_dates_stop(self):
        with self.assertRaises(SystemExit):
            self.frag("2026-10-31", law__enforcement_confirmed_on="2026-10-29")
        with self.assertRaises(SystemExit):
            self.frag("2026-10-20", law__enforcement_confirmed_on="2026-10-31")
        with self.assertRaises(SystemExit):
            self.frag("2026-10-20", comment__result_published_on="2026-10-15")

    def test_default_uses_public_updated_on(self):
        self.assertIn(f'data-as-of="{self.data["public"]["updated_on"]}"', opening.render_fragment(self.data))


if __name__ == "__main__":
    unittest.main()
