#!/usr/bin/env python3
"""高齢者免許返納 taxonomy の整合性を検証するユニットテスト。"""

import unittest

from scripts import classify_elderly_arena_hermes, elderly_license_taxonomy


class ElderlyLicenseTaxonomyTest(unittest.TestCase):
    def test_classifier_shares_taxonomy(self):
        self.assertEqual(classify_elderly_arena_hermes.ISSUES, elderly_license_taxonomy.ISSUE_SET)
        self.assertEqual(classify_elderly_arena_hermes.STANCES, elderly_license_taxonomy.STANCE_SET)
        self.assertEqual(classify_elderly_arena_hermes.ISSUE_INDEX, elderly_license_taxonomy.ISSUE_INDEX)

    def test_issues_list_length_and_order(self):
        self.assertEqual(len(elderly_license_taxonomy.ISSUES), 6)
        self.assertEqual(elderly_license_taxonomy.ISSUES[-1], "その他")
        self.assertEqual(len(set(elderly_license_taxonomy.ISSUES)), 6)

    def test_stances_list_length(self):
        self.assertEqual(len(elderly_license_taxonomy.STANCES), 4)


if __name__ == "__main__":
    unittest.main()
