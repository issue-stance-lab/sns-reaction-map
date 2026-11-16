"""定期収集の本文確認道具（scripts/wave_review）が全テーマの設定を読めることを確かめる。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "wave_review"))
import wave_review as wr  # noqa: E402

PRIVATE = (ROOT / "THEMES.yaml").exists() and all(
    (ROOT / yaml.safe_load((ROOT / "THEMES.yaml").read_text())["themes"][t]["sample_file"]).exists()
    for t in ("fukushuto",))


class WaveReviewTests(unittest.TestCase):
    def test_risky_reader_note_excludes_representative_post(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            stage, work = root / "stage", root / "work"
            stage.mkdir()
            work.mkdir()
            (root / "data/verification").mkdir(parents=True)
            (root / "quality/reviews").mkdir(parents=True)
            row = {"tweet_id": "1", "text": "本文", "classification": {
                "is_opinion": True, "main_issue": "その他", "stance": "未表明", "article_usable": True}}
            (stage / "new-only.json").write_text(json.dumps([row]))
            (stage / "classified-wave.json").write_text(json.dumps([row]))
            adjudicated = [{"index": 0, "tweet_id": "1", "agree": True, "is_opinion": True,
                            "main_issue": "その他", "stance": "未表明", "bucket": None,
                            "summary": "本文の要約", "notes": ["根拠不明の動機推測"]}]
            (work / "adjudicated.json").write_text(json.dumps(adjudicated, ensure_ascii=False))
            theme = SimpleNamespace(topic="example", sub={}, files={}, neutral="未表明")
            args = SimpleNamespace(stage=str(stage), work=str(work), date="2026-11-16")
            with patch.object(wr, "ROOT", root):
                wr.cmd_apply(args, theme)
            saved = json.loads((root / "data/verification/example-wave-review-20261116.json").read_text())
            self.assertFalse(saved["overrides"][0]["classification"]["article_usable"])

    def test_every_planet_theme_loads(self):
        for cfg in sorted((ROOT / "configs/planet").glob("*.yaml")):
            topic = cfg.stem
            theme = wr.Theme(topic)
            self.assertIn("その他", theme.issues, topic)
            self.assertTrue(theme.stances, topic)
            for issue in theme.sub:
                self.assertTrue(theme.buckets(issue), f"{topic}/{issue}: 理由区分が空")
                self.assertIsInstance(theme.items_of(issue), list, f"{topic}/{issue}")

    def test_prompt_renders_without_placeholders(self):
        for cfg in sorted((ROOT / "configs/planet").glob("*.yaml")):
            theme = wr.Theme(cfg.stem)
            text = wr.render_prompt(theme, Path("/tmp/in.json"), Path("/tmp/out.json"))
            self.assertNotRegex(text, r"\{[A-Z_]+\}", cfg.stem)
            self.assertIn("new_issue_candidate", text)

    def test_reader_guides_match_planet_config(self):
        for guide in sorted((ROOT / "configs/wave_review").glob("*.yaml")):
            self.assertTrue((ROOT / "configs/planet" / guide.name).exists(), guide.name)
            data = yaml.safe_load(guide.read_text())
            for key in ("title", "opinion_guide", "issue_guide", "stance_guide"):
                self.assertTrue(data.get(key), f"{guide.name}: {key}")

    def test_decide_rejects_unknown_bucket(self):
        theme = wr.Theme("constitutional-amendment")
        issue = next(iter(theme.sub))
        with tempfile.TemporaryDirectory() as d:
            work = Path(d)
            adj = [{"index": 0, "tweet_id": "1", "agree": True, "is_opinion": True, "main_issue": issue,
                    "stance": theme.stances[0], "bucket": "no-such-bucket", "bucket_choices": [], "exclude_kind": None,
                    "summary": "x", "summary_b": "x", "kimi": {}, "new_issue": [], "notes": []}]
            (work / "adjudicated.json").write_text(json.dumps(adj))
            (work / "decisions.json").write_text("{}")
            ns = type("A", (), {"work": str(work), "decisions": str(work / "decisions.json")})()
            with self.assertRaises(SystemExit):
                wr.cmd_decide(ns, theme)
            good = {"0": {"bucket": next(iter(theme.buckets(issue)))}}
            (work / "decisions.json").write_text(json.dumps(good))
            wr.cmd_decide(ns, theme)
            saved = json.loads((work / "adjudicated.json").read_text())
            self.assertEqual(saved[0]["bucket"], next(iter(theme.buckets(issue))))


if __name__ == "__main__":
    unittest.main()
