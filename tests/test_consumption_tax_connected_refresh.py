"""ローカル正典を使い、実際の生成・部分更新・仕上げ処理を通す。"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import consumption_tax_connected as connected
from refresh_adapters import consumption_tax as adapter
from refresh_planet_section import refresh
from scripts.seo import apply_classroom_section as classroom
from scripts.seo import apply_theme_trust as trust

CANONICAL = ROOT / "social-samples/consumption-tax-cut_hermes_arena_classified.json"


class ConnectedRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not CANONICAL.exists():
            raise RuntimeError("消費税の非公開正典をOPERATIONS.mdに従って復元してください")
        cls.temp = tempfile.TemporaryDirectory(prefix="tax-connected-test-")
        cls.stage = Path(cls.temp.name)
        cls.first = cls.stage / "first.html"
        cls.run_builder("--html-template", str(ROOT / "docs/consumption-tax-cut-reaction-map.html"),
                        "--output-html", str(cls.first), "--connected-layout")
        cls.source = cls.first.read_text()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @staticmethod
    def run_builder(*args):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/build_consumption_tax_page.py"),
                                 "--input", str(CANONICAL), "--skip-issue-counts", *args],
                                cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def test_full_builder_and_adapter_tide_are_idempotent(self):
        first = self.stage / "tide-first.html"
        first.write_text(self.source)
        adapter._apply_tide(ROOT, first, ROOT / "social-samples/updates/consumption-tax-cut/2026-09-17/classified.json", "2026-09-17")
        second = self.stage / "tide-second.html"
        self.run_builder("--html-template", str(first), "--output-html", str(second))
        adapter._apply_tide(ROOT, second, ROOT / "social-samples/updates/consumption-tax-cut/2026-09-17/classified.json", "2026-09-17")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        before = (ROOT / "docs/consumption-tax-cut-reaction-map.html").read_text()
        self.assertEqual(adapter.vote_fingerprint(before), adapter.vote_fingerprint(second.read_text()))
        for token in adapter.PROTECTED:
            self.assertEqual(before.count(token), second.read_text().count(token))

    def test_all_six_partial_update_entry_points_keep_the_connection(self):
        path = self.stage / "partial.html"
        path.write_text(self.source)
        for flag in ("--claim-audit-only", "--background-only", "--issue-cards-only",
                     "--conditions-only", "--public-counts-only"):
            with self.subTest(flag=flag):
                self.run_builder(flag, "--output-html", str(path))
                first = path.read_text()
                self.run_builder(flag, "--output-html", str(path))
                self.assertEqual(path.read_text(), first)
                self.assertEqual(connected.validate(first), [])
        # 6つめは山なみ区間だけの更新。
        _, first, failures = refresh("consumption-tax-cut", source=path.read_text())
        self.assertEqual(failures, [])
        _, second, failures = refresh("consumption-tax-cut", source=first)
        self.assertEqual(first, second)
        self.assertEqual(connected.validate(second), [])

    def test_seo_classroom_and_observations_finish_the_same_candidate(self):
        config = json.loads((ROOT / "configs/theme-seo.json").read_text())
        theme = next(t for t in config["themes"] if t["id"] == connected.TOPIC)
        classroom_config = json.loads((ROOT / "configs/classroom/consumption-tax-cut.json").read_text())
        public = json.loads((ROOT / "data/public/themes/consumption-tax-cut.json").read_text())
        def finish(source):
            source = trust.apply_theme(source, theme, config)
            source = trust.apply_observations_only(source, theme)
            return classroom.apply_theme(source, connected.TOPIC, classroom_config, public)
        first = finish(self.source)
        self.assertEqual(finish(first), first)
        self.assertEqual(connected.validate(first), [])
        self.assertIn('id="classroom-title"', first)


if __name__ == "__main__":
    unittest.main()
