import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import refresh_completion as rc
from scripts import refresh_topic as rt


def row(key, opinion=True):
    return {"tweet_id": key, "text": f"fixture {key}", "classification": {
        "is_opinion": opinion, "is_relevant": True, "main_issue": "issue", "stance": "pro"}}


def fixture_receipt(root, topic, stage):
    """Synthetic editorial evidence, only for packaging/integration test fixtures."""
    before = rc.baseline_path(root, topic)
    if not before.exists():
        rt.write_json(before, [])
    after = rc.read(stage / "cumulative-candidate.json")
    old = rc.indexed(rc.read(before))
    rt.write_json(stage / "new-only.json", [r for k, r in rc.indexed(after).items() if k not in old])
    cfg = root / "configs/planet" / f"{topic}.yaml"
    if not cfg.exists():
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text("sub_issues: {}\n")
    source = Path("quality/reviews") / f"{topic}-fixture.json"
    rt.write_json(root / source, {"fixture": "synthetic editorial judgments"})
    proof = rc.template(root, topic, stage)
    for record in proof["records"]:
        record["review"] = {
            "kind": "editorial_body_reread", "evidence_quality": "verified",
            "read_at": "2026-10-09T12:00:00+09:00", "reviewer_type": "editorial_ai",
            "reviewer": "test-fixture", "method_version": "fixture-v1",
            "text_sha256": rc.body_hash(rc.indexed(after)[record["post_key"]]),
            "reason_sha256": hashlib.sha256(b"test judgment").hexdigest(),
            "source_file": str(source), "source_sha256": rc.sha(root / source), "bucket": "confirmed"}
    rt.write_json(stage / "editorial-completion.json", proof)
    return proof


class RefreshCompletionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / ".staging/refresh/topic/run-1"
        (self.root / "THEMES.yaml").write_text("themes:\n  topic:\n    sample_file: social-samples/topic.json\n")
        # Historical missing evidence must not force a full-history reread.
        self.before = [row(str(i)) for i in range(100)]
        self.after = self.before + [row("new"), row("excluded", False)]
        rt.write_json(self.root / "social-samples/topic.json", self.before)
        rt.write_json(self.stage / "cumulative-candidate.json", self.after)
        self.proof = fixture_receipt(self.root, "topic", self.stage)

    def save_proof(self):
        rt.write_json(self.stage / "editorial-completion.json", self.proof)

    def check(self):
        return rc.prepare_targets(self.root, "topic", self.stage, {})

    def reasons(self, include=True, excluded=False):
        cfg = self.root / "configs/planet/topic.yaml"
        cfg.write_text("sub_issues:\n  issue:\n    file: data/verification/reasons.json\n    path: [issue, buckets]\n")
        body = rc.body_hash(row("new"))
        rt.write_json(self.root / "data/verification/reasons.json", {"issue": {
            "buckets": {"a": {"label": "A", "count": int(include)}},
            "items": [{"tweet_id": "new", "bucket": "a", "text_sha256": body}] if include else [],
            "excluded_items": [{"tweet_id": "new", "reason": "no applicable reason", "text_sha256": body}]
            if excluded else []}})

    def test_under_one_percent_unreviewed_blocks_even_for_nonopinion(self):
        for key in ("new", "excluded"):
            proof = copy.deepcopy(self.proof)
            next(r for r in proof["records"] if r["post_key"] == hashlib.sha256(key.encode()).hexdigest())["review"] = None
            rt.write_json(self.stage / "editorial-completion.json", proof)
            with self.assertRaisesRegex(ValueError, "本文確認の未完了"):
                self.check()

    def test_old_backlog_does_not_block_complete_current_wave(self):
        self.reasons()
        self.assertEqual(len(self.check()), 1)

    def test_body_review_without_reason_membership_blocks(self):
        self.reasons(include=False)
        with self.assertRaisesRegex(ValueError, "理由分類・記録への反映の未完了"):
            self.check()

    def test_explicit_reason_exclusion_completes_opinion(self):
        self.reasons(include=False, excluded=True)
        self.check()

    def test_old_error_only_record_does_not_force_reclassification(self):
        self.before[0]["classification"] = {"error": "historical failure"}
        rt.write_json(self.root / "social-samples/topic.json", self.before)
        rt.write_json(self.stage / "cumulative-candidate.json", self.after)
        fixture_receipt(self.root, "topic", self.stage)
        self.check()

    def test_automated_classification_is_not_body_review(self):
        self.proof["records"][0]["review"]["kind"] = "automated_classification"
        self.save_proof()
        with self.assertRaisesRegex(ValueError, "not editorial rereading"):
            self.check()

    def test_current_reason_record_must_bind_the_reviewed_body(self):
        self.reasons()
        path = self.root / "data/verification/reasons.json"
        value = rc.read(path)
        del value["issue"]["items"][0]["text_sha256"]
        rt.write_json(path, value)
        with self.assertRaisesRegex(ValueError, "現在の本文指紋"):
            self.check()

    def test_raw_text_cannot_be_added_to_durable_receipt(self):
        self.proof["records"][0]["text"] = "must stay private"
        self.save_proof()
        with self.assertRaisesRegex(ValueError, "投稿別項目"):
            self.check()

    def test_candidate_stance_or_body_change_invalidates_evidence(self):
        for field in ("text", "stance"):
            changed = copy.deepcopy(self.after)
            if field == "text":
                changed[-2]["text"] = "changed"
            else:
                changed[-2]["classification"]["stance"] = "con"
            rt.write_json(self.stage / "cumulative-candidate.json", changed)
            with self.assertRaisesRegex(ValueError, "候補が完了記録"):
                self.check()

    def test_changed_old_classification_is_also_a_target(self):
        self.after[0]["classification"]["stance"] = "con"
        rt.write_json(self.stage / "cumulative-candidate.json", self.after)
        fresh = rc.template(self.root, "topic", self.stage)
        self.assertEqual(len(fresh["records"]), 3)
        self.assertTrue(all(r["review"] is None for r in fresh["records"]))

    def test_dropped_or_held_wave_row_cannot_disappear_from_scope(self):
        rt.write_json(self.stage / "cumulative-candidate.json", self.after[:-1])
        with self.assertRaisesRegex(ValueError, "欠落・保留"):
            rc.template(self.root, "topic", self.stage)

    def test_changed_source_or_baseline_blocks(self):
        source = self.root / self.proof["records"][0]["review"]["source_file"]
        source.write_text("changed")
        with self.assertRaisesRegex(ValueError, "出所が変更"):
            self.check()
        rt.write_json(self.root / "social-samples/topic.json", self.before[:-1])
        with self.assertRaisesRegex(ValueError, "原本・候補"):
            self.check()

    def test_duplicate_or_missing_receipt_records_block(self):
        self.proof["records"] = [self.proof["records"][0]] * 2
        self.save_proof()
        with self.assertRaisesRegex(ValueError, "追加・変更分と一致"):
            self.check()

    def test_prepare_and_apply_retain_receipt_and_recheck_evidence(self):
        self.reasons()
        rt.prepare_promotion_manifest(self.root, "topic", "2026-10-09", "run-1", self.stage, {}, {})
        _, staged = rt.load_promotion_manifest(self.root, self.stage, "topic", "2026-10-09", "run-1")
        receipt = Path("data/verification/refresh-completion/topic/run-1.json")
        self.assertIn(receipt, staged)
        with patch.object(rt, "run"), patch.object(rt, "backup_private"):
            rt.apply_manifest_targets(self.root, self.stage, staged, self.root / "backup")
        self.assertEqual(rc.read(self.root / receipt), self.proof)
        self.assertEqual(rc.read(self.root / "social-samples/topic.json"), self.after)

    def test_apply_rejects_evidence_removed_after_preparation_before_mutation(self):
        rt.prepare_promotion_manifest(self.root, "topic", "2026-10-09", "run-1", self.stage, {}, {})
        _, staged = rt.load_promotion_manifest(self.root, self.stage, "topic", "2026-10-09", "run-1")
        self.reasons(include=False)
        with self.assertRaisesRegex(ValueError, "理由分類"):
            rt.apply_manifest_targets(self.root, self.stage, staged, self.root / "backup")
        self.assertEqual(rc.read(self.root / "social-samples/topic.json"), self.before)


    def test_missing_receipt_blocks_all_promotion_entry_points(self):
        (self.stage / "editorial-completion.json").unlink()
        entry = {"topic": "topic", "stage": self.stage, "report": {}, "adapter_targets": {}, "adapter": None}
        calls = [
            lambda: rt.prepare_promotion_manifest(self.root, "topic", "2026-10-09", "run-1", self.stage, {}, {}),
            lambda: rt.prepare_public_candidate_bundle(self.root, "topic", "2026-10-09", self.stage, {}, {}, None),
            lambda: rt.prepare_public_candidate_bundle_multi(self.root, [entry], "2026-10-09", self.root / "combined"),
            lambda: rt.promote(self.root, "topic", "2026-10-09", self.stage, {}, {}, self.root / "backup"),
            lambda: rt.apply_manifest_targets(self.root, self.stage,
                {Path("social-samples/topic.json"): self.stage / "cumulative-candidate.json"}, self.root / "backup"),
        ]
        for call in calls:
            with self.subTest(call=call), self.assertRaisesRegex(ValueError, "完了記録"):
                call()
        self.assertEqual(rc.read(self.root / "social-samples/topic.json"), self.before)


class HistoricalHeadroomTests(unittest.TestCase):
    def test_warning_separates_reason_backlog_and_exact_limit(self):
        from scripts import verify_reread_headroom as headroom
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "configs/planet/topic.yaml"
            config.parent.mkdir(parents=True)
            config.write_text("sub_issues: {issue: {}}\n")
            for count, expected in ((30, "warn"), (40, "warn"), (41, "danger")):
                data = {"issues": [{"label": "issue", "count": 100,
                    "sub": {"status": "reread", "skipped_count": count, "grown_count": 0}}]}
                with patch.object(headroom, "ROOT", root), patch.object(headroom.bpd, "build", return_value=data), \
                        patch.object(headroom.bpd, "stabilize", side_effect=lambda x: x):
                    finding = headroom.topic_findings("topic")[0]
                self.assertEqual(finding["tone"], expected)
                self.assertIn("理由", finding["title"])
                self.assertNotIn("あと", finding["detail"])



if __name__ == "__main__":
    unittest.main()
