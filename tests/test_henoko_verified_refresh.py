"""Regressions for the failed independent audit: result visibility and stale inputs."""
import copy
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
        for field in ['text', 'stance']:
            with self.subTest(field=field):
                rows = copy.deepcopy(self.records)
                if field == 'text':
                    rows[0]['text'] += ' changed'
                else:
                    rows[0]['classification']['stance'] = 'changed stance'
                self.canonical.write_text(json.dumps(rows, ensure_ascii=False))
                with self.assertRaisesRegex(builder.IssueCountError, '再読台帳'):
                    builder.apply_public_counts(self.page, self.public)

    def test_public_cli_rejects_changed_canonical_before_writing(self):
        self.canonical.write_text(self.canonical.read_text() + '\n')
        output = self.root / 'output.html'
        output.write_text(self.page)
        with patch.object(sys, 'argv', ['build_henoko_arena.py', '--public-counts-only',
                                       '--output-html', str(output)]):
            with self.assertRaisesRegex(builder.IssueCountError, '再読台帳'):
                builder.main()
        self.assertEqual(output.read_text(), self.page)

    def test_initial_conversion_rejects_stale_inputs_in_preview_and_public_modes(self):
        legacy = self.root / 'legacy.html'
        legacy.write_text('<html><body>Old arena before conversion</body></html>')
        output = self.root / 'converted.html'
        for kind in ['body', 'stance', 'add']:
            rows = copy.deepcopy(self.records)
            item = next(x for x in rows if x == self.opinions[0])
            if kind == 'body':
                item['text'] += ' changed'
            elif kind == 'stance':
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
                        with self.assertRaisesRegex(builder.IssueCountError, '再読台帳'):
                            preview.main()
                        build.assert_not_called()
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


if __name__ == '__main__':
    unittest.main()
