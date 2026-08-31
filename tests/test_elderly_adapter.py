import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.build_elderly_arena import apply_public_counts, classification
from scripts.refresh_adapters import elderly
from scripts.refresh_topic import identity


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/elderly-license-revocation-reaction-map.html"


class ElderlyAdapterTests(unittest.TestCase):
    def _canonical(self) -> list[dict]:
        return json.loads(
            (ROOT / "social-samples/elderly-license_2d_classified.json").read_text(
                encoding="utf-8"
            )
        )

    def _candidate(self) -> list[dict]:
        current = self._canonical()
        current_ids = {identity(row) for row in current}
        wave = json.loads(
            (
                ROOT
                / "social-samples/updates/elderly-license-revocation/2026-08-14/classified.json"
            ).read_text(encoding="utf-8")
        )
        return current + [row for row in wave if identity(row) not in current_ids]

    def test_builder_accepts_candidate_paths_and_is_idempotent(self):
        candidate = self._candidate()
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            input_path = work / "candidate.json"
            first = work / "first.html"
            second = work / "second.html"
            input_path.write_text(
                json.dumps(candidate, ensure_ascii=False), encoding="utf-8"
            )
            command = [
                sys.executable,
                str(ROOT / "scripts/build_elderly_arena.py"),
                "--input",
                str(input_path),
                "--html-template",
                str(PAGE),
                "--output-html",
                str(first),
            ]
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
            command[command.index("--html-template") + 1] = str(first)
            command[command.index("--output-html") + 1] = str(second)
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True)

            self.assertEqual(first.read_bytes(), second.read_bytes())
            page = first.read_text(encoding="utf-8")
            # 件数は候補データから数える。ここに数字を直書きすると、データを追加した回の
            # 更新でこのテストだけが古い件数のまま落ちる（2026-08-20 の更新で実際に起きた）。
            opinions = sum(
                1 for row in candidate if classification(row).get("is_opinion") is True
            )
            self.assertIn(f"公開投稿{len(candidate)}件", page)
            self.assertIn(f"意見と判定した{opinions}件", page)

    def test_adapter_updates_tide_and_preserves_vote_contract(self):
        candidate = self._candidate()
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / "cumulative-candidate.json").write_text(
                json.dumps(candidate, ensure_ascii=False), encoding="utf-8"
            )
            targets = elderly.build(ROOT, stage, "2026-08-14")
            candidate_page = targets[elderly.PAGE].read_text(encoding="utf-8")

            self.assertIn("7月26日 → 8月14日", candidate_page)
            full_wave = json.loads(
                (
                    ROOT
                    / "social-samples/updates/elderly-license-revocation/2026-08-14/classified.json"
                ).read_text(encoding="utf-8")
            )
            tide_stances = {"義務化賛成", "条件付き賛成", "義務化反対"}
            tide_total = sum(
                1
                for row in full_wave
                if row.get("classification", {}).get("is_relevant")
                and row.get("classification", {}).get("is_opinion")
                and row.get("classification", {}).get("stance") in tide_stances
            )
            self.assertIn(f"今回収集分{tide_total}件", candidate_page)
            topic, _, _, choices = elderly.vote_fingerprint(candidate_page)
            self.assertEqual(topic, elderly.VOTE_TOPIC)
            self.assertEqual(choices, elderly.VOTE_CHOICES)

    def test_published_page_matches_canonical(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_elderly_arena.py"), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_public_counts_replace_page_aggregates(self):
        public = ROOT / "data/public/themes/elderly-license-revocation.json"
        page = apply_public_counts(PAGE.read_text(encoding="utf-8"), public)
        data = json.loads(public.read_text(encoding="utf-8"))
        self.assertIn(f'>{data["opinion_count"]}件 | セクター=論点', page)
        self.assertIn(f'公開投稿{data["collected_count"]}件', page)


if __name__ == "__main__":
    unittest.main()
