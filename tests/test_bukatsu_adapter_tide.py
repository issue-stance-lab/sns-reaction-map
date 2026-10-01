import json
import tempfile
import unittest
from pathlib import Path

from scripts.refresh_adapters import bukatsu


class BukatsuAdapterTideTests(unittest.TestCase):
    def test_preserves_only_existing_tide_block(self):
        old = "before<!-- TIDE_CARD_START -->old<!-- TIDE_CARD_END -->after"
        new = "new-before<!-- TIDE_CARD_START -->new<!-- TIDE_CARD_END -->new-after"
        self.assertEqual(
            "new-before<!-- TIDE_CARD_START -->old<!-- TIDE_CARD_END -->new-after",
            bukatsu._preserve_tide_block(old, new),
        )

    def test_reads_model_from_saved_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            previous = root / "social-samples/updates/bukatsu-chiiki/2026-09-22"
            stage.mkdir(parents=True)
            previous.mkdir(parents=True)
            (stage / "report.json").write_text(json.dumps({
                "provenance": {"model": {"name": "kimi-k2.7-code"}}
            }))
            (previous / "report.json").write_text(json.dumps({
                "provenance": {"model": {"name": "kimi-k2.6"}}
            }))
            (previous / "classified.json").write_text(json.dumps([
                {"tweet_id": "123"}
            ]))
            self.assertEqual("kimi-k2.7-code", bukatsu._wave_model(
                root, stage, "2026-10-01", current=True))
            self.assertEqual("kimi-k2.6", bukatsu._previous_wave_model(
                root, [{"tweet_id": "123"}]))

    def test_syncs_only_head_sample_count(self):
        description = "SNS反応1,401件で整理します"
        page = "<head>" + description * 4 + "</head><body>" + description + "</body>"
        actual = bukatsu._sync_head_sample_count(page, 1494)
        self.assertEqual(4, actual.count("SNS反応1,494件で整理します"))
        self.assertEqual(1, actual.count(description))

    def test_syncs_seo_source_description(self):
        config = {"themes": [
            {"id": "other", "description": "unchanged"},
            {"id": "bukatsu-chiiki", "description": "SNS反応1,401件で整理します"},
        ]}
        actual = bukatsu._sync_seo_sample_count(config, 1494)
        self.assertEqual("SNS反応1,494件で整理します", actual["themes"][1]["description"])


if __name__ == "__main__":
    unittest.main()
