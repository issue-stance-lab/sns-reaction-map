"""会社運営の台帳・品質ゲート・媒体フォルダが切れないことを確かめる。"""

import json
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class CompanyOperationsTests(unittest.TestCase):
    def test_handoffs_have_required_fields_and_existing_sources(self):
        handoffs = yaml.safe_load((ROOT / "company/HANDOFFS.yaml").read_text(encoding="utf-8"))
        required = handoffs["required_fields"]
        for item in handoffs["items"]:
            for field in required:
                self.assertIn(field, item, f"{item['id']}: {field} がない")
            for source in item["canonical_sources"]:
                self.assertTrue((ROOT / source).exists(), f"{item['id']}: 正典がない: {source}")

    def test_operational_materials_are_in_channel_directories(self):
        for path in [
            "content/x/posts.md",
            "content/x/weekly-reviews.md",
            "content/note/posts.md",
            "content/note/drafts",
            "content/note/research",
            "content/website/internal",
            "content/website/research",
            "creative/brand-concepts",
            "creative/design",
            "creative/manga-prompts",
            "creative/templates",
            "quality/reviews",
            "quality/designs",
            "archive/design-system-experiment",
        ]:
            self.assertTrue((ROOT / path).exists(), f"媒体の正式な場所がない: {path}")
        for legacy in [
            "x-posts.md",
            "x-weekly-reviews.md",
            "note-posts.md",
            "note-drafts",
            "reviews",
            "brand-concepts",
            "design",
            "design-system",
            "docs-internal",
            "manga-prompts",
            "research",
            "templates",
        ]:
            self.assertFalse((ROOT / legacy).exists(), f"旧配置が残っている: {legacy}")

    def test_all_reaction_map_ogp_descriptions_avoid_two_choice_copy(self):
        for config_path in (ROOT / "configs").glob("*-reaction-map.json"):
            config = json.loads(config_path.read_text(encoding="utf-8"))
            description = config.get("ogp_description", "")
            self.assertNotIn("あなたはどっち", description, config_path.name)
            self.assertNotIn("どっちが多い", description, config_path.name)

    def test_quality_and_correction_ledgers_exist(self):
        self.assertTrue((ROOT / "company/QUALITY_GATE.md").exists())
        corrections = yaml.safe_load((ROOT / "company/CORRECTIONS.yaml").read_text(encoding="utf-8"))
        self.assertIn("items", corrections)
