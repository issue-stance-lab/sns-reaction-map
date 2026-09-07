import unittest
from types import SimpleNamespace
from scripts.build_henoko_arena import political_split_summary,IssueCountError
class SplitSummaryTest(unittest.TestCase):
    def test_categories_are_separate_and_idempotent(self):
        stats=SimpleNamespace(split=74,neutral=3)
        result=political_split_summary('<strong>事実整理・責任追及（73件）</strong>',stats)
        self.assertEqual(result,'<strong>論点の切り分け（74件）・中立情報（3件）</strong>')
        self.assertEqual(political_split_summary(result,stats),result)
    def test_unknown_or_duplicate_layout_stops(self):
        stats=SimpleNamespace(split=74,neutral=3)
        for text in ['', '<strong>事実整理・責任追及（73件）</strong>'*2]:
            with self.assertRaises(IssueCountError):political_split_summary(text,stats)
