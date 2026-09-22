"""ローカル正典を使い、実際の生成・部分更新・仕上げ処理を通す。"""
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import consumption_tax_connected as connected
from refresh_adapters import consumption_tax as adapter
from refresh_planet_section import refresh
from scripts.seo import apply_classroom_section as classroom
from scripts.seo import apply_theme_trust as trust

CANONICAL = ROOT / "social-samples/consumption-tax-cut_hermes_arena_classified.json"


class ConnectedRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not CANONICAL.exists():
            raise RuntimeError("消費税の非公開正典をOPERATIONS.mdに従って復元してください")
        cls.temp = tempfile.TemporaryDirectory(prefix="tax-connected-test-")
        cls.stage = Path(cls.temp.name)
        cls.first = cls.stage / "first.html"
        cls.run_builder("--html-template", str(ROOT / "docs/consumption-tax-cut-reaction-map.html"),
                        "--output-html", str(cls.first), "--connected-layout")
        cls.source = cls.first.read_text()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @staticmethod
    def run_builder(*args):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/build_consumption_tax_page.py"),
                                 "--input", str(CANONICAL), "--skip-issue-counts", *args],
                                cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def test_full_builder_and_adapter_tide_are_idempotent(self):
        first = self.stage / "tide-first.html"
        first.write_text(self.source)
        adapter._apply_tide(ROOT, first, ROOT / "social-samples/updates/consumption-tax-cut/2026-09-17/classified.json", "2026-09-17")
        second = self.stage / "tide-second.html"
        self.run_builder("--html-template", str(first), "--output-html", str(second))
        adapter._apply_tide(ROOT, second, ROOT / "social-samples/updates/consumption-tax-cut/2026-09-17/classified.json", "2026-09-17")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        before = (ROOT / "docs/consumption-tax-cut-reaction-map.html").read_text()
        self.assertEqual(adapter.vote_fingerprint(before), adapter.vote_fingerprint(second.read_text()))
        for token in adapter.PROTECTED:
            self.assertEqual(before.count(token), second.read_text().count(token))

    def test_all_six_partial_update_entry_points_keep_the_connection(self):
        path = self.stage / "partial.html"
        path.write_text(self.source)
        for flag in ("--claim-audit-only", "--background-only", "--issue-cards-only",
                     "--conditions-only", "--public-counts-only"):
            with self.subTest(flag=flag):
                self.run_builder(flag, "--output-html", str(path))
                first = path.read_text()
                self.run_builder(flag, "--output-html", str(path))
                self.assertEqual(path.read_text(), first)
                self.assertEqual(connected.validate(first), [])
        # 6つめは山なみ区間だけの更新。
        _, first, failures = refresh("consumption-tax-cut", source=path.read_text())
        self.assertEqual(failures, [])
        _, second, failures = refresh("consumption-tax-cut", source=first)
        self.assertEqual(first, second)
        self.assertEqual(connected.validate(second), [])

    def test_seo_classroom_and_observations_finish_the_same_candidate(self):
        config = json.loads((ROOT / "configs/theme-seo.json").read_text())
        theme = next(t for t in config["themes"] if t["id"] == connected.TOPIC)
        classroom_config = json.loads((ROOT / "configs/classroom/consumption-tax-cut.json").read_text())
        public = json.loads((ROOT / "data/public/themes/consumption-tax-cut.json").read_text())
        def finish(source):
            source = trust.apply_theme(source, theme, config)
            source = trust.apply_observations_only(source, theme)
            return classroom.apply_theme(source, connected.TOPIC, classroom_config, public)
        first = finish(self.source)
        self.assertEqual(finish(first), first)
        self.assertEqual(connected.validate(first), [])
        self.assertIn('id="classroom-title"', first)

    def test_tide_uses_supplied_waves_instead_of_prototype_dates_and_counts(self):
        # 本文を再分類せず、隔離した更新回を渡して表示データの追従だけを確認する。
        root = self.stage / 'changed-waves'
        rows = json.loads(CANONICAL.read_text())
        opinions = [r for r in rows if r.get('classification', {}).get('is_opinion')
                    and r['classification'].get('is_relevant')]
        previous = root / 'social-samples/updates/consumption-tax-cut/2026-09-20/classified.json'
        current = root / 'social-samples/updates/consumption-tax-cut/2026-09-21/classified.json'
        for path, count in ((previous, 11), (current, 23)):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(opinions[:count], ensure_ascii=False))
        page = root / 'candidate.html'; page.write_text(self.source)
        adapter._apply_tide(root, page, current, '2026-09-21')
        from bs4 import BeautifulSoup
        tide = BeautifulSoup(page.read_text(), 'html.parser').select_one('#consumption-tax-cut-tide-widget')
        self.assertIn('9月20日 → 9月21日', tide.get_text())
        self.assertIn('前回収集分11件と今回収集分23件', tide.get_text())
        self.assertNotIn('8月24日', tide.get_text())
        self.assertIn('consumption-tax-connected-page.js?v=7', page.read_text())

    def test_sequential_refresh_finishing_and_number_sync_are_idempotent(self):
        from build_consumption_tax_page import apply_public_counts
        config = json.loads((ROOT / 'configs/theme-seo.json').read_text())
        theme = next(t for t in config['themes'] if t['id'] == connected.TOPIC)
        lesson = json.loads((ROOT / 'configs/classroom/consumption-tax-cut.json').read_text())
        public = json.loads((ROOT / 'data/public/themes/consumption-tax-cut.json').read_text())
        path = self.stage / 'sequential.html'
        wave = sorted((ROOT / 'social-samples/updates/consumption-tax-cut').glob('*/classified.json'))[-1]
        def pipeline(source):
            _, source, failures = refresh(connected.TOPIC, source=source)
            self.assertEqual(failures, [])
            path.write_text(source)
            adapter._apply_tide(ROOT, path, wave, wave.parent.name)
            source = trust.apply_theme(path.read_text(), theme, config)
            source = classroom.apply_theme(source, connected.TOPIC, lesson, public)
            source = trust.apply_observations_only(source, theme)
            return connected.apply(apply_public_counts(source))
        first = pipeline(self.source)
        self.assertEqual(pipeline(first), first)
        self.assertEqual(connected.validate(first), [])
        self.assertEqual(adapter.vote_fingerprint(first), adapter.vote_fingerprint(self.source))

    def test_changed_aggregate_rank_refreshes_counts_focus_and_keeps_relationships(self):
        from bs4 import BeautifulSoup
        data = connected.planet_data(self.source)
        finance = next(i for i in data['issues'] if i['id'].endswith('-finance-welfare'))
        iid = finance['id']; stance = next(s for s in data['stances'] if s['id'].endswith('-support'))
        # 本文を変えず、集計後の検証入力に財源・推進1000件を加える。正典ファイルには書かない。
        finance['count'] += 1000; finance['stances'][stance['key']] += 1000; finance['intensity']['low'] += 1000
        finance['top_stance'] = stance['key']; stance['count'] += 1000
        data['totals']['collected'] += 1000; data['totals']['opinions'] += 1000
        for mode in data['modes']:
            if mode['id'] in ('all', stance['key']):
                mode['counts'][iid] += 1000; mode['total'] += 1000
            for key, count in mode['counts'].items():
                mode['width_pct'][key] = count / mode['total'] * 100
                mode['high_pct'][key] = mode['high_counts'][key] / count * 100 if count else 0
        for issue in data['issues']:
            issue['share_pct'] = issue['count'] / data['totals']['opinions'] * 100
        data['issues'].sort(key=lambda i: -i['count'])
        before = connected.content_index(connected.planet_data(self.source))
        with patch('refresh_planet_section.bpd.build', return_value=data):
            _, page, failures = refresh(connected.TOPIC, source=self.source)
        # 表示は追従しても、未再読の論点が増えすぎた候補は既存の公開ゲートで止める。
        self.assertEqual(failures, ['編集部が読み直した論点が意見の40%しかない（50%以上必要）'])
        soup = BeautifulSoup(page, 'html.parser')
        self.assertIn('1511', soup.select_one('#fb-' + iid).get_text())
        self.assertIn('4890', soup.select_one('#stance-glance').get_text())
        self.assertIn('1511', soup.select_one('.thirty-summary').get_text())
        self.assertIn('減った分は誰が払うのか', soup.select_one('.thirty-summary').get_text())
        self.assertEqual(connected.content_index(connected.planet_data(page)), before)
        self.assertEqual(adapter.vote_fingerprint(page), adapter.vote_fingerprint(self.source))
        self.assertEqual(connected.validate(page), [])


if __name__ == "__main__":
    unittest.main()
