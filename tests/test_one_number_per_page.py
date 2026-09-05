"""「同じ数字は1ページに1回だけ」の検査（課題54 段階8）。

自転車ページは同じ画面に「5つの論点」と「6つの論点」が同時に載っていたのに、
既存の検査は両方 OK と判定していた。読者が同時に見る数字を1つに保つ。

作った検査が実際の defect を捕まえること、そして**捕まえてはいけないもの**
（他テーマの紹介文・論点ごとの内訳・過去の版を述べた文）で騒がないことを固定する。
"""
from __future__ import annotations

import unittest

from scripts.verify_theme_page import verify_one_number_per_page


def page(body: str) -> str:
    return f"<html><body>{body}</body></html>"


class OneNumberPerPageTest(unittest.TestCase):
    THEME = "bike-blue-ticket"   # 正典: 論点5（その他を除く）

    @property
    def total(self) -> int:
        """ページの母数は正典から取る。ここを固定値にすると更新のたびに落ちる。"""
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        return json.loads(
            (root / "data/public/themes" / f"{self.THEME}.json").read_text(encoding="utf-8")
        )["opinion_count"]

    def failures(self, body: str) -> tuple[list[str], int]:
        return verify_one_number_per_page(self.THEME, page(body))

    def test_the_bike_defect_is_detected(self):
        # 段階8の完了条件そのもの
        lines, failures = self.failures(
            "<h2>このテーマを読み解く、5つの論点</h2>"
            "<p>中心の「自転車の青切符」を6つの論点セクターが囲みます。</p>")
        self.assertEqual(failures, 1)
        self.assertTrue(any("論点数が1ページに2通り以上" in x for x in lines), lines)

    def test_one_value_everywhere_passes(self):
        lines, failures = self.failures(
            "<h2>5つの論点</h2><p>5つの論点を把握してから投票へ。</p>")
        self.assertEqual(failures, 0, lines)

    def test_related_theme_blurbs_are_ignored(self):
        # 「関連テーマ」は他テーマの論点数を書く。このページの数字ではない
        lines, failures = self.failures(
            '<h2>5つの論点</h2>'
            '<section id="related-section"><div class="related-grid">'
            '<a class="related-card">憲法改正論議 9条・緊急事態条項をめぐる6論点</a>'
            '</div></section>')
        self.assertEqual(failures, 0, lines)

    def test_per_issue_counts_are_not_page_totals(self):
        # 「意見103件のうち100件が…」は論点ごとの内訳で、ページの母数ではない
        lines, failures = self.failures(
            f"<p>分析対象の意見{self.total}件</p>"
            "<p>意見103件のうち100件が「切り分け」スタンス。</p>")
        self.assertEqual(failures, 0, lines)

    def test_historical_sentences_are_not_page_totals(self):
        # 過去の版を述べた文（同じ文の中に日付がある）は対象外
        lines, failures = self.failures(
            "<p>分析対象の意見384件</p>"
            "<p>2026年8月8日にすべて同じ形式へ統合し、累計897件・意見765件から作り直しました。</p>")
        self.assertEqual(failures, 0, lines)

    def test_a_stale_total_in_prose_is_detected(self):
        # あだ名禁止で実際にあった形。更新履歴の近くに古い母数が残っていた
        lines, failures = self.failures(
            "<p>分析対象の意見384件</p><p>意見87件と母数が小さいため、比率は動きます。</p>")
        self.assertEqual(failures, 1)
        self.assertTrue(any("意見数" in x and "正典" in x for x in lines), lines)

    def test_counting_other_as_an_issue_is_a_note_not_a_failure(self):
        # ページの中では食い違っていない。catalog とのズレは知らせるだけにする
        lines, failures = self.failures("<h2>6つの論点</h2><p>6つの論点を整理しました。</p>")
        self.assertEqual(failures, 0, lines)
        self.assertTrue(any(x.startswith("注意") for x in lines), lines)

    def test_ordinal_labels_are_not_counts(self):
        # 「論点1」「論点2」は順番のラベルで、数ではない
        lines, failures = self.failures(
            "<h2>5つの論点</h2><h3>論点1</h3><h3>論点2</h3><h3>論点6</h3>")
        self.assertEqual(failures, 0, lines)


class LivePagesTest(unittest.TestCase):
    def test_no_published_page_shows_two_different_counts(self):
        import yaml
        from pathlib import Path
        from scripts.verify_theme_page import ROOT

        themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
        for name, meta in themes.items():
            path = ROOT / str(meta.get("html") or "")
            if not path.is_file():
                continue
            lines, failures = verify_one_number_per_page(name, path.read_text(encoding="utf-8"))
            self.assertEqual(failures, 0, f"{name}: {[x for x in lines if x.startswith('NG')]}")
