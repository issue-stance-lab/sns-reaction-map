from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from verify_claim_verdicts import LEGACY_CONSTITUTIONAL, audit  # noqa: E402


class ClaimVerdictTest(unittest.TestCase):
    def test_existing_claim_audits_use_only_shared_codes(self) -> None:
        counts, errors = audit()
        self.assertEqual(errors, [])
        self.assertEqual(set(counts), {
            "bike-blue-ticket", "constitutional-amendment", "consumption-tax-cut",
            "elderly-license-revocation", "fukushuto", "koshitsu-tenpakai",
        })
        self.assertEqual(sum(counts.values()), 41)

    def test_constitutional_legacy_labels_map_to_shared_codes(self) -> None:
        self.assertEqual(LEGACY_CONSTITUTIONAL, {
            "原典にある": "fact",
            "原典とずれる": "gap",
            "原典にたどり着けず": "miss",
        })


if __name__ == "__main__":
    unittest.main()
