import hashlib
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.prepare_cycle_supplement import prepare
from scripts.verify_editorial_hundred import dump, sha


class PrepareCycleSupplementTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.root, self.run, self.out = base / 'root', base / 'source-run', base / 'supplement'
        self.root.mkdir(); wave = self.run / 'wave-03'; wave.mkdir(parents=True)
        reservation = {'packet_hashes': {
            'batch-01/packet.private.json': 'one',
            'batch-02/packet.private.json': 'two',
        }}
        dump(wave / 'reservation.json', reservation)
        dump(self.run / 'reservation.json', {'waves': {'wave-03': sha(wave / 'reservation.json')}})
        self.current = {'is_relevant': True, 'is_opinion': True,
                        'main_issue': 'issue', 'stance': 'yes'}
        body = 'body'
        self.raw = {'topic': 'topic', 'record_id_hash': 'id', 'text': body,
                    'body_sha256': hashlib.sha256(body.encode()).hexdigest(),
                    'classification': self.current, 'classification_sha256': 'classification'}
        self.packet = {'records': [self.raw], 'criteria': {'topic': {'criteria': 'fixed'}}}
        self.editor = {'reviews': [{'index': 0, 'classification': self.current,
                                    'uncertain': False, 'evidence_sufficient': True,
                                    'reason': 'reason'}]}
        for batch in (1, 2):
            directory = wave / f'batch-{batch:02d}'; directory.mkdir()
            dump(directory / 'editor.private.json', self.editor)
            dump(directory / 'audit.private.json', {'reviews': []})
            dump(directory / 'quality_gate.private.json', {'reason_conflicts': []})

    def test_prepares_any_reserved_wave_and_pins_source(self):
        row = {'index': 0, 'topic': 'topic', 'adoption_status': 'pending_audit'}
        with patch('scripts.prepare_cycle_supplement.packet_for', return_value=self.packet), \
                patch('scripts.prepare_cycle_supplement.checked_packet'), \
                patch('scripts.prepare_cycle_supplement.assess_batch', return_value={'journal': [row]}), \
                patch('scripts.prepare_cycle_supplement.supplemental.prepare', return_value={'records': 2}) as freeze:
            self.assertEqual(prepare(self.root, self.run, 3, self.out), {'records': 2})
        provenance = freeze.call_args.kwargs['source_provenance']
        self.assertEqual(provenance['source_wave'], 'wave-03')
        self.assertEqual(provenance['source_batches'], [1, 2])
        self.assertEqual(len(freeze.call_args.args[2]), 2)

    def test_refuses_changed_wave_reservation(self):
        dump(self.run / 'wave-03/reservation.json', {'packet_hashes': {}})
        with self.assertRaisesRegex(ValueError, 'reservation changed'):
            prepare(self.root, self.run, 3, self.out)

    def test_refuses_output_inside_source_run(self):
        with self.assertRaisesRegex(ValueError, 'must not be inside'):
            prepare(self.root, self.run, 3, self.run / 'new-supplement')

    def test_cli_imports_from_repository_root(self):
        repo = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, 'scripts/prepare_cycle_supplement.py', '--help'],
            cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
