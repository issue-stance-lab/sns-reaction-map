import glob
import importlib
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

MODULES = sorted(
    "scripts." + Path(path).stem for path in glob.glob("scripts/classify_*_hermes.py")
)


class HermesClassifierSplitRetryTest(unittest.TestCase):
    """A batch Hermes keeps answering short is retried one post at a time."""

    def test_short_batch_is_split_into_single_posts(self):
        self.assertGreaterEqual(len(MODULES), 10)
        for name in MODULES:
            with self.subTest(name):
                module = importlib.import_module(name)
                batch = [{"text": "a"}, {"text": "b"}]

                def fake(rows, **_):
                    if len(rows) > 1:
                        raise RuntimeError("Hermes batch failed: expected 2 classifications, got 1")
                    return [{"label": rows[0]["text"]}]

                with patch.object(module, "classify", side_effect=fake) as mocked:
                    labels = module.classify_or_split(batch)
                self.assertEqual(labels, [{"label": "a"}, {"label": "b"}])
                self.assertEqual(mocked.call_count, 3)

    def test_single_post_failure_still_raises(self):
        for name in MODULES:
            with self.subTest(name):
                module = importlib.import_module(name)
                with patch.object(module, "classify", side_effect=RuntimeError("Hermes batch failed")):
                    with self.assertRaises(RuntimeError):
                        module.classify_or_split([{"text": "a"}])

    def test_upstream_refusal_is_reported_not_parsed(self):
        refusal = "HTTP 400: Upstream request failed: [400] The request was rejected because it was considered high risk\n"
        for name in MODULES:
            with self.subTest(name):
                module = importlib.import_module(name)
                done = subprocess.CompletedProcess(["hermes"], 0, stdout=refusal, stderr="")
                with patch.object(module.subprocess, "run", return_value=done):
                    with self.assertRaisesRegex(RuntimeError, "upstream error"):
                        module.classify([{"text": "a"}])

    def test_refused_post_is_kept_with_error_label(self):
        for name in MODULES:
            with self.subTest(name):
                module = importlib.import_module(name)

                def fake(rows, **_):
                    if len(rows) > 1 or rows[0]["text"] == "b":
                        raise RuntimeError("Hermes upstream error: HTTP 400 high risk")
                    return [{"label": "a"}]

                with patch.object(module, "classify", side_effect=fake):
                    labels = module.classify_or_split([{"text": "a"}, {"text": "b"}])
                self.assertEqual(labels[0], {"label": "a"})
                self.assertTrue(labels[1]["error"].startswith("upstream_refused"))


if __name__ == "__main__":
    unittest.main()
