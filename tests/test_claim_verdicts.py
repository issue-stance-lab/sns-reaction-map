from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from verify_claim_verdicts import (  # noqa: E402
    LEGACY_CONSTITUTIONAL,
    audit,
    canonical_claim_counts,
    public_claim_counts,
    verification_claim_counts,
)


class ClaimVerdictTest(unittest.TestCase):
    def test_existing_claim_audits_use_only_shared_codes(self) -> None:
        counts, errors = audit()
        self.assertEqual(errors, [])
        self.assertEqual(set(counts), {
            "bike-blue-ticket", "bukatsu-chiiki", "constitutional-amendment", "consumption-tax-cut",
            "elderly-license-revocation", "fukushuto", "koshitsu-tenpakai",
        })
        # 41主張＋部活動7主張（課題54 段階3）
        self.assertEqual(sum(counts.values()), 48)

    def test_post_counts_agree_across_all_three_files(self) -> None:
        # ページは data/{theme}_claim_posts.json、公開JSONは data/verification/ を読む。
        # 片方だけ更新すると同じサイトの2か所で違う数字が出る。
        for theme in ("bike-blue-ticket", "bukatsu-chiiki", "constitutional-amendment", "koshitsu-tenpakai"):
            canon = canonical_claim_counts(theme)
            self.assertTrue(canon, theme)
            self.assertEqual(verification_claim_counts(theme), canon, theme)
            self.assertEqual(public_claim_counts(theme), canon, theme)

    def test_constitutional_legacy_labels_map_to_shared_codes(self) -> None:
        self.assertEqual(LEGACY_CONSTITUTIONAL, {
            "原典にある": "fact",
            "原典とずれる": "gap",
            "原典にたどり着けず": "miss",
        })


if __name__ == "__main__":
    unittest.main()
