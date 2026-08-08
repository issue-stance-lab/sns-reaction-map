#!/usr/bin/env python3
"""自転車青切符 taxonomy の整合性を検証するユニットテスト。"""

import unittest

from scripts import classify_bike_arena_hermes, bike_blue_ticket_taxonomy


class BikeBlueTaxonomyTest(unittest.TestCase):
    def test_classifier_shares_taxonomy(self):
        self.assertEqual(classify_bike_arena_hermes.ISSUES, bike_blue_ticket_taxonomy.ISSUE_SET)
        self.assertEqual(classify_bike_arena_hermes.STANCES, bike_blue_ticket_taxonomy.STANCE_SET)

    def test_issues_list_length_and_order(self):
        self.assertEqual(len(bike_blue_ticket_taxonomy.ISSUES), 6)
        self.assertEqual(bike_blue_ticket_taxonomy.ISSUES[-1], "その他")
        self.assertEqual(len(set(bike_blue_ticket_taxonomy.ISSUES)), 6)

    def test_stances_list_length(self):
        self.assertEqual(len(bike_blue_ticket_taxonomy.STANCES), 3)


if __name__ == "__main__":
    unittest.main()
