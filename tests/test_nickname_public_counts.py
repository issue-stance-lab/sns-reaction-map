"""あだ名禁止ページの集計表示が、公開データJSON（課題57）から作れることの検査。

このテーマは「候補生成そのものが件数を数えるので公開JSONへ繋ぐと古い数字が出る」
という理由で一度接続を見送った（quality/reviews/2026-08-31-...-school-nickname-ban.md）。
段階5で候補ツリー内に公開JSONを作り直すようになったため接続したが、
**新しい件数がページへ伝わること**を検査で固定しておかないと、当時と同じ
「2回生成して差分ゼロは通るのに数字は古い」状態へ戻せてしまう。
"""

import json
import re
import unittest
from pathlib import Path

from scripts.build_nickname_arena import apply_public_counts

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/school-nickname-ban-reaction-map.html"
PUBLIC = ROOT / "data/public/themes/school-nickname-ban.json"
TMP = ROOT / ".tmp-nickname-public-counts.json"


class NicknamePublicCountsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.page = PAGE.read_text(encoding="utf-8")
        self.public = json.loads(PUBLIC.read_text(encoding="utf-8"))
        self.addCleanup(lambda: TMP.unlink(missing_ok=True))

    def _write(self, data: dict) -> Path:
        TMP.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return TMP

    def test_public_json_reproduces_published_page(self) -> None:
        """公開JSONだけから、いま公開しているページと同じバイト列に戻せる。"""
        self.assertEqual(apply_public_counts(self.page, PUBLIC), self.page)

    def test_new_opinion_reaches_every_count_on_the_page(self) -> None:
        """公開JSONの件数が増えたら、ページの各所の数字も増える。"""
        data = json.loads(json.dumps(self.public))
        target = next(item for item in data["issues"] if item["label"] == "いじめ・心理的安全")
        before = int(target["count"])
        target["count"] = before + 1
        next(s for s in target["stances"] if s["label"] == "禁止支持")["count"] += 1
        next(i for i in target["intensities"] if i["id"] == "high")["count"] += 1
        data["opinion_count"] += 1
        data["issue_assigned_count"] += 1
        data["collected_count"] += 1

        updated = apply_public_counts(self.page, self._write(data))
        opinions = int(self.public["opinion_count"]) + 1
        self.assertIn(f'分析対象となった意見{opinions}件', updated)
        self.assertIn(f'<span>{opinions}件 | セクター=論点', updated)
        self.assertIn(f'公開投稿 {int(self.public["collected_count"]) + 1}件', updated)
        self.assertIn(f'<span class="issue-count">{before + 1}件</span>', updated)
        self.assertIn(f'"key":"safety"', updated)
        issues = re.search(r"var issues=(\[[^\n]*?\]);", updated)
        assert issues is not None
        payload = {item["key"]: item["count"] for item in json.loads(issues.group(1))}
        self.assertEqual(payload["safety"], before + 1)

    def test_unknown_issue_with_count_is_rejected(self) -> None:
        """ページに論点ブロックが無いラベルへ件数が付いたら止まる。"""
        data = json.loads(json.dumps(self.public))
        other = next(item for item in data["issues"] if item["label"] == "その他")
        other["count"] = 1
        other["stances"] = [{"id": "x", "label": "禁止支持", "count": 1}]
        other["intensities"] = [{"id": "low", "count": 1}]
        data["opinion_count"] += 1
        with self.assertRaises(Exception):
            apply_public_counts(self.page, self._write(data))

    def test_issue_total_mismatch_is_rejected(self) -> None:
        """立場の合計が論点件数と合わない公開JSONは受け付けない。"""
        data = json.loads(json.dumps(self.public))
        target = next(item for item in data["issues"] if item["label"] == "いじめ・心理的安全")
        target["stances"][0]["count"] += 1
        with self.assertRaises(Exception):
            apply_public_counts(self.page, self._write(data))


if __name__ == "__main__":
    unittest.main()
