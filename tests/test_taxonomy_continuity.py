"""正典と分類器の taxonomy が食い違ったまま累積しないことを確認する。

2026-08-03 の ai-copyright で、正典（「学習データ・無断利用」）と分類器
（「学習データ無断利用」）の論点ラベルが別体系のまま累積候補が作られた。
件数・ID の検査は通ってしまうため、ラベルの連続性を別に見る必要がある。
"""

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.refresh_topic import ROOT, taxonomy_continuity


class TaxonomyContinuityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.classifier = Path(self.tmp.name) / "classifier.py"
        self.classifier.write_text(
            'ISSUES = {"論点A", "論点B"}\nSTANCES = {"賛成", "反対"}\n',
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def _row(main_issue, stance="賛成"):
        return {"tweet_id": "1", "classification": {"main_issue": main_issue, "stance": stance}}

    def test_same_taxonomy_is_compatible(self):
        result = taxonomy_continuity([self._row("論点A")], self.classifier)

        self.assertTrue(result["compatible"])
        self.assertEqual(result["unknown_issues"], [])

    def test_canonical_label_outside_classifier_is_rejected(self):
        result = taxonomy_continuity([self._row("論点C")], self.classifier)

        self.assertFalse(result["compatible"])
        self.assertEqual(result["unknown_issues"], ["論点C"])

    def test_canonical_stance_outside_classifier_is_rejected(self):
        result = taxonomy_continuity([self._row("論点A", stance="中立")], self.classifier)

        self.assertFalse(result["compatible"])
        self.assertEqual(result["unknown_stances"], ["中立"])

    def test_canonical_without_main_issue_is_rejected(self):
        result = taxonomy_continuity([{"tweet_id": "1", "text": "本文"}], self.classifier)

        self.assertFalse(result["compatible"])
        self.assertTrue(result["canonical_without_main_issue"])

    def test_flat_schema_canonical_is_read(self):
        """2Dフラット形式（classification 入れ子なし）の正典も見る。"""
        result = taxonomy_continuity([{"tweet_id": "1", "main_issue": "論点C"}], self.classifier)

        self.assertFalse(result["compatible"])
        self.assertEqual(result["unknown_issues"], ["論点C"])

    def test_scheduled_themes_are_checked_against_live_data(self):
        """実際の台帳で、どのテーマが不一致かを固定する（回帰検知用）。"""
        themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
        pipeline = yaml.safe_load((ROOT / "configs" / "refresh-pipeline.yaml").read_text(encoding="utf-8"))["topics"]

        incompatible = set()
        for name, fields in themes.items():
            rows = json.loads((ROOT / fields["sample_file"]).read_text(encoding="utf-8"))
            if not taxonomy_continuity(rows, ROOT / pipeline[name]["classifier"])["compatible"]:
                incompatible.add(name)

        self.assertEqual(
            incompatible,
            {"fukushuto", "bike-blue-ticket", "elderly-license-revocation"},
            "taxonomy不一致テーマが変わった。解消したなら期待値を減らし、増えたなら原因を調べること",
        )


if __name__ == "__main__":
    unittest.main()
