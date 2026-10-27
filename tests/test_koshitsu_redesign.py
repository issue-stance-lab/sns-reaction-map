"""皇室典範改正・新デザインの公開候補と更新経路（docs/ は書き換えない）。"""
from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from scripts import koshitsu_layout as layout
from scripts import build_koshitsu_redesign as redesign
from scripts.build_koshitsu_redesign import ALIASES, PAGE, ROOT, VOTE_TOPIC, build

AS_OF = "2026-10-11"

# 2026-10-27 から実設定の law.enforcement_confirmed_on に日付が入っている。このファイルの試験の多くは
# 施行日より前・施行直後（未確認）の時制を調べるので、実設定の値のときだけ読み込み時に外す。
# 試験の中で別の日付を設定した場合（施行後の確認済みの試験）は、そのまま使う。
_REAL_CONFIRMED = json.loads((ROOT / "configs/koshitsu-tenpakai-opening.json").read_text(encoding="utf-8"))["law"].get("enforcement_confirmed_on")
_patches: list = []


def setUpModule():
    import sys
    from unittest import mock

    sys.path.insert(0, str(ROOT / "scripts"))
    import koshitsu_reading  # noqa: PLC0415

    original = koshitsu_reading.load

    def load_without_real_confirmation(path):
        data = original(path)
        law = data["ocfg"]["law"]
        if _REAL_CONFIRMED and law.get("enforcement_confirmed_on") == _REAL_CONFIRMED:
            law["enforcement_confirmed_on"] = None
        return data

    patcher = mock.patch.object(koshitsu_reading, "load", load_without_real_confirmation)
    patcher.start()
    _patches.append(patcher)


def tearDownModule():
    while _patches:
        _patches.pop().stop()


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


PUBLIC = json.loads((ROOT / "docs/data/themes/koshitsu-tenpakai.json").read_text(encoding="utf-8"))
REREAD = json.loads((ROOT / "data/koshitsu-tenpakai_issues-reread.json").read_text(encoding="utf-8"))
INPUTS = (
    "THEMES.yaml",
    "docs/data/themes/koshitsu-tenpakai.json",
    "data/koshitsu-tenpakai_issues-reread.json",
    "data/verification/koshitsu-tenpakai-source-checks.json",
    "data/verification/koshitsu-tenpakai-background.json",
    "quality/research/koshitsu-tenpakai-primary-sources.md",
)


def vote_block(text: str, name: str) -> str:
    return re.search(r"var " + name + r"=\[(.*?)\];", text, re.S).group(1)


class RedesignCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name)
        cls.source_path = layout.source_for_refresh(ROOT)
        cls.source = cls.source_path.read_text(encoding="utf-8")
        build(cls.source_path, out / "release", "release", as_of=AS_OF)
        build(cls.source_path, out / "preview", "preview", as_of=AS_OF)
        cls.release = (out / "release" / PAGE).read_text(encoding="utf-8")
        cls.preview = (out / "preview" / PAGE).read_text(encoding="utf-8")
        cls.s = BeautifulSoup(cls.release, "html.parser")
        cls.out = out

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_same_input_same_output(self):
        build(self.source_path, self.out / "again", "release", as_of=AS_OF)
        self.assertEqual(self.release, (self.out / "again" / PAGE).read_text(encoding="utf-8"))

    def test_refuses_docs_and_new_page_input(self):
        with self.assertRaisesRegex(ValueError, "docs"):
            build(self.source_path, ROOT / "docs", "release", as_of=AS_OF)
        with tempfile.TemporaryDirectory() as temp:
            page = Path(temp) / "new.html"
            page.write_text(self.release, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "入力にできません"):
                build(page, Path(temp) / "out", "release", as_of=AS_OF)

    def test_seo_blocks_and_title_are_inherited_verbatim(self):
        for name in ("SEO_META", "ARTICLE_JSON_LD"):
            block = re.search(f"<!-- {name}_START -->.*?<!-- {name}_END -->", self.source, re.S).group()
            self.assertEqual(self.release.count(block), 1, name)
        self.assertEqual(self.s.head.title.get_text(), BeautifulSoup(self.source, "html.parser").head.title.get_text())
        self.assertEqual(self.s.select('link[rel="canonical"]')[0]["href"],
                         "https://sns-reaction-map.jp/koshitsu-tenpakai-reaction-map.html")

    def test_ga_and_adsense_only_in_release(self):
        for name in ("GA_TAG", "ADSENSE_TAG"):
            block = re.search(f"<!-- {name}_START -->.*?<!-- {name}_END -->", self.source, re.S).group()
            self.assertIn(block, self.release)
            self.assertNotIn(block, self.preview)
        self.assertIn('content="ca-pub-2542211932832864"', self.release)
        self.assertIn('name="robots" content="noindex"', self.preview)
        self.assertNotIn('name="robots"', self.release)

    def test_vote_contract_is_unchanged(self):
        for text in (self.release, self.preview):
            self.assertIn(f'data-vote-topic="{VOTE_TOPIC}"', text)
            self.assertIn(f"var TOPIC='{VOTE_TOPIC}'", text)
            self.assertEqual(vote_block(self.source, "VOTE_ISSUES"), vote_block(text, "VOTE_ISSUES"))
            self.assertEqual(vote_block(self.source, "STANCES"), vote_block(text, "STANCES"))
            self.assertIn("choiceIdx:issueIdx*STANCES.length+stanceIdx", text)
            self.assertIn("(window.SNS_REDESIGN_PRODUCTION?'sns_vote_':'sns_vote_preview_')+TOPIC+'_my'", text)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=location.hostname==='sns-reaction-map.jp'", self.release)
        self.assertIn("window.SNS_REDESIGN_PRODUCTION=false", self.preview)
        scripts = self.s.select("script")
        config = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-config.js"))
        client = next(i for i, x in enumerate(scripts) if (x.get("src") or "").startswith("vote-store.js"))
        self.assertEqual(config + 2, client)

    def test_counts_match_public_json_and_reread(self):
        self.assertIn(f'{int(PUBLIC["opinion_count"]):,}', self.s.select_one(".ko-total b").get_text())
        for issue in PUBLIC["issues"]:
            panel = self.s.find(id="issue-" + issue["id"])
            self.assertIsNotNone(panel, issue["id"])
            self.assertEqual(panel.select_one(".kr-count b").get_text(), f'{int(issue["count"]):,}')
            for bucket_id, bucket in REREAD["buckets"][issue["label"]].items():
                node = panel.select_one(f'li.kr-reason[data-reason="{bucket_id}"] .kr-reason-n b')
                self.assertEqual(node.get_text(), f'{int(bucket["count"]):,}', (issue["id"], bucket_id))

    def test_faq_json_ld_matches_visible_faq(self):
        payloads = [json.loads(s.get_text()) for s in self.s.select('script[type="application/ld+json"]')]
        faq = next(p for p in payloads if p.get("@type") == "FAQPage")
        visible = [(d.dt.get_text(strip=True), d.dd.get_text(strip=True)) for d in self.s.select("#bg-faq dl.kb-faq > div")]
        self.assertEqual(len(visible), 6)
        self.assertEqual([(q["name"], q["acceptedAnswer"]["text"]) for q in faq["mainEntity"]], visible)
        self.assertEqual(sum(1 for p in payloads if p.get("@type") == "Article"), 1)

    def test_public_contract_conditions_and_links(self):
        self.assertEqual(len(self.s.select("#planet-data")), 1)
        self.assertIn("社会全体の世論調査ではありません。", self.s.select_one("#caution").get_text())
        self.assertNotIn("../../../docs/", self.release)
        hrefs = {a["href"] for a in self.s.select("footer a[href]")}
        for href in ("about.html#operator", "about.html#method", "privacy.html", "disclaimer.html"):
            self.assertIn(href, hrefs)
        self.assertIn('href="about.html#corrections"', self.release)
        self.assertTrue(self.s.select('#related-topics a[href$="reaction-map.html"]'))
        for iso in (str(PUBLIC["updated_on"]), "2026-07-18"):
            self.assertIn(f'<time datetime="{iso}">', self.release)

    def test_planet_is_copied_from_source(self):
        """全体像の山なみは、元HTMLの対話式の山なみ（PLANET_SECTION）をそのまま写す（2026-10-11 に静的SVGから戻した）。"""
        src_section = re.search(r"<!-- PLANET_SECTION_START -->(.*?)<!-- PLANET_SECTION_END -->", self.source, re.S).group(1)
        src = soup_of(src_section)
        # 山なみのスクリプト・見た目・PLANET_DATA は1文字も変えない
        src_script = [x for x in src.find_all("script", recursive=False) if x.get("id") != "planet-data"][0].string
        self.assertEqual(self.release.count(src_script), 1)
        self.assertEqual(self.release.count(src.select_one("section.planet-panel > style").string), 1)
        self.assertEqual(self.release.count("window.PLANET_DATA="), 1)
        # 山なみは読書面の全体像の中。静的SVGと論点名リストは無い
        planet = self.s.select_one("#koshitsu-reading .kr-map section.planet-panel #planet-block")
        self.assertIsNotNone(planet)
        self.assertEqual(self.s.select(".kr-mountains, .kr-chip, .kr-map-shell"), [])
        # 立場モード・100マス・論点の一覧・見かた・図が使えないときの一覧は、元HTMLと同じ
        for sel in ("#modes", ".stage", "#dotbox", "#list", "#meta", ".floor-note", ".hint"):
            self.assertEqual(str(planet.select_one(sel)), str(src.select_one("#planet-block " + sel)), sel)
        self.assertEqual(planet.select_one("#fallback-nav").get_text(), src.select_one("#fallback-nav").get_text())
        # JSなしの論点一覧は新しい読書面へ直接つながる
        hrefs = [a["href"] for a in planet.select("#fallback-nav a")]
        self.assertEqual(sorted(hrefs), sorted("#issue-" + i["id"] for i in PUBLIC["issues"]))
        for href in hrefs:
            self.assertIsNotNone(self.s.find(id=href[1:]), href)
        # 新デザインで出さない部分（JSなし用の論点別本文・資料にしかない話・編集部整理）は外し、予想・クイズ・進捗は受け皿だけ
        self.assertEqual(planet.select("section.landing-panel, #ocean, #editorial"), [])
        for receiver in ("#guesses", "#quiz"):
            node = planet.select_one(receiver)
            self.assertTrue(node.has_attr("hidden") and not node.get_text(strip=True), receiver)
        self.assertTrue(self.s.select_one("#progress").has_attr("hidden"))
        # 調査条件は山なみの中（図の母数の位置）で、RESEARCH_CONDITIONS に囲まれている
        self.assertEqual(len(self.s.select("#caution")), 1)
        self.assertIsNotNone(planet.select_one("#research-conditions > #caution"))
        block = self.release[self.release.index("<!-- RESEARCH_CONDITIONS_START -->"):self.release.index("<!-- RESEARCH_CONDITIONS_END -->")]
        self.assertIn('id="caution"', block)
        # 山なみのスクリプトより後で、読書面（reading.js）と橋渡し（planet.js）が動く
        self.assertLess(self.release.index(src_script), self.release.index("window.KoshitsuReading"))
        self.assertLess(self.release.index("window.KoshitsuReading"), self.release.index("function goReading"))
        # 論点IDは PLANET_DATA・公開JSON・読書面で同じ（変換表は要らない）
        data = json.loads(re.search(r"window\.PLANET_DATA=(\{.*?\});?</script>", self.release, re.S).group(1))
        self.assertEqual(sorted(i["id"] for i in data["issues"]), sorted(i["id"] for i in PUBLIC["issues"]))
        for issue in data["issues"]:
            self.assertIsNotNone(self.s.select_one(f'[data-issue-panel="{issue["id"]}"]'), issue["id"])
        # 旧ページ用の部品は読み込まない（山なみの説明文には名前が出ることがある）
        for name in ('koshitsu-connected.js', 'koshitsu-connected-page.js', 'koshitsu-connected.css', 'theme-design.js', 'theme-design.css'):
            self.assertNotIn(f'="{name}', self.release)

    def test_planet_follows_source_updates(self):
        """定期更新で元HTMLの山なみが変われば、新ページにもそのまま載る（手入力なし）。"""
        changed = self.source.replace("このページの見かた", "このページの見かた（更新確認）", 1)
        self.assertNotEqual(changed, self.source)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.html"
            path.write_text(changed, encoding="utf-8")
            redesign.build(path, Path(temp) / "out", "release", as_of=AS_OF)
            page = (Path(temp) / "out" / redesign.PAGE).read_text(encoding="utf-8")
        self.assertIn("このページの見かた（更新確認）", page)
        broken = re.sub(r'<div class="dotbox" id="dotbox".*?<div class="waffle" id="waffle"></div>', "", self.source, count=1,
                        flags=re.S)
        self.assertNotEqual(broken, self.source)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.html"
            path.write_text(broken, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "山なみの部品"):
                redesign.build(path, Path(temp) / "out", "release", as_of=AS_OF)

    def test_old_anchor_targets_exist(self):
        for target in set(redesign.ALIASES.values()):
            self.assertIsNotNone(self.s.find(id=target), target)
        for alias in redesign.ALIASES:
            # 読み替えるのは、新ページに無いIDか、山なみのスクリプトのために隠して残した受け皿だけ
            if alias in redesign.HIDDEN_RECEIVERS:
                continue
            self.assertIsNone(self.s.find(id=alias), alias)
        for receiver in redesign.HIDDEN_RECEIVERS:
            self.assertIn(receiver, redesign.ALIASES)
            self.assertIsNotNone(self.s.find(id=receiver), receiver)
        # 受け皿は表示されていない（JSがあるとき）ので、旧アンカーは表示中の要素へ送る
        self.assertIn("cur.getClientRects().length", self.release)
        self.assertIsNotNone(self.s.find(id="planet-block"))
        self.assertNotIn("planet-block", redesign.ALIASES)

    def test_no_eager_x_widget_and_original_links_remain(self):
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.release)
        for embed in self.s.select(".x-embed"):
            self.assertRegex(embed.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")


class CompactReadingTests(unittest.TestCase):
    """2026-10-12 部活動型の圧縮（生成AIと著作権・副首都と同じ型）：見せる量だけを減らし、文・件数・出典は折りたたみの中にそのまま残す。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.source_path = layout.source_for_refresh(ROOT)
        build(cls.source_path, Path(cls.tmp.name), "release", as_of=AS_OF)
        cls.release = (Path(cls.tmp.name) / PAGE).read_text(encoding="utf-8")
        cls.s = soup_of(cls.release)
        cls.cfg = json.loads((ROOT / "configs/koshitsu-tenpakai-reading.json").read_text(encoding="utf-8"))
        cls.top = int(cls.cfg["compact"]["top_reasons"])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_folds_start_closed(self):
        """読書面と背景（作り方・詳細データの行を含む）の折りたたみは、初期表示ですべて閉じている。"""
        self.assertEqual([d.get("class") for d in self.s.select("details[open]")], [])
        rows = self.s.select("#koshitsu-background details.kb-row")
        self.assertGreaterEqual(len(rows), 7)
        self.assertIsNotNone(self.s.select_one("details#bg-method"))
        self.assertIsNotNone(self.s.select_one("details#bg-table"))

    def test_tabs_cover_all_issues(self):
        tabs = self.s.select("#koshitsu-reading nav.kr-tabs a.kr-tab")
        self.assertEqual(sorted(a["data-issue-id"] for a in tabs), sorted(i["id"] for i in PUBLIC["issues"]))
        self.assertEqual([a["href"] for a in tabs], ["#issue-" + a["data-issue-id"] for a in tabs])
        self.assertEqual(len([a for a in tabs if a.get("aria-current") == "true"]), 1)
        self.assertTrue(all(a.select_one(".kr-tab-icon").get_text() for a in tabs))

    def test_description_first_paragraph_then_more(self):
        for iid, icfg in self.cfg["issues"].items():
            head = self.s.find(id="issue-" + iid).select_one(".kr-panel-head")
            shown = [p.get_text() for p in head.select("p.kr-desc") if not p.find_parent("details")]
            folded = [p.get_text() for p in head.select("details.kr-desc-more p.kr-desc")]
            self.assertEqual(shown, icfg["description"][:1], iid)
            self.assertEqual(folded, icfg["description"][1:], iid)
            self.assertIsNotNone(head.select_one('.kr-back a[href="#koshitsu-reading"]'), iid)

    def test_reason_index_top_rows_and_one_open_detail(self):
        for issue in PUBLIC["issues"]:
            iid, buckets = issue["id"], REREAD["buckets"][issue["label"]]
            panel = self.s.find(id="issue-" + iid)
            rows = panel.select(".kr-reasons li.kr-reason")
            visible = [li for li in rows if not li.find_parent("details")]
            self.assertEqual(len(rows), len(buckets), iid)
            self.assertEqual(len(visible), min(self.top, len(rows)), iid)
            counts = [int(li.select_one(".kr-reason-n b").get_text().replace(",", "")) for li in rows]
            self.assertEqual(counts, sorted(counts, reverse=True), iid)
            if len(rows) > self.top:
                self.assertIn(f"ほかの{len(rows) - self.top}区分", panel.select_one("details.kr-reason-more").summary.get_text(), iid)
            details = panel.select("article.kr-reason-detail")
            self.assertEqual([a["data-reason"] for a in details], [li["data-reason"] for li in rows], iid)
            self.assertEqual([a["data-reason"] for a in details if a.has_attr("data-on")], [rows[0]["data-reason"]], iid)
            for li in rows:
                self.assertEqual(li.a["href"], f'#kr-r-{iid}-{li["data-reason"]}')
                self.assertIsNotNone(panel.find(id=f'kr-r-{iid}-{li["data-reason"]}'))
            voices = self.cfg["issues"][iid].get("reasons", {})
            self.assertEqual(len(panel.select("article.kr-reason-detail .kr-voice")),
                             len([b for b in buckets if voices.get(b, {}).get("voice")]), iid)

    def test_evidence_items_are_folds_with_visible_heading(self):
        for panel in self.s.select(".kr-panel.is-complete"):
            for node in panel.select("[data-claim], [data-memo-check], [data-sunk], [data-concern], [data-check]"):
                self.assertEqual(node.name, "details", (panel["id"], node.attrs))
                self.assertFalse(node.has_attr("open"))
                self.assertTrue(node.summary.get_text().strip(), (panel["id"], node.attrs))
                self.assertIsNotNone(node.find_parent(class_="kr-evidence"), (panel["id"], node.attrs))
            for node in panel.select("[data-claim]"):
                self.assertIsNotNone(node.summary.select_one(".kr-verdict"), panel["id"])
            for sel in (".kr-stance", ".kr-posts", ".kr-trend"):
                self.assertEqual(panel.select_one(sel).name, "details", (panel["id"], sel))
            self.assertIsNotNone(panel.select_one(".kr-evidence .kr-evidence-about .kr-lead"), panel["id"])

    def test_concerns_and_sunk_kept_with_same_text(self):
        """同じ心配から違う結論へ・資料にしかない話は、根拠の欄の折りたたみに移しただけで、文は公開JSONのまま。"""
        for v in PUBLIC["ocean_layer"]["veins"]:
            for iid in v["issue_ids"]:
                node = self.s.find(id="issue-" + iid).select_one(f'[data-concern="{v["id"]}"]')
                self.assertEqual(node.summary.get_text(), v["shared_concern"])
                self.assertIn(v["diverging_reason"], node.get_text())
        for x in PUBLIC["ocean_layer"]["sunk_continents"]:
            node = self.s.find(id="issue-" + x["nearest_issue_id"]).select_one(f'[data-sunk="{x["id"]}"]')
            self.assertEqual(node.summary.get_text(), x["topic"])
            self.assertIn(x["life_impact"], node.get_text())

    def test_hash_into_closed_fold_opens_it(self):
        self.assertIn("t.closest('details')", self.release)
        self.assertIn("h.startsWith('kr-r-' + x + '-')", self.release)  # 区分名のハイフン（other-evaluation など）でも理由が開く

    def test_provenance_reads_reason_details(self):
        from scripts.koshitsu_redesign_provenance import verified_selectors
        node = self.s.select_one("#issue-koshitsu-tenpakai-patrilineal-matrilineal article.kr-reason-detail .kr-eyebrow span")
        text = node.get_text()
        n = re.match(r"(\d[\d,]*)件", text).group(1)
        broken = self.release.replace(str(node), str(node).replace(f"{n}件", f"{int(n.replace(',', '')) + 1}件", 1), 1)
        self.assertNotEqual(broken, self.release)
        with self.assertRaisesRegex(ValueError, "一致しません"):
            verified_selectors(broken, ROOT)


class LayoutTests(unittest.TestCase):
    def _root(self, temp: str) -> Path:
        root = Path(temp)
        shutil.copytree(ROOT / "configs", root / "configs")
        shutil.copytree(ROOT / "scripts/koshitsu_redesign", root / "scripts/koshitsu_redesign")
        shutil.copytree(ROOT / "docs/images/topics/koshitsu-tenpakai", root / "docs/images/topics/koshitsu-tenpakai")
        for name in INPUTS:
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, root / name)
        shutil.copy2(layout.source_for_refresh(ROOT), root / layout.PAGE)
        return root

    def test_disabled_has_no_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            (root / layout.CONFIG).write_text('{"enabled": false}')
            before = (root / layout.PAGE).read_bytes()
            self.assertEqual(layout.finish(root, as_of=AS_OF), {})
            layout.materialize(root)
            self.assertEqual(before, (root / layout.PAGE).read_bytes())
            self.assertFalse((root / layout.SOURCE).exists())

    def test_repository_layout_state_is_consistent(self):
        published = layout.MARKER in (ROOT / layout.PAGE).read_text(encoding="utf-8")
        if published:  # 公開後：設定が有効で、元HTMLがある
            self.assertTrue(layout.enabled(ROOT))
            self.assertTrue((ROOT / layout.SOURCE).is_file())
        else:  # 公開前：docs/ は旧形式のまま
            self.assertFalse(layout.enabled(ROOT))

    def test_new_page_without_source_stops(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "configs").mkdir()
            (root / layout.PAGE).write_text('<meta name="koshitsu-layout">')
            (root / layout.CONFIG).write_text('{"enabled": true}')
            with self.assertRaisesRegex(ValueError, "更新元HTML"):
                layout.source_for_refresh(root)
            (root / layout.CONFIG).write_text('{"enabled": false}')
            with self.assertRaisesRegex(ValueError, "更新設定が無効"):
                layout.source_for_refresh(root)

    def test_pipeline_finish_keeps_source_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            legacy = (root / layout.PAGE).read_text(encoding="utf-8")
            (root / layout.CONFIG).write_text('{"enabled": true}')
            targets = layout.finish(root, as_of=AS_OF)
            self.assertEqual(set(targets), {layout.SOURCE, layout.PAGE})
            first = (root / layout.PAGE).read_bytes()
            self.assertIn(b'name="koshitsu-layout"', first)
            self.assertEqual(legacy, (root / layout.SOURCE).read_text(encoding="utf-8"))
            self.assertEqual(layout.source_for_refresh(root), root / layout.SOURCE)
            # 次の更新：隔離コピーで元HTMLを戻し、旧形式の処理の後に再適用すると同じページになる
            layout.materialize(root)
            self.assertEqual(legacy, (root / layout.PAGE).read_text(encoding="utf-8"))
            layout.finish(root, as_of=AS_OF)
            self.assertEqual(first, (root / layout.PAGE).read_bytes())
            with self.assertRaisesRegex(ValueError, "再入力"):
                layout.finish(root, as_of=AS_OF)

    def test_count_mismatch_stops_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            (root / layout.CONFIG).write_text('{"enabled": true}')
            reread = json.loads((root / "data/koshitsu-tenpakai_issues-reread.json").read_text(encoding="utf-8"))
            reread["items"].pop()
            (root / "data/koshitsu-tenpakai_issues-reread.json").write_text(json.dumps(reread, ensure_ascii=False))
            before = (root / layout.PAGE).read_bytes()
            with self.assertRaisesRegex(ValueError, "照合で停止"):
                layout.finish(root, as_of=AS_OF)
            self.assertEqual(before, (root / layout.PAGE).read_bytes())
            self.assertFalse((root / layout.SOURCE).exists())

    # ---- 施行日（2026-10-24）以降の時制。施行日を過ぎても生成を止めない（止まると全テーマの公開候補生成が止まる）

    def _set_json(self, path: Path, edit) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        edit(data)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _background(self, page: bytes) -> BeautifulSoup:
        return BeautifulSoup(page.decode("utf-8"), "html.parser").select_one("#koshitsu-background")

    def test_after_enforcement_generates_unconfirmed_text(self):
        for as_of in ("2026-10-24", "2027-01-10"):
            with self.subTest(as_of=as_of), tempfile.TemporaryDirectory() as temp:
                root = self._root(temp)
                (root / layout.CONFIG).write_text('{"enabled": true}')
                layout.finish(root, as_of=as_of)
                page = (root / layout.PAGE).read_bytes()
                s = BeautifulSoup(page.decode("utf-8"), "html.parser")
                self.assertEqual(s.select_one("#koshitsu-opening")["data-phase"], "after_unconfirmed")
                bg = self._background(page).get_text()
                self.assertNotIn("施行されます", bg)
                self.assertNotIn("施行予定", bg)
                self.assertIn("施行される予定でした", bg)
                self.assertIn("まだ編集部で確かめていません", bg)
                self.assertIn("施行日はいつですか", bg)
                # 構造化データのFAQも画面と同じ時制
                self.assertNotIn("施行されます", re.search(r'"FAQPage".*?</script>', page.decode("utf-8"), re.S).group())

    def test_confirmed_date_switches_to_after_text(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            (root / layout.CONFIG).write_text('{"enabled": true}')
            self._set_json(root / "configs/koshitsu-tenpakai-opening.json",
                           lambda d: d["law"].update(enforcement_confirmed_on="2026-10-26"))
            layout.finish(root, as_of="2026-10-30")
            page = (root / layout.PAGE).read_bytes()
            s = BeautifulSoup(page.decode("utf-8"), "html.parser")
            self.assertEqual(s.select_one("#koshitsu-opening")["data-phase"], "after_confirmed")
            bg = self._background(page).get_text()
            self.assertIn("施行されました", bg)
            self.assertIn("2026年10月26日に確かめています", bg)
            self.assertNotIn("まだ編集部で確かめていません", bg)
            self.assertNotIn("切り替わったかどうかは、まだ確かめていません", bg)

    def test_confirmed_date_before_enforcement_stops(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            (root / layout.CONFIG).write_text('{"enabled": true}')
            self._set_json(root / "configs/koshitsu-tenpakai-opening.json",
                           lambda d: d["law"].update(enforcement_confirmed_on="2026-10-20"))
            with self.assertRaisesRegex(ValueError, "enforcement_confirmed_on"):
                layout.finish(root, as_of="2026-10-30")

    def test_missing_after_text_stops_before_enforcement_date(self):
        """施行後の文が欠けていたら、施行日より前の更新で止める（施行日当日の更新で初めて止まらないように）。"""
        def drop(d):
            for g in d["groups"]:
                for row in g["rows"]:
                    if row["kind"] == "faq":
                        row["items"][0].pop("phase")
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            (root / layout.CONFIG).write_text('{"enabled": true}')
            self._set_json(root / "configs/koshitsu-tenpakai-background.json", drop)
            with self.assertRaisesRegex(ValueError, "施行後"):
                layout.finish(root, as_of=AS_OF)

    def test_other_theme_candidate_run_is_not_stopped_after_enforcement(self):
        """refresh_topic の公開候補生成（単一・複数テーマ）は as_of を渡さずに finish を呼ぶ。
        皇室の公開JSONの更新日が施行日を過ぎていても、他テーマの候補生成を止めない。"""
        with tempfile.TemporaryDirectory() as temp:
            root = self._root(temp)
            (root / layout.CONFIG).write_text('{"enabled": true}')
            self._set_json(root / "docs/data/themes/koshitsu-tenpakai.json", lambda d: d.update(updated_on="2026-10-25"))
            themes = (root / "THEMES.yaml").read_text(encoding="utf-8")
            block = re.search(r"\n  koshitsu-tenpakai:\n(?:    .*\n)+", themes).group()
            fixed = re.sub(r"(\n    updated_at: )['\"]?[0-9-]+['\"]?", r"\g<1>2026-10-25", block, count=1)
            (root / "THEMES.yaml").write_text(themes.replace(block, fixed), encoding="utf-8")
            targets = layout.finish(root)
            self.assertEqual(set(targets), {layout.SOURCE, layout.PAGE})
            self.assertIn("施行される予定でした", self._background((root / layout.PAGE).read_bytes()).get_text())
        refresh = (ROOT / "scripts/refresh_topic.py").read_text(encoding="utf-8")
        self.assertEqual(refresh.count("finish_koshitsu_layout(candidate_root)"), 2)


if __name__ == "__main__":
    unittest.main()
