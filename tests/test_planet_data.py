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
        self.ledger = bpd.load_ocean_layer(TOPIC)
        self._orig_public = bpd.load_public_theme
        self._orig_ledger = bpd.load_ocean_layer

    def tearDown(self) -> None:
        bpd.load_public_theme = self._orig_public
        bpd.load_ocean_layer = self._orig_ledger

    def build(self, public: dict | None = None, ledger: dict | None = None) -> dict:
        bpd.load_public_theme = lambda topic, _p=public or self.public: copy.deepcopy(_p)
        if ledger is not None:
            bpd.load_ocean_layer = lambda topic, _l=ledger: copy.deepcopy(_l)
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

    # ---------------------------------------------------------------- 課題62

    def test_read_at_with_mixed_dates_format_does_not_crash(self):
        """`read_at` が "2026-08-24 / 2026-09-06（追記）" の形でも、最も新しい日付を拾う。"""
        self.assertEqual(bpd.latest_read_date("2026-08-24 / 2026-09-06（追記）"),
                         bpd.date(2026, 9, 6))
        self.assertEqual(bpd.latest_read_date("2026-08-25"), bpd.date(2026, 8, 25))
        with self.assertRaises(SystemExit):
            bpd.latest_read_date("日付なし")

    def test_skipped_posts_fail_the_gate_even_within_40_percent(self):
        """読み飛ばしが1件でもあれば、4割以内でも不合格になる。"""
        data = self.build()
        cfg = bpd.yaml.safe_load((ROOT / "configs" / "planet" / f"{TOPIC}.yaml").read_text())
        issue = next(i for i in data["issues"] if i["sub"]["status"] == "reread")
        issue["sub"]["skipped_count"] = 1
        issue["sub"]["grown_count"] = 0
        ng = bpd.independence_gate(data, cfg)
        self.assertTrue(any("読み飛ばしが1件" in m and issue["label"] in m for m in ng), ng)

    def test_grown_after_read_passes_up_to_40_percent(self):
        """読了後に増えた分だけなら、4割まで合格する。"""
        data = self.build()
        cfg = bpd.yaml.safe_load((ROOT / "configs" / "planet" / f"{TOPIC}.yaml").read_text())
        issue = next(i for i in data["issues"] if i["sub"]["status"] == "reread")
        issue["sub"]["skipped_count"] = 0
        issue["sub"]["grown_count"] = int(0.4 * issue["count"])
        ng = bpd.independence_gate(data, cfg)
        self.assertFalse(any(issue["label"] in m for m in ng), ng)

    def test_grown_after_read_over_40_percent_fails(self):
        """増えた分でも4割を超えれば不合格になる。"""
        data = self.build()
        cfg = bpd.yaml.safe_load((ROOT / "configs" / "planet" / f"{TOPIC}.yaml").read_text())
        issue = next(i for i in data["issues"] if i["sub"]["status"] == "reread")
        issue["sub"]["skipped_count"] = 0
        issue["sub"]["grown_count"] = int(0.4 * issue["count"]) + 1
        ng = bpd.independence_gate(data, cfg)
        self.assertTrue(any("増えた分" in m and issue["label"] in m for m in ng), ng)

    def test_bukatsu_existing_rereads_are_connected_without_skips(self):
        """既存教員54件・制度教育471件を継承し、実読966件を接続する。"""
        data = bpd.build(TOPIC)
        cfg = bpd.yaml.safe_load((ROOT / "configs" / "planet" / f"{TOPIC}.yaml").read_text())
        by_label = {i["label"]: i["sub"] for i in data["issues"]}
        for label, count in [("教員の働き方", 323), ("制度・移行プロセス", 256),
                             ("教育的意義・機会", 215)]:
            self.assertEqual(by_label[label]["reread_count"], count)
            self.assertEqual(by_label[label]["unread_count"], 0)
        self.assertEqual(data["reread_summary"]["connected_editorial_count"], 966)
        self.assertEqual(data["reread_summary"]["not_connected_opinion_count"], 173)
        self.assertEqual(data["reread_summary"]["connected_issue_population"], 1075)
        self.assertEqual(by_label["費用・家庭負担"]["skipped_count"], 0)
        self.assertEqual(by_label["受け皿・指導者"]["skipped_count"], 0)
        self.assertEqual(bpd.independence_gate(data, cfg), [])


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


class PlanetCrossTalkTest(unittest.TestCase):
    """すれ違い装置（立場を切り替えると大陸の順位が入れ替わる）を固定する。

    立場フィルターは以前からあったが、大陸が黙って描き直されるだけで、
    順位が入れ替わったことは画面のどこにも出ていなかった。
    「同じ惑星の上で立場によって地形が変わる」ことが読者に見える状態を保つ。
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.template = (ROOT / "quality" / "prototypes"
                        / "planet-prototype.template.html").read_text()
        cls.data = bpd.stabilize(bpd.build(TOPIC))
        cls.script = max(re.findall(r"<script>(.*?)</script>", cls.template, re.S), key=len)
        m = re.search(r"\nfunction morphTo\(.*?\n\}\n", cls.script, re.S)
        assert m, "morphTo（地形の作り替え）がテンプレートから消えている"
        cls.morph = m.group(0)

    def test_switching_stance_redraws_width_and_height(self):
        # 立場を切り替えたら、幅（件数）と高さ（強い表現）を両方描き直す
        self.assertIn("m.counts[it.id]", self.script, "幅を data から採っていない")
        self.assertIn("m.high_pct[it.id]", self.script, "高さを data から採っていない")
        self.assertIn("render()", self.morph, "立場を切り替えても図を描き直していない")

    def test_switching_stance_keeps_the_reader_in_place(self):
        # 図を勝手に動かさない。狭い画面でだけ、押した結果が見える位置まで運ぶ
        self.assertIn("bringIntoView", self.morph, "狭い画面で結果まで運ぶ処理が無い")
        self.assertIn("window.innerWidth < 820", self.morph, "画面幅の条件が無い")

    def test_rank_comes_from_the_data(self):
        # 順位は data から数える。テンプレートへ書くと、データが増えて順位が
        # 変わっても直らない。「1位」だけは例外で、いちばん大きい大陸を指す
        # 言い方そのもの（どのテーマでも 1 のまま変わらない）。
        self.assertIn("function ranksOf(", self.script, "順位を data から数える関数が無い")
        # 見るのは画面に出る文字だけ。コメント（「1位と2位の差」など仕組みの説明）は外す
        code = re.sub(r"/\*.*?\*/", "", self.template, flags=re.S)
        code = re.sub(r"(?m)^[ \t]*//.*$", "", code)
        found = [x for x in re.findall(r"\d+位", code) if x != "1位"]
        self.assertEqual(found, [], f"テンプレートに手書きの順位がある: {found}")
        self.assertRegex(self.script, r"moved\s*\+\s*'位'",
                         "入れ替わった先の順位を数えずに書いている")

    def test_zero_count_issues_draw_no_hill(self):
        # 0件の論点は山を描かない（幅0の山や、母数0で割った高さを出さない）
        self.assertIn("if (!n) return;", self.script, "0件の論点を除いていない")

    def test_rank_is_reachable_without_the_globe(self):
        # 惑星が見えない読み方（キーボード操作）でも並びの変化を追えること
        self.assertRegex(self.script, r'rank\[i\]\s*\+\s*"位',
                         "論点一覧に順位が出ていない")


class SkylineTest(unittest.TestCase):
    """断面図（山なみ）の検査。球をやめた代わりに、幅と高さの意味を固定する。

    幅＝意見の数、高さ＝強い表現の割合。どちらも「いま選んでいる立場」の件数を
    母数にする。以前は幅だけ立場で絞られ、高さが全体の割合のままで、
    1つの図の中に分母が2つある状態だった。
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.template = (ROOT / "quality" / "prototypes"
                        / "planet-prototype.template.html").read_text()
        cls.data = bpd.stabilize(bpd.build(TOPIC))
        cls.script = max(re.findall(r"<script>(.*?)</script>", cls.template, re.S), key=len)

    def test_width_and_height_share_one_denominator(self):
        for mode in self.data["modes"]:
            for issue in self.data["issues"]:
                key = issue["id"]
                n = mode["counts"][key]
                want_w = round(100 * n / mode["total"], 2) if mode["total"] else 0.0
                self.assertAlmostEqual(mode["width_pct"][key], want_w, places=2,
                                       msg=f"{mode['label']}/{key}: 幅が件数と合わない")
                want_h = round(100 * mode["high_counts"][key] / n, 1) if n else 0.0
                self.assertAlmostEqual(mode["high_pct"][key], want_h, places=1,
                                       msg=f"{mode['label']}/{key}: 高さが同じ母数で数えられていない")

    def test_height_really_changes_by_stance(self):
        """立場ごとに高さが変わること。ここが変わらないなら、球のときと同じで
        「高さが表現されていない」状態に戻っている。"""
        rates = {m["label"]: m["high_pct"]["bukatsu-chiiki-ukezara"] for m in self.data["modes"]}
        self.assertGreater(max(rates.values()) - min(rates.values()), 10,
                           f"立場を変えても高さがほとんど動かない: {rates}")

    def test_the_globe_is_gone(self):
        for gone in ("canvas", "getContext", "yaw", "coastNoise", "weights_by_mode"):
            self.assertNotIn(gone, self.script, f"球の名残が残っている: {gone}")
        self.assertIn('id="section"', self.template, "断面図の描画先が無い")

    def test_a_hill_taller_than_the_axis_is_marked(self):
        """上限を超えた山を、上限どまりの高さのまま描かない。"""
        self.assertIn("clippedPath", self.script, "頂上を切る描き方が無い")
        self.assertIn("v.clipped", self.script)
        self.assertRegex(self.script, r'v\.clipped\?"▲"', "切れた山に実測値の印が付いていない")

    def test_small_samples_and_widened_hills_are_disclosed(self):
        self.assertIn("SMALL=30", self.script.replace(" ", ""), "母数が小さい山の断りが無い")
        self.assertIn("実際の割合より広く描いています", self.script,
                      "押せる幅まで広げたことを書いていない")


class PlanetDotsTest(unittest.TestCase):
    """点の装置（立場を絞ると件数は減るのに割合は増える、を見せる）を固定する。

    「323件→182件と減るのに 28.4%→39.6% と増える」が文章では通じなかったため、
    投稿1件＝点1つで見せる装置を入れた。数字は data から作り、
    3Dが使えない環境でも同じことが読めるようにしてある。
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.template = (ROOT / "quality" / "prototypes"
                        / "planet-prototype.template.html").read_text()
        cls.data = bpd.stabilize(bpd.build(TOPIC))
        cls.page = bpd.render_page(cls.data, cls.template, "null")
        cls.static = re.sub(r"<script.*?</script>", "", cls.page, flags=re.S)
        cls.script = max(re.findall(r"<script>(.*?)</script>", cls.template, re.S), key=len)

    def test_device_is_built_from_the_data(self):
        self.assertIn('id="waffle"', self.template, "点の装置がテンプレートから消えている")
        self.assertIn("const CELLS = 100;", self.script, "マスの数が100でない")
        self.assertIn("D.totals.opinions", self.script, "母数を data から採っていない")
        self.assertIn("m.counts[it.id]", self.script, "件数を data から採っていない")

    def test_device_sits_next_to_the_controls(self):
        """升目は着陸パネルの先頭側へ置く。

        最初は戻るボタンの直前（1,500px超のパネルの末尾）に置いたため、
        立場ボタンを押しても結果が画面外で「押しても何も起きない」ように見えた。
        """
        slot = self.script.index('<div id="dot-slot"></div>')
        rest = self.script.index("legend() + stanceBar(")
        self.assertLess(slot, rest,
                        "升目が着陸パネルの後ろにある（押した結果が画面外に出る）")
        self.assertIn("bringIntoView(document.getElementById(\"panel\"))", self.script,
                      "画面が狭いときに、選んだ論点のパネルまで運ぶ処理が無い")

    def test_scrolling_does_not_rely_on_smooth_or_animation_frames(self):
        """スクロールが必ず届くこと。

        scrollIntoView({behavior:"smooth"}) は効かない環境があり、
        requestAnimationFrame は画面が見えていないと止まる。どちらに頼っても届かなかった。
        """
        fn = re.search(r"function bringIntoView\(el\)\{.*?\n\}", self.script, re.S).group(0)
        self.assertNotIn('behavior', fn, "効かない環境がある smooth に頼っている")
        self.assertGreaterEqual(fn.count("setTimeout"), 2,
                                "rAF が止まる環境向けの取りこぼし対策が無い")

    def test_every_issue_colour_separates_from_the_muted_dots(self):
        """色つきのマスと灰色のマスが、明るさで見分けられること。

        大陸の色はどれも白を混ぜた淡い色なので、灰を明るくすると全7色が
        見分けの基準を下回る（実際に一度下回った。色差15に対し9〜14しか無かった）。
        明るさの差で見るのは、色が見分けにくい人にも効くため。
        """
        rest = self._rgb(re.search(r"--rest-dot:\s*(#[0-9a-fA-F]{6})", self.template).group(1))
        for issue in self.data["issues"]:
            stance = next(s for s in self.data["stances"] if s["key"] == issue["top_stance"])
            # continentRGB(it,"all") と同じ式: 白へ 0.58〜1.00 の割合で寄せる
            purity = issue["purity_pct"] / 100
            t = min(1.0, max(0.0, (purity - 0.30) / 0.45))
            hot = [236 + (c - 236) * (0.58 + 0.42 * t) for c in self._rgb(stance["color"])]
            ratio = self._contrast(hot, rest)
            self.assertGreaterEqual(
                ratio, 1.5,
                f"{issue['label']}: 色つきと灰色のマスの明暗差が {ratio:.2f}倍しかない")

    @staticmethod
    def _rgb(h):
        return [int(h[i:i + 2], 16) for i in (1, 3, 5)]

    @staticmethod
    def _luminance(c):
        def ch(v):
            v /= 255
            return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
        r, g, b = (ch(x) for x in c)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    @classmethod
    def _contrast(cls, a, b):
        la, lb = cls._luminance(a), cls._luminance(b)
        return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

    def test_stance_shares_are_readable_without_javascript(self):
        # 3Dも点も動かない環境で、同じこと（立場ごとの割合）が読めること
        text = re.sub(r"<[^>]+>", " ", self.static)
        self.assertIn("立場ごとに、その立場の中でこの論点が占める割合", text)
        self.assertIn("件数が減っても、その中での割合は増えることがあります", text)
        for issue in self.data["issues"]:
            for mode in self.data["modes"]:
                if not mode["total"]:
                    continue
                n = mode["counts"][issue["id"]]
                want = f'{n}件 / {100 * n / mode["total"]:.1f}%'
                self.assertIn(want, self.static,
                              f"{issue['label']} / {mode['label']} の割合が静的表示に無い")


class DevicesTest(unittest.TestCase):
    """滞在の仕掛け（予想・潜水・一次資料クイズ・探査記録）を固定する。

    どれも「読ませる量を増やす」のではなく「読者に手を動かさせて答え合わせをする」
    ための仕掛け。数字と論点名・立場名は全部 data から採る（テンプレートに書かない）。
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.template = (ROOT / "quality" / "prototypes"
                        / "planet-prototype.template.html").read_text()
        cls.data = bpd.stabilize(bpd.build(TOPIC))
        cls.script = max(re.findall(r"<script>(.*?)</script>", cls.template, re.S), key=len)
        cls.page = bpd.render_page(cls.data, cls.template, "null")
        cls.static = re.sub(r"<script.*?</script>", "", cls.page, flags=re.S)

    def test_quiz_uses_every_checked_claim(self):
        """クイズの出題は、照合済みの主張ぜんぶ。"""
        self.assertIn("claims", self.data, "平らな主張一覧が出ていない")
        ids = [c["id"] for c in self.data["claims"]]
        self.assertEqual(len(ids), len(set(ids)), "主張が重複している")
        public = json.loads(
            (ROOT / "data" / "public" / "themes" / f"{TOPIC}.json").read_text())
        self.assertEqual(ids, [c["id"] for c in public["claim_verification"]["claims"]],
                         "公開データの主張と数・順序が合わない")
        for c in self.data["claims"]:
            self.assertIn(c["verdict"], ("fact", "gap", "miss"), c["id"])
            self.assertTrue(c["verdict_label"], c["id"])
            self.assertTrue(c["finding"], c["id"])

    def test_devices_take_their_wording_from_the_data(self):
        # 選択肢に論点名・立場名を書くと、他テーマで意味が通らなくなる
        for issue in self.data["issues"]:
            self.assertNotIn(issue["label"], self.script,
                             f"テンプレートに論点名『{issue['label']}』が入っている")
        for stance in self.data["stances"]:
            self.assertNotIn(stance["key"], self.script,
                             f"テンプレートに立場名『{stance['key']}』が入っている")

    def test_progress_counts_every_stop(self):
        """探査記録の分母。数え漏らすと進み具合が100%を超える（実際に超えた）。"""
        self.assertRegex(
            self.script,
            r"const SPOTS = 2 \+ issues\.length \+ .*sunk_continents.*\n?.*claims.*veins",
            "地点の数え方が、予想2＋論点＋沈んだ大陸＋主張＋地下水脈になっていない")
        self.assertIn("Math.min(100,", self.script, "進み具合が100%で頭打ちになっていない")

    def test_progress_stays_on_the_device(self):
        """読んだ記録は端末の中だけ。サーバーへ送らない。"""
        self.assertIn("localStorage", self.script)
        for sent in ("fetch(", "XMLHttpRequest", "navigator.sendBeacon"):
            self.assertNotIn(sent, self.script, f"読んだ記録を外へ送っている（{sent}）")

    def test_below_sea_is_readable_without_javascript(self):
        """潜水はJSの飾り。JSが動かないときは海面下が出たままであること。"""
        self.assertIn('id="ocean"', self.static, "海面下のセクションが静的HTMLに無い")
        self.assertNotIn('id="ocean" class="ocean" hidden', self.static,
                         "JS無効時に海面下が隠れている")
        self.assertIn('box.hidden = !dived', self.script, "潜水がJS側で開閉していない")


class PlanetOceanPageTest(unittest.TestCase):
    """段階7-B: 着陸パネルの「資料との照合」と「海面より下」が画面に出ること。

    段階6で生成器が `ocean` を出していたのに、テンプレートは一度も読んでいなかった
    （`grep ocean` が0件）。設計書4章の画面構造3・4が画面から丸ごと落ちていたので、
    出ていることをテストで固定する。
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.template = (ROOT / "quality" / "prototypes" / "planet-prototype.template.html").read_text()
        cls.data = bpd.stabilize(bpd.build(TOPIC))
        cls.page = bpd.render_page(cls.data, cls.template, "null")
        cls.static = re.sub(r"<script.*?</script>", "", cls.page, flags=re.S)

    def test_template_keeps_every_insertion_point(self):
        # 差し込み口を消すと画面からセクションが丸ごと消える。消えたら落ちるようにする
        for mark in ("/*__PLANET_DATA__*/null", "<!--__QUESTION__-->", "<!--__CAUTION__-->",
                     "<!--__META__-->", "<!--__FALLBACK__-->", "<!--__OCEAN__-->",
                     "<!--__EDITORIAL__-->"):
            self.assertIn(mark, self.template, f"差し込み口 {mark} が消えている")
        with self.assertRaises(bpd.TemplateError):
            bpd.render_page(self.data, self.template.replace("<!--__OCEAN__-->", ""), "null")

    def test_the_chart_scales_with_the_screen(self):
        """図は SVG なので、幅が変わっても描き直さずに伸縮する。

        canvas のときは実寸で描いていたため、幅が変わるたびに描き直す必要があり、
        初回に文字が巨大なまま残る不具合が出ていた。
        """
        self.assertIn('viewBox="0 0 900 500"', self.template, "SVG の座標系が無い")
        self.assertIn(".chart-box svg{display:block;width:100%;height:auto}", self.template,
                      "図が画面幅に合わせて伸縮しない")

    def test_verdict_labels_are_fixed(self):
        # 課題54の「未着手」5: verdict と表示文言の対応を固定するテストが無かった
        self.assertEqual(set(bpd.VERDICT_LABELS), {"fact", "gap", "miss"})
        self.assertEqual(bpd.verdict_label("fact"), "資料どおり")
        self.assertEqual(bpd.verdict_label("gap"), "少しずれる")
        self.assertEqual(bpd.verdict_label("miss"), "裏が取れない")
        # miss を「嘘」「誤り」と断定しない（設計書3.3の読者への注意）
        self.assertNotIn("嘘", bpd.VERDICT_LABELS["miss"][1])
        with self.assertRaises(SystemExit):
            bpd.verdict_label("unknown")

    def test_claims_appear_with_their_verdict(self):
        for issue in self.data["issues"]:
            for claim in issue.get("claims") or []:
                self.assertIn(claim["claim"], self.static, claim["id"])
                self.assertIn(bpd.verdict_label(claim["verdict"]), self.static)
                for src in claim["sources"]:
                    self.assertIn(src["url"], self.static, claim["id"])

    def test_ocean_section_shows_every_item(self):
        ocean = self.data["ocean"]
        self.assertIn('id="ocean"', self.static)
        for item in ocean["sunk_continents"]:
            self.assertIn(item["topic"], self.static, item["id"])
            self.assertIn(item["life_impact"], self.static, item["id"])
            # 0件も「0件」と母数つきで出す（設計書3.3.2）
            self.assertIn(f'{item["sns_count"]}件', self.static)
            self.assertIn(f'意見{item["sns_base"]}件', self.static)
        for vein in ocean["veins"]:
            self.assertIn(vein["shared_concern"], self.static, vein["id"])
            self.assertIn(vein["diverging_reason"], self.static, vein["id"])

    def test_ocean_is_left_empty_when_nobody_has_read_the_sources(self):
        # 台帳が無いテーマは推測で埋めない（設計書3.3）
        blank = copy.deepcopy(self.data)
        blank["ocean"] = {"claim_status": "not_started", "checked_on": None,
                          "reviewer_type": None, "ocean_status": "not_started",
                          "ocean_checked_on": None, "ocean_reviewer_type": None,
                          "sunk_continents": [], "veins": []}
        html = bpd.static_ocean(blank)
        self.assertIn("まだ編集部が一次資料を読んで", html)
        self.assertNotIn("沈んだ大陸 —", html)

    def test_internal_field_names_do_not_reach_the_reader(self):
        text = re.sub(r"<[^>]+>", " ", self.static)
        for token in ("issue_bucket", "match_rule", "machine_hits", "tweet_id",
                      "representative_posts", "classification"):
            self.assertNotIn(token, text, f"読者向けの本文に内部の項目名『{token}』が出ている")

    def test_editorial_summary_is_on_the_page(self):
        # 設計書4章の5。論点をまたいだ整理が画面から落ちていないこと
        ed = self.data["editorial"]
        self.assertEqual(ed["status"], "complete")
        self.assertIn('id="editorial"', self.static)
        for finding in ed["findings"]:
            self.assertIn(finding["text"], self.static, finding["id"])
        for heading in bpd.EDITORIAL_HEADINGS.values():
            self.assertIn(heading, self.static)

    def test_editorial_is_left_empty_when_nothing_is_written(self):
        blank = copy.deepcopy(self.data)
        blank["editorial"] = {"status": "not_started", "checked_on": None,
                              "reviewer_type": None, "findings": []}
        html = bpd.static_editorial(blank)
        self.assertIn("まだです", html)
        for heading in bpd.EDITORIAL_HEADINGS.values():
            self.assertNotIn(heading, html)

    def test_landing_panel_html_exists_once(self):
        # 3D版のJSは静的HTMLを複製して使う。生成HTMLに同じ塊が2つあってはいけない
        for issue in self.data["issues"]:
            self.assertLessEqual(self.static.count(f'id="extras-{issue["id"]}"'), 1)
