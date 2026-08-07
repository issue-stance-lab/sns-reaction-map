import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TakaichiAdapterTests(unittest.TestCase):
    def test_changed_candidate_updates_once_then_is_idempotent(self):
        source = json.loads(
            (ROOT / "social-samples/takaichi_hermes_arena_classified.json").read_text(encoding="utf-8")
        )
        added = json.loads(json.dumps(next(
            row for row in source
            if row.get("classification", {}).get("main_issue") == "中傷動画・説明責任"
            and row.get("classification", {}).get("is_opinion")
        )))
        added["tweet_id"] = "adapter-test-only"
        added["url"] = "https://example.invalid/adapter-test-only"
        candidate = source + [added]

        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            input_path = work / "candidate.json"
            page_path = work / "page.html"
            data_path = work / "arena-data.js"
            input_path.write_text(json.dumps(candidate, ensure_ascii=False), encoding="utf-8")

            command = [
                "node", str(ROOT / "scripts/upgrade_takaichi_arena.js"),
                "--input", str(input_path),
                "--html-template", str(ROOT / "docs/takaichi-reaction-map-standard.html"),
                "--output-html", str(page_path),
                "--output-data", str(data_path),
            ]
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
            first = (digest(page_path), digest(data_path))
            page = page_path.read_text(encoding="utf-8")
            # 期待値は候補データから作る（件数をベタ書きすると更新のたびに落ちる）
            chusho = sum(
                1 for row in candidate
                if row.get("classification", {}).get("main_issue") == "中傷動画・説明責任"
                and row.get("classification", {}).get("is_opinion")
            )
            self.assertIn(f"公開投稿 {len(candidate)}件", page)
            self.assertIn(f'issue-count-takaichi-chusho">{chusho}件', page)

            command[command.index("--html-template") + 1] = str(page_path)
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
            second = (digest(page_path), digest(data_path))
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
