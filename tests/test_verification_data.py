import unittest

from scripts.verification_data import make_verification_records, record_id_hash


class VerificationDataTests(unittest.TestCase):
    def test_url_and_tweet_id_have_same_hash(self) -> None:
        self.assertEqual(
            record_id_hash({"tweet_id": "123"}),
            record_id_hash({"url": "https://x.com/example/status/123?s=20"}),
        )

    def test_summary_contains_only_hash_and_classification_allowlist(self) -> None:
        result = make_verification_records([
            {
                "tweet_id": "123",
                "url": "https://x.com/example/status/123",
                "text": "公開しない本文",
                "user_id": "example",
                "classification": {
                    "main_issue": "費用負担",
                    "stance": "移行支持",
                    "is_opinion": True,
                    "is_relevant": True,
                    "confidence": 0.9,
                    "summary": "公開しない要約",
                },
            }
        ])
        self.assertEqual(set(result[0]), {"record_id_hash", "classification"})
        self.assertEqual(
            set(result[0]["classification"]),
            {"main_issue", "stance", "is_opinion", "is_relevant", "confidence"},
        )
        rendered = str(result)
        for secret in ("tweet_id", "https://", "公開しない本文", "example", "公開しない要約"):
            self.assertNotIn(secret, rendered)

    def test_duplicate_ids_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate"):
            make_verification_records([{"tweet_id": "123"}, {"tweet_id": "123"}])


if __name__ == "__main__":
    unittest.main()
