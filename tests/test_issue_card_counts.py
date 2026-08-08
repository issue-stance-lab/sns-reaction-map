import unittest

from scripts.issue_card_counts import count_by_issue


class IssueCardCountsTest(unittest.TestCase):
    def test_opinion_basis_falls_back_to_legacy_top_level_flag(self):
        rows = [
            {
                "is_opinion": True,
                "classification": {"main_issue": "論点A"},
            }
        ]

        self.assertEqual(count_by_issue(rows, "opinion"), {"論点A": 1})

    def test_nested_opinion_flag_takes_precedence(self):
        rows = [
            {
                "is_opinion": True,
                "classification": {"is_opinion": False, "main_issue": "論点A"},
            }
        ]

        self.assertEqual(count_by_issue(rows, "opinion"), {})


if __name__ == "__main__":
    unittest.main()
