import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "ai-copyright-reaction-map.html"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AiCopyrightAdapterTests(unittest.TestCase):
    def test_public_json_drives_page_level_counts(self):
        # 課題54段階2-3で本番は山なみ形式へ差し替え済み。旧アリーナの母数属性・
        # 見出し・注目ポイントは対象セクションごと撤去されており、この関数は
        # それらへ触ろうとするとエラーになるため更新自体をやめる（safe no-op、
        # elderly/build_elderly_arena.pyと同じ設計）。「調査条件」（このマップの
        # 元データ）は山なみ形式でも生きているので、そちらは引き続き貼り直される
        # ことを確かめる。
        from scripts.build_ai_copyright_arena import apply_public_counts

        source = PAGE.read_text(encoding="utf-8")
        self.assertIn("<!-- PLANET_SECTION_START -->", source)
        public_path = ROOT / "data/public/themes/ai-copyright.json"
        public = json.loads(public_path.read_text(encoding="utf-8"))
        page = apply_public_counts(source, public_path)

        self.assertIn(f'で取得した公開投稿 {public["collected_count"]}件', page)
        self.assertNotIn("data-arena-total", page)

    def _canonical(self):
        import yaml
        themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
        return ROOT / themes["ai-copyright"]["sample_file"]

    def test_changed_candidate_updates_once_then_is_idempotent(self):
        # 課題54段階2-3で本番は山なみ形式へ差し替え済み（PAGEは新テンプレ）。
        # このビルダーは山なみ形式の入力に対して旧2D形式の書き換えを一切行わない
        # 安全なno-opになる（build_ai_copyright_arena.build()のガード参照）。
        # ページ本文は入力のまま変わらず、アリーナ用の生データ（現在は未使用だが
        # 無害に更新され続ける）だけが候補件数に応じて動くことを確かめる。
        canon = self._canonical()
        if not canon.is_file():
            self.skipTest(f"非公開の正典がない環境: {canon.name}")
        source_html = PAGE.read_text(encoding="utf-8")
        self.assertIn("<!-- PLANET_SECTION_START -->", source_html)
        source = json.loads(canon.read_text(encoding="utf-8"))
        added = json.loads(json.dumps(next(
            r for r in source
            if r.get("classification", {}).get("main_issue") == "学習データ・無断利用"
            and r.get("classification", {}).get("is_opinion")
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
                sys.executable, str(ROOT / "scripts/build_ai_copyright_arena.py"),
                "--input", str(input_path),
                "--html-template", str(PAGE),
                "--output-html", str(page_path),
                "--output-data", str(data_path),
                "--skip-issue-counts",
            ]
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
            first = (digest(page_path), digest(data_path))
            self.assertEqual(page_path.read_text(encoding="utf-8"), source_html)

            command[command.index("--html-template") + 1] = str(page_path)
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
            self.assertEqual(first, (digest(page_path), digest(data_path)))

    def test_published_page_matches_canonical(self):
        if not self._canonical().is_file():
            self.skipTest("非公開の正典がない環境")
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_ai_copyright_arena.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_vote_definition_is_v1_with_21_choices(self):
        sys.path.insert(0, str(ROOT))
        from scripts.refresh_adapters.ai_copyright import VOTE_CHOICES, VOTE_TOPIC, vote_fingerprint

        topic, issues, stances, choices = vote_fingerprint(PAGE.read_text(encoding="utf-8"))
        self.assertEqual(topic, VOTE_TOPIC)
        self.assertEqual(choices, VOTE_CHOICES)
        edge = (ROOT / "supabase/functions/cast-vote/index.ts").read_text(encoding="utf-8")
        self.assertIn(f'"{VOTE_TOPIC}": {VOTE_CHOICES}', edge)


if __name__ == "__main__":
    unittest.main()
