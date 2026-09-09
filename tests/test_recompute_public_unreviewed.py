import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import recompute_public_unreviewed as check
from scripts.prepare_body_review_pilot import inventory
from scripts import prepare_body_review_pilot as pilot


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def row(topic, ident, body='body', label='label', **extra):
    return dict(topic=topic, record_id_hash='sha256:' + ident,
                body_sha256=body, classification_sha256=label, **extra)


class MatchingTests(unittest.TestCase):
    def test_exact_versions_hold_attempt_and_same_body_other_id(self):
        report = {'topics': {'public': {'published': True}, 'takaichi': {'published': False}}}
        queues = {'public': [dict(row('public', str(i)), opinion=True, text='SECRET') for i in range(5)],
                  'takaichi': [dict(row('takaichi', 'x'), opinion=True, text='SECRET')]}
        work = {'records': [row('public', '0', state='hold'),
                            row('public', '1', body='old-body', state='retain_candidate'),
                            row('public', '2', label='old-label', state='change_candidate'),
                            row('public', '3', state='attempted')]}
        result = check.match_completion(report, queues, work)
        self.assertEqual(result['initial_unreviewed_public_opinions'], 5)
        self.assertEqual(result['formally_reviewed_public_opinions'], 1)
        self.assertEqual(result['unreviewed_public_opinions'], 4)
        self.assertEqual(result['attempt_only_remaining'], 1)
        self.assertNotIn('SECRET', json.dumps(result))
        self.assertEqual(result['matched_formal_states'], {'hold': 1})

    def test_different_theme_does_not_complete_same_id(self):
        report = {'topics': {'public': {'published': True}}}
        result = check.match_completion(report, {'public': [dict(row('public', '1'), opinion=True)]},
                                        {'records': [row('another', '1', state='hold')]})
        self.assertEqual(result['unreviewed_public_opinions'], 1)


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root, self.private, self.shared = [base / n for n in ('root', 'private', 'shared')]
        for path in (self.root, self.private, self.shared):
            path.mkdir()
        for folder in (self.root, self.shared):
            (folder / 'THEMES.yaml').write_text('frozen themes')
        self.theme_hash = check.sha(self.root / 'THEMES.yaml')
        self.report = {'topics': {}, 'source_fingerprints': {}, 'totals': {'published': {
            'opinion_editorial_record': 2, 'opinion_limited_record': 3}}}
        for topic in ('public', 'koshitsu-tenpakai', 'takaichi'):
            rel = 'raw/' + topic + '.json'
            for folder in (self.root, self.shared):
                write(folder / rel, ['SECRET BODY'])
            self.report['topics'][topic] = dict(published=topic != 'takaichi', canonical_file=rel,
                                                canonical_sha256=check.sha(self.root / rel))
        self.queues = {'public': [dict(row('public', '1'), opinion=True, text='SECRET'),
                                  dict(row('public', '2'), opinion=True, text='SECRET')],
                       'koshitsu-tenpakai': [dict(row('koshitsu-tenpakai', '3'), opinion=True)],
                       'takaichi': [dict(row('takaichi', '4'), opinion=True)]}
        self.work = {'sources': [], 'records': [row('public', '1', state='hold'),
                                               row('public', '2', state='attempted')]}
        write(self.root / 'data/verification/editorial-work.json', self.work)
        resolution = {'records': [row('public', '2'), row('koshitsu-tenpakai', '3')]}
        write(self.private / 'scope/resolution.json', resolution)
        self.scope = dict(resolution_path='scope/resolution.json',
                          resolution_sha256=check.sha(self.private / 'scope/resolution.json'),
                          provenance={'canonical_sha256': {t: m['canonical_sha256'] for t, m in self.report['topics'].items()}})
        write(self.root / 'data/verification/editorial-review-scope.json', self.scope)
        write(self.root / 'data/old-proof.json', {'reviewed': True})
        dep_hash = check.sha(self.root / 'data/old-proof.json')
        write(self.root / 'data/verification/reread/public.json', {'sources': {'data/old-proof.json': dep_hash}})
        write(self.private / 'old/limited.json', {'old': True})
        for storage, rel in [('repository', 'data/verification/reread/public.json'), ('private', 'old/limited.json')]:
            base = self.root if storage == 'repository' else self.private
            self.report['source_fingerprints'][rel] = check.sha(base / rel)
        for name, source in [('recompute_public_unreviewed', ''), ('prepare_body_review_pilot', 'from nested import dependency'),
                             ('editorial_work_registry', ''), ('verify_editorial_hundred', ''), ('nested', '')]:
            p = self.root / 'scripts' / (name + '.py'); p.parent.mkdir(exist_ok=True); p.write_text(source)

    def verify(self, inventory_effect=None):
        with patch.object(check, 'inventory', side_effect=inventory_effect,
                          return_value=(self.report, self.queues)), \
                patch.object(check, 'load_registry', return_value=self.work), \
                patch.object(check.subprocess, 'check_output', side_effect=AssertionError('git forbidden')):
            return check.recompute(self.root, self.private, self.shared, expected_themes_sha256=self.theme_hash,
                                   expected_initial=3, expected_public_themes=2, expected_canonical_files=3)

    def test_gitless_restore_keeps_transitive_exclusion_and_python_sources(self):
        result = self.verify()
        self.assertEqual(result['unreviewed_public_opinions'], 2)
        self.assertFalse(result['remaining_is_exactly_paused_scope'])
        paths = {(s['storage'], s['path']) for s in result['source_fingerprints']}
        self.assertIn(('repository', 'data/old-proof.json'), paths)
        self.assertIn(('private', 'old/limited.json'), paths)
        self.assertIn(('repository', 'scripts/nested.py'), paths)
        self.assertNotIn('SECRET', json.dumps(result))
        self.work['records'][1]['state'] = 'hold'
        result = self.verify()
        self.assertEqual(result['unreviewed_public_opinions'], 1)
        self.assertTrue(result['remaining_is_exactly_paused_scope'])

    def test_shared_or_baseline_changes_stop(self):
        for rel in ('THEMES.yaml', 'raw/public.json'):
            p = self.shared / rel; original = p.read_bytes(); p.write_text('changed')
            with self.assertRaises(ValueError): self.verify()
            p.write_bytes(original)
        self.theme_hash = '0' * 64
        with self.assertRaises(ValueError): self.verify()

    def test_missing_transitive_initial_evidence_stops(self):
        (self.root / 'data/old-proof.json').unlink()
        with self.assertRaisesRegex(ValueError, 'missing source'): self.verify()

    def test_wrong_exclusion_source_hash_stops(self):
        (self.private / 'old/limited.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'inventory source'): self.verify()

    def test_ledger_change_during_inventory_stops(self):
        def changed(*args):
            (self.root / 'data/verification/editorial-work.json').write_text('{}')
            return self.report, self.queues
        with self.assertRaisesRegex(ValueError, 'evidence missing or changed'):
            self.verify(changed)


class InitialExclusionTests(unittest.TestCase):
    def test_real_inventory_rebases_absolute_private_sources_without_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, private, original = [Path(tmp)/name for name in ('root', 'restored', 'original')]
            root.mkdir(); private.mkdir(); original.mkdir()
            (root/'THEMES.yaml').write_text('themes:\n  ai-copyright:\n    title: AI\n    published: done\n    sample_file: raw.json\n')
            raw={'tweet_id': '1900000000000000001', 'text': 'SECRET',
                 'classification': {'is_relevant': True, 'is_opinion': True, 'main_issue': 'x', 'stance': 'x'}}
            write(root/'raw.json', [raw])
            refs=[]
            for kind in ('focused_body_review', 'classification_review', 'classification_body_review'):
                rel=kind+'/decisions.json'
                for base in (private, original):write(base/rel, {'reviewed': True})
                refs.append({'kind': kind, 'path': str(original/rel), 'sha256': check.sha(private/rel)})
            legacy=private/'reread-inventory/20260906-v1/ai-copyright.json'
            write(legacy, {'baseline_sha256': check.sha(root/'raw.json'),
                           'focused_body_review_ids': [raw['tweet_id']], 'sources': refs})
            before=legacy.read_bytes()
            with patch.object(pilot, 'EXTERNAL', original):
                report, queues=inventory(root, private)
                self.assertEqual(report['totals']['published']['opinion_limited_record'], 1)
                self.assertEqual(check.match_completion(report, queues, {'records': []})['unreviewed_public_opinions'], 0)
                self.assertIn('classification_review/decisions.json', report['source_fingerprints'])
                restored=private/'classification_review/decisions.json'
                restored.write_text('{}')
                with self.assertRaisesRegex(ValueError, '欠落・変化'):inventory(root, private)
                restored.unlink()
                with self.assertRaisesRegex(ValueError, '欠落・変化'):inventory(root, private)
            self.assertEqual(legacy.read_bytes(), before)

    def test_legacy_repository_absolute_rebase_and_escape_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, private=Path(tmp)/'root', Path(tmp)/'private'
            root.mkdir(); private.mkdir()
            self.assertEqual(pilot.resolve_legacy_source('/old/issue-stance-aggregator/data/proof.json', root, private), root.resolve()/'data/proof.json')
            for value in ('../outside.json', '/unknown/proof.json', '/old/issue-stance-aggregator/../outside.json'):
                with self.assertRaises(ValueError):pilot.resolve_legacy_source(value, root, private)
            (root/'escape').symlink_to(private, target_is_directory=True)
            with self.assertRaises(ValueError):pilot.resolve_legacy_source('escape/proof.json', root, private)

    def test_real_inventory_excludes_limited_and_nonpublic_opinions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, private = Path(tmp) / 'root', Path(tmp) / 'private'
            root.mkdir(); private.mkdir()
            topic = 'ai-copyright'
            root.joinpath('THEMES.yaml').write_text('themes:\n  ai-copyright:\n    title: AI\n    published: done\n    sample_file: raw.json\n  takaichi:\n    title: private\n    published: pending\n    sample_file: private.json\n')
            def raw(i):
                return {'tweet_id': str(1900000000000000000+i), 'text': 'SECRET',
                        'classification': {'is_relevant': True, 'is_opinion': True, 'main_issue': 'x', 'stance': 'x'}}
            write(root/'raw.json', [raw(1), raw(2)])
            write(root/'private.json', [raw(3)])
            write(root/'focused.json', {'ids': [raw(1)['tweet_id']]})
            write(private/'reread-inventory/20260906-v1/ai-copyright.json', {
                'baseline_sha256': check.sha(root/'raw.json'), 'focused_body_review_ids': [raw(1)['tweet_id']],
                'sources': [{'kind': 'focused_body_review', 'path': 'focused.json', 'sha256': check.sha(root/'focused.json')}]})
            report, queues = inventory(root, private)
            result = check.match_completion(report, queues, {'records': []})
            self.assertEqual(report['totals']['published']['opinion_limited_record'], 1)
            self.assertEqual(result['initial_unreviewed_public_opinions'], 1)
            self.assertEqual(result['unreviewed_public_opinions'], 1)
            self.assertNotIn('SECRET', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
