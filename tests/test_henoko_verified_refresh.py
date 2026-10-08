"""Regressions for the failed independent audit: result visibility and stale inputs."""
import copy
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import build_henoko_arena as builder
from scripts import build_planet_page_preview as preview

ROOT = Path(__file__).resolve().parents[1]
TOPIC = builder.THEME


class VoteScrollTests(unittest.TestCase):
    def test_only_scroll_changes_and_vote_protection_remains_strict(self):
        page = (ROOT / builder.PAGE).read_text()
        corrected = preview.fix_henoko_vote_scroll(page)
        self.assertIn("getElementById('vote-result').scrollIntoView", corrected)
        self.assertNotIn("getElementById('issue-arena-section').scrollIntoView", corrected)
        preview.verify_preserved(page, corrected)
        with self.assertRaises(SystemExit):
            preview.verify_preserved(page, corrected.replace(
                'choiceIdx:selected*STANCES.length+index', 'choiceIdx:0'))
        other = page.replace("var TOPIC='henoko-student-accident-issue-stance-v1'",
                             "var TOPIC='another-topic'")
        self.assertEqual(preview.fix_henoko_vote_scroll(other), other)


@unittest.skipUnless((ROOT / "social-samples/henoko/henoko_hermes_arena_classified.json").exists(), "requires private canonical; checked locally before publication")
class VerifiedRefreshTests(unittest.TestCase):
    def setUp(self):
        self.records, self.opinions = builder.load_records(None)
        self.page = (ROOT / builder.PAGE).read_text()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        sample = builder.parse_themes_yaml(builder.THEMES_YAML)[TOPIC]['sample_file']
        paths = [Path('THEMES.yaml'), Path(sample), Path('configs/planet') / (TOPIC + '.yaml')]
        paths += [p.relative_to(ROOT) for p in (ROOT / 'data').rglob('*')
                  if p.is_file() and TOPIC in p.name]
        for path in paths:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, target)
        self.canonical = self.root / sample
        self.public = self.root / 'data/public/themes' / (TOPIC + '.json')
        for obj, attr, value in [(builder, 'ROOT', self.root),
                                 (builder, 'THEMES_YAML', self.root / 'THEMES.yaml'),
                                 (builder, 'PUBLIC_THEME', self.public),
                                 (preview.bpd, 'ROOT', self.root)]:
            context = patch.object(obj, attr, value)
            context.start()
            self.addCleanup(context.stop)

    def test_refresh_replaces_stale_planet_and_is_idempotent(self):
        start, end = '<!-- PLANET_SECTION_START -->', '<!-- PLANET_SECTION_END -->'
        i, j = self.page.index(start), self.page.index(end) + len(end)
        stale = self.page[:i] + start + 'STALE AUDIT MAP' + end + self.page[j:]
        refreshed = builder.build_page(stale, self.records, self.opinions)
        self.assertNotIn('STALE AUDIT MAP', refreshed)
        self.assertIn('window.PLANET_DATA=', refreshed)
        self.assertEqual(builder.build_page(refreshed, self.records, self.opinions), refreshed)
        self.assertEqual(builder.apply_public_counts(refreshed, self.public), refreshed)

    def test_candidate_addition_body_and_classification_changes_are_rejected(self):
        # 登録済みの公開JSON（正典と同じ版）のまま、候補だけが違う場面。追加は公開件数、
        # 既存投稿の本文・分類の書き換えは「正典の既存投稿を含まない」で止まる。
        # 公開JSONを候補から作り直した場合に通る追加は、下の test_new_wave_candidate_* にある。
        for kind in ['add', 'body', 'stance']:
            with self.subTest(kind=kind):
                rows = copy.deepcopy(self.records)
                item = next(x for x in rows if x == self.opinions[0])
                if kind == 'add':
                    extra = copy.deepcopy(item)
                    extra['tweet_id'] = 'audit-added'
                    rows.append(extra)
                elif kind == 'body':
                    item['text'] += ' changed body'
                else:
                    item['classification']['stance'] = 'changed stance'
                opinions = [r for r in rows if builder.classification(r)['is_opinion']
                            and builder.classification(r)['main_issue'] in builder.ISSUE_INDEX]
                with self.assertRaisesRegex(builder.IssueCountError, '入力候補'):
                    builder.build_page(self.page, rows, opinions)
        with self.assertRaisesRegex(builder.IssueCountError, '入力候補'):
            builder.build_page(self.page, self.records, self.opinions[:-1])

    def test_changed_canonical_cannot_bypass_evidence_with_public_counts(self):
        # 正典を書き換えたのに公開JSONを作り直していない場面は、公開JSONの元データ指紋
        # （source_sha256）が止める。本文だけの変更も、件数が同じ分類の変更も、ここで止まる
        # （2026-10-08以前は、本文の変更は再読台帳の照合まで進んで初めて止まっていた）。
        # 賛否の変更は、指紋より前に、論点別の賛否件数の不一致が止める。
        rows = copy.deepcopy(self.records)
        rows[0]['text'] += ' changed'
        self.canonical.write_text(json.dumps(rows, ensure_ascii=False))
        with self.assertRaisesRegex(builder.IssueCountError, '元データ指紋'):
            builder.apply_public_counts(self.page, self.public)

        rows = copy.deepcopy(self.records)
        rows[0]['classification']['stance'] = 'changed stance'
        self.canonical.write_text(json.dumps(rows, ensure_ascii=False))
        with self.assertRaisesRegex(builder.IssueCountError, '公開分類'):
            builder.apply_public_counts(self.page, self.public)

    def test_reread_evidence_still_stops_a_changed_post_when_the_public_json_is_rebuilt(self):
        # 公開JSONも作り直して指紋を合わせても、再読済みの投稿の本文が変わっていれば、
        # 再読台帳の本文指紋（build_planet_data.load_reread_registry）が止める。
        rows = copy.deepcopy(self.records)
        rows[0]['text'] += ' changed'
        self.canonical.write_text(json.dumps(rows, ensure_ascii=False))
        self.public.write_text(json.dumps(builder.candidate_public_theme(rows), ensure_ascii=False))
        with self.assertRaisesRegex(SystemExit, '本文'):
            builder.apply_public_counts(self.page, self.public)

    def wave_candidate(self, opinions: int = 2, others: int = 1):
        """正典に、新しい回の合成投稿を足した候補。意見は最大の論点から複製する。"""
        top = Counter(builder.classification(r)['main_issue'] for r in self.opinions).most_common(1)[0][0]
        template = next(r for r in self.opinions if builder.classification(r)['main_issue'] == top)
        rows = copy.deepcopy(self.records)
        for n in range(opinions + others):
            clone = copy.deepcopy(template)
            key = f'synthetic-wave-{n}'
            clone.update(tweet_id=key, url=f'https://x.com/example/status/{key}',
                         text=template['text'] + f' (合成の新しい回 {n})',
                         fetched_at='2026-10-08T00:00:00+00:00')
            if n >= opinions:
                clone['classification'].update(is_opinion=False, main_issue='その他')
            rows.append(clone)
        return rows, builder.opinions_of(rows)

    def candidate_public_with_current_ledger(self, rows):
        """候補から作った公開JSON。台帳の母数は、人が候補の意見数に更新した後の状態にする。"""
        public = builder.candidate_public_theme(rows)
        for item in public['ocean_layer']['sunk_continents']:
            item['sns_base'] = public['opinion_count']
        return public

    @staticmethod
    def planet_totals(page: str) -> dict:
        marker = 'window.PLANET_DATA='
        data, _ = json.JSONDecoder().raw_decode(page[page.index(marker) + len(marker):])
        return data['totals']

    def test_new_wave_candidate_builds_the_planet_from_the_candidate(self):
        # 2026-10-08まで、ここが必ず止まっていた（候補が今の正典と違う、の一点で）。
        # 正典も登録済みの公開JSONも書き換えず、候補を入力に山なみ全体を作る。
        rows, opinions = self.wave_candidate(opinions=2, others=1)
        self.assertGreater(len(opinions), len(self.opinions))
        public = self.candidate_public_with_current_ledger(rows)
        canonical_before = self.canonical.read_bytes()
        registered_before = self.public.read_bytes()

        refreshed = builder.build_page(self.page, rows, opinions, public)

        self.assertEqual(self.planet_totals(refreshed),
                         {'collected': len(rows), 'opinions': len(opinions)})
        self.assertNotEqual(refreshed, self.page)
        self.assertEqual(builder.build_page(refreshed, rows, opinions, public), refreshed)
        self.assertEqual(self.canonical.read_bytes(), canonical_before)
        self.assertEqual(self.public.read_bytes(), registered_before)

    def test_new_wave_candidate_stops_while_the_sunk_continent_ledger_is_stale(self):
        # 候補を入力にしても、人が更新する台帳（語られていない争点の母数）が追いついていなければ止まる。
        rows, opinions = self.wave_candidate(opinions=2, others=0)
        public = builder.candidate_public_theme(rows)
        with self.assertRaisesRegex(builder.IssueCountError, '母数'):
            builder.build_page(self.page, rows, opinions, public)

    def test_new_wave_candidate_is_rejected_with_the_registered_public_json(self):
        rows, opinions = self.wave_candidate(opinions=2, others=1)
        with self.assertRaisesRegex(builder.IssueCountError, '公開件数'):
            builder.build_page(self.page, rows, opinions)

    def test_new_wave_candidate_that_rewrites_a_reviewed_post_is_rejected(self):
        rows, _ = self.wave_candidate(opinions=2, others=1)
        rows[0]['text'] += ' changed'
        opinions = builder.opinions_of(rows)
        public = self.candidate_public_with_current_ledger(rows)
        with self.assertRaisesRegex(builder.IssueCountError, '入力候補'):
            builder.build_page(self.page, rows, opinions, public)

    def test_public_cli_rejects_changed_canonical_before_writing(self):
        rows = copy.deepcopy(self.records)
        rows[0]['classification']['stance'] = 'changed stance'
        self.canonical.write_text(json.dumps(rows, ensure_ascii=False))
        output = self.root / 'output.html'
        output.write_text(self.page)
        with patch.object(sys, 'argv', ['build_henoko_arena.py', '--public-counts-only',
                                       '--output-html', str(output)]):
            with self.assertRaisesRegex(builder.IssueCountError, '公開分類'):
                builder.main()
        self.assertEqual(output.read_text(), self.page)

    def test_initial_conversion_rejects_stale_inputs_in_preview_and_public_modes(self):
        # stance/addはverify_inputs自身の公開件数・公開分類の突き合わせが、bodyは公開JSONの
        # 元データ指紋（source_sha256）が、いずれもbpd.build()の前に止めるので、buildは呼ばれない。
        # （2026-10-08以前は、bodyだけは件数・分類が変わらないため検出できず、bpd.build()の
        # 再読台帳の照合まで届いて初めて止まっていた。）
        # このコードパス自体、docs/のページに山なみが入った後は
        # 「入力ページに山なみが既に入っています」で必ず先に止まる一度きりの変換専用のため、
        # 辺野古では変換済みの今、実運用では再現しない組み合わせ。
        legacy = self.root / 'legacy.html'
        legacy.write_text('<html><body>Old arena before conversion</body></html>')
        output = self.root / 'converted.html'
        expected = {'stance': '公開分類', 'add': '公開件数'}
        for kind in ['stance', 'add']:
            rows = copy.deepcopy(self.records)
            item = next(x for x in rows if x == self.opinions[0])
            if kind == 'stance':
                item['classification']['stance'] = 'changed stance'
            else:
                extra = copy.deepcopy(item)
                extra['tweet_id'] = 'audit-added'
                rows.append(extra)
            self.canonical.write_text(json.dumps(rows, ensure_ascii=False))
            for for_docs in [False, True]:
                with self.subTest(kind=kind, for_docs=for_docs):
                    output.write_text('HTML sentinel')
                    argv = ['build_planet_page_preview.py', '--topic', TOPIC,
                            '--page', str(legacy), '--out', str(output)]
                    if for_docs:
                        argv.append('--for-docs')
                    with patch.object(sys, 'argv', argv), patch.object(preview.bpd, 'build') as build:
                        with self.assertRaisesRegex(builder.IssueCountError, expected[kind]):
                            preview.main()
                        build.assert_not_called()
                    self.assertEqual(output.read_text(), 'HTML sentinel')

        rows = copy.deepcopy(self.records)
        item = next(x for x in rows if x == self.opinions[0])
        item['text'] += ' changed'
        self.canonical.write_text(json.dumps(rows, ensure_ascii=False))
        for for_docs in [False, True]:
            with self.subTest(kind='body', for_docs=for_docs):
                output.write_text('HTML sentinel')
                argv = ['build_planet_page_preview.py', '--topic', TOPIC,
                        '--page', str(legacy), '--out', str(output)]
                if for_docs:
                    argv.append('--for-docs')
                with patch.object(sys, 'argv', argv), patch.object(preview.bpd, 'build') as build:
                    with self.assertRaisesRegex(builder.IssueCountError, '元データ指紋'):
                        preview.main()
                    build.assert_not_called()
                self.assertEqual(output.read_text(), 'HTML sentinel')

        # 公開JSONも作り直して指紋を合わせた場合は、再読台帳の本文指紋が止める。
        self.public.write_text(json.dumps(builder.candidate_public_theme(rows), ensure_ascii=False))
        for for_docs in [False, True]:
            with self.subTest(kind='body-with-rebuilt-public-json', for_docs=for_docs):
                output.write_text('HTML sentinel')
                argv = ['build_planet_page_preview.py', '--topic', TOPIC,
                        '--page', str(legacy), '--out', str(output)]
                if for_docs:
                    argv.append('--for-docs')
                with patch.object(sys, 'argv', argv):
                    with self.assertRaisesRegex(SystemExit, '本文'):
                        preview.main()
                self.assertEqual(output.read_text(), 'HTML sentinel')

    def test_public_argument_is_not_ignored(self):
        data = json.loads(self.public.read_text())
        data['opinion_count'] += 1
        candidate = self.root / 'candidate-public.json'
        candidate.write_text(json.dumps(data))
        with self.assertRaises(builder.IssueCountError):
            builder.apply_public_counts(self.page, candidate)

    def test_stale_public_stance_is_rejected_even_with_same_total(self):
        data = json.loads(self.public.read_text())
        issue = next(x for x in data['issues'] if x['count'])
        source = next(x for x in issue['stances'] if x['count'])
        target = next(x for x in issue['stances'] if x is not source)
        source['count'] -= 1
        target['count'] += 1
        self.public.write_text(json.dumps(data))
        with self.assertRaisesRegex(builder.IssueCountError, '公開分類'):
            builder.apply_public_counts(self.page, self.public)

    def test_changed_reread_source_fails_before_regeneration(self):
        path = self.root / 'data' / (TOPIC + '_issues-reread.json')
        path.write_text(path.read_text() + '\n')
        with self.assertRaisesRegex(SystemExit, '出所が変更'):
            builder.build_page(self.page, self.records, self.opinions)

    def test_independence_failure_is_not_a_successful_refresh(self):
        with patch.object(preview.bpd, 'independence_gate', return_value=['audit failure']):
            with self.assertRaisesRegex(builder.IssueCountError, 'audit failure'):
                builder.build_page(self.page, self.records, self.opinions)


@unittest.skipUnless((ROOT / "social-samples/henoko/henoko_hermes_arena_classified.json").exists(), "requires private canonical; checked locally before publication")
class CliAtomicityTests(unittest.TestCase):
    def test_script_and_module_reject_changed_candidate_without_writing(self):
        records, _ = builder.load_records(None)
        records[0]['text'] += ' CLI changed body'
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            candidate = folder / 'candidate.json'
            candidate.write_text(json.dumps(records, ensure_ascii=False))
            output, asset = folder / 'page.html', folder / 'arena.js'
            for entry in [['scripts/build_henoko_arena.py'], ['-m', 'scripts.build_henoko_arena']]:
                for check in [False, True]:
                    with self.subTest(entry=entry, check=check):
                        output.write_text('HTML sentinel')
                        asset.write_text('JS sentinel')
                        args = [sys.executable, '-B', *entry, '--input', str(candidate),
                                '--output-html', str(output), '--output-data', str(asset)]
                        if check:
                            args.append('--check')
                        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn('入力候補', result.stderr)
                        self.assertEqual(output.read_text(), 'HTML sentinel')
                        self.assertEqual(asset.read_text(), 'JS sentinel')

    def test_script_and_module_build_from_a_candidate_that_adds_a_wave(self):
        # --prepare-promotion が呼ぶ形（--input に累積候補）。候補は正典と違っていても、
        # 候補から山なみを作って書き出し、正典も登録済みの公開JSONも書き換えない。
        # 意見でない投稿を足した候補にしておく（意見を足すと、人が更新する台帳の母数が
        # 追いつくまで独自性検査が止めるのが正しい動きで、その検査は上のクラスにある）。
        canonical = ROOT / builder.parse_themes_yaml(builder.THEMES_YAML)[TOPIC]['sample_file']
        before = (canonical.read_bytes(), builder.PUBLIC_THEME.read_bytes())
        records, _ = builder.load_records(None)
        extra = copy.deepcopy(records[0])
        extra.update(tweet_id='synthetic-wave-cli', url='https://x.com/example/status/synthetic-wave-cli')
        extra['classification'].update(is_opinion=False, main_issue='その他')
        records.append(extra)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            candidate = folder / 'candidate.json'
            candidate.write_text(json.dumps(records, ensure_ascii=False))
            for entry in [['scripts/build_henoko_arena.py'], ['-m', 'scripts.build_henoko_arena']]:
                with self.subTest(entry=entry):
                    output, asset = folder / 'page.html', folder / 'arena.js'
                    result = subprocess.run(
                        [sys.executable, '-B', *entry, '--input', str(candidate),
                         '--output-html', str(output), '--output-data', str(asset)],
                        cwd=ROOT, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    totals = VerifiedRefreshTests.planet_totals(output.read_text())
                    self.assertEqual(totals['collected'], len(records))
                    self.assertTrue(asset.read_text())
        self.assertEqual((canonical.read_bytes(), builder.PUBLIC_THEME.read_bytes()), before)


if __name__ == '__main__':
    unittest.main()
