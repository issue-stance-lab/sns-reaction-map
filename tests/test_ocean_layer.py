from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import verify_ocean_layer as vol  # noqa: E402


def make_sunk(items: list[dict]) -> dict:
    return {"theme_id": "t", "items": items}


def make_vein(items: list[dict]) -> dict:
    return {"theme_id": "t", "items": items}


def sunk_item(**overrides) -> dict:
    base = {
        "id": "t-sc-1",
        "primary_sources": [{"url": "https://example.com", "location": "p.1"}],
        "sns_count": 0,
        "sns_base": 100,
        "checked_on": "2026-09-02",
        "checked_by": "editorial_review",
        "match_rule": {"type": "regex", "pattern": "foo", "scope": "text", "machine_hits": ["1"]},
    }
    base.update(overrides)
    return base


def vein_item(**overrides) -> dict:
    base = {
        "id": "t-vein-1",
        "issue_ids": ["t-issue"],
        "shared_concern": "x",
        "sides": [
            {"stance_label": "a", "representative_posts": [{"tweet_id": "1"}, {"tweet_id": "2"}]},
            {"stance_label": "b", "representative_posts": [{"tweet_id": "3"}, {"tweet_id": "4"}]},
        ],
    }
    base.update(overrides)
    return base


class OceanLayerTest(unittest.TestCase):
    def test_existing_bukatsu_chiiki_files_pass(self) -> None:
        pairs = vol.find_theme_files()
        self.assertIn("bukatsu-chiiki", pairs)
        sunk_path, veins_path = pairs["bukatsu-chiiki"]
        errors, _skipped = vol.verify_sunk_continents("bukatsu-chiiki", sunk_path)
        self.assertEqual(errors, [])
        errors, _skipped = vol.verify_veins("bukatsu-chiiki", veins_path)
        self.assertEqual(errors, [])
        self.assertEqual(vol.verify_no_text_leak("bukatsu-chiiki", veins_path), [])

    def test_sunk_continents_over_four_items_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t-sunk-continents.json"
            path.write_text(json.dumps(make_sunk([sunk_item(id=f"t-sc-{i}") for i in range(5)])), encoding="utf-8")
            errors, _ = vol.verify_sunk_continents("t", path)
        self.assertTrue(any("1テーマ4件以内" in e for e in errors))

    def test_sunk_continents_missing_required_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t-sunk-continents.json"
            item = sunk_item()
            del item["checked_by"]
            path.write_text(json.dumps(make_sunk([item])), encoding="utf-8")
            errors, _ = vol.verify_sunk_continents("t", path)
        self.assertTrue(any("必須項目が欠けています" in e for e in errors))

    def test_sunk_continents_source_without_url_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t-sunk-continents.json"
            item = sunk_item(primary_sources=[{"location": "p.1"}])
            path.write_text(json.dumps(make_sunk([item])), encoding="utf-8")
            errors, _ = vol.verify_sunk_continents("t", path)
        self.assertTrue(any("URLがありません" in e for e in errors))

    def test_match_rule_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t-sunk-continents.json"
            path.write_text(json.dumps(make_sunk([sunk_item()])), encoding="utf-8")
            with mock.patch.object(vol, "run_match_rule", return_value={"9"}):
                errors, skipped = vol.verify_sunk_continents("t", path)
        self.assertEqual(skipped, [])
        self.assertTrue(any("machine_hits と一致しません" in e for e in errors))

    def test_match_rule_skipped_when_no_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t-sunk-continents.json"
            path.write_text(json.dumps(make_sunk([sunk_item()])), encoding="utf-8")
            with mock.patch.object(vol, "run_match_rule", return_value=None):
                errors, skipped = vol.verify_sunk_continents("t", path)
        self.assertEqual(errors, [])
        self.assertEqual(skipped, ["t-sc-1"])

    def test_run_match_rule_only_scans_opinion_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sample_path = Path(tmp) / "sample.json"
            sample_path.write_text(json.dumps([
                {"tweet_id": "1", "text": "foo", "classification": {"is_opinion": True}},
                {"tweet_id": "2", "text": "foo", "classification": {"is_opinion": False}},
            ]), encoding="utf-8")
            with mock.patch.object(vol, "find_sample_file", return_value="sample.json"), \
                 mock.patch.object(vol, "ROOT", Path(tmp)):
                hits = vol.run_match_rule("t", {"pattern": "foo", "scope": "text"})
        self.assertEqual(hits, {"1"})

    def test_vein_count_out_of_range_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t-veins.json"
            path.write_text(json.dumps(make_vein([vein_item()])), encoding="utf-8")
            errors, _ = vol.verify_veins("t", path)
        self.assertTrue(any("2〜4本" in e for e in errors))

    def test_vein_side_with_one_post_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t-veins.json"
            item = vein_item(sides=[
                {"stance_label": "a", "representative_posts": [{"tweet_id": "1"}]},
                {"stance_label": "b", "representative_posts": [{"tweet_id": "3"}, {"tweet_id": "4"}]},
            ])
            path.write_text(json.dumps(make_vein([item, vein_item(id="t-vein-2")])), encoding="utf-8")
            errors, _ = vol.verify_veins("t", path)
        self.assertTrue(any("代表投稿が1件で" in e for e in errors))

    def test_vein_tweet_id_not_in_canonical_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t-veins.json"
            path.write_text(json.dumps(make_vein([vein_item(), vein_item(id="t-vein-2")])), encoding="utf-8")
            with mock.patch.object(vol, "find_sample_file", return_value="sample.json"):
                sample_path = Path(tmp) / "sample.json"
                sample_path.write_text(json.dumps([{"tweet_id": "1"}]), encoding="utf-8")
                with mock.patch.object(vol, "ROOT", Path(tmp)):
                    errors, skipped = vol.verify_veins("t", path)
        self.assertFalse(skipped)
        self.assertTrue(any("正典に実在しません" in e for e in errors))

    def test_vein_existence_check_skipped_without_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t-veins.json"
            path.write_text(json.dumps(make_vein([vein_item(), vein_item(id="t-vein-2")])), encoding="utf-8")
            with mock.patch.object(vol, "find_sample_file", return_value=None):
                errors, skipped = vol.verify_veins("t", path)
        self.assertEqual(errors, [])
        self.assertTrue(skipped)

    def test_summary_in_representative_post_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t-veins.json"
            item = vein_item(sides=[
                {"stance_label": "a", "representative_posts": [
                    {"tweet_id": "1", "summary": "本文の要約"}, {"tweet_id": "2"},
                ]},
                {"stance_label": "b", "representative_posts": [{"tweet_id": "3"}, {"tweet_id": "4"}]},
            ])
            path.write_text(json.dumps(make_vein([item])), encoding="utf-8")
            errors = vol.verify_no_text_leak("t", path)
        self.assertTrue(any("summary/text が残っています" in e for e in errors))

    def test_excerpt_not_listed_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t-veins.json"
            item = vein_item(sides=[
                {"stance_label": "a", "representative_posts": [
                    {"tweet_id": "1", "excerpt": "not_listed"}, {"tweet_id": "2", "excerpt": "not_listed"},
                ]},
                {"stance_label": "b", "representative_posts": [{"tweet_id": "3"}, {"tweet_id": "4"}]},
            ])
            path.write_text(json.dumps(make_vein([item])), encoding="utf-8")
            errors = vol.verify_no_text_leak("t", path)
        self.assertEqual(errors, [])

    def test_no_pairs_found_returns_zero(self) -> None:
        with mock.patch.object(vol, "find_theme_files", return_value={}):
            with mock.patch("builtins.print"):
                self.assertEqual(vol.main(), 0)


if __name__ == "__main__":
    unittest.main()
