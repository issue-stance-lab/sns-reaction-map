import json
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class PublicDataContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.taxonomy = json.loads(
            (ROOT / "configs/public-data-taxonomy.json").read_text(encoding="utf-8")
        )["themes"]
        cls.themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]

    def test_taxonomy_matches_exactly_the_public_theme_set(self) -> None:
        public = {slug for slug, item in self.themes.items() if item.get("published") == "done"}
        self.assertEqual(set(self.taxonomy), public)

    def test_every_theme_has_one_other_and_unique_prefixed_ids(self) -> None:
        for slug, item in self.taxonomy.items():
            issues = item["issues"]
            stances = item["stances"]
            self.assertEqual(sum(value["kind"] == "other" for value in issues.values()), 1, slug)
            self.assertEqual(len({value["id"] for value in issues.values()}), len(issues), slug)
            self.assertEqual(len({value["id"] for value in stances.values()}), len(stances), slug)
            for value in [*issues.values(), *stances.values()]:
                self.assertTrue(value["id"].startswith(f"{slug}-"), (slug, value["id"]))

    def test_hash_fields_explain_their_different_targets(self) -> None:
        theme_schema = json.loads(
            (ROOT / "schemas/public-theme.schema.json").read_text(encoding="utf-8")
        )
        catalog_schema = json.loads(
            (ROOT / "schemas/public-catalog.schema.json").read_text(encoding="utf-8")
        )
        source_note = theme_schema["properties"]["source_sha256"]["description"]
        data_note = catalog_schema["properties"]["themes"]["items"]["properties"]["data_sha256"]["description"]
        self.assertIn("非公開正典", source_note)
        self.assertIn("公開テーマJSON", data_note)


if __name__ == "__main__":
    unittest.main()
