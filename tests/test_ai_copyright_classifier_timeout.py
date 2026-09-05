import subprocess
import unittest
from unittest.mock import patch

from scripts import classify_aicopyright_arena_hermes as classifier


class AiCopyrightClassifierTimeoutTest(unittest.TestCase):
    def test_timeout_is_retried_and_reported(self):
        batch = [{"text": "AIと著作権"}]
        with patch.object(
            classifier.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(["hermes"], 7),
        ) as run:
            with self.assertRaisesRegex(RuntimeError, "timed out after 7 seconds"):
                classifier.classify(batch, timeout=7)

        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args.kwargs["timeout"], 7)


if __name__ == "__main__":
    unittest.main()
