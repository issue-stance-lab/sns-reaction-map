import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "social-samples/bike-blue-ticket_2d_classified.json"
PAGE = ROOT / "docs/bike-blue-ticket-reaction-map.html"
REREAD = ROOT / "data/bike-blue-ticket_opposition_reread.json"

SUPPORT = "賛成（取締り強化支持）"
OPPOSE = "反対（インフラ・制度優先）"


def canonical() -> list[dict]:
    return json.loads(CANON.read_text(encoding="utf-8"))


def count(records: list[dict], main_issue: str) -> int:
    """論点の件数は正典から数える。

    収集回を足すたびに件数は変わる。期待値をテストに焼き込むと、
    データ更新のたびにテストが落ちて更新そのものが止まる。
    """
    return sum(1 for row in records if is_opinion(row)
               and row["classification"]["main_issue"] == main_issue)


def is_opinion(row: dict) -> bool:
    """ビルダーと同じ規則で数える。

    2026-09-06 に自転車の97件を意見から外したため、全行を数えると
    ビルダーの出力とずれる（それ以前は全468件が意見だった）。
    """
    from scripts.public_registry_common import is_opinion_record
    return is_opinion_record(row)


class BikeArenaBuilderTests(unittest.TestCase):
    """正典から作り直す部分（アリーナ・注目ポイント・帯・内訳）の検査。"""

    def _build(self, records: list[dict], work: Path) -> subprocess.CompletedProcess:
        source = work / "candidate.json"
        source.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
        return subprocess.run(
            [
                sys.executable, str(ROOT / "scripts/build_bike_arena.py"),
                "--input", str(source),
                "--html-template", str(PAGE),
                "--output-html", str(work / "page.html"),
            ],
            cwd=ROOT, capture_output=True, text=True,
        )

    def test_published_page_matches_canonical(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_bike_arena.py"), "--check"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_added_opinion_moves_every_place_that_shows_the_count(self):
        """1件足すと、帯・内訳・投票の説明文・「本当の対立点」がまとめて動く。

        更新のたびに手で直していた場所なので、どこか1つだけ古いまま残らないことを見る。
        """
        source = canonical()
        added = json.loads(json.dumps(next(
            row for row in source
            if row["classification"]["main_issue"] == "インフラ整備優先"
            and row["classification"]["stance"] == OPPOSE
        )))
        added["tweet_id"] = "adapter-test-only"
        added["url"] = "https://example.invalid/adapter-test-only"
        expected = count(source, "インフラ整備優先") + 1
        oppose = sum(
            1 for row in source
            if is_opinion(row)
            and row["classification"]["main_issue"] == "インフラ整備優先"
            and row["classification"]["stance"] == OPPOSE
        ) + 1

        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            result = self._build(source + [added], work)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            page = (work / "page.html").read_text(encoding="utf-8")
            for needle in (
                f"<b>{expected}件</b>",                        # 注目ポイントの内訳
                f"インフラ優先 {oppose}",                       # 帯の右の内訳
                f"インフラ整備優先派（{oppose}件）",             # issue-sides
                f"専用レーンなど道路整備が先決（{expected}件）",  # 投票の説明文
                f"インフラ整備優先{expected}件と",               # 「本当の対立点」
            ):
                # ページ全体を差分に出すと読めないので、見つからない文字列だけを出す
                self.assertTrue(needle in page, f"ページに {needle!r} がありません")

            # 2回目は差分ゼロ
            first = (work / "page.html").read_bytes()
            source_path = work / "candidate.json"
            subprocess.run(
                [
                    sys.executable, str(ROOT / "scripts/build_bike_arena.py"),
                    "--input", str(source_path),
                    "--html-template", str(work / "page.html"),
                    "--output-html", str(work / "page.html"),
                ],
                cwd=ROOT, check=True, capture_output=True,
            )
            self.assertEqual(first, (work / "page.html").read_bytes())

    def test_missing_is_opinion_stops_with_an_error(self):
        """is_opinion が無いレコードは静かに落とさず止める。

        2026-08-17 の更新で、新規174件が論点カードの母数から丸ごと消えた。
        """
        broken = canonical()
        broken[0].pop("is_opinion", None)
        with tempfile.TemporaryDirectory() as directory:
            result = self._build(broken, Path(directory))
        self.assertEqual(result.returncode, 1)
        self.assertIn("is_opinion が無いレコード", result.stderr)

    def test_every_stance_of_an_issue_is_shown(self):
        """論点ブロックの内訳は3つの立場をちょうど1回ずつ覆う。

        覆えていない立場があると、その件数がページのどこにも出ないまま消える。
        """
        sys.path.insert(0, str(ROOT / "scripts"))
        from build_bike_arena import BLOCKS, STANCE_ORDER  # type: ignore[import-not-found]

        for block in BLOCKS:
            covered = [s for _cls, _label, stances, _desc in block["sides"] for s in stances]
            self.assertCountEqual(covered, STANCE_ORDER, block["issue"])


class BikeRereadGateTests(unittest.TestCase):
    """人手の工程（反対投稿の再読）が追いついていなければ止まること。"""

    def test_unread_opposition_post_is_listed_and_stops_the_build(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from build_bike_process_sections import RereadGapError, check_reread_coverage

        source = canonical()
        reread = json.loads(REREAD.read_text(encoding="utf-8"))

        # そのままなら通る
        check_reread_coverage(source, reread)

        added = json.loads(json.dumps(next(
            row for row in source if row["classification"]["stance"] == OPPOSE
        )))
        added["tweet_id"] = "unread-opposition-post"
        added["url"] = "https://example.invalid/unread-opposition-post"
        with self.assertRaises(RereadGapError) as raised:
            check_reread_coverage(source + [added], reread)
        message = str(raised.exception)
        self.assertIn("unread-opposition-post", message)
        self.assertIn("未再読 1件", message)

    def test_swapped_assignment_is_caught_even_though_the_total_matches(self):
        """件数が合っていても、中身が入れ替わっていれば止まる。"""
        sys.path.insert(0, str(ROOT / "scripts"))
        from build_bike_process_sections import RereadGapError, check_reread_coverage

        source = canonical()
        reread = json.loads(json.dumps(json.loads(REREAD.read_text(encoding="utf-8"))))
        reread["buckets"]["abolish"][0] = "stale-assignment"
        with self.assertRaises(RereadGapError) as raised:
            check_reread_coverage(source, reread)
        message = str(raised.exception)
        self.assertIn("未再読 1件", message)
        self.assertIn("stale-assignment", message)


class BikeAdapterTests(unittest.TestCase):
    def test_public_json_drives_page_level_counts(self):
        from scripts.build_bike_arena import apply_public_counts

        public_path = ROOT / "data/public/themes/bike-blue-ticket.json"
        public = json.loads(public_path.read_text(encoding="utf-8"))
        named = [issue for issue in public["issues"] if issue["kind"] == "named"]
        other = next(issue for issue in public["issues"] if issue["kind"] == "other")
        five = sum(int(issue["count"]) for issue in named)
        page = apply_public_counts(PAGE.read_text(encoding="utf-8"), public_path)

        self.assertIn(f'分析対象の意見{public["opinion_count"]}件をAIで整理', page)
        self.assertIn(f'主要5論点{five}件に分類し、残る{other["count"]}件は「その他・分類保留」', page)
        self.assertIn(f'<h2>SNS反応マップ</h2><span>{public["opinion_count"]}件 |', page)

    def test_issue_cards_use_public_json(self):
        config = json.loads(
            (ROOT / "configs/bike-blue-ticket-reaction-map.json").read_text(encoding="utf-8")
        )
        self.assertEqual(config["issue_counts"]["basis"], "public_json")
        self.assertNotIn("lead", config["issue_counts"]["sync"])

    def test_vote_definition_stays_v1_with_18_choices(self):
        sys.path.insert(0, str(ROOT))
        from scripts.refresh_adapters.bike import VOTE_CHOICES, VOTE_TOPIC, vote_fingerprint

        topic, issues, stances, choices = vote_fingerprint(PAGE.read_text(encoding="utf-8"))
        self.assertEqual(topic, VOTE_TOPIC)
        self.assertEqual(choices, VOTE_CHOICES)
        self.assertEqual(len(issues) * len(stances), VOTE_CHOICES)

        edge = (ROOT / "supabase/functions/cast-vote/index.ts").read_text(encoding="utf-8")
        self.assertIn(f'"{VOTE_TOPIC}": {VOTE_CHOICES}', edge)

    def test_tide_widget_is_not_rebuilt_from_fixed_files(self):
        """潮目は更新回から作る。固定ファイル名が戻ると他テーマごと巻き戻る（課題38）。"""
        sys.path.insert(0, str(ROOT / "scripts"))
        from inject_tide_widget import THEMES  # type: ignore[import-not-found]

        entry = next(item for item in THEMES if item["slug"] == "bike-blue-ticket")
        self.assertIsNone(entry["prev_file"])
        self.assertIsNone(entry["cur_file"])

    def test_registered_as_an_adapter_theme(self):
        import yaml

        pipeline = yaml.safe_load((ROOT / "configs/refresh-pipeline.yaml").read_text(encoding="utf-8"))
        themes = yaml.safe_load((ROOT / "THEMES.yaml").read_text(encoding="utf-8"))["themes"]
        self.assertEqual(pipeline["topics"]["bike-blue-ticket"]["adapter"], "bike")
        self.assertEqual(themes["bike-blue-ticket"]["page_update_mode"], "adapter")
        self.assertTrue(themes["bike-blue-ticket"]["refresh_at"])


if __name__ == "__main__":
    unittest.main()
