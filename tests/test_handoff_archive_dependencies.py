"""Synthetic metadata and real temporary Git/tar files; no private review data."""
import hashlib
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

from scripts.handoff_archive_dependencies import collect_handoff_inputs, verify_handoff_manifest
from scripts.editorial_work_registry import build_registry, load_registry, fingerprint
from scripts.verify_editorial_hundred import dump, read, sha


class HandoffDependencyTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.root, self.private = self.base / 'repository', self.base / 'private'
        self.root.mkdir(); self.private.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        for relative in ('scripts/classifier.py', 'scripts/nested/unchanged_dependency.py',
                         'THEMES.yaml', 'quality/designs/body-review/CYCLE_2000_RUNBOOK.md',
                         'quality/designs/body-review/POLICY_STANCE_MAPPING_V3.md'):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Synthetic fixture\n')
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True)
        self.run = self.private / 'new-run'
        packet = self.run / 'packet.private.json'
        text = 'Synthetic post for archive restoration.'
        record = dict(topic='topic', record_id_hash='synthetic-id', text=text,
                      body_sha256=hashlib.sha256(text.encode()).hexdigest(),
                      classification={'stance': 'neutral'},
                      classification_sha256=fingerprint({'stance': 'neutral'}))
        dump(packet, {'records': [record], 'criteria': {'topic': {
            'source': 'scripts/classifier.py', 'source_sha256': sha(self.root / 'scripts/classifier.py')}}})
        source = {'storage': 'private', 'path': str(packet.relative_to(self.private)),
                  'sha256': sha(packet), 'kind': 'packet'}
        journal = self.run / 'journal.private.json'
        dump(journal, {'journal': [{**{k: record[k] for k in ('topic', 'record_id_hash', 'body_sha256', 'classification_sha256')},
                                   'route': 'hold', 'canonical_applied': False}]})
        journal_source = {'storage': 'private', 'path': str(journal.relative_to(self.private)),
                          'sha256': sha(journal), 'kind': 'journal'}
        self.ledger = build_registry([source, journal_source], self.root, self.private)
        self.assertEqual(self.ledger['counts'], {'hold': 1})
        dump(self.root / 'data/verification/editorial-work.json', self.ledger)
        self.resolution = self.private / 'inventory/resolution.private.json'
        dump(self.resolution, {'records': [], 'new_credit': 0})
        self.scope = {'resolution_path': str(self.resolution.relative_to(self.private)),
                      'resolution_sha256': sha(self.resolution)}
        dump(self.root / 'data/verification/editorial-review-scope.json', self.scope)
        self.protected = self.private / 'old-handoff/protected.private.json'
        dump(self.root / 'original.json', {'unchanged': True})
        dump(self.protected, {'original.json': sha(self.root / 'original.json')})

    def collect(self, folders=None, additional_sources=()):
        return collect_handoff_inputs(self.root, self.private, self.ledger, self.scope,
                                      [self.run] if folders is None else folders, self.protected,
                                      additional_sources=additional_sources)

    def test_old_limited_review_evidence_is_restored_at_its_original_relative_path(self):
        evidence = self.private / 'older-limited-review/decisions.json'
        dump(evidence, {'reviewed_ids': ['previously-excluded-synthetic-id']})
        source = {'storage': 'private', 'path': str(evidence.relative_to(self.private)),
                  'sha256': sha(evidence)}
        paths, expected = self.collect(additional_sources=[source])
        receipt = self.make_archive(paths)
        verify_handoff_manifest(self.private, receipt, expected)
        restored = self.base / 'restored-limited'
        with tarfile.open(self.private / receipt['archive']) as tar:
            tar.extractall(restored, filter='data')
        self.assertEqual(read(restored / 'private' / source['path']), read(evidence))

    def test_changed_old_limited_evidence_cannot_be_pinned_as_current(self):
        evidence = self.private / 'older-limited-review/decisions.json'
        dump(evidence, {'reviewed_ids': ['original']})
        source = {'storage': 'private', 'path': str(evidence.relative_to(self.private)),
                  'sha256': sha(evidence)}
        dump(evidence, {'reviewed_ids': ['changed']})
        with self.assertRaisesRegex(ValueError, 'evidence missing or changed'):
            self.collect(additional_sources=[source])

    def make_archive(self, paths, mutate_manifest=None):
        destination = self.private / 'archive'
        destination.mkdir(exist_ok=True)
        manifest = {}
        for path in paths:
            base = self.root if path.is_relative_to(self.root) else self.private
            storage = 'repository/' if base == self.root else 'private/'
            manifest[storage + str(path.relative_to(base))] = sha(path)
        if mutate_manifest:
            mutate_manifest(manifest)
        dump(destination / 'manifest.private.json', manifest)
        output = destination / 'evidence.tar.gz'
        with tarfile.open(output, 'w:gz') as tar:
            for path in paths:
                base = self.root if path.is_relative_to(self.root) else self.private
                storage = 'repository/' if base == self.root else 'private/'
                tar.add(path, arcname=storage + str(path.relative_to(base)))
        return {'archive': str(output.relative_to(self.private)), 'archive_sha256': sha(output),
                'manifest_sha256': sha(destination / 'manifest.private.json'),
                'file_count': len(manifest), 'restored_files_verified': len(manifest), 'restore_verified': True}

    def test_restored_ledger_has_criteria_scope_and_transitive_code(self):
        paths, expected = self.collect()
        for relative in ('repository/scripts/classifier.py', 'repository/scripts/nested/unchanged_dependency.py',
                         'repository/THEMES.yaml', 'private/inventory/resolution.private.json',
                         'private/old-handoff/protected.private.json'):
            self.assertIn(relative, expected)
        receipt = self.make_archive(paths)
        self.assertEqual(verify_handoff_manifest(self.private, receipt, expected)['pinned_dependencies_verified'], len(expected))
        restored = self.base / 'restored'
        with tarfile.open(self.private / receipt['archive']) as tar:
            tar.extractall(restored, filter='data')
        self.assertEqual(load_registry(restored / 'repository/data/verification/editorial-work.json',
                                       restored / 'repository', restored / 'private'), self.ledger)
        self.assertEqual(sha(restored / 'private/inventory/resolution.private.json'), self.scope['resolution_sha256'])

    def test_missing_folder_is_rejected_instead_of_silently_omitted(self):
        with self.assertRaisesRegex(ValueError, 'missing or nonprivate handoff folder'):
            self.collect([self.run, self.private / 'missing-run'])

    def test_scope_and_criteria_hash_changes_stop_collection(self):
        for path in (self.resolution, self.root / 'scripts/classifier.py'):
            original = path.read_bytes()
            with self.subTest(path=path.name):
                path.write_bytes(original + b' ')
                try:
                    with self.assertRaisesRegex(ValueError, 'evidence missing or changed'):
                        self.collect()
                finally:
                    path.write_bytes(original)

    def test_source_changed_after_collection_cannot_rebase_expected_hash(self):
        paths, expected = self.collect()
        packet = self.run / 'packet.private.json'
        packet.write_bytes(packet.read_bytes() + b' ')
        receipt = self.make_archive(paths)
        with self.assertRaisesRegex(ValueError, 'pre-archive dependency pins'):
            verify_handoff_manifest(self.private, receipt, expected)

    def test_final_ledger_changed_after_collection_is_rejected(self):
        paths, expected = self.collect()
        dump(self.root / 'data/verification/editorial-work.json', {'sources': [], 'records': []})
        receipt = self.make_archive(paths)
        with self.assertRaisesRegex(ValueError, 'pre-archive dependency pins'):
            verify_handoff_manifest(self.private, receipt, expected)

    def test_omitted_source_from_completed_manifest_is_rejected(self):
        paths, expected = self.collect()
        receipt = self.make_archive(paths, lambda manifest: manifest.pop('private/new-run/packet.private.json'))
        with self.assertRaisesRegex(ValueError, 'pre-archive dependency pins'):
            verify_handoff_manifest(self.private, receipt, expected)


if __name__ == '__main__':
    unittest.main()
