import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.refresh_adapters import takaichi
ROOT = Path(__file__).resolve().parents[1]

from scripts.refresh_topic import (
    ROOT,
    _replace_theme_fields,
    apply_manifest_targets,
    archive_wave,
    classifier_schema,
    identity,
    load_pipeline_config,
    next_collection_date,
    load_promotion_manifest,
    prepare_archived_resume,
    prepare_promotion_manifest,
    promote,
    record_collection_schedule,
    validate_sets,
    write_json,
)
from scripts.sync_portal_stats import parse_themes_yaml


def classified(tweet_id: str, issue: str = "中傷動画・説明責任") -> dict:
    return {
        "tweet_id": tweet_id,
        "url": f"https://x.com/example/status/{tweet_id}",
        "text": f"test {tweet_id}",
        "fetched_at": "2026-08-06T00:00:00+09:00",
        "classification": {
            "main_issue": issue,
            "stance": "批判・追及",
            "intensity": "medium",
            "is_relevant": True,
            "is_opinion": True,
            "summary": "説明責任を求める意見",
            "reason": "test",
            "confidence": 0.9,
            "article_usable": True,
            "risk": "low",
        },
    }


class RefreshTopicTests(unittest.TestCase):
    def test_manifest_application_uses_the_fixed_candidate_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / ".staging/refresh/topic/run-1"
            source = stage / "public-candidate/docs/index.html"
            source.parent.mkdir(parents=True)
            source.write_text("approved candidate", encoding="utf-8")
            target = root / "docs/index.html"
            target.parent.mkdir(parents=True)
            target.write_text("old public page", encoding="utf-8")

            with patch("scripts.refresh_topic.run") as mocked_run, patch(
                "scripts.refresh_topic.backup_private"
            ) as mocked_backup:
                apply_manifest_targets(
                    root,
                    stage,
                    {Path("docs/index.html"): source},
                    Path("/outside-backup"),
                )

            self.assertEqual(target.read_text(encoding="utf-8"), "approved candidate")
            # 公開反映のあとに回す検査の本数。2026-09-06 に「収集回ごとの出所」を足して6本。
            # 増減したら、検査を足し忘れ／外し忘れていないかをここで気づける。
            self.assertEqual(mocked_run.call_count, 6)
            mocked_backup.assert_called_once_with(root, Path("/outside-backup"))

    def test_promotion_manifest_binds_candidate_without_touching_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / ".staging/refresh/topic/run-1"
            write_json(stage / "cumulative-candidate.json", [classified("1")])
            candidate_page = stage / "page.html"
            candidate_page.write_text("candidate", encoding="utf-8")
            public_page = root / "docs/page.html"
            public_page.parent.mkdir(parents=True)
            public_page.write_text("public", encoding="utf-8")
            (root / "THEMES.yaml").write_text(
                "themes:\n  topic:\n    sample_file: social-samples/topic.json\n",
                encoding="utf-8",
            )

            manifest = prepare_promotion_manifest(
                root,
                "topic",
                "2026-08-29",
                "run-1",
                stage,
                {"raw": 1, "new": 1, "opinions": 1, "next_collect_at": "2026-09-12"},
                {Path("docs/page.html"): candidate_page},
            )

            self.assertEqual(public_page.read_text(encoding="utf-8"), "public")
            loaded, targets = load_promotion_manifest(root, stage, "topic", "2026-08-29", "run-1")
            self.assertEqual(loaded["manifest_sha256"], manifest["manifest_sha256"])
            self.assertEqual(targets[Path("docs/page.html")], candidate_page.resolve())

            candidate_page.write_text("changed after approval", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "承認後に公開候補が変わりました"):
                load_promotion_manifest(root, stage, "topic", "2026-08-29", "run-1")

    def test_archived_resume_preserves_wave_and_filters_against_current_canonical(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / ".staging/refresh/topic/run"
            archived = root / "social-samples/updates/topic/2026-08-14"
            current = [classified("1"), classified("2")]
            saved_wave = [classified("2"), classified("3")]
            for path, value in (
                (stage / "raw.json", saved_wave),
                (stage / "new-only.json", saved_wave),
                (stage / "classified-wave.json", saved_wave),
                (archived / "raw.json", saved_wave),
                (archived / "classified.json", saved_wave),
                (
                    archived / "report.json",
                    {"new": 2, "opinions": 2, "next_collect_at": "2026-08-21"},
                ),
            ):
                write_json(path, value)

            saved_report = prepare_archived_resume(
                root, "topic", "2026-08-14", stage, current
            )

            self.assertEqual(saved_report["new"], 2)
            self.assertEqual(
                [row["tweet_id"] for row in json.loads((stage / "new-only.json").read_text())],
                ["3"],
            )
            self.assertEqual(
                [row["tweet_id"] for row in json.loads((stage / "classified-wave.json").read_text())],
                ["3"],
            )
            self.assertEqual(
                [row["tweet_id"] for row in json.loads((archived / "classified.json").read_text())],
                ["2", "3"],
            )

    def test_all_themes_have_pipeline_refresh_config_and_classifier_schema(self):
        themes = parse_themes_yaml()
        pipelines = load_pipeline_config()
        self.assertEqual(set(themes), set(pipelines))
        for topic, theme in themes.items():
            self.assertTrue((ROOT / theme["refresh_config"]).is_file(), topic)
            classifier = ROOT / pipelines[topic]["classifier"]
            self.assertTrue(classifier.is_file(), topic)
            issues, stances = classifier_schema(classifier)
            self.assertTrue(issues, topic)
            self.assertTrue(stances, topic)

    def test_identity_uses_status_id_before_canonical_url(self):
        self.assertEqual(
            identity({"url": "https://x.com/example/status/123?ref=test"}),
            "tweet:123",
        )

    def test_common_set_invariants(self):
        current = [classified("1")]
        raw = [classified("1"), classified("2")]
        report = validate_sets(current, raw, [raw[1]], [raw[1]])
        self.assertEqual(report["duplicates"], 1)
        self.assertEqual(report["candidate"], 2)

    def test_cadence_uses_two_low_waves_and_two_zero_waves(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = root / "data/verification/updates/topic/2026-08-01/report.json"
            write_json(previous, {"new": 5, "opinions": 5})
            self.assertEqual(
                next_collection_date(root, "topic", "2026-08-10", {"new": 4, "opinions": 4}),
                "2026-09-07",
            )
            write_json(previous, {"new": 0, "opinions": 0})
            self.assertIsNone(
                next_collection_date(root, "topic", "2026-08-10", {"new": 0, "opinions": 0})
            )

    def test_cadence_uses_new_count_when_classifier_has_no_opinion_flag(self):
        """憲法改正のように is_opinion を出さないテーマでも件数ルールが効くこと。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(
                next_collection_date(
                    root,
                    "topic",
                    "2026-08-08",
                    {"new": 220, "opinions": 0, "opinion_flag_available": False},
                ),
                "2026-08-15",
            )

    def test_cadence_keeps_opinion_count_when_classifier_has_flag(self):
        """is_opinion を出すテーマで「意見0件」を新規件数で上書きしないこと。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(
                next_collection_date(
                    root,
                    "topic",
                    "2026-08-08",
                    {"new": 100, "opinions": 0, "opinion_flag_available": True},
                ),
                "2026-08-22",
            )

    def test_cadence_reads_legacy_report_without_opinion_flag(self):
        """opinion_flag_available を持たない過去回を「意見20件未満」と誤読しないこと。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            previous = root / "data/verification/updates/topic/2026-08-08/report.json"
            write_json(previous, {"new": 220, "opinions": 0})
            self.assertEqual(
                next_collection_date(
                    root,
                    "topic",
                    "2026-08-15",
                    {"new": 30, "opinions": 0, "opinion_flag_available": False},
                ),
                "2026-08-29",
            )

    def test_collection_registry_update_does_not_advance_updated_at(self):
        text = (
            "themes:\n  topic:\n    collect_at: 2026-08-04\n    refresh_at:\n"
            "    updated_at: 2026-07-26\n    collect_delta: 12\n"
        )
        changed = _replace_theme_fields(
            text,
            "topic",
            {"collect_at": "2026-08-18", "last_refresh_attempt_at": "2026-08-04"},
        )
        self.assertIn("collect_at: 2026-08-18", changed)
        self.assertIn("last_refresh_attempt_at: 2026-08-04", changed)
        self.assertIn("updated_at: 2026-07-26", changed)
        self.assertIn("collect_delta: 12", changed)

    def test_blank_registry_field_keeps_yaml_space_when_filled(self):
        text = "themes:\n  topic:\n    refresh_at:\n    collect_at: 2026-08-21\n"
        changed = _replace_theme_fields(
            text, "topic", {"refresh_at": "2026-08-21"}
        )
        self.assertIn("refresh_at: 2026-08-21", changed)

    def test_two_zero_waves_set_explicit_event_driven_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "THEMES.yaml").write_text(
                "themes:\n  topic:\n    collect_at: 2026-08-04\n    refresh_at:\n",
                encoding="utf-8",
            )
            record_collection_schedule(root, "topic", "2026-08-04", None)
            text = (root / "THEMES.yaml").read_text(encoding="utf-8")
            self.assertIn("collect_at: \n", text)
            self.assertIn("collect_mode: event-driven", text)

    def test_promotion_backup_failure_restores_public_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "configs").mkdir()
            (root / "docs").mkdir()
            (root / "social-samples").mkdir()
            (root / "THEMES.yaml").write_text(
                "themes:\n  topic:\n    title: Topic\n    html: docs/topic.html\n"
                "    sample_file: social-samples/topic.json\n    sample_period: unknown\n"
                "    sample_source: test\n    published: done\n    page_v3: done\n"
                "    collect_at: 2026-08-18\n    refresh_at: 2026-08-18\n"
                "    updated_at: 2026-07-26\n    collect_delta: 1\n",
                encoding="utf-8",
            )
            write_json(root / "configs/theme-seo.json", {"themes": [{"id": "topic", "dateModified": "2026-07-26"}]})
            original = [classified("1")]
            candidate = original + [classified("2")]
            write_json(root / "social-samples/topic.json", original)
            (root / "docs/topic.html").write_text("old page", encoding="utf-8")
            stage = root / "stage"
            write_json(stage / "cumulative-candidate.json", candidate)
            (stage / "page.html").write_text("new page", encoding="utf-8")
            original_registry = (root / "THEMES.yaml").read_text(encoding="utf-8")

            with patch("scripts.refresh_topic.run"), patch(
                "scripts.refresh_topic.backup_private", side_effect=RuntimeError("backup failed")
            ):
                with self.assertRaisesRegex(RuntimeError, "backup failed"):
                    promote(
                        root,
                        "topic",
                        "2026-08-06",
                        stage,
                        {"new": 1, "opinions": 1},
                        {Path("docs/topic.html"): stage / "page.html"},
                        root.parent / "backup",
                    )

            self.assertEqual(json.loads((root / "social-samples/topic.json").read_text()), original)
            self.assertEqual((root / "docs/topic.html").read_text(encoding="utf-8"), "old page")
            self.assertEqual((root / "THEMES.yaml").read_text(encoding="utf-8"), original_registry)

    def test_failed_backup_does_not_commit_private_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / "stage"
            write_json(stage / "raw.json", [classified("1")])
            write_json(stage / "classified-wave.json", [classified("1")])
            report = {"new": 1, "opinions": 1}

            def fail_backup(_root, _destination):
                raise RuntimeError("backup failed")

            with self.assertRaisesRegex(RuntimeError, "backup failed"):
                archive_wave(
                    root,
                    "topic",
                    "2026-08-04",
                    stage,
                    report,
                    root.parent / "backup",
                    backup_func=fail_backup,
                )
            history = root / "social-samples/updates/topic/2026-08-04"
            self.assertFalse(history.exists())

    def test_takaichi_adapter_preserves_vote_and_is_idempotent(self):
        source = json.loads(
            (ROOT / "social-samples/takaichi_hermes_arena_classified.json").read_text(encoding="utf-8")
        )
        added = classified("refresh-topic-adapter-test")
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            write_json(stage / "cumulative-candidate.json", source + [added])
            write_json(stage / "classified-wave.json", [added])
            targets = takaichi.build(ROOT, stage, "2026-08-06")
            page = targets[takaichi.PAGE].read_text(encoding="utf-8")
            self.assertEqual(
                takaichi.vote_fingerprint(page),
                takaichi.vote_fingerprint((ROOT / takaichi.PAGE).read_text(encoding="utf-8")),
            )
            self.assertIn("7月26日 → 8月6日", page)


if __name__ == "__main__":
    unittest.main()


class AdapterImportTest(unittest.TestCase):
    """`python3 scripts/refresh_topic.py` の起動形（sys.path[0] が scripts/）でも
    テーマ別adapterを読み込めること。2026-08-07 の takaichi 公開はここで落ちた。"""

    def test_adapter_loads_when_only_scripts_dir_is_on_path(self):
        for name in ("takaichi", "bukatsu", "koshitsu"):
            with self.subTest(adapter=name):
                result = subprocess.run(
                    [
                        sys.executable, "-c",
                        "import sys; sys.path.insert(0, 'scripts');"
                        f" from refresh_topic import load_adapter; load_adapter({name!r})",
                    ],
                    cwd=ROOT, capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
