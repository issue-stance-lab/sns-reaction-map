"""`scripts/build_planet_data.py`（惑星データの生成器）の検査。

2026-09-03 の段階6レビューで、次の3つが「間違っても止まらない」まま通ることが分かった。
このテストは、その3つが再発したら落ちる形で固定する。

- 指摘1: 立場を表示ラベルの文字列一致で集計していた（言い換えると件数が欠け、色が変わる）
- 指摘2: 海面下の母数が台帳に焼き込まれ、データが増えても同じ数字のままだった
- 指摘3: 設定ファイルに無い論点idを黙って捨てていた（画面の合計が合わなくなる）
"""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location("build_planet_data",
                                               ROOT / "scripts" / "build_planet_data.py")
bpd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bpd)

TOPIC = "bukatsu-chiiki"


def public_fixture() -> dict:
    return json.loads((ROOT / "data" / "public" / "themes" / f"{TOPIC}.json").read_text())


class PlanetDataTest(unittest.TestCase):
    def setUp(self) -> None:
        self.public = public_fixture()
        self.ledger = bpd.load_ocean_ledger(TOPIC)
        self._orig_public = bpd.load_public_theme
        self._orig_ledger = bpd.load_ocean_ledger

    def tearDown(self) -> None:
        bpd.load_public_theme = self._orig_public
        bpd.load_ocean_ledger = self._orig_ledger

    def build(self, public: dict | None = None, ledger: dict | None = None) -> dict:
        bpd.load_public_theme = lambda topic, _p=public or self.public: copy.deepcopy(_p)
        if ledger is not None:
            bpd.load_ocean_ledger = lambda topic, _l=ledger: copy.deepcopy(_l)
        return bpd.build(TOPIC)

    # ---------------------------------------------------------------- 基本

    def test_counts_follow_public_json(self):
        """件数・母数・立場の合計が公開JSONと一致する。"""
        data = self.build()
        by_id = {i["id"]: i for i in data["issues"]}
        for pub in self.public["issues"]:
            self.assertEqual(by_id[pub["id"]]["count"], pub["count"], pub["id"])
        self.assertEqual(data["totals"]["opinions"], self.public["opinion_count"])
        self.assertEqual(sum(s["count"] for s in data["stances"]),
                         self.public["opinion_count"])
        self.assertEqual(sum(i["count"] for i in data["issues"]),
                         self.public["opinion_count"])

    def test_stance_label_rename_does_not_change_numbers(self):
        """指摘1: 立場の表示文言を言い換えても、件数も色も変わらない。"""
        before = self.build()
        renamed = copy.deepcopy(self.public)
        for issue in renamed["issues"]:
            for stance in issue["stances"]:
                stance["label"] = stance["label"] + "（見直し要求）"
        after = self.build(renamed)
        self.assertEqual([s["count"] for s in before["stances"]],
                         [s["count"] for s in after["stances"]])
        self.assertEqual([(i["id"], i["top_stance"], i["stances"]) for i in before["issues"]],
                         [(i["id"], i["top_stance"], i["stances"]) for i in after["issues"]])

    def test_unknown_stance_id_stops(self):
        """公開JSONに未登録の立場idがあれば、黙って捨てずに止まる。"""
        broken = copy.deepcopy(self.public)
        broken["issues"][0]["stances"][0]["id"] = "bukatsu-chiiki-brand-new-stance"
        with self.assertRaises(SystemExit) as cm:
            self.build(broken)
        self.assertIn("bukatsu-chiiki-brand-new-stance", str(cm.exception))

    # ---------------------------------------------------------------- 指摘3

    def test_unknown_issue_id_stops_and_names_it(self):
        """指摘3: 未登録の論点idは捨てずに止め、追記すべきidを表示する。"""
        added = copy.deepcopy(self.public)
        added["issues"].append({
            "id": "bukatsu-chiiki-newtopic", "label": "新しい論点", "count": 50,
            "stances": [{"id": "bukatsu-chiiki-transition-support", "label": "移行支持", "count": 50}],
            "intensities": [{"id": "high", "count": 10}, {"id": "medium", "count": 20},
                            {"id": "low", "count": 20}],
        })
        added["opinion_count"] += 50
        added["issue_assigned_count"] += 50
        with self.assertRaises(SystemExit) as cm:
            self.build(added)
        message = str(cm.exception)
        self.assertIn("bukatsu-chiiki-newtopic", message)
        self.assertIn("configs/planet/bukatsu-chiiki.yaml", message)

    def test_issue_total_mismatch_stops(self):
        """論点別の合計と公開JSONの意見数が食い違えば止まる。"""
        broken = copy.deepcopy(self.public)
        broken["issues"][0]["count"] += 7
        with self.assertRaises(SystemExit) as cm:
            self.build(broken)
        self.assertIn("issue_assigned_count", str(cm.exception))

    # ---------------------------------------------------------------- 指摘2

    def test_ledger_base_is_not_trusted_blindly(self):
        """指摘2: 台帳の母数が古ければ印を付け、独自性の検査で公開を止める。"""
        stale = copy.deepcopy(self.ledger)
        stale["sunk_continents"][0]["sns_base"] = 999
        data = self.build(ledger=stale)
        first = data["ocean"]["sunk_continents"][0]
        self.assertTrue(first["base_stale"])
        self.assertEqual(first["sns_base"], 999, "人が読んだ時点の母数は書き換えない")
        self.assertEqual(first["opinion_count_now"], self.public["opinion_count"])
        cfg = bpd.yaml.safe_load((ROOT / "configs" / "planet" / f"{TOPIC}.yaml").read_text())
        self.assertTrue(any("母数" in ng for ng in bpd.independence_gate(data, cfg)))

    def test_ledger_counts_are_not_recalculated(self):
        """人が読んで確定した件数（sns_count）は機械で数え直さない。"""
        data = self.build()
        ledger_counts = [i["sns_count"] for i in self.ledger["sunk_continents"]]
        self.assertEqual([i["sns_count"] for i in data["ocean"]["sunk_continents"]],
                         ledger_counts)

    def test_base_matches_today(self):
        """いまの台帳と公開JSONの母数が一致している（ズレたらここで気づく）。"""
        data = self.build()
        self.assertEqual([i["base_stale"] for i in data["ocean"]["sunk_continents"]],
                         [False] * len(self.ledger["sunk_continents"]))

    # ---------------------------------------------------------------- 指摘4

    def test_veins_are_linked_to_issues(self):
        """指摘4: 地下水脈が台帳の issue_ids どおりに論点へ結ばれる。"""
        data = self.build()
        by_id = {i["id"]: i for i in data["issues"]}
        for vein in self.ledger["veins"]:
            for issue_id in vein["issue_ids"]:
                self.assertIn(vein["id"], by_id[issue_id]["veins"])
        linked = {v for i in data["issues"] for v in i["veins"]}
        self.assertEqual(linked, {v["id"] for v in self.ledger["veins"]})

    def test_vein_with_unknown_issue_stops(self):
        broken = copy.deepcopy(self.ledger)
        broken["veins"][0]["issue_ids"] = ["bukatsu-chiiki-nonexistent"]
        with self.assertRaises(SystemExit) as cm:
            self.build(ledger=broken)
        self.assertIn("bukatsu-chiiki-nonexistent", str(cm.exception))

    def test_theme_without_ledger_has_empty_ocean(self):
        """台帳が無いテーマは推測で埋めず、海面下が空で出る。"""
        data = self.build(ledger={"sunk_continents": [], "veins": []})
        self.assertEqual(data["ocean"]["sunk_continents"], [])
        self.assertEqual(data["ocean"]["veins"], [])
        self.assertEqual([i["veins"] for i in data["issues"]], [[]] * len(data["issues"]))

    # ---------------------------------------------------------------- 指摘6

    def test_unknown_verdict_message(self):
        """指摘6: 知らない判定語は KeyError ではなく、読めるメッセージで止まる。"""
        broken = copy.deepcopy(self.public)
        broken["claim_verification"]["claims"][0]["verdict"] = "たぶん正しい"
        with self.assertRaises(SystemExit) as cm:
            self.build(broken)
        self.assertIn("たぶん正しい", str(cm.exception))

    def test_verdict_is_the_strictest_of_matched_claims(self):
        """1論点に複数の主張が付いたら miss > gap > fact の順で最も厳しい判定を採る。"""
        self.assertEqual(bpd.issue_verdict("x", [
            {"id": "a", "verdict": "fact", "issue_ids": ["x"]},
            {"id": "b", "verdict": "miss", "issue_ids": ["x"]},
            {"id": "c", "verdict": "gap", "issue_ids": ["x"]},
        ])[0], "miss")
        self.assertEqual(bpd.issue_verdict("y", [{"id": "a", "verdict": "fact",
                                                  "issue_ids": ["x"]}]), (None, []))

    # ---------------------------------------------------------------- 設定

    def test_config_stances_have_public_ids(self):
        """設定ファイルの立場に、公開JSONの立場idが書かれている。"""
        cfg = bpd.yaml.safe_load((ROOT / "configs" / "planet" / f"{TOPIC}.yaml").read_text())
        cfg_ids = {s["id"] for s in cfg["stances"]}
        public_ids = {s["id"] for i in self.public["issues"] for s in i["stances"]}
        self.assertEqual(public_ids - cfg_ids, set())


if __name__ == "__main__":
    unittest.main()


class PlanetPageTest(unittest.TestCase):
    """段階7レビューの指摘を固定する。

    試作HTMLのフォールバック（3Dが描けないときの静的表示）に、件数と割合が
    手書きで入っていた。同じページの中で「28.5%」と「28.4%」が併存し、
    JSを切ると本文が消え、7本のうち6本がリンク切れだった。
    生成器が data から作る形へ直したので、手書きへ戻ったら落ちるようにする。
    """

    TEMPLATE = ROOT / "quality" / "prototypes" / "planet-prototype.template.html"

    @classmethod
    def setUpClass(cls) -> None:
        cls.template = cls.TEMPLATE.read_text()
        cls.data = bpd.stabilize(bpd.build(TOPIC))
        cls.page = bpd.render_page(cls.data, cls.template, "null")
        cls.static = re.sub(r"<script.*?</script>", "", cls.page, flags=re.S)

    def test_template_has_no_hardcoded_numbers(self):
        # 「323件」「28.5%」のような数字をテンプレートへ書くと、正典とずれても誰も気づかない
        found = re.findall(r"\d{2,4}件|\d+\.\d%", self.template)
        self.assertEqual(found, [], f"テンプレートに手書きの数字がある: {found}")

    def test_template_has_no_theme_specific_stance_labels(self):
        # テンプレートは10テーマ共通。特定テーマの立場名でCSSを書くと他テーマで無色になる
        for label in (s["key"] for s in self.data["stances"]):
            self.assertNotIn(label, self.template,
                             f"テンプレートにテーマ固有の立場名『{label}』が入っている")

    def test_every_in_page_link_has_a_destination(self):
        hrefs = set(re.findall(r'href="#([^"]+)"', self.static))
        ids = set(re.findall(r'id="([^"]+)"', self.static))
        self.assertEqual(hrefs - ids, set(), "飛び先の無いページ内リンクがある")

    def test_readable_without_javascript(self):
        # 完了条件「JavaScriptが使えなくても、論点・比率・理由・一次資料を読める」
        text = re.sub(r"<[^>]+>", " ", self.static)
        for it in self.data["issues"]:
            self.assertIn(it["label"], text, f"JS無効時に論点『{it['label']}』が読めない")
            self.assertIn(f"{it['count']}件", text)
        self.assertIn("landing-panel", self.static)
        self.assertIn("https://", self.static, "JS無効時に一次資料のリンクが無い")

    def test_static_numbers_come_from_the_data(self):
        for it in self.data["issues"]:
            self.assertIn(f"{it['count']}件・{it['share_pct']}%", self.static)
            self.assertIn(f"強い表現{it['high_adjusted_pct']}%", self.static)

    def test_floats_are_rounded_so_rebuilds_match(self):
        # 重みの当てはめは足す順序で最後の桁が動く。丸めないと再生成のたびに差分が出る
        def floats(o):
            if isinstance(o, float):
                yield o
            elif isinstance(o, dict):
                for v in o.values():
                    yield from floats(v)
            elif isinstance(o, list):
                for v in o:
                    yield from floats(v)

        for x in floats(self.data):
            self.assertEqual(x, round(x, 12), f"丸められていない値がある: {x!r}")

    def test_rebuilding_gives_the_same_page(self):
        again = bpd.render_page(bpd.stabilize(bpd.build(TOPIC)), self.template, "null")
        self.assertEqual(self.page, again)
