import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.refresh_adapters import fukushuto


class FukuShutoWaveReviewTest(unittest.TestCase):
    def test_review_changes_candidate_without_changing_archived_wave(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            stage = root / "stage"
            stage.mkdir()
            (root / "data/verification").mkdir(parents=True)
            old = {"tweet_id": "1", "classification": {"is_opinion": True}}
            new = {"tweet_id": "2", "classification": {"is_opinion": True, "stance": "法案賛成・推進"}}
            wave = [new]
            wave_path = stage / "classified-wave.json"
            wave_path.write_text(json.dumps(wave), encoding="utf-8")
            original = wave_path.read_bytes()
            (stage / "cumulative-candidate.json").write_text(json.dumps([old, new]), encoding="utf-8")
            review = {
                "source_sha256": hashlib.sha256(original).hexdigest(),
                "ids_sha256": hashlib.sha256(b"2").hexdigest(),
                "reviewed_count": 1,
                "overrides": [{
                    "tweet_id": "2",
                    "review_reason": "賛成を述べていない",
                    "classification": {"stance": "中立・情報"},
                }],
            }
            (root / fukushuto.REVIEW_RECORDS).write_text(json.dumps(review), encoding="utf-8")
            report = {"opinions": 1}

            fukushuto.review_candidate(root, stage, "2026-10-03", report)

            self.assertEqual(wave_path.read_bytes(), original)
            cumulative = json.loads((stage / "cumulative-candidate.json").read_text())
            self.assertEqual(cumulative[0], old)
            self.assertEqual(cumulative[1]["classification"]["stance"], "中立・情報")
            self.assertEqual(json.loads((stage / "reviewed-wave.json").read_text())[0]["classification"]["stance"], "中立・情報")
            self.assertEqual(report["body_review_changes"], 1)

    def test_review_rejects_changed_source(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            stage = root / "stage"
            stage.mkdir()
            (root / "data/verification").mkdir(parents=True)
            (root / fukushuto.REVIEW_RECORDS).write_text(json.dumps({"source_sha256": "wrong"}), encoding="utf-8")
            (stage / "classified-wave.json").write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "保存回が一致"):
                fukushuto.review_candidate(root, stage, "2026-10-03", {"opinions": 0})


if __name__ == "__main__":
    unittest.main()
