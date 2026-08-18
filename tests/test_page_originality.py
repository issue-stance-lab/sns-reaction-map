"""公開ページ同士で言い回しが使い回されていないことを、テストからも押さえる。

`scripts/verify_page_originality.py` が exit 0 であることを確かめる。
発注書に「見出しをコピーするな」と書いても守られなかった（2026-08-18）ので、
ここで止める。
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "verify_page_originality.py"


class PageOriginalityTest(unittest.TestCase):
    def test_no_recycled_wording(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(
            result.returncode,
            0,
            f"ページ間で言い回しが使い回されています:\n{result.stdout}\n{result.stderr}",
        )
