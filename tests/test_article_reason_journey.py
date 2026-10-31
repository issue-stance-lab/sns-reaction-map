"""GA4人数の水増しと未計測の0扱いを防ぐ。ブラウザ計測はオフラインVMで検査。"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import measure_article_reason_journey as m

CONFIG = {'focus_articles': ['bike-blue-ticket-unfair', 'kobe-katsu'],
          'published_at': '2026-10-31T18:00:00+09:00', 'first_full_day': '2026-11-01',
          'click_event': 'article_reason_click', 'view_event': 'article_reason_view'}


def report(n):
    return {'rows': [{'metricValues': [{'value': str(n)}, {'value': str(n * 2)}]}]}


class JourneyReportTest(unittest.TestCase):
    def test_combined_users_come_from_aggregate_query(self):
        calls = []
        def query(payload):
            calls.append(payload)
            return report(5 if 'kobe' in json.dumps(payload) and 'bike' in json.dumps(payload) else 4)
        result = m.measure(query, CONFIG, '2026-11-01', '2026-11-05')
        self.assertEqual(result['combined']['reason_view']['users'], 5)
        self.assertEqual(len(calls), 9)
        self.assertTrue(all('dimensions' not in p for p in calls))
        self.assertIn('pageReferrer', json.dumps(calls[2]))
        self.assertNotIn('customEvent:', json.dumps(calls))

    def test_baseline_is_unknown_not_zero(self):
        result = m.measure(lambda _: report(3), {**CONFIG, 'published_at': None},
                           '2026-10-04', '2026-10-30', baseline=True)
        self.assertIsNone(result['combined']['reason_view']['users'])
        self.assertEqual(result['combined']['reason_view']['status'], 'not_measured')

    def test_unpublished_and_mixed_periods_rejected(self):
        for config, start in [({**CONFIG, 'published_at': None}, '2026-11-01'),
                              (CONFIG, '2026-10-31')]:
            with self.assertRaises(ValueError):
                m.measure(lambda _: report(0), config, start, '2026-11-05')

    def test_thresholded_counts_are_unknown(self):
        result = m.read_count({'metadata': {'subjectToThresholding': True}})
        self.assertIsNone(result['users'])
        self.assertEqual(result['status'], 'limited')

    def test_never_sum_grouped_unique_users(self):
        with self.assertRaises(ValueError):
            m.read_count({'rows': report(2)['rows'] * 2})

    @unittest.skipUnless(shutil.which('node'), 'Node.jsが必要')
    def test_browser_event_semantics_offline(self):
        result = subprocess.run(['node', str(ROOT / 'tests/article_reason_journey_vm.cjs')],
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
