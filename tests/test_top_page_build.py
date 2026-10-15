"""トップページ生成器（scripts/build_top_page.py）の回帰検査。

- 設定JSONと正典から生成した結果が docs/index.html と一致する（手で直した跡が無い）
- 生成後に sync_portal_stats / refresh_featured_slots を流しても差分が出ない（目印の互換）
- verify_top_page が NG 0 で通る
- 「いまの段階」が日付で切り替わる
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_top_page as btp  # noqa: E402
from refresh_featured_slots import (  # noqa: E402
    _topic_grid_metadata,
    build_card_data,
    render_feature_card,
    render_question_card,
    update_index_html,
)
from sync_portal_stats import compute_stats, parse_themes_yaml, select_featured_themes, update_html  # noqa: E402
from verify_top_page import verify_top_page  # noqa: E402

INDEX = ROOT / "docs" / "index.html"
CONFIG = ROOT / "configs" / "top-page.json"
THEMES = parse_themes_yaml(ROOT / "THEMES.yaml")
HAS_CANON = all((ROOT / theme["sample_file"]).is_file() for theme in THEMES.values() if theme["published"])


@unittest.skipUnless(HAS_CANON, "非公開の正典が無い環境では件数を数えられない")
class TopPageBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg = btp.load_config(CONFIG)
        cls.html = btp.build_html(cls.cfg)
        cls.current = INDEX.read_text(encoding="utf-8")

    def test_generated_html_matches_committed_index(self) -> None:
        self.assertEqual(self.current, self.html, "docs/index.html が生成結果と違う。scripts/build_top_page.py を実行する")

    def test_sync_portal_stats_is_noop_on_generated_html(self) -> None:
        stats = compute_stats(THEMES, ROOT, allow_synthetic=True)
        self.assertEqual(update_html(self.html, stats), self.html)

    def test_refresh_featured_slots_is_noop_on_generated_html(self) -> None:
        stats = compute_stats(THEMES, ROOT, allow_synthetic=True)
        hero_id, *question_ids = select_featured_themes(THEMES, stats)
        topic_grid = _topic_grid_metadata(self.html)
        self.assertEqual(len(topic_grid), 10, "話題のテーマ一覧の正規表現が10枚に一致しない")
        feature = render_feature_card(build_card_data(ROOT, THEMES, topic_grid, hero_id), stats["sample_counts"][hero_id])
        questions = "".join(
            render_question_card(build_card_data(ROOT, THEMES, topic_grid, tid), stats["sample_counts"][tid])
            for tid in question_ids
        )
        self.assertEqual(update_index_html(self.html, feature, questions), self.html)

    def test_verify_top_page_passes(self) -> None:
        lines, failures = verify_top_page(ROOT, fail_on_collect_deadline=False)
        self.assertEqual(failures, 0, "\n".join(line for line in lines if line.startswith("NG")))

    def test_every_published_theme_has_an_entry_card_in_config_order(self) -> None:
        order = [entry["theme_id"] for entry in self.cfg["entries"]]
        positions = [self.html.index(f'class="entry-card" data-theme="{tid}"') for tid in order]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(len(order), 10)

    def test_entry_answers_do_not_carry_counts_or_percent(self) -> None:
        for entry in self.cfg["entries"]:
            with self.subTest(theme=entry["theme_id"]):
                self.assertNotRegex(entry["answer"], r"\d[\d,]*\s*件")
                self.assertNotRegex(entry["answer"], r"\d{1,3}%")

    def test_folded_sections_keep_required_markers(self) -> None:
        for marker in (
            'id="topic-atlas-overview"',
            'id="topic-atlas-title"',
            "topic-atlas-rows",
            "10テーマの論点アトラス",
            "home-story.css",
            'id="hero-map"',
            "世論調査ではありません",
            "fn.id=countEl.id.replace('topic-count-','topic-delta-')",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.html)
        self.assertLess(self.html.index("世論調査ではありません"), self.html.index('class="hero-stats'))

    def test_build_is_idempotent(self) -> None:
        self.assertEqual(btp.build_html(self.cfg), self.html)


class PhaseRuleTest(unittest.TestCase):
    def test_koshitsu_phase_switches_at_enforcement(self) -> None:
        cfg = json.loads((ROOT / "configs" / "koshitsu-tenpakai-opening.json").read_text(encoding="utf-8"))
        enforce = date.fromisoformat(cfg["law"]["enforcement_on"])
        before = btp.phase_text("koshitsu-tenpakai", {"rule": "koshitsu-tenpakai"}, date(enforce.year, enforce.month, enforce.day - 1))
        after = btp.phase_text("koshitsu-tenpakai", {"rule": "koshitsu-tenpakai"}, date(enforce.year, enforce.month, enforce.day))
        self.assertIn(f"{enforce.month}月{enforce.day}日に施行", before)
        if cfg["law"].get("enforcement_confirmed_on"):
            self.assertIn("施行済み", after)
        else:
            self.assertIn("未確認", after)

    def test_consumption_tax_phase_reads_enactment(self) -> None:
        cfg = json.loads((ROOT / "configs" / "consumption-tax-cut-opening.json").read_text(encoding="utf-8"))
        text = btp.phase_text("consumption-tax-cut", {"rule": "consumption-tax-cut"}, date.fromisoformat(cfg["checked_on"]))
        if cfg["law"].get("enacted_on"):
            self.assertNotIn("審議中", text)
        else:
            self.assertIn("審議中", text)

    def test_static_phase_is_returned_verbatim(self) -> None:
        self.assertEqual(btp.phase_text("x", {"static": "そのまま"}, date(2026, 10, 15)), "そのまま")

    def test_unknown_rule_fails(self) -> None:
        with self.assertRaises(btp.TopPageError):
            btp.phase_text("x", {"rule": "nope"}, date(2026, 10, 15))


if __name__ == "__main__":
    unittest.main()
