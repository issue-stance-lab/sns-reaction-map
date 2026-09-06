"""収集回ごとの出所の検査が、実際に止まることを確かめる。

「検査を作らずに文書だけ直さない」がこのプロジェクトの学び。指示文の禁止事項は
別セッションで破られるので、検査が無いと同じことが起きる。ここでは
scripts/verify_update_provenance.py が、項目を1つ抜いた回で**必ず落ちる**ことを見る。
落ちなければ検査になっていない。
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import verify_update_provenance as verifier  # noqa: E402
import refresh_topic  # noqa: E402


def full_report(new: int = 5) -> dict:
    return {
        "topic": "example-topic",
        "date": "2026-09-20",
        "new": new,
        "provenance": {
            "schema_version": 1,
            "model": {"name": "kimi-k2.6", "provider": "opencode-go"} if new else None,
            "classifier": {
                "script": "scripts/classify_example_arena_hermes.py",
                "script_sha256": "a" * 64,
                "taxonomy_sha256": "b" * 64,
            },
            "input": {"raw_sha256": "c" * 64, "raw_records": 24},
            "sources": {"x": 24},
        },
    }


def write_wave(root: Path, report: dict, *, rows: list[dict] | None = None) -> tuple[Path, Path]:
    public = root / "public" / report["topic"] / report["date"]
    private = root / "private" / report["topic"] / report["date"]
    public.mkdir(parents=True, exist_ok=True)
    (public / "report.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    if rows is not None:
        private.mkdir(parents=True, exist_ok=True)
        (private / "raw.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return root / "public", root / "private"


class VerifierStopsOnMissingFields(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self._dir = tempfile.TemporaryDirectory()
        self.root = Path(self._dir.name)
        self.addCleanup(self._dir.cleanup)

    def test_complete_report_passes(self) -> None:
        public, private = write_wave(self.root, full_report())
        self.assertEqual(verifier.check(public, private, "2026-09-07"), [])

    def test_missing_provenance_stops(self) -> None:
        report = full_report()
        del report["provenance"]
        public, private = write_wave(self.root, report)
        failures = verifier.check(public, private, "2026-09-07")
        self.assertTrue(failures)
        self.assertIn("provenance がありません", failures[0])

    def test_each_missing_field_stops(self) -> None:
        """4つの記録項目のどれか1つを抜いたら、必ず落ちること。"""
        removals = [
            ("model",),
            ("classifier", "script_sha256"),
            ("classifier", "taxonomy_sha256"),
            ("input", "raw_sha256"),
            ("sources",),
        ]
        for path in removals:
            with self.subTest(field=".".join(path)):
                report = full_report()
                target = report["provenance"]
                for key in path[:-1]:
                    target = target[key]
                del target[path[-1]]
                public, private = write_wave(self.root, report)
                self.assertTrue(
                    verifier.check(public, private, "2026-09-07"),
                    f"{'.'.join(path)} を抜いても止まらなかった",
                )

    def test_empty_model_name_stops(self) -> None:
        report = full_report()
        report["provenance"]["model"] = {"name": "", "provider": "opencode-go"}
        public, private = write_wave(self.root, report)
        self.assertTrue(verifier.check(public, private, "2026-09-07"))

    def test_no_new_records_wave_needs_no_model(self) -> None:
        """新規0件の回は分類していない。走っていない分類のモデル名は書かない。"""
        public, private = write_wave(self.root, full_report(new=0))
        self.assertEqual(verifier.check(public, private, "2026-09-07"), [])

    def test_no_new_records_wave_rejects_a_model(self) -> None:
        report = full_report(new=0)
        report["provenance"]["model"] = {"name": "kimi-k2.6"}
        public, private = write_wave(self.root, report)
        self.assertTrue(verifier.check(public, private, "2026-09-07"))

    def test_zero_fetch_wave_may_have_empty_sources(self) -> None:
        """1件も取れなかった回は取得元も空になる。空が正しい回まで落とさない。"""
        report = full_report(new=0)
        report["provenance"]["input"] = {"raw_sha256": "c" * 64, "raw_records": 0}
        report["provenance"]["sources"] = {}
        public, private = write_wave(self.root, report)
        self.assertEqual(verifier.check(public, private, "2026-09-07"), [])

    def test_empty_sources_with_fetched_posts_stops(self) -> None:
        report = full_report()
        report["provenance"]["sources"] = {}
        public, private = write_wave(self.root, report)
        self.assertTrue(verifier.check(public, private, "2026-09-07"))

    def test_old_waves_are_out_of_scope(self) -> None:
        """過去の回にはこの項目が無い。さかのぼって埋めないので、対象外にする。"""
        report = full_report()
        del report["provenance"]
        report["date"] = "2026-09-01"
        public, private = write_wave(self.root, report)
        self.assertEqual(verifier.check(public, private, "2026-09-07"), [])

    def test_missing_record_fields_stop(self) -> None:
        """投稿ごとの必須項目（取得日時・検索語・取得元）が欠けたら止まること。

        自転車の青切符の116件は、これが欠けたまま通ってしまった。
        """
        rows = [
            {"tweet_id": "1", "fetched_at": "2026-09-20T10:00:00", "query": "例", "source": "x"},
            {"tweet_id": "2", "fetched_at": "2026-09-20T10:00:00", "query": "例"},
        ]
        public, private = write_wave(self.root, full_report(), rows=rows)
        failures = verifier.check(public, private, "2026-09-07")
        self.assertTrue(failures)
        self.assertIn("source 1件", failures[0])

    def test_complete_records_pass(self) -> None:
        rows = [
            {"tweet_id": "1", "fetched_at": "2026-09-20T10:00:00", "query": "例", "source": "x"},
        ]
        public, private = write_wave(self.root, full_report(), rows=rows)
        self.assertEqual(verifier.check(public, private, "2026-09-07"), [])


class RefreshTopicRecordsProvenance(unittest.TestCase):
    def test_validate_record_fields_raises(self) -> None:
        with self.assertRaises(ValueError) as caught:
            refresh_topic.validate_record_fields([{"tweet_id": "1", "query": "例"}], "テスト")
        message = str(caught.exception)
        self.assertIn("fetched_at", message)
        self.assertIn("source", message)

    def test_validate_record_fields_accepts_complete_rows(self) -> None:
        rows = [{"fetched_at": "2026-09-20T10:00:00", "query": "例", "source": "x"}]
        self.assertEqual(refresh_topic.validate_record_fields(rows, "テスト")["records"], 1)

    def test_classifier_model_reads_config(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.yaml"
            config.write_text(
                "model:\n  default: kimi-k2.6\n  provider: opencode-go\n", encoding="utf-8"
            )
            model = refresh_topic.classifier_model(config)
        self.assertEqual(model["name"], "kimi-k2.6")
        self.assertEqual(model["provider"], "opencode-go")

    def test_classifier_model_without_default_raises(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.yaml"
            config.write_text("model:\n  provider: opencode-go\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                refresh_topic.classifier_model(config)


class WriterAndVerifierAgree(unittest.TestCase):
    """書き手（refresh_topic.build_provenance）が出す形が、検査を通ること。

    ここが食い違うと、収集は走るのに毎回検査で落ちる／逆に検査が素通りする。
    """

    def test_built_provenance_passes_the_verifier(self) -> None:
        import tempfile

        classifier = ROOT / "scripts" / "classify_nickname_arena_hermes.py"
        self.assertTrue(classifier.exists(), "分類器の実物が要る")
        rows = [
            {"tweet_id": "1", "fetched_at": "2026-09-20T10:00:00", "query": "例", "source": "x"},
            {"tweet_id": "2", "fetched_at": "2026-09-20T10:00:00", "query": "例", "source": "x"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            raw_path = work / "raw.json"
            raw_path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
            config = work / "config.yaml"
            config.write_text(
                "model:\n  default: kimi-k2.6\n  provider: opencode-go\n", encoding="utf-8"
            )
            provenance = refresh_topic.build_provenance(
                ROOT, classifier, raw_path, rows, classified=True, config_path=config
            )
            self.assertEqual(provenance["model"]["name"], "kimi-k2.6")
            self.assertEqual(provenance["sources"], {"x": 2})
            self.assertEqual(len(provenance["input"]["raw_sha256"]), 64)

            report = {"topic": "t", "date": "2026-09-20", "new": 2, "provenance": provenance}
            public, private = write_wave(work, report)
            self.assertEqual(verifier.check(public, private, "2026-09-07"), [])

    def test_no_new_records_wave_leaves_model_unknown(self) -> None:
        import tempfile

        classifier = ROOT / "scripts" / "classify_nickname_arena_hermes.py"
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            raw_path = work / "raw.json"
            raw_path.write_text("[]", encoding="utf-8")
            provenance = refresh_topic.build_provenance(
                ROOT, classifier, raw_path, [], classified=False
            )
        self.assertIsNone(provenance["model"])


class RealDataPassesTheGate(unittest.TestCase):
    """実データに対しても検査が回ること。

    検査スクリプトは、誰かが手で実行しない限り回らない。単体テストから実データを
    見ておくと、必須化した日以降の回に記録漏れがあれば必ずここで落ちる。
    """

    def test_repository_waves_have_provenance(self) -> None:
        failures = verifier.check(
            verifier.PUBLIC_UPDATES, verifier.PRIVATE_UPDATES, verifier.REQUIRED_FROM
        )
        self.assertEqual(failures, [], "\n".join(failures))


class ReusedClassificationModelTests(unittest.TestCase):
    """保存済みの分類を使い回した回に、いまの設定のモデル名を書かない。

    2026-09-06 のレビュー指摘。--resume で分類を再利用すると、分類を実際に走らせたのは
    別の日なのに、現在の `~/.hermes/config.yaml` の値が「そのモデルで分類した」ように
    残っていた。段階Bが防ごうとした「どのモデルで分類したか分からない」を、
    記録のほうが誤って埋めてしまう形だった。
    """

    def _provenance(self, *, classified: bool, reused: bool) -> dict:
        # 非公開の正典は読まない。GitHub Actions には存在せず、読むと常に赤になる。
        import tempfile
        classifier = ROOT / "scripts" / "classify_bike_arena_hermes.py"
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / "raw.json"
            raw.write_text("[]", encoding="utf-8")
            config = Path(directory) / "config.yaml"
            config.write_text("model:\n  default: fixture-model\n  provider: fixture\n")
            return refresh_topic.build_provenance(
                ROOT, classifier, raw, [], classified=classified, reused=reused, config_path=config)

    def test_reused_wave_records_unknown_instead_of_current_setting(self):
        model = self._provenance(classified=True, reused=True)["model"]
        self.assertIsNotNone(model, "再利用でも model の欄そのものは残す")
        self.assertIsNone(model["name"], "現在の設定値を書かない")
        self.assertIn("再利用", model["note"])

    def test_fresh_wave_records_the_actual_model(self):
        model = self._provenance(classified=True, reused=False)["model"]
        self.assertTrue(model["name"], "実際に分類した回はモデル名を残す")

    def test_no_new_posts_records_no_model(self):
        self.assertIsNone(self._provenance(classified=False, reused=False)["model"])


class ClassificationResumeIntegration(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.stage = Path(self.temp.name)
        self.classifier = ROOT / "scripts/classify_bike_arena_hermes.py"
        self.config = self.stage / "config.yaml"
        self.config.write_text("model:\n  default: original-model\n  provider: test\n")
        self.rows = [{"tweet_id": "1", "text": "example", "source": "x"}]
        for name in ("raw.json", "new-only.json"):
            refresh_topic.write_json(self.stage / name, self.rows)

    def classify(self, resume=False):
        return refresh_topic.classify_wave(ROOT, self.classifier, self.stage, self.rows, self.rows,
            resume=resume, classifier_args=[], config_path=self.config)

    def fake_run(self, command, **kwargs):
        refresh_topic.write_json(Path(command[command.index("--output") + 1]), self.rows)

    def fresh(self):
        from unittest.mock import patch
        with patch.object(refresh_topic, "run", side_effect=self.fake_run), patch.object(refresh_topic, "validate_classified"):
            return self.classify()

    def test_fresh_resume_preserves_complete_record_with_missing_current_config(self):
        from unittest.mock import patch
        original = self.fresh()
        self.assertEqual(original["model"]["name"], "original-model")
        self.config.unlink()
        with patch.object(refresh_topic, "run", side_effect=AssertionError("must not classify")), patch.object(refresh_topic, "taxonomy_fingerprint", side_effect=AssertionError("must not read current taxonomy")):
            resumed = self.classify(True)
        self.assertEqual(original, resumed)
        self.assertEqual(verifier._missing_provenance({"new": 1, "provenance": resumed}), [])

    def test_legacy_report_without_sidecar_preserves_original(self):
        original = self.fresh()
        (self.stage / "classification-provenance.json").unlink()
        refresh_topic.write_json(self.stage / "report.json", {"provenance": original})
        self.config.write_text("model:\n  default: other-model\n")
        self.assertEqual(self.classify(True), original)

    def test_unknown_reuse_still_fails_required_gate(self):
        refresh_topic.write_json(self.stage / "classified-wave.json", self.rows)
        self.config.unlink()
        result = self.classify(True)
        self.assertIsNone(result["classifier"])
        self.assertTrue(verifier._missing_provenance({"new": 1, "provenance": result}))

    def test_changed_input_or_output_rejected(self):
        self.fresh()
        for name in ("raw.json", "new-only.json", "classified-wave.json"):
            with self.subTest(name=name):
                path = self.stage / name
                saved = path.read_bytes()
                refresh_topic.write_json(path, [{**self.rows[0], "text": "changed"}])
                with self.assertRaisesRegex(ValueError, "一致しません"):
                    self.classify(True)
                path.write_bytes(saved)

    def test_partial_result_stops_without_mixing_models(self):
        from unittest.mock import patch
        refresh_topic.write_json(self.stage / "classified-wave.json", [])
        with patch.object(refresh_topic, "run", side_effect=AssertionError("must not classify")):
            with self.assertRaisesRegex(ValueError, "分類途中"):
                self.classify(True)

    def test_changed_configuration_during_classification_invalidates_record(self):
        from unittest.mock import patch
        def changing_run(command, **kwargs):
            self.fake_run(command, **kwargs)
            self.config.write_text("model:\n  default: changed-model\n")
        with patch.object(refresh_topic, "run", side_effect=changing_run), patch.object(refresh_topic, "validate_classified"):
            with self.assertRaisesRegex(ValueError, "分類中"):
                self.classify()
        record = json.loads((self.stage / "classification-provenance.json").read_text())
        self.assertIsNone(record["model"]["name"])
        with self.assertRaisesRegex(ValueError, "未完了"):
            self.classify(True)


    def test_snapshot_exists_before_classifier_and_interrupted_output_cannot_be_reused(self):
        from unittest.mock import patch
        def interrupted(command, **kwargs):
            record = json.loads((self.stage / "classification-provenance.json").read_text())
            self.assertEqual(record["model"]["name"], "original-model")
            refresh_topic.write_json(self.stage / "classified-wave.json", self.rows)
            raise RuntimeError("interrupted")
        with patch.object(refresh_topic, "run", side_effect=interrupted):
            with self.assertRaises(RuntimeError):
                self.classify()
        with self.assertRaisesRegex(ValueError, "未完了"):
            self.classify(True)

    def test_explicit_classifier_model_is_recorded(self):
        from unittest.mock import patch
        with patch.object(refresh_topic, "run", side_effect=self.fake_run), patch.object(refresh_topic, "validate_classified"):
            result = refresh_topic.classify_wave(ROOT, self.classifier, self.stage, self.rows, self.rows,
                resume=False, classifier_args=["--model", "override-model"], config_path=self.config)
        self.assertEqual(result["model"]["name"], "override-model")
        self.assertEqual(result["model"]["config_source"], "classifier_args:--model")

    def test_multiple_archives_preserve_each_original_model(self):
        archive_root = self.stage / "archive-test"
        waves = []
        for date, model, identity in (("2026-09-19", "first", "1"), ("2026-09-20", "second", "2")):
            rows = [{"tweet_id": identity, "text": "example"}]
            waves.extend(rows)
            path = archive_root / "social-samples/updates/t" / date
            for name in ("raw.json", "classified.json"):
                refresh_topic.write_json(path / name, rows)
            refresh_topic.write_json(path / "report.json", {"new": 1, "provenance": {"model": {"name": model}}})
        stage = archive_root / "stage"
        refresh_topic.write_json(stage / "raw.json", waves)
        result = refresh_topic.prepare_archived_resume(archive_root, "t", "2026-09-20", stage, [], ["2026-09-19"])
        self.assertIsNone(result["provenance"]["model"])
        self.assertEqual([wave["provenance"]["model"]["name"] for wave in result["provenance"]["reused_waves"]], ["first", "second"])


    def test_main_refuses_unknown_post_cutoff_before_archiving(self):
        from contextlib import ExitStack
        from unittest.mock import patch
        root = self.stage / "repo"
        stage = root / ".staging/refresh/t/run"
        row = {**self.rows[0], "fetched_at": "2026-09-20T10:00:00", "query": "test"}
        for name, value in (("raw.json", [row]), ("new-only.json", [row]), ("classified-wave.json", [row])):
            refresh_topic.write_json(stage / name, value)
        refresh_topic.write_json(root / "canonical.json", [])
        (root / "config.yaml").write_text("queries: []")
        (root / "classifier.py").write_text("# fixture")
        argv = ["refresh_topic.py", "--topic", "t", "--date", "2026-09-20", "--run-id", "run", "--resume", "--backup-dest", str(self.stage / "backup")]
        with ExitStack() as stack:
            for name, value in {
                "ROOT": root,
                "parse_themes_yaml": lambda: {"t": {"sample_file": "canonical.json", "refresh_config": "config.yaml"}},
                "load_pipeline_config": lambda: {"t": {"classifier": "classifier.py"}},
                "load_queries": lambda _: [],
                "taxonomy_continuity": lambda *args: {"compatible": True},
                "record_refresh_attempt": lambda *args: None,
                "validate_classified": lambda *args: {},
                "validate_sets": lambda *args: {"new": 1},
            }.items():
                stack.enter_context(patch.object(refresh_topic, name, value))
            stack.enter_context(patch.object(sys, "argv", argv))
            archive = stack.enter_context(patch.object(refresh_topic, "archive_wave"))
            with self.assertRaisesRegex(ValueError, "出所記録が不十分"):
                refresh_topic.main()
            archive.assert_not_called()


if __name__ == "__main__":
    unittest.main()
