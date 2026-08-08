import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "social-samples/koshitsu-tenpakai_hermes_cur_20260726.json"
PAGE = ROOT / "docs/koshitsu-tenpakai-reaction-map.html"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class KoshitsuAdapterTests(unittest.TestCase):
    def test_changed_candidate_updates_once_then_is_idempotent(self):
        source = json.loads(CANON.read_text(encoding="utf-8"))
        added = json.loads(json.dumps(next(
            row for row in source
            if row.get("classification", {}).get("main_issue") == "男系vs女系"
            and row.get("classification", {}).get("is_opinion") is True
        )))
        added["tweet_id"] = "adapter-test-only"
        added["url"] = "https://example.invalid/adapter-test-only"
        candidate = source + [added]

        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            input_path = work / "candidate.json"
            page_path = work / "page.html"
            input_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")

            command = [
                sys.executable, str(ROOT / "scripts/build_koshitsu_arena.py"),
                "--input", str(input_path),
                "--html-template", str(PAGE),
                "--output-html", str(page_path),
            ]
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
            first = digest(page_path)
            page = page_path.read_text(encoding="utf-8")
            # 意見1件を足したぶんだけ最大論点の件数が増える（93 → 94）。
            # 数えるのは意見のみなので、意見と判定された投稿を足さないと動かない
            self.assertIn('issue-count-koshitsu-tenpakai-dankei">94件', page)

            command[command.index("--html-template") + 1] = str(page_path)
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
            self.assertEqual(first, digest(page_path))

    def _build_with(self, records: list[dict]) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            input_path = work / "candidate.json"
            input_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable, str(ROOT / "scripts/build_koshitsu_arena.py"),
                    "--input", str(input_path),
                    "--html-template", str(PAGE),
                    "--output-html", str(work / "page.html"),
                ],
                cwd=ROOT, capture_output=True, text=True,
            )

    def test_non_opinion_record_does_not_change_counts(self):
        """意見でない投稿（ニュース共有など）は分母に入らない。"""
        source = json.loads(CANON.read_text(encoding="utf-8"))
        added = json.loads(json.dumps(next(
            row for row in source
            if row.get("classification", {}).get("main_issue") == "男系vs女系"
        )))
        added["tweet_id"] = "not-an-opinion"
        added["url"] = "https://example.invalid/not-an-opinion"
        added["classification"]["is_opinion"] = False

        result = self._build_with(source + [added])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("収集348件 → 意見283件", result.stdout)

    def test_missing_is_opinion_stops_with_an_error(self):
        """判定が無いレコードは静かに落とさず止める（件数の食い違いを追えなくなる）。"""
        source = json.loads(CANON.read_text(encoding="utf-8"))
        broken = json.loads(json.dumps(source))
        broken[0]["classification"].pop("is_opinion")

        result = self._build_with(broken)
        self.assertEqual(result.returncode, 1)
        self.assertIn("is_opinion を持たないレコード", result.stderr)

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
