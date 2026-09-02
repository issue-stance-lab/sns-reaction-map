from __future__ import annotations

import json
import unittest

from scripts import public_registry_common as prc


class ClaimVerificationContractTest(unittest.TestCase):
    def test_completed_and_not_started_are_distinguished(self) -> None:
        complete = prc.build_claim_verification("constitutional-amendment")
        self.assertEqual(complete["status"], "complete")
        self.assertEqual(len(complete["claims"]), 10)
        self.assertEqual({item["verdict"] for item in complete["claims"]}, {"fact", "gap", "miss"})
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

        pending = prc.build_claim_verification("ai-copyright")
        self.assertEqual(pending, {"status": "not_started", "checked_on": None, "reviewer_type": None, "claims": []})

    def test_bukatsu_chiiki_is_verified_by_editorial_review(self) -> None:
        # 課題54 段階3で照合済み。公開JSONを complete にできるのは人が確定した場合だけなので、
        # 確認者種別が ai_assisted へ変わっていないことをここで固定する。
        done = prc.build_claim_verification("bukatsu-chiiki")
        self.assertEqual(done["status"], "complete")
        self.assertEqual(done["reviewer_type"], "editorial_review")
        self.assertEqual(len(done["claims"]), 7)
        self.assertEqual({item["verdict"] for item in done["claims"]}, {"fact", "gap", "miss"})
        self.assertNotIn("tweet_id", json.dumps(done, ensure_ascii=False))

    def test_all_ten_themes_have_an_explicit_status(self) -> None:
        complete = {theme for theme in prc.CLAIM_AUDIT_SOURCES if prc.build_claim_verification(theme)["status"] == "complete"}
        self.assertEqual(complete, set(prc.CLAIM_AUDIT_SOURCES))
        self.assertEqual(
            {theme for theme in prc.QUESTIONS if prc.build_claim_verification(theme)["status"] == "not_started"},
            {"ai-copyright", "henoko-student-accident", "school-nickname-ban"},
        )
