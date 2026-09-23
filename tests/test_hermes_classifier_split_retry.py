import glob
import importlib
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


if __name__ == "__main__":
    unittest.main()
