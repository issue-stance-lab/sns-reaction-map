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

    def test_terrain_is_interpolated_between_modes(self):
        # 重みを直に読むと、立場を切り替えた瞬間に地形が飛ぶ（作り替えが見えない）
        self.assertIn("st.wCur", self.script, "補間中の重み st.wCur が無い")
        self.assertNotIn("D.weights_by_mode[st.mode]", self.script,
                         "モードの重みを直に描いている。作り替えの途中が飛ぶ")

    def test_mode_switch_does_not_turn_the_globe(self):
        # 新しい1位へ球を回すと、順位を落とした大陸が裏側へ行き、
        # いちばん見せたい「縮むところ」が見えなくなる（実測で確認済み）
        for attr in ("st.yaw =", "st.pitch =", "st.yaw=", "st.pitch="):
            self.assertNotIn(attr, self.morph,
                             f"立場の切り替えで球を回している（{attr}）")

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

    def test_zero_count_continents_disappear(self):
        # 0件の論点は weights_by_mode では 0.0 のまま。そのまま描くと
        # 「0件なのにいちばん大きい大陸」になる。確実に消える重みへ落とすこと
        self.assertIn("FLOOR", self.script, "0件の大陸を消すための重みが無い")
        floor = float(re.search(r"const FLOOR\s*=\s*(-?[\d.]+)", self.script).group(1))
        self.assertLessEqual(floor, -2.0,
                             "FLOOR が浅い。内積の差は最大2なので大陸が残る")

    def test_rank_is_reachable_without_the_globe(self):
        # 惑星が見えない読み方（キーボード操作）でも並びの変化を追えること
        self.assertRegex(self.script, r'rank\[i\]\s*\+\s*"位',
                         "論点一覧に順位が出ていない")


class PlanetSeaTest(unittest.TestCase):
    """海を入れても「面積＝意見の数」が崩れないことを固定する。

    大陸のあいだを海にすると、境界のまわりが一律に削られる。何もしないと
    周囲の長さに比例して削れるので、小さい大陸ほど損をして面積が件数と合わなくなる。
    面積合わせを「陸の中の比」で行うことでこれを避けている。
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.template = (ROOT / "quality" / "prototypes"
                        / "planet-prototype.template.html").read_text()
        cls.data = bpd.stabilize(bpd.build(TOPIC))
        cls.script = max(re.findall(r"<script>(.*?)</script>", cls.template, re.S), key=len)

    def test_land_area_still_matches_the_opinion_counts(self):
        for mode in self.data["modes"]:
            for key, want in mode["area_pct"].items():
                got = mode["area_actual_pct"][key]
                self.assertAlmostEqual(
                    got, want, delta=0.15,
                    msg=f"{mode['label']} / {key}: 面積{got}% が目標{want}% と合わない")

    def test_sea_takes_a_visible_share_but_never_drowns_a_continent(self):
        for mode in self.data["modes"]:
            self.assertGreater(mode["sea_pct"], 15, f"{mode['label']}: 海が狭すぎる")
            self.assertLess(mode["sea_pct"], 65, f"{mode['label']}: 海が広すぎる")
            for key, want in mode["area_pct"].items():
                if want > 0:
                    self.assertGreater(
                        mode["area_actual_pct"][key], 0,
                        f"{mode['label']} / {key}: 大陸が海に沈んで消えている")

    def test_coastline_noise_is_the_same_on_both_sides(self):
        # 生成器とテンプレートで振幅が食い違うと、測った面積と描く面積がずれる
        self.assertEqual(self.data["coast_noise_amp"], bpd.COAST_NOISE_AMP)
        self.assertIn("D.coast_noise_amp", self.script,
                      "テンプレートが振幅を data から受け取っていない")
        for term in ("6.7*x + 2.9*y + 11.3*z", "3.1*x + 13.1*y - 7.7*z",
                     "17.1*x - 5.3*y + 23.3*z"):
            self.assertIn(term, self.script, f"海岸線のゆらぎの式が生成器と違う: {term}")

    def test_every_continent_name_sits_on_land(self):
        """大陸名は、その立場での陸の上に置く。

        名前の位置を全立場で共通にしていたため、縮んだ大陸の名前が海の上に浮いていた
        （中立・情報の「費用・家庭負担」。3件まで縮むので陸が名前の位置まで届かない）。
        海を入れる前は球面が隙間なく大陸で埋まっていたので起きなかった。
        """
        import numpy as np
        d = self.data
        centers = np.array([i["center"] for i in d["issues"]])
        coast, amp = d["coast_margin"], d["coast_noise_amp"]
        for mode in d["modes"]:
            w = np.array(d["weights_by_mode"][mode["id"]])
            off = np.array([0.0 if mode["counts"][i["id"]] > 0 else -10.0
                            for i in d["issues"]])
            spots = d["centroid_by_mode"][mode["id"]]
            for k, issue in enumerate(d["issues"]):
                if mode["counts"][issue["id"]] == 0:
                    continue
                v = np.array(spots[k])
                score = centers @ v + w + off
                ranked = np.sort(score)
                margin = ranked[-1] - ranked[-2]
                n = float(bpd.coast_noise(v.reshape(1, 3))[0])
                margin += amp * n * max(0.0, 1 - abs(margin - coast) / amp)
                self.assertGreaterEqual(
                    margin, coast,
                    f"{mode['label']} / {issue['label']}: 大陸名が海の上に浮いている")
                self.assertEqual(
                    int(np.argmax(score)), k,
                    f"{mode['label']} / {issue['label']}: 大陸名が他の大陸の上にある")

    def test_the_page_says_the_sea_has_no_meaning(self):
        # 意味のない地形を意味ありげに見せない（設計書12）
        page = bpd.render_page(self.data, self.template, "null")
        static = re.sub(r"<script.*?</script>", "", page, flags=re.S)
        self.assertIn("青い海と海岸線の形には意味がありません", static)


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
        self.assertIn('id="dotbox"', self.template, "点の装置がテンプレートから消えている")
        # 点の数は「立場ごとの件数」の合計。テンプレートに件数を書いてはいけない
        self.assertIn("it.stances[s.key]", self.script, "点を data から作っていない")
        self.assertIn("D.totals.opinions", self.script, "母数を data から採っていない")

    def test_dot_class_does_not_collide_with_the_issue_list(self):
        # 論点一覧の丸も .dot を使っている。同じ名前にすると打ち消し合う
        self.assertIn(".dotframe .pdot{position:absolute", self.template,
                      "点の装置が既存の .dot と同じ名前を使っている")

    def test_every_issue_colour_separates_from_the_muted_dots(self):
        """色つきの点と灰色の点が、明るさで見分けられること。

        大陸の色はどれも白を混ぜた淡い色なので、灰を明るくすると全7色が
        見分けの基準を下回る（実際に一度下回った。色差15に対し9〜14しか無かった）。
        明るさの差で見るのは、色が見分けにくい人にも効くため。
        """
        rest = self._rgb(re.search(r'const REST_DOT = "(#[0-9a-fA-F]{6})"', self.script).group(1))
        for issue in self.data["issues"]:
            stance = next(s for s in self.data["stances"] if s["key"] == issue["top_stance"])
            # continentRGB(it,"all") と同じ式: 白へ 0.58〜1.00 の割合で寄せる
            purity = issue["purity_pct"] / 100
            t = min(1.0, max(0.0, (purity - 0.30) / 0.45))
            hot = [236 + (c - 236) * (0.58 + 0.42 * t) for c in self._rgb(stance["color"])]
            ratio = self._contrast(hot, rest)
            self.assertGreaterEqual(
                ratio, 1.5,
                f"{issue['label']}: 色つきの点と灰色の点の明暗差が {ratio:.2f}倍しかない")

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

    def test_the_planet_is_redrawn_when_its_width_changes(self):
        # 文字の大きさは canvas の表示幅から決めている。初回の render は
        # レイアウトが決まる前に走ることがあり、375px で文字が巨大なまま残っていた
        self.assertIn("ResizeObserver", self.template)
        self.assertIn("observe(cv)", self.template)

    def test_verdict_labels_are_fixed(self):
        # 課題54の「未着手」5: verdict と表示文言の対応を固定するテストが無かった
        self.assertEqual(set(bpd.VERDICT_LABELS), {"fact", "gap", "miss"})
        self.assertEqual(bpd.verdict_label("fact"), "実像")
        self.assertEqual(bpd.verdict_label("gap"), "ずれ")
        self.assertEqual(bpd.verdict_label("miss"), "蜃気楼")
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
