"""Preview composition must retain notices and vote contracts, and fail closed for publication."""
from pathlib import Path
import json
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_planet_page_preview as preview


class PreviewCompositionTest(unittest.TestCase):
    def test_generic_preserves_unknown_content_and_vote_siblings(self):
        source = '''<html><head></head><body><main>
<!-- RESEARCH_CONDITIONS_START --><aside>研究条件</aside><!-- RESEARCH_CONDITIONS_END -->
<aside data-correction="v1">取得履歴を補完しました</aside>
<section id="issue-arena-section"><div>old map</div></section>
<section class="panel" id="vote-section" data-vote-topic="fixture-v1">
<!-- ARTICLE_TRUST_START --><aside>編集情報</aside><!-- ARTICLE_TRUST_END -->
<div id="vote-step1"></div></section>
<script>var VOTE_ISSUES=['b','a']; var STANCES=['yes','no']; VoteStore.cast({choiceIdx:2});</script>
<section id="future-disclosure">将来追加された説明</section>
<!-- ADSENSE_TAG_START --><script src="ads.js"></script><!-- ADSENSE_TAG_END -->
</main></body></html>'''
        with patch.object(preview, "render_planet", return_value=""), patch.object(preview, "split_prototype", return_value={}), patch.object(preview, "build_section", return_value="<section>new map</section>"):
            html, _ = preview.build_generic("fixture", source, {})
        preview.verify_preserved(source, html)
        self.assertNotIn("old map", html)
        self.assertIn("new map", html)
        self.assertIn("将来追加された説明", html)
        self.assertIn("取得履歴を補完しました", html)
        self.assertIn("VOTE_ISSUES=['b','a']", html)

    def test_missing_protected_notice_fails(self):
        with self.assertRaisesRegex(SystemExit, "保護"):
            preview.verify_preserved('<aside>訂正</aside>', '')

    def test_vote_contract_mutation_fails(self):
        source = "<script>var STANCES=['a','b']; VoteStore.cast({topicId:'fixed'});</script>"
        with self.assertRaises(SystemExit):
            preview.verify_preserved(source, source.replace("['a','b']", "['b','a']"))

    def test_failed_gate_is_visible_and_noindex(self):
        result = preview.apply_preview_policy("<head></head><body></body>", ["読み飛ばしがあります"], False)
        self.assertIn('content="noindex,nofollow"', result)
        self.assertIn("試作・非公開", result)
        self.assertIn("読み飛ばしがあります", result)

    def test_failed_gate_rejects_for_docs(self):
        with self.assertRaisesRegex(SystemExit, "--for-docs"):
            preview.apply_preview_policy("<body></body>", ["未読"], True)

    def test_failed_cli_does_not_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "candidate.html"
            out.write_text("keep existing")
            # 部活動は課題54段階3で本番差し替え済みで、既定の --page（docs/bukatsu-chiiki-
            # reaction-map.html）は既に山なみ形式。この検査は「独自性の検査に落ちたら
            # 書かない」ことを見たいので、山なみ未挿入の入力ページを別途用意する。
            page = Path(td) / "source.html"
            page.write_text("<html><head></head><body></body></html>")
            with patch.object(sys, "argv", ["preview", "--for-docs", "--page", str(page), "--out", str(out)]), patch.object(preview.bpd, "build", return_value={}), patch.object(preview.bpd, "independence_gate", return_value=["未読"]):
                with self.assertRaisesRegex(SystemExit, "--for-docs"):
                    preview.main()
            self.assertEqual(out.read_text(), "keep existing")

    def test_output_under_docs_is_rejected_before_read(self):
        with patch.object(sys, "argv", ["preview", "--out", str(ROOT / "docs/forbidden-preview.html")]):
            with self.assertRaisesRegex(SystemExit, "docs/"):
                preview.main()

    def test_real_themes_keep_protected_fragments(self):
        for theme in ("bukatsu-chiiki", "bike-blue-ticket", "elderly-license-revocation"):
            cfg = ROOT / "configs/planet" / f"{theme}.yaml"
            if not cfg.exists():
                continue
            with self.subTest(theme=theme):
                source = (ROOT / "docs" / f"{theme}-reaction-map.html").read_text()
                if "<!-- PLANET_SECTION_START -->" in source:
                    # 課題54段階3で本番差し替え済み（部活動）。build_bukatsu/build_generic は
                    # 「まだ差し替えていない旧形式」を入力に想定しており、差し替え済みの
                    # ページを渡すと本番の更新モードと誤認してエラーで止まる（意図した挙動）。
                    # 初回差し替え時の保護区間チェックは既に通っており、この検査の対象は
                    # 今後は「初回差し替えがまだのテーマ」だけになる。
                    self.assertIn('id="planet-data"', source)
                    continue
                # Composition is verified from the checked-in display payload. Canonical
                # reread membership is covered by the separate local data tests.
                data = json.loads((ROOT / "quality/prototypes/data" / f"{theme}-planet.json").read_text())
                if theme == "bukatsu-chiiki":
                    result, _ = preview.build_bukatsu(source, data)
                else:
                    result, _ = preview.build_generic(theme, source, data)
                preview.verify_preserved(source, result)
                self.assertIn("<!-- PLANET_SECTION_START -->", result)


class ProgressVisibilityTest(unittest.TestCase):
    """進み具合が「動いて見える」ことを守る。

    2026-09-06 のオーナー指摘「バーが動いていません」の再発防止。原因は2つあった。
    帯だけを伸ばすと1回ぶんが十数ピクセルにもならず動いて見えないこと、
    そして増やし方の説明をスマホで display:none にしていたことである。
    """

    THEMES = ("bukatsu-chiiki", "bike-blue-ticket", "elderly-license-revocation")

    def test_progress_is_segmented_not_only_a_bar(self):
        # 区画の入れ物が無いと、1回の行動が帯のわずかな伸びにしかならない
        for theme in self.THEMES:
            page = ROOT / "quality/prototypes" / f"{theme}-page-preview.html"
            if not page.exists():
                continue
            with self.subTest(theme=theme):
                html = page.read_text()
                self.assertIn('id="pseg"', html)
                self.assertRegex(html, r"#progress\s+\.track\{display:none\}")

    def test_how_to_advance_is_readable_on_phones(self):
        # スマホでこそ要る説明なので、幅の狭い画面で消してはいけない
        for theme in self.THEMES:
            page = ROOT / "quality/prototypes" / f"{theme}-page-preview.html"
            if not page.exists():
                continue
            with self.subTest(theme=theme):
                html = page.read_text()
                for block in re.findall(r"@media[^{]*max-width[^{]*\{(.*?)\}\s*\}", html, flags=re.S):
                    self.assertNotRegex(
                        block, r"#progress\s+\.how\{[^}]*display:\s*none",
                        "狭い画面で増やし方の説明を消している")

    def test_progress_stays_below_the_sticky_header(self):
        # ヘッダーも上へ貼り付き、こちらより手前にいる。top:0 のままだと
        # スクロール中にヘッダーの下へ潜り込んで消える（オーナー指摘 2026-09-06）
        for theme in self.THEMES:
            page = ROOT / "quality/prototypes" / f"{theme}-page-preview.html"
            if not page.exists():
                continue
            with self.subTest(theme=theme):
                html = page.read_text()
                self.assertRegex(html, r"#progress\{position:sticky;top:var\(--isa-header-h")
                self.assertNotRegex(html, r"#progress\{position:sticky;top:0")
                # 高さは実測して入れる。決め打ちだと共通ヘッダーが変わった日に静かに隠れる
                self.assertIn("--isa-header-h", html)
                self.assertIn("getBoundingClientRect().height", html)

    def test_template_lights_segments(self):
        # 区画を点ける処理はテンプレート側にある。落とすと入れ物が空のままになる
        tpl = (ROOT / "quality/prototypes/planet-prototype.template.html").read_text()
        self.assertIn('getElementById("pseg")', tpl)
        self.assertIn('c.className = i<n ? "on" : ""', tpl)


if __name__ == "__main__":
    unittest.main()


class NicknameCompositionTest(unittest.TestCase):
    def test_legacy_map_is_removed_but_its_guarded_vote_call_survives(self):
        source = """<body><!-- RESEARCH_CONDITIONS_END -->
<section id="issue-arena-section">旧マップ</section>
<script>
(function(){
  var canvas=document.getElementById('nickname-arena'),ctx=canvas.getContext('2d');
})();
</script>
<script>VoteStore.cast({choiceIdx:0}); document.getElementById('nickname-arena')?.scrollIntoView();</script>
<section class="panel" id="explainer-section">旧カード</section>
<section class="panel" id="vote-section"></section></body>"""
        with patch.object(preview, 'render_planet', return_value=''), patch.object(preview, 'split_prototype', return_value={}), patch.object(preview, 'build_section', return_value='<section>新マップ</section>'):
            result, _ = preview.build_generic('school-nickname-ban', source, {})
        preview.verify_preserved(source, result)
        self.assertNotIn("ctx=canvas.getContext", result)
        self.assertIn('VoteStore.cast({choiceIdx:0})', result)
        self.assertNotIn('旧カード', result)

    def test_quiz_labels_exist_even_when_a_verdict_has_no_claims(self):
        template = (ROOT / 'quality/prototypes/planet-prototype.template.html').read_text()
        self.assertNotIn('return same ? same.verdict_label : v;', template)
        self.assertIn('gap:"少しずれる"', template)
