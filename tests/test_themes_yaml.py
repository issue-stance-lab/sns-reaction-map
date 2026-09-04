"""THEMES.yaml（登録簿）が小さいまま保たれることを確かめる。

登録簿は毎セッション読まれるので、経緯を書き足すと他の作業に使える余力が減る。
2026-09-04 に登録簿と作業記録（themes/{テーマ名}.md）を分けた（課題60）。
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class ThemesYamlTests(unittest.TestCase):
    def test_verify_themes_yaml_passes(self):
        result = subprocess.run(
            [sys.executable, "scripts/verify_themes_yaml.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_registry_stays_small(self):
        size = len((ROOT / "THEMES.yaml").read_bytes())
        self.assertLess(
            size, 20_000, f"THEMES.yaml が {size:,} バイト。経緯は themes/ へ移すこと"
        )

    def test_every_theme_has_notes_file(self):
        themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
        for name in themes:
            path = ROOT / "themes" / f"{name}.md"
            self.assertTrue(path.exists(), f"themes/{name}.md が無い")
            self.assertTrue(path.read_text(encoding="utf-8").strip(), f"themes/{name}.md が空")

    def test_verify_catches_revived_notes_field(self):
        """notes 欄を書き戻したら検査が落ちることを確かめる。

        検査そのものが効いていないと、この課題は静かに元へ戻る。
        """
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "repo"
            work.mkdir()
            (work / "scripts").mkdir()
            shutil.copy(ROOT / "scripts" / "verify_themes_yaml.py", work / "scripts")
            shutil.copytree(ROOT / "themes", work / "themes")

            text = (ROOT / "THEMES.yaml").read_text(encoding="utf-8")
            themes = yaml.safe_load(text)["themes"]
            first = next(iter(themes))
            revived = text.replace(
                f"  {first}:\n", f"  {first}:\n    notes: 経緯をここへ書き戻した\n", 1
            )
            (work / "THEMES.yaml").write_text(revived, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, "scripts/verify_themes_yaml.py"],
                cwd=work,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1, "notes を戻しても検査が通ってしまう")
            self.assertIn("notes", result.stdout)

    def test_admin_dashboard_still_reads_every_theme(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from admin_dashboard import collect

        themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
        rows = collect.collect_themes(collect.dt.date.today())
        self.assertEqual(sorted(row["key"] for row in rows), sorted(themes))
        for row in rows:
            self.assertTrue(row["title"], f"{row['key']}: タイトルが読めていない")


if __name__ == "__main__":
    unittest.main()
