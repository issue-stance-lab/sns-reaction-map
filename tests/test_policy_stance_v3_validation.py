import copy
import unittest

from scripts.policy_stance_v3_validation import validate_review


class PolicyStanceV3ValidationTests(unittest.TestCase):
    def setUp(self):
        self.packet = {
            "packet_fingerprint": "packet",
            "records": [
                {
                    "case_id": "ai",
                    "topic": "ai-copyright",
                    "record_id_hash": "ai-id",
                    "body_sha256": "ai-body",
                },
                {
                    "case_id": "fuku",
                    "topic": "fukushuto",
                    "record_id_hash": "fuku-id",
                    "body_sha256": "fuku-body",
                },
            ],
        }
        common = {
            "decision_route": "candidate",
            "stance_target": "対象",
            "evidence": "根拠",
            "reason": "判断理由",
        }
        self.review = {
            "packet_fingerprint": "packet",
            "records": [
                common
                | {
                    "case_id": "ai",
                    "record_id_hash": "ai-id",
                    "body_sha256": "ai-body",
                    "candidate": {
                        "is_relevant": True,
                        "is_opinion": True,
                        "main_issue": "AI生成物の権利・創作性",
                        "stance": "中立・情報",
                    },
                    "ai_use_position": "unexpressed",
                    "target_scope": None,
                    "target_stance": None,
                    "whole_policy_stance": None,
                    "aggregation_route": None,
                },
                common
                | {
                    "case_id": "fuku",
                    "record_id_hash": "fuku-id",
                    "body_sha256": "fuku-body",
                    "candidate": {
                        "is_relevant": True,
                        "is_opinion": True,
                        "main_issue": "候補地",
                        "stance": None,
                    },
                    "ai_use_position": None,
                    "target_scope": "local_bid",
                    "target_stance": "oppose",
                    "whole_policy_stance": None,
                    "aggregation_route": "scoped_only",
                },
            ],
        }

    def test_accepts_complete_topic_specific_reviews(self):
        result = validate_review(self.packet, self.review)
        self.assertEqual(set(result), {"ai", "fuku"})

    def test_rejects_fukushuto_fields_on_ai_record(self):
        review = copy.deepcopy(self.review)
        review["records"][0]["target_scope"] = "whole_policy"
        with self.assertRaisesRegex(ValueError, "must be null"):
            validate_review(self.packet, review)

    def test_rejects_missing_record(self):
        review = copy.deepcopy(self.review)
        review["records"].pop()
        with self.assertRaisesRegex(ValueError, "all 22 records"):
            validate_review(self.packet, review)


if __name__ == "__main__":
    unittest.main()
