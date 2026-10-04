import json
import tempfile
import unittest
from pathlib import Path

from scripts.refresh_adapters import constitutional


def _write_wave(root: Path, date: str, model: str | None) -> None:
    wave = root / "social-samples/updates/constitutional-amendment" / date
    wave.mkdir(parents=True)
    (wave / "classified.json").write_text("[]")
    provenance = {"model": {"name": model}} if model else {}
    (wave / "report.json").write_text(json.dumps({"provenance": provenance}))


class ConstitutionalAdapterTideTests(unittest.TestCase):
    def _check(self, previous_model, current_model) -> bool:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_wave(root, "2026-09-26", previous_model)
            stage = root / "stage"
            stage.mkdir()
            provenance = {"model": {"name": current_model}} if current_model else {}
            (stage / "report.json").write_text(json.dumps({"provenance": provenance}))
            return constitutional.tide_model_changed(root, stage, "2026-10-04")

    def test_model_change_keeps_previous_tide(self):
        self.assertTrue(self._check("kimi-k2.6", "kimi-k2.7-code"))

    def test_same_model_updates_tide(self):
        self.assertFalse(self._check("kimi-k2.7-code", "kimi-k2.7-code"))

    def test_unknown_model_is_not_treated_as_change(self):
        self.assertFalse(self._check(None, "kimi-k2.7-code"))


if __name__ == "__main__":
    unittest.main()
