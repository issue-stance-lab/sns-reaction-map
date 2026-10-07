"""scripts/rejudge_ai_copyright_wave.py（ある収集回の判定を、現在のAIで判定し直した結果で置き換える）の検査。

合成データだけで動く（公開CIでも回る）。実データでの置き換えは、正典（非公開）を読むので手元でしか回らない。
見たいことは次のとおり。
- 結果が正典のその回と過不足なく対応しないとき、エラーがあるとき、本文が違うとき、モデルが想定と違うときは止まる。
- 置き換えるのは、指定した回の判定だけ。ほかの回は1文字も変わらない。
- 意見でなくなった／論点が変わった投稿を、再読の記録から外し、区分の件数を合わせる。区分が0件になるなら止まる。
- 公開してよい記録に、本文・投稿IDが入らない。
- 二度目の実行は止まる（二重に適用しない）。
"""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import rejudge_ai_copyright_wave as tool  # noqa: E402

DATE = "2026-09-05"
OTHER_DATE = "2026-09-20"


def cls(opinion=True, issue="学習データ・無断利用", stance="規制・制限強化支持", relevant=True) -> dict:
    return {
        "is_relevant": relevant, "is_opinion": opinion, "main_issue": issue, "stance": stance,
        "intensity": "low", "summary": "要約", "reason": "理由", "confidence": 0.8,
        "article_usable": False, "risk": "low",
    }


def row(tweet_id: str, day: str, classification: dict, text: str | None = None) -> dict:
    return {
        "tweet_id": tweet_id, "url": f"https://x.example/{tweet_id}", "text": text or f"本文{tweet_id}",
        "fetched_at": f"{day}T03:00:00.000Z", "classification": classification,
    }


def canonical() -> list[dict]:
    return [
        row("1", DATE, cls(stance="中立・情報")),                       # 立場だけ変わる
        row("2", DATE, cls()),                                           # 意見でなくなる
        row("3", DATE, cls(issue="学習データ・無断利用")),                # 論点が変わる
        row("4", DATE, cls(opinion=False, relevant=False, issue="その他", stance="中立・情報")),  # 意見になる
        row("5", DATE, cls()),                                           # 変わらない
        row("9", OTHER_DATE, cls(issue="利用者モラル・倫理")),            # 別の回（触らない）
    ]


def redone() -> list[dict]:
    return [
        {**row("1", DATE, cls(stance="規制・制限強化支持"))},
        {**row("2", DATE, cls(opinion=False, issue="その他", stance="中立・情報"))},
        {**row("3", DATE, cls(issue="クリエイター保護・権利"))},
        {**row("4", DATE, cls(issue="法制度・規制整備", stance="推進・活用支持"))},
        {**row("5", DATE, cls())},
    ]


def reread() -> dict:
    def block(items, buckets):
        return {"buckets": {k: {"label": f"区分{k}", "count": v} for k, v in buckets.items()}, "items": items}

    def item(tid, bucket, issue):
        return {"tweet_id": tid, "main_issue": issue, "stance": "規制・制限強化支持", "bucket": bucket, "bucket_label": f"区分{bucket}", "summary": "s", "text_sha256": "x"}

    return {
        "theme": "ai-copyright", "scope": "s", "population": {"意見全体": 10, "5論点合計": 4}, "read_at": "2026-09-13", "method": "m",
        "learning_data": block([item("2", "A", "学習データ・無断利用"), item("3", "A", "学習データ・無断利用"), item("5", "B", "学習データ・無断利用"), item("9", "A", "学習データ・無断利用")], {"A": 3, "B": 1}),
        "creator_rights": block([], {}), "other": block([], {}), "generated_work_rights": block([], {}), "tech_promotion": block([], {}),
    }


class VerifyTest(unittest.TestCase):
    def test_a_matching_result_passes_and_returns_the_wave(self) -> None:
        wave = tool.verify(canonical(), redone(), DATE)
        self.assertEqual([r["tweet_id"] for r in wave], ["1", "2", "3", "4", "5"])

    def test_a_missing_or_extra_post_stops(self) -> None:
        with self.assertRaises(ValueError) as caught:
            tool.verify(canonical(), redone()[:-1], DATE)
        self.assertIn("対応しません", str(caught.exception))
        with self.assertRaises(ValueError):
            tool.verify(canonical(), redone() + [row("77", DATE, cls())], DATE)

    def test_provider_errors_stop(self) -> None:
        bad = redone()
        bad[0]["classification"] = {"error": "upstream_refused: x"}
        with self.assertRaises(ValueError) as caught:
            tool.verify(canonical(), bad, DATE)
        self.assertIn("拒否・エラー", str(caught.exception))

    def test_a_different_text_stops(self) -> None:
        bad = redone()
        bad[1]["text"] = "別の本文"
        with self.assertRaises(ValueError) as caught:
            tool.verify(canonical(), bad, DATE)
        self.assertIn("本文が正典と一致しない", str(caught.exception))

    def test_a_missing_label_stops(self) -> None:
        bad = redone()
        del bad[0]["classification"]["stance"]
        with self.assertRaises(ValueError):
            tool.verify(canonical(), bad, DATE)

    def test_duplicated_ids_stop(self) -> None:
        with self.assertRaises(ValueError):
            tool.verify(canonical(), redone() + [redone()[0]], DATE)

    def test_a_date_with_no_posts_stops(self) -> None:
        with self.assertRaises(ValueError):
            tool.verify(canonical(), redone(), "2026-01-01")


class ReplaceTest(unittest.TestCase):
    def test_only_the_given_wave_changes(self) -> None:
        before = canonical()
        after = tool.replace(before, redone(), DATE)
        self.assertEqual(after[-1], before[-1])  # 別の回は同じ
        self.assertEqual(after[1]["classification"]["is_opinion"], False)
        self.assertEqual(after[3]["classification"]["main_issue"], "法制度・規制整備")
        # 元のデータは書き換えない
        self.assertEqual(before, canonical())
        # 判定以外の項目（本文・URL・取得日時）は、そのまま
        for old, new in zip(before, after):
            self.assertEqual({k: v for k, v in old.items() if k != "classification"}, {k: v for k, v in new.items() if k != "classification"})

    def test_summary_counts_the_changes_without_texts_or_ids(self) -> None:
        wave = tool.verify(canonical(), redone(), DATE)
        after = [r for r in tool.replace(canonical(), redone(), DATE) if tool.collected_day(r) == DATE]
        stats = tool.summarize(wave, after)
        self.assertEqual((stats["rows"], stats["opinions_before"], stats["opinions_after"]), (5, 4, 4))
        self.assertEqual((stats["opinion_lost"], stats["opinion_gained"], stats["kept_opinions"]), (1, 1, 3))
        self.assertEqual((stats["stance_changed"], stats["issue_changed"]), (1, 1))
        self.assertEqual(stats["stance_moves"], {"中立・情報→規制・制限強化支持": 1})
        self.assertEqual(stats["issue_moves"], {"学習データ・無断利用→クリエイター保護・権利": 1})
        self.assertNotIn("本文", json.dumps(stats, ensure_ascii=False))

    def test_dump_matches_the_canonical_format(self) -> None:
        self.assertTrue(tool.dump_json([{"a": "日本語"}]).endswith("\n"))
        self.assertIn("日本語", tool.dump_json([{"a": "日本語"}]))
        self.assertIn('\n  {\n    "a"', tool.dump_json([{"a": 1}]))


class PruneRereadTest(unittest.TestCase):
    def after_rows(self) -> list[dict]:
        return tool.replace(canonical(), redone(), DATE)

    def test_posts_that_lost_opinion_or_changed_issue_are_removed_and_counts_follow(self) -> None:
        new, removed = tool.prune_reread(reread(), self.after_rows(), DATE)
        kept = [item["tweet_id"] for item in new["learning_data"]["items"]]
        self.assertEqual(kept, ["5", "9"])  # 2は意見でなくなった・3は論点が変わった。5と9は変わらない
        self.assertEqual(removed, {"学習データ・無断利用": ["2", "3"]})
        self.assertEqual(new["learning_data"]["buckets"]["A"]["count"], 1)
        self.assertEqual(new["learning_data"]["buckets"]["B"]["count"], 1)
        self.assertEqual(sum(b["count"] for b in new["learning_data"]["buckets"].values()), len(new["learning_data"]["items"]))

    def test_the_history_records_counts_but_no_ids(self) -> None:
        new, _ = tool.prune_reread(reread(), self.after_rows(), DATE)
        history = new["removed_after_read"]
        self.assertEqual(history[0]["count"], 2)
        self.assertEqual(history[0]["wave"], DATE)
        self.assertEqual(history[0]["per_issue"], {"学習データ・無断利用": 2})
        self.assertNotIn('"2"', json.dumps(history, ensure_ascii=False))
        self.assertEqual(new["read_at"], "2026-09-13")  # 読了日は動かさない

    def test_the_input_is_not_modified_and_nothing_changes_when_nothing_is_removed(self) -> None:
        original = reread()
        snapshot = copy.deepcopy(original)
        tool.prune_reread(original, self.after_rows(), DATE)
        self.assertEqual(original, snapshot)
        untouched, removed = tool.prune_reread(reread(), canonical(), DATE)
        self.assertEqual(removed, {})
        self.assertNotIn("removed_after_read", untouched)

    def test_records_of_other_waves_are_never_removed_even_if_they_disagree_with_the_canonical(self) -> None:
        # 9は別の回で、再読の記録は「学習データ」、正典は「利用者モラル・倫理」と食い違っている。それでも外さない。
        new, removed = tool.prune_reread(reread(), self.after_rows(), DATE)
        self.assertIn("9", [item["tweet_id"] for item in new["learning_data"]["items"]])
        self.assertNotIn("9", removed["学習データ・無断利用"])

    def test_a_bucket_that_would_become_empty_stops(self) -> None:
        data = reread()
        data["learning_data"]["items"] = [data["learning_data"]["items"][0]]  # 2だけ。区分Aは1件
        data["learning_data"]["buckets"] = {"A": {"label": "区分A", "count": 1}}
        with self.assertRaises(ValueError) as caught:
            tool.prune_reread(data, self.after_rows(), DATE)
        self.assertIn("0件", str(caught.exception))


class ApplyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        self.canon = self.tmp / "canonical.json"
        self.canon.write_text(tool.dump_json(canonical()), encoding="utf-8")
        self.reread = self.tmp / "reread.json"
        self.reread.write_text(tool.dump_json(reread()), encoding="utf-8")
        self.redone = self.tmp / "redone.json"
        self.redone.write_text(tool.dump_json(redone()), encoding="utf-8")
        self.input = self.tmp / "input.json"
        self.input.write_text(tool.dump_json([{"tweet_id": r["tweet_id"], "text": r["text"]} for r in redone()]), encoding="utf-8")
        self.records = self.tmp / "records"
        self.work = self.tmp / "work"
        patches = [
            mock.patch.object(tool, "canonical_path", lambda: self.canon),
            mock.patch.object(tool, "REREAD", self.reread),
            mock.patch.object(tool, "RECORD_DIR", self.records),
            mock.patch.object(tool, "model_settings", lambda: {"name": "kimi-k2.7-code", "provider": "opencode-go", "config_source": "test"}),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def run_apply(self, **kwargs):
        args = dict(date=DATE, redone_path=self.redone, input_path=self.input, directory=self.work, expected_model="kimi-k2.7-code", dry_run=False)
        args.update(kwargs)
        return tool.apply(**args)

    def test_dry_run_writes_nothing(self) -> None:
        before = (self.canon.read_bytes(), self.reread.read_bytes())
        stats = self.run_apply(dry_run=True)
        self.assertEqual(stats["opinion_lost"], 1)
        self.assertEqual((self.canon.read_bytes(), self.reread.read_bytes()), before)
        self.assertFalse(self.work.exists())
        self.assertFalse(self.records.exists())

    def test_apply_replaces_the_wave_backs_up_and_writes_a_record_without_texts_or_ids(self) -> None:
        before_canon = self.canon.read_bytes()
        stats = self.run_apply()
        after = json.loads(self.canon.read_text(encoding="utf-8"))
        self.assertEqual(after[1]["classification"]["is_opinion"], False)
        self.assertEqual(after[-1], canonical()[-1])  # 別の回
        self.assertEqual((self.work / "canonical-before.json").read_bytes(), before_canon)  # 置き換え前を退避
        self.assertTrue((self.work / "reread-before.json").exists())
        self.assertTrue((self.work / "reread-removed-ids.json").exists())
        record_path = next(self.records.glob("*.json"))
        self.assertEqual(stats["record"], str(record_path))
        text = record_path.read_text(encoding="utf-8")
        for forbidden in ("本文1", "本文2", "本文3", "本文4", "本文5", "https://x.example", '"tweet_id"', '"2"'):
            self.assertNotIn(forbidden, text)
        record = json.loads(text)["run"]
        self.assertEqual(record["wave"], DATE)
        self.assertEqual(record["canonical_sha256_after"], tool.sha256_file(self.canon))
        self.assertNotEqual(record["canonical_sha256_before"], record["canonical_sha256_after"])
        self.assertEqual(record["model"]["name"], "kimi-k2.7-code")
        self.assertEqual(record["opinion_lost"], 1)

    def test_a_second_run_stops_instead_of_applying_twice(self) -> None:
        self.run_apply()
        with self.assertRaises(ValueError) as caught:
            self.run_apply(directory=self.tmp / "work2")
        self.assertIn("すでに適用済み", str(caught.exception))

    def test_an_unexpected_model_stops_before_anything_is_written(self) -> None:
        before = self.canon.read_bytes()
        with self.assertRaises(RuntimeError):
            self.run_apply(expected_model="another-model")
        self.assertEqual(self.canon.read_bytes(), before)
        self.assertFalse(self.work.exists())

    def test_an_existing_backup_is_never_overwritten(self) -> None:
        self.work.mkdir()
        (self.work / "canonical-before.json").write_text("[]", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.run_apply()
        self.assertEqual((self.work / "canonical-before.json").read_text(encoding="utf-8"), "[]")


if __name__ == "__main__":
    unittest.main()
