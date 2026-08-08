import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class BuilderRebuildabilityTest(unittest.TestCase):
    def test_promotion_order_keeps_builders_rebuildable(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/verify_builder_rebuildability.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
