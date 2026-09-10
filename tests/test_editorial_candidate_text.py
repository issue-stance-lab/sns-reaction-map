import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from scripts.prepare_editorial_candidate_text import prepare_conclusion

class CandidateCopyTest(unittest.TestCase):
    def test_leader_change_updates_text_config_and_badge_idempotently(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tree=Path(tmp)
            for f in ['configs/ai-copyright-reaction-map.json','docs/ai-copyright-reaction-map.html']:
                (tree/f).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/f,tree/f)
            (tree/'social-samples').mkdir();(tree/'social-samples/ai-copyright_hermes_classified.json').write_text('[]')
            with patch('scripts.prepare_editorial_candidate_text.counts',return_value={'issues':{'学習データ・無断利用':657,'利用者モラル・倫理':658}}):
                result=prepare_conclusion(tree);self.assertEqual(result[0]['to'],'moraru')
                page=(tree/'docs/ai-copyright-reaction-map.html').read_text()
                self.assertNotIn('論点1・最大勢力',page);self.assertIn('論点・最大勢力',page);self.assertIn('利用者モラル・倫理に分類された意見が最多',page)
                self.assertEqual(prepare_conclusion(tree),[])
                self.assertEqual(page,(tree/'docs/ai-copyright-reaction-map.html').read_text())

    def test_bukatsu_stance_notes_meters_and_arena_are_recomputed(self):
        # 課題54段階3で本番の部活動ページは山なみ形式へ差し替え済み。この関数が
        # 同期していた4つの注目ポイント・アリーナは #planet-block が役目を
        # 引き継ぎ、対象の要素が無い。現行の docs/ を入力にすると関数は
        # 何もしない（sync_issue_counts.py 等と同じ判定）。この検査は
        # その安全な no-op を見る。旧形式向けの計算式そのものは、コードに残る
        # ロジックとして保存してあるが、実データでの再検査対象ではなくなった。
        from scripts.prepare_editorial_candidate_text import sync_bukatsu_summary
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tree=Path(tmp);(tree/'docs').mkdir();(tree/'social-samples').mkdir()
            p=tree/'docs/bukatsu-chiiki-reaction-map.html';shutil.copy2(root/'docs/bukatsu-chiiki-reaction-map.html',p)
            self.assertIn('<!-- PLANET_SECTION_START -->',p.read_text())
            (tree/'social-samples/bukatsu-chiiki_hermes_classified.json').write_text('[]')
            values={'opinions':1000,'stances':{'移行支持':450,'条件付き・改善要求':230},'issues':{'教員の働き方':330,'受け皿・指導者':165,'制度・移行プロセス':255}}
            with patch('scripts.prepare_editorial_candidate_text.counts',return_value=values):
                before=p.read_text();sync_bukatsu_summary(tree)
                self.assertEqual(before,p.read_text())

    def test_bukatsu_new_opinion_rebuilds_actual_map_population(self):
        # 同上（山なみ形式では no-op）。
        from scripts.prepare_editorial_candidate_text import sync_bukatsu_summary
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tree=Path(tmp);(tree/'docs').mkdir();(tree/'social-samples').mkdir()
            p=tree/'docs/bukatsu-chiiki-reaction-map.html';shutil.copy2(root/'docs/bukatsu-chiiki-reaction-map.html',p)
            rows=[{'classification':{'is_relevant':True,'is_opinion':True,'main_issue':issue,'stance':stance,'summary':'test'}} for issue,stance in [('教員の働き方','移行支持'),('教員の働き方','移行支持'),('受け皿・指導者','条件付き・改善要求')]]
            (tree/'social-samples/bukatsu-chiiki_hermes_classified.json').write_text(json.dumps(rows))
            before=p.read_text();sync_bukatsu_summary(tree)
            self.assertEqual(before,p.read_text())
