"""Keep failed API reads separate from Google exclusion states."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import fetch_gsc_index_status as audit


class IndexStatusTests(unittest.TestCase):
    def test_api_failure_is_not_exclusion(self):
        with patch.object(audit.urllib.request, 'urlopen', side_effect=TimeoutError):
            row = audit.inspect_url('https://example.com/', 'secret', 'sc-domain:example.com')
        self.assertEqual(audit.summarize([row]), {
            'total': 1, 'inspection_errors': 1, 'coverage_states': {}})
        self.assertNotIn('secret', str(row))

    def test_summary_preserves_google_states(self):
        rows = [{'indexStatusResult': {'coverageState': state}} for state in
                ['送信して登録されました', 'クロール済み - インデックス未登録', 'URL が Google に認識されていません']]
        summary = audit.summarize(rows)
        self.assertEqual(summary['total'], 3)
        self.assertEqual(summary['inspection_errors'], 0)
        self.assertEqual(len(summary['coverage_states']), 3)


if __name__ == '__main__':
    unittest.main()
