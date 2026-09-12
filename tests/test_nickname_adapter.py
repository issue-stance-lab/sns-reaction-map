import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "social-samples/school-nickname-ban_hermes_arena_classified.json"
PAGE = ROOT / "docs/school-nickname-ban-reaction-map.html"
ARENA_DATA = ROOT / "docs/school-nickname-ban-arena-data.js"
BUILDER = ROOT / "scripts/build_nickname_arena.py"

SAFETY = "いじめ・心理的安全"
SUPPORT = "禁止支持"


def canonical() -> list[dict]:
    return json.loads(CANON.read_text(encoding="utf-8"))


def count(records: list[dict], main_issue: str) -> int:
    """論点の件数は正典から数える。

    収集回を足すたびに件数は変わる。期待値をテストに焼き込むと、
    データ更新のたびにテストが落ちて更新そのものが止まる。
    """
    return sum(
        1
        for row in records
        if row["classification"]["main_issue"] == main_issue
        and row["classification"]["is_opinion"]
        and row["classification"]["is_relevant"]
    )


class NicknameArenaBuilderTests(unittest.TestCase):
    """正典から作り直す部分（アリーナの点・注目ポイント・帯・内訳・詳細表）の検査。"""

    def _build(self, records: list[dict], work: Path) -> subprocess.CompletedProcess:
        source = work / "candidate.json"
        source.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
        return subprocess.run(
            [
                sys.executable, str(BUILDER),
                "--input", str(source),
                "--html-template", str(PAGE),
                "--output-html", str(work / "page.html"),
            ],
            cwd=ROOT, capture_output=True, text=True,
        )

    def test_published_page_matches_canonical(self):
        result = subprocess.run(
            [sys.executable, str(BUILDER), "--check"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_added_opinion_moves_every_place_that_shows_the_count(self):
        """1件足すと、件数を出しているすべての場所がまとめて動く。

        移行用スクリプトの時代は十数か所を手で直していたので、
        どこか1つだけ古いまま残らないことを見る。
        """
        source = canonical()
        added = json.loads(json.dumps(next(
            row for row in source
            if row["classification"]["main_issue"] == SAFETY
            and row["classification"]["stance"] == SUPPORT
        )))
        added["tweet_id"] = "adapter-test-only"
        added["url"] = "https://x.com/example/status/9999999999999999999"
        expected = count(source, SAFETY) + 1
        opinions = sum(
            1
            for row in source
            if row["classification"]["is_opinion"] and row["classification"]["is_relevant"]
        ) + 1

        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            # 山なみは個々の投稿の再読が必須。未確認の追加分を数だけ足して
            # exit 0 にせず、既存の出力ファイルを触る前に停止する。
            if '<!-- PLANET_SECTION_START -->' in PAGE.read_text():
                output = work / "page.html"
                arena = work / ARENA_DATA.name
                output.write_text("existing page")
                arena.write_text("existing arena")
                result = self._build(source + [added], work)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("候補検証", result.stderr)
                self.assertEqual(output.read_text(), "existing page")
                self.assertEqual(arena.read_text(), "existing arena")
                return
            result = self._build(source + [added], work)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = (work / "page.html").read_text(encoding="utf-8")
            needles = (
            f"分析対象となった意見{opinions}件",                     # リード文
            f'<strong class="insight-value">{opinions}<small>件',    # 注目ポイント
            f'id="issue-count-school-nickname-ban-ijime">{expected}件',  # 論点カード
            f'"key":"safety","title":"{SAFETY}"',                    # 投票の論点（keyは不変）
            f'<a href="#issue-safety">心理的安全 {expected}</a>',    # 論点ナビ
            f'<span class="issue-count">{expected}件</span>',        # 論点ブロックの見出し
            f"<th>{SAFETY}</th><td>{expected}</td>",                 # 詳細データ表
            f"関連する意見{opinions}件",                             # 詳細データの見出し
            )
            for needle in needles:
                # ページ全体を差分に出すと読めないので、見つからない文字列だけを出す
                self.assertTrue(needle in page, f"ページに {needle!r} がありません")
            self.assertIn(f'"count":{expected}', page)  # 投票ボタンの「(N件)」

            # 2回目は差分ゼロ。ページとアリーナの点の両方を見る
            first_page = (work / "page.html").read_bytes()
            first_arena = (work / ARENA_DATA.name).read_bytes()
            subprocess.run(
                [
                    sys.executable, str(BUILDER),
                    "--input", str(work / "candidate.json"),
                    "--html-template", str(work / "page.html"),
                    "--output-html", str(work / "page.html"),
                ],
                cwd=ROOT, check=True, capture_output=True,
            )
            self.assertEqual(first_page, (work / "page.html").read_bytes())
            self.assertEqual(first_arena, (work / ARENA_DATA.name).read_bytes())

    def test_same_counts_with_unreviewed_body_are_rejected(self):
        source = canonical()
        source[0]["text"] = "unreviewed replacement with identical counts"
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            result = self._build(source, work)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertFalse((work / "page.html").exists())

    def test_planet_is_regenerated_instead_of_preserved(self):
        import scripts.build_nickname_arena as builder
        page = PAGE.read_text()
        self.assertIn('<!-- PLANET_SECTION_START -->', page)
        damaged = page.replace('window.PLANET_DATA=', 'window.STALE_DATA=')
        self.assertTrue(page != damaged)
        rows, _, records = builder.load_opinions()
        restored = builder.apply_planet_counts(damaged, rows, len(records), builder.sample_period(records))
        self.assertTrue(restored == page, "再生成後のページが正典から作ったページと異なります")

    def test_failed_reread_gate_leaves_destination_untouched(self):
        import scripts.build_nickname_arena as builder
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "page.html"
            output.write_text("previous page")
            with patch("scripts.build_planet_data.independence_gate", return_value=["再読が未完了"]):
                with self.assertRaisesRegex(builder.IssueCountError, "再読が未完了"):
                    builder.build(html_template=PAGE, output_html=output)
            self.assertEqual(output.read_text(), "previous page")
            self.assertFalse((output.parent / ARENA_DATA.name).exists())

    def test_public_counts_reject_stale_stances_before_writing(self):
        import scripts.build_nickname_arena as builder
        rows, _, records = builder.load_opinions()
        rows = json.loads(json.dumps(rows))
        rows[0]["classification"]["stance"] = (SUPPORT if rows[0]["classification"]["stance"] != SUPPORT else "中立・情報")
        with self.assertRaisesRegex(builder.IssueCountError, "正典に一致"):
            builder.apply_planet_counts(PAGE.read_text(), rows, len(records), builder.sample_period(records))

    def test_missing_is_opinion_stops_with_an_error(self):
        """is_opinion が無いレコードは静かに落とさず止める。

        付いていないと論点カードの母数（basis: opinion）から丸ごと消える。
        """
        broken = canonical()
        broken[0]["classification"].pop("is_opinion", None)
        with tempfile.TemporaryDirectory() as directory:
            result = self._build(broken, Path(directory))
        self.assertEqual(result.returncode, 1)
        self.assertIn("is_opinion", result.stderr)

    def test_seo_meta_is_left_to_the_seo_scripts(self):
        """ビルダーは meta description を書かない。

        前身の upgrade_nickname_arena.js は「374件」入りの固定文で3つの
        description を上書きし、apply_theme_trust.py の出力を巻き戻していた。
        """
        source = canonical()
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            self.assertEqual(self._build(source, work).returncode, 0)
            page = (work / "page.html").read_text(encoding="utf-8")
        template = PAGE.read_text(encoding="utf-8")
        for name in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
            start = template.index(name)
            self.assertIn(template[start : template.index(">", start) + 1], page)
        # 調査条件ブロックも apply_theme_trust.py の担当なので、そのまま持ち越す
        head = template.index("<!-- RESEARCH_CONDITIONS_START -->")
        tail = template.index("<!-- RESEARCH_CONDITIONS_END -->") + len("<!-- RESEARCH_CONDITIONS_END -->")
        self.assertIn(template[head:tail], page)

    def test_every_stance_of_an_issue_has_a_label(self):
        """帯に出る4つの立場すべてに短い名前と長い名前がある。

        欠けている立場があると、その件数がページのどこにも出ないまま消える。
        """
        sys.path.insert(0, str(ROOT / "scripts"))
        from build_nickname_arena import ISSUE_DEFS, STANCE_ORDER  # type: ignore[import-not-found]

        for issue in ISSUE_DEFS:
            self.assertCountEqual(issue["stance_labels"], STANCE_ORDER, issue["key"])
            for key, labels in issue["stance_labels"].items():
                self.assertEqual(len(labels), 2, f'{issue["key"]}/{key}')
                self.assertTrue(all(labels), f'{issue["key"]}/{key}')


class NicknameAdapterTests(unittest.TestCase):
    def test_planet_preparation_keeps_whole_previous_snapshot(self):
        from scripts.refresh_adapters.nickname import _run_builder
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            candidate = work / "candidate.json"
            candidate.write_text("[]")
            output = work / "page.html"
            with patch("scripts.refresh_adapters.nickname.subprocess.run") as run:
                _run_builder(ROOT, candidate, PAGE, output)
            run.assert_not_called()
            self.assertEqual(output.read_bytes(), PAGE.read_bytes())
            self.assertEqual((work / ARENA_DATA.name).read_bytes(), ARENA_DATA.read_bytes())

    def test_finalize_runs_checked_whole_page_builder_first(self):
        from scripts.refresh_adapters.nickname import finalize
        with patch("scripts.refresh_adapters.nickname.subprocess.run") as run:
            finalize(ROOT, "2026-09-12")
        calls = run.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0].args[0], [sys.executable, str(BUILDER)])
        self.assertIn("--public-counts-only", calls[1].args[0])
        self.assertTrue(all(call.kwargs["check"] for call in calls))

    def test_vote_definition_stays_v1_with_18_choices(self):
        sys.path.insert(0, str(ROOT))
        from scripts.refresh_adapters.nickname import VOTE_CHOICES, VOTE_TOPIC, vote_fingerprint

        topic, issues, stances, choices = vote_fingerprint(PAGE.read_text(encoding="utf-8"))
        self.assertEqual(topic, VOTE_TOPIC)
        self.assertEqual(choices, VOTE_CHOICES)
        self.assertEqual(len(issues) * len(stances), VOTE_CHOICES)

        edge = (ROOT / "supabase/functions/cast-vote/index.ts").read_text(encoding="utf-8")
        self.assertIn(f'"{VOTE_TOPIC}": {VOTE_CHOICES}', edge)

    def test_vote_fingerprint_ignores_the_counts(self):
        """件数は毎回変わるのが正しい。指紋に入れると更新のたびに止まる。"""
        sys.path.insert(0, str(ROOT))
        from scripts.refresh_adapters.nickname import vote_fingerprint

        page = PAGE.read_text(encoding="utf-8")
        before = vote_fingerprint(page)
        after = vote_fingerprint(page.replace('"count":17', '"count":29'))
        self.assertEqual(before, after)

    def test_arena_data_is_a_publish_target(self):
        """アリーナの点を公開対象から外すと、数字だけ新しく点は古いページになる。"""
        sys.path.insert(0, str(ROOT))
        from scripts.refresh_adapters.nickname import ARENA_DATA as TARGET, PAGE as PAGE_TARGET

        self.assertEqual(TARGET, ARENA_DATA.relative_to(ROOT))
        self.assertEqual(PAGE_TARGET, PAGE.relative_to(ROOT))

    def test_tide_widget_is_not_rebuilt_from_fixed_files(self):
        """潮目は更新回から作る。固定ファイル名が戻ると他テーマごと巻き戻る（課題38）。"""
        sys.path.insert(0, str(ROOT / "scripts"))
        from inject_tide_widget import THEMES  # type: ignore[import-not-found]

        entry = next(item for item in THEMES if item["slug"] == "school-nickname-ban")
        self.assertIsNone(entry["prev_file"])
        self.assertIsNone(entry["cur_file"])

    def test_registered_as_an_adapter_theme(self):
        import yaml

        pipeline = yaml.safe_load((ROOT / "configs/refresh-pipeline.yaml").read_text(encoding="utf-8"))
        themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
        self.assertEqual(pipeline["topics"]["school-nickname-ban"]["adapter"], "nickname")
        self.assertEqual(themes["school-nickname-ban"]["page_update_mode"], "adapter")
        self.assertTrue(themes["school-nickname-ban"]["refresh_at"])

    def test_migration_script_is_archived(self):
        """一度きりの移行用スクリプトを scripts/ に残さない。

        流すと空行が1行増え、SEO meta が374件時代へ戻る。
        """
        self.assertFalse((ROOT / "scripts/upgrade_nickname_arena.js").exists())
        self.assertTrue((ROOT / "archive/scripts/upgrade_nickname_arena.js").exists())


if __name__ == "__main__":
    unittest.main()
