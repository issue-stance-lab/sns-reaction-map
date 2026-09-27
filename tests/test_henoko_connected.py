import json
import re
import sys
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import henoko_connected as connected
from scripts.henoko_connected_content import END as CONTENT_END, START as CONTENT_START
from scripts.henoko_count_provenance import verified_selectors
from scripts.refresh_adapters.henoko import vote_fingerprint
from scripts.refresh_planet_section import _apply_connected_display


class HenokoConnectedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (ROOT / "docs/henoko-student-accident-reaction-map.html").read_text(encoding="utf-8")
        cls.base = re.sub(re.escape(connected.START) + r".*?" + re.escape(connected.END) + r"\n?", "", cls.original, flags=re.S)
        cls.base = re.sub(re.escape(CONTENT_START) + r".*?" + re.escape(CONTENT_END) + r"\n?", "", cls.base, flags=re.S)
        cls.base = re.sub(re.escape(connected.BRIDGE_START) + r".*?" + re.escape(connected.BRIDGE_END) + r"\n?", "", cls.base, flags=re.S)
        cls.candidate = connected.apply(cls.base, activate=True)
        cls.data = connected.planet_data(cls.base)
        cls.index = connected.content_index(cls.data)
        cls.soup = BeautifulSoup(cls.candidate, "html.parser")

    def test_activation_is_explicit_and_idempotent(self):
        self.assertNotIn(connected.START, self.base)
        self.assertEqual(self.base, connected.apply(self.base))
        self.assertEqual(self.candidate, connected.apply(self.candidate))
        self.assertEqual([], connected.validate(self.candidate))
        self.assertEqual(1, self.candidate.count("henoko-connected.css?v=1"))
        self.assertEqual(1, self.candidate.count(connected.BRIDGE_START))

    def test_mountain_chart_stretches_to_stage_width(self):
        css = (ROOT / "docs/henoko-connected.css").read_text(encoding="utf-8")
        self.assertRegex(
            css,
            r"body\.henoko-connected #planet-block \.stage\{[^}]*align-items:stretch",
        )

    def test_every_issue_has_one_reader_entry_and_no_guessed_posts(self):
        for issue in self.data["issues"]:
            iid = issue["id"]
            template = self.soup.select_one(f"#{connected.TOPIC}-reading-{iid}")
            self.assertIsNotNone(template)
            self.assertEqual(1, len(template.select("[data-henoko-post-unavailable]")))
            self.assertEqual([], template.select("[data-henoko-post-url], [data-henoko-post-id]"))

    def test_connection_order_matches_content_index(self):
        for issue in self.data["issues"]:
            iid = issue["id"]
            template = self.soup.select_one(f"#{connected.TOPIC}-reading-{iid}")
            for key, attr in (
                ("claim_ids", "data-henoko-claim"),
                ("source_only_ids", "data-henoko-source-only"),
                ("shared_concern_ids", "data-henoko-concern"),
                ("timeline_ids", "data-henoko-timeline"),
                ("check_ids", "data-henoko-check"),
                ("editorial_ids", "data-henoko-editorial"),
            ):
                self.assertEqual(
                    self.index["issues"][iid][key],
                    [node.get(attr) for node in template.select(f"[{attr}]")],
                    f"{iid} {key}",
                )

    def test_background_items_are_all_mapped(self):
        background = json.loads((ROOT / "data/verification/henoko-student-accident-background.json").read_text())
        connected_ids = {
            item_id
            for issue in self.index["issues"].values()
            for item_id in issue["timeline_ids"] + issue["check_ids"]
        }
        self.assertEqual({item["id"] for item in background["timeline"]} | {item["id"] for item in background["checklist"]["items"]}, connected_ids)

    def test_provenance_and_vote_contract(self):
        self.assertGreaterEqual(len(verified_selectors(self.candidate, ROOT)), 40)
        self.assertEqual(vote_fingerprint(self.base), vote_fingerprint(self.candidate))
        self.assertEqual(18, vote_fingerprint(self.candidate)[3])

    def test_reapply_hook_preserves_connected_page(self):
        reapplied = _apply_connected_display("henoko-student-accident", self.candidate)
        self.assertEqual(self.candidate, reapplied)

    def test_no_public_post_body_or_url_is_copied(self):
        for template in self.soup.select("template[id^='henoko-student-accident-reading-']"):
            text = template.decode_contents()
            self.assertNotIn("twitter.com/", text)
            self.assertNotIn("x.com/", text)
            self.assertNotIn("<blockquote", text)


if __name__ == "__main__":
    unittest.main()
