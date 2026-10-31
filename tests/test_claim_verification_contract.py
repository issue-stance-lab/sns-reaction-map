from __future__ import annotations

import json
import unittest

from scripts import public_registry_common as prc


class ClaimVerificationContractTest(unittest.TestCase):
    def test_completed_and_not_started_are_distinguished(self) -> None:
        complete = prc.build_claim_verification("constitutional-amendment")
        self.assertEqual(complete["status"], "complete")
        self.assertEqual(len(complete["claims"]), 6)
        self.assertEqual({item["verdict"] for item in complete["claims"]}, {"fact", "miss"})
        self.assertTrue(all(item["matched_post_count"] > 0 for item in complete["claims"]))
        self.assertNotIn("tweet_id", json.dumps(complete, ensure_ascii=False))
        # 段階6で大陸を実像／ずれ／蜃気楼に塗り分けるため、主張は必ず論点へ結びつける
        self.assertTrue(all(item["issue_ids"] for item in complete["claims"]))
        # miss（資料に見当たらない）以外は、一次資料が1件以上必要
        self.assertTrue(
            all(item["sources"] for item in complete["claims"] if item["verdict"] != "miss")
        )

    def test_claims_point_at_real_issues_and_never_at_other(self) -> None:
        import json as _json
        from pathlib import Path as _Path

        for theme in prc.CLAIM_AUDIT_SOURCES:
            data = _json.loads(
                (_Path(prc.ROOT) / "data" / "public" / "themes" / f"{theme}.json").read_text(encoding="utf-8")
            )
            known = {i["id"] for i in data["issues"]}
            other = {i["id"] for i in data["issues"] if i["kind"] == "other"}
            for claim in data["claim_verification"]["claims"]:
                for issue_id in claim["issue_ids"]:
                    self.assertIn(issue_id, known, f"{theme}/{claim['id']}")
                    self.assertNotIn(issue_id, other, f"{theme}/{claim['id']}")

    def test_bukatsu_chiiki_reports_ai_assisted_review(self) -> None:
        # 課題99の現行照合は別コンテキストのAIによる独立確認。人間の監査と表示しない。
        done = prc.build_claim_verification("bukatsu-chiiki")
        self.assertEqual(done["status"], "complete")
        self.assertEqual(done["reviewer_type"], "ai_assisted")
        self.assertEqual(len(done["claims"]), 7)
        self.assertEqual({item["verdict"] for item in done["claims"]}, {"fact", "gap", "miss"})
        self.assertNotIn("tweet_id", json.dumps(done, ensure_ascii=False))

    def test_all_ten_themes_have_an_explicit_status(self) -> None:
        complete = {theme for theme in prc.CLAIM_AUDIT_SOURCES if prc.build_claim_verification(theme)["status"] == "complete"}
        self.assertEqual(complete, set(prc.CLAIM_AUDIT_SOURCES))
        self.assertEqual(complete, set(prc.QUESTIONS))
        self.assertEqual(
            {theme for theme in prc.QUESTIONS if prc.build_claim_verification(theme)["status"] == "not_started"},
            set(),
        )

    def test_henoko_ai_review_is_not_described_as_human(self):
        done = prc.build_claim_verification("henoko-student-accident")
        self.assertEqual(done["reviewer_type"], "ai_assisted")
        self.assertEqual(len(done["claims"]), 6)

    def test_ai_copyright_is_verified_by_editorial_review(self) -> None:
        # 山なみ変換（2026-09-14）でCLAIM_AUDIT_SOURCESへの登録が漏れ、一次資料クイズが
        # 空のまま公開されていた（オーナー報告で発覚、2026-09-19に解消）。
        done = prc.build_claim_verification("ai-copyright")
        self.assertEqual(done["status"], "complete")
        self.assertEqual(done["reviewer_type"], "editorial_review")
        self.assertEqual(len(done["claims"]), 6)
        self.assertTrue(all(item["matched_post_count"] > 0 for item in done["claims"]))
        self.assertTrue(all(item["issue_ids"] for item in done["claims"]))
        self.assertTrue(all(item["sources"] for item in done["claims"]))
        self.assertNotIn("tweet_id", json.dumps(done, ensure_ascii=False))


class EmptyClaimAssociationsTest(unittest.TestCase):
    def test_explicitly_reviewed_zero_associations_are_published(self):
        done = prc.build_claim_verification("bukatsu-chiiki")
        counts = {c["id"]: c["matched_post_count"] for c in done["claims"]}
        self.assertEqual(counts["national-funding"], 0)
        self.assertEqual(counts["shidoin-role"], 0)
        self.assertEqual(sum(counts.values()), 10)

    def test_missing_positive_verification_rows_are_rejected(self):
        from pathlib import Path
        from unittest import mock
        original = Path.read_text
        target = prc.ROOT / "data/verification/bukatsu-chiiki-claims.json"
        def read(path, *args, **kwargs):
            text = original(path, *args, **kwargs)
            return json.dumps(json.loads(text)[1:]) if path == target else text
        with mock.patch.object(Path, "read_text", read):
            with self.assertRaisesRegex(prc.RegistryError, "件数が確定データと一致しません"):
                prc.build_claim_verification("bukatsu-chiiki")

    def test_unknown_verification_claim_is_rejected(self):
        from pathlib import Path
        from unittest import mock
        original = Path.read_text
        target = prc.ROOT / "data/verification/bukatsu-chiiki-claims.json"
        def read(path, *args, **kwargs):
            text = original(path, *args, **kwargs)
            if path == target:
                rows = json.loads(text)
                rows.append({"claim": "unknown"})
                return json.dumps(rows)
            return text
        with mock.patch.object(Path, "read_text", read):
            with self.assertRaises(prc.RegistryError):
                prc.build_claim_verification("bukatsu-chiiki")
