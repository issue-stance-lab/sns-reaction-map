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

    def test_progress_copy_describes_interactions_and_survives_regeneration(self):
        progress = self.soup.select_one("#progress > span:first-child")
        self.assertEqual(connected.PROGRESS_LABEL, progress.get_text(strip=True))
        self.assertNotIn("読んだところ", self.soup.select_one("#progress").get_text(" ", strip=True))
        self.assertIn("質問に答える・山を押す・クイズに答えると増えます", self.candidate)
        self.assertEqual(self.candidate, connected.apply(self.candidate))

    def test_progress_mechanics_remain_theme_scoped_and_unchanged(self):
        block = self.candidate.split("/* ---------- 探査記録 ----------", 1)[1].split(
            "/* ---------- 予想（見る前に当てる） ----------", 1
        )[0]
        self.assertIn("2 + issues.length", block)
        self.assertIn("sunk_continents", block)
        self.assertIn("D.claims", block)
        self.assertIn("D.ocean.veins", block)
        self.assertIn('localStorage.getItem("isa-seen-"+D.theme_id)', block)
        self.assertIn('localStorage.setItem("isa-seen-"+D.theme_id', block)
        for viewing_signal in ("scrollY", "scrollTop", "IntersectionObserver", "timeupdate"):
            self.assertNotIn(viewing_signal, block)

    def test_mountain_chart_stretches_to_stage_width(self):
        css = (ROOT / "docs/henoko-connected.css").read_text(encoding="utf-8")
        self.assertRegex(
            css,
            r"body\.henoko-connected #planet-block \.stage\{[^}]*align-items:stretch",
        )

    def test_mountain_chart_keeps_full_height_when_stretched(self):
        css = (ROOT / "docs/henoko-connected.css").read_text(encoding="utf-8")
        self.assertRegex(
            css,
            r"body\.henoko-connected #planet-block \.chart-box svg\{[^}]*height:225px;[^}]*margin-bottom:0",
        )

    def test_every_issue_has_one_reader_entry_and_no_guessed_posts(self):
        for issue in self.data["issues"]:
            iid = issue["id"]
            template = self.soup.select_one(f"#{connected.TOPIC}-reading-{iid}")
            self.assertIsNotNone(template)
            self.assertEqual([], template.select("[data-henoko-post-unavailable]"))
            self.assertEqual([], template.select("[data-henoko-post-url], [data-henoko-post-id]"))

    def test_mechanical_copy_is_removed_without_replacing_it(self):
        for phrase in connected.BANNED_USER_COPY:
            self.assertNotIn(phrase, self.candidate)
        self.assertNotIn("理由別の再読分類をまだ掲載していません", self.candidate)
        self.assertNotIn("照合した出典はありません", self.candidate)
        self.assertNotIn("まだ一次資料との突き合わせをしていません", self.candidate)
        self.assertNotIn("確かめるまで、ここは空のままにします", self.candidate)
        asset = (ROOT / "docs/henoko-connected.js").read_text(encoding="utf-8")
        self.assertNotIn("一次資料クイズは準備中です", asset)

    def test_legacy_mechanical_copy_is_removed_when_reconnected(self):
        legacy = self.candidate.replace(
            "<h3>SNS投稿の収集方法</h3>",
            "<h3>AIを使用した工程</h3><p>制作工程の説明</p><h3>SNS投稿の収集方法</h3>",
            1,
        ).replace(
            "</ul>\n  </div>\n  <p class=\"article-trust-caution\"",
            "<li>この回は分類モデルの切り替えと重なりました。内部事情です。</li></ul>\n  </div>\n  <p class=\"article-trust-caution\"",
            1,
        ).replace("（確認日 2026-09-20）", "（確認日 2026-09-20／AIの下読みを含む）", 1)
        reconnected = connected.apply(legacy)
        for phrase in connected.BANNED_USER_COPY:
            self.assertNotIn(phrase, reconnected)

    def test_counts_reread_state_and_sources_remain(self):
        # 件数は更新のたびに変わる。固定の数字ではなく、公開集計と台帳から導く。
        # 未読が0件のとき（2026-10-10の追い読み後）は、未読の別枠そのものが出ない。
        unread_counts = {issue["sub"]["unread_count"] for issue in self.data["issues"]}
        if unread_counts - {0}:
            self.assertIn("まだ読み直していない分", self.candidate)
            self.assertTrue(
                any(f"未読分{count}件は別枠で表示しています" in self.candidate for count in unread_counts),
                unread_counts,
            )
        else:
            self.assertNotIn("未読分", self.candidate)
        public = json.loads((ROOT / "data/public/themes/henoko-student-accident.json").read_text(encoding="utf-8"))
        self.assertIn(
            f"収集した{public['collected_count']}件のうち意見と判定した{public['opinion_count']}件", self.candidate
        )
        self.assertGreaterEqual(len(self.soup.select("[data-henoko-claim]")), 1)
        self.assertGreaterEqual(len(self.soup.select(".henoko-sources a")), 1)

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
