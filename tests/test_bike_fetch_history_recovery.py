import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts import build_planet_data as bpd


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "social-samples/bike-blue-ticket_2d_classified.json"
OUTPUT = ROOT / "data/verification/bike-blue-ticket-fetch-history-recovery.json"


class BikeFetchHistoryRecoveryTests(unittest.TestCase):
    def test_recovery_summary_is_current_and_does_not_publish_source_text(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_bike_fetch_history_recovery.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(data["canonical"]["missing_fetched_at"], 116)
        self.assertEqual(data["summary"], {
            "confirmed_observation": 115,
            "candidate_id_only": 1,
            "unknown": 0,
            "multiple_observation_dates": 52,
        })
        records = json.loads(CANONICAL.read_text(encoding="utf-8"))
        record_hashes = sorted(bpd.record_id_hash(record) for record in records)
        missing_hashes = sorted(
            bpd.record_id_hash(record) for record in records if not record.get("fetched_at")
        )
        self.assertEqual(
            data["canonical"]["record_id_set_sha256"],
            hashlib.sha256("\n".join(record_hashes).encode()).hexdigest(),
        )
        self.assertEqual(
            data["canonical"]["missing_fetched_at_id_set_sha256"],
            hashlib.sha256("\n".join(missing_hashes).encode()).hexdigest(),
        )
        rendered = OUTPUT.read_text(encoding="utf-8")
        first = json.loads(CANONICAL.read_text(encoding="utf-8"))[0]
        for private_value in (first["tweet_id"], first["text"], first["url"]):
            self.assertNotIn(private_value, rendered)

    def test_legacy_opinion_flag_and_confirmed_observation_are_counted(self):
        post = {
            "tweet_id": "legacy-post",
            "text": "同じ本文",
            "is_opinion": True,
            "classification": {"main_issue": "論点A"},
        }
        recovery = {
            bpd.record_id_hash(post): {
                "status": "confirmed_observation",
                "canonical_text_sha256": hashlib.sha256(post["text"].encode()).hexdigest(),
                "observations": [{"fetched_at": "2026-08-01T00:00:00Z"}],
            }
        }
        self.assertEqual(
            bpd.split_unread([post], "論点A", set(), date(2026, 8, 2), recovery),
            (1, 0),
        )

    def test_missing_flag_or_id_only_history_stops_instead_of_silently_excluding(self):
        no_flag = {"tweet_id": "no-flag", "classification": {"main_issue": "論点A"}}
        with self.assertRaises(SystemExit):
            bpd.split_unread([no_flag], "論点A", set(), date(2026, 8, 2))

        id_only = {
            "tweet_id": "id-only",
            "text": "現在の本文",
            "is_opinion": True,
            "classification": {"main_issue": "論点A"},
        }
        recovery = {
            bpd.record_id_hash(id_only): {
                "status": "candidate_id_only",
                "canonical_text_sha256": hashlib.sha256(id_only["text"].encode()).hexdigest(),
                "observations": [{"fetched_at": "2026-08-01T00:00:00Z"}],
            }
        }
        with self.assertRaises(SystemExit):
            bpd.split_unread([id_only], "論点A", set(), date(2026, 8, 2), recovery)

    def test_recovery_for_another_canonical_version_stops(self):
        with tempfile.TemporaryDirectory() as directory:
            altered = Path(directory) / "canonical.json"
            altered.write_bytes(CANONICAL.read_bytes() + b"\n")
            with self.assertRaises(SystemExit):
                bpd.load_fetch_history_recovery(OUTPUT, altered)


if __name__ == "__main__":
    unittest.main()
