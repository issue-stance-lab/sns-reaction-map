import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/koshitsu-tenpakai-reaction-map.html"


class KoshitsuAdapterTests(unittest.TestCase):
    def test_published_page_matches_canonical(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_koshitsu_arena.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_vote_definition_stays_v2_with_24_choices(self):
        sys.path.insert(0, str(ROOT))
        from scripts.refresh_adapters.koshitsu import VOTE_CHOICES, VOTE_TOPIC, vote_fingerprint

        topic, issues, stances, choices = vote_fingerprint(PAGE.read_text(encoding="utf-8"))
        self.assertEqual(topic, VOTE_TOPIC)
        self.assertEqual(choices, VOTE_CHOICES)
        self.assertEqual(len(issues) * len(stances), VOTE_CHOICES)

        edge = (ROOT / "supabase/functions/cast-vote/index.ts").read_text(encoding="utf-8")
        self.assertIn(f'"{VOTE_TOPIC}": {VOTE_CHOICES}', edge)


if __name__ == "__main__":
    unittest.main()
