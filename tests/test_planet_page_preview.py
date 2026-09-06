"""Preview composition must retain notices and vote contracts, and fail closed for publication."""
from pathlib import Path
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
            with patch.object(sys, "argv", ["preview", "--for-docs", "--out", str(out)]), patch.object(preview.bpd, "build", return_value={}), patch.object(preview.bpd, "independence_gate", return_value=["未読"]):
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
                data = preview.bpd.stabilize(preview.bpd.build(theme))
                if theme == "bukatsu-chiiki":
                    result, _ = preview.build_bukatsu(source, data)
                else:
                    result, _ = preview.build_generic(theme, source, data)
                preview.verify_preserved(source, result)
                self.assertIn("<!-- PLANET_SECTION_START -->", result)


if __name__ == "__main__":
    unittest.main()
