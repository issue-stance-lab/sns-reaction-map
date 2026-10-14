"""部活動の地域移行の新しい型（冒頭・読書面・背景の設定JSON化）の検査。

既存の tests/test_bukatsu_*.py（公開中の仕組み）は触らない。正典を読む検査は、正典が無い環境ではスキップする。
"""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from scripts import bukatsu_opening as opening

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "social-samples/bukatsu-chiiki_hermes_classified.json"
PUBLIC = json.loads((ROOT / "docs/data/themes/bukatsu-chiiki.json").read_text(encoding="utf-8"))


def write_config(cfg: dict) -> Path:
    tmp = Path(tempfile.mkdtemp()) / "opening.json"
    tmp.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    return tmp


class OpeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads(opening.DEFAULT_CONFIG.read_text(encoding="utf-8"))
        cls.data = opening.load_inputs()
        cls.html = opening.render_fragment(cls.data)
        cls.soup = BeautifulSoup(cls.html, "html.parser")

    def test_same_input_same_output(self):
        self.assertEqual(self.html, opening.render_fragment(opening.load_inputs()))

    def test_prototype_is_current(self):
        out = ROOT / "quality/prototypes/bukatsu-chiiki-opening/opening-fragment.html"
        self.assertEqual(out.read_text(encoding="utf-8"), self.html)

    def test_default_as_of_is_public_updated_on(self):
        self.assertEqual(self.soup.select_one(".bko")["data-as-of"], PUBLIC["updated_on"])

    def test_phase_by_as_of(self):
        cases = {"2025-06-01": "suishin", "2026-10-08": "zenki", "2029-03-31": "zenki",
                 "2029-04-01": "kouki_unchecked", "2032-04-01": "ended"}
        for as_of, phase in cases.items():
            self.assertEqual(opening.phase_of(self.cfg, as_of), phase, as_of)
        cfg = copy.deepcopy(self.cfg)
        cfg["period"]["midterm_checked_on"] = "2029-05-01"
        self.assertEqual(opening.phase_of(cfg, "2029-04-15"), "kouki_unchecked")
        self.assertEqual(opening.phase_of(cfg, "2029-06-01"), "kouki")

    def test_texts_switch_with_phase(self):
        for as_of in ("2025-06-01", "2028-05-01", "2029-06-01", "2033-01-01"):
            html = opening.render_fragment(self.data, as_of)
            phase = opening.phase_of(self.cfg, as_of)
            self.assertIn(f'data-phase="{phase}"', html)
            self.assertIn(self.cfg["phase_text"]["status_label"][phase], html)
        self.assertIn("前期の3年目", opening.render_fragment(self.data, "2028-05-01"))

    def test_h1_matches_display_headline(self):
        seo = json.loads((ROOT / "configs/theme-seo.json").read_text(encoding="utf-8"))
        entry = next(t for t in seo["themes"] if t["id"] == "bukatsu-chiiki")
        self.assertEqual(self.soup.select_one("h1").get_text(), entry["display_headline"])
        cfg = copy.deepcopy(self.cfg)
        cfg["title"]["sub"] = ["別の副題"]
        with self.assertRaises(SystemExit):
            opening.load_inputs(write_config(cfg))

    def test_checked_on_is_single_and_matches_memo(self):
        nodes = self.soup.select("[data-checked-on]")
        self.assertTrue(nodes)
        self.assertEqual({n["data-checked-on"] for n in nodes}, {self.cfg["checked_on"]})
        cfg = copy.deepcopy(self.cfg)
        cfg["checked_on"] = "2026-10-20"
        with self.assertRaises(SystemExit):
            opening.load_inputs(write_config(cfg))

    def test_period_order_stops(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["period"]["kouki_from"] = "2029-05-01"
        with self.assertRaises(SystemExit):
            opening.load_inputs(write_config(cfg))

    def test_counts_from_public_json(self):
        self.assertIn(f'{PUBLIC["opinion_count"]:,}', self.soup.select_one(".bko-poster").get_text())
        rows = self.soup.select(".bko-issue")
        self.assertEqual(len(rows), len(PUBLIC["issues"]))
        self.assertEqual(sum(int(r.select_one("b").get_text().replace("件", "").replace(",", "")) for r in rows),
                         PUBLIC["opinion_count"])
        self.assertEqual(rows[-1]["data-issue"], "bukatsu-chiiki-sonota")

    def test_no_reason_flags_only_where_reread_is_missing(self):
        flagged = {r["data-issue"] for r in self.soup.select(".bko-issue") if r.select_one(".bko-flag")}
        self.assertEqual(flagged, {"bukatsu-chiiki-kakusa", "bukatsu-chiiki-sonota"})

    def test_three_answers_keep_search_skeleton(self):
        self.assertEqual([h.get_text() for h in self.soup.select(".bko-answer h2")], ["いつから？", "費用はいくら？", "何が問題？"])
        self.assertIn("2026〜2031年度", self.soup.select_one(".bko-answer--when").get_text())
        self.assertIn("地域展開", self.soup.select_one(".bko-name-note").get_text())

    def test_midterm_shown_as_target_and_unconfirmed_after(self):
        before = BeautifulSoup(opening.render_fragment(self.data), "html.parser")
        self.assertEqual(len(before.select(".bko-step--target")), 1)
        after = BeautifulSoup(opening.render_fragment(self.data, "2029-06-01"), "html.parser")
        self.assertEqual(len(after.select(".bko-step--unconfirmed")), 1)

    def test_no_trial_wording(self):
        self.assertNotIn("試作", self.soup.get_text())


if __name__ == "__main__":
    unittest.main()
