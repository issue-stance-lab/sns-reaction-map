"""編集部の横断整理（設計書4章の5）の検査。

課題54 段階7-B ステップ3。設計書の例文は数字が手書きで、実データが動いたあとも
直っていなかった（「地域格差は9件」→実際は12件、「教員の働き方は58%」→56.3%）。
台帳には差し込みだけを書かせ、値は生成時に正典から入れる。手書きへ戻ったら落ちる。
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from scripts import public_registry_common as prc

PUBLIC = Path(prc.ROOT) / "data" / "public" / "themes"
LEDGER = Path(prc.ROOT) / "data" / "verification" / "bukatsu-chiiki-editorial.json"


def theme_json(theme_id: str) -> dict:
    return json.loads((PUBLIC / f"{theme_id}.json").read_text(encoding="utf-8"))


def build(findings: list[dict]) -> dict:
    data = theme_json("bukatsu-chiiki")
    original = LEDGER.read_text(encoding="utf-8")
    ledger = json.loads(original)
    ledger["findings"] = findings
    try:
        LEDGER.write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
        return prc.build_editorial_summary("bukatsu-chiiki", data["issues"],
                                           data["opinion_count"])
    finally:
        LEDGER.write_text(original, encoding="utf-8")


class EditorialSummaryContractTest(unittest.TestCase):
    def test_all_ten_themes_have_an_explicit_status(self) -> None:
        seen = 0
        for path in sorted(PUBLIC.glob("*.json")):
            summary = json.loads(path.read_text(encoding="utf-8"))["editorial_summary"]
            self.assertIn(summary["status"], {"complete", "not_started"}, path.stem)
            seen += 1
        self.assertEqual(seen, 10)

    def test_numbers_come_from_the_canonical_data(self) -> None:
        data = theme_json("bukatsu-chiiki")
        counts = {i["id"]: i["count"] for i in data["issues"]}
        text = " ".join(f["text"] for f in data["editorial_summary"]["findings"])
        # 台帳の差し込みが解決され、正典の件数がそのまま出ていること
        self.assertIn(f'{counts["bukatsu-chiiki-kakusa"]}件', text)
        self.assertIn(f'{data["opinion_count"]:,}件', text)

    def test_hand_typed_numbers_are_rejected(self) -> None:
        with self.assertRaises(prc.RegistryError) as caught:
            build([{"id": "x", "kind": "still_unknown", "text": "地域格差は9件しかない。"}])
        self.assertIn("数字を直接書かない", str(caught.exception))

    def test_naming_what_matters_is_rejected(self) -> None:
        # 設計書3.3.2と同じ制限。編集部が重要度を名指ししない
        for phrase in ("本当の問題", "見落とされている"):
            with self.assertRaises(prc.RegistryError):
                build([{"id": "x", "kind": "real_conflict", "text": f"{phrase}はここだ。"}])

    def test_unknown_issue_reference_is_rejected(self) -> None:
        with self.assertRaises(prc.RegistryError):
            build([{"id": "x", "kind": "real_conflict", "text": "{issue:nope.count}が多い。"}])

    def test_unknown_kind_is_rejected(self) -> None:
        with self.assertRaises(prc.RegistryError):
            build([{"id": "x", "kind": "opinion", "text": "ここが分かれる。"}])

    def test_ledger_itself_never_holds_a_number(self) -> None:
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        for item in ledger["findings"]:
            bare = prc._EDITORIAL_REF.sub("", item["text"])
            self.assertIsNone(re.search(r"[0-9０-９]", bare),
                              f'{item["id"]}: 台帳の本文に数字が書かれている')

    def test_theme_without_a_ledger_stays_empty(self) -> None:
        summary = prc.build_editorial_summary("takaichi", [], 0)
        self.assertEqual(summary["status"], "not_started")
        self.assertEqual(summary["findings"], [])
