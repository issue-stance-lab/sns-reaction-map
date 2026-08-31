import json
import unittest

from scripts import public_registry_common as prc


class PublicRegistryCommonTests(unittest.TestCase):
    def test_parse_collection_period_variants(self) -> None:
        self.assertEqual(
            prc.parse_collection_period("2026-06-27〜2026-08-26"),
            {"start": "2026-06-27", "end": "2026-08-26", "status": "known"},
        )
        self.assertEqual(
            prc.parse_collection_period("2026-06-27"),
            {"start": "2026-06-27", "end": None, "status": "start_only"},
        )
        self.assertEqual(
            prc.parse_collection_period(None),
            {"start": None, "end": None, "status": "unknown"},
        )
        self.assertEqual(
            prc.parse_collection_period("unknown"),
            {"start": None, "end": None, "status": "unknown"},
        )

    def test_source_sha256_is_order_independent_and_deterministic(self) -> None:
        a = [{"tweet_id": "2", "text": "b"}, {"tweet_id": "1", "text": "a"}]
        b = [{"tweet_id": "1", "text": "a"}, {"tweet_id": "2", "text": "b"}]
        self.assertEqual(prc.source_sha256(a), prc.source_sha256(b))

    def test_source_sha256_changes_with_content(self) -> None:
        a = [{"tweet_id": "1", "text": "a"}]
        b = [{"tweet_id": "1", "text": "changed"}]
        self.assertNotEqual(prc.source_sha256(a), prc.source_sha256(b))

    def test_is_opinion_record_handles_bike_blue_ticket_exception(self) -> None:
        nested = {"classification": {"is_relevant": True, "is_opinion": True}}
        flat = {"is_relevant": True, "is_opinion": True}
        self.assertTrue(prc.is_opinion_record(nested))
        self.assertTrue(prc.is_opinion_record(flat))
        self.assertFalse(
            prc.is_opinion_record({"classification": {"is_relevant": True, "is_opinion": False}})
        )

    def test_validate_schema_rejects_unexpected_property(self) -> None:
        schema = {"type": "object", "additionalProperties": False, "properties": {"a": {"type": "string"}}}
        errors = prc.validate_schema({"a": "x", "b": "y"}, schema)
        self.assertTrue(any("b" in error for error in errors))

    def test_validate_schema_accepts_valid_instance(self) -> None:
        schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["a"],
            "properties": {"a": {"type": "string"}},
        }
        self.assertEqual(prc.validate_schema({"a": "x"}, schema), [])

    def test_check_theme_invariants_catches_broken_issue_sum(self) -> None:
        theme = {
            "theme_id": "x",
            "collected_count": 10,
            "opinion_count": 2,
            "issue_assigned_count": 2,
            "collection_period": {"start": None, "end": None, "status": "unknown"},
            "issues": [
                {
                    "id": "x-a",
                    "kind": "named",
                    "count": 3,
                    "stances": [{"id": "x-s1", "count": 1}],
                    "intensities": [{"id": "low", "count": 1}, {"id": "medium", "count": 0}, {"id": "high", "count": 0}],
                },
                {
                    "id": "x-other",
                    "kind": "other",
                    "count": 0,
                    "stances": [{"id": "x-s1", "count": 0}],
                    "intensities": [{"id": "low", "count": 0}, {"id": "medium", "count": 0}, {"id": "high", "count": 0}],
                },
            ],
        }
        errors = prc.check_theme_invariants(theme)
        self.assertTrue(errors)


class PublicRegistryCommittedOutputTests(unittest.TestCase):
    """非公開正典が無い環境でも成立する検査（verify_public_registry.py --public-only 相当）。"""

    def setUp(self) -> None:
        if not prc.PUBLIC_THEMES_DIR.exists() or not any(prc.PUBLIC_THEMES_DIR.glob("*.json")):
            self.skipTest("data/public/themes/ が未生成（段階3の生成を先に実行する）")

    def test_committed_theme_json_passes_schema_and_invariants(self) -> None:
        for theme_id, data in prc.load_theme_json_files().items():
            errors = prc.validate_public_theme(data) + prc.check_theme_invariants(data)
            self.assertEqual(errors, [], f"{theme_id}: {errors}")

    def test_committed_catalog_passes_schema_and_invariants(self) -> None:
        if not prc.PUBLIC_CATALOG_PATH.exists():
            self.skipTest("data/public/catalog.json が未生成")
        catalog = json.loads(prc.PUBLIC_CATALOG_PATH.read_text(encoding="utf-8"))
        theme_jsons = prc.load_theme_json_files()
        errors = prc.validate_public_catalog(catalog) + prc.check_catalog_invariants(catalog, theme_jsons)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
