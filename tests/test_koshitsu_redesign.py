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
from scripts.build_koshitsu_redesign import ALIASES, PAGE, ROOT, VOTE_TOPIC, build

AS_OF = "2026-10-11"
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

    def test_old_anchor_targets_exist(self):
        for target in set(ALIASES.values()):
            self.assertIsNotNone(self.s.find(id=target), target)

    def test_no_eager_x_widget_and_original_links_remain(self):
        self.assertNotIn('<script async src="https://platform.twitter.com/widgets.js"', self.release)
        for embed in self.s.select(".x-embed"):
            self.assertRegex(embed.select_one("a.x-original-link")["href"], r"^https://x\.com/[^/]+/status/\d+$")


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


if __name__ == "__main__":
    unittest.main()
