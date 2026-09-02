from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import json  # noqa: E402
import tempfile  # noqa: E402
from unittest import mock  # noqa: E402

import verify_claim_verdicts as vcv  # noqa: E402
from verify_claim_verdicts import (  # noqa: E402
    LEGACY_CONSTITUTIONAL,
    audit,
    canonical_claim_counts,
    coverage_warnings,
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

    def test_coverage_warning_fires_when_reading_falls_behind(self) -> None:
        # 定期更新は母数を機械が数え直すが、主張ごとの件数は人が読んだ時点で止まる。
        # 3か所突き合わせは3つとも同じ確定データ由来のためこのズレを見つけられない。
        # 現在のデータ状態に依存しないよう、作った入力で挙動だけを固定する。
        def theme_json(checked_on: str, period_end: str) -> dict:
            return {
                "claim_verification": {"checked_on": checked_on},
                "collection_period": {"start": "2026-06-27", "end": period_end},
            }

        cases = {
            "behind": (theme_json("2026-08-16", "2026-08-24"), True),
            "caught-up": (theme_json("2026-09-02", "2026-09-02"), False),
            "no-checked-on": ({"claim_verification": {"checked_on": None},
                              "collection_period": {"end": "2026-09-02"}}, False),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, (payload, _) in cases.items():
                (root / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")
            with mock.patch.object(vcv, "SOURCES", {name: ("", "") for name in cases}), \
                 mock.patch.object(vcv, "public_path", lambda theme: root / f"{theme}.json"):
                warned = {line.split(":")[0] for line in coverage_warnings()}
        self.assertEqual(warned, {name for name, (_, expected) in cases.items() if expected})

    def test_coverage_warnings_never_change_the_exit_code(self) -> None:
        # 読み直す範囲はオーナー判断のため、警告で止めない。止める判断は課題54の残課題。
        _, errors = audit()
        self.assertEqual(errors, [])
        for line in coverage_warnings():
            self.assertIn(line.split(":")[0], vcv.SOURCES)

    def test_constitutional_legacy_labels_map_to_shared_codes(self) -> None:
        self.assertEqual(LEGACY_CONSTITUTIONAL, {
            "原典にある": "fact",
            "原典とずれる": "gap",
            "原典にたどり着けず": "miss",
        })


if __name__ == "__main__":
    unittest.main()
