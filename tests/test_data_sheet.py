import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class DataSheetTest(unittest.TestCase):
    def test_data_sheet_matches_canonical_data(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/build_data_sheet.py", "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
